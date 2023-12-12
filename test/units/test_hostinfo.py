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
    mock_getpwuid = mocker.patch('udocker.helper.hostinfo.pwd.getpwuid', return_value=usr)
    name = hinfo.username()
    assert name == usr.pw_name
    mock_getpwuid.assert_called()


def test_02_username(hinfo, mocker):
    """Test02 HostInfo().username. NO user"""
    mock_getpwuid = mocker.patch('udocker.helper.hostinfo.pwd.getpwuid',
                                 side_effect=KeyError("fail"))
    name = hinfo.username()
    assert name == ''
    mock_getpwuid.assert_called()


data_arch = (('UDOCKER', 'x86_64', (['amd64'], ['x86_64'], ['x86_64']), 'amd64'),
             ('UDOCKER', 'arm64', (['aarch64'], [], []), 'aarch64'),
             )


@pytest.mark.parametrize("target,mach,arch,expected", data_arch)
def test_03_arch(mocker, hinfo, target, mach, arch, expected):
    """Test03 HostInfo().arch. With mach and arch"""
    mock_mach = mocker.patch('udocker.helper.hostinfo.platform.machine', return_value=mach)
    mock_arch = mocker.patch.object(HostInfo, 'get_arch', return_value=arch)
    result = hinfo.arch(target)
    assert result == expected
    mock_mach.assert_called()
    mock_arch.assert_called()


def test_04_osversion(mocker, hinfo):
    """Test04 HostInfo().osversion. With osversion"""
    mock_osversion = mocker.patch('udocker.helper.hostinfo.platform.system', return_value="linux")
    result = hinfo.osversion()
    assert result == "linux"
    mock_osversion.assert_called()


def test_05_osversion(hinfo, mocker):
    """Test05 HostInfo().osversion. NO osversion"""
    mock_osversion = mocker.patch('udocker.helper.hostinfo.platform.system',
                                  side_effect=NameError('fail'))
    res_osversion = hinfo.osversion()
    assert res_osversion == ''
    mock_osversion.assert_called()


data_p1 = (({'os': 'linux', 'architecture': 'x86_64', 'variant': 'mint'},
            ('linux', 'x86_64', 'mint')),
           ({'os': 'Android', 'architecture': 'arm64', 'variant': ''},
            ('android', 'arm64', '')),
           ('Linux/X86_64/Mint', ('linux', 'x86_64', 'mint')),
           ('Android/arm64', ('android', 'arm64', '')),
           ('PowerPC', ('powerpc', '', '')),
           (None, ('', '', ''))
           )


@pytest.mark.parametrize("plat_in,expected", data_p1)
def test_06_parse_platform(hinfo, plat_in, expected):
    """Test06 HostInfo().parse_platform."""
    res_plat = hinfo.parse_platform(plat_in)
    assert res_plat == expected


data_p2 = (({'os': 'linux', 'architecture': 'x86_64', 'variant': 'mint'}, 'linux/x86_64/mint'),
           ({'os': 'Android', 'architecture': 'arm64', 'variant': ''}, 'android/arm64'),
           ('Linux/X86_64/Mint', 'linux/x86_64/mint'),
           ('Android/arm64', 'android/arm64'),
           ('PowerPC', 'powerpc'),
           ('', '')
           )


@pytest.mark.parametrize("plat_in,expected", data_p2)
def test_07_platform_to_str(hinfo, plat_in, expected):
    """Test07 HostInfo().parse_platform."""
    res_plat = hinfo.platform_to_str(plat_in)
    assert res_plat == expected


data_p3 = (('amd64', 'Linux', True, 'amd64/linux'),
           ('amd64', 'Linux', False, ('amd64', 'linux', ''))
           )


@pytest.mark.parametrize("osver,arch,ret_str,expected", data_p3)
def test_08_platform(hinfo, mocker, osver, arch, ret_str, expected):
    """Test08 HostInfo().platform."""
    mock_osver = mocker.patch.object(HostInfo, 'osversion', return_value=osver)
    mock_arch = mocker.patch.object(HostInfo, 'arch', return_value=arch)
    res_plat = hinfo.platform(ret_str)
    assert res_plat == expected


data_p4 = (('amd64/linux', 'amd64/linux', True),
           ('arm64/linux', 'amd64/Linux', False)
           )


@pytest.mark.parametrize("parplat,plat_host,expected", data_p4)
def test_09_is_same_platform(hinfo, mocker, parplat, plat_host, expected):
    """Test09 HostInfo().is_same_platform."""
    mock_osver = mocker.patch.object(HostInfo, 'parse_platform', return_value=parplat)
    mock_arch = mocker.patch.object(HostInfo, 'platform', return_value=plat_host)
    res_plat = hinfo.is_same_platform('')
    assert res_plat == expected


def test_10_oskernel(mocker, hinfo):
    """Test10 HostInfo().oskernel. With oskernel"""
    mock_oskernel = mocker.patch('udocker.helper.hostinfo.platform.release', return_value="3.2.1")
    result = hinfo.oskernel()
    assert result == "3.2.1"
    mock_oskernel.assert_called()


def test_11_oskernel(hinfo, mocker):
    """Test11 HostInfo().oskernel. NO oskernel"""
    mock_oskernel = mocker.patch('udocker.helper.hostinfo.platform.release',
                                 side_effect=NameError("fail"))
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
def test_12_oskernel_isgreater(mocker, hinfo, version, list_ver, expected):
    """Test12 HostInfo().oskernel_isgreater."""
    mock_kernel = mocker.patch.object(HostInfo, 'oskernel', return_value=version)
    result = hinfo.oskernel_isgreater(list_ver)
    assert result == expected
    mock_kernel.assert_called()


data_cmd_opt = (("ls", "-a", ["-a"], True),
                ("ls", "-a", "-a", True),
                ("ls", "-z", "-a", False),
                (None, "-z", "-a", False))


@pytest.mark.parametrize("cmd,option,argmt,expected", data_cmd_opt)
def test_13_cmd_has_option(mocker, hinfo, cmd, option, argmt, expected):
    """Test13 HostInfo().cmd_has_option."""
    status = hinfo.cmd_has_option(cmd, option, argmt)
    assert status == expected


@pytest.mark.parametrize("check_output, expected_size", [
    (b"48 90", (48, 90)),
    (OSError("fail"), (24, 80))
])
def test_14_termsize(mocker, hinfo, check_output, expected_size):
    """Test14 HostInfo().termsize. Change size"""

    if isinstance(check_output, Exception):
        mock_chk = mocker.patch('udocker.helper.hostinfo.Uprocess.check_output', side_effect=check_output)
    else:
        mock_chk = mocker.patch('udocker.helper.hostinfo.Uprocess.check_output', return_value=check_output)

    mock_file = mocker.mock_open(read_data="some data")
    mocker.patch('builtins.open', mock_file)

    status = hinfo.termsize()
    assert status == expected_size
    mock_chk.assert_called()
    mock_file.assert_called_with("/dev/tty")

