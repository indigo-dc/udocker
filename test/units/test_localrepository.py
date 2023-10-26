#!/usr/bin/env python
"""
udocker unit tests: LocalRepository
"""
import os
import random

import pytest

from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.utils.fileutil import FileUtil
from udocker.utils.uprocess import Uprocess

UDOCKER_TOPDIR = ["/home/u1/.udocker", ]
BUILTIN = "builtins"
BOPEN = BUILTIN + '.open'


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker, topdir):
    mocker.patch.object(Config, 'conf', {
        'topdir': None,
        'bindir': "",
        'libdir': "",
        'reposdir': "",
        'layersdir': "",
        'containersdir': "",
        'homedir': "/home/u1",
        'installdir': "",
        'tmpdir': ""
    })
    localrepo = LocalRepository(topdir)
    return localrepo


@pytest.fixture
def logger(mocker):
    mock_log = mocker.patch('udocker.container.localrepo.LOG')
    return mock_log


@pytest.fixture
def mock_fileutil(mocker):
    return mocker.patch('udocker.container.localrepo.FileUtil')


# from unittest import TestCase, main
# from unittest.mock import patch, mock_open, call
# from udocker.container.localrepo import LocalRepository, LOG
# from udocker.config import Config
# import collections
# collections.Callable = collections.abc.Callable
#
# BUILTIN = "builtins"
# BOPEN = BUILTIN + '.open'
# UDOCKER_TOPDIR = "/home/u1/.udocker"
#
#
# class LocalRepositoryTestCase(TestCase):
#     """Management of local repository of container
#     images and extracted containers
#     """
#
# def setUp(self):
#

# LOG.setLevel(100)
#         Config().getconf()
#         Config().conf['topdir'] = UDOCKER_TOPDIR
#         Config().conf['bindir'] = ""
#         Config().conf['libdir'] = ""
#         Config().conf['reposdir'] = ""
#         Config().conf['layersdir'] = ""
#         Config().conf['containersdir'] = ""
#         Config().conf['homedir'] = "/home/u1"
#
# def tearDown(self):


# pass
#
@pytest.mark.parametrize("topdir,conf,expected", [
    (UDOCKER_TOPDIR[0],
     {'topdir': None, 'bindir': "", 'libdir': "", 'reposdir': "", 'layersdir': "", 'containersdir': "",
      'homedir': "/home/u1", 'installdir': "", 'tmpdir': ""}, UDOCKER_TOPDIR[0]),
    # ("", {'topdir': None, 'bindir': "", 'libdir': "", 'reposdir': "", 'layersdir': "", 'containersdir': "",
    #                   'homedir': "/home/u1", 'installdir': "", 'tmpdir': ""}, ""),
])
def test_01_init(mocker, topdir, mock_fileutil, conf, expected):
    """Test01 LocalRepository() constructor."""
    mocker.patch.object(Config, 'conf', conf)

    localrepo = LocalRepository(topdir)
    assert localrepo.topdir == expected
    assert localrepo.installdir == ""
    assert localrepo.bindir == "" + "/bin"
    assert localrepo.libdir == "" + "/lib"
    assert localrepo.docdir == "" + "/doc"
    assert localrepo.tardir == "" + "/tar"
    assert localrepo.reposdir == topdir + "/repos"
    assert localrepo.layersdir == topdir + "/layers"
    assert localrepo.containersdir == topdir + "/containers"
    assert localrepo.homedir == "/home/u1"
    assert localrepo.cur_repodir == ""
    assert localrepo.cur_tagdir == ""
    assert localrepo.cur_containerdir == ""
    assert mock_fileutil.return_value.register_prefix.call_count == 3

    # self.topdir = topdir if topdir else Config.conf['topdir']
    # self.installdir = Config.conf['installdir']
    # self.bindir = self.installdir + '/bin'
    # self.libdir = self.installdir + '/lib'
    # self.docdir = self.installdir + '/doc'
    # self.tardir = self.installdir + '/tar'
    # self.reposdir = Config.conf['reposdir']
    # self.layersdir = Config.conf['layersdir']
    # self.containersdir = Config.conf['containersdir']
    # self.homedir = Config.conf['homedir']
    # if not self.reposdir:
    #     self.reposdir = self.topdir + "/repos"
    #
    # if not self.layersdir:
    #     self.layersdir = self.topdir + "/layers"
    #
    # if not self.containersdir:
    #     self.containersdir = self.topdir + "/containers"
    #
    # self.cur_repodir = ''
    # self.cur_tagdir = ''
    # self.cur_containerdir = ''
    # FileUtil(self.reposdir).register_prefix()
    # FileUtil(self.layersdir).register_prefix()
    # FileUtil(self.containersdir).register_prefix()


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         self.assertTrue(lrepo.topdir)
#         self.assertTrue(lrepo.reposdir)
#         self.assertTrue(lrepo.layersdir)
#         self.assertTrue(lrepo.containersdir)
#         self.assertTrue(lrepo.bindir)
#         self.assertTrue(lrepo.libdir)
#         self.assertTrue(lrepo.homedir)
#         self.assertEqual(lrepo.topdir, UDOCKER_TOPDIR)
#         self.assertEqual(lrepo.cur_repodir, "")
#         self.assertEqual(lrepo.cur_tagdir, "")
#         self.assertEqual(lrepo.cur_containerdir, "")
#         self.assertTrue(mock_fu.register_prefix.called_count, 3)
#
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("topdir,expected", [
    ("/home/u2/.udocker", "/home/u2/.udocker"),
])
def test_02_setup(mocker, localrepo, topdir, mock_fileutil, expected):
    """Test02 LocalRepository().setup()."""
    mocker.patch.object(Config, 'conf', {'topdir': None,
                                         'bindir': "",
                                         'libdir': "",
                                         'reposdir': "",
                                         'layersdir': "",
                                         'containersdir': "",
                                         'homedir': "/home/u1",
                                         'installdir': "",
                                         'tmpdir': ""})

    localrepo.setup(topdir)
    assert localrepo.topdir == expected
    assert localrepo.reposdir == topdir + "/repos"
    assert localrepo.layersdir == topdir + "/layers"
    assert localrepo.containersdir == topdir + "/containers"
    mock_fileutil.return_value.register_prefix.call_count == 3


@pytest.mark.parametrize(",os_exists,keystore,call_count,expected", [
    ([False] * 10, False, 10, True),
    (OSError, False, 0, False),
    ([False] * 10, True, 9, True),
    ([True] * 10, True, 0, True),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_03_create_repo(mocker, localrepo, topdir, os_exists, keystore, call_count, expected):
    """Test03 LocalRepository().create_repo()."""
    mocker.patch.object(os.path, 'exists', side_effect=os_exists)
    mock_makedirs = mocker.patch('udocker.container.localrepo.os.makedirs')
    mocker.patch.dict(Config.conf, {'keystore': "/" if keystore else "some_keystore"})

    assert localrepo.create_repo() == expected
    assert mock_makedirs.call_count == call_count
    # os.path.exists(self.homedir) not sure if this is correct


#         Config.conf['keystore'] = "tmp"
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [False, False, False, False, False, False, False, False]
#         mock_mkdir.side_effect = [None, None, None, None, None, None, None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.create_repo()
#         self.assertTrue(status)
#         self.assertTrue(mock_exists.call_count, 8)
#         self.assertTrue(mock_mkdir.call_count, 8)
#
#         Config.conf['keystore'] = "tmp"
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = OSError("fail")
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.create_repo()
#         self.assertFalse(status)
#
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("dirs_exists,expected", [
    ([True, True, True, True, True], True),
    ([False, True, True, True, True], False),
    ([True, False, True, True, True], False),
    ([True, True, False, True, True], False),
    ([True, True, True, False, True], False),
    ([True, True, True, True, False], False),
    ([False, False, False, False, False], False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_04_is_repo(mocker, localrepo, topdir, dirs_exists, expected):
    """Test04 LocalRepository().is_repo()."""
    mocker.patch('os.path.exists', side_effect=dirs_exists)
    assert localrepo.is_repo() == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [False, True, False, False, True]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.is_repo()
#         self.assertTrue(mock_exists.call_count, 5)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True, True, True, True]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.is_repo()
#         self.assertTrue(mock_exists.call_count, 5)
#         self.assertTrue(status)
#
#     @patch('udocker.container.localrepo.FileUtil')
@pytest.mark.parametrize("cont_id,expected", [
    (12345, False),
    (["d2578feb-acfc-37e0-8561-47335f85e46a"], False),
    ("d2578feb-acfc-37e0-8561-47335f85e46a", True),
    ("d2578feb-acfc-37e0-8561", False),
    ("d2578feb-ACFC-37e0-8561-47335f85e46a", False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_05_is_container_id(localrepo, cont_id, expected):
    """Test05 LocalRepository().is_container_id()."""
    assert localrepo.is_container_id(cont_id) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         contid = ""
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.is_container_id(contid)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         contid = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.is_container_id(contid)
#         self.assertTrue(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         contid = "d"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.is_container_id(contid)
#         self.assertFalse(status)
#
#     @patch.object(LocalRepository, '_protect')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("container_id,protected,expected", [
    ("d2578feb-acfc-37e0-8561-47335f85e46a", True, True),
    ("d2578feb", False, False)
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_06_protect_container(mocker, localrepo, container_id, protected, expected):
    """Test06 LocalRepository().protect_container()."""
    mocker.patch.object(localrepo, '_protect', return_value=protected)
    mock_cd_container = mocker.patch.object(localrepo, 'cd_container', return_value="/home/u1/.udocker/containerid")

    assert localrepo.protect_container(container_id) == expected
    mock_cd_container.assert_called_once_with(container_id)


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         contid = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         mock_prot.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.protect_container(contid)
#         self.assertTrue(status)
#         self.assertTrue(mock_prot.called)
#
#     @patch.object(LocalRepository, '_unprotect')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("container_id,unprotect,expected", [
    ("d2578feb-acfc-37e0-8561-47335f85e46a", True, True),
    ("d2578feb", False, False)
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_07_unprotect_container(mocker, localrepo, container_id, unprotect, expected):
    """Test07 LocalRepository().unprotect_container()."""
    mocker.patch.object(localrepo, '_unprotect', return_value=unprotect)
    mock_cd_container = mocker.patch.object(localrepo, 'cd_container', return_value="/home/u1/.udocker/containerid")

    assert localrepo.unprotect_container(container_id) == expected
    mock_cd_container.assert_called_once_with(container_id)


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         contid = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         mock_unprot.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.unprotect_container(contid)
#         self.assertTrue(status)
#         self.assertTrue(mock_unprot.called)
#
#     @patch.object(LocalRepository, '_isprotected')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("container_id,isprotected,expected", [
    ("d2578feb-acfc-37e0-8561-47335f85e46a", True, True),
    ("d2578feb", False, False)
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_08_isprotected_container(mocker, localrepo, container_id, isprotected, expected):
    """Test08 LocalRepository().isprotected_container()."""
    mocker.patch.object(localrepo, '_isprotected', return_value=isprotected)
    mock_cd_container = mocker.patch.object(localrepo, 'cd_container', return_value="/home/u1/.udocker/containerid")

    assert localrepo.isprotected_container(container_id) == expected
    mock_cd_container.assert_called_once_with(container_id)


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         contid = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         mock_isprot.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.isprotected_container(contid)
#         self.assertTrue(status)
#         self.assertTrue(mock_isprot.called)
#
#     @patch('udocker.container.localrepo.FileUtil')
@pytest.mark.parametrize("directory,file_created,expected", [
    ("/home/u1/.udocker/contid", True, True),
    ("/home/u1/.udocker/contid", False, False)
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_09__protect(mocker, localrepo, directory, file_created, expected):
    """Test09 LocalRepository()._protect()."""
    if file_created:
        mock_open = mocker.mock_open()
        mocker.patch('builtins.open', mock_open)
    else:
        mocker.patch('builtins.open', side_effect=OSError())

    assert localrepo._protect(directory) == expected

    if file_created:
        mock_open.assert_called_once_with(directory + "/PROTECT", 'w', encoding='utf-8')


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         cdir = "/home/u1/.udocker/contid"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         with patch(BOPEN, mock_open()):
#             status = lrepo._protect(cdir)
#             self.assertTrue(status)
#
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("directory,file_removal_outcome,expected", [
    ("/home/u1/.udocker/contid/", True, True),
    ("/home/u1/.udocker/contid/", False, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_10__unprotect(localrepo, mock_fileutil, directory, file_removal_outcome, expected):
    """Test10 LocalRepository()._unprotect()."""
    # FIXME: probably droping the use of mock_fileutil and mock method directly can simplify the test, need to check other tests using that logic
    mock_fileutil.return_value.remove.return_value = file_removal_outcome
    result = localrepo._unprotect(directory)
    assert result == expected
    mock_fileutil.assert_called_once_with(directory + "/PROTECT")
    mock_fileutil.return_value.remove.assert_called_once_with()


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         cdir = "/home/u1/.udocker/contid"
#         mock_fu.return_value.remove.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._unprotect(cdir)
#         self.assertTrue(status)
#         self.assertTrue(mock_fu.return_value.remove.called)
#
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("directory,protect_exists,expected", [
    ("/home/u1/.udocker/contid/", True, True),
    ("/home/u1/.udocker/contid/", False, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_11__isprotected(mocker, localrepo, directory, protect_exists, expected):
    """Test11 LocalRepository()._isprotected()."""
    mocker.patch.object(os.path, 'exists', return_value=protect_exists)
    result = localrepo._isprotected(directory)
    assert result == expected
    os.path.exists.assert_called_once_with(directory + "/PROTECT")


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         cdir = "/home/u1/.udocker/contid"
#         mock_exists.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._isprotected(cdir)
#         self.assertTrue(status)
#         self.assertTrue(mock_exists.called)
#
#     @patch.object(LocalRepository, 'cd_container')
#     @patch('udocker.container.localrepo.os.access')
#     @patch('udocker.container.localrepo.os.path.isdir')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("path_exists,is_dir,is_writable,expected", [
    (False, False, False, 2),
    (True, False, False, 3),
    (True, True, True, 1),
    (True, True, False, 0),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_12_iswriteable_container(mocker, container_id, localrepo, path_exists, is_dir, is_writable, expected):
    """Test12 LocalRepository().iswriteable_container()."""
    container = "/home/u1/.udocker/containerid"

    mocker.patch.object(localrepo, 'cd_container', return_value=container)

    mocker_os_path_exists = mocker.patch.object(os.path, 'exists', return_value=path_exists)
    mocker.patch.object(os.path, 'isdir', return_value=is_dir)
    mocker.patch.object(os, 'access', return_value=is_writable)

    assert localrepo.iswriteable_container(container_id) == expected
    mocker_os_path_exists.assert_called_once_with(container + "/ROOT")

    # FIXME: add test calls for other mocked methods


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         mock_exists.return_value = False
#         mock_cdcont.return_value = "/home/u1/.udocker/containerid"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.iswriteable_container(container_id)
#         self.assertEqual(status, 2)
#         self.assertTrue(mock_exists.called)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.return_value = True
#         mock_isdir.return_value = False
#         mock_cdcont.return_value = "/home/u1/.udocker/containerid"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.iswriteable_container(container_id)
#         self.assertEqual(status, 3)
#         self.assertTrue(mock_isdir.called)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.return_value = True
#         mock_isdir.return_value = True
#         mock_access.return_value = True
#         mock_cdcont.return_value = "/home/u1/.udocker/containerid"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.iswriteable_container(container_id)
#         self.assertEqual(status, 1)
#         self.assertTrue(mock_access.called)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.return_value = True
#         mock_isdir.return_value = True
#         mock_access.return_value = False
#         mock_cdcont.return_value = "/home/u1/.udocker/containerid"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.iswriteable_container(container_id)
#         self.assertEqual(status, 0)
#
#     @patch.object(LocalRepository, 'cd_container')
#     @patch('udocker.container.localrepo.Uprocess.get_output')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("du_output, expected_size", [
    ("1234\t/mock/path/to/container/ROOT", 1234),
    ("invalid_output", -1),
    ("", -1),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_13_get_size(container_id, du_output, expected_size, localrepo, mocker):
    """Test13 LocalRepository().get_size()."""
    mock_container_root = "/mock/path/to/container/ROOT"
    mocker.patch.object(localrepo, 'cd_container', return_value=mock_container_root[:-5])
    mock_uprocess = mocker.patch.object(Uprocess, 'get_output', return_value=du_output)

    assert localrepo.get_size(container_id) == expected_size
    mock_uprocess.assert_called_once_with(["du", "-s", "-m", "-x", mock_container_root])


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         mock_getout.return_value = "1234 dd"
#         mock_cdcont.return_value = "/home/u1/.udocker/containerid"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_size(container_id)
#         self.assertEqual(status, 1234)
#         self.assertTrue(mock_getout.called)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         mock_getout.return_value = ""
#         mock_cdcont.return_value = "/home/u1/.udocker/containerid"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_size(container_id)
#         self.assertEqual(status, -1)
#
#     @patch('udocker.container.localrepo.os.listdir')
#     @patch('udocker.container.localrepo.os.path.isdir')
#     @patch('udocker.container.localrepo.FileUtil')
@pytest.mark.parametrize("isdir,listdir,file_contents,dir_only,expected", [
    (False, [], None, True, []),
    (True, [], None, True, []),
    (True, ['container1'], "some_repo_name", True, ['/home/u1/.udocker/containers/container1']),
    (True, ['container1'], None, True, ['/home/u1/.udocker/containers/container1']),
    (True, ['container1'], "some_repo_name", False, [('container1', 'some_repo_name', 'container_name')]),
    (True, ['a'], None, True, ['/home/u1/.udocker/containers/a']),
    (True, ['a'], None, False, [('a', '', 'container_name')]),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_14_get_containers_list(mocker, localrepo, container_id, isdir, listdir, file_contents, dir_only, expected):
    """Test14 LocalRepository().get_containers_list()."""
    mocker.patch('os.path.isdir', return_value=isdir)
    mocker.patch('os.listdir', return_value=listdir)

    if file_contents is not None:
        mocker.patch('builtins.open', mocker.mock_open(read_data=file_contents))
    else:
        mocker.patch('builtins.open', side_effect=OSError)

    mocker.patch.object(localrepo, 'get_container_name', return_value="container_name")
    mocker.patch.object(localrepo, 'containersdir', '/home/u1/.udocker/containers')

    assert localrepo.get_containers_list(dir_only) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isdir.return_value = False
#         mock_listdir.return_value = list()
#         cdir = "/home/u1/.udocker/containers"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_containers_list()
#         self.assertEqual(status, list())
#         self.assertEqual(lrepo.containersdir, cdir)
#         self.assertFalse(mock_listdir.called)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isdir.return_value = True
#         mock_listdir.return_value = list()
#         cdir = "/home/u1/.udocker/containers"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_containers_list()
#         self.assertEqual(status, list())
#         self.assertTrue(mock_listdir.called)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isdir.side_effect = [True, False]
#         cdir = "/home/u1/.udocker/containers"
#         mock_listdir.return_value = [cdir]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_containers_list()
#         self.assertEqual(status, list())
#         self.assertTrue(mock_listdir.called)
#         self.assertTrue(mock_isdir.call_count, 2)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isdir.side_effect = [True, True]
#         cdir = "/home/u1/.udocker/containers"
#         mock_listdir.return_value = ["a"]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         with patch(BOPEN, mock_open()):
#             status = lrepo.get_containers_list()
#             self.assertEqual(status, [cdir + "/" + "a"])
#             self.assertTrue(mock_listdir.called)
#             self.assertTrue(mock_isdir.call_count, 2)
#
#     @patch.object(LocalRepository, 'del_container_name')
#     @patch.object(LocalRepository, 'cd_container')
#     @patch.object(LocalRepository, 'get_container_name')
#     @patch.object(LocalRepository, 'get_containers_list')
#     @patch('udocker.container.localrepo.FileUtil')
@pytest.mark.parametrize("container_dir,in_list,container_name, remove, force, expected", [
    (None, False, [], False, False, False),
    ("/home/u1/.udocker/containers", False, [], False, False, False),
    ("/home/u1/.udocker/containers", True, ["mycont"], False, False, False),
    ("/home/u1/.udocker/containers", True, ["mycont"], True, False, True),
    ("/home/u1/.udocker/containers", True, ["mycont"], True, True, True),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_15_del_container(mocker, localrepo, mock_fileutil, container_dir, topdir, container_id, in_list,
                          container_name, remove, force, expected):
    """Test15 LocalRepository().del_container()."""
    mocker.patch.object(localrepo, 'cd_container', return_value=container_dir)
    mocker.patch.object(localrepo, 'get_containers_list', return_value=[container_dir] if in_list else [])
    mocker.patch.object(localrepo, 'get_container_name', return_value=container_name)
    mocker.patch.object(localrepo, 'del_container_name')

    mock_fileutil.return_value.remove.return_value = remove

    assert localrepo.del_container(container_id, force=force) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         cont_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         mock_cdcont.return_value = ""
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.del_container(cont_id)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         cont_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         cdirs = "/home/u1/.udocker/containers"
#         contdir = cdirs + "/" + cont_id
#         mock_cdcont.return_value = contdir
#         mock_getlist.return_value = [contdir]
#         mock_delname.return_value = None
#         mock_getname.return_value = ["mycont"]
#         mock_fu.return_value.remove.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.del_container(cont_id)
#         self.assertFalse(status)
#         self.assertTrue(mock_getlist.called)
#         self.assertTrue(mock_delname.called)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         cont_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         cdirs = "/home/u1/.udocker/containers"
#         contdir = cdirs + "/" + cont_id
#         mock_cdcont.return_value = contdir
#         mock_getlist.return_value = [contdir]
#         mock_delname.return_value = None
#         mock_getname.return_value = ["mycont"]
#         mock_fu.return_value.remove.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.del_container(cont_id)
#         self.assertTrue(status)
#         self.assertTrue(mock_fu.return_value.remove.called)
#
#     @patch.object(LocalRepository, 'get_containers_list')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("os_exists,in_list,container_list,expected", [
    (False, False, [], ""),
    (True, False, [], ""),
    (True, True, ["/home/u1/.udocker/containers/d2578feb-acfc-37e0-8561-47335f85e46a"],
     "/home/u1/.udocker/containers/d2578feb-acfc-37e0-8561-47335f85e46a"),
    (True, False, ["/home/u1/.udocker/containers/random_id"], ""),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_16_cd_container(mocker, localrepo, topdir, container_id, os_exists, in_list, container_list, expected):
    """Test16 LocalRepository().cd_container()."""

    # FIXME: remove container_list and use in_list instead to build return value
    mocker.patch('os.path.exists', return_value=os_exists)
    mocker.patch.object(localrepo, 'get_containers_list', return_value=container_list)
    assert localrepo.cd_container(container_id) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         cont_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         cdirs = "/home/u1/.udocker/containers"
#         contdir = cdirs + "/" + cont_id
#         mock_getlist.return_value = [contdir]
#         mock_exists.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.cd_container(cont_id)
#         self.assertEqual(status, "")
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         cont_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         cdirs = "/home/u1/.udocker/containers"
#         contdir = cdirs + "/" + cont_id
#         mock_getlist.return_value = [contdir]
#         mock_exists.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.cd_container(cont_id)
#         self.assertEqual(status, contdir)
#
#     @patch('udocker.container.localrepo.os.path.relpath')
#     @patch('udocker.container.localrepo.os.symlink')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("os_exists,symlink_success,log_debug,expected", [
    (True, False, [], False),
    (False, True, ['set name through link: %s LINKFILE', 'container name set OK'], True),
    (False, False, ['set name through link: %s LINKFILE'], False),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_17__symlink(mocker, localrepo, logger, container_id, os_exists, symlink_success, log_debug, expected):
    """Test17 LocalRepository()._symlink()."""
    mocker.patch('os.path.exists', return_value=os_exists)
    mock_os_symlink = mocker.patch('os.symlink')

    if not symlink_success:
        mock_os_symlink.side_effect = OSError

    assert localrepo._symlink("EXISTINGFILE", "LINKFILE") == expected

    # FIXME: fix the logger calls
    # for debug_message in log_debug:
    #     assert debug_message in logger.debug.call_args_list


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._symlink("EXISTINGFILE", "LINKFILE")
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.return_value = False
#         mock_symlink.return_value = None
#         mock_relpath.return_value = "cont/ROOT"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._symlink("EXISTINGFILE", "LINKFILE")
#         self.assertTrue(status)
#
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("name,expected", [
    ("lzskjghdlak", True),
    ("lzskjghd/lak", False),
    (".lzsklak", False),
    ("lzs klak", False),
    ("lzsklak ", False),
    ("]lzsklak", False),
    ("lzs[klak", False),
    ("a" * 2049, False),
    ("a" * 2048, True)
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_18__name_is_valid(localrepo, topdir, container_id, name, expected):
    """Test18 LocalRepository()._name_is_valid().
    Check name alias validity.
    """
    assert localrepo._name_is_valid(name) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         name = "lzskjghdlak"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._name_is_valid(name)
#         self.assertTrue(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         name = "lzskjghd/lak"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._name_is_valid(name)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         name = ".lzsklak"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._name_is_valid(name)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         name = "]lzsklak"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._name_is_valid(name)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         name = "lzs[klak"
#         status = lrepo._name_is_valid(name)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         name = "lzs klak"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._name_is_valid(name)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         name = "x" * 2049
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._name_is_valid(name)
#         self.assertFalse(status)
#
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch.object(LocalRepository, '_symlink')
#     @patch.object(LocalRepository, 'cd_container')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("name,container_id,is_valid,exists,expected", [
    ("WRONG[/", "d2578feb-acfc-37e0-8561-47335f85e46a", False, False, False),
    ("RIGHT", "d2578feb", True, False, False),
    ("RIGHT", "d2578feb-acfc-37e0-8561-47335f85e46a", True, True, False),
    ("RIGHT", "d2578feb-acfc-37e0-8561-47335f85e46a", True, False, False),  # debug this case
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_18_set_container_name(mocker, localrepo, logger, name, container_id, is_valid, exists, expected):
    """Test18 LocalRepository().set_container_name()."""
    mocker.patch.object(localrepo, '_name_is_valid', return_value=is_valid)
    mocker.patch.object(localrepo, 'cd_container',
                        return_value="/home/u1/.udocker/containers" if container_id == "RIGHT" else "")
    mocker.patch('os.path.exists', return_value=exists)
    mocker.patch.object(localrepo, '_symlink', return_value=not exists)

    # FIXME: add check to logger calls
    assert localrepo.set_container_name(container_id, name) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.set_container_name(container_id, "WRONG[/")
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_cd.return_value = "CONTAINERDIR"
#         mock_exists.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.set_container_name(container_id, "RIGHT")
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_cd.return_value = "CONTAINERDIR"
#         mock_exists.return_value = False
#         mock_slink.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.set_container_name(container_id, "RIGHT")
#         self.assertTrue(status)
#
#     @patch.object(LocalRepository, '_name_is_valid')
#     @patch('udocker.container.localrepo.os.path.islink')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("contname,is_valid,is_link,file_remove,expected", [
    ("invalid/name", False, False, False, False),
    ("validname", True, False, False, False),
    ("validname", True, True, False, False),
    ("validname", True, True, True, True),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_19_del_container_name(mocker, localrepo, container_id, mock_fileutil, contname, is_valid, is_link, file_remove,
                               expected):
    """Test19 LocalRepository().del_container_name()."""
    mocker.patch.object(localrepo, '_name_is_valid', return_value=is_valid)
    mocker.patch('os.path.islink', return_value=is_link)
    # mocker.patch('udocker.container.localrepo.FileUtil.remove', return_value=file_remove)
    mock_fileutil.return_value.remove.return_value = file_remove

    assert localrepo.del_container_name(contname) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         contname = "mycont"
#         mock_nameisvalid.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.del_container_name(contname)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         contname = "mycont"
#         mock_nameisvalid.return_value = True
#         mock_islink.return_value = True
#         mock_fu.return_value.remove.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.del_container_name(contname)
#         self.assertTrue(status)
#
#     @patch('udocker.container.localrepo.os.readlink')
#     @patch('udocker.container.localrepo.os.path.isdir')
#     @patch('udocker.container.localrepo.os.path.islink')
#     @patch('udocker.container.localrepo.FileUtil')
@pytest.mark.parametrize("contname,is_link,is_dir,readlink,expected", [
    (None, False, False, [""], ""),
    ("", False, False, [""], ""),
    ("ALIASNAM", False, False, [""], ""),
    ("ALIASNAM", True, False, ["BASENAME"], "BASENAME"),
    ("ALIASNAM", False, True, [""], "ALIASNAM"),
    ("ALIASNAM", True, False, ["", ""], ""),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_20_get_container_id(mocker, localrepo, container_id, contname, is_link, is_dir, readlink, expected):
    """Test20 LocalRepository().get_container_id()."""
    mocker.patch('os.path.islink', return_value=is_link)
    mocker.patch('os.path.isdir', return_value=is_dir)
    mocker.patch('os.readlink', side_effect=readlink)

    assert localrepo.get_container_id(contname) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_container_id(None)
#         self.assertEqual(status, "")
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_islink.return_value = True
#         mock_readlink.return_value = "BASENAME"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_container_id("ALIASNAM")
#         self.assertEqual(status, "BASENAME")
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_islink.return_value = False
#         mock_isdir.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_container_id("ALIASNAM")
#         self.assertEqual(status, "")
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_islink.return_value = False
#         mock_isdir.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_container_id("ALIASNAM")
#         self.assertEqual(status, "ALIASNAM")
#
#     @patch('udocker.container.localrepo.os.readlink')
#     @patch('udocker.container.localrepo.os.path.islink')
#     @patch('udocker.container.localrepo.os.listdir')
#     @patch('udocker.container.localrepo.os.path.isdir')
#     @patch('udocker.container.localrepo.FileUtil')
@pytest.mark.parametrize("dir_exists,list_dir,link_targets,expected", [
    (False, [], [], []),
    (True, [], [], []),
    (True, ["FILE1", "FILE2"], [], []),
    (True, ["LINK1", "LINK2"], ["other_id", "another_id"], []),
    (True, ["LINK1", "LINK2", "LINK3"], ["LINK1", "LINK2", "yet_another_id"], ["LINK1", "LINK2"]),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_21_get_container_name(mocker, localrepo, container_id, dir_exists, list_dir, link_targets, expected):
    """Test21 LocalRepository().get_container_name()."""
    mocker.patch('os.path.isdir', return_value=dir_exists)
    mocker.patch('os.listdir', return_value=list_dir)
    mocker.patch('os.path.islink', side_effect=[item in link_targets for item in list_dir])

    full_link_targets = [f"/home/u1/.udocker/{container_id}" if item in link_targets else None for item in list_dir]
    mocker.patch('os.readlink', side_effect=full_link_targets)

    # TODO: check if is better to mock os.path.basename

    assert localrepo.get_container_name(container_id) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isdir.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         name_list = lrepo.get_container_name("IMAGE:TAG")
#         self.assertEqual(name_list, list())
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isdir.return_value = True
#         mock_listdir.return_value = ['LINK']
#         mock_islink.return_value = True
#         mock_readlink.return_value = "/a/b/IMAGE:TAG"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         name_list = lrepo.get_container_name("IMAGE:TAG")
#         self.assertEqual(name_list, ["LINK"])
#
#     @patch('udocker.container.localrepo.os.makedirs')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("os_path_exists,os_makedirs_success,expected", [
    (True, True, ""),
    (False, False, None),
    (False, True, "/home/u1/.udocker/d2578feb-acfc-37e0-8561-47335f85e46a"),  # Scenario 3
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_22_setup_container(mocker, localrepo, container_id, os_path_exists, os_makedirs_success, expected):
    """Test22 LocalRepository().setup_container()."""
    container_dir = "/home/u1/.udocker/" + container_id
    mocker.patch.object(localrepo, 'containersdir', '/home/u1/.udocker')

    mocker.patch('os.path.exists', return_value=os_path_exists)
    mocker.patch('os.makedirs') if os_makedirs_success else mocker.patch('os.makedirs', side_effect=OSError)
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    assert localrepo.setup_container("imagerepo", "tag", container_id) == expected

    if os_makedirs_success and not os_path_exists:
        mock_open.assert_called_once_with(container_dir + "/imagerepo.name", 'w', encoding='utf-8')


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.setup_container("REPO", "TAG", "ID")
#         self.assertEqual(status, "")
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.return_value = False
#         mock_makedirs.return_value = None
#         with patch(BOPEN, mock_open()):
#             lrepo = LocalRepository(UDOCKER_TOPDIR)
#             status = lrepo.setup_container("REPO", "TAG", "ID")
#             self.assertEqual(status, lrepo.containersdir + "/ID")
#             self.assertEqual(lrepo.cur_containerdir, lrepo.containersdir + "/ID")
#
#     @patch('udocker.container.localrepo.os.path.isfile')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("tag_file_exists,expected", [
    ([True], True),
    ([False], False),
    ([OSError], False),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_23__is_tag(mocker, localrepo, container_id, tag_file_exists, expected):
    """Test23 LocalRepository()._is_tag()."""
    tag_dir = "/home/u1/.udocker/" + container_id
    mocker.patch('os.path.isfile', side_effect=tag_file_exists)
    assert localrepo._is_tag(tag_dir) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isfile.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._is_tag("tagdir")
#         self.assertTrue(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isfile.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._is_tag("tagdir")
#         self.assertFalse(status)
#
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("protect,expected", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_24_protect_imagerepo(mocker, localrepo, protect, expected):
    """Test24 LocalRepository().protect_imagerepo()."""
    mocker.patch.object(localrepo, '_protect', return_value=protect)
    imagerepo = "IMAGE/TAG/PROTECT"
    tag = "latest"
    assert localrepo.protect_imagerepo(imagerepo, tag) == expected
    # FIXME: if the mopen.call_args, call(protect, 'w') it to be tested the mock_open must be patched and the
    #  mocker.patch.object(localrepo, '_protect', return_value=protect) must be removed


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         with patch(BOPEN, mock_open()) as mopen:
#             lrepo = LocalRepository(UDOCKER_TOPDIR)
#             lrepo.protect_imagerepo("IMAGE", "TAG")
#             self.assertTrue(mopen.called)
#             protect = lrepo.reposdir + "/IMAGE/TAG/PROTECT"
#             self.assertEqual(mopen.call_args, call(protect, 'w'))
#
#     @patch('udocker.container.localrepo.FileUtil')
#     @patch.object(LocalRepository, '_unprotect')

@pytest.mark.parametrize("unprotect,expected", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_25_unprotect_imagerepo(mocker, localrepo, unprotect, expected):
    """Test25 LocalRepository().unprotected_imagerepo()."""
    mocker.patch.object(localrepo, '_unprotect', return_value=unprotect)
    imagerepo = "IMAGE/TAG/SOMEDIR"
    tag = "latest"
    assert localrepo.unprotect_imagerepo(imagerepo, tag) == expected
    # FIXME: same as test_24_protect_imagerepo


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.unprotect_imagerepo("IMAGE", "TAG")
#         self.assertTrue(mock_unprotect.called)
#
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("tag_protection,expected", [
    (True, True),
    (False, False),
])
# @pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_26_isprotected_imagerepo(mocker, localrepo, tag_protection, expected):
    """Test26 LocalRepository().isprotected_imagerepo()."""
    mocker.patch.object(localrepo, '_isprotected', return_value=tag_protection)
    imagerepo = "/IMAGE/TAG/PROTECT"
    tag = "latest"
    assert localrepo.isprotected_imagerepo(imagerepo, tag) == expected
    # FIXME: same as test_24_protect_imagerepo


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.isprotected_imagerepo("IMAGE", "TAG")
#         self.assertTrue(mock_exists.called)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         protect = lrepo.reposdir + "/IMAGE/TAG/PROTECT"
#         self.assertEqual(mock_exists.call_args, call(protect))
#
#     @patch.object(LocalRepository, '_is_tag')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("imagerepo,tag,path_exists,is_tag,expected", [
    ("sample_repo", "latest", True, True, "/home/u2/.udocker/repos/sample_repo/latest"),
    ("sample_repo", "latest", False, True, ""),
    ("sample_repo", "latest", True, False, ""),
    (None, "latest", True, True, ""),
    ("sample_repo", None, True, True, ""),
])
# @pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_27_cd_imagerepo(mocker, localrepo, imagerepo, tag, path_exists, is_tag, expected):
    """Test27 LocalRepository().cd_imagerepo()."""
    mocker.patch.object(localrepo, 'reposdir', '/home/u2/.udocker/repos')
    mocker.patch('os.path.exists', return_value=path_exists)
    mocker.patch.object(localrepo, '_is_tag', return_value=is_tag)

    assert localrepo.cd_imagerepo(imagerepo, tag) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         Config().conf['reposdir'] = "/tmp"
#         mock_exists.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         out = lrepo.cd_imagerepo("", "")
#         self.assertEqual(out, "")
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         Config().conf['reposdir'] = "/tmp"
#         mock_exists.return_value = True
#         mock_istag.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         out = lrepo.cd_imagerepo("IMAGE", "TAG")
#         self.assertEqual(out, "/tmp/IMAGE/TAG")
#
#     @patch('udocker.container.localrepo.os.path.islink')
#     @patch('udocker.container.localrepo.os.path.isdir')
#     @patch('udocker.container.localrepo.os.listdir')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("listdir_map,isdir,islink,filename,expected", [
    ({'/dir': []}, [True], False, 'test.layer', []),
    ({'/dir': ['file1.txt', 'file2.txt']}, [True, False, False], False, 'test.layer', []),
    ({'/dir': ['other.link', 'random.link']}, [True, False, False], True, 'test.layer', []),
    ({'/dir': ['test.layer']}, [True, False], True, 'test.layer', ['/dir/test.layer']),
    ({'/dir': ['subdir', 'test.layer'], '/dir/subdir': []}, [True, True, False], True, 'test.layer',
     ['/dir/test.layer']),  # this expected may be wrong, check if subdir is to be included
    ({'/dir': ['subdir1', 'subdir2'], '/dir/subdir1': ['test.layer'], '/dir/subdir2': ['other.layer', 'test.layer']},
     [True, True, True, False, False], True, 'test.layer', []),
    # expecting this, revise ['/dir/subdir1/test.layer', '/dir/subdir2/test.layer']
])
# @pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_28__find(mocker, localrepo, listdir_map, isdir, islink, filename, expected):
    """Test28 LocalRepository()._find()."""
    # isdir_iter = iter(isdir_side_effect)

    mocker.patch('os.listdir', side_effect=lambda x: listdir_map.get(x, []))
    mocker.patch('os.path.isdir', side_effect=lambda x: next(iter(isdir), False))
    mocker.patch('os.path.islink', return_value=islink)

    # FIXME: maybe flaky if list are not ordered
    assert localrepo._find(filename, '/dir') == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_fu.return_value.isdir.return_value = True
#         mock_listdir.return_value = ["file"]
#         mock_islink.return_value = True
#         filename = "file"
#         folder = "/tmp"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         out = lrepo._find(filename, folder)
#         self.assertEqual(out, ["/tmp/file"])
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_islink.return_value = False
#         mock_isdir.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         out = lrepo._find(filename, folder)
#         self.assertEqual(out, [])
#
#     @patch('udocker.container.localrepo.os.path.islink')
#     @patch('udocker.container.localrepo.os.path.isdir')
#     @patch('udocker.container.localrepo.os.listdir')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("filename,expected", [
    ('existing_file.layer', True),
    ('nonexistent_file.layer', False)
])
# @pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_29__inrepository(mocker, localrepo, filename, expected):
    """Test29 LocalRepository()._inrepository()."""
    find_result = [filename] if expected else []
    mocker.patch.object(localrepo, '_find', return_value=find_result)
    assert (localrepo._inrepository(filename) != []) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_fu.return_value.isdir.return_value = True
#         mock_listdir.return_value = ["file"]
#         mock_islink.return_value = True
#         filename = "file"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.reposdir = "/tmp"
#         out = lrepo._inrepository(filename)
#         self.assertEqual(out, ["/tmp/file"])
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_islink.return_value = False
#         mock_isdir.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         out = lrepo._inrepository(filename)
#         self.assertEqual(out, [])
#
#     @patch('udocker.container.localrepo.os.readlink')
#     @patch('udocker.container.localrepo.os.path.islink')
#     @patch('udocker.container.localrepo.os.listdir')
#     @patch.object(LocalRepository, '_inrepository')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("links_in_dir,remove_link, remove_layer,force,expected", [
    (['FILE1', 'FILE2'], True, True, False, True),
    (['FILE1', 'FILE2'], False, True, False, False),
    (['FILE1', 'FILE2'], True, False, False, False),
    (['FILE1', 'FILE2'], False, False, True, True)
])
# @pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_30__remove_layers(mocker, localrepo, links_in_dir, remove_link, remove_layer, force, expected):
    """Test30 LocalRepository()._remove_layers()."""
    tag_dir = 'TAG_DIR'
    mocker.patch('os.listdir', return_value=links_in_dir)
    mocker.patch('os.path.islink', return_value=True)
    mocker.patch('os.readlink', side_effect=lambda x: x + '_link')
    mocker.patch.object(FileUtil, 'remove', side_effect=[remove_link, remove_layer] * len(links_in_dir))
    mocker.patch.object(localrepo, '_inrepository', return_value=False)

    assert localrepo._remove_layers(tag_dir, force) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_listdir.return_value = []
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._remove_layers("TAG_DIR", False)
#         self.assertTrue(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_listdir.return_value = ["FILE1,", "FILE2"]
#         mock_islink.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._remove_layers("TAG_DIR", False)
#         self.assertTrue(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_islink.return_value = True
#         mock_readlink.return_value = "REALFILE"
#         mock_fu.return_value.remove.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._remove_layers("TAG_DIR", False)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_fu.return_value.remove.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._remove_layers("TAG_DIR", False)
#         self.assertTrue(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_fu.return_value.remove.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._remove_layers("TAG_DIR", True)
#         self.assertTrue(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_fu.return_value.remove.return_value = False
#         mock_in.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._remove_layers("TAG_DIR", True)
#         self.assertTrue(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_fu.return_value.remove.return_value = False
#         mock_in.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._remove_layers("TAG_DIR", False)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_fu.return_value.remove.return_value = False
#         mock_in.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._remove_layers("TAG_DIR", True)
#         self.assertTrue(status)
#
#     @patch.object(LocalRepository, 'cd_imagerepo')
#     @patch.object(LocalRepository, '_remove_layers')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("exist_repo,remove_layers,remove_tag_dir,expected", [
    (True, True, True, True),
    (False, True, True, False),
    (True, False, True, False),
    (True, True, False, False),
])
# @pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_31_del_imagerepo(mocker, localrepo, exist_repo, remove_layers, remove_tag_dir, expected):
    """Test31 LocalRepository()._del_imagerepo()."""
    mocker.patch.object(localrepo, 'cd_imagerepo', return_value='reposdir/imagerepo/tag' if exist_repo else "")
    mocker.patch.object(localrepo, '_remove_layers', return_value=remove_layers)
    mocker.patch.object(FileUtil, 'remove', return_value=remove_tag_dir)
    mocker.patch.object(FileUtil, 'rmdir')

    # TODO: force is used insude _remove_layers, probably is not needed here to mock, default value is False but this can
    #  be tested in test_30__remove_layers

    assert localrepo.del_imagerepo("IMAGE", "TAG") == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_cd.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.del_imagerepo("IMAGE", "TAG", False)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_cd.return_value = True
#         mock_fu.return_value.remove.return_value = True
#         mock_rmlayers.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = "XXXX"
#         lrepo.cur_tagdir = "XXXX"
#         status = lrepo.del_imagerepo("IMAGE", "TAG", False)
#         self.assertEqual(lrepo.cur_repodir, "")
#         self.assertEqual(lrepo.cur_tagdir, "")
#         self.assertTrue(status)
#
def _sideffect_test_32(self, arg):
    """Side effect for isdir on test 23 _get_tags()."""


#         if self.itr < 3:
#             self.itr += 1
#             return False
#
#         return True
#
#     @patch('udocker.container.localrepo.os.path.isdir')
#     @patch('udocker.container.localrepo.os.listdir')
#     @patch.object(LocalRepository, '_is_tag')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("directories, is_tag, expected", [
    (['/repo/tag1', '/repo/tag2'], [True, True], [('CONTAINERS_DIR', 'tag1'), ('CONTAINERS_DIR', 'tag2')]),
    (['/repo/dir1/tag1', '/repo/dir2/tag2'], [False, True, False, True], [('CONTAINERS_DIR', 'tag2')]),
    # revise scenario [('CONTAINERS_DIR', 'tag2')] and tag1
    (['/repo/tag1', '/repo/dir1/tag2'], [True, True, True], [('CONTAINERS_DIR', 'tag1'), ('CONTAINERS_DIR', 'tag2')]),
    (['/repo/dir'], [False], []),
    (['/repo/dir1', '/repo/dir2'], [False, False], [])
])
# @pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_32__get_tags(mocker, localrepo, mock_fileutil, directories, is_tag, expected):
    """Test32 LocalRepository()._get_tags()."""
    tag_dir = 'CONTAINERS_DIR'
    mocker.patch('os.listdir', return_value=[d.split('/')[-1] for d in directories])
    mocker.patch('os.path.isdir', side_effect=lambda x: x in directories and '/tag' not in x)
    mocker.patch.object(mock_fileutil, 'isdir', side_effect=lambda x: x in directories)
    mocker.patch.object(localrepo, '_is_tag', side_effect=is_tag)

    assert localrepo._get_tags(tag_dir) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isdir.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_tags("CONTAINERS_DIR")
#         self.assertEqual(status, [])
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isdir.return_value = True
#         mock_listdir.return_value = []
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_tags("CONTAINERS_DIR")
#         self.assertEqual(status, [])
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isdir.return_value = True
#         mock_listdir.return_value = ["FILE1", "FILE2"]
#         mock_is.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_tags("CONTAINERS_DIR")
#         expected_status = [('CONTAINERS_DIR', 'FILE1'), ('CONTAINERS_DIR', 'FILE2')]
#         self.assertEqual(status, expected_status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_isdir.return_value = True
#         mock_listdir.return_value = ["FILE1", "FILE2"]
#         mock_is.return_value = False
#         self.itr = 0
#         mock_isdir.side_effect = self._sideffect_test_32
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_tags("CONTAINERS_DIR")
#         expected_status = [('CONTAINERS_DIR', 'FILE1'), ('CONTAINERS_DIR', 'FILE2')]
#         self.assertEqual(self.itr, 2)
#         self.assertEqual(status, [])
#
#     @patch.object(LocalRepository, '_get_tags')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("get_tags", [
    ([]),
    ([('repo1', 'tag1'), ('repo1', 'tag2')]),
    ([('repo1', 'tag1'), ('repo2', 'tag1'), ('repo2', 'tag2')]),
])
# @pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_33_get_imagerepos(mocker, localrepo, get_tags):
    """Test33 LocalRepository().get_imagerepos()."""
    expected = get_tags
    mocker.patch.object(localrepo, '_get_tags', return_value=expected)
    assert localrepo.get_imagerepos() == expected
    # check if test _get_tags is correct


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_gtags.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.get_imagerepos()
#         self.assertTrue(mock_gtags.called)
#
#     @patch.object(LocalRepository, 'cd_imagerepo')
#     @patch('udocker.container.localrepo.os.path.islink')
#     @patch('udocker.container.localrepo.os.listdir')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("tag_dir, listdir_output, expected_output", [
    ("IMAGE/TAG/tag1", [], []),
])
# @pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_34_get_layers(mocker, localrepo, mock_fileutil, tag_dir, listdir_output, expected_output):
    """Test34 LocalRepository().get_layers()."""
    # mocker.patch.object(localrepo, 'cd_imagerepo', return_value=tag_dir)
    # mocker.patch('os.listdir', return_value=listdir_output)
    # mocker.patch('os.path.islink', side_effect=lambda x: "layer" in x)
    # mocker.patch(mock_fileutil, 'size', side_effect=lambda x: x.split('/')[-1] + "size")

    assert localrepo.get_layers("imagerepo", "tag") == expected_output


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_ldir.return_value = ""
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_layers("", "")
#         self.assertTrue(mock_cd.called)
#         self.assertEqual(status, list())
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_ldir.return_value = ["f1"]
#         mock_cd.return_value = "IMAGE/TAG"
#         mock_islink.return_value = True
#         mock_fu.return_value.size.return_value = 123
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.get_layers("IMAGE", "TAG")
#         self.assertTrue(mock_ldir.called)
#         self.assertTrue(mock_islink.called)
#         self.assertEqual(status, [("IMAGE/TAG/f1", 123)])
#
#     @patch.object(LocalRepository, '_symlink')
#     @patch('udocker.container.localrepo.os.path.basename')
#     @patch('udocker.container.localrepo.os.path.islink')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')

@pytest.mark.parametrize("cur_tagdir,filename,linkname,file_exists,tagdir_exists,expected", [
    (None, "FILE", None, True, True, False),
    ("TAG", "FILE", None, False, True, False),
    ("TAG", "FILE", "linkname", True, True, False),  # debug
])
# @pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_35_add_image_layer(mocker, localrepo, cur_tagdir, filename, linkname, file_exists, tagdir_exists, expected):
    """Test35 LocalRepository().add_image_layer()."""

    mocker.patch.object(localrepo, 'cur_tagdir', return_value=cur_tagdir)
    mocker.patch('os.path.exists',
                 side_effect=lambda x: x in [filename, cur_tagdir] if (file_exists and tagdir_exists) else False)
    mocker.patch('os.path.islink', return_value=False)
    mocker.patch.object(localrepo, '_symlink', return_value=None)

    if linkname and os.path.islink(linkname):
        mocker.patch('your_module.FileUtil.remove', return_value=True)
    # TODO: not complete
    assert localrepo.add_image_layer(filename, linkname) == expected


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = ""
#         lrepo.cur_tagdir = ""
#         status = lrepo.add_image_layer("FILE")
#         self.assertFalse(status)
#         self.assertFalse(mock_exists.called)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [False, False]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = "IMAGE"
#         lrepo.cur_tagdir = "TAG"
#         status = lrepo.add_image_layer("FILE")
#         self.assertFalse(status)
#         self.assertTrue(mock_exists.call_count, 1)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, False]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = "IMAGE"
#         lrepo.cur_tagdir = "TAG"
#         status = lrepo.add_image_layer("FILE")
#         self.assertFalse(status)
#         self.assertTrue(mock_exists.call_count, 2)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True]
#         mock_base.return_value = "file1"
#         mock_islink.return_value = True
#         mock_fu.return_value.remove.return_value = None
#         mock_symln.return_value = None
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = "IMAGE"
#         lrepo.cur_tagdir = "TAG"
#         status = lrepo.add_image_layer("FILE")
#         self.assertTrue(status)
#         self.assertTrue(mock_base.called)
#         self.assertTrue(mock_fu.return_value.remove.called)
#         self.assertTrue(mock_islink.called)
#         self.assertTrue(mock_symln.called)
#
#     @patch('udocker.container.localrepo.os.makedirs')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')
def test_36_setup_imagerepo(self, mock_fu, mock_exists, mock_mkdirs):
    """Test36 LocalRepository().setup_imagerepo()."""


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.setup_imagerepo("")
#         self.assertEqual(status, None)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.return_value = True
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.setup_imagerepo("IMAGE")
#         expected_directory = lrepo.reposdir + "/IMAGE"
#         self.assertEqual(lrepo.cur_repodir, expected_directory)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.setup_imagerepo("IMAGE")
#         expected_directory = lrepo.reposdir + "/IMAGE"
#         self.assertTrue(mock_mkdirs.called)
#         self.assertEqual(lrepo.cur_repodir, expected_directory)
#         self.assertTrue(status)
#
#     @patch('udocker.container.localrepo.os.makedirs')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')
def test_37_setup_tag(self, mock_fu, mock_exists, mock_mkdirs):
    """Test37 LocalRepository().setup_tag()."""


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
#         with patch(BOPEN, mock_open()) as mopen:
#             status = lrepo.setup_tag("NEWTAG")
#             self.assertTrue(mock_mkdirs.called)
#             expected_directory = lrepo.reposdir + "/IMAGE/NEWTAG"
#             self.assertEqual(lrepo.cur_tagdir, expected_directory)
#             self.assertTrue(mopen.called)
#             self.assertTrue(status)
#
#     @patch('udocker.container.localrepo.os.listdir')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')
def test_38_set_version(self, mock_fu, mock_exists, mock_listdir):
    """Test38 LocalRepository().set_version()."""


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.set_version("v1")
#         self.assertFalse(mock_exists.called)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [False, False]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
#         lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
#         status = lrepo.set_version("v1")
#         self.assertTrue(mock_exists.call_count, 1)
#         self.assertFalse(mock_listdir.called)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, False]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
#         lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
#         status = lrepo.set_version("v1")
#         self.assertTrue(mock_exists.call_count, 2)
#         self.assertFalse(mock_listdir.called)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True, True, True]
#         mock_listdir.return_value = ["file1"]
#         mock_fu.return_value.remove.side_effect = [None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo.set_version("v2")
#         self.assertFalse(status)
#         self.assertTrue(mock_exists.call_count, 3)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True, False, False]
#         mock_listdir.return_value = ["file1"]
#         mock_fu.return_value.remove.side_effect = [None, None]
#         with patch(BOPEN, mock_open()) as mopen:
#             lrepo = LocalRepository(UDOCKER_TOPDIR)
#             status = lrepo.set_version("v2")
#             # self.assertTrue(status)
#             self.assertTrue(mock_exists.call_count, 4)
#             # self.assertTrue(mopen.called)
#
#     @patch.object(LocalRepository, 'load_json')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')
def test_39__get_image_attr_v1(self, mock_fu, mock_exists, mock_loadjson):
    """Test39 LocalRepository()._get_image_attributes_v1()."""


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_loadjson.return_value = None
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_image_attributes_v1("/cont")
#         self.assertEqual(status, (None, None))
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_loadjson.return_value = ["lname1"]
#         mock_exists.side_effect = [False, False]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_image_attributes_v1("/cont")
#         self.assertEqual(status, (None, None))
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_loadjson.side_effect = [["lname1"], ["lname1"]]
#         mock_exists.side_effect = [True, True]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_image_attributes_v1("/cont")
#         self.assertEqual(status, (['lname1'], ['/cont/lname1.layer']))
#
#     @patch('udocker.container.localrepo.json.loads')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')
def test_40__get_image_attr_v2_s1(self, mock_fu, mock_exists, mock_jload):
    """Test40 LocalRepository()._get_image_attributes_v2_s1()."""


#         manifest = {
#             "fsLayers": ({"blobSum": "foolayername"},),
#             "history": ({"v1Compatibility": '["foojsonstring"]'},)
#         }
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [False, False]
#         mock_jload.return_value = manifest
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_image_attributes_v2_s1("/cont", manifest)
#         self.assertEqual(status, (None, None))
#
#         manifest = {
#             "fsLayers": ({"blobSum": "foolayername"},),
#             "history": ({"v1Compatibility": '["foojsonstring"]'},)
#         }
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True]
#         mock_jload.return_value = manifest
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_image_attributes_v2_s1("/cont", manifest)
#         self.assertEqual(status, (manifest, ['/cont/foolayername']))
#
#     @patch('udocker.container.localrepo.json.loads')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')
def test_41__get_image_attr_v2_s2(self, mock_fu, mock_exists, mock_jload):
    """Test41 LocalRepository()._get_image_attributes_v2_s2()."""


#         manifest = {
#             "layers": ({"digest": "foolayername"},),
#             "config": ({"digest": '["foojsonstring"]'},)
#         }
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [False, False]
#         mock_jload.return_value = manifest
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_image_attributes_v2_s2("/cont", manifest)
#         self.assertEqual(status, (None, None))
#
#         manifest = {
#             "layers": ({"digest": "foolayername"},),
#             "config": ({"digest": '["foojsonstring"]'},)
#         }
#         # res = (['foojsonstring'], ['/cont/foolayername'])
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True]
#         mock_jload.return_value = manifest
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._get_image_attributes_v2_s2("/cont", manifest)
#         self.assertEqual(status, (None, ['/cont/foolayername']))
#
#     @patch.object(LocalRepository, '_get_image_attributes_v2_s2')
#     @patch.object(LocalRepository, '_get_image_attributes_v2_s1')
#     @patch.object(LocalRepository, '_get_image_attributes_v1')
#     @patch.object(LocalRepository, 'load_json')
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')
def test_42_get_image_attributes(self, mock_fu, mock_exists, mock_loadjson, mock_attrv1, mock_attrv1s1, mock_attrv1s2):
    """Test42 LocalRepository().get_image_attributes()."""

    #         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
    #         mock_exists.side_effect = [False, False]
    #         mock_loadjson.return_value = None
    #         mock_attrv1.return_value = (None, None)
    #         lrepo = LocalRepository(UDOCKER_TOPDIR)
    #         status = lrepo.get_image_attributes()
    #         self.assertEqual(status, (None, None))
    #         self.assertTrue(mock_exists.call_count, 2)
    #
    #         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
    #         mock_exists.side_effect = [True, False]
    #         mock_loadjson.return_value = None
    #         mock_attrv1.return_value = (['lname1'], ['/cont/lname1.layer'])
    #         lrepo = LocalRepository(UDOCKER_TOPDIR)
    #         status = lrepo.get_image_attributes()
    #         self.assertEqual(status, (['lname1'], ['/cont/lname1.layer']))
    #         self.assertTrue(mock_exists.call_count, 1)
    #         self.assertTrue(mock_attrv1.call_count, 1)
    #
    #         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
    #         manifest = {
    #             "fsLayers": ({"blobSum": "foolayername"},),
    #             "history": ({"v1Compatibility": '["foojsonstring"]'},)
    #         }
    #         mock_exists.side_effect = [False, True]
    #         mock_loadjson.return_value = manifest
    #         mock_attrv1s1.return_value = (['lname1'], ['/cont/lname1.layer'])
    #         lrepo = LocalRepository(UDOCKER_TOPDIR)
    #         status = lrepo.get_image_attributes()
    #         self.assertEqual(status, (['lname1'], ['/cont/lname1.layer']))
    #         self.assertTrue(mock_exists.call_count, 1)
    #         self.assertTrue(mock_attrv1s1.call_count, 1)
    #
    #         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
    #         manifest = {
    #             "layers": ({"digest": "foolayername"},),
    #             "config": ({"digest": '["foojsonstring"]'},)
    #         }
    #         mock_exists.side_effect = [False, True]
    #         mock_loadjson.return_value = manifest
    #         mock_attrv1s2.return_value = (['lname1'], ['/cont/lname1.layer'])
    #         lrepo = LocalRepository(UDOCKER_TOPDIR)
    #         status = lrepo.get_image_attributes()
    #         self.assertEqual(status, (['lname1'], ['/cont/lname1.layer']))
    #         self.assertTrue(mock_exists.call_count, 1)
    #         self.assertTrue(mock_attrv1s2.call_count, 1)
    #
    #     @patch('udocker.container.localrepo.os.path.exists')
    #     @patch('udocker.container.localrepo.FileUtil')


def test_43_save_json(self, mock_fu, mock_exists):
    """Test43 LocalRepository().save_json()."""


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = ""
#         lrepo.cur_tagdir = ""
#         status = lrepo.save_json("filename", "data")
#         self.assertFalse(mock_exists.called)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [False, False]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
#         lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
#         status = lrepo.save_json("filename", "data")
#         self.assertTrue(mock_exists.call_count, 1)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, False]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
#         lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
#         status = lrepo.save_json("filename", "data")
#         self.assertTrue(mock_exists.call_count, 2)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True]
#         with patch(BOPEN, mock_open()) as mopen:
#             lrepo = LocalRepository(UDOCKER_TOPDIR)
#             lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
#             lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
#             status = lrepo.save_json("filename", "data")
#             self.assertTrue(mock_exists.call_count, 2)
#             self.assertTrue(mopen.called)
#             self.assertTrue(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True]
#         with patch(BOPEN, mock_open()) as mopen:
#             mopen.side_effect = IOError('foo')
#             lrepo = LocalRepository(UDOCKER_TOPDIR)
#             status = lrepo.save_json("/filename", "data")
#             self.assertTrue(mopen.called)
#             self.assertFalse(status)
#
#     @patch('udocker.container.localrepo.os.path.exists')
#     @patch('udocker.container.localrepo.FileUtil')
def test_44_load_json(self, mock_fu, mock_exists):
    """Test44 LocalRepository().load_json()."""


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = ""
#         lrepo.cur_tagdir = ""
#         status = lrepo.load_json("filename")
#         self.assertFalse(mock_exists.called)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [False, False]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
#         lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
#         status = lrepo.load_json("filename")
#         self.assertTrue(mock_exists.call_count, 1)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, False]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
#         lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
#         status = lrepo.load_json("filename")
#         self.assertTrue(mock_exists.call_count, 2)
#         self.assertFalse(status)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True]
#         with patch(BOPEN, mock_open()) as mopen:
#             lrepo = LocalRepository(UDOCKER_TOPDIR)
#             lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
#             lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
#             status = lrepo.load_json("filename")
#             self.assertTrue(mock_exists.call_count, 2)
#             self.assertTrue(mopen.called)
#             self.assertEqual(status, None)
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_exists.side_effect = [True, True]
#         with patch(BOPEN, mock_open()) as mopen:
#             mopen.side_effect = IOError('foo')
#             lrepo = LocalRepository(UDOCKER_TOPDIR)
#             status = lrepo.load_json("/filename")
#             self.assertTrue(mopen.called)
#             self.assertFalse(status)
#
#     @patch.object(LocalRepository, 'load_json')
#     @patch('udocker.container.localrepo.os.listdir')
#     @patch('udocker.container.localrepo.FileUtil')
def test_45__load_structure(self, mock_fu, mock_listdir, mock_json):
    """Test45 LocalRepository()._load_structure().
#         Scan the repository structure of a given image tag.
    """


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         mock_fu.return_value.isdir.return_value = False
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._load_structure("IMAGETAGDIR")
#         self.assertEqual(status, {"repolayers": dict()})
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         res = {'repolayers': {}, 'ancestry': {'layers': 'foolayername'}}
#         mock_fu.return_value.isdir.return_value = True
#         mock_listdir.return_value = ["ancestry"]
#         jsload = {"layers": "foolayername"}
#         mock_json.return_value = jsload
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._load_structure("IMAGETAGDIR")
#         self.assertEqual(status, res)
#
#     @patch('udocker.container.localrepo.FileUtil')
def test_46__find_top_layer_id(self, mock_fu):
    """Test46 LocalRepository()._find_top_layer_id"""


#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         struct = ""
#         lid = ""
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._find_top_layer_id(struct, lid)
#         self.assertEqual(status, "")
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         struct = {'repolayers': {"lay1": "l1",
#                                  "json": {"j1": 1, "parent": "123"}},
#                   'ancestry': {'layers': 'foolayername'}}
#         lid = "123"
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._find_top_layer_id(struct, lid)
#         self.assertEqual(status, "123")
#
def test_47__sorted_layers(self):
    """Test47 LocalRepository()._sorted_layers"""
    pass


#
#     @patch('udocker.container.localrepo.FileUtil')
def test_48__split_layer_id(self, mock_fu):
    """Test48 LocalRepository()._split_layer_id"""
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         lid = ("524b0c1e57f8ee5fee01a1decba2f301c324a6513ca3551021264e3aa7341ebc")
#         lidsha = "sha256:" + lid
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._split_layer_id(lidsha)
#         self.assertEqual(status, ["sha256", lid])
#
#         mock_fu.return_value.register_prefix.side_effect = [None, None, None]
#         lrepo = LocalRepository(UDOCKER_TOPDIR)
#         status = lrepo._split_layer_id(lid)
#         self.assertEqual(status, ("", lid))
#
# def test_49__verify_layer_file(self):
#     """Test49 LocalRepository()._verify_layer_file"""
#     pass

# def test_50__verify_image_v1(self):
#     """Test50 LocalRepository()._verify_image_v1"""
#     pass

# def test_51__verify_image_v2_s1(self):
#     """Test51 LocalRepository()._verify_image_v2_s1"""
#     pass

# def test_52__verify_image_v2_s2(self):
#     """Test52 LocalRepository()._verify_image_v2_s2"""
#     pass

# def test_53_verify_image(self):
#     """Test53 LocalRepository().verify_image"""
#     pass
#
#
# if __name__ == '__main__':
#     main()
