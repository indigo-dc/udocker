#!/usr/bin/env python
"""
udocker unit tests: FakechrootEngine
"""
import logging
import random
import pytest

from contextlib import nullcontext as does_not_raise

from udocker.config import Config
from udocker.engine.execmode import ExecutionMode
from udocker.engine.fakechroot import FakechrootEngine

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
def mock_fileutil(mocker):
    return mocker.patch('udocker.engine.fakechroot.FileUtil')


@pytest.fixture
def ufake(localrepo, mock_exec_mode, container_id):
    fakeroot = FakechrootEngine(localrepo, mock_exec_mode)
    fakeroot.container_id = container_id
    fakeroot.container_dir = "/tmp"
    return fakeroot


@pytest.fixture
def mock_os_path_exists(mocker):
    return mocker.patch('udocker.engine.fakechroot.os.path.exists')


@pytest.fixture
def mock_os_path_realpath(mocker):
    return mocker.patch('udocker.engine.fakechroot.os.path.realpath')


@pytest.fixture
def mock_os_path_isdir(mocker):
    return mocker.patch('udocker.engine.fakechroot.os.path.isdir')


@pytest.fixture
def mock_osinfo(mocker):
    return mocker.patch('udocker.helper.osinfo.OSInfo')


@pytest.fixture
def mock_logger(mocker):
    return mocker.patch('udocker.engine.fakechroot.LOG')


@pytest.fixture
def mock_uvolume(mocker):
    return mocker.patch('udocker.utils.uvolume.Uvolume')


@pytest.fixture
def mock_elphpatcher(mocker):
    return mocker.patch('udocker.helper.elfpatcher.ElfPatcher')


@pytest.mark.parametrize('xmode', ['P1', 'P2'])
def test_01__init(ufake):
    """Test01 FakechrootEngine Constructor."""
    assert ufake._fakechroot_so == ""
    assert ufake._elfpatcher is None
    assert ufake._recommend_expand_symlinks is False


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('fakechroot_so,os_exist,os_info,error,expected', [
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
def test_02_select_fakechroot_so(ufake, mock_os_path_exists, mock_fileutil, mock_osinfo,
                                 fakechroot_so, os_exist, os_info, error, expected):
    """Test02 FakechrootEngine.select_fakechroot_so."""

    Config.conf['fakechroot_so'] = fakechroot_so
    mock_os_path_exists.side_effect = os_exist
    mock_osinfo.return_value.osdistribution.return_value = os_info
    mock_fileutil.return_value.find_file_in_dir.return_value = "/tmp/libfakechroot.so"

    with error:
        select = ufake.select_fakechroot_so()
        assert select == expected


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('user', ["user1", "root"])
def test_03__setup_container_user(ufake, mocker, user):
    """Test03 FakechrootEngine._setup_container_user()."""
    mock_setup_container_user_noroot = mocker.patch.object(ufake, '_setup_container_user_noroot', return_value=True)
    ufake._setup_container_user(user=user)
    assert mock_setup_container_user_noroot.call_count == 1


@pytest.mark.parametrize('user', [("user1", 0), ("root", 1), ("0", 1), ("", 0)])
@pytest.mark.parametrize('xmode', XMODE)
def test_04__uid_check(ufake, mocker, mock_logger, user):
    """Test04 FakechrootEngine._uid_check()."""
    ufake.opt["user"] = user[0]
    ufake._uid_check()
    assert mock_logger.warning.call_count == user[1]
    if user[1] > 0:
        assert mock_logger.warning.call_args_list == [mocker.call("this engine does not support execution as root")]
    ufake.opt.pop("user")
    mock_logger.warning.call_count == 0


get_volume_bindings_data = (
    ((), [], False, [], [False, False], ("", "")),
    (("/tmp",), [("/tmp", "/tmp")], True, [], [True, False, False], ('', '/tmp!/tmp')),
    (("/tmp", "/bin"), [("/tmp", "/tmp"), ("/bin", "/bin")], True, [], [True, True, True],
     ('', '/tmp!/tmp:/usr/bin!/bin')),
    (("/tmp", "/bin"), [("/tmp", "/tmp"), ("/bin", "/bin")], True, [], [True, False, False], ('/bin', '/tmp!/tmp')),
    (("", "/bin"), [("", ""), ("/bin", "/bin")], True, [], [False, False], ('/bin', '')),
    (("/tmp", "/bin"), [("/tmp", "/tmp"), ("/bin", "/bin")], False, [], [False, False], ('/tmp:/bin', '')),
    (("/tmp",), [("/tmp", "/tmp"), ("/bin", "/bin")], True, ["/tmp"], [False, False], ('/tmp', '')),
    (("/tmp",), [("/tmp", "/tmp"), ("/bin", "/bin")], False, ["/bin"], [False, False], ('/tmp', '')),
    (("/tmp",), [("/tmp", "/tmp")], False, [], [False, False], ('/tmp', '')),
)


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('vol,uvolume,symlinks,sysdirs_list,is_dir,expected', get_volume_bindings_data)
def test_05__get_volume_bindings(ufake, mocker, mock_os_path_isdir, mock_fileutil, vol, uvolume, symlinks,
                                 sysdirs_list, is_dir, expected):
    """Test05 FakechrootEngine._get_volume_bindings()."""
    # TODO: simplify this test_data and mock_realpath
    ufake.opt["vol"] = vol
    Config.conf['fakechroot_expand_symlinks'] = symlinks
    Config.conf['sysdirs_list'] = sysdirs_list
    mock_os_path_exists.side_effect = [False, False]
    mock_os_path_isdir.side_effect = is_dir
    mock_uvolume.side_effect = uvolume
    mock_fileutil.return_value.find_file_in_dir.return_value = "/tmp/libfakechroot.so"
    status = ufake._get_volume_bindings()
    assert status == expected
    if is_dir == [True, True, True]:
        assert ufake._recommend_expand_symlinks is True
    else:
        assert ufake._recommend_expand_symlinks is False
    mocker.resetall()


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('access_files,cont2host,expected,os_path_exists', (
        (("/sys/infin",), "", "", False),
        (("/sys/infin",), "/c/sys/infin", "", False),
        (("/sys/infin",), "/c/sys/infin", "/sys/infin", True),
))
def test_06__get_access_filesok(ufake, mocker, mock_os_path_exists, access_files,
                                cont2host, expected, os_path_exists):
    """Test06 FakechrootEngine._get_access_filesok()."""
    Config.conf['access_files'] = access_files
    mock_os_path_exists.return_value = os_path_exists
    ufake.opt["vol"] = ("/tmp",)
    mock_cont2host = mocker.patch('udocker.utils.fileutil.FileUtil.cont2host', return_value=cont2host)

    access_filesok = ufake._get_access_filesok()

    # assert return
    assert access_filesok == expected

    # assert calls
    if cont2host:
        mock_os_path_exists.assert_called_once_with(cont2host)
        assert mock_os_path_exists.call_count == len(access_files)
    assert mock_cont2host.call_count == len(access_files)


@pytest.mark.parametrize('expand_symlinks,cwd,verbose_level,sel_patchelf,container_loader,expected,xmode', (
        (None, "", logging.DEBUG, None, "/ROOT/elf", {'PWD': '', 'FAKECHROOT_BASE': '/bin/fakepath',
                                                      'LD_PRELOAD': '/ROOT/lib/libfakechroot.so',
                                                      'FAKECHROOT_EXPAND_SYMLINKS': 'false',
                                                      'FAKECHROOT_AF_UNIX_PATH': '/some/tmp',
                                                      'FAKECHROOT_EXCLUDE_PATH': 'v1:v2', 'FAKECHROOT_DIR_MAP': 'm1:m2',
                                                      'FAKECHROOT_DEBUG': 'true', 'LD_DEBUG': 'libs:files',
                                                      'FAKECHROOT_ACCESS_FILESOK': '/sys/infin'}, "P1"),
        (True, "/home/ls", logging.DEBUG, None, "/ROOT/elf", {'PWD': '/home/ls', 'FAKECHROOT_BASE': '/bin/fakepath',
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
        (True, "/home/ls", logging.DEBUG, None, "/ROOT/elf", {'PWD': '/home/ls',
                                                              'FAKECHROOT_ELFLOADER': '/ROOT/elf',
                                                              'LD_LIBRARY_PATH': '/a'}, "F1"),
        (True, "/home/ls", logging.DEBUG, None, "/ROOT/elf", {'PWD': '/home/ls',
                                                              'FAKECHROOT_ELFLOADER': '/ROOT/elf',
                                                              'FAKECHROOT_LIBRARY_ORIG': '/a',
                                                              'LD_LIBRARY_REAL': '/a',
                                                              'LD_LIBRARY_PATH': '/a'}, "F2"),
        (True, "", logging.DEBUG, None, "/ROOT/elf", {'PWD': '',
                                                      'FAKECHROOT_ELFLOADER': '/ROOT/elf',
                                                      'FAKECHROOT_LIBRARY_ORIG': '/a',
                                                      'LD_LIBRARY_REAL': '/a',
                                                      'LD_LIBRARY_PATH': '/a'}, "F3"),
        (True, "", logging.DEBUG, [], "/ROOT/elf", {'PWD': '',
                                                    'FAKECHROOT_ELFLOADER': '/ROOT/elf',
                                                    'FAKECHROOT_LIBRARY_ORIG': '/a',
                                                    'LD_LIBRARY_REAL': '/a',
                                                    'LD_LIBRARY_PATH': '/a',
                                                    'FAKECHROOT_PATCH_PATCHELF': None,
                                                    'FAKECHROOT_PATCH_ELFLOADER': None,
                                                    'FAKECHROOT_PATCH_LAST_TIME': None}, "F4"),
        (True, "", logging.DEBUG, "/ROOT/elf", "/ROOT/elf", {'PWD': '',
                                                             'FAKECHROOT_PATCH_PATCHELF': '/ROOT/elf',
                                                             'FAKECHROOT_PATCH_ELFLOADER': '/ROOT/elf',
                                                             'FAKECHROOT_PATCH_LAST_TIME': '/ROOT/elf'}, "F4"),
))
def test_07__fakechroot_env_set(ufake, mocker, mock_elphpatcher, expand_symlinks, cwd, verbose_level,
                                sel_patchelf, container_loader, expected, xmode):
    """Test07 FakechrootEngine._fakechroot_env_set()."""
    ufake._get_volume_bindings = lambda: ('v1:v2', 'm1:m2')
    ufake.select_fakechroot_so = lambda: '/ROOT/lib/libfakechroot.so'
    ufake._get_access_filesok = lambda: "/sys/infin"
    ufake._is_volume = lambda x: ""

    mocker.patch('udocker.engine.fakechroot.os.path.realpath', return_value='/bin/fakepath')

    ufake.opt['cwd'] = cwd

    Config.conf['fakechroot_expand_symlinks'] = expand_symlinks
    Config.conf['verbose_level'] = verbose_level
    Config.conf['tmpdir'] = '/some/tmp'

    ufake._elfpatcher = mock_elphpatcher
    mocker.patch.object(mock_elphpatcher, 'get_ld_library_path', return_value='/a')
    mocker.patch.object(mock_elphpatcher, 'select_patchelf', return_value=sel_patchelf)
    mocker.patch.object(mock_elphpatcher, 'get_container_loader', return_value=container_loader)
    mocker.patch.object(mock_elphpatcher, 'get_patch_last_time', return_value=container_loader)

    ufake._fakechroot_env_set()
    assert ufake._elfpatcher.get_ld_library_path.call_count == 1

    for k, v in expected.items():
        print(k, v)
        assert ufake.opt.get('env').env.get(k) == v


@pytest.mark.parametrize('portsmap', [(True, 1,), (False, 0)])
@pytest.mark.parametrize('netcoop', [(True, 1), (False, 0)])
@pytest.mark.parametrize('xmode', XMODE)
def test_08__run_invalid_options(ufake, mocker, mock_logger, portsmap, netcoop):
    """Test08 FakechrootEngine._run_invalid_options()"""
    ufake.opt["portsmap"] = portsmap[0]
    ufake.opt["netcoop"] = netcoop[0]
    mock_logger.reset_mock()
    ufake._run_invalid_options()

    sum_opt = portsmap[1] + netcoop[1]
    assert mock_logger.warning.call_count == sum_opt
    if ufake.opt["portsmap"]:
        assert (mocker.call("this execution mode does not support -p --publish")
                in mock_logger.warning.call_args_list)

    if ufake.opt["netcoop"]:
        assert (mocker.call('this execution mode does not support -P --netcoop --publish-all')
                in mock_logger.warning.call_args_list)


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('file_type,find_exec_result,expected_result,raise_error,msg_log', [
    ("/bin/ls: ELF, x86-64, static", None, [], does_not_raise(), ""),
    ("/bin/ls: xxx, x86-64, yyy", "ls", ["/ROOT/ls"], does_not_raise(), ""),
    ("/bin/ls: xxx, x86-64, yyy", "", ["/ls"], pytest.raises(SystemExit), ""),
    ("/bin/ls: xxx, x86-64, yyy", "", [], pytest.raises(SystemExit), ""),
    ("#! bin/ls: xxx, x86-64, yyy", "ls", ["/ROOT/ls"], pytest.raises(SystemExit), "no such file"),
    ("#! /bin/ls: xxx, x86-64, yyy", "ls", ['/ROOT//bin/ls:', 'xxx,', 'x86-64,', 'yyy'], does_not_raise(), ""),
])
def test_09__run_add_script_support(ufake, mocker, mock_fileutil, mock_logger, xmode, file_type, find_exec_result,
                                    expected_result, raise_error, msg_log):
    """Test09 FakechrootEngine._run_add_script_support()"""
    ufake.container_root = "/ROOT"
    ufake.opt["cmd"] = ["fds"]

    mock_fileutil_instance = mock_fileutil.return_value
    mock_fileutil_instance.find_exec.return_value = find_exec_result

    mocker.patch('udocker.utils.fileutil.FileUtil.cont2host', return_value="/bin/ls")
    mocker.patch('udocker.helper.osinfo.OSInfo.get_filetype', return_value=("", file_type))
    mock_fileutil.return_value.get1stline.return_value = file_type.encode('utf-8')

    with raise_error:
        status = ufake._run_add_script_support("/bin/ls")
        assert status == expected_result

    if msg_log:
        assert any(msg_log in call_args[0][0] for call_args in mock_logger.error.call_args_list)


@pytest.mark.parametrize('exec_path,log_count,expected', (
        ("/bin/bash", 1, 0),
        (None, 0, 2),
))
@pytest.mark.parametrize('xmode', ['P1', 'P2', 'F1', 'F2'])
def test_10_run(ufake, mocker, container_id, xmode, mock_elphpatcher, mock_logger, exec_path, log_count, expected):
    """Test10 FakechrootEngine.run()."""
    ufake.opt["cmd"].append(exec_path)

    ufake._run_init = lambda container_id: exec_path
    ufake.exec_mode.get_mode = lambda: xmode
    ufake._run_invalid_options = lambda: None
    ufake._run_env_set = lambda: None
    ufake._fakechroot_env_set = lambda: None
    ufake._run_banner = lambda exec_path: None
    ufake._run_add_script_support = lambda exec_path: ["--script", "some_script.sh"]

    ufake._elfpatcher = mock_elphpatcher
    mocker.patch('udocker.helper.elfpatcher.os.path.exists', return_value=True)
    mocker.patch.object(mock_elphpatcher, 'get_container_loader()', return_value="/ROOT/elf")

    mocker.patch('udocker.utils.fileutil.FileUtil.cont2host', return_value="/cont/ROOT")

    with mocker.patch('subprocess.call', return_value=0):
        result = ufake.run(container_id)

    assert mock_logger.debug.call_count == log_count
    assert result == expected
