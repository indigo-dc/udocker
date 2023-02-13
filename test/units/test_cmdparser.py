#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: CmdParser
"""
import pytest
from udocker.cmdparser import CmdParser


@pytest.fixture
def cmdp():
    return CmdParser()


data_parse = [(["udocker"], False),
              (["udocker", "run"], True),
              (["udocker", "-h"], False)]


@pytest.mark.parametrize("argv,expected", data_parse)
def test_01_parse(cmdp, argv, expected):
    """Test01_01 CmdParser().parse()."""
    status = cmdp.parse(argv)
    assert status == expected


data_missopt = [(["udocker"], []),
                (["udocker", "-h"], ["-h"]),
                (["udocker", "-h", "import", "centos"], ["-h", "centos"])]


@pytest.mark.parametrize("argv,expected", data_missopt)
def test_04_missing_options(cmdp, argv, expected):
    """Test04 CmdParser().missing_options()."""
    cmdp.parse(argv)
    out = cmdp.missing_options()
    assert out == expected


# Param is    argv                       p1     p2        p3     expected
data_get = [(["udocker", "-D"],          "-D", "GEN_OPT", False, True),
            (["udocker", "-h"],          "-D", "GEN_OPT", False, False),
            (["udocker", "-D", "-h"],    "-h", "GEN_OPT", True,  [True]),
            (["udocker", "run"],         "",   "CMD",     False, "run"),
            (["udocker", "run", "cont"], "P1", "CMD_OPT", False, "cont"),
            (["udocker", "run", "cont"], "",   "GEN_OPT", False, None)
            ]



@pytest.mark.parametrize("argv,p1,p2,p3,expected", data_get)
def test_07_get(cmdp, argv, p1, p2, p3, expected):
    """Test07 CmdParser().get() gen option exist."""
    cmdp.parse(argv)
    out = cmdp.get(p1, p2, p3)
    assert out == expected
