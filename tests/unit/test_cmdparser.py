#!/usr/bin/env python2
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
        status = cmdp.parse("udocker run --bindhome "
                            "--hostauth --hostenv -v /sys"
                            " -v /proc -v /var/run -v /dev"
                            " --user=jorge --dri myfed firefox")
        self.assertTrue(status)

    def test_03_missing_options(self):
        """Test CmdParser().missing_options()."""
        cmdp = CmdParser()
        cmdp.parse("udocker run --bindhome "
                   "--hostauth --hostenv -v /sys"
                   " -v /proc -v /var/run -v /dev"
                   " --user=jorge --dri myfed firefox")
        out = cmdp.missing_options()
        self.assertIsInstance(out, list)

    def test_04_get(self):
        """Test CmdParser().get()."""
        cmdp = CmdParser()
        cmdp.declare_options("-v= -e= -w= -u= -i -t -a")
        cmdp.parse("udocker --debug run --bindhome "
                   "--hostauth --hostenv -v /sys"
                   " -v /proc -v /var/run -v /dev"
                   " --user=jorge --dri myfed firefox")

        out = cmdp.get("xyz")
        self.assertIsNone(out)

        # out = cmdp.get("--user=", "CMD_OPT")
        # self.assertEqual(out, "jorge")

        out = cmdp.get("run", "CMD")
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
