#!/usr/bin/env python
"""
udocker unit tests: NVIDIA mode
"""
import glob
import os
import random
import shutil
from contextlib import nullcontext as does_not_raise

import pytest

from udocker.config import Config
from udocker.engine.nvidia import NvidiaMode
from udocker.utils.uprocess import Uprocess


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def lrepo(mocker, container_id):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mock_lrepo._container_id = container_id
    return mock_lrepo


@pytest.fixture
def nvidia(lrepo, container_id):
    nvidia = NvidiaMode(lrepo, container_id)
    nvidia._nvidia_main_libs = ('libnvidia-cfg.so', 'libcuda.so',)
    nvidia._container_root = '/home/.udocker/cont'
    return nvidia


@pytest.fixture
def logger(mocker):
    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    return mock_log


def test_01_init(nvidia, lrepo, container_id):
    """Test01 NvidiaMode() constructor."""
    cdir = lrepo.cd_container(container_id)

    assert nvidia.localrepo == lrepo
    assert nvidia.container_id == container_id
    assert nvidia.container_dir == cdir
    assert nvidia.container_root == cdir + "/ROOT"
    assert nvidia._container_nvidia_set == cdir + "/nvidia"
    assert nvidia._nvidia_main_libs == ("libnvidia-cfg.so", "libcuda.so",)


@pytest.mark.parametrize("cont_dst_dir, files_list, os_exists, error", [
    ('some_dir', ['a', 'b'], False, does_not_raise()),
    ('some_dir', ['a', 'b'], True, pytest.raises(OSError)),
])
def test_02__files_exist(nvidia, mocker, cont_dst_dir, files_list, os_exists, error):
    """Test02 NvidiaMode._files_exist."""
    os_path_exists = mocker.patch.object(os.path, 'exists', return_value=os_exists)

    with error:
        nvidia._files_exist(cont_dst_dir, files_list)

    assert os_path_exists.call_count == len(files_list) if error == does_not_raise() else 1
    assert os_path_exists.call_args_list == [mocker.call(nvidia.container_root + '/' + cont_dst_dir + '/' + fname)
                                             for fname in files_list] if error == does_not_raise() else [
        mocker.call(nvidia.container_root + '/' + cont_dst_dir + '/' + files_list[0])]


@pytest.mark.parametrize("params_dict", [
    {"flist": ['a'], "force": False, 'is_link': [True], "is_file": [True], "os_remove": [], "is_dir": [],
     "makedirs": [], "os_chmod": [], "os_access": [], "debug_count": 2, "warning_count": 0, "error_count": 0,
     "info_count": 1, "expected": False},

    {"flist": ['a'], "force": True, 'is_link': [False, False], "is_file": [True, False], "os_remove": OSError,
     "is_dir": [True], "makedirs": [], "os_chmod": [], "os_access": [], "debug_count": 3, "warning_count": 1,
     "error_count": 1, "info_count": 0, "expected": True},

    {"flist": ['a'], "force": True, 'is_link': [False, False], "is_file": [True, True], "os_remove": [True],
     "is_dir": [True], "makedirs": [], "os_chmod": [True], "os_access": [True], "debug_count": 3, "warning_count": 0,
     "error_count": 0, "info_count": 1, "expected": True},

    {"flist": ['a'], "force": True, 'is_link': [False, False], "is_file": [False, True], "os_remove": [True],
     "is_dir": [False], "makedirs": [True], "os_chmod": [OSError, OSError], "os_access": [False], "debug_count": 3,
     "warning_count": 0, "error_count": 2, "info_count": 1, "expected": True},

    {"flist": ['a'], "force": True, 'is_link': [False, False], "is_file": [True, True], "os_remove": [True],
     "is_dir": [True], "makedirs": [], "os_chmod": [OSError], "os_access": [False], "debug_count": 3,
     "warning_count": 0, "error_count": 1, "info_count": 1, "expected": True},

    {"flist": ['a'], "force": True, 'is_link': [True, True], "is_file": [False, False], "os_remove": [True],
     "is_dir": [False], "makedirs": [True], "os_chmod": [True, True], "os_access": [False],
     "debug_count": 3, "warning_count": 0, "error_count": 0, "info_count": 1, "expected": True},

], ids=["file or link already exists but force is false",
        "file or link already exists but force is true, fail to remove file",
        "file or link already exists, force is true, file removed, change mode",
        "is file, force is false, destination dir does not exist, fail to create change permission",
        "file or link already exists, force is true, file removed, fail to change mode",
        "is link does not exists, force is true, destination dir does not exist, create dir"])
def test_03__copy_files(mocker, nvidia, logger, params_dict):
    """Test03 NvidiaMode._copy_files."""
    hsrc_dir = '/usr/lib'
    cdst_dir = 'lib'

    mocker.patch.object(shutil, 'copy2')
    mocker.patch.object(os, 'readlink')
    mocker.patch.object(os, 'symlink')

    mocker.patch.object(os.path, 'islink', side_effect=params_dict['is_link'])
    mocker.patch.object(os.path, 'isfile', side_effect=params_dict['is_file'])
    mocker.patch.object(os, 'remove', side_effect=params_dict['os_remove'])
    mocker.patch.object(os.path, 'isdir', side_effect=params_dict['is_dir'])
    mocker.patch.object(os, 'makedirs', side_effect=params_dict['makedirs'])
    mocker.patch.object(os, 'chmod', side_effect=params_dict['os_chmod'])
    mocker.patch.object(os, 'access', side_effect=params_dict['os_access'])

    mocker.patch.object(os, 'stat', side_effect=[mocker.Mock(st_mode=444), mocker.Mock(st_mode=644)])
    mocker.patch.object(os.stat, 'S_IMODE', side_effect=[644, 777])

    copy_files = nvidia._copy_files(hsrc_dir, cdst_dir, params_dict['flist'], params_dict['force'])
    assert copy_files == params_dict['expected']

    assert logger.debug.call_count == params_dict['debug_count']
    assert logger.warning.call_count == params_dict['warning_count']
    assert logger.info.call_count == params_dict['info_count']
    assert logger.error.call_count == params_dict['error_count']


@pytest.mark.parametrize("nvi_lib_list, glob_value, expected", [
    (['/lib/libnvidia.so'], ['/lib/libnvidia.so'], ['/lib/libnvidia.so']),
    ([], [], []),
])
def test_04__get_nvidia_libs(mocker, nvidia, logger, nvi_lib_list, glob_value, expected):
    """Test04 NvidiaMode._get_nvidia_libs."""
    host_dir = '/usr/lib'
    mocker.patch.object(Config, 'conf', {'nvi_lib_list': nvi_lib_list})
    mocker.patch.object(glob, 'glob', return_value=glob_value)

    nvidia_libs = nvidia._get_nvidia_libs(host_dir)

    assert nvidia_libs == expected
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('list nvidia libs: %s', nvidia_libs)]


@pytest.mark.parametrize("arch, ldconfig_output, expected", [
    ('x86-64', '    libnvidia-cfg.so (libc6,x86-64 => /usr/lib/x86_64-linux-gnu/libnvidia-cfg.so\n'
               '    libcuda.so (libc6,x86-64 => /usr/lib/x86_64-linux-gnu/libcuda.so\n',
     {'/usr/lib/x86_64-linux-gnu/'}),
    ('', '    libnvidia-cfg.so (libc6 => /usr/lib/libnvidia-cfg.so\n'
         '    libcuda.so (libc6 => /usr/lib/libcuda.so\n',
     {'/usr/lib/'}),
    ('i386', '    libnvidia-cfg.so (libc6,i386 => /usr/lib32/libnvidia-cfg.so\n'
             '    libcuda.so (libc6,i386 => /usr/lib32/libcuda.so\n',
     {'/usr/lib32/'}),
])
def test_05__find_host_dir_ldconfig(mocker, nvidia, logger, arch, ldconfig_output, expected):
    """Test05 NvidiaMode._find_host_dir_ldconfig."""
    mocker.patch.object(os.path, 'realpath', side_effect=lambda x: x, autospec=True)
    mocker.patch.object(Uprocess, 'get_output', return_value=ldconfig_output)

    find_host_dir_ldconfig = nvidia._find_host_dir_ldconfig(arch)

    assert find_host_dir_ldconfig == expected
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('list nvidia libs via ldconfig: %s', find_host_dir_ldconfig)]


@pytest.mark.parametrize("library_path, expected", [
    ("/usr/lib:/lib/x86_64-linux-gnu", {"/usr/lib/", "/usr/lib/x86_64-linux-gnu/"}),
    ("", set())
])
def test_06__find_host_dir_ldpath(mocker, nvidia, logger, library_path, expected):
    """Test06 NvidiaMode._find_host_dir_ldpath."""
    mocker.patch.object(glob, 'glob', return_value=library_path)

    host_dir_ldpath = nvidia._find_host_dir_ldpath(library_path)

    assert host_dir_ldpath == expected
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('list nvidia libs via path: %s', host_dir_ldpath)]


@pytest.mark.parametrize("lib_dirs, ldpath, ldconfig, expected", [
    ({'lib_dirs_list_nvidia': ['/usr/lib', '/lib/x86_64-linux-gnu']}, [{'/lib/x86_64-linux-gnu/', "/usr/lib/"},
                                                                       {'/lib64/x86_64-linux-gnu'}],
     {'/lib64/x86_64-linux-gnu'}, {'/lib/x86_64-linux-gnu/', '/usr/lib/', '/lib64/x86_64-linux-gnu'}),
    ({'lib_dirs_list_nvidia': []}, [{}, {}], [], set()),
    ({'lib_dirs_list_nvidia': []}, [{}, {'/lib64/x86_64-linux-gnu'}], [], {'/lib64/x86_64-linux-gnu'}),
])
def test_07__find_host_dir(mocker, nvidia, logger, lib_dirs, ldpath, ldconfig, expected):
    """Test07 NvidiaMode._find_host_dir."""
    mocker.patch.object(Config, 'conf', lib_dirs)
    mocker.patch.object(nvidia, '_find_host_dir_ldpath', side_effect=ldpath)
    mocker.patch.object(nvidia, '_find_host_dir_ldconfig', side_effect=lambda: ldconfig)
    mocker.patch.dict('os.environ', {'LD_LIBRARY_PATH': '/lib64/x86_64-linux-gnu'})

    find_host_dir = nvidia._find_host_dir()

    assert find_host_dir == expected
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('host location nvidia: %s', find_host_dir)]


@pytest.mark.parametrize("is_dir, log_debug, expected", [
    ([True], 1, '/usr/lib/x86_64-linux-gnu'),
    ([False, True], 1, '/usr/lib64'),
    ([False, False], 0, ''),
])
def test_08__find_cont_dir(mocker, nvidia, logger, is_dir, log_debug, expected):
    """Test08 NvidiaMode._find_cont_dir."""
    mocker.patch.object(os.path, 'isdir', side_effect=is_dir)

    find_cont_dir = nvidia._find_cont_dir()

    assert find_cont_dir == expected
    if log_debug == 1:
        assert logger.debug.call_count == 1
        assert logger.debug.call_args_list == [mocker.call('cont. location nvidia: %s', find_cont_dir)]


@pytest.mark.parametrize("host_dir,cont_dir,file_exists,log_info,expected", [
    (['/home/.udocker/cont/usr/lib'], '/home/.udocker/cont/usr/lib', [True, True, True], 1, False),
    ([], '/home/.udocker/cont/usr/lib', [True, True], 1, False),
    (['/home/.udocker/cont/usr/lib'], '/home/.udocker/cont/usr/lib', [OSError], 0, True),
])
def test_09__installation_exists(mocker, nvidia, logger, host_dir, cont_dir, file_exists, log_info, expected):
    """Test09 NvidiaMode._installation_exists."""
    mocker.patch.object(nvidia, '_files_exist', side_effect=file_exists)

    assert expected == nvidia._installation_exists(host_dir, cont_dir)
    assert logger.info.call_count == log_info

    if not expected:
        assert logger.info.call_args_list == [mocker.call('container has files from previous nvidia install')]


@pytest.mark.parametrize("force, cdir, msg, find_host_dir, find_cont_dir, debug_count, info_count, expected", [
    (False, None, "nvidia set mode container dir not found", [set(), {"/usr/lib"}], [""], 1, 0, False),
    (False, "/home/.udocker/cont", "host nvidia libraries not found", [set(), {"/usr/lib"}], [""], 1, 0, False),
    (False, "/home/.udocker/cont", "destination dir for nvidia libs not found", [{"/usr/lib"}], [""], 1, 0, False),
    (False, "/home/.udocker/cont", "nvidia install already exists, --force to overwrite", [{"/usr/lib"}], ["/dir"],
     1, 0, False),
    (True, "/home/.udocker/cont", "nvidia mode set", [{"/usr/lib"}], ["/dir"],
     0, 1, True),
])
def test_10_set_mode(mocker, nvidia, logger, force, cdir, msg, find_host_dir, find_cont_dir, debug_count, info_count,
                     expected):
    """Test10 NvidiaMode.set_mode()."""
    mocker.patch.object(nvidia, '_find_host_dir', side_effect=find_host_dir, autospec=True)
    mocker.patch.object(nvidia, '_find_cont_dir', side_effect=find_cont_dir, autospec=True)
    mocker.patch.object(nvidia, '_copy_files', side_effect=[True] if expected is False else [True, True, True])
    mocker.patch.object(nvidia, 'container_dir', cdir)

    set_mode = nvidia.set_mode(force=force)

    assert set_mode == expected
    assert logger.error.call_count == debug_count
    assert logger.info.call_count == info_count
    assert logger.error.call_args_list == [mocker.call(msg)] if debug_count > 0 else logger.error.call_args_list == []
    assert logger.info.call_args_list == [mocker.call(msg)] if info_count > 0 else logger.info.call_args_list == []

@pytest.mark.parametrize("os_exists, os_exists_counts, container, expected", [
    (True, 1, '/home/.udocker/container/nvidia', True),
    (False, 1, '', False)
])
def test_11_get_mode(mocker, nvidia, os_exists, os_exists_counts, container, expected):
    """Test11 NvidiaMode.get_mode()."""
    mock_os_path_exists = mocker.patch.object(os.path, 'exists', return_value=os_exists)
    mocker.patch.object(nvidia, '_container_nvidia_set', container)

    get_mode = nvidia.get_mode()

    assert get_mode == expected
    assert mock_os_path_exists.call_count == os_exists_counts
    assert mock_os_path_exists.called
    assert mock_os_path_exists.call_args_list == [mocker.call(nvidia._container_nvidia_set)]


@pytest.mark.parametrize("dev_list,glob_value,glob_count,expected", [
    (['/dev/nvidia'], ['/dev/nvidia'], 1, ['/dev/nvidia']),
    ([], ['/dev/nvidia'], 0, []),
])
def test_12_get_devices(mocker, nvidia, logger, dev_list, glob_value, glob_count, expected):
    """Test12 NvidiaMode.get_devices()."""
    mocked_glob = mocker.patch.object(glob, 'glob', return_value=glob_value)
    mocker.patch.object(Config, 'conf', {"nvi_dev_list": dev_list})

    devices = nvidia.get_devices()

    assert devices == expected
    assert mocked_glob.call_count == glob_count
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('nvidia device list: %s', dev_list)]
