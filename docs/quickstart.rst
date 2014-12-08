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
- ``www.git-scm.com``

**Vagrant**
- ``www.vagrantup.com``

**Virtual Box**
- `www.virtualbox.org`

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

        ➜  ~  git clone http://github.com/kzvezdarov/ircdd
        Cloning into 'ircdd'...
        remote: Counting objects: 1405, done.
        remote: Compressing objects: 100% (604/604), done.
        remote: Total 1405 (delta 810), reused 1267 (delta 729)
        Receiving objects: 100% (1405/1405), 249.10 KiB | 337.00 KiB/s, done.
        Resolving deltas: 100% (810/810), done.
        Checking connectivity... done.

        ➜  ~  cd ircdd/scripts/config/dev-vagrant 
        ➜  dev-vagrant git:(master) curl http://discovery.etcd.io/new
        https://discovery.etcd.io/f9f94b83cde8f4a5a01e436ca82251c6

        # put the new token in cloud-config
        ➜  dev-vagrant git:(master) vim cloud-config.yaml 

        ➜  dev-vagrant git:(master) ✗ export NUM_INSTANCES=2
        ➜  dev-vagrant git:(master) ✗ export SYNCED_FOLDER=/home/kiril/ircdd
        
1. Running the Project:
   
   .. code-block:: shell-session

        ➜  dev-vagrant git:(master) ✗ vagrant up
        # (lots of vagrant output omitted)

        ➜  dev-vagrant git:(master) ✗ eval $(ssh-agent)
        Agent pid 4462
        ➜  dev-vagrant git:(master) ✗ ssh-add ~/.vagrant.d/insecure_private_key 
        Identity added: /home/kiril/.vagrant.d/insecure_private_key (rsa w/o comment)
        
        ➜  dev-vagrant git:(master) ✗ vagrant ssh core-01 -- -A                
        Last login: Mon Dec  8 04:49:24 2014 from 10.0.2.2
        CoreOS (alpha)
        core@core-01 ~ $

        core@core-01 ~ $ systemctl status etcd
        ● etcd.service - etcd
           Loaded: loaded (/usr/lib64/systemd/system/etcd.service; static)
          Drop-In: /run/systemd/system/etcd.service.d
                   └─20-cloudinit.conf
           Active: active (running) since Mon 2014-12-08 04:55:15 UTC; 1min 11s ago
         Main PID: 972 (etcd)
           CGroup: /system.slice/etcd.service
                   └─972 /usr/bin/etcd

        Dec 08 04:55:15 core-01 systemd[1]: Started etcd.
        Dec 08 04:55:15 core-01 etcd[972]: [etcd] Dec  8 04:55:15.314 INFO      | The path /var/lib/etcd/log is in btrfs
        Dec 08 04:55:15 core-01 etcd[972]: [etcd] Dec  8 04:55:15.315 INFO      | Set NOCOW to path /var/lib/etcd/log succeeded
        Dec 08 04:55:15 core-01 etcd[972]: [etcd] Dec  8 04:55:15.315 INFO      | Discovery via https://discovery.etcd.io using prefix /180f5bfc55ec8f093398db792e6ad96f.
        Dec 08 04:55:16 core-01 etcd[972]: [etcd] Dec  8 04:55:16.506 INFO      | Discovery _state was empty, so this machine is the initial leader.
        Dec 08 04:55:16 core-01 etcd[972]: [etcd] Dec  8 04:55:16.506 INFO      | Discovery fetched back peer list: []
        Dec 08 04:55:16 core-01 etcd[972]: [etcd] Dec  8 04:55:16.507 INFO      | f67a70a1c1244c098791c73007d5c642 is starting a new cluster
        Dec 08 04:55:16 core-01 etcd[972]: [etcd] Dec  8 04:55:16.512 INFO      | etcd server [name f67a70a1c1244c098791c73007d5c642, listen on :4001, advertised url http://172.17.8.101:4001]
        Dec 08 04:55:16 core-01 etcd[972]: [etcd] Dec  8 04:55:16.513 INFO      | peer server [name f67a70a1c1244c098791c73007d5c642, listen on :7001, advertised url http://172.17.8.101:7001]
        Dec 08 04:55:16 core-01 etcd[972]: [etcd] Dec  8 04:55:16.513 INFO      | f67a70a1c1244c098791c73007d5c642 starting in peer mode
        Dec 08 04:55:16 core-01 etcd[972]: [etcd] Dec  8 04:55:16.514 INFO      | f67a70a1c1244c098791c73007d5c642: state changed from 'initialized' to 'follower'.
        Dec 08 04:55:16 core-01 etcd[972]: [etcd] Dec  8 04:55:16.515 INFO      | f67a70a1c1244c098791c73007d5c642: state changed from 'follower' to 'leader'.
        Dec 08 04:55:16 core-01 etcd[972]: [etcd] Dec  8 04:55:16.516 INFO      | f67a70a1c1244c098791c73007d5c642: leader changed from '' to 'f67a70a1c1244c098791c73007d5c642'.
        Dec 08 04:55:45 core-01 etcd[972]: [etcd] Dec  8 04:55:45.615 INFO      | f67a70a1c1244c098791c73007d5c642: peer added: 'a831dd40d4404743ab440d6d1eb8ac68'

        core@core-01 ~ $ fleetctl list-machines
        MACHINE		IP		METADATA
        a831dd40...	172.17.8.102	-
        f67a70a1...	172.17.8.101	-
        
        core@core-01 ~ $ fleetctl submit ircdd/scripts/services/*
        core@core-01 ~ $ fleetctl start rethinkdb@1
        Unit rethinkdb@1.service launched on a831dd40.../172.17.8.102
        core@core-01 ~ $ fleetctl start rethinkdb-discovery@1
        Unit rethinkdb-discovery@1.service launched on a831dd40.../172.17.8.102

        core@core-01 ~ $ fleetctl list-units
        UNIT				MACHINE				ACTIVE		SUB
        rethinkdb-discovery@1.service	a831dd40.../172.17.8.102	inactive	dead
        rethinkdb@1.service		a831dd40.../172.17.8.102	activating	start-pre

        # Some time after
        core@core-01 ~ $ fleetctl list-units
        UNIT				MACHINE				ACTIVE	SUB
        rethinkdb-discovery@1.service	22a1cd27.../172.17.8.101	active	running
        rethinkdb@1.service		22a1cd27.../172.17.8.101	active	running
        
        core@core-01 ~ $ fleetctl start rethinkdb@2
        Unit rethinkdb@2.service launched on 2e332120.../172.17.8.102
        core@core-01 ~ $ fleetctl start rethinkdb-discovery@2
        Unit rethinkdb-discovery@2.service launched on 2e332120.../172.17.8.102

        core@core-01 ~ $ fleetctl start nsqlookupd@{1..2}
        Unit nsqlookupd@1.service launched on 2e332120.../172.17.8.102
        Unit nsqlookupd@2.service launched on 22a1cd27.../172.17.8.101
        core@core-01 ~ $ fleetctl start nsqlookupd-discovery@{1..2}
        Unit nsqlookupd-discovery@2.service launched on 22a1cd27.../172.17.8.101
        Unit nsqlookupd-discovery@1.service launched on 2e332120.../172.17.8.102
        
        core@core-01 ~ $ fleetctl start nsqd
        Triggered global unit nsqd.service start
        
        core@core-01 ~ $ fleetctl start ircdd@{1..2}
        Unit ircdd@1.service launched on 22a1cd27.../172.17.8.101
        Unit ircdd@2.service launched on 2e332120.../172.17.8.102

        core@core-01 ~ $ fleetctl list-units
        UNIT				MACHINE				ACTIVE	SUB
        ircdd@1.service			22a1cd27.../172.17.8.101	active	running
        ircdd@2.service			2e332120.../172.17.8.102	active	running
        nsqd.service			22a1cd27.../172.17.8.101	active	running
        nsqd.service			2e332120.../172.17.8.102	active	running
        nsqlookupd-discovery@1.service	2e332120.../172.17.8.102	active	running
        nsqlookupd-discovery@2.service	22a1cd27.../172.17.8.101	active	running
        nsqlookupd@1.service		2e332120.../172.17.8.102	active	running
        nsqlookupd@2.service		22a1cd27.../172.17.8.101	active	running
        rethinkdb-discovery@1.service	22a1cd27.../172.17.8.101	active	running
        rethinkdb-discovery@2.service	2e332120.../172.17.8.102	active	running
        rethinkdb@1.service		22a1cd27.../172.17.8.101	active	running
        rethinkdb@2.service		2e332120.../172.17.8.102	active	running
