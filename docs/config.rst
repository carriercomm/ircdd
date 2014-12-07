.. Configuration

Configuration
*************

The following document describes the configuration options for ``IRCDD`` when running in a CoreOS environment.

IRCDD Configuration:
====================

.. _ircdd-service-config:

IRCDD@.service Configuration:
-----------------------------

The IRCDD service file must pass the following options when running the service container
(unless you have built a custom container which modifies these rules):

-e HOST_IP: This sets the HOST_IP environment variable of the container to match the IP address
            on which the ``IRCDD`` server will serve. This should be either $COREOS_PUBLIC_IPV4 or
            $COREOS_PRIVATE_IPV4.

-e ETCD_PORT: This sets the ETCD_PORT environment variable of the container. The ETCD_PORT is the port
              on which the local ``ETCD`` instance is running.

-e NSQD_PORT: This sets the NSQD_PORT environment variable of the container. The NSQD_PORT is the port
              on which the local ``NSQD`` service is listening - ``IRCDD`` will use that to communicate
              with it.

-e INSTANCE_NAME: This sets the INSTANCE_NAME environment variable of the container. The INSTANCE_NAME is the
                  name that this ``IRCDD`` instance will use.

-p 5799:5799: This option sets the container to bind its port 5799 to the CoreOS's port 5799. 5799 is the default
              port on which the ``IRCDD`` server accepts connections.

IRCDD Container Configuration:
------------------------------

The default ``IRCDD`` container uses ``CONFD`` for dynamic reconfiguration. There are three files of interest,
located in the ``scripts/containers/ircdd-confd`` directory:

``confd/conf.d/ircdd.toml``: This file configures ``CONFD`` to watch for changes on the ``RethinkDB`` and ``NSQLookupd`` registries and specifies the command needed to restart the server on configuration changes.

``confd/templates/ircdd.tmpl``: This file is the template for ``IRCDD``'s configuration - when ``CONFD`` detects a change, it will fill it out with the required data. By default the template pulls the ``NSQLookupd`` addresses and the address of a ``RethinkDB`` instance.

``bin/confd-watch-ircdd``: This script runs ``confd`` and lets it take control of ``IRCDD``'s execution. First it builds the initial configuration, then it starts continuously monitoring the ``ETCD`` registry for changes, while starting the ``IRCDD`` server with the initially generated configuration. It uses the environmental variables passed to the container by the service file :ref:`ircdd-service-config`

IRCDD Server Configuration:
---------------------------

The ``IRCDD`` server is implemented as a ``Twisted`` plugin and has the following 
command line usage and options:

.. code-block:: shell-session

    Usage: twistd [options] ircdd [options]
    Options:
      -G, --group_on_request       Create groups on request.
      -U, --user_on_request        Create users on request.
      -H, --hostname=              The name of this instance. [default: 127.0.0.1]
      -P, --port=                  Port on which to listen for client connections.
                                   [default: 5799]
      -D, --db=                    Name of the database holding cluster data.
                                   [default: ircdd]
          --rdb_port=              Database port for client connections. [default:
                                   28015]
          --rdb_host=              Database host. [default: localhost]
      -C, --config=                Configuration file.
          --help                   Display this help and exit.
          --nsqd-tcp-address=      
          --lookupd-http-address=  
          --version                Display Twisted version and exit.

The ``IRCDD`` server's configuration goes through three stages:

First, there are the built in defaults for all options but the nsqd and lookupd addresses.

Second, if a config file is provided, the options available within will override the defaults.

Lastly, any options passed directly via the command line will trump the previos settings (whether
default or obtained via a config file).

In short, the options have precedence based on how they are provided:

Command line > overwrites > Config file > overwrites > Defaults

This allows for more flexible configuration schemes - for example, all instances can share the same
config file, but can have some of those values overwritten by command line options if desired.

Lastly, the configuration file must be specified in the ``YAML`` format.

RethinkDB Configuration:
========================

RethinkDB@.service Configuration:
---------------------------------

The rethinkdb@.service file is the template of the service that runs ``RethinkDB``. It is bound to the lifetime of its 
dicovery service (see :ref:`rdb-discovery-service-config`)

-e HOST_IP: This sets the HOST_IP environment variable of the container to match the IP address
            on which the ``RethinkDB`` server will serve. This should be either $COREOS_PUBLIC_IPV4 or
            $COREOS_PRIVATE_IPV4. ``RethinkDB`` will use this as its canonical address.

-p 28015:28015: This maps CoreOS's port 28015 to the container's 28015. 28015 is configured as the port on which ``RethinkDB``
                listens for client connections.

-p 29015:29015: This maps CoreOS's port 29015 to the container's 29015. 29015 is configured as the port on which ``RethinkDB`` listens for intracluster connections.

-p 8080:8080: This maps CoreOS's port 8080 to the container's 8080. This is the port on which ``RethinkDB`` serves the admin
interface.

.. _rdb-discovery-service-config:

RethinkDB-Discovery@.service Configuration:
-------------------------------------------

The discovery service runs a simple registration script in a continuous loop. It is configured to co-locate and match the 
lifetime of the ``RethinkDB`` service. The discovery script simply sets an ``ETCD`` key on behalf of the local ``RethinkDB`` instance, giving it 30 seconds of time to live. The script is defined in the default ``cloud-config.yaml`` file.

RethinkDB Container Configuration:
----------------------------------

The default ``RethinkDB`` container uses ``CONFD`` for automatic clustering. There are three files of interest,
located in the ``scripts/containers/ircdd-rethinkdb-confd`` directory:

``confd/conf.d/rethinkdb.toml``: This file configures ``CONFD`` to watch for changes on the ``RethinkDB`` registries. It does not specify a restart command as ``RethinkDB`` does not need to be restarted in order to expand the cluster.

``confd/templates/rethinkdb.tmpl``: This file is the template for ``RethinkDB``'s configuration. It is rendered only once, on the initial startup of the server. If it detects any foreign entries in the ``RethinkDB`` registry in ``ETCD`` it will render them the ``join`` parameter of the config file.

``bin/confd-watch-rethindkb``: This script runs ``confd`` once in order to render the configuration and starts the ``RethinkDB`` server. First, the script registers the local instance with ``ETCD`` in order to allow for the config generation to trigger (due to a quirk in cofd v0.6.3). Then it prepends the local node's IP to the top of the config template in order to filter out the local ``ETCD`` entry (so that the server does not try to join itself). After generating the
initial configuration, the script creates and initializes the data directory if it does not exist. Lastly, the server is started.

``rethinkdb_base``: Contains the base, emtpy database and table structure in JSON format.

RethinkDB Server Configuration:
-------------------------------

Refer to ``RethinkDB``'s documentation: 

http://rethinkdb.com/

NSQLookupd Configuration:
=========================

NSQLookupd@.service Configuration:
----------------------------------

The rethinkdb@.service file is the template of the service that runs ``NSQLookupd``. It is bound to the lifetime of its 
dicovery service (see :ref:`lookupd-discovery-service-config`). It only maps two ports to the CoreOS ports:

-p 4160:4160: Maps the 4160 port of the container to the 4160 port of the CoreOS node. ``NSQLookupd`` is configured to listen for tcp clients on 4161.

-p 4161:4161: Maps the 4161 port of the container to the 4161 port of the CoreOS node. ``NSQLookupd`` is configured to listen for http clients on 4161.

.. _lookupd-discovery-service-config:

NSQLookupd-Discovery@.service Configuration:
--------------------------------------------

The discovery service runs a simple registration script in a continuous loop. It is configured to co-locate and match the 
lifetime of the ``NSQLookupd`` service. The discovery script simply sets an ``ETCD`` key on behalf of the local ``NSQLookupd`` instance, giving it 30 seconds of time to live. The script is defined in the default ``cloud-config.yaml`` file.

NSQLookupd Container Configuration:
-----------------------------------

The NSQLookupd service uses the default NSQ container - refer to its dockerfile for details:

https://github.com/dockerfile/nsq

NSQLookupd Server Configuration:
--------------------------------

Refer to the ``NSQ`` project's documentation:

http://www.nsq.io

NSQD Configuration:
===================

NSQD@.service Configuration:
----------------------------

The NSQD service runs the ``NSQD`` container with the following configuration:

-e HOST_IP: Sets the container's HOST_IP environment variable. This is the address that ``NSQD`` will use for broadcasting.

-p 4150:4150: Maps the container's 4150 port to the CoreOS node's 4150 port. ``NSQD`` will listen on 4150 for TCP clients.

-p 4151:4151: Maps the container's 4151 port to the CoreOS node's 4151 port. ``NSQD`` will listen on 4151 for HTTP clients.

NSQD Container Configration:
----------------------------
The default ``NSQD`` container uses ``CONFD`` for automatic clustering. There are three files of interest,
located in the ``scripts/containers/ircdd-nsq-confd`` directory:

``confd/conf.d/nsqd.toml``: This file configures ``CONFD`` to watch for changes on the ``NSQLookupd`` registry. The reload command simply kills the ``NSQD`` instance and restarts it with the new configuration.

``confd/templates/nsqd.tmpl``: This template renders ``NSQD``'s config file. It iterates over the entries found in the ``NSQLookupd`` registry, adding them to list of instances that ``NSQD`` will register with.

``bin/confd-watch-nsqd``: This script generates the initial configuration, starts a background job to watch for changes, and finally runs the ``NSQD`` binary.

NSQD Server Configuration:
--------------------------

Refer to the ``NSQ`` project's documentation for more available settings:

http://www.nsq.io
