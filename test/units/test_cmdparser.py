#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: CmdParser
"""
import pytest
from udocker.cmdparser import CmdParser


@pytest.fixture
def cmdparse():
    return CmdParser()


data_parse = [(["udocker"], False),
              (["udocker", "run"], True),
              (["udocker", "-h"], False)]


@pytest.mark.parametrize("argv,expected", data_parse)
def test_01_parse(cmdparse, argv, expected):
    """Test01_01 CmdParser().parse()."""
    status = cmdparse.parse(argv)
    assert status == expected


data_missopt = [(["udocker"], []),
                (["udocker", "-h"], ["-h"]),
                (["udocker", "-h", "import", "centos"], ["-h", "centos"])]


@pytest.mark.parametrize("argv,expected", data_missopt)
def test_02_missing_options(cmdparse, argv, expected):
    """Test02 CmdParser().missing_options()."""
    cmdparse.parse(argv)
    out = cmdparse.missing_options()
    assert out == expected


# Param is    argv                       p1     p2        p3     expected
data_get = [(["udocker", "-D"], "-D", "GEN_OPT", False, True),
            (["udocker", "-h"], "-D", "GEN_OPT", False, False),
            (["udocker", "-D", "-h"], "-h", "GEN_OPT", True, [True]),
            (["udocker", "run"], "", "CMD", False, "run"),
            (["udocker", "run", "cont"], "P1", "CMD_OPT", False, "cont"),
            (["udocker", "run", "cont"], "", "GEN_OPT", False, None)
            ]


@pytest.mark.parametrize("argv,p1,p2,p3,expected", data_get)
def test_03_get(cmdparse, argv, p1, p2, p3, expected):
    """Test03 CmdParser().get() gen option exist."""
    cmdparse.parse(argv)
    out = cmdparse.get(p1, p2, p3)
    assert out == expected


@pytest.mark.parametrize("cmdline, opts_string, expected_consumed", [
    (["udocker", "-x", "-y"], "-x", {"CMD_OPT": [0], 'GEN_OPT': []}),
    (["udocker", "--option=value", "--another"], "--option=", {"CMD_OPT": [0], 'GEN_OPT': []}),
    (["udocker", "--option"], "--option=", {"CMD_OPT": [0], 'GEN_OPT': []}),
    (["udocker", "-x", "--option=value"], "-x --option=", {"CMD_OPT": [0, 1], 'GEN_OPT': []}),
    (["udocker", "--option", "value"], "--option=", {"CMD_OPT": [0, 1], 'GEN_OPT': []}),
    (["udocker", "-y"], "-x", {"CMD_OPT": [], 'GEN_OPT': []}),
])
def test_04_declare_options(cmdparse, cmdline, opts_string, expected_consumed):
    """Test04 CmdParser().declare_options()"""
    cmdparse._argv_split['CMD_OPT'] = cmdline[1:]
    cmdparse.parse(cmdline)
    cmdparse.declare_options(opts_string)
    assert cmdparse._argv_consumed_options == expected_consumed


@pytest.mark.parametrize("argv, opt_name, opt_where, opt_multiple, expected", [
    (["udocker", "--option=value"], "--option=", "CMD_OPT", False, "value"),
    (["udocker", "-x"], "-x", "CMD_OPT", False, True),
    (["udocker", "run"], "-x", "CMD_OPT", False, False),
    (["udocker", "--option=value", "--option=another"], "--option=", "CMD_OPT", True, ["value", "another"]),
    (["udocker", "--option", "value"], "--option=", "CMD_OPT", False, "value"),
    (["udocker", "-x", "run"], "-x", "CMD_OPT", False, True),
    (["udocker", "-x", "--option=value", "run"], "--option=", "CMD_OPT", False, "value"),
])
def test_05__get_option(cmdparse, argv, opt_name, opt_where, opt_multiple, expected):
    """Test05 CmdParser()._get_option() """
    cmdparse._argv_split['CMD_OPT'] = argv[1:]
    opt_list = cmdparse._argv_split[opt_where]
    consumed = []
    result = cmdparse._get_option(opt_name, opt_list, consumed, opt_multiple)
    assert result == expected


@pytest.mark.parametrize("opt_list, opt_name, expected_result, expected_consumed", [
    (["p1", "p2", "--opt", "value"], "p1", "p1", [0]),
    (["--opt", "value", "p2", "p1"], "p2", "p2", [2]),
    (["--opt", "value"], "p1", 'value', [1]),
    (["--opt", "value", "p1"], 'p*', ['value', 'p1'], [1, 2]),
    (["--opt", "value", "p2"], 'p+', ['p2'], [1, 2]),
    (["-"], 'p0', None, []),
])
def test_06_get_param(cmdparse, opt_list, opt_name, expected_result, expected_consumed):
    """Test06 CmdParser()._get_param() """
    cmdparse._argv_split['CMD_OPT'] = opt_list[1:]
    consumed = []
    consumed_params = []
    result = cmdparse._get_param(opt_name, opt_list, consumed, consumed_params)
    assert result == expected_result
    assert consumed_params == expected_consumed