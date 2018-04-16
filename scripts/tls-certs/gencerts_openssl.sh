#!/bin/bash -ex
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
# under the License
#

# Creates a root CA and creates password protected server and client certificates using openssl commands

##### Create root CA #####
openssl genrsa -aes256 -passout pass:ca-password -out ca.key 4096
openssl req -key ca.key -new -x509 -days 99999 -sha256 -out ca.crt -passin pass:ca-password -subj "/C=US/ST=New York/L=Brooklyn/O=Trust Me Inc./CN=Trusted.CA.com"


for L in onstage azure aws; do
  echo "$L-password" | cat > tls.$L.pw
  openssl genrsa -aes256 -passout file:tls.$L.pw -out tls.$L.key 4096
done

openssl req -new -key tls.onstage.key -passin file:tls.onstage.pw -out tls.onstage.csr -subj "/C=US/ST=CA/L=San Francisco/O=Red Hat Inc./CN=inter-router-demo2-amq.apps.summit.sysdeseng.com"
openssl req -new -key tls.azure.key -passin file:tls.azure.pw -out tls.azure.csr -subj "/C=US/ST=TX/L=Azure/O=Red Hat Inc./CN=inter-router-demo2-amq.apps.summit-azr.sysdeseng.com"
openssl req -new -key tls.aws.key -passin file:tls.aws.pw -out tls.aws.csr -subj "/C=US/ST=OH/L=AWS/O=Red Hat Inc./CN=inter-router-demo2-amq.apps.summit-aws.sysdeseng.com"

for L in onstage azure aws; do
  openssl x509 -req -in tls.$L.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 9999 -out tls.$L.crt -passin pass:ca-password
done

rm *.csr *.srl ca.key

for L in onstage azure aws; do
  openssl verify -verbose -CAfile ca.crt tls.$L.crt
done
