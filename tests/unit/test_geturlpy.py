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

from udocker.utils.curl import GetURLpyCurl


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class GetURLpyCurlTestCase(unittest.TestCase):
    """GetURLpyCurl TestCase."""

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
    @mock.patch('udocker.utils.curl.GetURLpyCurl')
    def test_01_is_available(self, mock_gupycurl, mock_msg):
        """Test GetURLpyCurl()._is_available()."""
        self._init()
        mock_msg.level = 0
        geturl = GetURLpyCurl()
        geturl.is_available()
        mock_gupycurl.return_value.is_available.return_value = True
        self.assertTrue(geturl.is_available())

        mock_gupycurl.return_value.is_available.return_value = False
        self.assertFalse(geturl.is_available())

    def test_02__select_implementation(self):
        """Test GetURLpyCurl()._select_implementation()."""
        pass

    #    @mock.patch('udocker.GetURLpyCurl._select_implementation')
    #    @mock.patch('udocker.Msg')
    #    @mock.patch('udocker.pycurl')
    #    @mock.patch('udocker.CurlHeader')
    #    def test_03__set_defaults(self, mock_hdr, mock_pyc, mock_msg, mock_sel):
    #        """Test GetURLpyCurl()._set_defaults()."""
    #        self._init()
    #        mock_sel.return_value.insecure.return_value = True
    #        geturl = udocker.GetURLpyCurl()
    #        geturl._set_defaults(mock_pyc, mock_hdr)
    #        self.assertTrue(mock_pyc.setopt.called)
    #
    #        # when Msg.level >= Msg.DBG: AND insecure
    #        mock_msg.DBG.return_value = 3
    #        mock_msg.level.return_value = 3
    #        geturl._set_defaults(mock_pyc, mock_hdr)
    #        self.assertEqual(mock_pyc.setopt.call_count, 18)
    #
    #        mock_sel.return_value.insecure.return_value = True
    #
    #        # when Msg.level < Msg.DBG: AND secure
    #        mock_msg.DBG.return_value = 3
    #        mock_msg.level.return_value = 2
    #        geturl._set_defaults(mock_pyc, mock_hdr)
    #        self.assertEqual(mock_pyc.setopt.call_count, 27)
    #
    #    @mock.patch('udocker.GetURLpyCurl._select_implementation')
    #    @mock.patch('udocker.Msg')
    #    @mock.patch('udocker.pycurl')
    #    @mock.patch('udocker.CurlHeader')
    #    def test_04__mkpycurl(self, mock_hdr, mock_pyc, mock_msg, mock_sel):
    #        """Test GetURL()._mkpycurl()."""
    #        self._init()
    #        mock_sel.return_value.insecure.return_value = True
    #        geturl = udocker.GetURLpyCurl()
    #        geturl._set_defaults(mock_pyc, mock_hdr)
    #        self.assertTrue(mock_pyc.setopt.called)
    #
    #        # WIP(...)

    @mock.patch('udocker.utils.curl.GetURLpyCurl._select_implementation')
    def test_05_get(self, mock_sel):
        """Test GetURLpyCurl().get() generic get."""
        self._init()
        #
        geturl = GetURLpyCurl()
        geturl._geturl = type('test', (object,), {})()
        geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")
