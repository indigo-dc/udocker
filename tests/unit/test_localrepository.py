#!/usr/bin/env python
"""
udocker unit tests: LocalRepository
"""
import sys
import os
import subprocess
from unittest import TestCase, main
from udocker.container.localrepo import LocalRepository
from udocker.config import Config
try:
    from unittest.mock import patch, mock_open, call
except ImportError:
    from mock import patch, mock_open, call

try:
    from io import BytesIO as bytestr
except ImportError:
    from StringIO import StringIO as bytestr

if sys.version_info[0] >= 3:
    BUILTIN = "builtins"
else:
    BUILTIN = "__builtin__"

BOPEN = BUILTIN + '.open'
UDOCKER_TOPDIR = "test_topdir"


class LocalRepositoryTestCase(TestCase):
    """Management of local repository of container
    images and extracted containers
    """

    def setUp(self):
        Config().getconf()
        Config().conf['topdir'] = UDOCKER_TOPDIR
        Config().conf['tmpdir'] = "/tmp"
        Config().conf['homedir'] = "/tmp"
        Config().conf['bindir'] = ""
        Config().conf['libdir'] = ""
        Config().conf['reposdir'] = ""
        Config().conf['layersdir'] = ""
        Config().conf['containersdir'] = ""

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test LocalRepository() constructor."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        self.assertTrue(lrepo.topdir)
        self.assertTrue(lrepo.reposdir)
        self.assertTrue(lrepo.layersdir)
        self.assertTrue(lrepo.containersdir)
        self.assertTrue(lrepo.bindir)
        self.assertTrue(lrepo.libdir)
        self.assertTrue(lrepo.homedir)
        self.assertEqual(lrepo.cur_repodir, "")
        self.assertEqual(lrepo.cur_tagdir, "")
        self.assertEqual(lrepo.cur_containerdir, "")

    def test_02_setup(self):
        """Test LocalRepository().setup()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        self.assertEqual(os.path.basename(lrepo.topdir), UDOCKER_TOPDIR)

        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.setup("YYYY")
        self.assertEqual(os.path.basename(lrepo.topdir), "YYYY")

    # def test_03_sha256(self):
    #     """Test LocalRepository().sha256()."""
    #     sha256sum = (
    #         "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     file_data = bytestr("qwerty".encode())
    #     if sys.version_info[0] < 3:   # TODO: implement for python3
    #         with patch(BOPEN, mock_open()) as mopen:
    #             mopen.return_value.__iter__ = \
    #                 (lambda self: iter(file_data.readline, ''))
    #             status = lrepo.sha256("filename")
    #             self.assertEqual(status, sha256sum)

    #     with patch(BOPEN, mock_open()) as mopen:
    #         mopen.side_effect = IOError
    #         status = lrepo.sha256("filename")
    #         self.assertRaises(IOError)
    #         self.assertEqual(status, "")

    def test_04_create_repo(self):
        """Test LocalRepository().create_repo()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        subprocess.call(["/bin/rm", "-Rf", lrepo.topdir])
        self.assertFalse(os.path.exists(lrepo.topdir))

        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.create_repo()
        self.assertTrue(os.path.exists(lrepo.topdir))
        self.assertTrue(os.path.exists(lrepo.reposdir))
        self.assertTrue(os.path.exists(lrepo.layersdir))
        self.assertTrue(os.path.exists(lrepo.containersdir))
        self.assertTrue(os.path.exists(lrepo.bindir))
        self.assertTrue(os.path.exists(lrepo.libdir))
        subprocess.call(["/bin/rm", "-Rf", lrepo.topdir])

    def test_05_is_repo(self):
        """Test LocalRepository().is_repo()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        subprocess.call(["/bin/rm", "-Rf", lrepo.topdir])
        lrepo.create_repo()
        self.assertTrue(lrepo.is_repo())
        subprocess.call(["/bin/rm", "-Rf", lrepo.topdir])

    @patch('udocker.container.localrepo.os.readlink')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.os.path.isdir')
    def test_06_get_container_name(self, mock_isdir, mock_listdir,
                                   mock_islink, mock_readlink):
        """Test LocalRepository().get_container_name()."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ['LINK']
        mock_islink.return_value = True
        mock_readlink.return_value = "/a/b/IMAGE:TAG"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        name_list = lrepo.get_container_name("IMAGE:TAG")
        self.assertEqual(name_list, ["LINK"])

    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.listdir')
    def test_07a_get_containers_list(self, mock_listdir, mock_isdir):
        """Test LocalRepository().get_containers_list() - 01."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ['LINK']
        with patch(BOPEN, mock_open(read_data='REPONAME')):
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            containers_list = lrepo.get_containers_list()
            self.assertEqual(os.path.basename(containers_list[0]), "LINK")

    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.LocalRepository.get_container_name')
    def test_07b_get_containers_list(self, mock_getname, mock_isdir,
                                     mock_listdir, mock_islink):
        """Test LocalRepository().get_containers_list() - 02."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ['LINK']
        mock_islink.return_value = False
        mock_getname.return_value = ["NAME1", "NAME2"]
        with patch(BOPEN, mock_open(read_data='REPONAME')):
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            containers_list = lrepo.get_containers_list(False)
            self.assertEqual(os.path.basename(containers_list[0][1]),
                             "REPONAME")

    @patch('udocker.container.localrepo.os.path.exists')
    @patch.object(LocalRepository, 'get_containers_list')
    def test_08_cd_container(self, mock_getlist, mock_exists):
        """Test LocalRepository().cd_container()."""
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        mock_getlist.return_value = [lrepo.containersdir +
                                     "/CONTAINERNAME"]
        container_path = lrepo.cd_container("CONTAINERNAME")
        self.assertEqual(container_path, mock_getlist.return_value[0])

    def test_09_protect_container(self):
        """Test LocalRepository().protect_container()."""
        with patch(BOPEN, mock_open()) as mopen:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            lrepo.protect_container(container_id)
            self.assertTrue(mopen.called)
            self.assertEqual(mopen.call_args, call('/PROTECT', 'w'))

    @patch('udocker.container.localrepo.os.path.exists')
    def test_10_isprotected_container(self, mock_exists):
        """Test LocalRepository().isprotected_container() - Protected."""
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.isprotected_container(container_id)
        self.assertTrue(mock_exists.called)
        self.assertEqual(mock_exists.call_args, call('/PROTECT'))

    @patch.object(LocalRepository, 'cd_container')
    @patch.object(LocalRepository, '_unprotect')
    def test_11_unprotect_container(self, mock_unprotect, mock_cdcont):
        """Test LocalRepository().isprotected_container() - Unprotected."""
        mock_cdcont.return_value = "/tmp"
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.unprotect_container(container_id)
        self.assertTrue(mock_unprotect.called)

    def test_12_protect_imagerepo(self):
        """Test LocalRepository().protect_imagerepo()."""
        with patch(BOPEN, mock_open()) as mopen:
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            lrepo.protect_imagerepo("IMAGE", "TAG")
            self.assertTrue(mopen.called)
            protect = lrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mopen.call_args, call(protect, 'w'))

    @patch('udocker.container.localrepo.os.path.exists')
    def test_13_isprotected_imagerepo(self, mock_exists):
        """Test LocalRepository().isprotected_imagerepo()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.isprotected_imagerepo("IMAGE", "TAG")
        self.assertTrue(mock_exists.called)

        lrepo = LocalRepository(UDOCKER_TOPDIR)
        protect = lrepo.reposdir + "/IMAGE/TAG/PROTECT"
        self.assertEqual(mock_exists.call_args, call(protect))

    @patch.object(LocalRepository, '_unprotect')
    def test_14_unprotect_imagerepo(self, mock_unprotect):
        """Test LocalRepository().unprotected_imagerepo()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.unprotect_imagerepo("IMAGE", "TAG")
        self.assertTrue(mock_unprotect.called)

    @patch('udocker.container.localrepo.os.access')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch.object(LocalRepository, 'cd_container')
    def test_15_iswriteable_container(self, mock_cd, mock_exists,
                                      mock_isdir, mock_access):
        """Test LocalRepository().iswriteable_container()."""
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.iswriteable_container(container_id)
        self.assertEqual(status, 2)

        mock_exists.return_value = True
        mock_isdir.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.iswriteable_container(container_id)
        self.assertEqual(status, 3)

        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.iswriteable_container(container_id)
        self.assertEqual(status, 1)

        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.iswriteable_container(container_id)
        self.assertEqual(status, 0)

    # @patch.object(LocalRepository, '_name_is_valid')
    # @patch('udocker.container.localrepo.FileUtil.remove')
    # @patch('udocker.container.localrepo.os.path.exists')
    # def test_16_del_container_name(self, mock_exists, mock_remove,
    #                                mock_namevalid):
    #     """Test LocalRepository().del_container_name()."""
    #     mock_namevalid.return_value = False
    #     mock_exists.return_value = True
    #     mock_remove.return_value = True
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.del_container_name("NAMEALIAS")
    #     self.assertFalse(status)

    #     mock_namevalid.return_value = True
    #     mock_exists.return_value = False
    #     mock_remove.return_value = True
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.del_container_name("NAMEALIAS")
    #     self.assertFalse(status)

    #     mock_namevalid.return_value = True
    #     mock_exists.return_value = True
    #     mock_remove.return_value = True
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.del_container_name("NAMEALIAS")
    #     self.assertTrue(status)

    #     mock_namevalid.return_value = True
    #     mock_exists.return_value = True
    #     mock_remove.return_value = False
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.del_container_name("NAMEALIAS")
    #     self.assertFalse(status)

    @patch('udocker.container.localrepo.os.symlink')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_17__symlink(self, mock_exists, mock_symlink):
        """Test LocalRepository()._symlink()."""
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertFalse(status)

        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertTrue(status)

    @patch('udocker.container.localrepo.os.path.exists')
    @patch.object(LocalRepository, '_symlink')
    @patch.object(LocalRepository, 'cd_container')
    def test_18_set_container_name(self, mock_cd, mock_slink, mock_exists):
        """Test LocalRepository().set_container_name()."""
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.set_container_name(container_id, "WRONG[/")
        self.assertFalse(status)

        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.set_container_name(container_id, "RIGHT")
        self.assertFalse(status)

        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.set_container_name(container_id, "RIGHT")
        self.assertTrue(status)

    # @patch('udocker.container.localrepo.os.readlink')
    # @patch('udocker.container.localrepo.os.path.isdir')
    # @patch('udocker.container.localrepo.os.path.islink')
    # def test_19_get_container_id(self, mock_islink,
    #                              mock_isdir, mock_readlink):
    #     """Test LocalRepository().get_container_id()."""
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_container_id(None)
    #     self.assertEqual(status, "")

    #     mock_islink.return_value = True
    #     mock_readlink.return_value = "BASENAME"
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_container_id("ALIASNAM")
    #     self.assertEqual(status, "BASENAME")

    #     mock_islink.return_value = False
    #     mock_isdir.return_value = False
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_container_id("ALIASNAM")
    #     self.assertEqual(status, "")

    #     mock_islink.return_value = False
    #     mock_isdir.return_value = True
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_container_id("ALIASNAM")
    #     self.assertEqual(status, "ALIASNAM")

    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_20_setup_container(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_container()."""
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.setup_container("REPO", "TAG", "ID")
        self.assertEqual(status, "")

        mock_exists.return_value = False
        with patch(BOPEN, mock_open()):
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            status = lrepo.setup_container("REPO", "TAG", "ID")
            self.assertEqual(status, lrepo.containersdir + "/ID")
            self.assertEqual(lrepo.cur_containerdir,
                             lrepo.containersdir + "/ID")

    # @patch('udocker.container.localrepo.FileUtil.remove')
    # @patch('udocker.container.localrepo.os.readlink')
    # @patch('udocker.container.localrepo.os.path.islink')
    # @patch('udocker.container.localrepo.os.listdir')
    # @patch.object(LocalRepository, '_inrepository')
    # def test_21__remove_layers(self, mock_in, mock_listdir, mock_islink,
    #                            mock_readlink, mock_remove):
    #     """Test LocalRepository()._remove_layers()."""
    #     mock_listdir.return_value = []
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._remove_layers("TAG_DIR", False)
    #     self.assertTrue(status)

    #     mock_listdir.return_value = ["FILE1,", "FILE2"]
    #     mock_islink.return_value = False
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._remove_layers("TAG_DIR", False)
    #     self.assertTrue(status)

    #     mock_islink.return_value = True
    #     mock_readlink.return_value = "REALFILE"
    #     mock_remove.return_value = False
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._remove_layers("TAG_DIR", False)
    #     self.assertFalse(status)

    #     mock_remove.return_value = True
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._remove_layers("TAG_DIR", False)
    #     self.assertTrue(status)

    #     mock_remove.return_value = True
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._remove_layers("TAG_DIR", True)
    #     self.assertTrue(status)

    #     mock_remove.return_value = False
    #     mock_in.return_value = False
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._remove_layers("TAG_DIR", True)
    #     self.assertTrue(status)

    #     mock_remove.return_value = False
    #     mock_in.return_value = False
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._remove_layers("TAG_DIR", False)
    #     self.assertFalse(status)

    #     mock_remove.return_value = False
    #     mock_in.return_value = True
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._remove_layers("TAG_DIR", True)
    #     self.assertTrue(status)

    @patch('udocker.container.localrepo.FileUtil.remove')
    @patch.object(LocalRepository, 'cd_imagerepo')
    @patch.object(LocalRepository, '_remove_layers')
    def test_22_del_imagerepo(self, mock_rmlayers, mock_cd, mock_remove):
        """Test LocalRepository()._del_imagerepo()."""
        mock_cd.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertFalse(status)

        mock_cd.return_value = True
        mock_remove.return_value = True
        mock_rmlayers.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = "XXXX"
        lrepo.cur_tagdir = "XXXX"
        status = lrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertEqual(lrepo.cur_repodir, "")
        self.assertEqual(lrepo.cur_tagdir, "")
        self.assertTrue(status)

    # def _sideffect_test_23(self, arg):
    #     """Side effect for isdir on test 23 _get_tags()."""
    #     if self.iter < 3:
    #         self.iter += 1
    #         return False
    #     else:
    #         return True

    # @patch('udocker.container.localrepo.os.path.isdir')
    # @patch('udocker.container.localrepo.os.listdir')
    # @patch.object(LocalRepository, '_is_tag')
    # def test_23__get_tags(self, mock_is, mock_listdir, mock_isdir):
    #     """Test LocalRepository()._get_tags()."""
    #     mock_isdir.return_value = False
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._get_tags("CONTAINERS_DIR")
    #     self.assertEqual(status, [])

    #     mock_isdir.return_value = True
    #     mock_listdir.return_value = []
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._get_tags("CONTAINERS_DIR")
    #     self.assertEqual(status, [])

    #     mock_isdir.return_value = True
    #     mock_listdir.return_value = ["FILE1", "FILE2"]
    #     mock_is.return_value = False
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._get_tags("CONTAINERS_DIR")
    #     self.assertEqual(status, [])

    #     mock_isdir.return_value = True
    #     mock_listdir.return_value = ["FILE1", "FILE2"]
    #     mock_is.return_value = True
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._get_tags("CONTAINERS_DIR")
    #     expected_status = [('CONTAINERS_DIR', 'FILE1'),
    #                        ('CONTAINERS_DIR', 'FILE2')]
    #     self.assertEqual(status, expected_status)

    #     mock_isdir.return_value = True
    #     mock_listdir.return_value = ["FILE1", "FILE2"]
    #     mock_is.return_value = False
    #     self.iter = 0
    #     mock_isdir.side_effect = self._sideffect_test_23
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo._get_tags("CONTAINERS_DIR")
    #     expected_status = [('CONTAINERS_DIR', 'FILE1'),
    #                        ('CONTAINERS_DIR', 'FILE2')]
    #     self.assertEqual(self.iter, 2)
    #     self.assertEqual(status, [])

    @patch('udocker.container.localrepo.FileUtil.remove')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.FileUtil')
    def test_24_add_image_layer(self, mock_futil, mock_exists,
                                mock_islink, mock_remove):
        """Test LocalRepository().add_image_layer()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = ""
        lrepo.cur_tagdir = ""
        status = lrepo.add_image_layer("FILE")
        self.assertFalse(status)

        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = "IMAGE"
        lrepo.cur_tagdir = "TAG"
        status = lrepo.add_image_layer("FILE")
        self.assertTrue(status)

        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.add_image_layer("FILE")
        self.assertFalse(status)

        mock_exists.return_value = True
        mock_islink.return_value = True
        mock_remove.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.add_image_layer("FILE")
        self.assertTrue(mock_futil.called)
        # self.assertTrue(status)

        mock_exists.return_value = True
        mock_islink.return_value = False
        mock_futil.reset_mock()
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.add_image_layer("FILE")
        # self.assertFalse(mock_futil.called)
        # self.assertTrue(status)

    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_25_setup_imagerepo(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_imagerepo()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.setup_imagerepo("")
        self.assertFalse(status)

        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.setup_imagerepo("IMAGE")
        expected_directory = lrepo.reposdir + "/IMAGE"
        self.assertEqual(lrepo.cur_repodir, expected_directory)
        self.assertFalse(status)

        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.setup_imagerepo("IMAGE")
        expected_directory = lrepo.reposdir + "/IMAGE"
        self.assertTrue(mock_makedirs.called)
        self.assertEqual(lrepo.cur_repodir, expected_directory)
        self.assertTrue(status)

    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_26_setup_tag(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_tag()."""
        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        with patch(BOPEN, mock_open()) as mopen:
            status = lrepo.setup_tag("NEWTAG")
            self.assertTrue(mock_makedirs.called)
            expected_directory = lrepo.reposdir + "/IMAGE/NEWTAG"
            self.assertEqual(lrepo.cur_tagdir, expected_directory)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_27_set_version(self, mock_exists, mock_makedirs, mock_listdir):
        """Test LocalRepository().set_version()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.set_version("v1")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)

        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
        status = lrepo.set_version("v1")
        self.assertFalse(mock_listdir.called)
        self.assertFalse(status)

        mock_exists.return_value = True
        with patch(BOPEN, mock_open()) as mopen:
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            status = lrepo.set_version("v1")
            # self.assertTrue(mock_listdir.called)
            # self.assertTrue(mopen.called)
            # self.assertTrue(status)

    # @patch.object(LocalRepository, 'save_json')
    # @patch.object(LocalRepository, 'load_json')
    # @patch('udocker.container.localrepo.os.path.exists')
    # def test_28_get_image_attributes(self, mock_exists, mock_loadjson,
    #                                  mock_savejson):
    #     """Test LocalRepository().get_image_attributes()."""
    #     mock_exists.return_value = True
    #     mock_loadjson.return_value = None
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_image_attributes()
    #     self.assertEqual((None, None), status)

    #     mock_exists.side_effect = [True, False]
    #     mock_loadjson.side_effect = [("foolayername",), ]
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_image_attributes()
    #     self.assertEqual((None, None), status)

    #     mock_exists.side_effect = [True, True, False]
    #     mock_loadjson.side_effect = [("foolayername",), "foojson"]
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_image_attributes()
    #     self.assertEqual((None, None), status)

    #     mock_exists.side_effect = [True, True, True]
    #     mock_loadjson.side_effect = [("foolayername",), "foojson"]
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_image_attributes()
    #     self.assertEqual(('foojson', ['/foolayername.layer']), status)

    #     mock_exists.side_effect = [False, True]
    #     mock_loadjson.side_effect = [None, ]
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_image_attributes()
    #     self.assertEqual((None, None), status)

    #     mock_exists.side_effect = [False, True, False]
    #     manifest = {
    #         "fsLayers": ({"blobSum": "foolayername"},),
    #         "history": ({"v1Compatibility": '["foojsonstring"]'},)
    #     }
    #     mock_loadjson.side_effect = [manifest, ]
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_image_attributes()
    #     self.assertEqual((None, None), status)

    #     mock_exists.side_effect = [False, True, True]
    #     mock_loadjson.side_effect = [manifest, ]
    #     lrepo = LocalRepository(UDOCKER_TOPDIR)
    #     status = lrepo.get_image_attributes()
    #     self.assertEqual(([u'foojsonstring'], ['/foolayername']), status)

    @patch('udocker.container.localrepo.json.dump')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_29_save_json(self, mock_exists, mock_jsondump):
        """Test LocalRepository().save_json()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.save_json("filename", "data")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)

        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
        status = lrepo.save_json("filename", "data")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)

        mock_exists.reset_mock()
        with patch(BOPEN, mock_open()) as mopen:
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            status = lrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertTrue(status)

        mock_exists.reset_mock()
        with patch(BOPEN, mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            status = lrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @patch('udocker.container.localrepo.json.load')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_30_load_json(self, mock_exists, mock_jsonload):
        """Test LocalRepository().load_json()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.load_json("filename")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)

        mock_exists.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.cur_repodir = lrepo.reposdir + "/IMAGE"
        lrepo.cur_tagdir = lrepo.cur_repodir + "/TAG"
        status = lrepo.load_json("filename")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)

        mock_exists.reset_mock()
        with patch(BOPEN, mock_open()) as mopen:
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            status = lrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertTrue(status)

        mock_exists.reset_mock()
        with patch(BOPEN, mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            lrepo = LocalRepository(UDOCKER_TOPDIR)
            status = lrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @patch('udocker.container.localrepo.FileUtil')
    def test_31__protect(self, mock_futil):
        """Test LocalRepository()._protect().

        Set the protection mark in a container or image tag
        """
        mock_futil.return_value.isdir.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._protect
        self.assertTrue(status)

    @patch('udocker.container.localrepo.FileUtil.remove')
    def test_32__unprotect(self, mock_rm):
        """Test LocalRepository()._unprotect().
        Remove protection mark from container or image tag.
        """
        mock_rm.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._unprotect("dir")
        self.assertTrue(mock_rm.called)
        self.assertTrue(status)

    @patch('udocker.container.localrepo.FileUtil')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_33__isprotected(self, mock_exists, mock_futil):
        """Test LocalRepository()._isprotected().
        See if container or image tag are protected.
        """
        mock_futil.return_value.isdir.return_value = True
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._isprotected("dir")
        self.assertTrue(status)

    @patch.object(LocalRepository, 'cd_container')
    @patch.object(LocalRepository, 'get_containers_list')
    def test_34_del_container(self, mock_cdcont, mock_getcl):
        """Test LocalRepository().del_container()."""
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.del_container(container_id)
        self.assertTrue(mock_cdcont.called)
        self.assertFalse(status)

        mock_cdcont.return_value = ""
        mock_getcl.return_value = "tmp"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.del_container(container_id)
        self.assertFalse(status)

        mock_cdcont.return_value = "/tmp"
        mock_getcl.return_value = "/tmp"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo.del_container(container_id)
        # self.assertTrue(status)

    def test_35__relpath(self):
        """Test LocalRepository()._relpath()."""
        pass

    def test_36__name_is_valid(self):
        """Test LocalRepository()._name_is_valid().
        Check name alias validity.
        """
        name = "lzskjghdlak"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertTrue(status)

        name = "lzskjghd/lak"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

        name = ".lzsklak"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "]lzsklak"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "lzs[klak"
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "lzs klak"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "x" * 2049
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._name_is_valid(name)
        self.assertFalse(status)

    @patch('udocker.container.localrepo.FileUtil')
    @patch('udocker.container.localrepo.os.path.isfile')
    def test_37__is_tag(self, mock_isfile, mock_futil):
        """Test LocalRepository()._is_tag().
        Does this directory contain an image tag ?
        An image TAG indicates that this repo directory
        contains references to layers and metadata from
        which we can extract a container.
        """
        mock_isfile.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._is_tag("tagdir")
        self.assertTrue(status)

        mock_isfile.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._is_tag("tagdir")
        self.assertFalse(status)

    @patch('udocker.container.localrepo.os.path.exists')
    def test_38_cd_imagerepo(self, mock_exists):
        """Test LocalRepository().cd_imagerepo()."""
        Config().conf['reposdir'] = "/tmp"
        mock_exists.return_value = True
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.setup("YYYY")
        out = lrepo.cd_imagerepo("IMAGE", "TAG")
        # self.assertNotEqual(out, "")

    @patch('udocker.container.localrepo.FileUtil')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.listdir')
    def test_39__find(self, mock_listdir, mock_isdir, mock_islink, mock_futil):
        """Test LocalRepository()._find().
        is a specific layer filename referenced by another image TAG
        """
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["file"]
        mock_islink.return_value = True
        filename = "file"
        folder = "/tmp"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        out = lrepo._find(filename, folder)
        self.assertEqual(out, ["/tmp/file"])

        mock_islink.return_value = False
        mock_isdir.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        out = lrepo._find(filename, folder)
        self.assertEqual(out, [])

    @patch('udocker.container.localrepo.FileUtil')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.listdir')
    def test_40__inrepository(self, mock_listdir,
                              mock_isdir, mock_islink, mock_futil):
        """Test LocalRepository()._inrepository().
        Check if a given file is in the repository.
        """
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["file"]
        mock_islink.return_value = True
        filename = "file"
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.reposdir = "/tmp"
        out = lrepo._inrepository(filename)
        self.assertEqual(out, ["/tmp/file"])

        mock_islink.return_value = False
        mock_isdir.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        out = lrepo._inrepository(filename)
        self.assertEqual(out, [])

    @patch('udocker.container.localrepo.FileUtil.remove')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.readlink')
    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.os.path.realpath')
    def test_41__remove_layers(self, mock_realpath, mock_listdir,
                               mock_readlink, mock_islink, mock_remove):
        """Test LocalRepository()._remove_layers().
        Remove link to image layer and corresponding layer
        if not being used by other images.
        """
        mock_realpath.return_value = "/tmp"
        mock_listdir.return_value = "file"
        mock_islink.return_value = True
        mock_readlink.return_value = "file"
        tag_dir = "TAGDIR"
        mock_remove.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.reposdir = "/tmp"
        status = lrepo._remove_layers(tag_dir, True)
        self.assertTrue(status)

        mock_remove.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        status = lrepo._remove_layers(tag_dir, False)
        # (FIXME lalves): This is not OK, it should be False. Review this test.
        self.assertFalse(status)

    @patch.object(LocalRepository, '_get_tags')
    def test_42_get_imagerepos(self, mock_gtags):
        """Test LocalRepository().get_imagerepos()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.get_imagerepos()
        self.assertTrue(mock_gtags.called)

    @patch.object(LocalRepository, 'cd_container')
    def test_43_get_layers(self, mock_cd):
        """Test LocalRepository().get_layers()."""
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.get_layers("IMAGE", "TAG")
        # self.assertTrue(mock_cd.called)

    @patch('udocker.container.localrepo.os.path.isdir')
    @patch.object(LocalRepository, 'load_json')
    @patch('udocker.container.localrepo.os.listdir')
    def test_44__load_structure(self, mock_listdir, mock_json, mock_isdir):
        """Test LocalRepository()._load_structure().
        Scan the repository structure of a given image tag.
        """
        mock_isdir.return_value = False
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        structure = lrepo._load_structure("IMAGETAGDIR")
        # self.assertTrue(structure["layers"])

        mock_isdir.return_value = True
        mock_listdir.return_value = ["ancestry"]
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.return_value = "JSON"
        structure = lrepo._load_structure("IMAGETAGDIR")
        # WIP
        # self.assertTrue("JSON" in structure["ancestry"])

    def test_45__find_top_layer_id(self):
        """Test LocalRepository()._find_top_layer_id"""
        pass

    def test_46__sorted_layers(self):
        """Test LocalRepository()._sorted_layers"""
        pass

    def test_47__verify_layer_file(self):
        """Test LocalRepository()._verify_layer_file"""
        pass

    @patch('udocker.container.localrepo.Msg')
    @patch.object(LocalRepository, '_load_structure')
    def test_48_verify_image(self, mock_lstruct, mock_msg):
        """Test LocalRepository().verify_image()."""
        mock_msg.level = 0
        lrepo = LocalRepository(UDOCKER_TOPDIR)
        lrepo.verify_image()
        self.assertTrue(mock_lstruct.called)


if __name__ == '__main__':
    main()
