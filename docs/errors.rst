.. Error Messages

Error Messages
**************

Errors Returned to the Client:
==============================

These are errors which are sent to the client in order for them to correct their request/input.

"Already logged in! No pod people allowed."
-------------------------------------------

Indicates that an active session for this user already exists. This can be due to several reasons:

1. Another client is logged in under the same case (in the case of anonymous users).

2. If this is a registered user, the user is logged in from a different terminal

3. A hard server crash occurred and the session wasn't closed properly. In this case, the session will expire 30 seconds
   after the crash.

"No such user!"
---------------

Indicates that the ``user`` target of the last query does not exist.

"No such channel!"
------------------

Indicates that the ``group`` target of the last query does not exist.

"No such channel (could not decode your unicode)!"
--------------------------------------------------

Indicates that the ``group`` name was malformed.

"Bad password!"
---------------

Indicates that the password parameter of the last query did not match.

"Server error! Sorry!"
----------------------

Indicates that an internal server error occurred.



Internal Server Errors:
=======================

Non-fatal server errors unwind the call stack up until the initial deferred in the chain. The
stack trace can be seen in the server's log. If you are using CoreOS and fleet to run the service:

.. code-block:: shell-session

    journalctl -u ircdd@N

Where N is the server instance.
