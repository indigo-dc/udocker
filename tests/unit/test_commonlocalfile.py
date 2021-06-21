#!/usr/bin/env python
"""
udocker unit tests: CommonLocalFileApi
"""

from unittest import TestCase, main
from unittest.mock import Mock, patch
from udocker.commonlocalfile import CommonLocalFileApi


class CommonLocalFileApiTestCase(TestCase):
    """Test CommonLocalFileApi()."""

    def setUp(self):
        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

    def tearDown(self):
        self.lrepo.stop()

    def test_01_init(self):
        """Test01 CommonLocalFileApi() constructor"""
        clfapi = CommonLocalFileApi(self.local)
        self.assertEqual(clfapi.localrepo, self.local)

    @patch('udocker.commonlocalfile.FileUtil.copyto')
    @patch('udocker.commonlocalfile.os.rename')
    def test_02__move_layer_to_v1repo(self, mock_rename, mock_copy):
        """Test02 CommonLocalFileApi()._move_layer_to_v1repo()."""
        layer_id = "xxx"
        filepath = "yy"
        self.local.layersdir = "/home/.udocker"
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._move_layer_to_v1repo(filepath, layer_id)
        self.assertFalse(status)

        layer_id = "12345"
        filepath = "/home/.udocker/12345.json"
        self.local.layersdir = "/home/.udocker"
        mock_rename.return_value = None
        mock_copy.return_value = True
        self.local.add_image_layer.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._move_layer_to_v1repo(filepath, layer_id)
        self.assertTrue(status)
        self.assertTrue(mock_rename.called)
        self.assertTrue(self.local.add_image_layer.called)

        layer_id = "12345"
        filepath = "/home/.udocker/12345.layer.tar"
        self.local.layersdir = "/home/.udocker"
        mock_rename.return_value = None
        mock_copy.return_value = True
        self.local.add_image_layer.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._move_layer_to_v1repo(filepath, layer_id)
        self.assertTrue(status)
        self.assertTrue(mock_rename.called)
        self.assertTrue(self.local.add_image_layer.called)

    # def test_03__load_image_step2(self):
    #     """Test03 CommonLocalFileApi()._load_image_step2()."""

    @patch('udocker.commonlocalfile.Msg')
    def test_04__load_image(self, mock_msg):
        """Test04 CommonLocalFileApi()._load_image()."""
        mock_msg.level = 0
        structure = "12345"
        imagerepo = "/home/.udocker/images"
        tag = "v1"
        self.local.cd_imagerepo.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._load_image(structure, imagerepo, tag)
        self.assertEqual(status, [])

        self.local.cd_imagerepo.return_value = False
        self.local.setup_imagerepo.return_value = True
        self.local.setup_tag.return_value = False
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._load_image(structure, imagerepo, tag)
        self.assertEqual(status, [])

        self.local.cd_imagerepo.return_value = False
        self.local.setup_imagerepo.return_value = True
        self.local.setup_tag.return_value = True
        self.local.set_version.return_value = False
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._load_image(structure, imagerepo, tag)
        self.assertEqual(status, [])

        self.local.cd_imagerepo.return_value = False
        self.local.setup_imagerepo.return_value = True
        self.local.setup_tag.return_value = True
        self.local.set_version.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._load_image(structure, imagerepo, tag)
        self.assertEqual(status, None)

    @patch('udocker.commonlocalfile.Uprocess.call')
    def test_05__untar_saved_container(self, mock_ucall):
        """Test05 CommonLocalFileApi()._untar_saved_container()."""
        tarfile = "file.tar"
        destdir = "/home/.udocker/images"
        mock_ucall.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._untar_saved_container(tarfile, destdir)
        self.assertFalse(status)

        mock_ucall.return_value = False
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._untar_saved_container(tarfile, destdir)
        self.assertTrue(status)

    @patch('udocker.commonlocalfile.FileUtil.size')
    @patch('udocker.commonlocalfile.HostInfo.osversion')
    @patch('udocker.commonlocalfile.HostInfo.arch')
    def test_06_create_container_meta(self, mock_arch, mock_version,
                                      mock_size):
        """Test06 CommonLocalFileApi().create_container_meta()."""
        layer_id = "12345"
        comment = "created by my udocker"
        mock_arch.return_value = "x86_64"
        mock_version.return_value = "8"
        mock_size.return_value = 125
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.create_container_meta(layer_id, comment)
        self.assertEqual(status["id"], layer_id)
        self.assertEqual(status["comment"], comment)
        self.assertTrue(mock_arch.called)
        self.assertTrue(mock_version.called)
        self.assertTrue(mock_size.called)

    @patch('udocker.commonlocalfile.Msg')
    @patch('udocker.commonlocalfile.os.rename')
    @patch('udocker.commonlocalfile.FileUtil.copyto')
    @patch('udocker.commonlocalfile.Unique.layer_v1')
    @patch('udocker.commonlocalfile.os.path.exists')
    def test_07_import_toimage(self, mock_exists, mock_layerv1,
                               mock_copy, mock_rename, mock_msg):
        """Test07 CommonLocalFileApi().import_toimage()."""
        tarfile = "img.tar"
        imagerepo = "/home/.udocker/images"
        tag = "v1"
        move_tarball = True
        mock_msg.level = 0
        mock_exists.side_effect = [False, False]
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_toimage(tarfile, imagerepo, tag, move_tarball)
        self.assertFalse(status)

        mock_exists.side_effect = [True, False]
        self.local.setup_imagerepo.return_value = True
        self.local.cd_imagerepo.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_toimage(tarfile, imagerepo, tag, move_tarball)
        self.assertFalse(status)
        self.assertTrue(self.local.setup_imagerepo.called)
        self.assertTrue(self.local.cd_imagerepo.called)

        mock_exists.side_effect = [True, False]
        self.local.setup_imagerepo.return_value = True
        self.local.cd_imagerepo.return_value = False
        self.local.setup_tag.return_value = False
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_toimage(tarfile, imagerepo, tag, move_tarball)
        self.assertFalse(status)
        self.assertTrue(self.local.setup_imagerepo.called)
        self.assertTrue(self.local.cd_imagerepo.called)
        self.assertTrue(self.local.setup_tag.called)

        mock_exists.side_effect = [True, False]
        self.local.setup_imagerepo.return_value = True
        self.local.cd_imagerepo.return_value = False
        self.local.setup_tag.return_value = True
        self.local.set_version.return_value = False
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_toimage(tarfile, imagerepo, tag, move_tarball)
        self.assertFalse(status)
        self.assertTrue(self.local.setup_imagerepo.called)
        self.assertTrue(self.local.cd_imagerepo.called)
        self.assertTrue(self.local.setup_tag.called)

        tarfile = "img.tar"
        imagerepo = "/home/.udocker/images"
        tag = "v1"
        move_tarball = True
        mock_exists.side_effect = [True, False]
        self.local.setup_imagerepo.return_value = True
        self.local.cd_imagerepo.return_value = False
        self.local.setup_tag.return_value = True
        self.local.set_version.return_value = True
        mock_layerv1.return_value = "12345"
        mock_copy.return_value = False
        mock_rename.return_value = None
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_toimage(tarfile, imagerepo, tag, move_tarball)
        self.assertFalse(status)
        self.assertTrue(mock_layerv1.called)
        self.assertTrue(mock_rename.called)

        move_tarball = False
        mock_exists.side_effect = [True, True]
        self.local.setup_imagerepo.return_value = True
        self.local.cd_imagerepo.return_value = False
        self.local.setup_tag.return_value = True
        self.local.set_version.return_value = True
        self.local.add_image_layer.side_effect = [True, True]
        self.local.save_json.side_effect = [True, True]
        mock_layerv1.return_value = "12345"
        mock_copy.return_value = False
        mock_rename.return_value = None
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_toimage(tarfile, imagerepo, tag, move_tarball)
        self.assertEqual(status, "12345")
        self.assertTrue(mock_layerv1.called)

    @patch('udocker.commonlocalfile.Msg')
    @patch('udocker.commonlocalfile.ContainerStructure.create_fromlayer')
    @patch('udocker.commonlocalfile.Unique.layer_v1')
    @patch('udocker.commonlocalfile.os.path.exists')
    def test_08_import_tocontainer(self, mock_exists, mock_layerv1,
                                   mock_create, mock_msg):
        """Test08 CommonLocalFileApi().import_tocontainer()."""
        tarfile = ""
        imagerepo = ""
        tag = ""
        container_name = ""
        mock_msg.level = 0
        mock_exists.return_value = False
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_tocontainer(tarfile, imagerepo,
                                           tag, container_name)
        self.assertFalse(status)

        tarfile = "img.tar"
        imagerepo = "/home/.udocker/images"
        tag = "v1"
        container_name = "mycont"
        self.local.get_container_id.return_value = True
        mock_exists.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_tocontainer(tarfile, imagerepo,
                                           tag, container_name)
        self.assertTrue(self.local.get_container_id.called)
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)

        tarfile = "img.tar"
        imagerepo = "/home/.udocker/images"
        tag = "v1"
        container_name = "mycont"
        self.local.get_container_id.return_value = False
        self.local.set_container_name.return_value = True
        mock_exists.return_value = True
        mock_layerv1.return_value = "12345"
        mock_create.return_value = "345"
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_tocontainer(tarfile, imagerepo,
                                           tag, container_name)
        self.assertTrue(self.local.get_container_id.called)
        self.assertTrue(mock_exists.called)
        self.assertTrue(mock_layerv1.called)
        self.assertTrue(mock_create.called)
        self.assertEqual(status, "345")

    @patch('udocker.commonlocalfile.Msg')
    @patch('udocker.commonlocalfile.ContainerStructure.clone_fromfile')
    @patch('udocker.commonlocalfile.os.path.exists')
    def test_09_import_clone(self, mock_exists, mock_clone, mock_msg):
        """Test09 CommonLocalFileApi().import_clone()."""
        tarfile = ""
        container_name = ""
        mock_msg.level = 0
        mock_exists.return_value = False
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_clone(tarfile, container_name)
        self.assertFalse(status)

        tarfile = "img.tar"
        container_name = "mycont"
        self.local.get_container_id.return_value = True
        mock_exists.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_clone(tarfile, container_name)
        self.assertTrue(self.local.get_container_id.called)
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)

        tarfile = "img.tar"
        container_name = "mycont"
        self.local.get_container_id.return_value = False
        self.local.set_container_name.return_value = True
        mock_exists.return_value = True
        mock_clone.return_value = "345"
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.import_clone(tarfile, container_name)
        self.assertTrue(self.local.get_container_id.called)
        self.assertTrue(mock_exists.called)
        self.assertTrue(mock_clone.called)
        self.assertEqual(status, "345")

    @patch('udocker.commonlocalfile.Msg')
    @patch('udocker.commonlocalfile.ExecutionMode.set_mode')
    @patch('udocker.commonlocalfile.ExecutionMode.get_mode')
    @patch('udocker.commonlocalfile.ContainerStructure.clone')
    def test_10_clone_container(self, mock_clone,
                                mock_exget, mock_exset, mock_msg):
        """Test10 CommonLocalFileApi().clone_container()."""
        container_name = "mycont"
        container_id = ""
        mock_msg.level = 0
        self.local.get_container_id.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.clone_container(container_id, container_name)
        self.assertFalse(status)

        container_name = "mycont"
        container_id = ""
        self.local.get_container_id.return_value = False
        self.local.set_container_name.return_value = True
        mock_clone.return_value = "345"
        mock_exget.return_value = "P1"
        mock_exset.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.clone_container(container_id, container_name)
        self.assertTrue(self.local.get_container_id.called)
        self.assertTrue(self.local.set_container_name.called)
        self.assertTrue(mock_exget.called)
        self.assertFalse(mock_exset.called)
        self.assertTrue(mock_clone.called)
        self.assertEqual(status, "345")

        container_name = "mycont"
        container_id = ""
        self.local.get_container_id.return_value = False
        self.local.set_container_name.return_value = True
        mock_clone.return_value = "345"
        mock_exget.return_value = "F1"
        mock_exset.return_value = True
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi.clone_container(container_id, container_name)
        self.assertTrue(self.local.get_container_id.called)
        self.assertTrue(self.local.set_container_name.called)
        self.assertTrue(mock_exget.called)
        self.assertTrue(mock_exset.called)
        self.assertTrue(mock_clone.called)
        self.assertEqual(status, "345")

    @patch('udocker.commonlocalfile.os.path.exists')
    def test_11__get_imagedir_type(self, mock_exists):
        """Test11 CommonLocalFileApi()._get_imagedir_type()."""
        tmp_imagedir = "/home/.udocker/images/myimg"
        mock_exists.side_effect = [False, False]
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._get_imagedir_type(tmp_imagedir)
        self.assertEqual(status, "")

        mock_exists.side_effect = [True, False]
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._get_imagedir_type(tmp_imagedir)
        self.assertEqual(status, "OCI")

        mock_exists.side_effect = [False, True]
        clfapi = CommonLocalFileApi(self.local)
        status = clfapi._get_imagedir_type(tmp_imagedir)
        self.assertEqual(status, "Docker")

if __name__ == '__main__':
    main()
