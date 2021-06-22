#!/usr/bin/env python
"""
udocker unit tests: NixAuthentication
"""

import pwd
import grp
from unittest import TestCase, main
from unittest.mock import patch, mock_open
from io import StringIO
from udocker.helper.nixauth import NixAuthentication
from udocker.config import Config

BUILTINS = "builtins"


class NixAuthenticationTestCase(TestCase):
    """Test NixAuthentication() *nix authentication portably."""

    def setUp(self):
        Config().getconf()

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test01 NixAuthentication() constructor."""
        auth = NixAuthentication()
        self.assertEqual(auth.passwd_file, None)
        self.assertEqual(auth.group_file, None)

        auth = NixAuthentication("passwd", "group")
        self.assertEqual(auth.passwd_file, "passwd")
        self.assertEqual(auth.group_file, "group")

    # def test_02__user_in_subid(self):
    #     """Test02 NixAuthentication()._user_in_subid."""

    @patch.object(NixAuthentication, '_get_user_from_host')
    @patch.object(NixAuthentication, '_get_user_from_file')
    def test_03_user_in_subuid(self, mock_file, mock_host):
        """Test03 NixAuthentication().user_in_subuid."""
        mock_host.return_value = ("user", "1000", "1000", "usr",
                                  "/home/user", "/bin/bash")
        auth = NixAuthentication()
        auth.subuid_file = "/etc/subuid"
        subuid_line = StringIO('user:100000:65536')
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(subuid_line.readline, ''))
            listuser = auth.user_in_subuid("user")
            self.assertEqual(listuser, [("100000", "65536")])
            self.assertTrue(mock_host.called)

        mock_file.return_value = ("user", "1000", "1000", "usr",
                                  "/home/user", "/bin/bash")
        auth = NixAuthentication()
        auth.passwd_file = "/etc/passwd"
        auth.subuid_file = "/etc/subuid"
        subuid_line = StringIO('user:100000:65536')
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(subuid_line.readline, ''))
            listuser = auth.user_in_subuid("user")
            self.assertEqual(listuser, [("100000", "65536")])
            self.assertTrue(mock_file.called)

    @patch.object(NixAuthentication, '_get_user_from_host')
    @patch.object(NixAuthentication, '_get_user_from_file')
    def test_04_user_in_subgid(self, mock_file, mock_host):
        """Test04 NixAuthentication().user_in_subgid."""
        mock_host.return_value = ("user", "1000", "1000", "usr",
                                  "/home/user", "/bin/bash")
        auth = NixAuthentication()
        auth.subuid_file = "/etc/subgid"
        subgid_line = StringIO('user:100000:65536')
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(subgid_line.readline, ''))
            listuser = auth.user_in_subgid("user")
            self.assertEqual(listuser, [("100000", "65536")])
            self.assertTrue(mock_host.called)

        mock_file.return_value = ("user", "1000", "1000", "usr",
                                  "/home/user", "/bin/bash")
        auth = NixAuthentication()
        auth.passwd_file = "/etc/passwd"
        auth.subgid_file = "/etc/subgid"
        subgid_line = StringIO('user:100000:65536')
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(subgid_line.readline, ''))
            listuser = auth.user_in_subgid("user")
            self.assertEqual(listuser, [("100000", "65536")])
            self.assertTrue(mock_file.called)

    @patch('udocker.helper.nixauth.pwd.getpwnam')
    @patch('udocker.helper.nixauth.pwd.getpwuid')
    def test_05__get_user_from_host(self, mock_getpwuid, mock_getpwnam):
        """Test05 NixAuthentication()._get_user_from_host()."""
        usr = pwd.struct_passwd(["root", "*", "0", "0", "root usr",
                                 "/root", "/bin/bash"])
        mock_getpwuid.return_value = usr
        auth = NixAuthentication()
        (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host(0)
        self.assertEqual(name, usr.pw_name)
        self.assertEqual(uid, usr.pw_uid)
        self.assertEqual(gid, str(usr.pw_gid))
        self.assertEqual(gecos, usr.pw_gecos)
        self.assertEqual(_dir, usr.pw_dir)
        self.assertEqual(shell, usr.pw_shell)

        mock_getpwnam.return_value = usr
        auth = NixAuthentication()
        (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host("root")
        self.assertEqual(name, usr.pw_name)
        self.assertEqual(uid, usr.pw_uid)
        self.assertEqual(gid, str(usr.pw_gid))
        self.assertEqual(gecos, usr.pw_gecos)
        self.assertEqual(_dir, usr.pw_dir)

    # TODO: (mdavid) review test
    @patch('udocker.helper.nixauth.grp.getgrnam')
    @patch('udocker.helper.nixauth.grp.getgrgid')
    def test_06__get_group_from_host(self, mock_grgid, mock_grname):
        """Test06 NixAuthentication()._get_group_from_host()."""
        hgr = grp.struct_group(["root", "*", "0", str([])])
        mock_grgid.return_value = hgr
        auth = NixAuthentication()
        (name, gid, mem) = auth._get_group_from_host(0)
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)

        mock_grname.return_value = hgr
        auth = NixAuthentication()
        (name, gid, mem) = auth._get_group_from_host("root")
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)

    def test_07__get_user_from_file(self):
        """Test07 NixAuthentication()._get_user_from_file()."""
        auth = NixAuthentication()
        auth.passwd_file = "passwd"
        passwd_line = StringIO('root:x:0:0:root:/root:/bin/bash')
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(passwd_line.readline, ''))
            (name, uid, gid,
             gecos, _dir, shell) = auth._get_user_from_file("root")
            self.assertEqual(name, "root")
            self.assertEqual(uid, "0")
            self.assertEqual(gid, "0")
            self.assertEqual(gecos, "root")
            self.assertEqual(_dir, "/root")
            self.assertEqual(shell, "/bin/bash")

        passwd_line = StringIO('root:x:0:0:root:/root:/bin/bash')
        auth = NixAuthentication()
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(passwd_line.readline, ''))
            (name, uid, gid,
             gecos, _dir, shell) = auth._get_user_from_file(0)
            self.assertEqual(name, "root")
            self.assertEqual(uid, "0")
            self.assertEqual(gid, "0")
            self.assertEqual(gecos, "root")
            self.assertEqual(_dir, "/root")
            self.assertEqual(shell, "/bin/bash")

    def test_08__get_group_from_file(self):
        """Test08 NixAuthentication()._get_group_from_file()."""
        auth = NixAuthentication()
        auth.passwd_file = "passwd"
        group_line = StringIO('root:x:0:a,b,c')
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(group_line.readline, ''))
            (name, gid, mem) = auth._get_group_from_file("root")
            self.assertEqual(name, "root")
            self.assertEqual(gid, "0")
            self.assertEqual(mem, "a,b,c")

        group_line = StringIO('root:x:0:a,b,c')
        auth = NixAuthentication()
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(group_line.readline, ''))
            (name, gid, mem) = auth._get_group_from_file(0)
            self.assertEqual(name, "root")
            self.assertEqual(gid, "0")
            self.assertEqual(mem, "a,b,c")

    def test_09_add_user(self):
        """Test09 NixAuthentication().add_user()."""
        auth = NixAuthentication()
        with patch(BUILTINS + '.open', mock_open()):
            status = auth.add_user("root", "pw", 0, 0, "gecos",
                                   "/home", "/bin/bash")
            self.assertTrue(status)

    def test_10_add_group(self):
        """Test10 NixAuthentication().add_group()."""
        auth = NixAuthentication()
        with patch(BUILTINS + '.open', mock_open()):
            status = auth.add_group("root", 0)
            self.assertTrue(status)

    @patch.object(NixAuthentication, '_get_user_from_host')
    @patch.object(NixAuthentication, '_get_user_from_file')
    def test_11_get_user(self, mock_file, mock_host):
        """Test11 NixAuthentication().get_user()."""
        auth = NixAuthentication()
        auth.passwd_file = ""
        auth.get_user("user")
        self.assertTrue(mock_host.called)
        self.assertFalse(mock_file.called)

        mock_host.reset_mock()
        mock_file.reset_mock()
        auth = NixAuthentication()
        auth.passwd_file = "passwd"
        auth.get_user("user")
        self.assertFalse(mock_host.called)
        self.assertTrue(mock_file.called)

    @patch.object(NixAuthentication, '_get_group_from_host')
    @patch.object(NixAuthentication, '_get_group_from_file')
    def test_12_get_group(self, mock_file, mock_host):
        """Test12 NixAuthentication().get_group()."""
        auth = NixAuthentication()
        auth.group_file = ""
        auth.get_group("group")
        self.assertTrue(mock_host.called)
        self.assertFalse(mock_file.called)

        mock_host.reset_mock()
        mock_file.reset_mock()
        auth = NixAuthentication()
        auth.group_file = "group"
        auth.get_group("group")
        self.assertFalse(mock_host.called)
        self.assertTrue(mock_file.called)

    @patch.object(NixAuthentication, 'get_user')
    def test_13_get_home(self, mock_user):
        """Test13 NixAuthentication().get_home()."""
        mock_user.return_value = ('root', '0', '0', 'root',
                                  '/root', '/bin/bash')
        auth = NixAuthentication()
        status = auth.get_home()
        self.assertEqual(status, '/root')


if __name__ == '__main__':
    main()
