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

from udocker.cmdparser import CmdParser


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class CmdParserTestCase(unittest.TestCase):
    """Test CmdParserTestCase() command line interface."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01__init(self):
        """Test CmdParser() Constructor."""

        cmdp = CmdParser()
        self.assertEqual(cmdp._argv, "")
        self.assertIsInstance(cmdp._argv_split, dict)
        self.assertIsInstance(cmdp._argv_consumed_options, dict)
        self.assertIsInstance(cmdp._argv_consumed_params, dict)
        self.assertEqual(cmdp._argv_split['CMD'], "")
        self.assertEqual(cmdp._argv_split['GEN_OPT'], [])
        self.assertEqual(cmdp._argv_split['CMD_OPT'], [])
        self.assertEqual(cmdp._argv_consumed_options['GEN_OPT'], [])
        self.assertEqual(cmdp._argv_consumed_options['CMD_OPT'], [])
        self.assertEqual(cmdp._argv_consumed_params['GEN_OPT'], [])
        self.assertEqual(cmdp._argv_consumed_params['CMD_OPT'], [])

    def test_02_parse(self):
        """Test CmdParser().parse()."""

        cmdp = CmdParser()
        status = cmdp.parse("udocker run --bindhome "
                            "--hostauth --hostenv -v /sys"
                            " -v /proc -v /var/run -v /dev"
                            " --user=jorge --dri myfed  firefox")
        self.assertTrue(status)

    def test_03_missing_options(self):
        """Test CmdParser().missing_options()."""

        cmdp = CmdParser()
        cmdp.parse("udocker run --bindhome "
                   "--hostauth --hostenv -v /sys"
                   " -v /proc -v /var/run -v /dev"
                   " --user=jorge --dri myfed  firefox")
        out = cmdp.missing_options()
        self.assertIsInstance(out, list)

    def test_04_get(self):
        """Test CmdParser().get()."""

        cmdp = CmdParser()
        cmdp.declare_options("-v= -e= -w= -u= -i -t -a")
        cmdp.parse("udocker run --bindhome "
                   "--hostauth --hostenv -v /sys"
                   " -v /proc -v /var/run -v /dev --debug"
                   " -u=jorge --dri myfed  firefox")
        out = cmdp.get("xyz")
        self.assertIsNone(out)

        # out = cmdp.get("--user=")
        # self.assertEqual(out, "jorge")

        # out = cmdp.get("--debug", "GEN_OPT")
        # self.assertTrue(out)

    def test_05_declare_options(self):
        """Test CmdParser().declare_options()."""
        pass

    def test_06__get_options(self):
        """Test CmdParser()._get_options()."""
        pass

    def test_07__get_params(self):
        """Test CmdParser()._get_params()."""
        pass
