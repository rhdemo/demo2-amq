# Messaging Work Queue Mission for Vert.x

## Purpose

This mission booster demonstrates how to dispatch tasks to a scalable
set of worker processes using a message queue. It uses the AMQP 1.0
message protocol to send and receive messages.

## Prerequisites

* The user has access to an OpenShift instance and is logged in.

* The user has selected a project in which the frontend and backend
  processes will be deployed.

## Deployment

Run the following commands to configure and deploy the applications.


### Deployment using S2I

```bash
oc apply -f ./service.yaml

oc new-app --template=amq-broker-71-basic \
  -p APPLICATION_NAME=work-queue-broker \
  -p IMAGE_STREAM_NAMESPACE=$(oc project -q) \
  -p AMQ_PROTOCOL=amqp \
  -p AMQ_QUEUES=work-queue/requests,work-queue/responses \
  -p AMQ_ADDRESSES=work-queue/worker-updates \
  -p AMQ_USER=work-queue \
  -p AMQ_PASSWORD=work-queue
  
oc apply -f ./frontend/.openshiftio/application.yaml

oc new-app --template=vertx-messaging-frontend \
  -p SOURCE_REPOSITORY_URL=https://github.com/ted-ross/vertx-messaging-work-queue-booster \
  -p SOURCE_REPOSITORY_REF=master \
  -p SOURCE_REPOSITORY_DIR=frontend  

oc apply -f ./worker/.openshiftio/application.yaml

oc new-app --template=vertx-messaging-worker \
  -p SOURCE_REPOSITORY_URL=https://github.com/ted-ross/vertx-messaging-work-queue-booster \
  -p SOURCE_REPOSITORY_REF=master \
  -p SOURCE_REPOSITORY_DIR=worker
```

### Deployment with the Fabric8 Maven Plugin

```bash
oc apply -f ./service.yaml

oc new-app --template=amq-broker-71-basic \
  -p APPLICATION_NAME=work-queue-broker \
  -p IMAGE_STREAM_NAMESPACE=$(oc project -q) \
  -p AMQ_PROTOCOL=amqp \
  -p AMQ_QUEUES=work-queue/requests,work-queue/responses \
  -p AMQ_ADDRESSES=work-queue/worker-updates \
  -p AMQ_USER=work-queue \
  -p AMQ_PASSWORD=work-queue 
  
mvn fabric8:deploy -Popenshift  
```


## Modules

The `frontend` module serves the web interface and communicates with
workers in the backend.

The `worker` module implements the worker service in the backend.
