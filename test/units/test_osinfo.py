#!/usr/bin/env python
"""
udocker unit tests: OSInfo
"""
import pytest
from udocker.helper.osinfo import OSInfo


@pytest.fixture
def osinfo():
    return OSInfo("/bin")


def test_01_get_filetype(osinfo, mocker):
    """Test01 OSInfo.get_filetype(filename) full filepath exists"""
    ftype = ('file', ' ELF 64-bit')
    mock_isfile = mocker.patch('udocker.helper.osinfo.os.path.isfile', return_value=True)
    mock_islnk = mocker.patch('udocker.helper.osinfo.os.path.islink', return_value=False)
    mock_getout = mocker.patch('udocker.helper.osinfo.Uprocess.get_output',
                               return_value='/bin/ls: ELF 64-bit')
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
                               side_effect=[False, 'x86'])
    status = osinfo.get_filetype("ls")
    assert status == ('readelf', 'x86')
    mock_isfile.assert_called()
    mock_islnk.assert_called()
    assert mock_getout.call_count == 2


def test_03_get_filetype(osinfo, mocker):
    """Test03 OSInfo.get_filetype(filename) file exists is readelf"""
    mock_isfile = mocker.patch('udocker.helper.osinfo.os.path.isfile', return_value=False)
    mock_islnk = mocker.patch('udocker.helper.osinfo.os.path.islink', return_value=False)
    status = osinfo.get_filetype('')
    assert status == ('', '')
    mock_isfile.assert_called()
    mock_islnk.assert_called()


data_arch = [(('file', 'x86-64'), 'x86_64'),
             (('file', 'Intel 80386'), 'x86'),
             (('file', 'aarch64'), 'arm64'),
             (('file', 'ARM'), 'arm')]


@pytest.mark.parametrize("ftype,expected", data_arch)
def test_04_arch(osinfo, ftype, expected, mocker):
    """Test04 OSInfo.arch()"""
    mock_getftype = mocker.patch.object(OSInfo, 'get_filetype', return_value=ftype)
    status = osinfo.arch()
    assert status == expected
    mock_getftype.assert_called()


data_same = (('x86_64', 'x86_64', True),
             ('x86_64', 'x86', False),
             (None, 'x86', None))


@pytest.mark.parametrize("arch1,arch2,expected", data_same)
def test_05_is_same_arch(osinfo, arch1, arch2, expected, mocker):
    """Test05 OSInfo.is_same_arch()"""
    mock_getftype = mocker.patch.object(OSInfo, 'arch', side_effect=[arch1, arch2])
    status = osinfo.is_same_arch()
    assert status == expected
#    mock_getftype.assert_called()


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
           (1, LSB_DATA, '/etc/lsb-release', [False, True, False], ("Ubuntu", "16")),
           (1, OS_DATA, '/etc/os-release', [False, False, True], ("Ubuntu", "20")),
           (0, '', '', [False, False, False], ("", ""))]


@pytest.mark.parametrize("mock_count,data,filepath,path_exist,expected", data_os)
def test_06_osdistribution(osinfo, mock_count, data, filepath, path_exist, expected, mocker):
    """Test06 OSInfo.osdistribution()"""
    mock_match = mocker.patch('udocker.helper.osinfo.FileUtil.match', return_value=[filepath])
    mock_exists = mocker.patch('udocker.helper.osinfo.os.path.exists', side_effect=path_exist)
    mock_gdata = mocker.patch('udocker.helper.osinfo.FileUtil.getdata', return_value=data)
    status = osinfo.osdistribution()
    assert status == expected
    mock_match.assert_called()
    mock_exists.assert_called()
    assert mock_gdata.call_count == mock_count


data_ver = [(("Ubuntu", "20"), 'linux'),
            (("", ""), '')]


@pytest.mark.parametrize("osver,expected", data_ver)
def test_07_osversion(osinfo, osver, expected, mocker):
    """Test07 OSInfo.osversion()"""
    mock_osdist = mocker.patch.object(OSInfo, 'osdistribution', return_value=osver)
    status = osinfo.osversion()
    assert status == expected
    mock_osdist.assert_called()
