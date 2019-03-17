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

sys.path.append('../../')

from udocker.helper.unique import Unique

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class UniqueTestCase(unittest.TestCase):
    """Test Unique() class."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01_init(self):
        """Test Unique() constructor."""
        uniq = Unique()
        self.assertEqual(uniq.def_name, "udocker")

    def test_02__rnd(self):
        """Test Unique._rnd()."""
        uniq = Unique()
        rand = uniq._rnd(64)
        self.assertIsInstance(rand, str)
        self.assertEqual(len(rand), 64)

    def test_03_uuid(self):
        """Test Unique.uuid()."""
        uniq = Unique()
        rand = uniq.uuid("zxcvbnm")
        self.assertEqual(len(rand), 36)
        rand = uniq.uuid(789)
        self.assertEqual(len(rand), 36)

    def test_04_imagename(self):
        """Test Unique.imagename()."""
        uniq = Unique()
        rand = uniq.imagename()
        self.assertEqual(len(rand), 16)

    def test_05_layer_v1(self):
        """Test Unique.layer_v1()."""
        uniq = Unique()
        rand = uniq.layer_v1()
        self.assertEqual(len(rand), 64)

    def test_06_filename(self):
        """Test Unique.filename()."""
        uniq = Unique()
        rand = uniq.filename("zxcvbnmasdf")
        self.assertTrue(rand.endswith("zxcvbnmasdf"))
        self.assertTrue(rand.startswith("udocker"))
        self.assertGreater(len(rand.strip()), 56)
        rand = uniq.filename(12345)
        self.assertTrue(rand.endswith("12345"))
        self.assertTrue(rand.startswith("udocker"))
        self.assertGreater(len(rand.strip()), 50)
