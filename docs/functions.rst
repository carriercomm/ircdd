.. Application Functions

Application Functions
*********************

``IRCDD`` is a command line distributed IRC server. It provides a basic implementation of the IRC protocol - 
relaying messages between users based on channel subscription. The distributed function comes from ``IRCDD``'s
ability to spread the relaying of a single channel across many server nodes, while providing a consistent view of the 
channel state, communication, and messaging to the connected users.

Operations:
===========

``IRCDD`` is meant to be run alongside two other services - ``RethinkDB`` and ``NSQ``. ``IRCDD`` relies on those
to perform its functions.

The server cluster is easy to operate. Instances are independent of eachother and can be started and killed with minimum
effect on the system's stability. Each server instance is a long running process that does not take or require the opreator's
input once started - it is entirely dependent on its configuration. In order to provide automatic reconfiguration, the
``IRCDD`` server container manages the server instance through the ``Confd`` daemon.

For proper client distribution, it is recommended that a load balancer is set up in front of the ``IRCDD`` instances, such as
``Haproxy``. 

The only health check that the server provides is whetehr it is reachable or not. There is no metrics plugin at this moment.

IRC Clients
===========

The ``IRCDD`` server serves requests on the IRC protocol from common IRC clients:

- `Limechat <http://limechat.net/mac/>`_ (Mac Only)
- `HexChat <http://hexchat.github.io/downloads.html>`_ (Windows, Linux, Mac)
- `mIRC <http://www.mirc.com/get.html>`_ (Windows Only)
- `HydraIRC <http://www.hydrairc.com/content/downloads>`_ (Windows Only)
- `xchat <http://xchat.org/download/>`_ (Windows, Linux)
- `Konversation <https://konversation.kde.org/>`_ (Linux Only)
