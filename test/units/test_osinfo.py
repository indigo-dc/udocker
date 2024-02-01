#!/usr/bin/env python
"""
udocker unit tests: OSInfo
"""
import json

import pytest

from udocker.helper.osinfo import OSInfo
from udocker.utils.fileutil import FileUtil


@pytest.fixture
def osinfo():
    return OSInfo("/bin")


def test_01_get_filetype(osinfo, mocker):
    """Test01 OSInfo.get_filetype(filename) full filepath exists"""
    ftype = ('file', ' ELF 64-bit')
    mock_isfile = mocker.patch('udocker.helper.osinfo.os.path.isfile', return_value=True)
    mock_islnk = mocker.patch('udocker.helper.osinfo.os.path.islink', return_value=False)
    mock_getout = mocker.patch('udocker.helper.osinfo.Uprocess.get_output',
                               side_effect=[None, 'something: ELF 64-bit'])
    status = osinfo.get_filetype("/bin/ls")
    assert status == ftype
    mock_isfile.assert_called()
    mock_islnk.assert_called()
    mock_getout.assert_called()


def test_02_get_filetype(osinfo, mocker):
    """Test02 OSInfo.get_filetype(filename) file exists is readelf"""
    mock_isfile = mocker.patch('udocker.helper.osinfo.os.path.isfile', return_value=True)
    mock_islnk = mocker.patch('udocker.helper.osinfo.os.path.islink', return_value=False)
    mock_getout = mocker.patch('udocker.helper.osinfo.Uprocess.get_output',
                               side_effect=['x86'])
    status = osinfo.get_filetype("ls")
    assert status == ('readelf', 'x86')
    mock_isfile.assert_called()
    mock_islnk.assert_called()
    assert mock_getout.call_count == 1


def test_03_get_filetype(osinfo, mocker):
    """Test03 OSInfo.get_filetype(filename) file exists is readelf"""
    mock_isfile = mocker.patch('udocker.helper.osinfo.os.path.isfile', return_value=False)
    mock_islnk = mocker.patch('udocker.helper.osinfo.os.path.islink', return_value=False)
    status = osinfo.get_filetype('')
    assert status == ('', '')
    mock_isfile.assert_called()
    mock_islnk.assert_called()


@pytest.mark.parametrize("filename, filetype, is_exec, expected", [
    ("binary_executable", ("file", "ELF 64-bit"), True, True),
    ("binary_executable", (None, None), True, True),
    ("binary_non_executable", (None, None), False, False),
    ("binary_non_executable", ("file", "ELF 64-bit"), False, True),
    ("non_binary_executable", (None, None), True, False),
    ("non_binary_non_executable", (None, None), False, False),
])
def test_04_is_binary_executable(mocker, osinfo, filename, filetype, is_exec, expected):
    """Test04 OSInfo.is_binary_executable()"""
    mocker.patch.object(osinfo, 'get_filetype', return_value=filetype)
    mocker.patch.object(FileUtil, 'getdata', return_value=b'\x7fELF' if filename.startswith("binary") else b'')
    mocker.patch.object(FileUtil, 'isexecutable', return_value=is_exec)
    result = osinfo.is_binary_executable(filename)
    assert result == expected


@pytest.mark.parametrize("binary_list, expected_filetype_outputs, arch, error_arch, expected_arch", [
    ([], [(None, None)], "", False, ""),
    (["binary1", "binary2"], [("file", "x86_64"), ("file", "unknown")], "x86_64", False, "x86_64"),
    (["unknown1", "unknown2"], [("file", "unknown"), ("file", "unknown")], "", False, ""),
    (["binary_x86", "binary_arm"], [("file", "x86_64"), ("file", "arm")], "x86_64", False, "x86_64"),
    (["no_source_type"], [(None, None)], "", False, ""),
    (["binary1", "binary2"], [("file", "x86_64"), ("file", "unknown")], "", True, ""),
])
def test_05_arch_from_binaries(mocker, osinfo, binary_list, expected_filetype_outputs, arch, error_arch, expected_arch):
    """Test05 OSInfo.arch_from_binaries()"""
    filetype_dict = {binary: output for binary, output in zip(binary_list, expected_filetype_outputs)}
    mocker.patch.object(OSInfo, 'get_filetype', side_effect=lambda file_path:
    filetype_dict.get(next((binary for binary in binary_list if file_path.endswith(binary)), None),
                      ("file", "unknown")))

    mocker.patch.object(osinfo, 'get_binaries_list', return_value=binary_list)
    mocker.patch.object(osinfo, 'get_arch', return_value=(arch, "", "") if not error_arch else ())

    arch = osinfo.arch_from_binaries()
    assert arch == expected_arch



@pytest.mark.parametrize("file_presence, file_contents, expected", [
    (["container.json"], '{"key": "value"}', {"key": "value"}),
    (["config.json"], '{"key2": "value2"}', {"key2": "value2"}),
    (["container.json"], "invalid json", None),
    ([], None, None),
])
def test_06__load_config_json(mocker, osinfo, file_presence, file_contents, expected):
    """Test06 OSInfo._load_config_json()"""
    if file_contents and "invalid json" in file_contents:
        mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("json.load", side_effect=json.JSONDecodeError("Expecting value", "", 0))
    else:
        mocker.patch("builtins.open", mocker.mock_open(read_data=file_contents), create=True)
        mocker.patch("json.load", side_effect=lambda f: json.loads(f.read()))

    result = osinfo._load_config_json()
    assert result == expected


@pytest.mark.parametrize("config_json, mock_get_arch_return, error_arch_index, expected", [
    ({"architecture": "x86_64", "variant": "v8"}, [("x86_64/v8", "", "")], False, ("x86_64/v8", "", "")),
    ({"architecture": "x86_64"}, [("x86_64/v8", "", "")],  False,  ("x86_64/v8", "", "")),
    ({"architecture": "x86_64", "variant": "v8"}, [], False, ""),
    ({"architecture": None}, [],  False, ""),
    ({"something_else": "some_other_key"}, [],  False, ""),
    ({}, [],  False, ""),
    (None, [],  False, ""),
])
def test_07_arch_from_metadata(mocker, osinfo, config_json, mock_get_arch_return, error_arch_index, expected):
    """Test07 OSInfo.arch_from_metadata()"""
    mocker.patch.object(osinfo, '_load_config_json', side_effect=[config_json])
    mocker.patch.object(osinfo, 'get_arch', side_effect=[mock_get_arch_return, mock_get_arch_return])
    result = osinfo.arch_from_metadata()
    assert result == expected


data_arch = [(('file', 'x86-64'), ['x86_64']),
             (('file', 'Intel 80386'), ['x86']),
             (('file', 'aarch64'), ['arm64']),
             (('file', 'ELF 32-bit LSB executable, ARM, EABI5 version 1'), ['armhf'])]


@pytest.mark.parametrize("ftype,expected", data_arch)
def test_08_arch(osinfo, ftype, expected, mocker):
    """Test08 OSInfo.arch()"""
    mocker.patch.object(OSInfo, 'arch_from_metadata', return_value="")
    mock_getftype = mocker.patch.object(OSInfo, 'get_filetype', return_value=ftype)
    mocker.patch.object(OSInfo, 'get_binaries_list', return_value=["dummy_binary"])
    status = osinfo.arch()
    assert status == expected
    mock_getftype.assert_called()


data_same = (('x86_64', 'x86_64', True),
             ('x86_64', 'x86', False),
             (None, 'x86', None))


@pytest.mark.parametrize("arch1,arch2,expected", data_same)
def test_09_is_same_arch(osinfo, arch1, arch2, expected, mocker):
    """Test09 OSInfo.is_same_arch()"""
    mock_getftype = mocker.patch.object(OSInfo, 'arch', side_effect=[arch1, arch2])
    status = osinfo.is_same_arch()
    assert status == expected
    mock_getftype.assert_called()


RELEASE_DATA = 'CentOS release 6.10 (Final)'
LSB_DATA = ("DISTRIB_ID=Ubuntu\n"
            "DISTRIB_RELEASE=16.04\n"
            "DISTRIB_CODENAME=xenial\n"
            "DISTRIB_DESCRIPTION=Ubuntu 16.04.5 LTS\n")
OS_DATA = ("NAME=\"Ubuntu\"\n"
           "VERSION=\"20.04.2 LTS (Focal Fossa)\"\n"
           "ID=ubuntu\n"
           "ID_LIKE=debian\n"
           "PRETTY_NAME=\"Ubuntu 20.04.2 LTS\"\n"
           "VERSION_ID=\"20.04\"\n"
           "VERSION_CODENAME=focal\n"
           "UBUNTU_CODENAME=focal")

data_os = [(1, RELEASE_DATA, '/etc/centos-release', [True, False, False], ("CentOS", "6")),
           (1, LSB_DATA, '/etc/lsb-release', [False, True, False], ("Ubuntu", "16.04")),
           (1, OS_DATA, '/etc/os-release', [False, False, True], ("Ubuntu", "20.04")),
           (0, '', '', [False, False, False], ("", ""))]


@pytest.mark.parametrize("mock_count,data,filepath,path_exist,expected", data_os)
def test_10__osdistribution(osinfo, mock_count, data, filepath, path_exist, expected, mocker):
    """Test10 OSInfo._osdistribution()"""
    mock_match = mocker.patch('udocker.helper.osinfo.FileUtil.match', return_value=[filepath])
    mock_exists = mocker.patch('udocker.helper.osinfo.os.path.exists', side_effect=path_exist)
    mock_gdata = mocker.patch('udocker.helper.osinfo.FileUtil.getdata', return_value=data)
    status = osinfo._osdistribution()
    assert status == expected
    mock_match.assert_called()
    mock_exists.assert_called()
    assert mock_gdata.call_count == mock_count


data_ver = [(("Ubuntu", "20"), 'linux'),
            (("", ""), '')]

@pytest.mark.parametrize("osdist_output, expected", [
    (("Ubuntu", "20.04.1"), ("Ubuntu", "20.04")),
    (("Debian", "10.6.0"), ("Debian", "10.6")),
    (("Fedora", "38.0"), ("Fedora", "38")),
    (("CentOS", "7"), ("CentOS", "7")),
    (("OpenSUSE", ""), ("OpenSUSE", "")),
])
def test_11_osdistribution(mocker, osinfo, osdist_output, expected):
    """Test11 OSInfo.osdistribution()"""

    mocker.patch.object(osinfo, '_osdistribution', return_value=osdist_output)

    result = osinfo.osdistribution()
    assert result == expected


@pytest.mark.parametrize("osver,expected", data_ver)
def test_12_osversion(osinfo, osver, expected, mocker):
    """Test12 OSInfo.osversion()"""
    mock_osdist = mocker.patch.object(OSInfo, 'osdistribution', return_value=osver)
    status = osinfo.osversion()
    assert status == expected
    mock_osdist.assert_called()
