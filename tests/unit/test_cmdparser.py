#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: CmdParser
"""
from unittest import TestCase, main
from udocker.cmdparser import CmdParser


class CmdParserTestCase(TestCase):
    """Test CmdParserTestCase() command line interface."""

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
        argv = ("udocker run --bindhome --hostauth --hostenv -v /sys "
                "-v /proc -v /var/run -v /dev --user=jorge "
                "--dri myfed firefox")
        status = cmdp.parse(argv)
        self.assertTrue(status)

        argv = ""
        status = cmdp.parse(argv)
        self.assertFalse(status)

    def test_03_get(self):
        """Test CmdParser().get()."""
        argv = ("udocker --debug run --bindhome --hostauth --hostenv -v /sys"
                " -v /proc -v /var/run -v /dev --user=jorge "
                "--dri myfed firefox")
        cmdp = CmdParser()
        cmdp.parse(argv)
        out = cmdp.get("xyz")
        self.assertIsNone(out)

        argv = ("udocker --debug run --bindhome --hostauth --hostenv -v /sys"
                " -v /proc -v /var/run -v /dev --user=jorge "
                "--dri myfed firefox")
        cmdp = CmdParser()
        cmdp.parse(argv)
        #out = cmdp.get("--dri", "CMD_OPT", True)
        #self.assertTrue(out)
        #out = cmdp.get("--user=", "CMD_OPT", True)
        #self.assertEqual(out, "jorge")

        out = cmdp.get("run", "CMD")
        self.assertTrue(out)

    def test_04_missing_options(self):
        """Test CmdParser().missing_options()."""
        cmdp = CmdParser()
        argv = ("udocker run --bindhome --hostauth --hostenv -v /sys"
                " -v /proc -v /var/run -v /dev --user=jorge "
                "--dri myfed firefox")
        cmdp.parse(argv)
        out = cmdp.missing_options()
        self.assertIsInstance(out, list)

    def test_05_declare_options(self):
        """Test CmdParser().declare_options()."""
        #cmdp.declare_options("-v= -e= -w= -u= -i -t -a")
        pass


if __name__ == '__main__':
    main()
