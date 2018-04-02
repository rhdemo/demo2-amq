#!/usr/bin/env python
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from __future__ import print_function, unicode_literals
import optparse
import uuid
from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container, DynamicNodeProperties
import os
import json

class Timer(object):
    def __init__(self, parent):
        self.parent = parent

    def on_timer_task(self, event):
        self.parent.tick_500ms()


class Client(MessagingHandler):
    def __init__(self, url):
        super(Client, self).__init__()
        self.uuid = str(uuid.uuid4())[0:8]
        self.url = url
        self.report_address  = "multicast.amq-demo-report"
        self.stats_address   = "multicast.amq-demo-stats"
        self.control_address = "amq-demo-control"
        self.service_address = "TBDService"
        self.capacity = 0
        self.outstanding = 0
        self.samples = []
        self.max_samples = 4
        self.request_count = 0
        self.locations = {}

    def send(self):
        if self.outstanding >= self.capacity:
            return
        to_send = self.capacity - self.outstanding
        if self.service_sender.credit < to_send:
            to_send = self.service_sender.credit
        for i in range(to_send):
            msg = Message(reply_to = self.reply_to, correlation_id = 0, body = "Client Request")
            self.service_sender.send(msg)
            self.outstanding += 1
            self.request_count += 1

    def count_received(self, location):
        if location not in self.locations:
            self.locations[location] = []
            for i in range(self.max_samples):
                self.locations[location].append(0)
        self.locations[location][0] += 1

    def send_stats_update(self):
        stat_map = {}
        for loc,samples in self.locations.items():
            stat_map[loc] = sum(samples) / (len(samples) * 0.5)
            self.locations[loc].pop()
            self.locations[loc].insert(0, 0)
            if sum(self.locations[loc]) == 0:
                self.locations.pop(loc)
        if self.stats_sender.credit > 0:
            msg = Message(properties={'api':'amq-demo.server-stats.v1'}, body=json.dumps(stat_map, sort_keys=True))
            dlv = self.stats_sender.send(msg)
            dlv.settle()
        
    def tick_500ms(self):
        self.timer = self.reactor.schedule(0.5, Timer(self))
        self.samples.append(self.request_count)
        self.request_count = 0
        if len(self.samples) > self.max_samples:
            self.samples.pop(0)
        rate = sum(self.samples) / (len(self.samples) * 0.5)  # average rate/sec over the sample span
        report = {u'capacity': self.capacity,
                  u'outstanding': self.outstanding,
                  u'rate': int(rate)}
        if self.report_sender.credit > 0:
            msg = Message(properties={'api': 'amq-demo.client-report.v1'}, body=report)
            dlv = self.report_sender.send(msg)
            dlv.settle()
        self.send_stats_update()

    def on_start(self, event):
        self.container = event.container
        self.reactor   = event.reactor
        self.conn      = event.container.connect(self.url)

    def on_connection_opened(self, event):
        self.receiver  = event.container.create_receiver(self.conn, None, dynamic=True)
        self.control_receiver = event.container.create_receiver(self.conn, self.control_address)

    def on_link_opened(self, event):
        if event.receiver == self.receiver:
            self.reply_to = event.receiver.remote_source.address
            self.service_sender = event.container.create_sender(self.conn, self.service_address)
            self.report_sender  = event.container.create_sender(self.conn, self.report_address)
            self.stats_sender   = event.container.create_sender(self.conn, self.stats_address)
            self.timer    = self.reactor.schedule(0.5, Timer(self))

    def on_sendable(self, event):
        self.send()

    def on_message(self, event):
        try:
            if event.receiver == self.control_receiver:
                props = event.message.properties
                opcode = props.get('opcode')
                value  = int(props.get('value', 0))
                if opcode == 'INC_CAPACITY':
                    self.capacity += value
                if opcode == 'DEC_CAPACITY':
                    self.capacity -= value
                    if self.capacity < 0:
                        self.capacity = 0
            elif event.receiver == self.receiver:
                ap = event.message.properties
                if 'location' in ap:
                    self.count_received(ap['location'])
        except:
            pass

    def on_accepted(self, event):
        if event.sender == self.service_sender:
            self.outstanding -= 1
            self.send()

    def on_rejected(self, event):
        if event.sender == self.service_sender:
            self.outstanding -= 1
            self.send()

    def on_released(self, event):
        if event.sender == self.service_sender:
            self.outstanding -= 1
            self.send()


try:
    ##
    ## Try to get the message bus hostname from the openshift environment
    ## Fall back to 127.0.0.1 (loopback)
    ##
    host = os.getenv("MESSAGING_SERVICE_HOST", "127.0.0.1")
    Container(Client(host)).run()
except KeyboardInterrupt: pass
