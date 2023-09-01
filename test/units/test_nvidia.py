#!/usr/bin/env python
"""
udocker unit tests: NVIDIA mode
"""
import pytest
import random
from udocker.config import Config
from udocker.engine.nvidia import NvidiaMode
import collections

collections.Callable = collections.abc.Callable


@pytest.mark.parametrize("container_id", [str(random.randint(1, 1000))])
def test_01_init(mocker, container_id):
    """Test01 NvidiaMode() constructor."""
    cdir = "/" + container_id

    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mock_lrepo._container_id = container_id

    # this is mocked here, but should be tested in test_localrepo.py
    mock_lrepo.cd_container.return_value = cdir

    nvmode = NvidiaMode(mock_lrepo, container_id)

    assert nvmode.localrepo == mock_lrepo, f"localrepo {nvmode.localrepo} != {mock_lrepo}"
    assert nvmode.container_id == container_id, f"container_id {nvmode.container_id} != {container_id}"
    assert nvmode.container_dir == cdir, f"container_dir {nvmode.container_dir} != {cdir}"
    assert nvmode.container_root == cdir + "/ROOT", f"container_root {nvmode.container_root} != {cdir}/ROOT"
    assert nvmode._container_nvidia_set == cdir + "/nvidia", \
        f"_container_nvidia_set {nvmode._container_nvidia_set} != {cdir}/nvidia"
    assert nvmode._nvidia_main_libs == ("libnvidia-cfg.so", "libcuda.so",), \
        f"_nvidia_main_libs {nvmode._nvidia_main_libs} != ('libnvidia-cfg.so', 'libcuda.so', )"


@pytest.mark.parametrize("cont_dst_dir", ['some_dir'])
@pytest.mark.parametrize("files_list", [['a', 'b']])
def test_02__files_exist(mocker, cont_dst_dir, files_list):
    """Test02 NvidiaMode._files_exist."""
    mock_exists = mocker.patch('udocker.engine.nvidia.os.path.exists')
    mock_exists.return_value = False
    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())
    nvmode.container_root = '/home/.udocker/container'
    nvmode._files_exist(cont_dst_dir, files_list)

    mock_exists.assert_called()

    # assert if all files are checked
    assert mock_exists.call_count == len(files_list), f"call_count {mock_exists.call_count} != {len(files_list)}"
    assert mock_exists.call_args_list == [mocker.call('/home/.udocker/container/some_dir/a'),
                                          mocker.call('/home/.udocker/container/some_dir/b')], \
        f"call_args_list {mock_exists.call_args_list} != " \
        f"[call('/home/.udocker/container/some_dir/a'), call('/home/.udocker/container/some_dir/b')]"
    mock_exists.reset_mock()

    # assert if exception is raised
    with pytest.raises(OSError):
        mock_exists.return_value = True
        nvmode._files_exist(cont_dst_dir, files_list)

#TODO: check test_fileutils.py, init as feature
@pytest.mark.parametrize("hsrc_dir", ['/usr/lib'])
@pytest.mark.parametrize("cdst_dir", ['lib'])
@pytest.mark.parametrize("flist", [['a']])
@pytest.mark.parametrize("force", [False])
def test_03__copy_files(mocker, hsrc_dir, cdst_dir, flist, force):
    """Test03 NvidiaMode._copy_files."""

    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())
    nvmode.container_root = '/home/.udocker/cont/ROOT'

    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    mock_log.debug = mocker.MagicMock()
    mock_log.debug.side_effect = [None, None]

    mock_log.info = mocker.MagicMock()
    mock_log.info.side_effect = [None, None]

    # scenario link or file is true and force is false
    mock_isfile = mocker.patch('udocker.engine.nvidia.os.path.isfile', return_value=True)
    # empty_list
    state = nvmode._copy_files(hsrc_dir, cdst_dir, flist, force)

    # check if loggers are writing correctly
    assert isinstance(mock_log.debug, collections.Callable), f"mock_log.debug {mock_log.debug} is not callable"
    assert mock_log.debug.call_count == 2, f"call_count {mock_log.debug.call_count} != 2"
    assert mock_log.debug.call_args_list == [mocker.call('Source (host) dir %s', hsrc_dir),
                                             mocker.call('Destination (container) dir %s', cdst_dir)]

    # file or link exists
    dstname = nvmode.container_root + '/' + cdst_dir + '/' + flist[0]

    assert isinstance(mock_log.info, collections.Callable), f"mock_log.info {mock_log.info} is not callable"
    assert mock_log.info.call_count == 1, f"call_count {mock_log.info.call_count} != 1"
    assert mock_log.info.call_args_list == [mocker.call('nvidia file already exists %s, use --force to overwrite',
                                                        dstname)]

    assert state is False, f"state {state} != False"

    # scenario link or file is true and force is true
    mock_log.info.side_effect = [None, None]
    mock_log.debug.side_effect = [None, None]
    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())

    with pytest.raises(OSError):
        nvmode._copy_files(hsrc_dir, cdst_dir, flist, force=True)


    mock_rm = mocker.patch('udocker.engine.nvidia.os.remove')
    mock_dirname = mocker.patch('udocker.engine.nvidia.os.path.dirname')
    mock_isdir = mocker.patch('udocker.engine.nvidia.os.path.isdir')
    mock_mkdir = mocker.patch('udocker.engine.nvidia.os.makedirs')
    mock_chmod = mocker.patch('udocker.engine.nvidia.os.chmod')
    mock_readln = mocker.patch('udocker.engine.nvidia.os.readlink')
    mock_symln = mocker.patch('udocker.engine.nvidia.os.symlink')
    mock_copy2 = mocker.patch('udocker.engine.nvidia.shutil.copy2')
    mock_stat = mocker.patch('udocker.engine.nvidia.os.stat')
    mock_s_imode = mocker.patch('udocker.engine.nvidia.os.stat.S_IMODE')

    mock_access = mocker.patch('udocker.engine.nvidia.os.access')

    mock_log.info.side_effect = [None, None]
    mock_log.debug.side_effect = [None, None, None]
    mock_stat.side_effect = [mocker.Mock(st_mode=444), mocker.Mock(st_mode=222), mocker.Mock(st_mode=111)]
    mock_s_imode.side_effect = [644, 755]

    nvmode._copy_files(hsrc_dir, cdst_dir, flist, force=True)

    assert mock_log.info.call_count == 2, f"call_count {mock_log.info.call_count} != 2"
    assert mock_rm.call_count == 1, f"call_count {mock_rm.call_count} != 1"

# @patch('udocker.engine.nvidia.os.access')
# @patch('udocker.engine.nvidia.stat')
# @patch('udocker.engine.nvidia.shutil.copy2')
# @patch('udocker.engine.nvidia.os.symlink')
# @patch('udocker.engine.nvidia.os.readlink')
# @patch('udocker.engine.nvidia.os.chmod')
# @patch('udocker.engine.nvidia.os.makedirs')
# @patch('udocker.engine.nvidia.os.path.isdir')
# @patch('udocker.engine.nvidia.os.path.dirname')
# @patch('udocker.engine.nvidia.os.remove')
# @patch('udocker.engine.nvidia.os.path.islink')
# @patch('udocker.engine.nvidia.os.path.isfile')
# def test_03__copy_files(self, mock_isfile, mock_islink, mock_rm, mock_dirname, mock_isdir,
#                         mock_mkdir, mock_chmod, mock_readln, mock_symln, mock_copy2,
#                         mock_stat, mock_access):
#     """Test03 NvidiaMode._copy_files."""
#     hsrc_dir = "/usr/lib"
#     cdst_dir = "/hone/.udocker/cont/ROOT/usr/lib"
#     flist = ["a"]
#     force = False
#     mock_isfile.side_effect = [True, False] #
#     mock_islink.side_effect = [True, False] #
#     mock_rm.return_value = None
#     nvmode = NvidiaMode(self.local, self.cont_id)
#     status = nvmode._copy_files(hsrc_dir, cdst_dir, flist, force)
#     self.assertFalse(status)
#     self.assertTrue(mock_isfile.called)
#
#     force = True
#     mock_isfile.side_effect = [True, True]
#     mock_islink.side_effect = [True, False]
#     mock_dirname.side_effect = [None, None]
#     mock_rm.return_value = None
#     mock_isdir.return_value = True
#     mock_mkdir.return_value = None
#     mock_chmod.side_effect = [644, 755]
#     mock_readln.return_value = "/usr/xxx"
#     mock_symln.return_value = None
#     mock_copy2.return_value = None
#     mock_stat.side_effect = [444, 222, 111, 111]
#     mock_access.return_value = False
#     nvmode = NvidiaMode(self.local, self.cont_id)
#     status = nvmode._copy_files(hsrc_dir, cdst_dir, flist, force)
#     self.assertTrue(status)
#     self.assertTrue(mock_isfile.called)
#     self.assertTrue(mock_rm.called)


@pytest.mark.parametrize("host_dir", ['/usr/lib'])
def test_04__get_nvidia_libs(mocker, host_dir):
    """Test04 NvidiaMode._get_nvidia_libs."""

    Config.conf['nvi_lib_list'] = ['/lib/libnvidia.so']
    mock_glob = mocker.patch('udocker.engine.nvidia.glob.glob')
    mock_glob.return_value = ['/lib/libnvidia.so']

    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())
    nvidia_libs = nvmode._get_nvidia_libs(host_dir)

    assert nvidia_libs == Config.conf['nvi_lib_list'], f"status {nvidia_libs} != {Config.conf['nvi_lib_list']}"

    # check if loggers are writting correctly
    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    mock_log.debug = mocker.MagicMock()
    mock_log.debug.side_effect = [None, None]

    nvmode._get_nvidia_libs(host_dir)

    assert isinstance(mock_log.debug, collections.Callable)
    assert mock_log.debug.call_count == 1
    assert mock_log.debug.call_args_list == [mocker.call('list nvidia libs: %s', Config.conf['nvi_lib_list'])]


@pytest.mark.parametrize('arch', ['x86-64'])
def test_05__find_host_dir_ldconfig(mocker, arch):
    """Test05 NvidiaMode._find_host_dir_ldconfig."""
    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())

    mock_realp = mocker.patch('udocker.engine.nvidia.os.path.realpath')
    mock_realp.return_value = "/lib/x86_64-linux-gnu"
    mock_dname = mocker.patch('udocker.engine.nvidia.os.path.dirname')
    mock_dname.return_value = "/lib/x86_64-linux-gnu"

    mock_uproc = mocker.patch('udocker.engine.nvidia.Uprocess.get_output')
    mock_uproc.return_value = (' libnvidia-cfg.so (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libnvidia-cfg.so\n,'
                               ' libcuda.so (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libcuda.so\n')

    dir_list = nvmode._find_host_dir_ldconfig(arch)

    assert dir_list == {"/lib/x86_64-linux-gnu/"}, f"dir_list {dir_list} != {set(['/lib/x86_64-linux-gnu/'])}"

    # check if loggers are writing correctly
    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    mock_log.debug = mocker.MagicMock()

    # flush mock_log.debug
    mock_log.debug.side_effect = [None, None]
    nvmode._find_host_dir_ldconfig(arch)

    assert isinstance(mock_log.debug, collections.Callable)
    assert mock_log.debug.call_count == 1
    assert mock_log.debug.call_args_list == [mocker.call('list nvidia libs via ldconfig: %s', dir_list)]


@pytest.mark.parametrize('library_path', ['/usr/lib:/lib/x86_64-linux-gnu'])
def test_06__find_host_dir_ldpath(mocker, library_path):
    """Test06 NvidiaMode._find_host_dir_ldpath."""
    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())

    mock_glob = mocker.patch('udocker.engine.nvidia.glob.glob')
    mock_glob.return_value = ["/usr/lib/x86_64-linux-gnu"]

    dir_list = nvmode._find_host_dir_ldpath(library_path)
    print(dir_list)

    assert dir_list == {"/usr/lib/", "/usr/lib/x86_64-linux-gnu/"}, \
        f"dir_list {dir_list} != {set(['/lib/x86_64-linux-gnu/'])}"

    # check if loggers are writing correctly
    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    mock_log.debug = mocker.MagicMock()
    mock_log.debug.side_effect = [None, None]
    dir_list = nvmode._find_host_dir_ldpath(library_path)

    assert isinstance(mock_log.debug, collections.Callable)
    assert mock_log.debug.call_count == 1
    assert mock_log.debug.call_args_list == [mocker.call('list nvidia libs via path: %s', dir_list)]


def test_07__find_host_dir(mocker):
    """Test07 NvidiaMode._find_host_dir."""
    mock_ldpath = mocker.patch('udocker.engine.nvidia.NvidiaMode._find_host_dir_ldpath')
    mock_ldpath.return_value = set()

    mock_ldconf = mocker.patch('udocker.engine.nvidia.NvidiaMode._find_host_dir_ldconfig')
    mock_ldconf.return_value = set()

    # scenario empty set
    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())
    dir_list = nvmode._find_host_dir()

    assert mock_ldpath.called
    assert mock_ldconf.called
    assert dir_list == set(), f"status {dir_list} != {set()}"

    # scenario with _find_host_dir_ldconfig() returning a set with a value
    mock_ldpath.side_effect = [set(), set()]
    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())
    mock_ldconf.return_value = {"/lib/x86_64-linux-gnu/"}

    status = nvmode._find_host_dir()
    assert status == {'/lib/x86_64-linux-gnu/'}, f"status {status} != {'/lib/x86_64-linux-gnu/'}"

    # scenario with _find_host_dir_ldpath() and _find_host_dir_ldconfig() returning a set with a value
    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())

    mocker.patch('udocker.engine.nvidia.NvidiaMode._find_host_dir_ldpath',
                 return_value={'/lib/x86_64-linux-gnu/', "/usr/lib/"})

    mock_ldconf.return_value = {"/lib/x86_64-linux-gnu/"}

    # check loggers
    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    mock_log.debug = mocker.MagicMock()

    status = nvmode._find_host_dir()
    assert status == {'/lib/x86_64-linux-gnu/', "/usr/lib/"}, \
        f"status {status} != {'/lib/x86_64-linux-gnu/', '/usr/lib/'}"
    assert mock_log.debug.call_args_list == [mocker.call('host location nvidia: %s', status)]


def test_08__find_cont_dir(mocker):
    """Test08 NvidiaMode._find_cont_dir."""
    mock_isdir = mocker.patch('udocker.engine.nvidia.os.path.isdir')

    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())
    nvmode.container_root = '/home/.udocker/cont'
    mock_isdir.return_value = False

    state = nvmode._find_cont_dir()
    assert state == '', f"state {state} != ''"

    mock_isdir.return_value = True
    state = nvmode._find_cont_dir()
    assert state == '/usr/lib/x86_64-linux-gnu', f"state {state} != '/usr/lib/x86_64-linux-gnu'"

    # check loggers
    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    mock_log.debug = mocker.MagicMock()
    mock_log.debug.side_effect = [None, None]

    nvmode._find_cont_dir()

    assert isinstance(mock_log.debug, collections.Callable)
    assert mock_log.debug.call_count == 1
    assert mock_log.debug.call_args_list == [mocker.call('cont. location nvidia: %s', state)]


@pytest.mark.parametrize("host_dir", [['/usr/lib'], ])
@pytest.mark.parametrize("cont_dir", ['/home/.udocker/cont/usr/lib', ])
def test_09__installation_exists(mocker, host_dir, cont_dir):
    """Test09 NvidiaMode._installation_exists."""
    files_exists = mocker.patch('udocker.engine.nvidia.os.path.exists')
    mock_file_exist = mocker.patch('udocker.engine.nvidia.NvidiaMode._files_exist')

    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())
    instalation_exists = nvmode._installation_exists(host_dir, cont_dir)
    nvmode._nvidia_main_libs = ('libnvidia-cfg.so', 'libcuda.so',)
    nvmode._container_root = '/home/.udocker/cont'

    files_exists.return_value = False
    mock_file_exist.return_value = None

    assert instalation_exists is False

    # check if logger
    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    mock_log.info = mocker.MagicMock()
    mock_log.info.side_effect = [None, None]
    nvmode._installation_exists(host_dir, cont_dir)
    assert isinstance(mock_log.info, collections.Callable)
    assert mock_log.info.call_count == 1
    assert mock_log.info.call_args_list == [mocker.call('container has files from previous nvidia install')]

    # exception OSError
    mocker.patch('udocker.engine.nvidia.os.path.exists', return_value=True)
    mocker.patch('udocker.engine.nvidia.NvidiaMode._files_exist', side_effect=OSError("fail"))
    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())

    # the exception is raised, but the function returns True
    assert nvmode._installation_exists(host_dir, cont_dir) is True, \
        f"status {nvmode._installation_exists(host_dir, cont_dir)} != True"

#
# @patch('udocker.engine.nvidia.FileUtil.putdata')
# @patch.object(NvidiaMode, '_copy_files')
# @patch.object(NvidiaMode, '_get_nvidia_libs')
# @patch.object(NvidiaMode, '_installation_exists')
# @patch.object(NvidiaMode, '_find_cont_dir')
# @patch.object(NvidiaMode, '_find_host_dir')
# def test_10_set_mode(self, mock_findhdir, mock_findcdir, mock_instexist, mock_libs,
#                      mock_cpfiles, mock_futilput):
#     """Test10 NvidiaMode.set_mode()."""
#     self.mock_cdcont.return_value = ""
#     nvmode = NvidiaMode(self.local, self.cont_id)
#     status = nvmode.set_mode()
#     self.assertFalse(status)
#
#     self.mock_cdcont.return_value = "/home/.udocker/cont"
#     mock_findhdir.return_value = set()
#     mock_findcdir.return_value = "/usr/lib/x86_64-linux-gnu"
#     nvmode = NvidiaMode(self.local, self.cont_id)
#     nvmode.container_dir = "/" + self.cont_id
#     status = nvmode.set_mode()
#     self.assertFalse(status)
#
#     self.mock_cdcont.return_value = "/home/.udocker/cont"
#     host_dir = set()
#     mock_findhdir.return_value = host_dir.update("/usr/lib")
#     mock_findcdir.return_value = ""
#     nvmode = NvidiaMode(self.local, self.cont_id)
#     nvmode.container_dir = "/" + self.cont_id
#     status = nvmode.set_mode()
#     self.assertFalse(status)
#
#     # TODO: need work
#     self.mock_cdcont.return_value = "/home/.udocker/cont"
#     host_dir = set()
#     host_dir.add("/usr/lib")
#     mock_findhdir.return_value = host_dir
#     mock_findcdir.return_value = "/usr/lib/x86_64-linux-gnu"
#     mock_libs.return_value = ['/lib/libnvidia.so']
#     mock_instexist.return_value = False
#     mock_cpfiles.side_effect = [True, True, True]
#     mock_futilput.return_value = None
#     nvmode = NvidiaMode(self.local, self.cont_id)
#     nvmode.container_dir = "/" + self.cont_id
#     status = nvmode.set_mode(True)
#     self.assertTrue(mock_findhdir.called)
#     self.assertTrue(mock_findcdir.called)
#     # self.assertTrue(mock_instexist.called)
#     # self.assertTrue(mock_futilput.called)
#     # self.assertTrue(status)
#

def test_11_get_mode(mocker):
    """Test11 NvidiaMode.get_mode()."""
    os_exists = mocker.patch('udocker.engine.nvidia.os.path.exists')

    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())
    nvmode._container_nvidia_set = '/home/.udocker/container/nvidia'

    mode = nvmode.get_mode()
    assert mode == os_exists.return_value, f"status {mode} != {os_exists.return_value}"

    os_exists.side_effect = [True]
    mode = nvmode.get_mode()
    assert mode is True, f"status {mode} != True"

    os_exists.side_effect = [False]
    mode = nvmode.get_mode()
    assert mode is False, f"status {mode} != False"

    os_exists.call_args_list = [mocker.call(nvmode._container_nvidia_set)]
    assert os_exists.called
    assert os_exists.call_args_list == [mocker.call(nvmode._container_nvidia_set)], \
        f"call_args_list {os_exists.call_args_list} != [call({nvmode._container_nvidia_set})]"


def test_12_get_devices(mocker):
    """Test12 NvidiaMode.get_devices()."""
    mock_glob = mocker.patch('udocker.engine.nvidia.glob.glob')
    mock_glob.return_value = ['/dev/nvidia']
    nvmode = NvidiaMode(mocker.MagicMock(), mocker.MagicMock())
    devices = nvmode.get_devices()
    assert devices == Config().conf['nvi_dev_list'], f"status {devices} != {Config().conf['nvi_dev_list']}"

    # check logger
    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    mock_log.debug = mocker.MagicMock()
    mock_log.debug.side_effect = [None, None]
    nvmode.get_devices()
    assert isinstance(mock_log.debug, collections.Callable)
    assert mock_log.debug.call_count == 1, f"call_count {mock_log.debug.call_count} != 1"
    assert mock_log.debug.call_args_list == [mocker.call('nvidia device list: %s', Config().conf['nvi_dev_list'])]
