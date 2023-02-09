#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: CmdParser
"""
from udocker.cmdparser import CmdParser


def test_01_parse():
    """Test01_01 CmdParser().parse() no cmd."""
    cmdp = CmdParser()
    argv = ["udocker"]
    status = cmdp.parse(argv)
    assert not status


def test_02_parse():
    """Test02 CmdParser().parse() with cmd."""
    cmdp = CmdParser()
    argv = ["udocker", "run"]
    status = cmdp.parse(argv)
    assert status


def test_03_parse():
    """Test03 CmdParser().parse() with gen options."""
    cmdp = CmdParser()
    argv = ["udocker", "-h"]
    status = cmdp.parse(argv)
    assert not status


def test_04_missing_options():
    """Test04 CmdParser().missing_options() no options."""
    cmdp = CmdParser()
    argv = ["udocker"]
    cmdp.parse(argv)
    out = cmdp.missing_options()
    assert out == []


def test_05_missing_options():
    """Test05 CmdParser().missing_options() -h."""
    cmdp = CmdParser()
    argv = ["udocker", "-h"]
    cmdp.parse(argv)
    out = cmdp.missing_options()
    assert out == ["-h"]


def test_06_missing_options():
    """Test06 CmdParser().missing_options() -h and cmd options."""
    cmdp = CmdParser()
    argv = ["udocker", "-h", "import", "centos"]
    cmdp.parse(argv)
    out = cmdp.missing_options()
    assert out == ["-h", "centos"]


def test_07_get():
    """Test07 CmdParser().get() gen option exist."""
    argv = ["udocker", "-D"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("-D", "GEN_OPT")
    assert out


def test_08_get():
    """Test08 CmdParser().get() gen option non exist."""
    argv = ["udocker", "-h"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("-D", "GEN_OPT")
    assert not out


def test_09_get():
    """Test09 CmdParser().get() multi gen option exist."""
    argv = ["udocker", "-D", "-h"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("-h", "GEN_OPT", True)
    assert out == [True]


def test_10_get():
    """Test10 CmdParser().get() command."""
    argv = ["udocker", "run"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("", "CMD")
    assert out == "run"


def test_11_get():
    """Test11 CmdParser().get() command with options."""
    argv = ["udocker", "run", "cont"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("P1", "CMD_OPT")
    assert out == "cont"


def test_12_get():
    """Test12 CmdParser().get() none."""
    argv = ["udocker", "run", "cont"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("", "GEN_OPT")
    assert out is None
