#!/usr/bin/env python
"""
udocker unit tests: NixAuthentication
"""
import pwd
import grp
from udocker.helper.nixauth import NixAuthentication


def test_01_user_in_subuid(mocker):
    """Test01 NixAuthentication().user_in_subuid."""
    sub_file = ("user1:100000:65536\n"
                "user2:165536:65536")
    uinfo = ("user2", "1000", "1000", "usr", "/home/user", "/bin/bash")
    mock_file = mocker.mock_open(read_data=sub_file)
    mocker.patch("builtins.open", mock_file)
    mock_userfile = mocker.patch.object(NixAuthentication, '_get_user_from_file',
                                        return_value=uinfo)
    mock_userhost = mocker.patch.object(NixAuthentication, '_get_user_from_host')

    auth = NixAuthentication(passwd_file='/etc/passwd', group_file='/etc/group',
                             subuid_file=sub_file)
    out = auth.user_in_subuid('user2')
    assert out == [("165536", "65536")]
    mock_file.assert_called()
    mock_userfile.assert_called()
    mock_userhost.assert_not_called()


def test_02_user_in_subuid(mocker):
    """Test02 NixAuthentication().user_in_subuid."""
    sub_file = ("user1:100000:65536\n"
                "user2:165536:65536")
    uinfo = ("user2", "1000", "1000", "usr", "/home/user", "/bin/bash")
    mock_file = mocker.mock_open(read_data=sub_file)
    mocker.patch("builtins.open", mock_file)
    mock_userfile = mocker.patch.object(NixAuthentication, '_get_user_from_file')
    mock_userhost = mocker.patch.object(NixAuthentication, '_get_user_from_host',
                                        return_value=uinfo)

    auth = NixAuthentication(subuid_file=sub_file)
    out = auth.user_in_subuid('user2')
    assert out == [("165536", "65536")]
    mock_file.assert_called()
    mock_userfile.assert_not_called()
    mock_userhost.assert_called()


def test_03_user_in_subuid(mocker):
    """Test03 NixAuthentication().user_in_subuid."""
    uinfo = ("user2", "1000", "1000", "usr", "/home/user", "/bin/bash")
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    mock_userfile = mocker.patch.object(NixAuthentication, '_get_user_from_file')
    mock_userhost = mocker.patch.object(NixAuthentication, '_get_user_from_host',
                                        return_value=uinfo)

    auth = NixAuthentication()
    out = auth.user_in_subuid('user2')
    assert out == []
    mock_userfile.assert_not_called()
    mock_userhost.assert_called()


def test_04_user_in_subgid(mocker):
    """Test04 NixAuthentication().user_in_subgid."""
    mock_subid = mocker.patch.object(NixAuthentication, '_user_in_subid',
                                     return_value=[("165536", "65536")])

    auth = NixAuthentication()
    out = auth.user_in_subgid('user2')
    assert out == [("165536", "65536")]
    mock_subid.assert_called()


def test_09_add_user(mocker):
    """Test09 NixAuthentication().add_user()."""
    uinfo = "root:pw:0:0:gecos:/home:/bin/bash\n"
    mock_get = mocker.patch('udocker.helper.nixauth.FileUtil.getdata', return_value=uinfo)
    mock_put = mocker.patch('udocker.helper.nixauth.FileUtil.putdata')

    auth = NixAuthentication()
    out = auth.add_user("root", "pw", 0, 0, "gecos", "/home", "/bin/bash")
    assert out
    mock_get.assert_called()
    mock_put.assert_not_called()


def test_10_add_user(mocker):
    """Test10 NixAuthentication().add_user()."""
    uget = "user:upw:1000:1000:gecos:/home/user:/bin/bash\n"
    uput = "root:pw:0:0:gecos:/home:/bin/bash\n"
    mock_get = mocker.patch('udocker.helper.nixauth.FileUtil.getdata', return_value=uget)
    mock_put = mocker.patch('udocker.helper.nixauth.FileUtil.putdata', return_value=uput)

    auth = NixAuthentication()
    out = auth.add_user("root", "pw", 0, 0, "gecos", "/home", "/bin/bash")
    assert out == uput
    mock_get.assert_called()
    mock_put.assert_called()


def test_11_add_group(mocker):
    """Test11 NixAuthentication().add_group()."""
    uinfo = "group1:x:1001:user1,user2,\n"
    mock_get = mocker.patch('udocker.helper.nixauth.FileUtil.getdata', return_value=uinfo)
    mock_put = mocker.patch('udocker.helper.nixauth.FileUtil.putdata')

    auth = NixAuthentication()
    out = auth.add_group("group1", 1001, users=["user1", "user2"])
    assert out
    mock_get.assert_called()
    mock_put.assert_not_called()


def test_12_add_group(mocker):
    """Test12 NixAuthentication().add_group()."""
    uget = "group1:x:1001:user1,user2,\n"
    uput = "group2:x:1002:user3,user4,\n"
    mock_get = mocker.patch('udocker.helper.nixauth.FileUtil.getdata', return_value=uget)
    mock_put = mocker.patch('udocker.helper.nixauth.FileUtil.putdata', return_value=uput)

    auth = NixAuthentication()
    out = auth.add_group("group2", 1002, users=["user3", "user4"])
    assert out == uput
    mock_get.assert_called()
    mock_put.assert_called()


# @patch('udocker.helper.nixauth.pwd.getpwnam')
# @patch('udocker.helper.nixauth.pwd.getpwuid')
# def test_05__get_user_from_host(self, mock_getpwuid, mock_getpwnam):
#     """Test05 NixAuthentication()._get_user_from_host()."""
#     usr = pwd.struct_passwd(["root", "*", "0", "0", "root usr", "/root", "/bin/bash"])
#     mock_getpwuid.return_value = usr
#     auth = NixAuthentication()
#     (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host(0)
#     self.assertEqual(name, usr.pw_name)
#     self.assertEqual(uid, usr.pw_uid)
#     self.assertEqual(gid, str(usr.pw_gid))
#     self.assertEqual(gecos, usr.pw_gecos)
#     self.assertEqual(_dir, usr.pw_dir)
#     self.assertEqual(shell, usr.pw_shell)

#     mock_getpwnam.return_value = usr
#     auth = NixAuthentication()
#     (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host("root")
#     self.assertEqual(name, usr.pw_name)
#     self.assertEqual(uid, usr.pw_uid)
#     self.assertEqual(gid, str(usr.pw_gid))
#     self.assertEqual(gecos, usr.pw_gecos)
#     self.assertEqual(_dir, usr.pw_dir)

#     mock_getpwuid.side_effect = IOError("fail")
#     auth = NixAuthentication()
#     self.assertEqual(auth._get_user_from_host(0), ("", "", "", "", "", ""))

#     mock_getpwnam.side_effect = IOError("fail")
#     auth = NixAuthentication()
#     self.assertEqual(auth._get_user_from_host("root"), ("", "", "", "", "", ""))

# @patch('udocker.helper.nixauth.grp.getgrnam')
# @patch('udocker.helper.nixauth.grp.getgrgid')
# def test_06__get_group_from_host(self, mock_grgid, mock_grname):
#     """Test06 NixAuthentication()._get_group_from_host()."""
#     hgr = grp.struct_group(["root", "*", "0", str([])])
#     mock_grgid.return_value = hgr
#     auth = NixAuthentication()
#     (name, gid, mem) = auth._get_group_from_host(0)
#     self.assertEqual(name, hgr.gr_name)
#     self.assertEqual(gid, str(hgr.gr_gid))
#     self.assertEqual(mem, hgr.gr_mem)

#     mock_grname.return_value = hgr
#     auth = NixAuthentication()
#     (name, gid, mem) = auth._get_group_from_host("root")
#     self.assertEqual(name, hgr.gr_name)
#     self.assertEqual(gid, str(hgr.gr_gid))
#     self.assertEqual(mem, hgr.gr_mem)

#     mock_grgid.side_effect = IOError("fail")
#     auth = NixAuthentication()
#     self.assertEqual(auth._get_group_from_host(0), ("", "", ""))

#     mock_grname.side_effect = IOError("fail")
#     auth = NixAuthentication()
#     self.assertEqual(auth._get_group_from_host("root"), ("", "", ""))

# def test_07__get_user_from_file(self):
#     """Test07 NixAuthentication()._get_user_from_file()."""
#     auth = NixAuthentication()
#     auth.passwd_file = "passwd"
#     passwd_line = StringIO('root:x:0:0:root:/root:/bin/bash')
#     with patch(BUILTINS + '.open') as mopen:
#         mopen.return_value.__iter__ = (lambda self: iter(passwd_line.readline, ''))
#         (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_file("root")
#         self.assertEqual(name, "root")
#         self.assertEqual(uid, "0")
#         self.assertEqual(gid, "0")
#         self.assertEqual(gecos, "root")
#         self.assertEqual(_dir, "/root")
#         self.assertEqual(shell, "/bin/bash")

#     passwd_line = StringIO('root:x:0:0:root:/root:/bin/bash')
#     auth = NixAuthentication()
#     with patch(BUILTINS + '.open') as mopen:
#         mopen.return_value.__iter__ = (lambda self: iter(passwd_line.readline, ''))
#         (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_file(0)
#         self.assertEqual(name, "root")
#         self.assertEqual(uid, "0")
#         self.assertEqual(gid, "0")
#         self.assertEqual(gecos, "root")
#         self.assertEqual(_dir, "/root")
#         self.assertEqual(shell, "/bin/bash")

#     mock_open.side_effect = OSError("fail")
#     auth = NixAuthentication()
#     auth.passwd_file = ""
#     self.assertEqual(auth._get_user_from_file(0), ("", "", "", "", "", ""))

# def test_08__get_group_from_file(self):
#     """Test08 NixAuthentication()._get_group_from_file()."""
#     auth = NixAuthentication()
#     auth.passwd_file = "passwd"
#     group_line = StringIO('root:x:0:a,b,c')
#     with patch(BUILTINS + '.open') as mopen:
#         mopen.return_value.__iter__ = (lambda self: iter(group_line.readline, ''))
#         (name, gid, mem) = auth._get_group_from_file("root")
#         self.assertEqual(name, "root")
#         self.assertEqual(gid, "0")
#         self.assertEqual(mem, "a,b,c")

#     group_line = StringIO('root:x:0:a,b,c')
#     auth = NixAuthentication()
#     with patch(BUILTINS + '.open') as mopen:
#         mopen.return_value.__iter__ = (lambda self: iter(group_line.readline, ''))
#         (name, gid, mem) = auth._get_group_from_file(0)
#         self.assertEqual(name, "root")
#         self.assertEqual(gid, "0")
#         self.assertEqual(mem, "a,b,c")

#     mock_open.side_effect = IOError("fail")
#     auth = NixAuthentication()
#     auth.group_file = ""
#     self.assertEqual(auth._get_group_from_file(0), ("", "", ""))



# @patch.object(NixAuthentication, '_get_user_from_host')
# @patch.object(NixAuthentication, '_get_user_from_file')
# def test_11_get_user(self, mock_file, mock_host):
#     """Test11 NixAuthentication().get_user()."""
#     auth = NixAuthentication()
#     auth.passwd_file = ""
#     auth.get_user("user")
#     self.assertTrue(mock_host.called)
#     self.assertFalse(mock_file.called)

#     mock_host.reset_mock()
#     mock_file.reset_mock()
#     auth = NixAuthentication()
#     auth.passwd_file = "passwd"
#     auth.get_user("user")
#     self.assertFalse(mock_host.called)
#     self.assertTrue(mock_file.called)

# @patch.object(NixAuthentication, '_get_group_from_host')
# @patch.object(NixAuthentication, '_get_group_from_file')
# def test_12_get_group(self, mock_file, mock_host):
#     """Test12 NixAuthentication().get_group()."""
#     auth = NixAuthentication()
#     auth.group_file = ""
#     auth.get_group("group")
#     self.assertTrue(mock_host.called)
#     self.assertFalse(mock_file.called)

#     mock_host.reset_mock()
#     mock_file.reset_mock()
#     auth = NixAuthentication()
#     auth.group_file = "group"
#     auth.get_group("group")
#     self.assertFalse(mock_host.called)
#     self.assertTrue(mock_file.called)

# @patch('udocker.helper.nixauth.HostInfo')
# @patch.object(NixAuthentication, 'get_user')
# def test_13_get_home(self, mock_user, mock_hinfo):
#     """Test13 NixAuthentication().get_home()."""
#     mock_user.return_value = ('root', '0', '0', 'root', '/root', '/bin/bash')
#     mock_hinfo.uid = 0
#     auth = NixAuthentication()
#     status = auth.get_home()
#     self.assertEqual(status, '/root')

#     mock_user.return_value = ('', '', '', '', '', '')
#     mock_hinfo.uid = None
#     auth = NixAuthentication()
#     status = auth.get_home()
#     self.assertEqual(status, '')
