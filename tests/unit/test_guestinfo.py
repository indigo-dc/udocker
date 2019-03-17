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
import unittest
import mock

sys.path.append('../../')

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from udocker.helper.guestinfo import GuestInfo

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()

class GuestInfoTestCase(unittest.TestCase):
    """Test GuestInfo() class."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Common variables."""
        self.rootdir = "~/.udocker/container/abcd0/ROOT"
        self.file = "/bin/ls"
        self.ftype = "/bin/ls: yyy, x86-64, xxx"
        self.nofile = "ddd: cannot open"
        self.osdist = ("Ubuntu", "16.04")
        self.noosdist = ("", "xx")

    def test_01_init(self):
        """Test GuestInfo() constructor."""
        self._init()
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo._root_dir, self.rootdir)

    @mock.patch('udocker.utils.uprocess.Uprocess.get_output')
    @mock.patch('os.path.isfile')
    def test_02_get_filetype(self, mock_isfile, mock_getout):
        """Test GuestInfo.get_filetype(filename)"""
        self._init()
        # full filepath exists
        mock_isfile.return_value = True
        mock_getout.return_value = self.ftype
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo.get_filetype(self.file), self.ftype)
        # file does not exist
        mock_isfile.return_value = False
        mock_getout.return_value = self.nofile
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo.get_filetype(self.nofile), "")

#    @mock.patch('udocker.Uprocess.get_output')
#    @mock.patch('udocker.GuestInfo')
#    @mock.patch('udocker.GuestInfo._binarylist')
#    def test_03_arch(self, mock_binlist, mock_gi, mock_getout):
#        """Test GuestInfo.arch()"""
#        self._init()
#        # arch is x86_64
#        mock_binlist.return_value = ["/bin/bash", "/bin/ls"]
#        mock_getout.return_value.get_filetype.side_effect = [self.ftype, self.ftype]
#        ginfo = udocker.GuestInfo(self.rootdir)
#        self.assertEqual(ginfo.arch(), "amd64")

    # @mock.patch('udocker.os.path.exists')
    # @mock.patch('udocker.FileUtil.match')
    # @mock.patch('udocker.FileUtil.getdata')
    # def test_04_osdistribution(self, mock_gdata, mock_match, mock_exists):
    #     """Test GuestInfo.osdistribution()"""
    #     self._init()
    #     # has osdistro
    #     self.lsbdata = "DISTRIB_ID=Ubuntu\n" \
    #                    "DISTRIB_RELEASE=16.04\n" \
    #                    "DISTRIB_CODENAME=xenial\n" \
    #                    "DISTRIB_DESCRIPTION=Ubuntu 16.04.5 LTS\n"
    #     mock_match.return_value = ["/etc/lsb-release"]
    #     mock_exists.return_value = True
    #     mock_gdata.return_value = self.lsbdata
    #     ginfo = udocker.GuestInfo(self.rootdir)
    #     self.assertEqual(ginfo.osdistribution(), self.osdist)

    @mock.patch('udocker.helper.guestinfo.GuestInfo.osdistribution')
    def test_05_osversion(self, mock_osdist):
        """Test GuestInfo.osversion()"""
        self._init()
        # has osdistro
        mock_osdist.return_value = self.osdist
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo.osversion(), "linux")
        # has no osdistro
        mock_osdist.return_value = self.noosdist
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo.osversion(), "")

