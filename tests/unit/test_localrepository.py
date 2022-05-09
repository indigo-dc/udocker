#!/usr/bin/env python
"""
udocker unit tests: LocalRepository
"""

from unittest import TestCase, main
from unittest.mock import patch, mock_open, call
from udocker.container.localrepo import LocalRepository
from udocker.config import Config

BUILTIN = "builtins"
BOPEN = BUILTIN + '.open'
UDOCKER_TOPDIR = "/home/u1/.udocker"


class LocalRepositoryTestCase(TestCase):
    """Management of local repository of container
    images and extracted containers
    """

    def setUp(self):
        Config().getconf()
        Config().conf['topdir'] = UDOCKER_TOPDIR
        Config().conf['bindir'] = ""
        Config().conf['libdir'] = ""
        Config().conf['reposdir'] = ""
        Config().conf['layersdir'] = ""
        Config().conf['containersdir'] = ""
        Config().conf['homedir'] = "/home/u1"

    def tearDown(self):
        pass

    @patch('udocker.container.localrepo.FileUtil')
    def test_01_init(self, mock_fu):
        """Test01 LocalRepository() constructor."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        self.assertTrue(lrepo.topdir)
        self.assertTrue(lrepo.reposdir)
        self.assertTrue(lrepo.layersdir)
        self.assertTrue(lrepo.containersdir)
        self.assertTrue(lrepo.bindir)
        self.assertTrue(lrepo.libdir)
        self.assertTrue(lrepo.homedir)
        self.assertEqual(lrepo.topdir, UDOCKER_TOPDIR)
        self.assertEqual(lrepo.cur_repodir, "")
        self.assertEqual(lrepo.cur_tagdir, "")
        self.assertEqual(lrepo.cur_containerdir, "")
        self.assertTrue(mock_fu.register_prefix.called_count, 3)

    @patch('udocker.container.localrepo.FileUtil')
    def test_02_setup(self, mock_fu):
        """Test02 LocalRepository().setup()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None, None, None, None]
        newdir = "/home/u2/.udocker"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.setup(newdir)
        self.assertEqual(lrepo.topdir, newdir)

    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.FileUtil')
    def test_03_create_repo(self, mock_fu, mock_mkdir, mock_exists):
        """Test03 LocalRepository().create_repo()."""
        Config.conf['keystore'] = "tmp"
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [False, False, False, False,
                                   False, False, False, False]
        mock_mkdir.side_effect = [None, None, None, None,
                                  None, None, None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.create_repo()
        self.assertTrue(status)
        self.assertTrue(mock_exists.call_count, 8)
        self.assertTrue(mock_mkdir.call_count, 8)

        Config.conf['keystore'] = "tmp"
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = OSError("fail")
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.create_repo()
        self.assertFalse(status)

    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_04_is_repo(self, mock_fu, mock_exists):
        """Test04 LocalRepository().is_repo()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [False, True, False, False,
                                   True]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.is_repo()
        self.assertTrue(mock_exists.call_count, 5)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True, True, True,
                                   True]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.is_repo()
        self.assertTrue(mock_exists.call_count, 5)
        self.assertTrue(status)

    @patch('udocker.container.localrepo.FileUtil')
    def test_05_is_container_id(self, mock_fu):
        """Test05 LocalRepository().is_container_id()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        contid = ""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.is_container_id(contid)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        contid = "d2578feb-acfc-37e0-8561-47335f85e46a"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.is_container_id(contid)
        self.assertTrue(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        contid = "d"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.is_container_id(contid)
        self.assertFalse(status)

    @patch.object(LocalRepository, '_protect')
    @patch('udocker.container.localrepo.FileUtil')
    def test_06_protect_container(self, mock_fu, mock_prot):
        """Test06 LocalRepository().protect_container()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        contid = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_prot.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.protect_container(contid)
        self.assertTrue(status)
        self.assertTrue(mock_prot.called)

    @patch.object(LocalRepository, '_unprotect')
    @patch('udocker.container.localrepo.FileUtil')
    def test_07_unprotect_container(self, mock_fu, mock_unprot):
        """Test07 LocalRepository().unprotect_container()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        contid = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_unprot.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.unprotect_container(contid)
        self.assertTrue(status)
        self.assertTrue(mock_unprot.called)

    @patch.object(LocalRepository, '_isprotected')
    @patch('udocker.container.localrepo.FileUtil')
    def test_08_isprotected_container(self, mock_fu, mock_isprot):
        """Test08 LocalRepository().isprotected_container()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        contid = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_isprot.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.isprotected_container(contid)
        self.assertTrue(status)
        self.assertTrue(mock_isprot.called)

    @patch('udocker.container.localrepo.FileUtil')
    def test_09__protect(self, mock_fu):
        """Test09 LocalRepository()._protect()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        cdir = "/home/u1/.udocker/contid"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        with patch(BOPEN, mock_open()):
            status = lrepo._protect(cdir)
            self.assertTrue(status)

    @patch('udocker.container.localrepo.FileUtil')
    def test_10__unprotect(self, mock_fu):
        """Test10 LocalRepository()._unprotect()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        cdir = "/home/u1/.udocker/contid"
        mock_fu.return_value.remove.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._unprotect(cdir)
        self.assertTrue(status)
        self.assertTrue(mock_fu.return_value.remove.called)

    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_11__isprotected(self, mock_fu, mock_exists):
        """Test11 LocalRepository()._isprotected()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        cdir = "/home/u1/.udocker/contid"
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._isprotected(cdir)
        self.assertTrue(status)
        self.assertTrue(mock_exists.called)

    @patch.object(LocalRepository, 'cd_container')
    @patch('udocker.container.localrepo.os.access')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_12_iswriteable_container(self, mock_fu, mock_exists,
                                      mock_isdir, mock_access,
                                      mock_cdcont):
        """Test12 LocalRepository().iswriteable_container()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_exists.return_value = False
        mock_cdcont.return_value = "/home/u1/.udocker/containerid"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.iswriteable_container(container_id)
        self.assertEqual(status, 2)
        self.assertTrue(mock_exists.called)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.return_value = True
        mock_isdir.return_value = False
        mock_cdcont.return_value = "/home/u1/.udocker/containerid"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.iswriteable_container(container_id)
        self.assertEqual(status, 3)
        self.assertTrue(mock_isdir.called)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = True
        mock_cdcont.return_value = "/home/u1/.udocker/containerid"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.iswriteable_container(container_id)
        self.assertEqual(status, 1)
        self.assertTrue(mock_access.called)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = False
        mock_cdcont.return_value = "/home/u1/.udocker/containerid"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.iswriteable_container(container_id)
        self.assertEqual(status, 0)

    @patch.object(LocalRepository, 'cd_container')
    @patch('udocker.container.localrepo.Uprocess.get_output')
    @patch('udocker.container.localrepo.FileUtil')
    def test_13_get_size(self, mock_fu, mock_getout, mock_cdcont):
        """Test13 LocalRepository().get_size()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_getout.return_value = "1234 dd"
        mock_cdcont.return_value = "/home/u1/.udocker/containerid"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_size(container_id)
        self.assertEqual(status, 1234)
        self.assertTrue(mock_getout.called)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_getout.return_value = ""
        mock_cdcont.return_value = "/home/u1/.udocker/containerid"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_size(container_id)
        self.assertEqual(status, -1)

    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.FileUtil')
    def test_14_get_containers_list(self, mock_fu, mock_isdir,
                                    mock_listdir):
        """Test14 LocalRepository().get_containers_list()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isdir.return_value = False
        mock_listdir.return_value = list()
        cdir = "/home/u1/.udocker/containers"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_containers_list()
        self.assertEqual(status, list())
        self.assertEqual(lrepo.containersdir, cdir)
        self.assertFalse(mock_listdir.called)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isdir.return_value = True
        mock_listdir.return_value = list()
        cdir = "/home/u1/.udocker/containers"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_containers_list()
        self.assertEqual(status, list())
        self.assertTrue(mock_listdir.called)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isdir.side_effect = [True, False]
        cdir = "/home/u1/.udocker/containers"
        mock_listdir.return_value = [cdir]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_containers_list()
        self.assertEqual(status, list())
        self.assertTrue(mock_listdir.called)
        self.assertTrue(mock_isdir.call_count, 2)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isdir.side_effect = [True, True]
        cdir = "/home/u1/.udocker/containers"
        mock_listdir.return_value = ["a"]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        with patch(BOPEN, mock_open()):
            status = lrepo.get_containers_list()
            self.assertEqual(status, [cdir + "/" + "a"])
            self.assertTrue(mock_listdir.called)
            self.assertTrue(mock_isdir.call_count, 2)

    @patch.object(LocalRepository, 'del_container_name')
    @patch.object(LocalRepository, 'cd_container')
    @patch.object(LocalRepository, 'get_container_name')
    @patch.object(LocalRepository, 'get_containers_list')
    @patch('udocker.container.localrepo.FileUtil')
    def test_15_del_container(self, mock_fu,
                              mock_getlist, mock_getname,
                              mock_cdcont, mock_delname):
        """Test15 LocalRepository().del_container()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        cont_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_cdcont.return_value = ""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.del_container(cont_id)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        cont_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        cdirs = "/home/u1/.udocker/containers"
        contdir = cdirs + "/" + cont_id
        mock_cdcont.return_value = contdir
        mock_getlist.return_value = [contdir]
        mock_delname.return_value = None
        mock_getname.return_value = ["mycont"]
        mock_fu.return_value.remove.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.del_container(cont_id)
        self.assertFalse(status)
        self.assertTrue(mock_getlist.called)
        self.assertTrue(mock_delname.called)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        cont_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        cdirs = "/home/u1/.udocker/containers"
        contdir = cdirs + "/" + cont_id
        mock_cdcont.return_value = contdir
        mock_getlist.return_value = [contdir]
        mock_delname.return_value = None
        mock_getname.return_value = ["mycont"]
        mock_fu.return_value.remove.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.del_container(cont_id)
        self.assertTrue(status)
        self.assertTrue(mock_fu.return_value.remove.called)

    @patch.object(LocalRepository, 'get_containers_list')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_16_cd_container(self, mock_fu, mock_exists,
                             mock_getlist):
        """Test16 LocalRepository().cd_container()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        cont_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        cdirs = "/home/u1/.udocker/containers"
        contdir = cdirs + "/" + cont_id
        mock_getlist.return_value = [contdir]
        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.cd_container(cont_id)
        self.assertEqual(status, "")

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        cont_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        cdirs = "/home/u1/.udocker/containers"
        contdir = cdirs + "/" + cont_id
        mock_getlist.return_value = [contdir]
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.cd_container(cont_id)
        self.assertEqual(status, contdir)

    @patch('udocker.container.localrepo.os.path.relpath')
    @patch('udocker.container.localrepo.os.symlink')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_17__symlink(self, mock_fu, mock_exists,
                         mock_symlink, mock_relpath):
        """Test17 LocalRepository()._symlink()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.return_value = False
        mock_symlink.return_value = None
        mock_relpath.return_value = "cont/ROOT"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertTrue(status)

    @patch('udocker.container.localrepo.FileUtil')
    def test_18__name_is_valid(self, mock_fu):
        """Test18 LocalRepository()._name_is_valid().
        Check name alias validity.
        """
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        name = "lzskjghdlak"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertTrue(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        name = "lzskjghd/lak"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        name = ".lzsklak"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        name = "]lzsklak"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        name = "lzs[klak"
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        name = "lzs klak"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        name = "x" * 2049
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

    @patch('udocker.container.localrepo.os.path.exists')
    @patch.object(LocalRepository, '_symlink')
    @patch.object(LocalRepository, 'cd_container')
    @patch('udocker.container.localrepo.FileUtil')
    def test_18_set_container_name(self, mock_fu, mock_cd,
                                   mock_slink, mock_exists):
        """Test18 LocalRepository().set_container_name()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.set_container_name(container_id, "WRONG[/")
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.set_container_name(container_id, "RIGHT")
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = False
        mock_slink.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.set_container_name(container_id, "RIGHT")
        self.assertTrue(status)

    @patch.object(LocalRepository, '_name_is_valid')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.FileUtil')
    def test_19_del_container_name(self, mock_fu,
                                   mock_islink, mock_nameisvalid):
        """Test19 LocalRepository().del_container_name()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        contname = "mycont"
        mock_nameisvalid.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.del_container_name(contname)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        contname = "mycont"
        mock_nameisvalid.return_value = True
        mock_islink.return_value = True
        mock_fu.return_value.remove.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.del_container_name(contname)
        self.assertTrue(status)

    @patch('udocker.container.localrepo.os.readlink')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.FileUtil')
    def test_20_get_container_id(self, mock_fu, mock_islink,
                                 mock_isdir, mock_readlink):
        """Test20 LocalRepository().get_container_id()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_container_id(None)
        self.assertEqual(status, "")

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_islink.return_value = True
        mock_readlink.return_value = "BASENAME"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "BASENAME")

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_islink.return_value = False
        mock_isdir.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "")

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_islink.return_value = False
        mock_isdir.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "ALIASNAM")

    @patch('udocker.container.localrepo.os.readlink')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.FileUtil')
    def test_21_get_container_name(self, mock_fu, mock_isdir,
                                   mock_listdir,
                                   mock_islink, mock_readlink):
        """Test21 LocalRepository().get_container_name()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isdir.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        name_list = lrepo.get_container_name("IMAGE:TAG")
        self.assertEqual(name_list, list())

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isdir.return_value = True
        mock_listdir.return_value = ['LINK']
        mock_islink.return_value = True
        mock_readlink.return_value = "/a/b/IMAGE:TAG"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        name_list = lrepo.get_container_name("IMAGE:TAG")
        self.assertEqual(name_list, ["LINK"])

    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_22_setup_container(self, mock_fu, mock_exists,
                                mock_makedirs):
        """Test22 LocalRepository().setup_container()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.setup_container("REPO", "TAG", "ID")
        self.assertEqual(status, "")

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.return_value = False
        mock_makedirs.return_value = None
        with patch(BOPEN, mock_open()):
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            status = lrepo.setup_container("REPO", "TAG", "ID")
            self.assertEqual(status, lrepo.containersdir + "/ID")
            self.assertEqual(lrepo.cur_containerdir,
                             lrepo.containersdir + "/ID")

    @patch('udocker.container.localrepo.os.path.isfile')
    @patch('udocker.container.localrepo.FileUtil')
    def test_23__is_tag(self, mock_fu, mock_isfile):
        """Test23 LocalRepository()._is_tag()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isfile.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._is_tag("tagdir")
        self.assertTrue(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isfile.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._is_tag("tagdir")
        self.assertFalse(status)

    @patch('udocker.container.localrepo.FileUtil')
    def test_24_protect_imagerepo(self, mock_fu):
        """Test24 LocalRepository().protect_imagerepo()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        with patch(BOPEN, mock_open()) as mopen:
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            lrepo.protect_imagerepo("IMAGE", "TAG")
            self.assertTrue(mopen.called)
            protect = lrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mopen.call_args, call(protect, 'w', encoding='utf-8'))

    @patch('udocker.container.localrepo.FileUtil')
    @patch.object(LocalRepository, '_unprotect')
    def test_25_unprotect_imagerepo(self, mock_fu, mock_unprotect):
        """Test25 LocalRepository().unprotected_imagerepo()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.unprotect_imagerepo("IMAGE", "TAG")
        self.assertTrue(mock_unprotect.called)

    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_26_isprotected_imagerepo(self, mock_fu, mock_exists):
        """Test26 LocalRepository().isprotected_imagerepo()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.isprotected_imagerepo("IMAGE", "TAG")
        self.assertTrue(mock_exists.called)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        protect = lrepo.reposdir + "/IMAGE/TAG/PROTECT"
        self.assertEqual(mock_exists.call_args, call(protect))

    @patch.object(LocalRepository, '_is_tag')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_27_cd_imagerepo(self, mock_fu, mock_exists, mock_istag):
        """Test27 LocalRepository().cd_imagerepo()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        Config().conf['reposdir'] = "/tmp"
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        out = lrepo.cd_imagerepo("", "")
        self.assertEqual(out, "")

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        Config().conf['reposdir'] = "/tmp"
        mock_exists.return_value = True
        mock_istag.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        out = lrepo.cd_imagerepo("IMAGE", "TAG")
        self.assertEqual(out, "/tmp/IMAGE/TAG")

    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.FileUtil')
    def test_28__find(self, mock_fu, mock_listdir, mock_isdir, mock_islink):
        """Test28 LocalRepository()._find()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_fu.return_value.isdir.return_value = True
        mock_listdir.return_value = ["file"]
        mock_islink.return_value = True
        filename = "file"
        folder = "/tmp"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        out = lrepo._find(filename, folder)
        self.assertEqual(out, ["/tmp/file"])

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_islink.return_value = False
        mock_isdir.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        out = lrepo._find(filename, folder)
        self.assertEqual(out, [])

    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.FileUtil')
    def test_29__inrepository(self, mock_fu, mock_listdir,
                              mock_isdir, mock_islink):
        """Test29 LocalRepository()._inrepository()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_fu.return_value.isdir.return_value = True
        mock_listdir.return_value = ["file"]
        mock_islink.return_value = True
        filename = "file"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.reposdir = "/tmp"
        out = lrepo._inrepository(filename)
        self.assertEqual(out, ["/tmp/file"])

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_islink.return_value = False
        mock_isdir.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        out = lrepo._inrepository(filename)
        self.assertEqual(out, [])

    @patch('udocker.container.localrepo.os.readlink')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.listdir')
    @patch.object(LocalRepository, '_inrepository')
    @patch('udocker.container.localrepo.FileUtil')
    def test_30__remove_layers(self, mock_fu, mock_in, mock_listdir,
                               mock_islink, mock_readlink):
        """Test30 LocalRepository()._remove_layers()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_listdir.return_value = []
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_listdir.return_value = ["FILE1,", "FILE2"]
        mock_islink.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_islink.return_value = True
        mock_readlink.return_value = "REALFILE"
        mock_fu.return_value.remove.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_fu.return_value.remove.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_fu.return_value.remove.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_fu.return_value.remove.return_value = False
        mock_in.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_fu.return_value.remove.return_value = False
        mock_in.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_fu.return_value.remove.return_value = False
        mock_in.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)

    @patch.object(LocalRepository, 'cd_imagerepo')
    @patch.object(LocalRepository, '_remove_layers')
    @patch('udocker.container.localrepo.FileUtil')
    def test_31_del_imagerepo(self, mock_fu, mock_rmlayers, mock_cd):
        """Test31 LocalRepository()._del_imagerepo()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_cd.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_cd.return_value = True
        mock_fu.return_value.remove.return_value = True
        mock_rmlayers.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = "XXXX"
        lrepo.cur_tagdir = "XXXX"
        status = lrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertEqual(lrepo.cur_repodir, "")
        self.assertEqual(lrepo.cur_tagdir, "")
        self.assertTrue(status)

    def _sideffect_test_32(self, arg):
        """Side effect for isdir on test 23 _get_tags()."""
        if self.itr < 3:
            self.itr += 1
            return False

        return True

    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.listdir')
    @patch.object(LocalRepository, '_is_tag')
    @patch('udocker.container.localrepo.FileUtil')
    def test_32__get_tags(self, mock_fu, mock_is,
                          mock_listdir, mock_isdir):
        """Test32 LocalRepository()._get_tags()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isdir.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isdir.return_value = True
        mock_listdir.return_value = []
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(status, expected_status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        self.itr = 0
        mock_isdir.side_effect = self._sideffect_test_32
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(self.itr, 2)
        self.assertEqual(status, [])

    @patch.object(LocalRepository, '_get_tags')
    @patch('udocker.container.localrepo.FileUtil')
    def test_33_get_imagerepos(self, mock_fu, mock_gtags):
        """Test33 LocalRepository().get_imagerepos()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_gtags.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.get_imagerepos()
        self.assertTrue(mock_gtags.called)

    @patch.object(LocalRepository, 'cd_imagerepo')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.FileUtil')
    def test_34_get_layers(self, mock_fu, mock_ldir,
                           mock_islink, mock_cd):
        """Test34 LocalRepository().get_layers()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_ldir.return_value = ""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_layers("", "")
        self.assertTrue(mock_cd.called)
        self.assertEqual(status, list())

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_ldir.return_value = ["f1"]
        mock_cd.return_value = "IMAGE/TAG"
        mock_islink.return_value = True
        mock_fu.return_value.size.return_value = 123
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_layers("IMAGE", "TAG")
        self.assertTrue(mock_ldir.called)
        self.assertTrue(mock_islink.called)
        self.assertEqual(status, [("IMAGE/TAG/f1", 123)])

    @patch.object(LocalRepository, '_symlink')
    @patch('udocker.container.localrepo.os.path.basename')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_35_add_image_layer(self, mock_fu, mock_exists,
                                mock_islink, mock_base, mock_symln):
        """Test35 LocalRepository().add_image_layer()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = ""
        lrepo.cur_tagdir = ""
        status = lrepo.add_image_layer("FILE")
        self.assertFalse(status)
        self.assertFalse(mock_exists.called)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [False, False]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = "IMAGE"
        lrepo.cur_tagdir = "TAG"
        status = lrepo.add_image_layer("FILE")
        self.assertFalse(status)
        self.assertTrue(mock_exists.call_count, 1)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, False]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = "IMAGE"
        lrepo.cur_tagdir = "TAG"
        status = lrepo.add_image_layer("FILE")
        self.assertFalse(status)
        self.assertTrue(mock_exists.call_count, 2)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True]
        mock_base.return_value = "file1"
        mock_islink.return_value = True
        mock_fu.return_value.remove.return_value = None
        mock_symln.return_value = None
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = "IMAGE"
        lrepo.cur_tagdir = "TAG"
        status = lrepo.add_image_layer("FILE")
        self.assertTrue(status)
        self.assertTrue(mock_base.called)
        self.assertTrue(mock_fu.return_value.remove.called)
        self.assertTrue(mock_islink.called)
        self.assertTrue(mock_symln.called)

    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_36_setup_imagerepo(self, mock_fu, mock_exists,
                                mock_mkdirs):
        """Test36 LocalRepository().setup_imagerepo()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.setup_imagerepo("")
        self.assertEqual(status, None)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.setup_imagerepo("IMAGE")
        expected_directory = lrepo.reposdir + "/IMAGE"
        self.assertEqual(lrepo.cur_repodir, expected_directory)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.setup_imagerepo("IMAGE")
        expected_directory = lrepo.reposdir + "/IMAGE"
        self.assertTrue(mock_mkdirs.called)
        self.assertEqual(lrepo.cur_repodir, expected_directory)
        self.assertTrue(status)

    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_37_setup_tag(self, mock_fu, mock_exists, mock_mkdirs):
        """Test37 LocalRepository().setup_tag()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        with patch(BOPEN, mock_open()) as mopen:
            status = lrepo.setup_tag("NEWTAG")
            self.assertTrue(mock_mkdirs.called)
            expected_directory = lrepo.reposdir + "/IMAGE/NEWTAG"
            self.assertEqual(lrepo.cur_tagdir, expected_directory)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_38_set_version(self, mock_fu, mock_exists,
                            mock_listdir):
        """Test38 LocalRepository().set_version()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.set_version("v1")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [False, False]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
        status = lrepo.set_version("v1")
        self.assertTrue(mock_exists.call_count, 1)
        self.assertFalse(mock_listdir.called)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, False]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
        status = lrepo.set_version("v1")
        self.assertTrue(mock_exists.call_count, 2)
        self.assertFalse(mock_listdir.called)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True, True, True]
        mock_listdir.return_value = ["file1"]
        mock_fu.return_value.remove.side_effect = \
            [None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.set_version("v2")
        self.assertFalse(status)
        self.assertTrue(mock_exists.call_count, 3)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True, False, False]
        mock_listdir.return_value = ["file1"]
        mock_fu.return_value.remove.side_effect = \
            [None, None]
        with patch(BOPEN, mock_open()) as mopen:
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            status = lrepo.set_version("v2")
            # self.assertTrue(status)
            self.assertTrue(mock_exists.call_count, 4)
            # self.assertTrue(mopen.called)

    @patch.object(LocalRepository, 'load_json')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_39__get_image_attr_v1(self, mock_fu, mock_exists,
                                   mock_loadjson):
        """Test39 LocalRepository()._get_image_attributes_v1()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_loadjson.return_value = None
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_image_attributes_v1("/cont")
        self.assertEqual(status, (None, None))

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_loadjson.return_value = ["lname1"]
        mock_exists.side_effect = [False, False]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_image_attributes_v1("/cont")
        self.assertEqual(status, (None, None))

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_loadjson.side_effect = [["lname1"], ["lname1"]]
        mock_exists.side_effect = [True, True]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_image_attributes_v1("/cont")
        self.assertEqual(status, (['lname1'], ['/cont/lname1.layer']))

    @patch('udocker.container.localrepo.json.loads')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_40__get_image_attr_v2_s1(self, mock_fu, mock_exists,
                                      mock_jload):
        """Test40 LocalRepository()._get_image_attributes_v2_s1()."""
        manifest = {
            "fsLayers": ({"blobSum": "foolayername"},),
            "history": ({"v1Compatibility": '["foojsonstring"]'},)
        }
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [False, False]
        mock_jload.return_value = manifest
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_image_attributes_v2_s1("/cont", manifest)
        self.assertEqual(status, (None, None))

        manifest = {
            "fsLayers": ({"blobSum": "foolayername"},),
            "history": ({"v1Compatibility": '["foojsonstring"]'},)
        }
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True]
        mock_jload.return_value = manifest
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_image_attributes_v2_s1("/cont", manifest)
        self.assertEqual(status, (manifest, ['/cont/foolayername']))

    @patch('udocker.container.localrepo.json.loads')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_41__get_image_attr_v2_s2(self, mock_fu, mock_exists,
                                      mock_jload):
        """Test41 LocalRepository()._get_image_attributes_v2_s2()."""
        manifest = {
            "layers": ({"digest": "foolayername"},),
            "config": ({"digest": '["foojsonstring"]'},)
        }
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [False, False]
        mock_jload.return_value = manifest
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_image_attributes_v2_s2("/cont", manifest)
        self.assertEqual(status, (None, None))

        manifest = {
            "layers": ({"digest": "foolayername"},),
            "config": ({"digest": '["foojsonstring"]'},)
        }
        # res = (['foojsonstring'], ['/cont/foolayername'])
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True]
        mock_jload.return_value = manifest
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._get_image_attributes_v2_s2("/cont", manifest)
        self.assertEqual(status, (None, ['/cont/foolayername']))

    @patch.object(LocalRepository, '_get_image_attributes_v2_s2')
    @patch.object(LocalRepository, '_get_image_attributes_v2_s1')
    @patch.object(LocalRepository, '_get_image_attributes_v1')
    @patch.object(LocalRepository, 'load_json')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_42_get_image_attributes(self, mock_fu, mock_exists,
                                     mock_loadjson, mock_attrv1,
                                     mock_attrv1s1, mock_attrv1s2):
        """Test42 LocalRepository().get_image_attributes()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [False, False]
        mock_loadjson.return_value = None
        mock_attrv1.return_value = (None, None)
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_image_attributes()
        self.assertEqual(status, (None, None))
        self.assertTrue(mock_exists.call_count, 2)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, False]
        mock_loadjson.return_value = None
        mock_attrv1.return_value = (['lname1'], ['/cont/lname1.layer'])
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_image_attributes()
        self.assertEqual(status, (['lname1'], ['/cont/lname1.layer']))
        self.assertTrue(mock_exists.call_count, 1)
        self.assertTrue(mock_attrv1.call_count, 1)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        manifest = {
            "fsLayers": ({"blobSum": "foolayername"},),
            "history": ({"v1Compatibility": '["foojsonstring"]'},)
        }
        mock_exists.side_effect = [False, True]
        mock_loadjson.return_value = manifest
        mock_attrv1s1.return_value = (['lname1'], ['/cont/lname1.layer'])
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_image_attributes()
        self.assertEqual(status, (['lname1'], ['/cont/lname1.layer']))
        self.assertTrue(mock_exists.call_count, 1)
        self.assertTrue(mock_attrv1s1.call_count, 1)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        manifest = {
            "layers": ({"digest": "foolayername"},),
            "config": ({"digest": '["foojsonstring"]'},)
        }
        mock_exists.side_effect = [False, True]
        mock_loadjson.return_value = manifest
        mock_attrv1s2.return_value = (['lname1'], ['/cont/lname1.layer'])
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.get_image_attributes()
        self.assertEqual(status, (['lname1'], ['/cont/lname1.layer']))
        self.assertTrue(mock_exists.call_count, 1)
        self.assertTrue(mock_attrv1s2.call_count, 1)

    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_43_save_json(self, mock_fu, mock_exists):
        """Test43 LocalRepository().save_json()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = ""
        lrepo.cur_tagdir = ""
        status = lrepo.save_json("filename", "data")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [False, False]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
        status = lrepo.save_json("filename", "data")
        self.assertTrue(mock_exists.call_count, 1)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, False]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
        status = lrepo.save_json("filename", "data")
        self.assertTrue(mock_exists.call_count, 2)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True]
        with patch(BOPEN, mock_open()) as mopen:
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
            lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
            status = lrepo.save_json("filename", "data")
            self.assertTrue(mock_exists.call_count, 2)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True]
        with patch(BOPEN, mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            status = lrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_44_load_json(self, mock_fu, mock_exists):
        """Test44 LocalRepository().load_json()."""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = ""
        lrepo.cur_tagdir = ""
        status = lrepo.load_json("filename")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [False, False]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
        status = lrepo.load_json("filename")
        self.assertTrue(mock_exists.call_count, 1)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, False]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
        status = lrepo.load_json("filename")
        self.assertTrue(mock_exists.call_count, 2)
        self.assertFalse(status)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True]
        with patch(BOPEN, mock_open()) as mopen:
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
            lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
            status = lrepo.load_json("filename")
            self.assertTrue(mock_exists.call_count, 2)
            self.assertTrue(mopen.called)
            self.assertEqual(status, None)

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_exists.side_effect = [True, True]
        with patch(BOPEN, mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            status = lrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @patch.object(LocalRepository, 'load_json')
    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.FileUtil')
    def test_45__load_structure(self, mock_fu, mock_listdir,
                                mock_json):
        """Test45 LocalRepository()._load_structure().
        Scan the repository structure of a given image tag.
        """
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        mock_fu.return_value.isdir.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._load_structure("IMAGETAGDIR")
        self.assertEqual(status, {"repolayers": dict()})

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        res = {'repolayers': {}, 'ancestry': {'layers': 'foolayername'}}
        mock_fu.return_value.isdir.return_value = True
        mock_listdir.return_value = ["ancestry"]
        jsload = {"layers": "foolayername"}
        mock_json.return_value = jsload
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._load_structure("IMAGETAGDIR")
        self.assertEqual(status, res)

    @patch('udocker.container.localrepo.FileUtil')
    def test_46__find_top_layer_id(self, mock_fu):
        """Test46 LocalRepository()._find_top_layer_id"""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        struct = ""
        lid = ""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._find_top_layer_id(struct, lid)
        self.assertEqual(status, "")

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        struct = {'repolayers': {"lay1": "l1",
                                 "json": {"j1": 1, "parent": "123"}},
                  'ancestry': {'layers': 'foolayername'}}
        lid = "123"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._find_top_layer_id(struct, lid)
        self.assertEqual(status, "123")

    # def test_47__sorted_layers(self):
    #     """Test47 LocalRepository()._sorted_layers"""
    #     pass

    @patch('udocker.container.localrepo.FileUtil')
    def test_48__split_layer_id(self, mock_fu):
        """Test48 LocalRepository()._split_layer_id"""
        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        lid = ("524b0c1e57f8ee5fee01a1decba2f30"
               "1c324a6513ca3551021264e3aa7341ebc")
        lidsha = "sha256:" + lid
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._split_layer_id(lidsha)
        self.assertEqual(status, ["sha256", lid])

        mock_fu.return_value.register_prefix.side_effect = \
            [None, None, None]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._split_layer_id(lid)
        self.assertEqual(status, ("", lid))

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


if __name__ == '__main__':
    main()
