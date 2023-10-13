#!/usr/bin/env python
"""
udocker unit tests: SingularityEngine
"""
import logging
import random
from contextlib import nullcontext as does_not_raise

import mock
import pytest

from udocker.config import Config
from udocker.engine.singularity import SingularityEngine


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def lrepo(mocker, container_id):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mock_lrepo._container_id = container_id
    return mock_lrepo


@pytest.fixture
def singularity(lrepo):
    mode = mock.patch('udocker.engine.execmode.ExecutionMode')
    return SingularityEngine(lrepo, mode.start())


@pytest.fixture
def mock_os_path_exists(mocker):
    return mocker.patch('udocker.engine.singularity.os.path.exists')


@pytest.fixture
def mock_os_path_isdir(mocker):
    return mocker.patch('udocker.engine.singularity.os.path.isdir')


@pytest.fixture
def mock_fileutil(mocker):
    return mocker.patch('udocker.engine.singularity.FileUtil')


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.engine.singularity.LOG')


@pytest.fixture
def mock_hostinfo(mocker):
    return mocker.patch('udocker.engine.singularity.HostInfo')


@pytest.fixture
def mock_nixauth(mocker):
    return mocker.patch('udocker.engine.singularity.NixAuthentication')


def test_01_init(singularity, tmpdir):
    """Test the init() function"""
    assert singularity.executable is None
    assert singularity.execution_id is None


@pytest.mark.parametrize("os_exists,executable,findexec,arch,logcount,loggermsg,error,expected", [
    (True, None, "/bin/runc-arm", "i386", 0, [], does_not_raise(), "/bin/runc-arm"),
    (True, "UDOCKER", "singularity-x86_64", "amd64", 0, [], does_not_raise(), "singularity-x86_64"),
    (False, "UDOCKER", "singularity-x86_64", "amd64", 1, "Error: singularity executable not found",
     pytest.raises(SystemExit), "singularity-x86_64"),
    (False, "UDOCKER", "", "i386", 1, "Error: singularity executable not found", pytest.raises(SystemExit),
     "singularity-x86_64"),
])
def test_02_select_singularity(mocker, singularity, mock_fileutil, mock_os_path_exists, logger, os_exists,
                               executable, findexec, arch, logcount, loggermsg, error, expected):
    """Test the select_singularity() function"""
    mocker.patch.object(Config, 'conf', {'use_singularity_executable': executable})

    mock_os_path_exists.return_value = os_exists
    mock_fileutil.return_value.find_exec.return_value = findexec
    mock_fileutil.return_value.find_file_in_dir.return_value = findexec

    with error as exit_code:
        singularity.select_singularity()
        if exit_code is not None:
            assert exit_code.type == SystemExit
            assert exit_code.value.code == 1
        assert logger.error.call_args_list == loggermsg
        assert logger.error.call_count == logcount
        assert singularity.executable == findexec


@pytest.mark.parametrize("vol,home,istmp,expected", [
    (["/dir1", "/home/user"], "", True,
     ['-B', '/dir1:/dir1', '-B', '/home/user:/home/user', '--home', '/root:/root', '-B', '/tmp:/tmp', '-B',
      '/var/tmp:/var/tmp']),
    (["/home/user", "/tmp", "/var/tmp"], "/home/user", True, ['-B', '/home/user:/home/user', '-B', '/tmp:/tmp',
                                                              '-B', '/var/tmp:/var/tmp']),
    (["/home/user", "/tmp", "/var/tmp"], "/home/user", True, ['-B', '/home/user:/home/user', '-B', '/tmp:/tmp',
                                                              '-B', '/var/tmp:/var/tmp']),
    (["/dir1"], "/home/user", False, ['-B', '/dir1:/dir1', '--home', '/root:/root', '-B', '/tmp:/tmp',
                                      '-B', '/var/tmp:/var/tmp']),
    ([], "/home/user", True, ['--home', '/root:/root', '-B', '/tmp:/tmp', '-B', '/var/tmp:/var/tmp']),
])
def test_03__get_volume_bindings(mocker, singularity, mock_nixauth, mock_os_path_isdir, vol, home, istmp, expected):
    """Test the _get_volume_bindings() function"""
    mock_os_path_isdir.side_effect = [istmp for _ in vol]
    mocker.patch.object(singularity, 'opt', {'vol': vol})
    mock_nixauth.return_value.get_home.return_value = home

    status = singularity._get_volume_bindings()
    assert status == expected


@pytest.mark.parametrize("envkeys,expected", (
        ([("AA", "aa"), ("BB", "bb")], {"SINGULARITYENV_AA": "aa", "SINGULARITYENV_BB": "bb"}),
        ([], {})
))
def test_04__singularity_env_get(mocker, singularity, envkeys, expected):
    """Test04 SingularityEngine()._singularity_env_get()."""
    mocker.patch.object(singularity, 'opt', {'env': envkeys})

    status = singularity._singularity_env_get()
    assert status == expected


@pytest.mark.parametrize("mkdir", [
    ([True, True, True, True, True, True]),
    ([False, False, False, False, False, False]),
])
def test_05__make_container_dirs(singularity, mock_fileutil, mkdir):
    """Test05 SingularityEngine()._make_container_directories()."""
    mock_fileutil.return_value.mkdir.side_effect = mkdir
    singularity._make_container_directories()
    assert mock_fileutil.return_value.mkdir.call_count == 6


@pytest.mark.parametrize("portsmap,netcoop,logcount,call", [
    ("netcoop", "portsmap", 2, [mock.call("this execution mode does not support -p --publish"),
                                mock.call("Warning: this exec mode does not support -P --netcoop --publish-all")]),
    (None, None, 0, []),
])
def test_06__run_invalid_options(mocker, singularity, logger, portsmap, netcoop, logcount, call):
    """Test06 SingularityEngine()._run_invalid_options()."""
    mocker.patch.object(singularity, 'opt', {'portsmap': portsmap, 'netcoop': netcoop})
    singularity._run_invalid_options()
    assert logger.warning.call_count == logcount
    assert logger.warning.call_args_list == call


@pytest.mark.parametrize("opts,uname,logcount,loggermsg,option,user_in,expected", [
    ({'user': 'u1', 'uid': 1001, 'home': "/home/user"}, 'u1', 0, [], "", (False, False), False),
    ({'user': 'u1', 'uid': 1001, 'home': "/home/user"}, "u2", 1, [mock.call("running as another user not supported")],
     "", (False, False), False),
    ({'user': 'root', 'uid': 1001, 'home': "/home/user"}, "u1", 0, [], "", (False, False), False),
    ({'user': 'root', 'uid': 1001, 'home': "/home/user"}, "u1", 0, [], "--fakeroot", (True, True), True),
    ({'user': 'root', 'uid': 1001, 'home': "/home/user"}, "u1", 0, [], "", (False, False), False),
    ({'uid': 1001, 'home': "/home/user"}, "u1", 0, [], "", (False, False), False),
])
def test_07__run_as_root(mocker, singularity, mock_hostinfo, mock_nixauth, logger, logcount, uname,
                         loggermsg, option, user_in, expected, opts):
    """Test07 SingularityEngine()._run_as_root()."""
    mocker.patch.object(Config, 'conf', {'singularity_options': []})
    mocker.patch.object(singularity, 'opt', opts)
    mocker.patch.object(singularity, '_has_option', return_value=lambda x, y: True if option == "--fakeroot" else False)

    mock_hostinfo.return_value.username.return_value = uname
    mock_nixauth.return_value.user_in_subuid.return_value = user_in[0]
    mock_nixauth.return_value.user_in_subgid.return_value = user_in[1]

    assert singularity._run_as_root() == expected
    assert ('--fakeroot' in Config.conf['singularity_options']) == expected
    assert logger.warning.call_count == logcount
    assert logger.warning.call_args_list == loggermsg

#
# @pytest.mark.parametrize("is_dir,execpath,loglevel,opts,expected", [
#     # ("/home/user/execpath", "/home/user/container", "root", 2), execpath,croot,uname,expected
#     (True, "/home/user/execpath", {'verbose_level': logging.DEBUG}, {'cmd': ['pwd']}, 0),
#     (False, "/home/user/execpath", {'verbose_level': logging.DEBUG}, {'cmd': ['pwd']}, 0),
#     (False, None, None, {}, 2),
# ])
# def test_08_run(mocker, singularity, container_id, mock_nixauth, is_dir, execpath, loglevel, opts,
#                 expected):
#     """Test08 SingularityEngine().run()."""
#     mocker.patch.object(singularity, 'opt', opts)
#
#     mocker.patch.object(singularity, '_check_arch')
#     mocker.patch.object(singularity, '_run_invalid_options')
#     mocker.patch.object(singularity, '_make_container_directories')
#     mocker.patch.object(singularity, 'select_singularity')
#     mocker.patch.object(singularity, '_run_env_set')
#
#     mocker.patch('udocker.engine.singularity.FileBind.restore', return_value=[])
#     mocker.patch('udocker.engine.singularity.os.path.isdir', return_value=is_dir)
#     config = mocker.patch.object(Config, 'conf', {'env': {},
#                                                   'root_path': '',
#                                                   'tmpdir': '/tmp',
#                                                   'use_singularity_executable': [],
#                                                   'singularity_options': [],
#                                                   'sysdirs_list': (
#                                                       "/etc/resolv.conf", "/etc/host.conf", "/lib/modules",)})
#
#     if loglevel:
#         config.update(loglevel)
#
#     mocker.patch.object(singularity, '_run_init', lambda container_id: execpath)
#
#     assert singularity.run(container_id) == expected

# @patch.object(SingularityEngine, '_run_banner')
#     @patch.object(SingularityEngine, '_run_env_cleanup_dict')
#     @patch.object(SingularityEngine, '_get_volume_bindings')
#     @patch.object(SingularityEngine, '_run_env_set')
#     @patch.object(SingularityEngine, '_run_as_root')
#     @patch.object(SingularityEngine, 'select_singularity')
#     @patch.object(SingularityEngine, '_make_container_directories')
#     @patch.object(SingularityEngine, '_run_invalid_options')
#     @patch.object(SingularityEngine, '_run_init')
#     @patch('udocker.engine.singularity.subprocess.call')
#     @patch('udocker.engine.singularity.Unique.uuid')
#     @patch('udocker.engine.singularity.FileBind')
#     @patch('udocker.engine.singularity.os.path.isdir')
#     def test_08_run(self, mock_isdir, mock_fbind, mock_uuid, mock_call, mock_rinit, mock_rinvopt,
#                     mock_mkcontdir, mock_selsing, mock_runroot, mock_renvset, mock_getvolbind,
#                     mock_renvclean, mock_rbann):
#         """Test08 SingularityEngine().run()."""
#         mock_isdir.return_value = True
#         mock_fbind.return_value.container_orig_dir.return_value = "/d1"
#         mock_fbind.return_value.restore.return_value = None
#         mock_rinit.return_value = False
#         sing = SingularityEngine(self.local, self.xmode)
#         status = sing.run("CONTAINERID")
#         self.assertEqual(status, 2)
#
#         mock_isdir.return_value = True
#         mock_fbind.return_value.container_orig_dir.return_value = "/d1"
#         mock_fbind.return_value.restore.return_value = None
#         mock_rinit.return_value = "/cont/"
#         mock_rinvopt.return_value = None
#         mock_mkcontdir.return_value = None
#         mock_selsing.return_value = None
#         mock_runroot.return_value = None
#         mock_renvset.return_value = None
#         self.local.bindir = "/cont/bin"
#         mock_getvolbind.return_value = ['-B', '/home/user:/home/user',
#                                         '-B', '/tmp:/tmp',
#                                         '-B', '/var/tmp:/var/tmp']
#         mock_uuid.return_value = "EXECUTION_ID"
#         mock_renvclean.return_value = None
#         mock_rbann.return_value = None
#         mock_call.return_value = 0
#         sing = SingularityEngine(self.local, self.xmode)
#         sing.executable = "/bin/sing"
#         sing.opt["cmd"] = [""]
#         status = sing.run("CONTAINERID")
#         self.assertEqual(status, 0)
#
#
# if __name__ == '__main__':
#     main()
