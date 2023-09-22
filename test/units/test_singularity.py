#!/usr/bin/env python
"""
udocker unit tests: SingularityEngine
"""
import random
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
def mock_sing_engine(lrepo):
    mode = mock.patch('udocker.engine.execmode.ExecutionMode')
    return SingularityEngine(lrepo, mode.start())


@pytest.fixture
def os_path(mocker):
    return mocker.patch('udocker.engine.singularity.os.path.exists')


@pytest.fixture
def isdir(mocker):
    return mocker.patch('udocker.engine.singularity.os.path.isdir')


@pytest.fixture
def tmpdir(tmpdir_factory):
    return tmpdir_factory.mktemp("singularity")


@pytest.fixture
def fileutil(mocker):
    return mocker.patch('udocker.engine.singularity.FileUtil')


@pytest.fixture
def mkdir(mocker):
    return mocker.patch('udocker.engine.singularity.FileUtil.mkdir')


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.engine.singularity.LOG')


@pytest.fixture
def hostusername(mocker):
    return mocker.patch('udocker.engine.singularity.HostInfo.username')


@pytest.fixture
def nixauth(mocker):
    return mocker.patch('udocker.engine.singularity.NixAuthentication')


@pytest.fixture
def nixaut_gethome(mocker):
    return mocker.patch('udocker.engine.singularity.NixAuthentication.get_home')


@pytest.fixture
def hasopt(mocker):
    return mocker.patch('udocker.engine.singularity.SingularityEngine._has_option')


def test_01_init(mock_sing_engine, tmpdir):
    """Test the init() function"""
    engine = SingularityEngine(tmpdir, None)
    assert engine.executable is None
    assert engine.execution_id is None


select_singularity_data = (
    (True, None, "/bin/runc-arm", "i386", 0, "Error: singularity executable not found"),
    (True, "UDOCKER", "/bin/runc-arm", "i386", 0, "Error: singularity executable not found"),
    (False, "UDOCKER", "/bin/runc-arm", "", 1, ""),
    (False, "UDOCKER", "", "amd64", 1, ""),
)


@pytest.mark.parametrize("os_exists,executable,findexec,arch,logcount,loggermsg", select_singularity_data)
def test_02_select_singularity(mock_sing_engine, fileutil, tmpdir, logger, os_path, os_exists, executable, findexec,
                               arch, logcount, loggermsg):
    """Test the select_singularity() function"""

    Config.conf['use_singularity_executable'] = executable
    fileutil.return_value.find_exec.return_value = findexec
    os_path.return_value = os_exists
    fileutil.return_value.find_file_in_dir.return_value = findexec
    fileutil.find_file_in_dir.return_value = "singularity-x86_64"

    logger.error.reset_mock()
    if os_exists:
        mock_sing_engine.select_singularity()
    else:
        with pytest.raises(SystemExit) as exit_code:
            mock_sing_engine.select_singularity()
            assert exit_code.type == SystemExit
            assert exit_code.value.code == 1
            assert logger.error.call_args_list == [mock.call(loggermsg)]

    assert logger.error.call_count == logcount
    assert mock_sing_engine.executable == findexec


volume_bindings_data = (
    (["/dir1", "/home/user"], "", True, ['-B', '/dir1:/dir1', '-B', '/home/user:/home/user', '--home', '/root:/root',
                                         '-B', '/tmp:/tmp', '-B', '/var/tmp:/var/tmp']),
    (["/home/user", "/tmp", "/var/tmp"], "/home/user", True, ['-B', '/home/user:/home/user', '-B', '/tmp:/tmp',
                                                              '-B', '/var/tmp:/var/tmp']),
    (["/home/user", "/tmp", "/var/tmp"], "/home/user", True, ['-B', '/home/user:/home/user', '-B', '/tmp:/tmp',
                                                              '-B', '/var/tmp:/var/tmp']),
    (["/dir1"], "/home/user", False, ['-B', '/dir1:/dir1', '--home', '/root:/root', '-B', '/tmp:/tmp',
                                      '-B', '/var/tmp:/var/tmp']),
    ([], "/home/user", True, ['--home', '/root:/root', '-B', '/tmp:/tmp', '-B', '/var/tmp:/var/tmp']),
)


@pytest.mark.parametrize("vol,home,istmp,expected", volume_bindings_data)
def test_03__get_volume_bindings(mock_sing_engine, nixaut_gethome, isdir, vol, home, istmp, expected):
    """Test the _get_volume_bindings() function"""
    isdir.side_effect = [istmp for _ in vol]
    mock_sing_engine.opt['vol'] = vol
    nixaut_gethome.return_value = home
    status = mock_sing_engine._get_volume_bindings()

    assert status == expected


singularity_env_get_data = (
    ([("AA", "aa"), ("BB", "bb")], {"SINGULARITYENV_AA": "aa", "SINGULARITYENV_BB": "bb"}),
    ([], {})
)


@pytest.mark.parametrize("envkeys,expected", singularity_env_get_data)
def test_04__singularity_env_get(mock_sing_engine, envkeys, expected):
    """Test04 SingularityEngine()._singularity_env_get()."""
    mock_sing_engine.opt['env'] = envkeys
    status = mock_sing_engine._singularity_env_get()
    assert status == expected


def test_05__make_container_dirs(mock_sing_engine, mkdir):
    """Test05 SingularityEngine()._make_container_directories()."""
    mkdir.side_effect = [True, True, True, True, True, True]
    mock_sing_engine._make_container_directories()
    assert mkdir.call_count == 6


invalid_options_data = (
    ("netcoop", "portsmap", 2, [mock.call("this execution mode does not support -p --publish"),
                     mock.call("Warning: this exec mode does not support -P --netcoop --publish-all")]),
    (None, None, 0, []),
)


@pytest.mark.parametrize("portsmap,netcoop,logcount,call", invalid_options_data)
def test_06__run_invalid_options(mock_sing_engine, logger, portsmap, netcoop, logcount, call):
    """Test06 SingularityEngine()._run_invalid_options()."""
    mock_sing_engine.opt['netcoop'] = netcoop
    mock_sing_engine.opt['portsmap'] = portsmap
    mock_sing_engine._run_invalid_options()
    assert logger.warning.call_count == logcount
    assert logger.warning.call_args_list == call


run_as_root_data = (
    ("u1", 1001, "u1", 0, [], False),
    ("u1", 1001, "u2", 1, [mock.call("running as another user not supported")], False),
    ("root", 1001, "u1", 0, [], True),
    (None, 1001, "u1", 0, [], False),
)


@pytest.mark.parametrize("envuname,envuid,uname,logcount,loggermsg,expected", run_as_root_data)
def test_07__run_as_root(mock_sing_engine, hostusername, nixauth, hasopt, logger, envuname, envuid, uname, logcount,
                         loggermsg, expected):
    """Test07 SingularityEngine()._run_as_root()."""
    Config.conf['singularity_options'] = []
    mock_sing_engine.opt['user'] = envuname
    mock_sing_engine.opt['uid'] = envuid

    hostusername.return_value = uname
    nixauth.user_in_subuid.return_value = True
    nixauth.user_in_subgid.return_value = True

    if envuname is None:
        mock_sing_engine.opt.pop('user')

    status = mock_sing_engine._run_as_root()

    assert status == expected
    assert logger.warning.call_count == logcount
    assert logger.warning.call_args_list == loggermsg
    assert ('--fakeroot' in Config.conf['singularity_options']) == expected


@pytest.fixture
def run_init(mocker):
    return mocker.patch('udocker.engine.singularity.SingularityEngine._run_init')


@pytest.fixture
def select_singularity(mocker):
    return mocker.patch('udocker.engine.singularity.SingularityEngine.select_singularity')


run_data = (
    #("", 2),
    ("/home/user/execpath", "/home/user/container", "root", 2),
)


# @pytest.mark.parametrize("execpath,croot,uname,expected", run_data)
# def test_08_run(mock_sing_engine, container_id, run_init, nixauth, select_singularity,
#                 execpath, croot, uname,
#                 expected):
#     """Test08 SingularityEngine().run()."""
#     run_init.return_value = execpath
#     mock_sing_engine.container_root = croot

#     mock_sing_engine.opt["cmd"] = [["/bin/bash"], ]
#     mock_sing_engine.opt["portsmap"] = None
#     mock_sing_engine.opt["netcoop"] = None  # TODO: check this opt is not in default
#     mock_sing_engine.opt['user'] = uname
#     mock_sing_engine.opt['uid'] = 1001
#     mock_sing_engine.opt['home'] = "/home/user"
#     select_singularity.return_value = "execpath"

#     hostusername.return_value = uname
#     nixauth.user_in_subuid.return_value = True
#     nixauth.user_in_subgid.return_value = True

#     status = mock_sing_engine.run(container_id)
#     assert status == expected


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
