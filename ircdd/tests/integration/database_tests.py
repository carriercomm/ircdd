import rethinkdb as r
from ircdd import database

from ircdd.tests import integration


class TestIRCDDatabase():
    def setUp(self):
        self.conn = r.connect(db=integration.DB,
                              host=integration.HOST,
                              port=integration.PORT)

        self.db = database.IRCDDatabase(integration.DB,
                                        integration.HOST,
                                        integration.PORT)

    def tearDown(self):
        integration.cleanTables()

        self.conn.close()

        self.db.conn.close()
        self.db = None

    def test_createUser(self):
        self.db.createUser('test_user',
                           email='user@test.dom',
                           password='password',
                           registered=True)
        user = self.db.lookupUser('test_user')
        assert user['nickname'] == "test_user"
        assert user['email'] == 'user@test.dom'
        assert user['password'] == 'password'
        assert user['registered']
        assert user['permissions'] == {}

    def test_createManyUsers(self):
        self.db.createUser('test_user_1',
                           email='user1@test.dom',
                           password='password',
                           registered=True)

        self.db.createUser('test_user_2',
                           email='user2@test.dom',
                           password='password',
                           registered=True)

        self.db.createUser('test_user_3',
                           email='user3@test.dom',
                           password='password',
                           registered=True)

        self.db.createUser('test_user_4',
                           email='user4@test.dom',
                           password='password',
                           registered=True)

        self.db.createUser('test_user_5',
                           email='user5@test.dom',
                           password='password',
                           registered=True)

        user1 = self.db.lookupUser('test_user_1')
        user2 = self.db.lookupUser('test_user_2')
        user3 = self.db.lookupUser('test_user_3')
        user4 = self.db.lookupUser('test_user_4')
        user5 = self.db.lookupUser('test_user_5')

        assert user1['nickname'] == "test_user_1"
        assert user1['email'] == 'user1@test.dom'
        assert user1['password'] == 'password'
        assert user1['registered']
        assert user1['permissions'] == {}

        assert user2['nickname'] == "test_user_2"
        assert user2['email'] == 'user2@test.dom'
        assert user2['password'] == 'password'
        assert user2['registered']
        assert user2['permissions'] == {}

        assert user3['nickname'] == "test_user_3"
        assert user3['email'] == 'user3@test.dom'
        assert user3['password'] == 'password'
        assert user3['registered']
        assert user3['permissions'] == {}

        assert user4['nickname'] == "test_user_4"
        assert user4['email'] == 'user4@test.dom'
        assert user4['password'] == 'password'
        assert user4['registered']
        assert user4['permissions'] == {}

        assert user5['nickname'] == "test_user_5"
        assert user5['email'] == 'user5@test.dom'
        assert user5['password'] == 'password'
        assert user5['registered']
        assert user5['permissions'] == {}

    def test_registerUser(self):
        self.db.createUser('test_user')

        user = self.db.lookupUser('test_user')
        assert user['nickname'] == 'test_user'
        assert user['email'] == ''
        assert user['password'] == ''
        assert not user['registered']
        assert user['permissions'] == {}

        self.db.registerUser('test_user', 'user@test.dom', 'password')
        user = self.db.lookupUser('test_user')
        assert user['nickname'] == 'test_user'
        assert user['email'] == 'user@test.dom'
        assert user['password'] == 'password'
        assert user['registered']
        assert user['permissions'] == {}

    def test_deleteUser(self):
        self.db.createUser('test_user')
        user = self.db.lookupUser('test_user')
        assert user['nickname'] == 'test_user'
        assert user['email'] == ''
        assert user['password'] == ''
        assert not user['registered']
        assert user['permissions'] == {}

        self.db.deleteUser('test_user')
        user = self.db.lookupUser('test_user')
        assert user is None

    def test_floodDeleteUser(self):
        self.db.createUser('test_user')
        user = self.db.lookupUser('test_user')
        assert user['nickname'] == 'test_user'
        assert user['email'] == ''
        assert user['password'] == ''
        assert not user['registered']
        assert user['permissions'] == {}

        self.db.deleteUser('test_user')
        self.db.createUser('test_user')
        self.db.deleteUser('test_user')
        self.db.createUser('test_user')
        self.db.deleteUser('test_user')
        self.db.createUser('test_user')
        self.db.deleteUser('test_user')
        self.db.createUser('test_user')
        self.db.deleteUser('test_user')
        self.db.createUser('test_user')
        self.db.deleteUser('test_user')
        self.db.createUser('test_user')
        self.db.deleteUser('test_user')
        self.db.createUser('test_user')
        self.db.deleteUser('test_user')

        user = self.db.lookupUser('test_user')
        assert user is None

    def test_setPermission(self):
        self.db.createUser('test_user', 'user@test.dom', 'pass', True)
        user = self.db.lookupUser('test_user')
        assert user['nickname'] == 'test_user'
        assert user['email'] == 'user@test.dom'
        assert user['password'] == 'pass'
        assert user['registered']
        assert user['permissions'] == {}
        self.db.setPermission('test_user', 'test_channel', '+s')
        user = self.db.lookupUser('test_user')
        assert user['permissions']['test_channel'] == ['+s']

    def test_createGroup(self):
        self.db.createGroup('test_channel', 'public')

        group = self.db.lookupGroup('test_channel')

        assert group['name'] == 'test_channel'
        assert group['type'] == 'public'
        assert group['meta'] != {}
        assert group["users"] == {}

    def test_createManyGroups(self):
        self.db.createGroup('test_channel_1', 'public')
        self.db.createGroup('test_channel_2', 'public')
        self.db.createGroup('test_channel_3', 'public')
        self.db.createGroup('test_channel_4', 'public')
        self.db.createGroup('test_channel_5', 'public')
        self.db.createGroup('test_channel_6', 'public')
        self.db.createGroup('test_channel_7', 'public')
        self.db.createGroup('test_channel_8', 'public')
        self.db.createGroup('test_channel_9', 'public')

        group1 = self.db.lookupGroup('test_channel_1')
        group2 = self.db.lookupGroup('test_channel_2')
        group3 = self.db.lookupGroup('test_channel_3')
        group4 = self.db.lookupGroup('test_channel_4')
        group5 = self.db.lookupGroup('test_channel_5')
        group6 = self.db.lookupGroup('test_channel_6')
        group7 = self.db.lookupGroup('test_channel_7')
        group8 = self.db.lookupGroup('test_channel_8')
        group9 = self.db.lookupGroup('test_channel_9')

        assert group1['name'] == 'test_channel_1'
        assert group1['type'] == 'public'
        assert group1['meta'] != {}
        assert group1["users"] == {}

        assert group2['name'] == 'test_channel_2'
        assert group2['type'] == 'public'
        assert group2['meta'] != {}
        assert group2["users"] == {}

        assert group3['name'] == 'test_channel_3'
        assert group3['type'] == 'public'
        assert group3['meta'] != {}
        assert group3["users"] == {}

        assert group4['name'] == 'test_channel_4'
        assert group4['type'] == 'public'
        assert group4['meta'] != {}
        assert group4["users"] == {}

        assert group5['name'] == 'test_channel_5'
        assert group5['type'] == 'public'
        assert group5['meta'] != {}
        assert group5["users"] == {}

        assert group6['name'] == 'test_channel_6'
        assert group6['type'] == 'public'
        assert group6['meta'] != {}
        assert group6["users"] == {}

        assert group7['name'] == 'test_channel_7'
        assert group7['type'] == 'public'
        assert group7['meta'] != {}
        assert group7["users"] == {}

        assert group8['name'] == 'test_channel_8'
        assert group8['type'] == 'public'
        assert group8['meta'] != {}
        assert group8["users"] == {}

        assert group9['name'] == 'test_channel_9'
        assert group9['type'] == 'public'
        assert group9['meta'] != {}
        assert group9["users"] == {}

    def test_deleteGroup(self):
        self.db.createGroup('test_channel', 'public')
        channel = self.db.lookupGroup('test_channel')
        assert channel['name'] == 'test_channel'
        assert channel['type'] == 'public'
        assert channel['meta'] != {}

        self.db.deleteGroup('test_channel')

        channel = self.db.lookupGroup('test_channel')
        assert channel is None

        state = self.db.getGroupState("test_channel")
        assert state is None

    def test_floodDeleteGroup(self):
        self.db.createGroup('java4ever', 'public')
        channel = self.db.lookupGroup('java4ever')
        assert channel['name'] == 'java4ever'
        assert channel['type'] == 'public'
        assert channel['meta'] != {}

        self.db.deleteGroup('java4ever')
        self.db.createGroup('java4ever', 'public')
        self.db.deleteGroup('java4ever')
        self.db.createGroup('java4ever', 'public')
        self.db.deleteGroup('java4ever')
        self.db.createGroup('java4ever', 'public')
        self.db.deleteGroup('java4ever')
        self.db.createGroup('java4ever', 'public')
        self.db.deleteGroup('java4ever')
        self.db.createGroup('java4ever', 'public')
        self.db.deleteGroup('java4ever')
        self.db.createGroup('java4ever', 'public')
        self.db.deleteGroup('java4ever')
        self.db.createGroup('java4ever', 'public')
        self.db.deleteGroup('java4ever')
        self.db.createGroup('java4ever', 'public')
        self.db.deleteGroup('java4ever')

        channel = self.db.lookupGroup('java4ever')
        assert channel is None

        state = self.db.getGroupState('java4ever')
        assert state is None

    def test_setGroupData(self):
        self.db.createGroup('test_channel', 'public')
        channel = self.db.lookupGroup('test_channel')
        assert channel['name'] == 'test_channel'
        assert channel['type'] == 'public'
        assert channel['meta'] != {}

        self.db.setGroupTopic('test_channel', 'test', 'john_doe')
        channel = self.db.lookupGroup('test_channel')

        assert channel['meta']['topic'] == 'test'
        assert channel['meta']['topic_time']
        assert channel['meta']['topic_author'] == 'john_doe'

    def test_floodSetGroupData(self):
        self.db.createGroup('test_channel', 'public')
        channel = self.db.lookupGroup('test_channel')
        assert channel['name'] == 'test_channel'
        assert channel['type'] == 'public'
        assert channel['meta'] != {}

        self.db.setGroupTopic('test_channel', 'test', 'john_doe')
        self.db.setGroupTopic('test_channel', 'foo', 'john_doe')
        self.db.setGroupTopic('test_channel', 'baz', 'john_doe')
        self.db.setGroupTopic('test_channel', 'meh', 'john_doe')
        self.db.setGroupTopic('test_channel', 'test', 'john_doe')
        self.db.setGroupTopic('test_channel', 'test', 'john_doe')
        self.db.setGroupTopic('test_channel', 'foo', 'john_doe')
        self.db.setGroupTopic('test_channel', 'baz', 'john_doe')
        self.db.setGroupTopic('test_channel', 'meh', 'john_doe')
        self.db.setGroupTopic('test_channel', 'test', 'john_doe')
        channel = self.db.lookupGroup('test_channel')

        assert channel['meta']['topic'] == 'test'
        assert channel['meta']['topic_time']
        assert channel['meta']['topic_author'] == 'john_doe'

    def test_checkIfValidEmail(self):
        email = "validemail@email.com"

        self.db.checkIfValidEmail(email)

    def test_checkIfValidNickname(self):
        nickname = "valid2013"

        self.db.checkIfValidNickname(nickname)

    def test_checkIfValidPassword(self):
        password = "goodPassword2"

        self.db.checkIfValidPassword(password)

    def test_heartbeatsUserSession(self):
        result = self.db.heartbeatUserSession("test_user")
        assert result["inserted"] == 1

        result = self.db.heartbeatUserSession("test_user")
        assert result["replaced"] == 1

    def test_heartbeatUserInGroup(self):
        # Creates initial heartbeat
        result = self.db.heartbeatUserInGroup("test_user", "test_group")
        group_state = self.db.getGroupState("test_group")

        assert result["inserted"] == 1
        assert group_state["users"].get("test_user")

        # Updates user heartbeat
        result = self.db.heartbeatUserInGroup("test_user", "test_group")
        assert result["replaced"] == 1

        new_group_state = self.db.getGroupState("test_group")
        assert new_group_state["users"]["test_user"] != \
            group_state["users"]["test_user"]

    def test_removeUserFromGroup(self):
        self.db.heartbeatUserInGroup("test_user", "test_group")
        result = self.db.removeUserFromGroup("test_user", "test_group")

        assert result["replaced"] == 1

        group_state = self.db.getGroupState("test_group")
        assert False == group_state["users"].get("test_user",
                                                 False)

    def test_observesGroupStateChanges(self):

        changefeed = self.db.observeGroupState("test_group")
        self.db.heartbeatUserInGroup("john", "test_group")
        self.db.heartbeatUserInGroup("bob", "test_group")

        added_users_change = next(changefeed)
        assert "john" in added_users_change["users"]
        assert "bob" in added_users_change["users"]

        self.db.removeUserFromGroup("john", "test_group")
        removed_user_change = next(changefeed)
        assert "john" not in removed_user_change["users"]
