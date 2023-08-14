#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: HostInfo
"""
import pytest
import pwd
from udocker.helper.hostinfo import HostInfo


@pytest.fixture
def hinfo(mocker):
    mock_uid = mocker.patch('os.getuid', return_value=1000)
    mock_gid = mocker.patch('os.getgid', return_value=1000)
    return HostInfo()


def test_01_username(hinfo, mocker):
    """Test01 HostInfo().username. With user"""
    usr = pwd.struct_passwd(["user", "*", "1000", "1000", "User", "/home/user", "/bin/bash"])
    mock_getpwuid = mocker.patch('pwd.getpwuid', return_value=usr)

    name = hinfo.username()
    assert name == usr.pw_name
    mock_getpwuid.assert_called()


def test_02_username(hinfo, mocker):
    """Test02 HostInfo().username. NO user"""
    mock_getpwuid = mocker.patch('pwd.getpwuid', side_effect=KeyError("fail"))

    name = hinfo.username()
    assert name == ""
    mock_getpwuid.assert_called()


data_arch = (('UDOCKER', 'x86_64', (['amd64'], ['x86_64'], ['x86_64']), 'amd64'),
             ('UDOCKER', 'arm64', (['aarch64'], [], []), 'aarch64'),
             )


@pytest.mark.parametrize("target,mach,arch,expected", data_arch)
def test_03_arch(mocker, hinfo, target, mach, arch, expected):
    """Test03 HostInfo().arch. With mach and arch"""
    mock_mach = mocker.patch('platform.machine', return_value=mach)
    mock_arch = mocker.patch.object(HostInfo, 'get_arch', return_value=arch)

    result = hinfo.arch(target)
    assert result == expected
    mock_mach.assert_called()
    mock_arch.assert_called()


def test_05_osversion(mocker, hinfo):
    """Test05 HostInfo().osversion. With osversion"""
    mock_osversion = mocker.patch('platform.system', return_value="linux")

    result = hinfo.osversion()
    assert result == "linux"
    mock_osversion.assert_called()


def test_06_osversion(hinfo, mocker):
    """Test06 HostInfo().osversion. NO osversion"""
    mock_osversion = mocker.patch('platform.system', side_effect=NameError("fail"))

    res_osversion = hinfo.osversion()
    assert res_osversion == ""
    mock_osversion.assert_called()


def test_07_oskernel(mocker, hinfo):
    """Test07 HostInfo().oskernel. With oskernel"""
    mock_oskernel = mocker.patch('platform.release', return_value="3.2.1")

    result = hinfo.oskernel()
    assert result == "3.2.1"
    mock_oskernel.assert_called()


def test_08_oskernel(hinfo, mocker):
    """Test08 HostInfo().oskernel. NO oskernel"""
    mock_oskernel = mocker.patch('platform.release', side_effect=NameError("fail"))

    res_oskernel = hinfo.oskernel()
    assert res_oskernel == "6.1.1"
    mock_oskernel.assert_called()


data_version = (("1.1.2-", [1, 1, 1], True),
                ("1.1.2-", [1, 1, 2], True),
                ("1.2.1-", [1, 1, 1], True),
                ("2.2.1-", [1, 1, 1], True),
                ("0.1.0-", [1, 1, 1], False),
                ("1.0.0-", [1, 1, 1], False),
                ("1.1.0-", [1, 1, 1], False))


@pytest.mark.parametrize("version,list_ver,expected", data_version)
def test_09_oskernel_isgreater(mocker, hinfo, version, list_ver, expected):
    """Test09 HostInfo().oskernel_isgreater."""
    mock_kernel = mocker.patch.object(HostInfo, 'oskernel', return_value=version)

    result = hinfo.oskernel_isgreater(list_ver)
    assert result == expected
    mock_kernel.assert_called()


data_cmd_opt = (("ls", "-a", ["-a"], True),
                ("ls", "-a", "-a", True),
                ("ls", "-z", "-a", False))


@pytest.mark.parametrize("cmd,option,argmt,expected", data_cmd_opt)
def test_10_cmd_has_option(mocker, hinfo, cmd, option, argmt, expected):
    """Test10 HostInfo().cmd_has_option."""
    status = hinfo.cmd_has_option(cmd, option, argmt)
    assert status == expected


def test_11_termsize(mocker, hinfo):
    """Test11 HostInfo().termsize. Change size"""
    mock_chk = mocker.patch('udocker.helper.hostinfo.Uprocess.check_output', return_value = "48 90")

    status = hinfo.termsize()
    assert status == (48, 90)
    mock_chk.assert_called()


def test_12_termsize(mocker, hinfo):
    """Test12 HostInfo().termsize. Default termsize and raises"""
    mock_chk = mocker.patch('udocker.helper.hostinfo.Uprocess.check_output',
                            side_effect=OSError("fail"))

    status = hinfo.termsize()
    assert status == (24, 80)
    mock_chk.assert_called()
