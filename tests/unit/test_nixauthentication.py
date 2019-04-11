#!/usr/bin/env python2
"""
udocker unit tests: NixAuthentication
"""
import sys
import pwd
import grp
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

sys.path.append('.')

from udocker.helper.nixauth import NixAuthentication
from udocker.config import Config

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


class NixAuthenticationTestCase(TestCase):
    """Test NixAuthentication() *nix authentication portably."""

    def _init(self):
        """Configure variables."""
        self.conf = Config().getconf()

    def test_01_init(self):
        """Test NixAuthentication() constructor."""
        self._init()
        auth = NixAuthentication(self.conf)
        self.assertEqual(auth.passwd_file, None)
        self.assertEqual(auth.group_file, None)
        #
        auth = NixAuthentication(self.conf, "passwd", "group")
        self.assertEqual(auth.passwd_file, "passwd")
        self.assertEqual(auth.group_file, "group")

    @patch('udocker.helper.nixauth.pwd.getpwnam')
    @patch('udocker.helper.nixauth.pwd.getpwuid')
    def test_02__get_user_from_host(self, mock_getpwuid, mock_getpwnam):
        """Test NixAuthentication()._get_user_from_host()."""
        self._init()
        usr = pwd.struct_passwd(["root", "*", "0", "0", "root usr",
                                 "/root", "/bin/bash"])
        mock_getpwuid.return_value = usr
        auth = NixAuthentication(self.conf)
        (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host(0)
        self.assertEqual(name, usr.pw_name)
        self.assertEqual(uid, usr.pw_uid)
        self.assertEqual(gid, str(usr.pw_gid))
        self.assertEqual(gecos, usr.pw_gecos)
        self.assertEqual(_dir, usr.pw_dir)
        self.assertEqual(shell, usr.pw_shell)
        #
        mock_getpwnam.return_value = usr
        auth = NixAuthentication(self.conf)
        (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host("root")
        self.assertEqual(name, usr.pw_name)
        self.assertEqual(uid, usr.pw_uid)
        self.assertEqual(gid, str(usr.pw_gid))
        self.assertEqual(gecos, usr.pw_gecos)
        self.assertEqual(_dir, usr.pw_dir)

    # TODO: (mdavid) review test
    @patch('udocker.helper.nixauth.grp.getgrnam')
    @patch('udocker.helper.nixauth.grp.getgrgid')
    def test_03__get_group_from_host(self, mock_grgid, mock_grname):
        """Test NixAuthentication()._get_group_from_host()."""
        self._init()
        hgr = grp.struct_group(["root", "*", "0", str([])])
        mock_grgid.return_value = hgr
        auth = NixAuthentication(self.conf)
        (name, gid, mem) = auth._get_group_from_host(0)
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)
        #
        mock_grname.return_value = hgr
        auth = NixAuthentication(self.conf)
        (name, gid, mem) = auth._get_group_from_host("root")
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)

    def test_04__get_user_from_file(self):
        """Test NixAuthentication()._get_user_from_file()."""
        self._init()
        auth = NixAuthentication(self.conf)
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
            #
        passwd_line = StringIO('root:x:0:0:root:/root:/bin/bash')
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

    def test_05__get_group_from_file(self):
        """Test NixAuthentication()._get_group_from_file()."""
        self._init()
        auth = NixAuthentication(self.conf)
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
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(group_line.readline, ''))
            (name, gid, mem) = auth._get_group_from_file(0)
            self.assertEqual(name, "root")
            self.assertEqual(gid, "0")
            self.assertEqual(mem, "a,b,c")

    def test_06_add_user(self):
        """Test NixAuthentication().add_user()."""
        self._init()
        auth = NixAuthentication(self.conf)
        with patch(BUILTINS + '.open', mock_open()):
            status = auth.add_user("root", "pw", 0, 0, "gecos",
                                   "/home", "/bin/bash")
            self.assertTrue(status)

    def test_07_add_group(self):
        """Test NixAuthentication().add_group()."""
        self._init()
        auth = NixAuthentication(self.conf)
        with patch(BUILTINS + '.open', mock_open()):
            status = auth.add_group("root", 0)
            self.assertTrue(status)

    @patch('udocker.helper.nixauth.NixAuthentication._get_user_from_host')
    @patch('udocker.helper.nixauth.NixAuthentication._get_user_from_file')
    def test_08_get_user(self, mock_file, mock_host):
        """Test NixAuthentication().get_user()."""
        self._init()
        auth = NixAuthentication(self.conf)
        auth.passwd_file = ""
        auth.get_user("user")
        self.assertTrue(mock_host.called)
        self.assertFalse(mock_file.called)
        #
        mock_host.reset_mock()
        mock_file.reset_mock()
        auth.passwd_file = "passwd"
        auth.get_user("user")
        self.assertFalse(mock_host.called)
        self.assertTrue(mock_file.called)

    @patch('udocker.helper.nixauth.NixAuthentication._get_group_from_host')
    @patch('udocker.helper.nixauth.NixAuthentication._get_group_from_file')
    def test_09_get_group(self, mock_file, mock_host):
        """Test NixAuthentication().get_group()."""
        self._init()
        auth = NixAuthentication(self.conf)
        auth.group_file = ""
        auth.get_group("group")
        self.assertTrue(mock_host.called)
        self.assertFalse(mock_file.called)
        #
        mock_host.reset_mock()
        mock_file.reset_mock()
        auth.group_file = "group"
        auth.get_group("group")
        self.assertFalse(mock_host.called)
        self.assertTrue(mock_file.called)


if __name__ == '__main__':
    main()
