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

You can now deploy the three footprints by logging into OpenShift for
each cluster and running the `setup-*-all` script.  Use the `Copy Login
Command` feature on the OpenShift Web UI to obtain the correct login command.

<center>
<img src="images/CopyLogin.png" />
</center>

```
$ oc login https://openshift-master.summit-aws.sysdeseng.com --token=...
$ ./setup-aws-all

$ oc login https://openshift-master.summit-azr.sysdeseng.com --token=...
$ ./setup-azure-all

$ oc login https://openshift-master.summit-onstage.sysdeseng.com --token=...
$ ./setup-onstage-all
```

Please note that you may use `setup-*-ic-only` to deploy only the AMQ
Interconnect network without the services for this demo.  This might be useful
if you wish to use the network for a different distributed service deployment.

Once the three projects are running on their respective clusters, you
may use the following URLs to access the console and the
demo-controller:

<http://demo-console-demo2-amq.apps.summit-onstage.sysdeseng.com>

<http://console-demo2-amq.apps.summit-onstage.sysdeseng.com/controller.html>

To log into the console, use the address
`console-demo2-amq.apps.summit-onstage.sysdeseng.com`
and port 80.



