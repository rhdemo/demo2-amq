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

class Client(MessagingHandler):
    def __init__(self, url):
        super(Client, self).__init__()
        self.uuid = str(uuid.uuid4())[0:8]
        self.url = url
        self.service_address = "work-requests"
        self.capacity = 10
        self.outstanding = 0
        self.request_count = 0
        self.locations = {}
        self.receiver = None
        self.service_sender = None

    def send(self):
        if self.outstanding >= self.capacity:
            return
        to_send = self.capacity - self.outstanding
        if self.service_sender.credit < to_send:
            to_send = self.service_sender.credit
        for i in range(to_send):
            ap = {u'uppercase': True, u'reverse': True}
            msg = Message(reply_to = self.reply_to,
                          correlation_id = 0,
                          properties = ap,
                          body = "Load Request")
            self.service_sender.send(msg)
            self.outstanding += 1
            self.request_count += 1

    def on_start(self, event):
        self.container = event.container
        self.reactor   = event.reactor
        self.conn      = event.container.connect(self.url)

    def on_connection_opened(self, event):
        if self.receiver == None:
            self.receiver = event.container.create_receiver(self.conn, None, dynamic=True)
        self.outstanding = 0

    def on_link_opened(self, event):
        if event.receiver == self.receiver:
            self.reply_to = event.receiver.remote_source.address
            if self.service_sender == None:
                self.service_sender = event.container.create_sender(self.conn, self.service_address)

    def on_sendable(self, event):
        self.send()

    def on_message(self, event):
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
    container = Container(Client(host))
    container.container_id = os.getenv("HOSTNAME", "client")
    container.run()
except KeyboardInterrupt: pass
