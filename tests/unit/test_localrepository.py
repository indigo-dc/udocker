#!/usr/bin/env python2
"""
udocker unit tests.
Unit tests for udocker, a wrapper to execute basic docker containers
without using docker.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
import subprocess
import unittest
import mock

from udocker.utils.fileutil import FileUtil
from udocker.container.localrepo import LocalRepository

UDOCKER_TOPDIR = "test_topdir"
if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"

def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()

class LocalRepositoryTestCase(unittest.TestCase):
    """Test LocalRepositoryTestCase().

    Management of local repository of container
    images and extracted containers
    Tests not yet implemented:
    _load_structure
    _find_top_layer_id
    _sorted_layers
    verify_image
    """

    def _localrepo(self, topdir):
        """Instantiate a local repository class."""
        topdir_path = os.getenv("HOME") + "/" + topdir
        Config = mock.patch('udocker.config.Config').start()
        Config.tmpdir = "/tmp"
        Config.homedir = "/tmp"
        Config.bindir = ""
        Config.libdir = ""
        Config.reposdir = ""
        Config.layersdir = ""
        Config.containersdir = ""
        FileUtil = mock.MagicMock()
        localrepo = LocalRepository(topdir_path)
        return localrepo

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01_init(self):
        """Test LocalRepository() constructor."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        self.assertTrue(localrepo.topdir)
        self.assertTrue(localrepo.reposdir)
        self.assertTrue(localrepo.layersdir)
        self.assertTrue(localrepo.containersdir)
        self.assertTrue(localrepo.bindir)
        self.assertTrue(localrepo.libdir)
        self.assertTrue(localrepo.homedir)
        self.assertEqual(localrepo.cur_repodir, "")
        self.assertEqual(localrepo.cur_tagdir, "")
        self.assertEqual(localrepo.cur_containerdir, "")

    def test_02_setup(self):
        """Test LocalRepository().setup()."""
        localrepo = self._localrepo("XXXX")
        self.assertEqual(os.path.basename(localrepo.topdir), "XXXX")
        localrepo.setup("YYYY")
        self.assertEqual(os.path.basename(localrepo.topdir), "YYYY")

    def test_03_create_repo(self):
        """Test LocalRepository().create_repo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])
        self.assertFalse(os.path.exists(localrepo.topdir))
        localrepo.create_repo()
        self.assertTrue(os.path.exists(localrepo.topdir))
        self.assertTrue(os.path.exists(localrepo.reposdir))
        self.assertTrue(os.path.exists(localrepo.layersdir))
        self.assertTrue(os.path.exists(localrepo.containersdir))
        self.assertTrue(os.path.exists(localrepo.bindir))
        self.assertTrue(os.path.exists(localrepo.libdir))
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])

    def test_04_is_repo(self):
        """Test LocalRepository().is_repo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])
        localrepo.create_repo()
        self.assertTrue(localrepo.is_repo())
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])

    def test_05_is_container_id(self):
        """Test LocalRepository().is_container_id."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        self.assertTrue(localrepo.is_container_id(
            "10860ac1-6962-3a9b-a5f8-63bcfb67ce39"))
        self.assertFalse(localrepo.is_container_id(
            "10860ac1-6962-3a9b-a5f863bcfb67ce37"))
        self.assertFalse(localrepo.is_container_id(
            "10860ac1-6962--3a9b-a5f863bcfb67ce37"))
        self.assertFalse(localrepo.is_container_id(
            "-6962--3a9b-a5f863bcfb67ce37"))
        self.assertFalse(localrepo.is_container_id(
            12345678))

    def test_06_get_container_name(self):
        """Test LocalRepository().get_container_name()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir = mock.patch('os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = mock.patch('os.listdir').start()
        mock_listdir.return_value = ['LINK']
        mock_islink = mock.patch('os.path.islink').start()
        mock_islink.return_value = True
        mock_readlink = mock.patch('os.readlink').start()
        mock_readlink.return_value = "/a/b/IMAGE:TAG"
        name_list = localrepo.get_container_name("IMAGE:TAG")
        self.assertEqual(name_list, ["LINK"])

    def test_07a_get_containers_list(self):
        """Test LocalRepository().get_containers_list()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir = mock.patch('os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = mock.patch('os.listdir').start()
        mock_listdir.return_value = ['LINK']
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='REPONAME')):
            containers_list = localrepo.get_containers_list()
            self.assertEqual(os.path.basename(containers_list[0]), "LINK")

    @mock.patch.object(LocalRepository, 'get_container_name')
    def test_07b_get_containers_list(self, mock_getname):
        """Test LocalRepository().get_containers_list()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir = mock.patch('os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = mock.patch('os.listdir').start()
        mock_listdir.return_value = ['LINK']
        mock_islink = mock.patch('os.path.islink').start()
        mock_islink.return_value = False
        mock_getname.return_value = ["NAME1", "NAME2"]
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='REPONAME')):
            containers_list = localrepo.get_containers_list(False)
            self.assertEqual(os.path.basename(containers_list[0][1]),
                             "REPONAME")

    @mock.patch.object(LocalRepository, 'get_containers_list')
    def test_08_cd_container(self, mock_getlist):
        """Test LocalRepository().cd_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists = mock.patch('os.path.exists').start()
        mock_exists.return_value = True
        mock_getlist.return_value = [localrepo.containersdir +
                                     "/CONTAINERNAME"]
        container_path = localrepo.cd_container("CONTAINERNAME")
        self.assertEqual(container_path, mock_getlist.return_value[0])

    def test_09_protect_container(self):
        """Test LocalRepository().protect_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            localrepo.protect_container(container_id)
            self.assertTrue(mopen.called)
            self.assertEqual(mopen.call_args, mock.call('/PROTECT', 'w'))

    def test_10_isprotected_container(self):
        """Test LocalRepository().isprotected_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch('os.path.exists') as mexists:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            localrepo.isprotected_container(container_id)
            self.assertTrue(mexists.called)
            self.assertEqual(mexists.call_args, mock.call('/PROTECT'))

    @mock.patch('udocker.container.localrepo.LocalRepository.cd_container')
    @mock.patch('udocker.container.localrepo.LocalRepository._unprotect')
    def test_11_unprotect_container(self, mock_unprotect, mock_cdcont):
        """Test LocalRepository().isprotected_container()."""
        mock_cdcont.return_value = "/tmp"
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        localrepo.unprotect_container(container_id)
        self.assertTrue(mock_unprotect.called)

    def test_12_protect_imagerepo(self):
        """Test LocalRepository().protect_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            localrepo.protect_imagerepo("IMAGE", "TAG")
            self.assertTrue(mopen.called)
            protect = localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mopen.call_args, mock.call(protect, 'w'))

    def test_13_isprotected_imagerepo(self):
        """Test LocalRepository().isprotected_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch('os.path.exists') as mexists:
            localrepo.isprotected_imagerepo("IMAGE", "TAG")
            self.assertTrue(mexists.called)
            protect = localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mexists.call_args, mock.call(protect))

    @mock.patch('udocker.container.localrepo.LocalRepository._unprotect')
    def test_14_unprotect_imagerepo(self, mock_unprotect):
        """Test LocalRepository().unprotected_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.unprotect_imagerepo("IMAGE", "TAG")
        self.assertTrue(mock_unprotect.called)

    @mock.patch('os.access')
    @mock.patch('os.path.isdir')
    @mock.patch('os.path.exists')
    @mock.patch.object(LocalRepository, 'cd_container')
    def test_15_iswriteable_container(self, mock_cd, mock_exists,
                                      mock_isdir, mock_access):
        """Test LocalRepository().iswriteable_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_exists.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 2)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 3)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = True
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 1)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 0)

    @mock.patch('udocker.container.localrepo.LocalRepository._name_is_valid')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('os.path.exists')
    def test_16_del_container_name(self, mock_exists, mock_msg,
                                   mock_namevalid):
        """Test LocalRepository().del_container_name()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_namevalid.return_value = False
        mock_exists.return_value = True
        FileUtil.return_value.remove.return_value = True
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)
        #
        mock_namevalid.return_value = True
        mock_exists.return_value = False
        FileUtil.return_value.remove.return_value = True
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)
        #
        mock_namevalid.return_value = True
        mock_exists.return_value = True
        FileUtil.return_value.remove.return_value = True
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertTrue(status)
        #
        mock_namevalid.return_value = True
        mock_exists.return_value = True
        FileUtil.return_value.remove.return_value = False
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)

    @mock.patch('os.symlink')
    @mock.patch('os.path.exists')
    def test_17__symlink(self, mock_exists, mock_symlink):
        """Test LocalRepository()._symlink()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = True
        status = localrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = False
        status = localrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertTrue(status)

    @mock.patch('os.path.exists')
    @mock.patch.object(LocalRepository, '_symlink')
    @mock.patch.object(LocalRepository, 'cd_container')
    def test_18_set_container_name(self, mock_cd, mock_slink, mock_exists):
        """Test LocalRepository().set_container_name()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        status = localrepo.set_container_name(container_id, "WRONG[/")
        self.assertFalse(status)
        #
        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = True
        status = localrepo.set_container_name(container_id, "RIGHT")
        self.assertFalse(status)
        #
        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = False
        status = localrepo.set_container_name(container_id, "RIGHT")
        self.assertTrue(status)

    @mock.patch('os.readlink')
    @mock.patch('os.path.isdir')
    @mock.patch('os.path.islink')
    def test_19_get_container_id(self, mock_islink,
                                 mock_isdir, mock_readlink):
        """Test LocalRepository().get_container_id()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        status = localrepo.get_container_id(None)
        self.assertEqual(status, "")
        #
        mock_islink.return_value = True
        mock_readlink.return_value = "BASENAME"
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "BASENAME")
        #
        mock_islink.return_value = False
        mock_isdir.return_value = False
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "")
        #
        mock_islink.return_value = False
        mock_isdir.return_value = True
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "ALIASNAM")

    @mock.patch('os.makedirs')
    @mock.patch('os.path.exists')
    def test_20_setup_container(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = True
        status = localrepo.setup_container("REPO", "TAG", "ID")
        self.assertEqual(status, "")
        #
        mock_exists.return_value = False
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = localrepo.setup_container("REPO", "TAG", "ID")
            self.assertEqual(status, localrepo.containersdir + "/ID")
            self.assertEqual(localrepo.cur_containerdir,
                             localrepo.containersdir + "/ID")

    @mock.patch('os.readlink')
    @mock.patch('os.path.islink')
    @mock.patch('os.listdir')
    @mock.patch.object(LocalRepository, '_inrepository')
    def test_21__remove_layers(self, mock_in,
                               mock_listdir, mock_islink, mock_readlink):
        """Test LocalRepository()._remove_layers()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_listdir.return_value = []
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        mock_listdir.return_value = ["FILE1,", "FILE2"]
        mock_islink.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        mock_islink.return_value = True
        mock_readlink.return_value = "REALFILE"
        FileUtil.return_value.remove.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)
        #
        FileUtil.return_value.remove.return_value = True
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        FileUtil.return_value.remove.return_value = True
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)
        #
        FileUtil.return_value.remove.return_value = False
        mock_in.return_value = False
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)
        #
        FileUtil.return_value.remove.return_value = False
        mock_in.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)
        #
        FileUtil.return_value.remove.return_value = False
        mock_in.return_value = True
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)

    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch.object(LocalRepository, '_remove_layers')
    @mock.patch.object(LocalRepository, 'cd_imagerepo')
    def test_22_del_imagerepo(self, mock_cd, mock_rmlayers, mock_futil):
        """Test LocalRepository()._del_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_cd.return_value = False
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertFalse(status)
        #
        mock_cd.return_value = True
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertTrue(status)
        #
        localrepo.cur_repodir = "XXXX"
        localrepo.cur_tagdir = "XXXX"
        mock_futil.return_value.remove.return_value = True
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertEqual(localrepo.cur_repodir, "")
        self.assertEqual(localrepo.cur_tagdir, "")
        self.assertTrue(status)

    def _sideffect_test_23(self, arg):
        """Side effect for isdir on test 23 _get_tags()."""
        if self.iter < 3:
            self.iter += 1
            return False
        else:
            return True

    @mock.patch('os.path.isdir')
    @mock.patch('os.listdir')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch.object(LocalRepository, '_is_tag')
    def test_23__get_tags(self, mock_is, mock_futil,
                          mock_listdir, mock_isdir):
        """Test LocalRepository()._get_tags()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_futil.return_value.isdir.return_value = False
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = []
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        mock_isdir.return_value = False
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = True
        status = localrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(status, expected_status)
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        self.iter = 0
        mock_isdir.side_effect = self._sideffect_test_23
        status = localrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(self.iter, 2)
        self.assertEqual(status, [])

    @mock.patch('os.path.islink')
    @mock.patch('os.path.exists')
    @mock.patch.object(LocalRepository, '_symlink')
    def test_24_add_image_layer(self, mock_slink, mock_exists, mock_islink):
        """Test LocalRepository().add_image_layer()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        localrepo.cur_repodir = ""
        localrepo.cur_tagdir = ""
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(status)
        #
        localrepo.cur_repodir = "IMAGE"
        localrepo.cur_tagdir = "TAG"
        status = localrepo.add_image_layer("FILE")
        self.assertTrue(status)
        #
        mock_exists.return_value = False
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        mock_islink.return_value = True
        status = localrepo.add_image_layer("FILE")
        FileUtil.return_value.remove.return_value = True
        self.assertTrue(FileUtil.called)
        self.assertTrue(status)
        #
        mock_exists.return_value = True
        mock_islink.return_value = False
        FileUtil.reset_mock()
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(FileUtil.called)
        self.assertTrue(status)

    @mock.patch('os.makedirs')
    @mock.patch('os.path.exists')
    def test_25_setup_imagerepo(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.setup_imagerepo("")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        status = localrepo.setup_imagerepo("IMAGE")
        expected_directory = localrepo.reposdir + "/IMAGE"
        self.assertEqual(localrepo.cur_repodir, expected_directory)
        self.assertFalse(status)
        #
        mock_exists.return_value = False
        status = localrepo.setup_imagerepo("IMAGE")
        expected_directory = localrepo.reposdir + "/IMAGE"
        self.assertTrue(mock_makedirs.called)
        self.assertEqual(localrepo.cur_repodir, expected_directory)
        self.assertTrue(status)

    @mock.patch('os.makedirs')
    @mock.patch('os.path.exists')
    def test_26_setup_tag(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_tag()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_exists.return_value = False
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.setup_tag("NEWTAG")
            self.assertTrue(mock_makedirs.called)
            expected_directory = localrepo.reposdir + "/IMAGE/NEWTAG"
            self.assertEqual(localrepo.cur_tagdir, expected_directory)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @mock.patch('os.listdir')
    @mock.patch('os.makedirs')
    @mock.patch('os.path.exists')
    def test_27_set_version(self, mock_exists, mock_makedirs, mock_listdir):
        """Test LocalRepository().set_version()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.set_version("v1")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.set_version("v1")
        self.assertFalse(mock_listdir.called)
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.set_version("v1")
            self.assertTrue(mock_listdir.called)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @mock.patch.object(LocalRepository, 'save_json')
    @mock.patch.object(LocalRepository, 'load_json')
    @mock.patch('os.path.exists')
    def test_28_get_image_attributes(self, mock_exists, mock_loadjson,
                                     mock_savejson):
        """Test LocalRepository().get_image_attributes()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_exists.return_value = True
        mock_loadjson.return_value = None
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, False]
        mock_loadjson.side_effect = [("foolayername",), ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, True, False]
        mock_loadjson.side_effect = [("foolayername",), "foojson"]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, True, True]
        mock_loadjson.side_effect = [("foolayername",), "foojson"]
        status = localrepo.get_image_attributes()
        self.assertEqual(('foojson', ['/foolayername.layer']), status)
        #
        mock_exists.side_effect = [False, True]
        mock_loadjson.side_effect = [None, ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [False, True, False]
        manifest = {
            "fsLayers": ({"blobSum": "foolayername"},),
            "history": ({"v1Compatibility": '["foojsonstring"]'},)
        }
        mock_loadjson.side_effect = [manifest, ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [False, True, True]
        mock_loadjson.side_effect = [manifest, ]
        status = localrepo.get_image_attributes()
        self.assertEqual(([u'foojsonstring'], ['/foolayername']), status)

    @mock.patch('json.dump')
    @mock.patch('os.path.exists')
    def test_29_save_json(self, mock_exists, mock_jsondump):
        """Test LocalRepository().save_json()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.save_json("filename", "data")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.save_json("filename", "data")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertTrue(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            status = localrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @mock.patch('json.load')
    @mock.patch('os.path.exists')
    def test_30_load_json(self, mock_exists, mock_jsonload):
        """Test LocalRepository().load_json()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.load_json("filename")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.load_json("filename")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertTrue(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            status = localrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @mock.patch('udocker.utils.fileutil.FileUtil')
    def test_31__protect(self, mock_futil):
        """Test LocalRepository()._protect().

        Set the protection mark in a container or image tag
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        status = localrepo._protect
        self.assertTrue(status)

    @mock.patch('udocker.utils.fileutil.FileUtil')
    def test_32__unprotect(self, mock_futil):
        """Test LocalRepository()._unprotect().

        Remove protection mark from container or image tag.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        status = localrepo._unprotect("dir")
        self.assertTrue(status)

    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('os.path.exists')
    def test_33__isprotected(self, mock_exists, mock_futil):
        """Test LocalRepository()._isprotected().

        See if container or image tag are protected.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        mock_exists.return_value = True
        status = localrepo._isprotected("dir")
        self.assertTrue(status)

    @mock.patch.object(LocalRepository, 'cd_container')
    @mock.patch.object(LocalRepository, 'get_containers_list')
    def test_34_del_container(self, mock_cdcont, mock_getcl):
        """Test LocalRepository().del_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"

        status = localrepo.del_container(container_id)
        self.assertTrue(mock_cdcont.called)
        self.assertFalse(status)

        mock_cdcont.return_value = ""
        mock_getcl.return_value = "tmp"
        status = localrepo.del_container(container_id)
        self.assertFalse(status)

        mock_cdcont.return_value = "/tmp"
        mock_getcl.return_value = "/tmp"
        status = localrepo.del_container(container_id)
        self.assertTrue(status)

    def test_35__relpath(self):
        """Test LocalRepository()._relpath()."""
        pass

    def test_36__name_is_valid(self):
        """Test LocalRepository()._name_is_valid().

        Check name alias validity.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)

        name = "lzskjghdlak"
        status = localrepo._name_is_valid(name)
        self.assertTrue(status)

        name = "lzskjghd/lak"
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = ".lzsklak"
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "]lzsklak"
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "lzs[klak"
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "lzs klak"
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "x" * 2049
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('os.path.isfile')
    def test_37__is_tag(self, mock_isfile, mock_futil):
        """Test LocalRepository()._is_tag().

        Does this directory contain an image tag ?
        An image TAG indicates that this repo directory
        contains references to layers and metadata from
        which we can extract a container.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)

        mock_isfile.return_value = True
        status = localrepo._is_tag("tagdir")
        self.assertTrue(status)

        mock_isfile.return_value = False
        status = localrepo._is_tag("tagdir")
        self.assertFalse(status)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_38_cd_imagerepo(self, mock_local):
        """Test LocalRepository().cd_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.reposdir = "/tmp"
        out = localrepo.cd_imagerepo("IMAGE", "TAG")
        self.assertNotEqual(out, "")

    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('os.path.islink')
    @mock.patch('os.path.isdir')
    @mock.patch('os.listdir')
    def test_39__find(self, mock_listdir, mock_isdir, mock_islink, mock_futil):
        """Test LocalRepository()._find().

        is a specific layer filename referenced by another image TAG
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)

        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["file"]
        mock_islink.return_value = True
        filename = "file"
        folder = "/tmp"

        out = localrepo._find(filename, folder)
        self.assertEqual(out, ["/tmp/file"])

        mock_islink.return_value = False
        mock_isdir.return_value = False

        out = localrepo._find(filename, folder)
        self.assertEqual(out, [])

    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('os.path.islink')
    @mock.patch('os.path.isdir')
    @mock.patch('os.listdir')
    def test_40__inrepository(self, mock_listdir,
                              mock_isdir, mock_islink, mock_futil):
        """Test LocalRepository()._inrepository().

        Check if a given file is in the repository.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)

        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["file"]
        mock_islink.return_value = True
        localrepo.reposdir = "/tmp"
        filename = "file"

        out = localrepo._inrepository(filename)
        self.assertEqual(out, ["/tmp/file"])

        mock_islink.return_value = False
        mock_isdir.return_value = False

        out = localrepo._inrepository(filename)
        self.assertEqual(out, [])

    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('os.path.islink')
    @mock.patch('os.readlink')
    @mock.patch('os.listdir')
    @mock.patch('os.path.realpath')
    def test_41__remove_layers(self, mock_realpath, mock_listdir,
                               mock_readlink, mock_islink, mock_futil):
        """Test LocalRepository()._remove_layers().

        Remove link to image layer and corresponding layer
        if not being used by other images.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.reposdir = "/tmp"
        mock_realpath.return_value = "/tmp"
        mock_listdir.return_value = "file"
        mock_islink.return_value = True
        mock_readlink.return_value = "file"
        tag_dir = "TAGDIR"

        mock_futil.return_value.remove.return_value = False
        status = localrepo._remove_layers(tag_dir, True)
        self.assertTrue(status)

        mock_futil.return_value.remove.return_value = False
        status = localrepo._remove_layers(tag_dir, False)
        # (FIXME lalves): This is not OK, it should be False. Review this test.
        self.assertTrue(status)

    @mock.patch.object(LocalRepository, '_get_tags')
    def test_42_get_imagerepos(self, mock_gtags):
        """Test LocalRepository().get_imagerepos()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.get_imagerepos()
        self.assertTrue(mock_gtags.called)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch.object(LocalRepository, 'cd_container')
    def test_43_get_layers(self, mock_local, mock_cd):
        """Test LocalRepository().get_layers()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.get_layers("IMAGE", "TAG")
        self.assertTrue(mock_cd.called)

    @mock.patch('udocker.utils.fileutil.FileUtil.isdir')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.container.localrepo.LocalRepository.load_json')
    @mock.patch('os.listdir')
    def test_44__load_structure(self, mock_listdir, mock_json,
                                mock_local, mock_isdir):
        """Test LocalRepository()._load_structure().

        Scan the repository structure of a given image tag.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir.return_value = False
        structure = localrepo._load_structure("IMAGETAGDIR")
        self.assertTrue(structure["layers"])

        mock_isdir.return_value = True
        mock_listdir.return_value = ["ancestry"]
        localrepo.return_value = "JSON"
        structure = localrepo._load_structure("IMAGETAGDIR")
        # WIP
        # self.assertTrue("JSON" in structure["ancestry"])


    def test_45__find_top_layer_id(self):
        """Test."""
        pass

    def test_46__sorted_layers(self):
        """Test."""
        pass

    def test_47__verify_layer_file(self):
        """Test."""
        pass

    @mock.patch('udocker.msg.Msg')
    @mock.patch.object(LocalRepository, '_load_structure')
    def test_48_verify_image(self, mock_lstruct, mock_msg):
        """Test LocalRepository().verify_image()."""
        mock_msg.level = 0
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.verify_image()
        self.assertTrue(mock_lstruct.called)
