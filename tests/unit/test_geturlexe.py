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
import unittest
import mock

from udocker.utils.curl import GetURLexeCurl
from udocker.config import Config


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class GetURLexeCurlTestCase(unittest.TestCase):
    """GetURLexeCurl TestCase."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        Config = mock.patch('udocker.config.Config').start()
        Config.timeout = 1
        Config.ctimeout = 1
        Config.download_timeout = 1
        Config.http_agent = ""
        Config.http_proxy = ""
        Config.http_insecure = 0

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.utils.curl.GetURL')
    def test_01_init(self, mock_gcurl, mock_msg):
        """Test GetURLexeCurl().__init__()."""
        self._init()
        self.assertIsNone(GetURLexeCurl()._opts)
        self.assertIsNone(GetURLexeCurl()._files)

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.utils.curl.GetURLexeCurl._select_implementation')
    def test_02_is_available(self, mock_sel, mock_futil, mock_msg):
        """Test GetURLexeCurl()._is_available()."""
        self._init()
        mock_msg.level = 0
        geturl = GetURLexeCurl()
        mock_futil.return_value.find_exec.return_value = "/tmp"
        self.assertTrue(geturl.is_available())

        mock_futil.return_value.find_exec.return_value = ""
        self.assertFalse(geturl.is_available())

    def test_03__select_implementation(self):
        """Test GetURLexeCurl()._select_implementation()."""
        pass

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.utils.curl.GetURLexeCurl._select_implementation')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    def test_04__set_defaults(self, mock_sel, mock_futil, mock_msg):
        """Set defaults for curl command line options"""
        self._init()
        geturl = GetURLexeCurl()
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], "")

        geturl.insecure = True
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], "-k")

        mock_msg.DBG = 0
        mock_msg.level = 1
        geturl._set_defaults()
        # self.assertEqual(geturl._opts["verbose"], "-v")

        self.assertEqual(geturl._files["url"], "")

    def test_05__mkcurlcmd(self):
        """Test GetURLexeCurl()._mkcurlcmd()."""
        pass

    @mock.patch('udocker.utils.curl.GetURLexeCurl._select_implementation')
    def test_06_get(self, mock_sel):
        """Test GetURLexeCurl().get() generic get."""
        self._init()
        #
        geturl = GetURLexeCurl()
        geturl._geturl = type('test', (object,), {})()
        geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")
