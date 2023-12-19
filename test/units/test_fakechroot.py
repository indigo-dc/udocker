#!/usr/bin/env python
"""
udocker unit tests: FakechrootEngine
"""
import logging
import os
import random
import subprocess
from contextlib import nullcontext as does_not_raise

import pytest

from udocker.config import Config
from udocker.engine.execmode import ExecutionMode
from udocker.engine.fakechroot import FakechrootEngine
from udocker.helper.elfpatcher import ElfPatcher
from udocker.helper.osinfo import OSInfo
from udocker.utils.fileutil import FileUtil
from udocker.utils.uenv import Uenv

XMODE = ["P1", "P2"]


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker, container_id):
    return mocker.patch('udocker.container.localrepo.LocalRepository')


@pytest.fixture(autouse=True)
@pytest.mark.parametrize('xmode', XMODE)
def mock_exec_mode(localrepo, container_id, xmode):
    mocker_exec_mode = ExecutionMode(localrepo, container_id)
    mocker_exec_mode.force_mode = xmode
    return mocker_exec_mode


@pytest.fixture
def ufake(localrepo, mock_exec_mode, container_id):
    fakeroot = FakechrootEngine(localrepo, mock_exec_mode)
    fakeroot.container_id = container_id
    fakeroot.container_dir = "/tmp"
    return fakeroot


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.engine.fakechroot.LOG')


@pytest.mark.parametrize('xmode', ['P1', 'P2'])
def test_01__init(ufake):
    """Test01 FakechrootEngine Constructor."""
    assert ufake._fakechroot_so == ""
    assert ufake._elfpatcher is None
    assert ufake._recommend_expand_symlinks is False


@pytest.mark.parametrize('fakechroot_so, os_exist, os_info, error, expected', [
    ("", [True, True, True, True, True, True], ("linux", "4.8.1"), does_not_raise(), "/tmp/libfakechroot.so"),
    ("", [False, True, True, True, True, True], ("linux", "4.8.1"), does_not_raise(), "/tmp/libfakechroot.so"),
    ("", [False, False, False, False, False, False], ("linux", "4.8.1"), pytest.raises(SystemExit),
     "/tmp/libfakechroot.so"),
    ("/s/fake1", [False, True, True, True, True, True], ("linux", "4.8.1"), does_not_raise(), "/tmp/libfakechroot.so"),
    ("/s/fake1", [True, True, True, True, True, True], ("linux", "4.8.1"), does_not_raise(), "/s/fake1"),
    (["/s/fake1", ], [False, True, True, True, True, True], ("linux", "4.8.1"), pytest.raises(SystemExit),
     "/tmp/libfakechroot.so"),
    (["/s/fake1", ], [False, True, True, True, True, True], ("Alpine", "4.8.1"), pytest.raises(SystemExit),
     "/tmp/libfakechroot.so"),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_02_select_fakechroot_so(mocker, ufake, fakechroot_so, os_exist, os_info, error, expected):
    """Test02 FakechrootEngine.select_fakechroot_so."""
    mocker.patch.object(Config, 'conf',
                        {'fakechroot_so': fakechroot_so, 'root_path': '', 'verbose_level': '', 'tmpdir': '/tmp'})
    mocker.patch.object(os.path, 'exists', side_effect=os_exist)
    mocker.patch.object(OSInfo, 'osdistribution', return_value=os_info)
    mocker.patch.object(FileUtil, 'find_file_in_dir', return_value="/tmp/libfakechroot.so")

    with error:
        select = ufake.select_fakechroot_so()
        assert select == expected


@pytest.mark.parametrize("fakechroot_libc, libc_search, matches, filetype, expected", [
    ("/lib/libc.so.6", None, None, None, "/lib/libc.so.6"),
    (None, ["/lib/libc-*"], ["/container/lib/libc.so.6"], "ELF 64-bit LSB shared object, dynamically linked",
     "/container/lib/libc.so.6"),
    (None, ("/lib/libc-*"), ["/container/lib/libc.so.6"], "ELF 64-bit LSB shared object, dynamically linked",
     "/container/lib/libc.so.6"),
    (None, ("/lib/libc-*",), ["/container/lib/libc.so.6"], "ELF 64-bit LSB shared object, dynamically linked",
     "/container/lib/libc.so.6"),
    (None, "/lib/libc-*", ["/container/lib/libc.so.6"], "ELF 64-bit LSB shared object, dynamically linked",
     "/container/lib/libc.so.6"),
    (None, ["/lib/libc-*"], [], "", ""),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_03_get_libc_pathname(ufake, mocker, fakechroot_libc, libc_search, matches, filetype, expected):
    """ Test03 FakechrootEngine._get_libc_pathname()."""
    mocker.patch.object(Config, 'conf', {'fakechroot_libc': fakechroot_libc, 'libc_search': libc_search,
                                         'tmpdir': '/tmp'})
    if libc_search is not None:
        mocker.patch.object(FileUtil, "match_recursive", return_value=matches)
        mocker.patch.object(OSInfo, "get_filetype", return_value=(None, filetype))

    result = ufake._get_libc_pathname()
    assert result == expected


@pytest.mark.parametrize('user', ["user1", "root"])
@pytest.mark.parametrize('xmode', XMODE)
def test_04__setup_container_user(ufake, mocker, user):
    """Test04 FakechrootEngine._setup_container_user()."""
    mock_setup_container_user_noroot = mocker.patch.object(ufake, '_setup_container_user_noroot', return_value=True)
    ufake._setup_container_user(user=user)
    assert mock_setup_container_user_noroot.call_count == 1


@pytest.mark.parametrize('user', [("user1", 0), ("root", 1), ("0", 1), ("", 0)])
@pytest.mark.parametrize('xmode', XMODE)
def test_05__uid_check(ufake, mocker, logger, user):
    """Test05 FakechrootEngine._uid_check()."""
    mocker.patch.object(ufake, 'opt', {'user': user[0]})
    ufake._uid_check()
    assert logger.warning.call_count == user[1]
    logger.warning.assert_has_calls([mocker.call(
        "this engine does not support execution as root")]) if user[1] > 0 else logger.warning.assert_not_called()


@pytest.mark.parametrize('vol, uvolume, symlinks, sysdirs_list, is_dir, expected_symlinks , expected', [
    ((), [], False, [], [False, False], False, ("", "")),
    (("/tmp",), [("/tmp", "/tmp")], True, [], [True, False, False], False, ('', '/tmp!/tmp')),
    (("/tmp", "/bin"), [("/tmp", "/tmp"), ("/bin", "/bin")], True, [], [True, True, True], True,
     ('', '/tmp!/tmp:/usr/bin!/bin')),
    (("/tmp", "/bin"), [("/tmp", "/tmp"), ("/bin", "/bin")], True, [], [True, False, False], False,
     ('/bin', '/tmp!/tmp')),
    (("", "/bin"), [("", ""), ("/bin", "/bin")], True, [], [False, False], False, ('/bin', '')),
    (("/tmp", "/bin"), [("/tmp", "/tmp"), ("/bin", "/bin")], False, [], [False, False], False, ('/tmp:/bin', '')),
    (("/tmp",), [("/tmp", "/tmp"), ("/bin", "/bin")], True, ["/tmp"], [False, False], False, ('/tmp', '')),
    (("/tmp",), [("/tmp", "/tmp"), ("/bin", "/bin")], False, ["/bin"], [False, False], False, ('/tmp', '')),
    (("/tmp",), [("/tmp", "/tmp")], False, [], [False, False], False, ('/tmp', '')),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_06__get_volume_bindings(ufake, mocker, vol, uvolume, symlinks, sysdirs_list, is_dir, expected_symlinks,
                                 expected):
    """Test06 FakechrootEngine._get_volume_bindings()."""
    mocker.patch.object(ufake, 'opt', {'vol': vol})
    mocker.patch.object(Config, 'conf', {'fakechroot_expand_symlinks': symlinks, 'sysdirs_list': sysdirs_list})
    mocker.patch.object(os.path, 'exists', side_effect=lambda _: False)
    mocker.patch.object(os.path, 'isdir', side_effect=is_dir)
    mocker.patch.object(FileUtil, 'find_file_in_dir', return_value="/tmp/libfakechroot.so")

    status = ufake._get_volume_bindings()
    assert status == expected
    assert ufake._recommend_expand_symlinks == expected_symlinks


@pytest.mark.parametrize('access_files, cont2host, os_path_exists, expected', (
        (("/sys/infin",), "", False, ""),
        (("/sys/infin",), "/c/sys/infin", False, ""),
        (("/sys/infin",), "/c/sys/infin", True, "/sys/infin"),
))
@pytest.mark.parametrize('xmode', XMODE)
def test_07__get_access_filesok(ufake, mocker, access_files, cont2host, os_path_exists, expected):
    """Test07 FakechrootEngine._get_access_filesok()."""
    mocker.patch.object(Config, 'conf', {'access_files': access_files, 'tmpdir': '/tmp'})
    mocker_os_path_exists = mocker.patch.object(os.path, 'exists', return_value=os_path_exists)
    mocker.patch.object(ufake, 'opt', {'vol': ("/tmp",)})
    mock_cont2host = mocker.patch.object(FileUtil, 'cont2host', return_value=cont2host)

    access_filesok = ufake._get_access_filesok()
    assert access_filesok == expected

    if cont2host:
        mocker_os_path_exists.assert_called_once_with(cont2host)
        assert mocker_os_path_exists.call_count == len(access_files)
    assert mock_cont2host.call_count == len(access_files)


@pytest.mark.parametrize('expand_symlinks, cwd, verbose_level, sel_patchelf, container_loader, expected, xmode', (
        (None, "", logging.DEBUG, None, "/ROOT/elf",
         {'PWD': '', 'FAKECHROOT_BASE': '/bin/fakepath',
          'LD_PRELOAD': '/ROOT/lib/libfakechroot.so',
          'FAKECHROOT_EXPAND_SYMLINKS': 'false',
          'FAKECHROOT_AF_UNIX_PATH': '/some/tmp',
          'FAKECHROOT_EXCLUDE_PATH': 'v1:v2', 'FAKECHROOT_DIR_MAP': 'm1:m2',
          'FAKECHROOT_DEBUG': 'true', 'LD_DEBUG': 'libs:files',
          'FAKECHROOT_ACCESS_FILESOK': '/sys/infin'}, "P1"),
        (True, "/home/ls", logging.DEBUG, None, "/ROOT/elf",
         {'PWD': '/home/ls', 'FAKECHROOT_BASE': '/bin/fakepath',
          'LD_PRELOAD': '/ROOT/lib/libfakechroot.so',
          'FAKECHROOT_EXPAND_SYMLINKS': 'true',
          'FAKECHROOT_AF_UNIX_PATH': '/some/tmp',
          'FAKECHROOT_EXCLUDE_PATH': 'v1:v2',
          'FAKECHROOT_DIR_MAP': 'm1:m2',
          'FAKECHROOT_DEBUG': 'true', 'LD_DEBUG': 'libs:files',
          'FAKECHROOT_ACCESS_FILESOK': '/sys/infin',
          'FAKECHROOT_ELFLOADER': None,
          'FAKECHROOT_LIBRARY_ORIG': None,
          'LD_LIBRARY_REAL': None,
          'LD_LIBRARY_PATH': None}, "P1"),
        (True, "/home/ls", logging.DEBUG, None, "/ROOT/elf", {'PWD': '/home/ls'}, "P2"),
        (True, "/home/ls", None, None, "/ROOT/elf", {'PWD': '/home/ls'}, "P1"),
        (True, "/home/ls", None, None, "/ROOT/elf", {'PWD': '/home/ls'}, "P2"),
        (True, "/home/ls", logging.DEBUG, None, "/ROOT/elf",
         {'PWD': '/home/ls',
          'FAKECHROOT_ELFLOADER': '/ROOT/elf',
          'LD_LIBRARY_PATH': '/a'}, "F1"),
        (True, "/home/ls", logging.DEBUG, None, "/ROOT/elf",
         {'PWD': '/home/ls',
          'FAKECHROOT_ELFLOADER': '/ROOT/elf',
          'FAKECHROOT_LIBRARY_ORIG': '/a',
          'LD_LIBRARY_REAL': '/a',
          'LD_LIBRARY_PATH': '/a'}, "F2"),
        (True, "", logging.NOTSET, None, "/ROOT/elf",
         {'PWD': '',
          'FAKECHROOT_ELFLOADER': None,
          'FAKECHROOT_LIBRARY_ORIG': '/a',
          'LD_LIBRARY_REAL': '/a',
          'LD_LIBRARY_PATH': '/a'}, "F3"),
        (True, "", logging.DEBUG, [], "/ROOT/elf",
         {'PWD': '',
          'FAKECHROOT_ELFLOADER': None,
          'FAKECHROOT_LIBRARY_ORIG': '/a',
          'LD_LIBRARY_REAL': '/a',
          'LD_LIBRARY_PATH': '/a',
          'FAKECHROOT_PATCH_PATCHELF': None,
          'FAKECHROOT_PATCH_ELFLOADER': None,
          'FAKECHROOT_PATCH_LAST_TIME': None}, "F4"),
        (True, "", logging.DEBUG, "/ROOT/elf", "/ROOT/elf",
         {'PWD': '',
          'FAKECHROOT_PATCH_PATCHELF': '/ROOT/elf',
          'FAKECHROOT_PATCH_ELFLOADER': '/ROOT/elf',
          'FAKECHROOT_PATCH_LAST_TIME': '/ROOT/elf'}, "F4"),
))
def test_08__fakechroot_env_set(ufake, mocker, expand_symlinks, cwd, verbose_level,
                                sel_patchelf, container_loader, expected, xmode):
    """Test08 FakechrootEngine._fakechroot_env_set()."""
    mocker.patch.object(ufake, '_get_volume_bindings', return_value=('v1:v2', 'm1:m2'))
    mocker.patch.object(ufake, 'select_fakechroot_so', return_value='/ROOT/lib/libfakechroot.so')
    mocker.patch.object(ufake, '_get_access_filesok', return_value='/sys/infin')
    mocker.patch.object(os.path, 'realpath', return_value='/bin/fakepath')
    mocker.patch.object(ufake, 'opt', {'env': Uenv(), 'cwd': cwd, 'vol': '/tmp'})
    mocker.patch.object(Config, 'conf', {'fakechroot_expand_symlinks': expand_symlinks, 'tmpdir': '/some/tmp',
                                         'verbose_level': verbose_level, 'fakechroot_libc': '/path/to/libc'})

    mock_elphpatcher = mocker.patch.object(ufake, '_elfpatcher', return_value=mocker.Mock())
    mocker.patch.object(mock_elphpatcher, 'get_ld_library_path', return_value='/a')
    mocker.patch.object(mock_elphpatcher, 'select_patchelf', return_value=sel_patchelf)
    mocker.patch.object(mock_elphpatcher, 'get_container_loader', return_value=container_loader)
    mocker.patch.object(mock_elphpatcher, 'get_patch_last_time', return_value=container_loader)

    ufake._fakechroot_env_set()
    assert ufake._elfpatcher.get_ld_library_path.call_count == 1
    for k, v in expected.items():
        assert ufake.opt.get('env').env.get(k) == v


@pytest.mark.parametrize('portsmap', [(True, 1,), (False, 0)])
@pytest.mark.parametrize('netcoop', [(True, 1), (False, 0)])
@pytest.mark.parametrize('xmode', XMODE)
def test_09__run_invalid_options(ufake, mocker, logger, portsmap, netcoop):
    """Test09 FakechrootEngine._run_invalid_options()"""
    mocker.patch.object(ufake, 'opt', {'portsmap': portsmap[0], 'netcoop': netcoop[0]})

    ufake._run_invalid_options()
    sum_opt = portsmap[1] + netcoop[1]

    assert logger.warning.call_count == sum_opt
    if ufake.opt["portsmap"]:
        logger.warning.assert_any_call('this execution mode does not support -p --publish')

    if ufake.opt["netcoop"]:
        logger.warning.assert_any_call('this execution mode does not support -P --netcoop --publish-all')


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('file_type, find_exec_result, expected_result, raise_error, msg_log', [
    ("/bin/ls: ELF, x86-64, static", None, [], does_not_raise(), ""),
    ("/bin/ls: xxx, x86-64, yyy", "ls", ["/ROOT/ls"], does_not_raise(), ""),
    ("/bin/ls: xxx, x86-64, yyy", None, [], pytest.raises(SystemExit), ""),
    ("/bin/ls: xxx, x86-64, yyy", None, [], pytest.raises(SystemExit), ""),
    ("#! bin/ls: xxx, x86-64, yyy", None, [], pytest.raises(SystemExit), "no such file"),
    ("#! /bin/ls: xxx, x86-64, yyy", None, ['/ROOT//bin/ls:', 'xxx,', 'x86-64,', 'yyy'], does_not_raise(), ""),
])
def test_10__run_add_script_support(ufake, mocker, logger, xmode, file_type, find_exec_result, expected_result,
                                    raise_error, msg_log):
    """Test10 FakechrootEngine._run_add_script_support()"""
    mocker.patch.object(ufake, 'container_root', "/ROOT")
    mocker.patch.object(ufake, 'opt', {'cmd': ["ls"], 'env': Uenv(), 'cwd': '', 'vol': ''})
    mocker.patch.object(FileUtil, 'find_exec', return_value=find_exec_result)
    mocker.patch.object(FileUtil, 'cont2host', return_value="/bin/ls")
    mocker.patch.object(OSInfo, 'get_filetype', return_value=("", file_type))
    mocker.patch.object(OSInfo, 'is_binary_executable', side_effect=lambda x: "ELF" in file_type)

    hashbang_line = file_type if file_type.startswith("#!") else ""
    mocker.patch.object(FileUtil, 'get1stline', return_value=hashbang_line.encode('utf-8'))

    with raise_error:
        status = ufake._run_add_script_support("/bin/ls")
        assert status == expected_result

    if msg_log:
        assert any(msg_log in call_args[0][0] for call_args in logger.error.call_args_list)


@pytest.mark.parametrize('exec_path, log_count, last_path, expected', (
        ("/bin/bash", 1, None, 0),
        (None, 0, '/ROOT/elf', 2),
))
@pytest.mark.parametrize('xmode', ['P1', 'P2', 'F1', 'F2'])
def test_11_run(ufake, mocker, logger, container_id, xmode, exec_path, log_count, last_path, expected):
    """Test11 FakechrootEngine.run()."""
    mocker_uenv = Uenv()
    mocker.patch.object(ufake, 'opt',
                        {'cmd': exec_path, 'env': mocker_uenv, 'hostenv': '', 'cpuset': '', 'cwd': '', 'vol': ''})

    mocker.patch.object(ufake, '_run_init', return_value=exec_path)
    mocker.patch.object(ufake.exec_mode, 'get_mode', return_value=xmode)
    mocker.patch.object(ufake, '_run_invalid_options')
    mocker.patch.object(ufake, '_run_env_set')
    mocker.patch.object(ufake, '_fakechroot_env_set')
    mocker.patch.object(ufake, '_run_banner')
    mocker.patch.object(ufake, '_run_add_script_support', return_value=["--script", "some_script.sh"])

    mock_elphpatcher = mocker.Mock()
    elphpatcher = mocker.patch.object(ufake, '_elfpatcher', return_value=mock_elphpatcher)
    mocker.patch.object(os.path, 'exists', return_value=True)
    mocker.patch.object(ElfPatcher, 'get_container_loader', return_value="/ROOT/elf")
    mocker.patch.object(FileUtil, 'cont2host', return_value="/cont/ROOT")
    mocker.patch.object(subprocess, 'call', return_value=0)
    mocker.patch.object(ElfPatcher, 'get_patch_last_path', return_value="/ROOT/elf")
    elphpatcher.check_container_path.return_value = False if last_path else True

    result = ufake.run(container_id)
    assert logger.debug.call_count == log_count
    assert result == expected
    logger.warning.assert_called_once_with(
        "container path mismatch, use setup to convert") if not last_path else logger.warning.assert_not_called()
