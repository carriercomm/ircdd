.. Backup and Recovery

Backup and Recovery
*******************

This section describes the backup and recovery capabilities of the full service cluster.

IRCDD Crash Recovery
====================

The ``IRCDD`` server recovers from most bad requests without terminating the client connection. The callback stack is unwound until the initial callback 
in the chain and the trace is emitted.


RethinkDB Data Replication
==========================

``RethinkDB`` has a high-consistency replication capabilities that allow tables to be replicated between the nodes in the cluster. Furthermore, one can adjust the write acknowledgements required to authorize writes to any replicated table.

This has to be done manually through ``RethinkDB``'s admin interface. For more details see:

http://rethinkdb.com/docs/sharding-and-replication/


NSQ Recovery
============

Messages published on ``NSQ`` topics are not replicated across the nodes, which means that a hard failure of a ``CoreOS`` node results in permanent data loss.
Soft failures are handled automatically by ``NSQ``'s ability to cache unprocessed messages to disk and requeue failed messages.

For more details on the caching and requeueing options see:

http://www.nsq.io
