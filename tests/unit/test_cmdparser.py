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
        """Test01 CmdParser() Constructor."""
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
        """Test02 CmdParser().parse()."""
        cmdp = CmdParser()
        argv = ["udocker", "run", "--bindhome", "--hostauth", "--hostenv",
                "-v", "/sys", "-v", "/proc", "-v", "/var/run", "-v", "/dev",
                "--user=jorge", "--dri", "myfed", "firefox"]
        status = cmdp.parse(argv)
        self.assertTrue(status)

        argv = ""
        status = cmdp.parse(argv)
        self.assertFalse(status)

    def test_03_missing_options(self):
        """Test03 CmdParser().missing_options()."""
        cmdp = CmdParser()
        argv = ["udocker", "run", "--bindhome", "--hostauth", "--hostenv",
                "-v", "/sys", "-v", "/proc", "-v", "/var/run", "-v", "/dev",
                "--user=jorge", "--dri", "myfed", "firefox"]
        cmdp.parse(argv)
        out = cmdp.missing_options()
        self.assertIsInstance(out, list)

    def test_04_get(self):
        """Test04 CmdParser().get()."""
        argv = ["udocker", "--debug", "run", "--bindhome", "--hostauth",
                "--hostenv", "-v", "/sys", "-v", "/proc", "-v",
                "/var/run", "-v", "/dev", "--user=jorge", "--dri",
                "myfed", "firefox"]
        cmdp = CmdParser()
        cmdp.parse(argv)
        out = cmdp.get("xyz")
        self.assertIsNone(out)

        argv = ["udocker", "--debug", "run", "--bindhome",
                "-v", "/sys", "--user=jorge", "--dri", "myfed", "firefox"]
        cmdp = CmdParser()
        cmdp.parse(argv)
        out = cmdp.get("--debug", "GEN_OPT", True)
        self.assertTrue(out)
        out = cmdp.get("", "CMD", True)
        self.assertTrue(out, "run")
        out = cmdp.get("--bindhome", "CMD_OPT", True)
        self.assertEqual(out, [True])

        argv = ["udocker", "export", "-o", "cont.tar", "12345"]
        cmdp = CmdParser()
        cmdp.parse(argv)
        out = cmdp.get("", "CMD", True)
        cmdp.get("-o")
        tarfile = cmdp.get("P1")
        container_id = cmdp.get("P2")
        self.assertTrue(out, "export")
        self.assertTrue(tarfile, "cont.tar")
        self.assertTrue(container_id, "12345")

    # def test_05_declare_options(self):
    #     """Test05 CmdParser().declare_options()."""

    # def test_06__get_option(self):
    #     """Test06 CmdParser()._get_option()."""

    # def test_07__get_param(self):
    #     """Test07 CmdParser()._get_param()."""

if __name__ == '__main__':
    main()
