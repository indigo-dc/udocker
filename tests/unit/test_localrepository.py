#!/usr/bin/env python
"""
udocker unit tests: LocalRepository
"""
import sys
import os
import subprocess
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open, call
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open, call

sys.path.append('.')

from udocker.container.localrepo import LocalRepository
from udocker.config import Config

UDOCKER_TOPDIR = "test_topdir"
if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


class LocalRepositoryTestCase(TestCase):
    """Test LocalRepositoryTestCase().

    Management of local repository of container
    images and extracted containers
    Tests not yet implemented:
    _load_structure
    _find_top_layer_id
    _sorted_layers
    verify_image
    """

    def setUp(self):
        self.conf = Config().getconf()
        self.conf['tmpdir'] = "/tmp"
        self.conf['homedir'] = "/tmp"
        self.conf['bindir'] = ""
        self.conf['libdir'] = ""
        self.conf['reposdir'] = ""
        self.conf['layersdir'] = ""
        self.conf['containersdir'] = ""
        self.localrepo = LocalRepository(self.conf)

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test LocalRepository() constructor."""
        self.assertTrue(self.localrepo.topdir)
        self.assertTrue(self.localrepo.reposdir)
        self.assertTrue(self.localrepo.layersdir)
        self.assertTrue(self.localrepo.containersdir)
        self.assertTrue(self.localrepo.bindir)
        self.assertTrue(self.localrepo.libdir)
        self.assertTrue(self.localrepo.homedir)
        self.assertEqual(self.localrepo.cur_repodir, "")
        self.assertEqual(self.localrepo.cur_tagdir, "")
        self.assertEqual(self.localrepo.cur_containerdir, "")

    def test_02_setup(self):
        """Test LocalRepository().setup()."""
        self.conf['topdir'] = UDOCKER_TOPDIR
        self.assertEqual(os.path.basename(self.localrepo.topdir), UDOCKER_TOPDIR)
        self.localrepo.setup("YYYY")
        self.assertEqual(os.path.basename(self.localrepo.topdir), "YYYY")

    def test_03_create_repo(self):
        """Test LocalRepository().create_repo()."""
        subprocess.call(["/bin/rm", "-Rf", self.localrepo.topdir])
        self.assertFalse(os.path.exists(self.localrepo.topdir))
        self.localrepo.create_repo()
        self.assertTrue(os.path.exists(self.localrepo.topdir))
        self.assertTrue(os.path.exists(self.localrepo.reposdir))
        self.assertTrue(os.path.exists(self.localrepo.layersdir))
        self.assertTrue(os.path.exists(self.localrepo.containersdir))
        self.assertTrue(os.path.exists(self.localrepo.bindir))
        self.assertTrue(os.path.exists(self.localrepo.libdir))
        subprocess.call(["/bin/rm", "-Rf", self.localrepo.topdir])

    def test_04_is_repo(self):
        """Test LocalRepository().is_repo()."""
        subprocess.call(["/bin/rm", "-Rf", self.localrepo.topdir])
        self.localrepo.create_repo()
        self.assertTrue(self.localrepo.is_repo())
        subprocess.call(["/bin/rm", "-Rf", self.localrepo.topdir])

    def test_05_is_container_id(self):
        """Test LocalRepository().is_container_id."""
        self.assertTrue(self.localrepo.is_container_id(
            "10860ac1-6962-3a9b-a5f8-63bcfb67ce39"))
        self.assertFalse(self.localrepo.is_container_id(
            "10860ac1-6962-3a9b-a5f863bcfb67ce37"))
        self.assertFalse(self.localrepo.is_container_id(
            "10860ac1-6962--3a9b-a5f863bcfb67ce37"))
        self.assertFalse(self.localrepo.is_container_id(
            "-6962--3a9b-a5f863bcfb67ce37"))
        self.assertFalse(self.localrepo.is_container_id(
            12345678))

    def test_06_get_container_name(self):
        """Test LocalRepository().get_container_name()."""
        mock_isdir = patch('udocker.container.localrepo.os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = patch('udocker.container.localrepo.os.listdir').start()
        mock_listdir.return_value = ['LINK']
        mock_islink = patch('udocker.container.localrepo.os.path.islink').start()
        mock_islink.return_value = True
        mock_readlink = patch('udocker.container.localrepo.os.readlink').start()
        mock_readlink.return_value = "/a/b/IMAGE:TAG"
        name_list = self.localrepo.get_container_name("IMAGE:TAG")
        self.assertEqual(name_list, ["LINK"])

    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.listdir')
    def test_07a_get_containers_list(self, mock_isdir, mock_listdir):
        """Test LocalRepository().get_containers_list() - 01."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ['LINK']
        with patch(BUILTINS + '.open', mock_open(read_data='REPONAME')):
            containers_list = self.localrepo.get_containers_list()
            self.assertEqual(os.path.basename(containers_list[0]), "LINK")

    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch.object(LocalRepository, 'get_container_name')
    def test_07b_get_containers_list(self, mock_getname, mock_isdir,
                                     mock_listdir, mock_islink):
        """Test LocalRepository().get_containers_list() - 02."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ['LINK']
        mock_islink.return_value = False
        mock_getname.return_value = ["NAME1", "NAME2"]
        with patch(BUILTINS + '.open', mock_open(read_data='REPONAME')):
            containers_list = self.localrepo.get_containers_list(False)
            self.assertEqual(os.path.basename(containers_list[0][1]),
                             "REPONAME")

    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository.get_containers_list')
    def test_08_cd_container(self, mock_getlist, mock_exists):
        """Test LocalRepository().cd_container()."""
        mock_exists.return_value = True
        mock_getlist.return_value = [self.localrepo.containersdir +
                                     "/CONTAINERNAME"]
        container_path = self.localrepo.cd_container("CONTAINERNAME")
        self.assertEqual(container_path, mock_getlist.return_value[0])

    def test_09_protect_container(self):
        """Test LocalRepository().protect_container()."""
        with patch(BUILTINS + '.open', mock_open()) as mopen:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            self.localrepo.protect_container(container_id)
            self.assertTrue(mopen.called)
            self.assertEqual(mopen.call_args, call('/PROTECT', 'w'))

    def test_10_isprotected_container(self):
        """Test LocalRepository().isprotected_container()."""
        with patch('udocker.container.localrepo.os.path.exists') as mexists:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            self.localrepo.isprotected_container(container_id)
            self.assertTrue(mexists.called)
            self.assertEqual(mexists.call_args, call('/PROTECT'))

    @patch('udocker.container.localrepo.LocalRepository.cd_container')
    @patch('udocker.container.localrepo.LocalRepository._unprotect')
    def test_11_unprotect_container(self, mock_unprotect, mock_cdcont):
        """Test LocalRepository().isprotected_container()."""
        mock_cdcont.return_value = "/tmp"
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        self.localrepo.unprotect_container(container_id)
        self.assertTrue(mock_unprotect.called)

    def test_12_protect_imagerepo(self):
        """Test LocalRepository().protect_imagerepo()."""
        with patch(BUILTINS + '.open', mock_open()) as mopen:
            self.localrepo.protect_imagerepo("IMAGE", "TAG")
            self.assertTrue(mopen.called)
            protect = self.localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mopen.call_args, call(protect, 'w'))

    def test_13_isprotected_imagerepo(self):
        """Test LocalRepository().isprotected_imagerepo()."""
        with patch('os.path.exists') as mexists:
            self.localrepo.isprotected_imagerepo("IMAGE", "TAG")
            self.assertTrue(mexists.called)
            protect = self.localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mexists.call_args, call(protect))

    @patch('udocker.container.localrepo.LocalRepository._unprotect')
    def test_14_unprotect_imagerepo(self, mock_unprotect):
        """Test LocalRepository().unprotected_imagerepo()."""
        self.localrepo.unprotect_imagerepo("IMAGE", "TAG")
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
        status = self.localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 2)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = False
        status = self.localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 3)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = True
        status = self.localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 1)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = False
        status = self.localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 0)

    @patch('udocker.container.localrepo.LocalRepository._name_is_valid')
    @patch('udocker.utils.fileutil.FileUtil.remove')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_16_del_container_name(self, mock_exists, mock_remove,
                                   mock_namevalid):
        """Test LocalRepository().del_container_name()."""
        mock_namevalid.return_value = False
        mock_exists.return_value = True
        mock_remove.return_value = True
        status = self.localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)
        #
        mock_namevalid.return_value = True
        mock_exists.return_value = False
        mock_remove.return_value = True
        status = self.localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)
        #
        mock_namevalid.return_value = True
        mock_exists.return_value = True
        mock_remove.return_value = True
        status = self.localrepo.del_container_name("NAMEALIAS")
        self.assertTrue(status)
        #
        mock_namevalid.return_value = True
        mock_exists.return_value = True
        mock_remove.return_value = False
        status = self.localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)

    @patch('udocker.container.localrepo.os.symlink')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_17__symlink(self, mock_exists, mock_symlink):
        """Test LocalRepository()._symlink()."""
        mock_exists.return_value = True
        status = self.localrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = False
        status = self.localrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertTrue(status)

    @patch('udocker.container.localrepo.os.path.exists')
    @patch.object(LocalRepository, '_symlink')
    @patch.object(LocalRepository, 'cd_container')
    def test_18_set_container_name(self, mock_cd, mock_slink, mock_exists):
        """Test LocalRepository().set_container_name()."""
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        status = self.localrepo.set_container_name(container_id, "WRONG[/")
        self.assertFalse(status)
        #
        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = True
        status = self.localrepo.set_container_name(container_id, "RIGHT")
        self.assertFalse(status)
        #
        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = False
        status = self.localrepo.set_container_name(container_id, "RIGHT")
        self.assertTrue(status)

    @patch('udocker.container.localrepo.os.readlink')
    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.path.islink')
    def test_19_get_container_id(self, mock_islink,
                                 mock_isdir, mock_readlink):
        """Test LocalRepository().get_container_id()."""
        status = self.localrepo.get_container_id(None)
        self.assertEqual(status, "")
        #
        mock_islink.return_value = True
        mock_readlink.return_value = "BASENAME"
        status = self.localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "BASENAME")
        #
        mock_islink.return_value = False
        mock_isdir.return_value = False
        status = self.localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "")
        #
        mock_islink.return_value = False
        mock_isdir.return_value = True
        status = self.localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "ALIASNAM")

    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_20_setup_container(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_container()."""
        mock_exists.return_value = True
        status = self.localrepo.setup_container("REPO", "TAG", "ID")
        self.assertEqual(status, "")
        #
        mock_exists.return_value = False
        with patch(BUILTINS + '.open', mock_open()):
            status = self.localrepo.setup_container("REPO", "TAG", "ID")
            self.assertEqual(status, self.localrepo.containersdir + "/ID")
            self.assertEqual(self.localrepo.cur_containerdir,
                             self.localrepo.containersdir + "/ID")

    @patch('udocker.utils.fileutil.FileUtil.remove')
    @patch('udocker.container.localrepo.os.readlink')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.listdir')
    @patch.object(LocalRepository, '_inrepository')
    def test_21__remove_layers(self, mock_in, mock_listdir, mock_islink,
                               mock_readlink, mock_remove):
        """Test LocalRepository()._remove_layers()."""
        mock_listdir.return_value = []
        status = self.localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        mock_listdir.return_value = ["FILE1,", "FILE2"]
        mock_islink.return_value = False
        status = self.localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        mock_islink.return_value = True
        mock_readlink.return_value = "REALFILE"
        mock_remove.return_value = False
        status = self.localrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)
        #
        mock_remove.return_value = True
        status = self.localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        mock_remove.return_value = True
        status = self.localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)
        #
        mock_remove.return_value = False
        mock_in.return_value = False
        status = self.localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)
        #
        mock_remove.return_value = False
        mock_in.return_value = False
        status = self.localrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)
        #
        mock_remove.return_value = False
        mock_in.return_value = True
        status = self.localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)

    @patch('udocker.utils.fileutil.FileUtil.remove')
    @patch.object(LocalRepository, 'cd_imagerepo')
    def test_22_del_imagerepo(self, mock_cd, mock_remove):
        """Test LocalRepository()._del_imagerepo()."""
        mock_cd.return_value = False
        status = self.localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertFalse(status)
        #
        mock_cd.return_value = True
        status = self.localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertTrue(status)
        #
        self.localrepo.cur_repodir = "XXXX"
        self.localrepo.cur_tagdir = "XXXX"
        mock_remove.return_value = True
        status = self.localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertEqual(self.localrepo.cur_repodir, "")
        self.assertEqual(self.localrepo.cur_tagdir, "")
        self.assertTrue(status)

    def _sideffect_test_23(self, arg):
        """Side effect for isdir on test 23 _get_tags()."""
        if self.iter < 3:
            self.iter += 1
            return False
        else:
            return True

    @patch('udocker.container.localrepo.os.path.isdir')
    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.utils.fileutil.FileUtil.isdir')
    @patch.object(LocalRepository, '_is_tag')
    def test_23__get_tags(self, mock_is, mock_futilisdir,
                          mock_listdir, mock_isdir):
        """Test LocalRepository()._get_tags()."""
        mock_futilisdir.return_value = False
        status = self.localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futilisdir.return_value = True
        mock_listdir.return_value = []
        status = self.localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futilisdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        mock_isdir.return_value = False
        status = self.localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futilisdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = True
        status = self.localrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(status, expected_status)
        #
        mock_futilisdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        self.iter = 0
        mock_isdir.side_effect = self._sideffect_test_23
        status = self.localrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(self.iter, 2)
        self.assertEqual(status, [])

    @patch('udocker.utils.fileutil.FileUtil.remove')
    @patch('udocker.container.localrepo.os.path.islink')
    @patch('udocker.container.localrepo.os.path.exists')
    @patch('udocker.utils.fileutil.FileUtil')
    def test_24_add_image_layer(self, mock_futil, mock_exists,
                                mock_islink, mock_remove):
        """Test LocalRepository().add_image_layer()."""
        self.localrepo.cur_repodir = ""
        self.localrepo.cur_tagdir = ""
        status = self.localrepo.add_image_layer("FILE")
        self.assertFalse(status)
        #
        self.localrepo.cur_repodir = "IMAGE"
        self.localrepo.cur_tagdir = "TAG"
        status = self.localrepo.add_image_layer("FILE")
        self.assertTrue(status)
        #
        mock_exists.return_value = False
        status = self.localrepo.add_image_layer("FILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        mock_islink.return_value = True
        status = self.localrepo.add_image_layer("FILE")
        mock_remove.return_value = True
        self.assertTrue(mock_futil.called)
        self.assertTrue(status)
        #
        mock_exists.return_value = True
        mock_islink.return_value = False
        mock_futil.reset_mock()
        status = self.localrepo.add_image_layer("FILE")
        self.assertFalse(mock_futil.called)
        self.assertTrue(status)

    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_25_setup_imagerepo(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_imagerepo()."""
        status = self.localrepo.setup_imagerepo("")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        status = self.localrepo.setup_imagerepo("IMAGE")
        expected_directory = self.localrepo.reposdir + "/IMAGE"
        self.assertEqual(self.localrepo.cur_repodir, expected_directory)
        self.assertFalse(status)
        #
        mock_exists.return_value = False
        status = self.localrepo.setup_imagerepo("IMAGE")
        expected_directory = self.localrepo.reposdir + "/IMAGE"
        self.assertTrue(mock_makedirs.called)
        self.assertEqual(self.localrepo.cur_repodir, expected_directory)
        self.assertTrue(status)

    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_26_setup_tag(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_tag()."""
        mock_exists.return_value = False
        self.localrepo.cur_repodir = self.localrepo.reposdir + "/IMAGE"
        with patch(BUILTINS + '.open', mock_open()) as mopen:
            status = self.localrepo.setup_tag("NEWTAG")
            self.assertTrue(mock_makedirs.called)
            expected_directory = self.localrepo.reposdir + "/IMAGE/NEWTAG"
            self.assertEqual(self.localrepo.cur_tagdir, expected_directory)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @patch('udocker.container.localrepo.os.listdir')
    @patch('udocker.container.localrepo.os.makedirs')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_27_set_version(self, mock_exists, mock_makedirs, mock_listdir):
        """Test LocalRepository().set_version()."""
        status = self.localrepo.set_version("v1")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        self.localrepo.cur_repodir = self.localrepo.reposdir + "/IMAGE"
        self.localrepo.cur_tagdir = self.localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = self.localrepo.set_version("v1")
        self.assertFalse(mock_listdir.called)
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        with patch(BUILTINS + '.open', mock_open()) as mopen:
            status = self.localrepo.set_version("v1")
            self.assertTrue(mock_listdir.called)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @patch.object(LocalRepository, 'save_json')
    @patch.object(LocalRepository, 'load_json')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_28_get_image_attributes(self, mock_exists, mock_loadjson,
                                     mock_savejson):
        """Test LocalRepository().get_image_attributes()."""
        mock_exists.return_value = True
        mock_loadjson.return_value = None
        status = self.localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, False]
        mock_loadjson.side_effect = [("foolayername",), ]
        status = self.localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, True, False]
        mock_loadjson.side_effect = [("foolayername",), "foojson"]
        status = self.localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, True, True]
        mock_loadjson.side_effect = [("foolayername",), "foojson"]
        status = self.localrepo.get_image_attributes()
        self.assertEqual(('foojson', ['/foolayername.layer']), status)
        #
        mock_exists.side_effect = [False, True]
        mock_loadjson.side_effect = [None, ]
        status = self.localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [False, True, False]
        manifest = {
            "fsLayers": ({"blobSum": "foolayername"},),
            "history": ({"v1Compatibility": '["foojsonstring"]'},)
        }
        mock_loadjson.side_effect = [manifest, ]
        status = self.localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [False, True, True]
        mock_loadjson.side_effect = [manifest, ]
        status = self.localrepo.get_image_attributes()
        self.assertEqual(([u'foojsonstring'], ['/foolayername']), status)

    @patch('udocker.container.localrepo.json.dump')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_29_save_json(self, mock_exists, mock_jsondump):
        """Test LocalRepository().save_json()."""
        status = self.localrepo.save_json("filename", "data")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        self.localrepo.cur_repodir = self.localrepo.reposdir + "/IMAGE"
        self.localrepo.cur_tagdir = self.localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = self.localrepo.save_json("filename", "data")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)
        #
        mock_exists.reset_mock()
        with patch(BUILTINS + '.open', mock_open()) as mopen:
            status = self.localrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertTrue(status)
        #
        mock_exists.reset_mock()
        with patch(BUILTINS + '.open', mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            status = self.localrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @patch('udocker.container.localrepo.json.load')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_30_load_json(self, mock_exists, mock_jsonload):
        """Test LocalRepository().load_json()."""
        status = self.localrepo.load_json("filename")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        self.localrepo.cur_repodir = self.localrepo.reposdir + "/IMAGE"
        self.localrepo.cur_tagdir = self.localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = self.localrepo.load_json("filename")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)
        #
        mock_exists.reset_mock()
        with patch(BUILTINS + '.open', mock_open()) as mopen:
            status = self.localrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertTrue(status)
        #
        mock_exists.reset_mock()
        with patch(BUILTINS + '.open', mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            status = self.localrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @patch('udocker.utils.fileutil.FileUtil')
    def test_31__protect(self, mock_futil):
        """Test LocalRepository()._protect().

        Set the protection mark in a container or image tag
        """
        mock_futil.return_value.isdir.return_value = True
        status = self.localrepo._protect
        self.assertTrue(status)

    @patch('udocker.utils.fileutil.FileUtil.isdir')
    def test_32__unprotect(self, mock_futilisdir):
        """Test LocalRepository()._unprotect().
        Remove protection mark from container or image tag.
        """
        mock_futilisdir.return_value = True
        status = self.localrepo._unprotect("dir")
        self.assertTrue(status)

    @patch('udocker.utils.fileutil.FileUtil')
    @patch('udocker.container.localrepo.os.path.exists')
    def test_33__isprotected(self, mock_exists, mock_futil):
        """Test LocalRepository()._isprotected().
        See if container or image tag are protected.
        """
        mock_futil.return_value.isdir.return_value = True
        mock_exists.return_value = True
        status = self.localrepo._isprotected("dir")
        self.assertTrue(status)

    @patch.object(LocalRepository, 'cd_container')
    @patch.object(LocalRepository, 'get_containers_list')
    def test_34_del_container(self, mock_cdcont, mock_getcl):
        """Test LocalRepository().del_container()."""
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        status = self.localrepo.del_container(container_id)
        self.assertTrue(mock_cdcont.called)
        self.assertFalse(status)

        mock_cdcont.return_value = ""
        mock_getcl.return_value = "tmp"
        status = self.localrepo.del_container(container_id)
        self.assertFalse(status)

        mock_cdcont.return_value = "/tmp"
        mock_getcl.return_value = "/tmp"
        status = self.localrepo.del_container(container_id)
        self.assertTrue(status)

    def test_35__relpath(self):
        """Test LocalRepository()._relpath()."""
        pass

    def test_36__name_is_valid(self):
        """Test LocalRepository()._name_is_valid().
        Check name alias validity.
        """
        name = "lzskjghdlak"
        status = self.localrepo._name_is_valid(name)
        self.assertTrue(status)

        name = "lzskjghd/lak"
        status = self.localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = ".lzsklak"
        status = self.localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "]lzsklak"
        status = self.localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "lzs[klak"
        status = self.localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "lzs klak"
        status = self.localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "x" * 2049
        status = self.localrepo._name_is_valid(name)
        self.assertFalse(status)

    @patch('udocker.utils.fileutil.FileUtil')
    @patch('udocker.container.localrepo.os.path.isfile')
    def test_37__is_tag(self, mock_isfile, mock_futil):
        """Test LocalRepository()._is_tag().
        Does this directory contain an image tag ?
        An image TAG indicates that this repo directory
        contains references to layers and metadata from
        which we can extract a container.
        """
        mock_isfile.return_value = True
        status = self.localrepo._is_tag("tagdir")
        self.assertTrue(status)

        mock_isfile.return_value = False
        status = self.localrepo._is_tag("tagdir")
        self.assertFalse(status)

    @patch('udocker.container.localrepo.LocalRepository')
    def test_38_cd_imagerepo(self, mock_local):
        """Test LocalRepository().cd_imagerepo()."""
        self.localrepo.reposdir = "/tmp"
        out = self.localrepo.cd_imagerepo("IMAGE", "TAG")
        self.assertNotEqual(out, "")

    @patch('udocker.utils.fileutil.FileUtil')
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

        out = self.localrepo._find(filename, folder)
        self.assertEqual(out, ["/tmp/file"])

        mock_islink.return_value = False
        mock_isdir.return_value = False

        out = self.localrepo._find(filename, folder)
        self.assertEqual(out, [])

    @patch('udocker.utils.fileutil.FileUtil')
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
        self.localrepo.reposdir = "/tmp"
        filename = "file"

        out = self.localrepo._inrepository(filename)
        self.assertEqual(out, ["/tmp/file"])

        mock_islink.return_value = False
        mock_isdir.return_value = False

        out = self.localrepo._inrepository(filename)
        self.assertEqual(out, [])

    @patch('udocker.utils.fileutil.FileUtil.remove')
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
        self.localrepo.reposdir = "/tmp"
        mock_realpath.return_value = "/tmp"
        mock_listdir.return_value = "file"
        mock_islink.return_value = True
        mock_readlink.return_value = "file"
        tag_dir = "TAGDIR"

        mock_remove.return_value = False
        status = self.localrepo._remove_layers(tag_dir, True)
        self.assertTrue(status)

        mock_remove.return_value = False
        status = self.localrepo._remove_layers(tag_dir, False)
        # (FIXME lalves): This is not OK, it should be False. Review this test.
        self.assertTrue(status)

    @patch.object(LocalRepository, '_get_tags')
    def test_42_get_imagerepos(self, mock_gtags):
        """Test LocalRepository().get_imagerepos()."""
        self.localrepo.get_imagerepos()
        self.assertTrue(mock_gtags.called)

    @patch.object(LocalRepository, 'cd_container')
    def test_43_get_layers(self, mock_cd):
        """Test LocalRepository().get_layers()."""
        self.localrepo.get_layers("IMAGE", "TAG")
        self.assertTrue(mock_cd.called)

    @patch('udocker.utils.fileutil.FileUtil.isdir')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.container.localrepo.LocalRepository.load_json')
    @patch('udocker.container.localrepo.os.listdir')
    def test_44__load_structure(self, mock_listdir, mock_json,
                                mock_local, mock_isdir):
        """Test LocalRepository()._load_structure().
        Scan the repository structure of a given image tag.
        """
        mock_isdir.return_value = False
        structure = self.localrepo._load_structure("IMAGETAGDIR")
        self.assertTrue(structure["layers"])

        mock_isdir.return_value = True
        mock_listdir.return_value = ["ancestry"]
        self.localrepo.return_value = "JSON"
        structure = self.localrepo._load_structure("IMAGETAGDIR")
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

    @patch('udocker.msg.Msg.level')
    @patch.object(LocalRepository, '_load_structure')
    def test_48_verify_image(self, mock_lstruct, mock_level):
        """Test LocalRepository().verify_image()."""
        mock_level.return_value = 0
        self.localrepo.verify_image()
        self.assertTrue(mock_lstruct.called)


if __name__ == '__main__':
    main()
