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

def test_02_missing_options_01():
    """Test02_01 CmdParser().missing_options() no options."""
    cmdp = CmdParser()
    argv = ["udocker"]
    cmdp.parse(argv)
    out = cmdp.missing_options()
    assert out == []

def test_02_missing_options_02():
    """Test02_02 CmdParser().missing_options() -h."""
    cmdp = CmdParser()
    argv = ["udocker", "-h"]
    cmdp.parse(argv)
    out = cmdp.missing_options()
    assert out == ["-h"]

def test_02_missing_options_03():
    """Test02_03 CmdParser().missing_options() -h ans cmd options."""
    cmdp = CmdParser()
    argv = ["udocker", "-h", "import", "centos"]
    cmdp.parse(argv)
    out = cmdp.missing_options()
    assert out == ["-h", "centos"]

def test_03_get_01():
    """Test03_01 CmdParser().get() gen option exist."""
    argv = ["udocker", "-D"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("-D", "GEN_OPT")
    assert out == True

def test_03_get_02():
    """Test03_02 CmdParser().get() gen option non exist."""
    argv = ["udocker", "-h"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("-D", "GEN_OPT")
    assert out == False

def test_03_get_03():
    """Test03_03 CmdParser().get() multi gen option exist."""
    argv = ["udocker", "-D", "-h"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("-h", "GEN_OPT", True)
    assert out == [True]

def test_03_get_04():
    """Test03_04 CmdParser().get() command."""
    argv = ["udocker", "run"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("", "CMD")
    assert out == "run"

def test_03_get_05():
    """Test03_05 CmdParser().get() command with options."""
    argv = ["udocker", "run", "cont"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("P1", "CMD_OPT")
    assert out == "cont"

def test_03_get_06():
    """Test03_06 CmdParser().get() none."""
    argv = ["udocker", "run", "cont"]
    cmdp = CmdParser()
    cmdp.parse(argv)
    out = cmdp.get("", "GEN_OPT")
    assert out == None
