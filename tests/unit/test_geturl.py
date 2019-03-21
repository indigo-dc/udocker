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

from udocker.utils.curl import GetURL
from udocker.config import Config


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class GetURLTestCase(unittest.TestCase):
    """Test GetURL() perform http operations portably."""

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
        Config.use_curl_executable = ""

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.utils.curl.GetURL._select_implementation')
    def test_01_init(self, mock_simplement, mock_msg):
        """Test GetURL() constructor."""
        self._init()
        mock_msg.level = 0
        geturl = GetURL()
        self.assertEqual(geturl.ctimeout, Config.ctimeout)
        self.assertEqual(geturl.insecure, Config.http_insecure)
        self.assertEqual(geturl.cache_support, False)

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.utils.curl.GetURLexeCurl')
    @mock.patch('udocker.utils.curl.GetURLpyCurl')
    def test_02__select_implementation(self, mock_gupycurl, mock_guexecurl, mock_msg):
        """Test GetURL()._select_implementation()."""
        self._init()
        mock_msg.level = 0
        mock_gupycurl.return_value.is_available.return_value = True
        geturl = GetURL()
        geturl._select_implementation()
        self.assertEqual(geturl.cache_support, True)
        #
        mock_gupycurl.return_value.is_available.return_value = False
        geturl = GetURL()
        geturl._select_implementation()
        self.assertEqual(geturl.cache_support, False)
        #
        mock_guexecurl.return_value.is_available.return_value = False
        with self.assertRaises(NameError):
            GetURL()

    @mock.patch('udocker.utils.curl.GetURL._select_implementation')
    def test_03_get_content_length(self, mock_sel):
        """Test GetURL().get_content_length()."""
        self._init()
        geturl = GetURL()
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10, }
        self.assertEqual(geturl.get_content_length(hdr), 10)
        hdr.data = {"content-length": dict(), }
        self.assertEqual(geturl.get_content_length(hdr), -1)

    @mock.patch('udocker.utils.curl.GetURLpyCurl')
    def test_04_set_insecure(self, mock_gupycurl):
        """Test GetURL().set_insecure()."""
        self._init()
        mock_gupycurl.return_value.is_available.return_value = True
        geturl = GetURL()
        geturl.set_insecure()
        self.assertEqual(geturl.insecure, True)
        #
        geturl.set_insecure(False)
        self.assertEqual(geturl.insecure, False)

    @mock.patch('udocker.utils.curl.GetURLpyCurl')
    def test_05_set_proxy(self, mock_gupycurl):
        """Test GetURL().set_proxy()."""
        self._init()
        mock_gupycurl.return_value.is_available.return_value = True
        geturl = GetURL()
        geturl.set_proxy("http://host")
        self.assertEqual(geturl.http_proxy, "http://host")

    @mock.patch('udocker.utils.curl.GetURL._select_implementation')
    def test_06_get(self, mock_sel):
        """Test GetURL().get() generic get."""
        self._init()
        geturl = GetURL()
        self.assertRaises(TypeError, geturl.get)
        #
        geturl = GetURL()
        geturl._geturl = type('test', (object,), {})()
        geturl._geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")

    @mock.patch('udocker.utils.curl.GetURL._select_implementation')
    def test_07_post(self, mock_sel):
        """Test GetURL().post() generic post."""
        self._init()
        geturl = GetURL()
        self.assertRaises(TypeError, geturl.post)
        self.assertRaises(TypeError, geturl.post, "http://host")
        #
        geturl = GetURL()
        geturl._geturl = type('test', (object,), {})()
        geturl._geturl.get = self._get
        self.assertEqual(geturl.post("http://host",
                                     {"DATA": 1, }), "http://host")
