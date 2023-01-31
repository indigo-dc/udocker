#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: CmdParser
"""
import pytest
from udocker.cmdparser import CmdParser


def test_01_parse_01():
    """Test01_01 CmdParser().parse() no cmd."""
    cmdp = CmdParser()
    argv = ["udocker"]
    status = cmdp.parse(argv)
    assert status == False

def test_01_parse_02():
    """Test01_02 CmdParser().parse() with cmd."""
    cmdp = CmdParser()
    argv = ["udocker", "run"]
    status = cmdp.parse(argv)
    assert status == True

def test_01_parse_03():
    """Test01_03 CmdParser().parse() with gen options."""
    cmdp = CmdParser()
    argv = ["udocker", "-h"]
    status = cmdp.parse(argv)
    assert status == False

def test_02_missing_options():
    """Test02 CmdParser().missing_options()."""
    cmdp = CmdParser()
    argv = ["udocker", "run", "--bindhome", "--hostauth", "--hostenv",
            "-v", "/sys", "-v", "/proc", "-v", "/var/run", "-v", "/dev",
            "--user=jorge", "--dri", "myfed", "firefox"]
    cmdp.parse(argv)
    out = cmdp.missing_options()
    self.assertIsInstance(out, list)

# def test_03_missing_options(self):
#     """Test03 CmdParser().missing_options()."""
#     cmdp = CmdParser()
#     argv = ["udocker", "run", "--bindhome", "--hostauth", "--hostenv",
#             "-v", "/sys", "-v", "/proc", "-v", "/var/run", "-v", "/dev",
#             "--user=jorge", "--dri", "myfed", "firefox"]
#     cmdp.parse(argv)
#     out = cmdp.missing_options()
#     self.assertIsInstance(out, list)

# def test_04_get(self):
#     """Test04 CmdParser().get()."""
#     argv = ["udocker", "--debug", "run", "--bindhome", "--hostauth",
#             "--hostenv", "-v", "/sys", "-v", "/proc", "-v",
#             "/var/run", "-v", "/dev", "--user=jorge", "--dri",
#             "myfed", "firefox"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     out = cmdp.get("xyz")
#     self.assertIsNone(out)

#     argv = ["udocker", "--debug", "run", "--bindhome",
#             "-v", "/sys", "--user=jorge", "--dri", "myfed", "firefox"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     out = cmdp.get("--debug", "GEN_OPT", True)
#     self.assertTrue(out)
#     out = cmdp.get("", "CMD", True)
#     self.assertTrue(out, "run")
#     out = cmdp.get("--bindhome", "CMD_OPT", True)
#     self.assertEqual(out, [True])

#     argv = ["udocker", "export", "-o", "cont.tar", "12345"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     out = cmdp.get("", "CMD", True)
#     cmdp.get("-o")
#     tarfile = cmdp.get("P1")
#     container_id = cmdp.get("P2")
#     self.assertTrue(out, "export")
#     self.assertTrue(tarfile, "cont.tar")
#     self.assertTrue(container_id, "12345")

# def test_05_declare_options(self):
#     """Test05 CmdParser().declare_options()."""

# def test_06__get_option(self):
#     """Test06 CmdParser()._get_option()."""

# def test_07__get_param(self):
#     """Test07 CmdParser()._get_param()."""
