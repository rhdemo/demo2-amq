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

from __future__ import print_function
from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container, DynamicNodeProperties
from time import time
import os

class Timer(object):
    def __init__(self, parent):
        self.parent = parent

    def on_timer_task(self, event):
        self.parent.tick()


class Request(object):
    def __init__(self, parent, delivery, message):
        self.parent   = parent
        self.delivery = delivery
        self.body     = message.body + "\nProcessed by service running on %s" % os.uname()[1]
        self.start    = time()
        self.cid      = message.correlation_id
        self.reply_to = message.reply_to

    def response(self):
        return Message(body = self.body, address = self.reply_to, correlation_id = self.cid, properties={'location':self.parent.location})


class Service(MessagingHandler):
    def __init__(self, url, location, rate):
        super(Service, self).__init__(auto_accept = False)
        self.url      = url
        self.rate     = rate
        self.address  = "TBDService"
        self.requests = []
        self.can_process = self.rate / 2  # acceptances per half-second
        self.location = location

    def process_requests(self):
        while self.can_process > 0 and len(self.requests) > 0:
            request = self.requests.pop()
            self.anon_sender.send(request.response())
            self.accept(request.delivery)
            self.can_process -= 1

    def tick(self):
        ##
        ## Schedule the next half-second tick
        ##
        self.timer = self.reactor.schedule(0.5, Timer(self))
        self.can_process = self.rate / 2

        ##
        ## Process any pending requests
        ##
        self.process_requests()

    def on_start(self, event):
        self.container   = event.container
        self.reactor     = event.reactor
        self.conn        = self.container.connect(self.url)
        self.timer       = self.reactor.schedule(0.5, Timer(self))
        self.receiver    = self.container.create_receiver(self.conn, self.address)
        self.anon_sender = self.container.create_sender(self.conn, None)

    def on_message(self, event):
        if event.receiver == self.receiver:
            ##
            ## This is a new client request received on the service address
            ##
            self.requests.append(Request(self, event.delivery, event.message))
            self.process_requests()

try:
    ##
    ## Try to get the message bus hostname from the openshift environment
    ## Fall back to 127.0.0.1 (loopback)
    ##
    host = os.getenv("MESSAGING_SERVICE_HOST", "127.0.0.1")
    location = os.getenv("AMQ_LOCATION_KEY", "On-Stage")
    Container(Service(host, location, 50)).run()
except KeyboardInterrupt: pass



