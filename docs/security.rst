.. Security

Security
********

Currently ``IRCDD`` is insecure by default. This is due to the fact that securing a multi-component solution like that is not
a one-size-fits-all problem. To secure the whole system, each separate component and the underlying architecture
must be secure by themselves.

The following sections serve as an initial guideline for securing the system.

IRCDD Security:
===============

The server does not provide any security and encryption at this moment. Those can be added through 
``Twisted``, but the application does not make use of them.

CoreOS Security:
================

``CoreOS`` manages connections to the cores in the cluster via SSH. SSH keys have to be added before booting
the nodes through the ``cloud-config`` file.

For more details refer to ``CoreOS``'s documentation:
https://coreos.com/docs/cluster-management/setup/cloudinit-cloud-config/

RethinkDB Cluster Security:
===========================

``RethinkDB`` does not provide built-in encryption of data. The recommended practice for securing
the exposed ports and interfaces is to utilize ``IPTables`` and filter out intruders.

For more details refer to ``RethinkDB``'s documentation:
http://rethinkdb.com/docs/security/


NSQ Cluster Security:
=====================

``NSQ`` has the option of both providing encryption for client and cluster connections and
verifying requests through an authentication server.

For more details consult ``NSQ``'s documentation:

http://www.nsq.io
