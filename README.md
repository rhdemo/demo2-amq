# demo2-amq
Workload, Tools, and scripts for the AMQ section of Demo-2

## Setting up the Demo

The first time you set up this demo, you must first generate the TLS
certificate authority, certificates, and keys that will be used to secure the
inter-cluster connections.

Note that this script uses `openssl` to generate keys and certificates.

```
$ cd scripts
$ ./generate-certs
```

You can now deploy the public-cloud footprints by logging into OpenShift for
each public cluster and running the `setup-*-all` script.  Use the `Copy Login
Command` feature on the OpenShift Web UI to obtain the correct login command.

<center>
<img src="images/CopyLogin.png" />
</center>

```
$ oc login https://openshift-master.summit-aws.sysdeseng.com --token=...
$ ./setup-aws-all
```

and

```
$ oc login https://openshift-master.summit-azr.sysdeseng.com --token=...
$ ./setup-azure-all
```

Please note that you may use `setup-*-ic-only` to deploy only the AMQ
Interconnect network without the services for this demo.  This might be useful
if you wish to use the network for a different distributed service deployment.

## Demo Script

[Demo Script](https://docs.google.com/document/d/1Xz_aSJAs6kbIBWFiZ4SnaCFhto1BfnMU5wXW6eqn0rs/edit?usp=sharing)

## Components of the Demo

 - Client
 - Server
 - Controller

## APIs used in the Demo

 - FraudDetection.v1
 - amq-demo.server-control/v1
 - amq-demo.server-stats/v1
 - amq-demo.client-report/v1
 - amq-demo.client-control/v1
