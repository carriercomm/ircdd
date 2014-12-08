.. Getting Started

Getting Started
***************

This guide will walk you through the steps needed to setup a small test cluster with
Vagrant. The test cluster uses several virtual machines to set up a CoreOS cluster on
your host OS, which can then be used to run the full service stack, just like in 
production.


Minimum System Prerequisites:
=============================
Your system must be running a x64 Linux
distribution.

0. Kernel 3.0+
1. Dual Core x64 CPU @ 2.2 GHz.
2. 4 GB RAM.
3. 5 GB of free storage.
4. An Internet connection.

The more virtual machines that you want to have in your cluster, the more powerful
hardware you will need. The rule of thumb is that each VM uses one CPU core and 1 GB of
memory, and takes up about 500 MB of disk space.


Software Prerequisites
======================

You will need the following software installed on your host OS:

**Git**
- http://www.git-scm.com

**Vagrant**
- http://www.vagrantup.com

**Virtual Box**
- http://www.virtualbox.org

Project setup
=============

These steps will guide you through setting up the host OS's environment for running the
virtual cluster.

1. First, obtain the source code by cloning the project's repository.
   The repository contains the project's source code, this documentation,
   and a set of configuration scripts needed to run a full cluster.

    .. code-block:: shell-session

        git clone https://github.com/kzvezdarov/ircdd
    

2. Move to the `scripts/config/dev-vagrant` directory:
   This location contains a ``Vagrantfile`` and a ``cloud-config.yaml`` file. The 
   ``Vagrantfile`` starts and configures a number of virtual machines running CoreOS,
   while the ``cloud-config.yaml`` serves as shared configuration for the VMs.

    .. code-block:: shell-session

        cd ircdd/scripts/config/dev-vagrant


3. In order for the machines to cluster on startup, they need to know a shared discovery token.
   The discovery token can be obtained by running:

    .. code-block:: shell-session

       curl https://discovery.etcd.io/new

   This will return a URL with a discovery token at the end. Copy and paste the token inside of ``cloud-config.yaml``
   in place of ``discovery: https://discovery.etcd.io/<token>``, replacing ``<token>`` with your token.

4. Lastly, set the following environment variables: 
   
   ``NUM_INSTANCES`` controls how many virtual machines are started at once.
   At most three instances are recommended - the VMs are quite resource heavy! Set the variable 
   like this:

   ``export NUM_INSTANCES=2`` to run two nodes.

   ``SYNCED_FOLDER`` points to where ``IRCDD`` was downloaded. This will allow the VM to
   access the project's files. Set it like this:
   
   ``export SYNCED_FOLDER=/path/to/ircdd``
   replacing ``/path/to/ircdd`` with the full path to the download location of the ``ircdd`` folder.

5. The cluster should be properly configured now. Proceed to the next section.

Running the Project
====================

These steps will walk you through starting the virtual cluster, ensuring that the
machines are clustered properly, and finally starting the service stack.

0. With the above configuration, issue the following command 
   (you should still be in ``ircdd/scripts/config/dev-config``):
   
    .. code-block:: shell-session

       vagrant up
   
   This will download the VM image, start the ``NUM_INSTANCES`` number of instances, provision and
   cluster them.

1. Set up the SSH credentials. If ``ssh-agent`` is not running start it:
   
    .. code-block:: shell-session

       eval $(ssh-agent)

   Then add the Vagrant insecure key:
   
    .. code-block:: shell-session

       ssh-add ~/.vagrant.d/insecure_private_key

   If you are using a different type of ssh key management, refer to your manager's documentation.

2. Time to SSH into one of the machines and check if they have clustered properly!
   To SSH into the first machine execute:
   
    .. code-block:: shell-session

       vagrant ssh core-01 -- -A

   from the ``ircdd/scripts/config/dev-config`` directory.

3. Once SSH'd, check if ``ETCD`` is running. ``ETCD`` is the distributed key-value store
   that enables CoreOS instances to cluster. The following should show that ``ETCD`` is in
   good status:

    .. code-block:: shell-session
   
        systemctl status etcd
   
   To make sure that the rest of the machines have clustered properly, execute:

    .. code-block:: shell-session
   
       fleetctl list-machines

   This should return a list of all machines in the cluster.

4. Make sure that the project's files were synced properly. In the home directory (default: ``/home/core``)
   there should be a directory called ``ircdd`` which has the same contents as the one that you cloned.

5. Before the ``IRCDD`` cluster can be run, the service files that control the separate
   components must be submitted to ``fleet``. ``Fleet`` is the cluster-level init system of CoreOS. It schedules, monitors,
   and controls services just like ``systemd``, except on the cluster level.

   To submit the service files issue the following command from
   CoreOS' home directory:
    
    .. code-block:: shell-session

       fleetctl submit ircdd/scripts/services/*

   This command loads all service files in the ``ircdd/scripts/services`` to the cluster, but does not
   schedule them for running yet. 

6. Now that the cluster is configured properly and all service templates are loaded in, it is time to start
   the service stack. First, start the ``RethinkDB`` cluster. Start a single node first by executing:
   
    .. code-block:: shell-session

       fleetctl start rethinkdb@1
       fleetctl start rethinkdb-discovery@1

   The initial startup of any service might take a while as the container is being 
   downloaded. To check on the status of the service run:
   
    .. code-block:: shell-session

       fleetctl status rethinkdb@1

   Once the service is ``active`` and ``running``, feel free to add another node in the
   same manner, e.g.:

    .. code-block:: shell-session

       fleetctl start rethinkdb@2
       fleetctl start rethinkdb-discovery@2

   Note that the ``RethinkDB`` service is configured to run at most one server node per machine in the
   cluster - you won't be able to start three ``RethinkDB`` servers in a cluster of two machines.

6. The ``NSQ`` cluster is started in a similar manner. Because of ``NSQ`` different
   clustering, all nodes can be started at the same time.
   To start two Lookup nodes:

    .. code-block:: shell-session
   
       fleetctl start nsqlookupd@{1..2}}
       fleetctl start nsqlookupd-discovery@{1..2}
   
   To start the ``NSQD`` nodes:

    .. code-block:: shell-session

       fleetctl start nsqd

   The ``NSQD`` service is configured as global, which means it will automatically be scheduled to run 
   on every machine in the cluster.

   Again, the actual startup might take a while as the containers are being downloaded.

7. Finally, to start two ``IRCDD`` nodes:
   
    .. code-block:: shell-session

       fleetctl start ircdd{1..2}

   The ``IRCDD`` service is configured to run one node per machine - if you have more than two
   machines in the cluster you can start more ``IRCDD`` nodes.

8. All services will take some time to start at the beginning due to their containers being downloaded
   for the first time. 
   After all entries are ``active`` and ``running``, you should be able to connect to the following
   endpoints from your host machine:
   
   ``localhost:5799`` and ``localhost:5800`` are the actual IRC servers.

   ``localhost:8080`` provides access to the database's admin interface.

Example:
========

This is the bash log of performing the above tutorial. The output of your steps should looks something like that:

0. Project Setup:
    
   .. code-block:: shell-session

1. Running the Project:
   
   .. code-block:: shell-session
