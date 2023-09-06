#!/usr/bin/env python
"""
udocker unit tests: NVIDIA mode
"""
import mock
import pytest
import random

from udocker import LOG
from udocker.config import Config
from udocker.engine.nvidia import NvidiaMode
import collections

collections.Callable = collections.abc.Callable


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def lrepo(mocker, container_id):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mock_lrepo._container_id = container_id
    return mock_lrepo


@pytest.fixture
def mock_nvidia(lrepo, container_id):
    mock_nvidia = NvidiaMode(lrepo, container_id)
    mock_nvidia._nvidia_main_libs = ('libnvidia-cfg.so', 'libcuda.so',)
    mock_nvidia._container_root = '/home/.udocker/cont'
    return mock_nvidia


@pytest.fixture
def cont_dst_dir():
    return 'some_dir'


@pytest.fixture
def host_src_dir():
    return '/usr/lib'


@pytest.fixture
def files_list():
    return ['a', 'b']


@pytest.fixture
def logger(mocker):
    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    return mock_log


@pytest.fixture
def glob(mocker):
    mock_glob = mocker.patch('udocker.engine.nvidia.glob.glob', return_value=['/dev/nvidia'])
    return mock_glob


@pytest.fixture
def os_path_exists(mocker):
    mock_exists = mocker.patch('udocker.engine.nvidia.os.path.exists')
    return mock_exists


@pytest.fixture
def is_dir(mocker):
    mock_isdir = mocker.patch('udocker.engine.nvidia.os.path.isdir')
    return mock_isdir

@pytest.fixture
def ldpath(mocker, mock_nvidia):
    mock_ldpath = mocker.patch('udocker.engine.nvidia.NvidiaMode._find_host_dir_ldpath')
    mock_ldpath.return_value = set()
    return mock_ldpath

@pytest.fixture
def ldconf(mocker, mock_nvidia):
    mock_ldconf = mocker.patch('udocker.engine.nvidia.NvidiaMode._find_host_dir_ldconfig')
    mock_ldconf.return_value = set()
    return mock_ldconf


@pytest.fixture
def arch():
    return 'x86-64'


@pytest.fixture
def realpath(mocker):
    mock_realp = mocker.patch('udocker.engine.nvidia.os.path.realpath')
    return mock_realp


@pytest.fixture
def dirname(mocker):
    mock_dname = mocker.patch('udocker.engine.nvidia.os.path.dirname')
    return mock_dname


@pytest.fixture
def getoutput(mocker):
    mock_getoutput = mocker.patch('udocker.engine.nvidia.Uprocess.get_output')
    return mock_getoutput

@pytest.fixture
def isfile(mocker):
    mock_isfile = mocker.patch('udocker.engine.nvidia.os.path.isfile')
    return mock_isfile

@pytest.fixture
def os_access(mocker):
    mock_access = mocker.patch('udocker.engine.nvidia.os.access')
    return mock_access

@pytest.fixture
def stat(mocker):
    mock_stat = mocker.patch('udocker.engine.nvidia.os.stat')
    return mock_stat

@pytest.fixture
def s_imode(mocker):
    mock_s_imode = mocker.patch('udocker.engine.nvidia.os.stat.S_IMODE')
    return mock_s_imode


@pytest.fixture
def os_remove(mocker):
    mock_remove = mocker.patch('udocker.engine.nvidia.os.remove')
    return mock_remove


@pytest.fixture
def os_makedirs(mocker):
    mock_makedirs = mocker.patch('udocker.engine.nvidia.os.makedirs')
    return mock_makedirs


@pytest.fixture
def os_chmod(mocker):
    mock_chmod = mocker.patch('udocker.engine.nvidia.os.chmod')
    return mock_chmod


@pytest.fixture
def os_readlink(mocker):
    mock_readlink = mocker.patch('udocker.engine.nvidia.os.readlink')
    return mock_readlink



@pytest.fixture
def os_symlink(mocker):
    mock_symlink = mocker.patch('udocker.engine.nvidia.os.symlink')
    return mock_symlink


@pytest.fixture
def shutil_copy2(mocker):
    mock_copy2 = mocker.patch('udocker.engine.nvidia.shutil.copy2')
    return mock_copy2




installation_data = [(["/home/.udocker/cont/usr/lib", ], ['/home/.udocker/cont/usr/lib', ])]
copy_files_data = [('/usr/lib', 'lib', ['a'], False)]

#('/usr/lib', 'lib', ['a'], True)

def test_01_init(mock_nvidia, lrepo, container_id):
    """Test01 NvidiaMode() constructor."""
    cdir = lrepo.cd_container(container_id)

    assert mock_nvidia.localrepo == lrepo, f"localrepo {mock_nvidia.localrepo} != {lrepo}"
    assert mock_nvidia.container_id == container_id, f"container_id {mock_nvidia.container_id} != {container_id}"
    assert mock_nvidia.container_dir == cdir, f"container_dir {mock_nvidia.container_dir} != {cdir}"
    assert mock_nvidia.container_root == cdir + "/ROOT", f"container_root {mock_nvidia.container_root} != {cdir}/ROOT"
    assert mock_nvidia._container_nvidia_set == cdir + "/nvidia", \
        f"_container_nvidia_set {mock_nvidia._container_nvidia_set} != {cdir}/nvidia"
    assert mock_nvidia._nvidia_main_libs == ("libnvidia-cfg.so", "libcuda.so",), \
        f"_nvidia_main_libs {mock_nvidia._nvidia_main_libs} != ('libnvidia-cfg.so', 'libcuda.so',)"

def test_02__files_exist(mocker, cont_dst_dir, files_list, mock_nvidia, os_path_exists):
    """Test02 NvidiaMode._files_exist."""
    os_path_exists.return_value = False
    mock_nvidia._files_exist(cont_dst_dir, files_list)
    os_path_exists

    # assert if all files are checked
    assert os_path_exists.call_count == len(files_list), f"call_count {os_path_exists.call_count} != {len(files_list)}"
    assert os_path_exists.call_args_list == [mocker.call(mock_nvidia.container_root + '/' + cont_dst_dir + '/' + fname)
                                             for fname in files_list]
    # assert if exception is raised
    with pytest.raises(OSError):
        os_path_exists.return_value = True
        mock_nvidia._files_exist(cont_dst_dir, files_list)


@pytest.mark.parametrize('fixture_name', ['foo', 'bar'], indirect=True)
def test_03__copy_files(mocker, mock_nvidia, hsrc_dir, cdst_dir, flist, force, isfile, os_remove, logger):
    """Test03 NvidiaMode._copy_files."""

    mock_nvidia.container_root = '/home/.udocker/cont/ROOT'

    # scenario link or file is true and force is false, this should return false
    isfile.return_value = True
    copy_files = mock_nvidia._copy_files(hsrc_dir, cdst_dir, flist, force)

    # check if loggers are writing correctly
    assert logger.debug.call_count == 2, f""
    assert logger.debug.call_args_list == [mocker.call('Source (host) dir %s', hsrc_dir),
                                           mocker.call('Destination (container) dir %s', cdst_dir)], \
        f"call_args_list {logger.debug.call_args_list} != [mocker.call('Source (host) dir %s', hsrc_dir)," \
        f"mocker.call('Destination (container) dir %s', cdst_dir)]"

    # file or link exists
    dstname = mock_nvidia.container_root + '/' + cdst_dir + '/' + flist[0]
    assert logger.info.call_count == 1, f"call_count {logger.info.call_count} != 1"
    assert logger.info.call_args_list == [mocker.call('nvidia file already exists %s, use --force to overwrite',
                                                      dstname)]

    assert logger.debug.call_count == 2, f"call_count {logger.debug.call_count} != 2"
    assert logger.debug.call_args_list == [mocker.call('Source (host) dir %s', hsrc_dir),
                                           mocker.call('Destination (container) dir %s', cdst_dir)], \
        f"call_args_list {logger.debug.call_args_list} != [mocker.call('Source (host) dir %s', hsrc_dir)," \
        f"mocker.call('Destination (container) dir %s', cdst_dir)]"

    assert copy_files is False, f"state {copy_files} != False"

    # file or link, force is true
    logger.reset_mock()
    force = True
    os_remove.return_value = None

    copy_files = mock_nvidia._copy_files(hsrc_dir, cdst_dir, flist, force)
    logger.info.call_count == 1, f"call_count {logger.info.call_count} != 1"
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
    mock_symln = mocker.patch('udocker.engine.nvidia.os.symlink') #
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


def test_04__get_nvidia_libs(mocker, mock_nvidia, host_src_dir, logger):
    """Test04 NvidiaMode._get_nvidia_libs."""

    Config.conf['nvi_lib_list'] = ['/lib/libnvidia.so']
    mock_glob = mocker.patch('udocker.engine.nvidia.glob.glob')
    mock_glob.return_value = ['/lib/libnvidia.so']

    nvidia_libs = mock_nvidia._get_nvidia_libs(host_src_dir)

    assert nvidia_libs == Config.conf['nvi_lib_list'], f"status {nvidia_libs} != {Config.conf['nvi_lib_list']}"

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('list nvidia libs: %s', Config.conf['nvi_lib_list'])]


def test_05__find_host_dir_ldconfig(mocker, mock_nvidia, arch, realpath, dirname, getoutput, logger):
    """Test05 NvidiaMode._find_host_dir_ldconfig."""

    realpath.return_value = "/lib/x86_64-linux-gnu"
    dirname.return_value = "/lib/x86_64-linux-gnu"
    getoutput.return_value = (' libnvidia-cfg.so (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libnvidia-cfg.so\n,'
                               ' libcuda.so (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libcuda.so\n')

    find_host_dir_ldconfig = mock_nvidia._find_host_dir_ldconfig(arch)

    assert find_host_dir_ldconfig == {"/lib/x86_64-linux-gnu/"}, \
        f"dir_list {find_host_dir_ldconfig} != {set(['/lib/x86_64-linux-gnu/'])}"

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('list nvidia libs via ldconfig: %s', find_host_dir_ldconfig)]


def test_06__find_host_dir_ldpath(mocker, mock_nvidia, glob, logger):
    """Test06 NvidiaMode._find_host_dir_ldpath."""
    glob.return_value = ["/usr/lib/x86_64-linux-gnu"]
    library_path = '/usr/lib:/lib/x86_64-linux-gnu'

    host_dir_ldpath = mock_nvidia._find_host_dir_ldpath(library_path)

    assert host_dir_ldpath == {"/usr/lib/", "/usr/lib/x86_64-linux-gnu/"}, \
        f"dir_list {host_dir_ldpath} != {set(['/lib/x86_64-linux-gnu/'])}"

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('list nvidia libs via path: %s', host_dir_ldpath)]


def test_07__find_host_dir(mocker, mock_nvidia, ldconf, ldpath, logger):
    """Test07 NvidiaMode._find_host_dir."""
    # scenario empty set
    find_host_dir = mock_nvidia._find_host_dir()

    assert ldpath.called
    assert ldconf.called
    assert find_host_dir == set(), f"status {find_host_dir} != {set()}"

    # scenario with _find_host_dir_ldconfig() returning a set with a value
    ldpath.return_value = {"/lib/x86_64-linux-gnu/"}

    # scenario with _find_host_dir_ldpath() and _find_host_dir_ldconfig() returning a set with a value
    ldpath.return_value = {'/lib/x86_64-linux-gnu/', "/usr/lib/"}
    ldconf.return_value = {'/lib/x86_64-linux-gnu/'}

    logger.debug.call_count = 0  # flush logger.debug
    find_host_dir = mock_nvidia._find_host_dir()
    assert find_host_dir == {'/lib/x86_64-linux-gnu/', '/usr/lib/'}, \
        f"status {find_host_dir} != {'/lib/x86_64-linux-gnu/', '/usr/lib/'}"

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('host location nvidia: %s', set()),
                                           mocker.call('host location nvidia: %s', find_host_dir)]


def test_08__find_cont_dir(mocker, mock_nvidia, is_dir, logger):
    """Test08 NvidiaMode._find_cont_dir."""
    is_dir.return_value = False

    find_cont_dir = mock_nvidia._find_cont_dir()
    assert find_cont_dir == '', f"state {find_cont_dir} != ''"

    is_dir.return_value = True
    find_cont_dir = mock_nvidia._find_cont_dir()
    assert find_cont_dir == '/usr/lib/x86_64-linux-gnu', f"state {find_cont_dir} != '/usr/lib/x86_64-linux-gnu'"

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('cont. location nvidia: %s', find_cont_dir)]


@pytest.mark.parametrize("host_dir,cont_dir", installation_data)
def test_09__installation_exists(mocker, mock_nvidia, host_dir, cont_dir, os_path_exists, logger):
    """Test09 NvidiaMode._installation_exists."""
    mock_file_exist = mocker.patch('udocker.engine.nvidia.NvidiaMode._files_exist')

    installation_exists = mock_nvidia._installation_exists(host_dir, cont_dir)
    os_path_exists.return_value = False
    mock_file_exist.return_value = True

    assert installation_exists is False

    # check loggers
    assert logger.info.call_count == 1
    assert logger.info.call_args_list == [mocker.call('container has files from previous nvidia install')]

    # exception OSError
    os_path_exists.return_value = True
    mock_file_exist.side_effect = OSError

    installation_exists = mock_nvidia._installation_exists(host_dir, cont_dir)
    assert installation_exists is True, f"status {installation_exists} != True"


#
# @patch('udocker.engine.nvidia.FileUtil.putdata')
@mock.patch('udocker.engine.nvidia.nvidia._copy_files')
@mock.patch('udocker.engine.nvidia.nvidia._get_nvidia_libs')
@mock.patch('udocker.engine.nvidia.nvidia._installation_exists')
@mock.patch('udocker.engine.nvidia.nvidia._find_cont_dir')
@mock.patch('udocker.engine.nvidia.nvidia._find_host_dir')
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

def test_11_get_mode(mocker, mock_nvidia, os_path_exists):
    """Test11 NvidiaMode.get_mode()."""
    os_path_exists.side_effect = [True, False]
    mock_nvidia._container_nvidia_set = '/home/.udocker/container/nvidia'

    mode = mock_nvidia.get_mode()
    assert mode is True, f"status {mode} != True"

    mode = mock_nvidia.get_mode()
    assert mode is False, f"status {mode} != False"

    # check loggers
    assert os_path_exists.call_count == 2, f"call_count {os_path_exists.call_count} != 2"
    assert os_path_exists.called, f"mock_os_path_exists {os_path_exists} is not called"
    assert os_path_exists.call_args_list == [mocker.call(mock_nvidia._container_nvidia_set),
                                             mocker.call(mock_nvidia._container_nvidia_set)], \
        f"call_args_list {os_path_exists.call_args_list} != [mocker.call(mock_nvidia._container_nvidia_set)]"


def test_12_get_devices(mocker, mock_nvidia, glob, logger):
    """Test12 NvidiaMode.get_devices()."""
    devices = mock_nvidia.get_devices()

    assert devices == Config().conf['nvi_dev_list'], f"status {devices} != {Config().conf['nvi_dev_list']}"
    assert glob.called, f"mock_glob {glob} is not called"

    # check loggers
    assert logger.debug.call_count == 1, f"call_count {logger.debug.call_count} != 1"
    assert logger.debug.call_args_list == [mocker.call('nvidia device list: %s', Config().conf['nvi_dev_list'])]
