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
def logger(mocker):
    mock_log = mocker.patch('udocker.engine.nvidia.LOG')
    return mock_log


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


installation_data = [(["/home/.udocker/cont/usr/lib", ], ['/home/.udocker/cont/usr/lib', ])]
copy_files_data = [('/usr/lib', 'lib', ['a'], False)]
files_exist_data = [('some_dir', ['a', 'b'])]
nvidia_libs_data = ['/usr/lib']


def test_01_init(mock_nvidia, lrepo, container_id):
    """Test01 NvidiaMode() constructor."""
    cdir = lrepo.cd_container(container_id)

    assert mock_nvidia.localrepo == lrepo
    assert mock_nvidia.container_id == container_id
    assert mock_nvidia.container_dir == cdir
    assert mock_nvidia.container_root == cdir + "/ROOT"
    assert mock_nvidia._container_nvidia_set == cdir + "/nvidia"
    assert mock_nvidia._nvidia_main_libs == ("libnvidia-cfg.so", "libcuda.so",)


@pytest.mark.parametrize("cont_dst_dir,files_list", files_exist_data)
def test_02__files_exist(mocker, cont_dst_dir, files_list, mock_nvidia):
    """Test02 NvidiaMode._files_exist."""
    os_path_exists = mocker.patch('udocker.engine.nvidia.os.path.exists', return_value=False)
    mock_nvidia._files_exist(cont_dst_dir, files_list)

    # assert if all files are checked
    assert os_path_exists.call_count == len(files_list)
    assert os_path_exists.call_args_list == [mocker.call(mock_nvidia.container_root + '/' + cont_dst_dir + '/' + fname)
                                             for fname in files_list]
    # assert if exception is raised
    with pytest.raises(OSError):
        os_path_exists.return_value = True
        mock_nvidia._files_exist(cont_dst_dir, files_list)


@pytest.mark.parametrize("hsrc_dir,cdst_dir,flist,force", copy_files_data)
def test_03__copy_files(mocker, mock_nvidia, hsrc_dir, cdst_dir, flist, force, logger):
    """Test03 NvidiaMode._copy_files."""
    # FIXME: this test need to be rebuild
    mock_nvidia.container_root = '/home/.udocker/cont/ROOT'
    dstname = mock_nvidia.container_root + '/' + cdst_dir + '/' + flist[0]
    srcname = hsrc_dir + '/' + flist[0]

    os_remove = mocker.patch('udocker.engine.nvidia.os.remove')

    # scenario 1, empty list, mock default; expected write loggers 3 debug, return true and write logger 1 warning
    copy_files = mock_nvidia._copy_files(hsrc_dir, cdst_dir, flist, force)
    assert logger.debug.call_count == 3
    assert logger.debug.call_args_list == [mocker.call('Source (host) dir %s', hsrc_dir),
                                           mocker.call('Destination (container) dir %s', cdst_dir),
                                           mocker.call('nvidia copied %s to %s', srcname, dstname)]
    assert logger.warning.call_count == 1
    assert logger.warning.call_args_list == [mocker.call('nvidia file in config not found: %s', srcname)]
    assert copy_files is True

    # scenario2 link or file are true, force is false, this should return false and write logger 1 error
    is_file = mocker.patch('udocker.engine.nvidia.os.path.isfile', return_value=False)
    is_link = mocker.patch('udocker.engine.nvidia.os.path.islink', return_value=True)

    with pytest.raises(OSError):
        os_remove.side_effect = OSError
        logger.reset_mock()
        mock_nvidia._copy_files(hsrc_dir, cdst_dir, flist, force=True)
        assert logger.error.call_count == 1

    # scenario 3 similar working scenario 2 but with force true, should write logger 1 info and return false
    logger.reset_mock()
    copy_files = mock_nvidia._copy_files(hsrc_dir, cdst_dir, flist, force)
    assert logger.info.call_count == 1
    assert logger.info.call_args_list == [mocker.call('nvidia file already exists %s, use --force to overwrite',
                                                      dstname)]
    assert copy_files is False

    os_chmod = mocker.patch('udocker.engine.nvidia.os.chmod', side_effect=[644, 755])
    os_mkdir = mocker.patch('udocker.engine.nvidia.os.makedirs')
    os_access = mocker.patch('udocker.engine.nvidia.os.access')
    is_dir = mocker.patch('udocker.engine.nvidia.os.path.isdir')
    mocker.patch('udocker.engine.nvidia.os.path.dirname')
    mocker.patch('udocker.engine.nvidia.shutil.copy2')
    mocker.patch('udocker.engine.nvidia.os.stat', side_effect=[mocker.Mock(st_mode=444), mocker.Mock(st_mode=222),
                                                               mocker.Mock(st_mode=111), mocker.Mock(st_mode=111)])
    mocker.patch('udocker.engine.nvidia.os.stat.S_IMODE', side_effect=[644, 755])
    mocker.patch('udocker.engine.nvidia.os.readlink')

    # scenario 4, not dir, not link or file, should return true
    is_dir.return_value = False
    os_mkdir.side_effect = None
    is_file.return_value = False
    is_link.return_value = False
    copy_files = mock_nvidia._copy_files(hsrc_dir, cdst_dir, flist, force)
    assert copy_files is True

    # scenario 5, not dir, not link or file, permission denied write logger 1 error and return false
    logger.reset_mock()
    is_file.return_value = True
    is_file.return_value = False
    is_link.return_value = False
    os_mkdir.side_effect = OSError
    copy_files = mock_nvidia._copy_files(hsrc_dir, cdst_dir, flist, force)
    assert copy_files is True
    assert logger.error.call_count == 1

    # scenario 6, is link and force is true, when force is false and return false
    mocker.patch('udocker.engine.nvidia.os.readlink')
    mocker.patch('udocker.engine.nvidia.os.symlink')
    is_link.return_value = True
    logger.reset_mock()
    copy_files = mock_nvidia._copy_files(hsrc_dir, cdst_dir, flist, force=True)
    assert copy_files is True
    assert logger.info.call_count == 1
    assert copy_files is True

    # scenario 7, is file and not link
    is_link.return_value = False
    is_file.return_value = True
    logger.reset_mock()
    copy_files = mock_nvidia._copy_files(hsrc_dir, cdst_dir, flist, force=True)
    assert logger.info.call_count == 1
    assert logger.info.call_args_list == [mocker.call('is file %s to %s', srcname, dstname)]
    assert copy_files is True

    # scenario 8, similar to scenario 7 but with OSError give no access
    os_chmod.side_effect = [None, OSError]
    logger.reset_mock()
    is_link.return_value = False
    is_file.return_value = True
    os_access.return_value = False
    os_remove.side_effect = None
    os_mkdir.side_effect = None
    copy_files = mock_nvidia._copy_files(hsrc_dir, cdst_dir, flist, force=True)
    assert logger.error.call_count == 1
    assert copy_files is True


@pytest.mark.parametrize("host_src_dir", nvidia_libs_data)
def test_04__get_nvidia_libs(mocker, mock_nvidia, host_src_dir, logger):
    """Test04 NvidiaMode._get_nvidia_libs."""

    Config.conf['nvi_lib_list'] = ['/lib/libnvidia.so']
    mock_glob = mocker.patch('udocker.engine.nvidia.glob.glob')
    mock_glob.return_value = ['/lib/libnvidia.so']

    nvidia_libs = mock_nvidia._get_nvidia_libs(host_src_dir)

    assert nvidia_libs == Config.conf['nvi_lib_list']

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('list nvidia libs: %s', Config.conf['nvi_lib_list'])]


@pytest.mark.parametrize("arch", ["x86-64"])
def test_05__find_host_dir_ldconfig(mocker, mock_nvidia, arch, logger):
    """Test05 NvidiaMode._find_host_dir_ldconfig."""

    mocker.patch('udocker.engine.nvidia.os.path.realpath', return_value="/lib/x86_64-linux-gnu")
    mocker.patch('udocker.engine.nvidia.os.path.dirname', return_value="/lib/x86_64-linux-gnu")

    mocker.patch('udocker.engine.nvidia.Uprocess.get_output',
                 return_value=(' libnvidia-cfg.so (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libnvidia-cfg.so\n,'
                               ' libcuda.so (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libcuda.so\n'))

    find_host_dir_ldconfig = mock_nvidia._find_host_dir_ldconfig(arch)
    assert find_host_dir_ldconfig == {"/lib/x86_64-linux-gnu/"}

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('list nvidia libs via ldconfig: %s', find_host_dir_ldconfig)]


def test_06__find_host_dir_ldpath(mocker, mock_nvidia, logger):
    """Test06 NvidiaMode._find_host_dir_ldpath."""

    mocker.patch('udocker.engine.nvidia.glob.glob', return_value=['/usr/lib/x86_64-linux-gnu'])
    library_path = '/usr/lib:/lib/x86_64-linux-gnu'

    host_dir_ldpath = mock_nvidia._find_host_dir_ldpath(library_path)
    assert host_dir_ldpath == {"/usr/lib/", "/usr/lib/x86_64-linux-gnu/"}

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('list nvidia libs via path: %s', host_dir_ldpath)]


def test_07__find_host_dir(mocker, mock_nvidia, ldconf, ldpath, logger):
    """Test07 NvidiaMode._find_host_dir."""
    # scenario empty set
    find_host_dir = mock_nvidia._find_host_dir()

    assert ldpath.called
    assert ldconf.called
    assert find_host_dir == set()

    # scenario with _find_host_dir_ldconfig() returning a set with a value
    ldpath.return_value = {"/lib/x86_64-linux-gnu/"}

    # scenario with _find_host_dir_ldpath() and _find_host_dir_ldconfig() returning a set with a value
    ldpath.return_value = {'/lib/x86_64-linux-gnu/', "/usr/lib/"}
    ldconf.return_value = {'/lib/x86_64-linux-gnu/'}

    logger.debug.call_count = 0  # flush logger.debug
    find_host_dir = mock_nvidia._find_host_dir()
    assert find_host_dir == {'/lib/x86_64-linux-gnu/', '/usr/lib/'}

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('host location nvidia: %s', set()),
                                           mocker.call('host location nvidia: %s', find_host_dir)]


def test_08__find_cont_dir(mocker, mock_nvidia, logger):
    """Test08 NvidiaMode._find_cont_dir."""
    mock_isdir = mocker.patch('udocker.engine.nvidia.os.path.isdir', return_value=False)

    find_cont_dir = mock_nvidia._find_cont_dir()
    assert find_cont_dir == ''

    mock_isdir.return_value = True
    find_cont_dir = mock_nvidia._find_cont_dir()
    assert find_cont_dir == '/usr/lib/x86_64-linux-gnu'

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('cont. location nvidia: %s', find_cont_dir)]


@pytest.mark.parametrize("host_dir,cont_dir", installation_data)
def test_09__installation_exists(mocker, mock_nvidia, host_dir, cont_dir, logger):
    """Test09 NvidiaMode._installation_exists."""
    file_exists = mocker.patch('udocker.engine.nvidia.NvidiaMode._files_exist')
    os_path_exists = mocker.patch('udocker.engine.nvidia.os.path.exists')

    installation_exists = mock_nvidia._installation_exists(host_dir, cont_dir)
    os_path_exists.return_value = False
    file_exists.return_value = True

    assert installation_exists is False

    # check loggers
    assert logger.info.call_count == 1
    assert logger.info.call_args_list == [mocker.call('container has files from previous nvidia install')]

    # exception OSError
    os_path_exists.return_value = True
    file_exists.side_effect = OSError

    installation_exists = mock_nvidia._installation_exists(host_dir, cont_dir)
    assert installation_exists is True


set_mode_data = (
    (False, None, "nvidia set mode container dir not found", [set(), {"/usr/lib"}], [""], 1, 0, False),
    (False, "/home/.udocker/cont", "host nvidia libraries not found", [set(), {"/usr/lib"}], [""], 1, 0, False),
    (False, "/home/.udocker/cont", "destination dir for nvidia libs not found", [{"/usr/lib"}], [""], 1, 0, False),
    (False, "/home/.udocker/cont", "nvidia install already exists, --force to overwrite", [{"/usr/lib"}], ["/dir"],
     1, 0, False),
    (True, "/home/.udocker/cont", "nvidia mode set", [{"/usr/lib"}], ["/dir"],
     0, 1, True)
)


@pytest.mark.parametrize("force, cdir,msg,find_host_dir,find_cont_dir,debug,info,expected", set_mode_data)
def test_10_set_mode(mocker, mock_nvidia, logger, force, msg, cdir, find_host_dir, find_cont_dir, debug, info,
                     expected):
    """Test10 NvidiaMode.set_mode()."""

    mocker.patch('udocker.engine.nvidia.NvidiaMode._find_host_dir', side_effect=find_host_dir)
    mocker.patch('udocker.engine.nvidia.NvidiaMode._find_cont_dir', side_effect=find_cont_dir)
    mocker.patch('udocker.engine.nvidia.NvidiaMode._copy_files', side_effect=[True, True, True])

    mock_nvidia.container_dir = cdir
    logger.reset_mock()
    set_mode = mock_nvidia.set_mode(force=force)
    assert set_mode is expected
    assert logger.error.call_count == debug
    assert logger.info.call_count == info
    if debug > 0:
        assert logger.error.call_args_list == [mocker.call(msg)]
    if info > 0:
        assert logger.info.call_args_list == [mocker.call(msg)]


get_mode_data = (
    (True, 1, True),
    (False, 1, False)
)


@pytest.mark.parametrize("os_exists,calls,expected", get_mode_data)
def test_11_get_mode(mocker, mock_nvidia, os_exists, calls, expected):
    """Test11 NvidiaMode.get_mode()."""

    os_path_exists = mocker.patch('udocker.engine.nvidia.os.path.exists', return_value=os_exists)
    mock_nvidia._container_nvidia_set = '/home/.udocker/container/nvidia'

    mode = mock_nvidia.get_mode()
    assert mode is expected

    # check loggers
    assert os_path_exists.call_count == calls
    assert os_path_exists.called
    assert os_path_exists.call_args_list == [mocker.call(mock_nvidia._container_nvidia_set)]


def test_12_get_devices(mocker, mock_nvidia, logger):
    """Test12 NvidiaMode.get_devices()."""
    glob = mocker.patch('udocker.engine.nvidia.glob.glob', return_value=['/dev/nvidia'])
    devices = mock_nvidia.get_devices()

    assert devices == Config().conf['nvi_dev_list']
    assert glob.called

    # check loggers
    assert logger.debug.call_count == 1
    assert logger.debug.call_args_list == [mocker.call('nvidia device list: %s', Config().conf['nvi_dev_list'])]
