import re
import rethinkdb as r
from twisted.python import log


class IRCDDatabase:
    """
    Container class which holds common queries and handles connection
    to ``RDB``.

    :param db: the name of the database to connect to.

    :param host: the hostname of the database to connect to.

    :param port: the client port of the databse.
    """

    USERS_TABLE = 'users'
    GROUPS_TABLE = 'groups'
    USER_SESSIONS_TABLE = 'user_sessions'
    GROUP_STATES_TABLE = 'group_states'

    def __init__(self, db="ircdd", host="127.0.0.1", port=28015):
        """
        Initialize the database. If no values are provided,
        assume host address of 'localhost' and port of 28015.
        """
        self.rdb_host = host
        self.rdb_port = port
        self.db = db
        self.conn = r.connect(db=self.db,
                              host=self.rdb_host,
                              port=self.rdb_port)

    def createUser(self, nickname,
                   email="", password="", registered=False, permissions={}):
        """
        Add a user to the user table.

        :param nickname: the nickname of the user.

        :param email: optional email for the user.

        :param password: optional password for the user.

        :param regustered: whether the user is registered or not.

        :param permissions: a mapping of user permissions.
        """

        exists = r.table(self.USERS_TABLE).get(
            nickname
        ).run(self.conn)

        if not exists:
            r.table(self.USERS_TABLE).insert({
                "id": nickname,
                "nickname": nickname,
                "email": email,
                "password": password,
                "registered": registered,
                "permissions": permissions
            }).run(self.conn)
        else:
            log.err("User already exists: %s" % nickname)

    def heartbeatUserSession(self, nickname):
        """
        Updates the ``last_heartbeat`` field of this user's session.
        If the session does not exist it creates it.

        :param nickname: the nickname of the user whose session will
            be updated.

        Returns:
            Dict of the user session.
        """
        session = r.table(self.USER_SESSIONS_TABLE).get(
            nickname
        ).run(self.conn)

        if not session:
            return r.table(self.USER_SESSIONS_TABLE).insert({
                "id": nickname,
                "last_heartbeat": r.now(),
                "last_message": r.now(),
                "session_start": r.now()
            }).run(self.conn)
        else:
            return r.table(self.USER_SESSIONS_TABLE).get(nickname).update({
                "last_heartbeat": r.now()
            }).run(self.conn)

    def removeUserSession(self, nickname):
        """
        Removes a user's session from existance.

        :param nickname: the nickname of the user whose session
            will be deleted.
        """
        return r.table(self.USER_SESSIONS_TABLE).get(
            nickname
        ).delete().run(self.conn)

    def removeUserFromGroup(self, nickname, group):
        """
        Removes a user's subscription from a group.

        :param nickname: the nickname of the user to unsubscribe.

        :param group: the name of the group to which the user
            is subscribed.
        """
        return r.table(self.GROUP_STATES_TABLE).get(group).replace(
            r.row.without({"users": {nickname: True}})
        ).run(self.conn)

    def heartbeatUserInGroup(self, nickname, group):
        """
        Updates a user's subscription to a group. If the subscription
        does not exist it is created. If the group state entry for the
        group does not exist, it is created.

        :param nickname: the nickname of the user to subscribe.

        :param group: the name of the group to subscribe to.
        """
        presence = r.table(self.GROUP_STATES_TABLE).get(
            group
        ).run(self.conn)

        if not presence:
            return r.table(self.GROUP_STATES_TABLE).insert({
                "id": group,
                "users": {
                    nickname: {
                        "heartbeat": r.now()
                    }
                }
            }).run(self.conn)
        else:
            return r.table(self.GROUP_STATES_TABLE).get(group).update({
                "users": r.row["users"].merge({
                    nickname: {
                        "heartbeat": r.now()
                    }
                })
            }).run(self.conn)

    def observeGroupState(self, group):
        """
        Creates a changefeed that watches the state changes for a given
        group. The changefeed lives on its own dedicated connection
        to ``RDB``. The changefeed also filters out any inactive users.

        :param group: the name of the group which the changefeed will
            observe.

        Returns:
            A changefeed that returns changes for the given group.
        """
        conn = r.connect(db=self.db,
                         host=self.rdb_host,
                         port=self.rdb_port)

        return r.table(self.GROUP_STATES_TABLE).changes().filter(
            r.row["old_val"]["id"] == group or r.row["new_val"]["id"] == group
        )["new_val"].merge(
            lambda state: {
                "users": state["users"].keys().filter(
                    lambda user: r.now()
                                  .sub(state["users"][user]["heartbeat"])
                                  .lt(30)
                                  .default(False)
                )
            }
        ).run(conn)

    def observeGroupMeta(self, group):
        """
        Creates a changefeed that watches changes to the group's metadata.
        The changefeed has its own dedicated connection to ``RDB``.

        :param group: the group whose meta to watch.

        Returns:
            A changefeed which iterates the changes for teh given group.
        """

        conn = r.connect(db=self.db,
                         host=self.rdb_host,
                         port=self.rdb_port)

        return r.table(self.GROUPS_TABLE).changes().filter(
            r.row["old_val"]["id"] == group or r.row["new_val"]["id"] == group
        ).run(conn)

    def lookupUser(self, nickname):
        """
        Finds the user with given nickname and returns the dict for it
        Returns None if the user is not found
        """
        exists = r.table(self.USERS_TABLE).get(
            nickname
        ).run(self.conn)

        if exists:
            return r.table(self.USERS_TABLE).get(
                nickname
            ).merge({
                "session": r.table(self.USER_SESSIONS_TABLE).get(nickname),
                "groups": r.table(self.GROUPS_TABLE).filter(
                    lambda group: r.table(self.GROUP_STATES_TABLE)
                                   .get(group["id"])
                                   .has_fields({
                                       "users": {
                                           nickname: True
                                       }
                                   })
                ).coerce_to("array")
            }).run(self.conn)
        else:
            return None

    def lookupUserSession(self, nickname):
        """
        Finds and returns the session for a given user. Merges
        an ``active`` field which is True if the ``last_heartbeat``
        was within the past 30 seconds.

        :param nickname: the user's nickname.

        Returns:
            A dictionary with the user session.
        """
        exists = r.table(self.USER_SESSIONS_TABLE).get(
            nickname
        ).run(self.conn)

        if exists:
            return r.table(self.USER_SESSIONS_TABLE).get(
                nickname
            ).merge(
                lambda session: {
                    "active": r.now()
                               .sub(session["last_heartbeat"])
                               .lt(30).default(False)
                }
            ).run(self.conn)

    def registerUser(self, nickname, email, password):
        """
        Finds unregistered user with same nickname and registers them with
        the given email, password, and sets registered to True

        :param nickname: the nickname of the user to register.

        :param email: the email for the user.

        :param password: the password with which to register.

        Returns:
            The updated user dta
        """

        self.checkIfValidEmail(email)
        self.checkIfValidNickname(nickname)
        self.checkIfValidPassword(password)

        result = r.table(self.USERS_TABLE).filter({
            "nickname": nickname
            }).update({
                "email": email,
                "password": password,
                "registered": True
            }).run(self.conn)
        return result

    def deleteUser(self, nickname):
        """
        Find and delete the user given by nickname.

        :param nickname: the nickname of the user to delete.

        Returns:
            The deleted user data.
        """

        return r.table(self.USERS_TABLE).get(
            nickname
            ).delete().run(self.conn)

    def setPermission(self, nickname, channel, permission):
        """
        Set permission for user for the given channel to the permissions string
        defined by permission.
        """
        current_permissions = r.table(self.USERS_TABLE).get(
            nickname
            ).pluck("permissions").run(self.conn)

        permissions_for_channel = current_permissions.get(channel, [])
        permissions_for_channel.append(permission)

        return r.table(self.USERS_TABLE).get(
            nickname
            ).update({
                "permissions": r.row["permissions"].merge({
                    channel: permissions_for_channel
                    })
            }).run(self.conn)

    def createGroup(self, name, channelType):
        """
        Creates a new group metadata and group state.

        :param name: the name of the new group.

        :param channelType: the type of the group.

        Returns:
            The metadata of the new group,
            The state of the new group.
        """
        assert name
        assert channelType

        exists = r.table(self.GROUPS_TABLE).get(
            name
            ).run(self.conn)

        if not exists:
            group = r.table(self.GROUPS_TABLE).insert({
                "id": name,
                "name": name,
                "type": channelType,
                "meta": {
                    "topic": "",
                    "topic_author": "",
                    "topic_time": r.now()
                },
            }).run(self.conn)

            state = r.table(self.GROUP_STATES_TABLE).insert({
                "id": name,
                "users": {}
            }).run(self.conn)

            return group, state
        else:
            log.err("Group already exists: %s" % name)

    def lookupGroup(self, name):
        """
        Return the IRC channel dict for channel with given name,
        along with the merged state data.

        :param name: the name of the group.

        Returns:
            The group data or None.
        """
        group = r.table(self.GROUPS_TABLE).get(
            name
        ).run(self.conn)

        if group:
            return r.table(self.GROUPS_TABLE).get(
                name
            ).merge({
                "users": r.table(self.GROUP_STATES_TABLE)
                          .get(name)["users"]
            }).run(self.conn)
        else:
            return None

    def getGroupState(self, name):
        """
        Gets the raw group state.

        :param name: the name of the group whose state to return.

        Returns:
            The state of the group
        """
        return r.table(self.GROUP_STATES_TABLE).get(
            name
        ).run(self.conn)

    def listGroups(self):
        """
        Returns a list of all groups, filtered by the ``public``
        type. Appends a list of current users to the groupdata.

        Returns:
            A list of group data.
        """

        return list(r.table(self.GROUPS_TABLE).filter(
            {"type": "public"}
        ).merge(lambda group: {
            "users": r.table(self.GROUP_STATES_TABLE)
                      .get(group["id"])["users"]
        }).run(self.conn))

    def deleteGroup(self, name):
        """
        Delete the IRC channel with the given channel name.

        :param name: the group name.

        Returns:
            The deleted group data.
        """

        deleted_group = r.table(self.GROUPS_TABLE).get(
            name
        ).delete().run(self.conn)

        deleted_state = r.table(self.GROUP_STATES_TABLE).get(
            name
        ).delete().run(self.conn)

        return deleted_group, deleted_state

    def setGroupTopic(self, name, topic, author):
        """
        Set the IRC channel's topic.

        :param name: the name of the group whose topic
            to set.

        :param topic: the topic string.

        :param author: the nickname of the author.

        Returns:
            The new group meta.
        """

        return r.table(self.GROUPS_TABLE).get(name).update({
            "meta": {
                "topic": topic,
                "topic_time": r.now(),
                "topic_author": author
                }
            }).run(self.conn)

    def checkIfValidEmail(self, email):
        """
        Checks if the passed email is valid based on the regex string
        """

        valid_email = re.compile(
            r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

        if not valid_email.match(email):
            log.error("Invalid email: %s" % email)
            raise ValueError(email)

    def checkIfValidNickname(self, nickname):
        """
        Checks if the passed nickname is valid based on the regex string
        """

        min_len = 3
        max_len = 64

        valid_nickname = re.compile(
            r"^(?i)[a-z0-9_-]{%s,%s}$" % (min_len, max_len))

        if not valid_nickname.match(nickname):
            log.error("Invalid nick: %s" % nickname)
            raise ValueError(nickname)

    def checkIfValidPassword(self, password):
        """
        Checks if the passed password is valid based on the regex string
        """

        min_len = 6
        max_len = 64

        valid_password = re.compile(
            r"^(?i)[a-z0-9_-]{%s,%s}$" % (min_len, max_len))

        if not valid_password.match(password):
            log.error("Invalid password: %s" % password)
            raise ValueError(password)
