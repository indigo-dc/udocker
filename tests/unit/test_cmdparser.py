#!/usr/bin/env python
"""
udocker unit tests: CmdParser
"""
import sys
from unittest import TestCase, main

sys.path.append('.')
from udocker.cmdparser import CmdParser


class CmdParserTestCase(TestCase):
    """Test CmdParserTestCase() command line interface."""

    def setUp(self):
        self.cmdp = CmdParser()

    def tearDown(self):
        pass

    def test_01__init(self):
        """Test CmdParser() Constructor."""
        self.assertEqual(self.cmdp._argv, "")
        self.assertIsInstance(self.cmdp._argv_split, dict)
        self.assertIsInstance(self.cmdp._argv_consumed_options, dict)
        self.assertIsInstance(self.cmdp._argv_consumed_params, dict)
        self.assertEqual(self.cmdp._argv_split['CMD'], "")
        self.assertEqual(self.cmdp._argv_split['GEN_OPT'], [])
        self.assertEqual(self.cmdp._argv_split['CMD_OPT'], [])
        self.assertEqual(self.cmdp._argv_consumed_options['GEN_OPT'], [])
        self.assertEqual(self.cmdp._argv_consumed_options['CMD_OPT'], [])
        self.assertEqual(self.cmdp._argv_consumed_params['GEN_OPT'], [])
        self.assertEqual(self.cmdp._argv_consumed_params['CMD_OPT'], [])

    def test_02_parse(self):
        """Test CmdParser().parse()."""
        argv = ("udocker run --bindhome --hostauth --hostenv -v /sys "
                "-v /proc -v /var/run -v /dev --user=jorge "
                "--dri myfed firefox")
        status = self.cmdp.parse(argv)
        self.assertTrue(status)

        argv = ""
        status = self.cmdp.parse(argv)
        self.assertFalse(status)

    def test_03_missing_options(self):
        """Test CmdParser().missing_options()."""
        argv = ("udocker run --bindhome --hostauth --hostenv -v /sys"
                " -v /proc -v /var/run -v /dev --user=jorge "
                "--dri myfed firefox")
        self.cmdp.parse(argv)
        out = self.cmdp.missing_options()
        self.assertIsInstance(out, list)

    def test_04_get(self):
        """Test CmdParser().get()."""
        self.cmdp.declare_options("-v= -e= -w= -u= -i -t -a")
        argv = ("udocker --debug run --bindhome --hostauth --hostenv -v /sys"
                " -v /proc -v /var/run -v /dev --user=jorge "
                "--dri myfed firefox")
        self.cmdp.parse(argv)

        out = self.cmdp.get("xyz")
        self.assertIsNone(out)

        #argv = ("udocker --debug run --bindhome --hostauth --hostenv -v /sys"
        #        " -v /proc -v /var/run -v /dev --user=jorge "
        #        "--dri myfed firefox")
        #self.cmdp.parse(argv)
        #out = self.cmdp.get("--user=", "CMD_OPT")
        #self.assertEqual(out, "jorge")

        out = self.cmdp.get("run", "CMD")
        self.assertTrue(out)

    def test_05_declare_options(self):
        """Test CmdParser().declare_options()."""
        pass

    def test_06__get_options(self):
        """Test CmdParser()._get_options()."""
        pass

    def test_07__get_params(self):
        """Test CmdParser()._get_params()."""
        pass


if __name__ == '__main__':
    main()
