#!/usr/bin/env python2
"""
udocker unit tests.
Unit tests for udocker, a wrapper to execute basic docker containers
without using docker.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
import pwd
import grp
import unittest
import mock
from StringIO import StringIO

sys.path.append('.')

from udocker.helper.nixauth import NixAuthentication

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class NixAuthenticationTestCase(unittest.TestCase):
    """Test NixAuthentication() *nix authentication portably."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        pass

    def test_01_init(self):
        """Test NixAuthentication() constructor."""
        self._init()
        auth = NixAuthentication()
        self.assertEqual(auth.passwd_file, None)
        self.assertEqual(auth.group_file, None)
        #
        auth = NixAuthentication("passwd", "group")
        self.assertEqual(auth.passwd_file, "passwd")
        self.assertEqual(auth.group_file, "group")

    @mock.patch('pwd.getpwnam')
    @mock.patch('pwd.getpwuid')
    def test_01__get_user_from_host(self, mock_getpwuid, mock_getpwnam):
        """Test NixAuthentication()._get_user_from_host()."""
        self._init()
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
        #
        mock_getpwnam.return_value = usr
        auth = NixAuthentication()
        (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host("root")
        self.assertEqual(name, usr.pw_name)
        self.assertEqual(uid, usr.pw_uid)
        self.assertEqual(gid, str(usr.pw_gid))
        self.assertEqual(gecos, usr.pw_gecos)
        self.assertEqual(_dir, usr.pw_dir)

    # TODO: (mdavid) review test
    @mock.patch('grp.getgrnam')
    @mock.patch('grp.getgrgid')
    def test_02__get_group_from_host(self, mock_grgid, mock_grname):
        """Test NixAuthentication()._get_group_from_host()."""
        self._init()
        hgr = grp.struct_group(["root", "*", "0", str([])])
        mock_grgid.return_value = hgr
        auth = NixAuthentication()
        (name, gid, mem) = auth._get_group_from_host(0)
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)
        #
        mock_grname.return_value = hgr
        auth = NixAuthentication()
        (name, gid, mem) = auth._get_group_from_host("root")
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)

    def test_03__get_user_from_file(self):
        """Test NixAuthentication()._get_user_from_file()."""
        self._init()
        auth = NixAuthentication()
        auth.passwd_file = "passwd"
        passwd_line = StringIO('root:x:0:0:root:/root:/bin/bash')
        with mock.patch(BUILTINS + '.open') as mopen:
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
        with mock.patch(BUILTINS + '.open') as mopen:
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

    def test_04__get_group_from_file(self):
        """Test NixAuthentication()._get_group_from_file()."""
        self._init()
        auth = NixAuthentication()
        auth.passwd_file = "passwd"
        group_line = StringIO('root:x:0:a,b,c')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(group_line.readline, ''))
            (name, gid, mem) = auth._get_group_from_file("root")
            self.assertEqual(name, "root")
            self.assertEqual(gid, "0")
            self.assertEqual(mem, "a,b,c")

        group_line = StringIO('root:x:0:a,b,c')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(group_line.readline, ''))
            (name, gid, mem) = auth._get_group_from_file(0)
            self.assertEqual(name, "root")
            self.assertEqual(gid, "0")
            self.assertEqual(mem, "a,b,c")

    def test_05_add_user(self):
        """Test NixAuthentication().add_user()."""
        self._init()
        auth = NixAuthentication()
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = auth.add_user("root", "pw", 0, 0, "gecos",
                                   "/home", "/bin/bash")
            self.assertTrue(status)

    def test_06_add_group(self):
        """Test NixAuthentication().add_group()."""
        self._init()
        auth = NixAuthentication()
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = auth.add_group("root", 0)
            self.assertTrue(status)

    @mock.patch('udocker.helper.nixauth.NixAuthentication._get_user_from_host')
    @mock.patch('udocker.helper.nixauth.NixAuthentication._get_user_from_file')
    def test_07_get_user(self, mock_file, mock_host):
        """Test NixAuthentication().get_user()."""
        self._init()
        auth = NixAuthentication()
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

    @mock.patch('udocker.helper.nixauth.NixAuthentication._get_group_from_host')
    @mock.patch('udocker.helper.nixauth.NixAuthentication._get_group_from_file')
    def test_08_get_group(self, mock_file, mock_host):
        """Test NixAuthentication().get_group()."""
        self._init()
        auth = NixAuthentication()
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
    unittest.main()
