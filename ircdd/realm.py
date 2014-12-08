from zope.interface import implements

from twisted.cred import portal
from twisted.words import ewords, iwords
from twisted.internet import defer
from twisted.python import failure

from ircdd.user import ShardedUser
from ircdd.group import ShardedGroup
from ircdd.protocol import ProxyIRCDDUser


class ShardedRealm(object):
    """
    A realm which may exist in a sharded state across different
    servers. It works with :class:`ircdd.server.ShardedUser` and
    :class:`ircdd.server.ShardedGroup` and handles operations on those
    both for the local shard and the common state in the database.
    It represents both the local view of the cumulative realm state
    (all server nodes, everywhere) and the local scope (users connected
    to the local instance).
    It subscribes to groups on behalf of the locally connected users
    and performs message relaying to the latter.

    :param ctx: an initialized context which will be used to access
        ``RDB`` and ``NSQ``.

    :param name: the name of the realm.
    """

    implements(portal.IRealm, iwords.IChatService)

    _encoding = "utf8"

    createUserOnRequest = True
    createGroupOnRequest = False

    def __init__(self, ctx, name):
        self.name = name

        self.ctx = ctx

        self.createUserOnRequest = ctx["user_on_request"]
        self.createGroupOnRequest = ctx["group_on_request"]

        self.users = {}

        # Groups contain proxies to groups that the local users are
        # interested in. The group state and meta found in the DB
        # are the authoritative versions of the data.
        # The local ShardedGroup serves as a local relay and cache.
        self.groups = {}

    def userFactory(self, name):
        """
        Returns a new ShardedUser for the given avatar id.
        The ShardedUser serves as a controller to the user's
        model.

        :param name: the name of the user to return.
        """
        return ShardedUser(self.ctx, name)

    def groupFactory(self, name):
        """
        Returns a new ShardedGroup for the given group name.
        The ShardedGroup severs as a controller to the group's
        model.

        :param name: the name of the group to return.
        """
        return ShardedGroup(self.ctx, name)

    def logoutFactory(self, avatar, facet):
        """
        Factory for providing logout functionality.
        Returns a logout function that removes tthe avatar from
        the realm.

        :param avatar: the avatar object :class:`ircdd.user.ShardedUser`).

        :param facet: the facet for the logout.
        """

        def logout():
            getattr(facet, "logout", lambda: None)()
            avatar.realm = avatar.mind = None

        return logout

    def requestAvatar(self, avatarId, mind, *interfaces):
        """
        Attempts to create a controller object for the given avatarId
        and connect it with the client connection (mind).
        At this point the avatar has been authenticated and the
        avatar's model must exist in the RDB table.

        :param avatarId: the nickname (id) of the requested avatar.

        :param mind: a :class:`twisted.words.service.IRCUser` instance
            representing the user connection.

        :param interfaces: a list of interfaces for the request.
        """
        if isinstance(avatarId, str):
            avatarId = avatarId.decode(self._encoding)

        def gotAvatar(avatar):
            # This is a leftover from the original Twisted code;
            # should never get hit.
            if avatar.realm is not None:
                raise ewords.AlreadyLoggedIn()

            for iface in interfaces:
                facet = iface(avatar, None)
                if facet is not None:
                    avatar.loggedIn(self, mind)
                    mind.name = avatarId
                    mind.realm = self
                    mind.avatar = avatar
                    return iface, facet, self.logoutFactory(avatar, facet)
            raise NotImplementedError(self, interfaces)
        return self.getUser(avatarId).addCallback(gotAvatar)

    def addUser(self, user):
        """
        Adds a user to the local store. If the user is already
        registered a Duplicate User error is returned.
        """
        if user.name in self.users:
            return defer.fail(failure.Failure(ewords.DuplicateUser()))

        self.users[user.name] = user
        return defer.succeed(user)

    def getUser(self, name):
        """
        Returns the requested user; if the user does not exist they will
        be created if the ``createUserOnRequest`` flag is set.

        :param name: the name of the user.
        """
        assert isinstance(name, unicode)

        if self.createUserOnRequest:
            def ebUser(err):
                err.trap(ewords.DuplicateUser)
                return self.lookupUser(name)
            return self.createUser(name).addErrback(ebUser)

        return self.lookupUser(name)

    def lookupUser(self, name):
        """
        Looks for the given user first in the local store and
        failing that in the database. If found in the databse,
        checks the session for validity - if the session is valid
        the user must be connected to some other node, so a ShardedUser
        with a ProxyIRCDDUser for mind is returned. If the session is
        not valid, fail with NoSuchUser.

        :param name: the name of the user to look for.
        """
        assert isinstance(name, unicode)
        name = name.lower()

        local_user = self.users.get(name)
        if local_user:
            return defer.succeed(local_user)

        remote_user = self.ctx.db.lookupUser(name)
        user_session = self.ctx.db.lookupUserSession(name)

        # User exists and session is active, so he must be
        # connected to some remote
        if remote_user and user_session and user_session["active"]:
            return defer.succeed(ShardedUser(self.ctx,
                                             name,
                                             ProxyIRCDDUser(self.ctx, name)))

        return defer.fail(failure.Failure(ewords.NoSuchUser(name)))

    def createUser(self, name):
        """
        Creates a ShardedUser instance to serve as the
        controller for a user's model. At this point the
        user is authenticated and the profile must exist
        in the RDB table.

        :param name: the name for the new user.
        """
        assert isinstance(name, unicode)

        def cbLookup(user):
            return failure.Failure(ewords.DuplicateUser(name))

        def ebLookup(err):
            err.trap(ewords.NoSuchUser)
            return self.userFactory(name)

        name = name.lower()

        d = self.lookupUser(name)
        d.addCallbacks(cbLookup, ebLookup)
        d.addCallback(self.addUser)

        return d

    def lookupGroup(self, name):
        """
        Looks for the group in the local shard's store.

        :param name: the name of the group.
        """
        assert isinstance(name, unicode)
        name = name.lower()

        group = self.groups.get(name)
        if group:
            return defer.succeed(group)

        return defer.fail(failure.Failure(ewords.NoSuchGroup(name)))

    def getGroup(self, name):
        """
        Returns the requested group. If the group does not exist
        it is created if the ``createGroupOnRequest`` flag is set.

        :param name: the name of the group.
        """
        assert isinstance(name, unicode)

        # Get this setting from the cluster's policy
        if self.createGroupOnRequest:
            def ebGroup(err):
                err.trap(ewords.DuplicateGroup)
                return self.lookupGroup(name)
            return self.createGroup(name).addErrback(ebGroup)

        return self.lookupGroup(name)

    def addGroup(self, group):
        """
        Adds a group to this realm.

        :param group: the :class:`ircdd.group.ShardedGroup`
            instance to add.
        """
        if group.name in self.groups:
            return defer.fail(failure.Failure(ewords.DuplicateGroup()))

        self.groups[group.name] = group
        return defer.succeed(group)

    def createGroup(self, name):
        """
        Creates a new group and returns the :class:`ircdd.group.ShardedGroup`
        instance that represents it.

        :param name: the name for the new group.
        """
        assert isinstance(name, unicode)

        def cbLookup(group):
            return failure.Failure(ewords.DuplicateGroup(name))

        def ebLookup(err):
            err.trap(ewords.NoSuchGroup)
            group = self.ctx.db.lookupGroup(name)

            if not group:
                self.ctx.db.createGroup(name, "public")

            return self.groupFactory(name)

        name = name.lower()

        d = self.lookupGroup(name)
        d.addCallbacks(cbLookup, ebLookup)
        d.addCallback(self.addGroup)

        return d
