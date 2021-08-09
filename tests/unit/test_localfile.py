#!/usr/bin/env python
"""
udocker unit tests: LocalFileAPI
"""

from unittest import TestCase, main
from unittest.mock import patch, Mock
from udocker.localfile import LocalFileAPI


class LocalFileAPITestCase(TestCase):
    """Test LocalFileAPI()."""

    def setUp(self):
        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

    def tearDown(self):
        self.lrepo.stop()

    # def test_01__init(self):
    #     """Test01 LocalFileAPI() constructor."""

    @patch('udocker.localfile.OciLocalFileAPI.load')
    @patch('udocker.localfile.DockerLocalFileAPI.load')
    @patch.object(LocalFileAPI, '_get_imagedir_type')
    @patch('udocker.localfile.FileUtil.remove')
    @patch.object(LocalFileAPI, '_untar_saved_container')
    @patch('udocker.localfile.os.makedirs')
    @patch('udocker.localfile.FileUtil.mktmp')
    @patch('udocker.localfile.Msg.err')
    @patch('udocker.localfile.os.path.exists')
    def test_02_load(self, mock_exists, mock_msg, mock_mktmp, mock_mkdir,
                     mock_untar, mock_remove, mock_imgtype, mock_dockerload,
                     mock_ociload):
        """Test02 LocalFileAPI().load."""
        mock_exists.return_value = False
        status = LocalFileAPI(self.mock_lrepo).load('imgfile')
        self.assertTrue(mock_msg.called)
        self.assertFalse(status)

        mock_exists.return_value = True
        mock_mktmp.return_value = '/tmp/imgdir'
        mock_mkdir.return_value = None
        mock_untar.return_value = False
        mock_remove.return_value = None
        status = LocalFileAPI(self.mock_lrepo).load('imgfile')
        self.assertTrue(mock_mktmp.called)
        self.assertTrue(mock_mkdir.called)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_msg.called)
        self.assertFalse(status)

        mock_exists.return_value = True
        mock_mktmp.return_value = '/tmp/imgdir'
        mock_mkdir.return_value = None
        mock_untar.return_value = True
        mock_remove.return_value = None
        mock_imgtype.return_value = 'Docker'
        mock_dockerload.return_value = ['docker-repo1', 'docker-repo2']
        status = LocalFileAPI(self.mock_lrepo).load('imgfile')
        self.assertTrue(mock_imgtype.called)
        self.assertTrue(mock_dockerload.called)
        self.assertEqual(status, ['docker-repo1', 'docker-repo2'])

        mock_exists.return_value = True
        mock_mktmp.return_value = '/tmp/imgdir'
        mock_mkdir.return_value = None
        mock_untar.return_value = True
        mock_remove.return_value = None
        mock_imgtype.return_value = 'OCI'
        mock_ociload.return_value = ['OCI-repo1', 'OCI-repo2']
        status = LocalFileAPI(self.mock_lrepo).load('imgfile')
        self.assertTrue(mock_imgtype.called)
        self.assertTrue(mock_ociload.called)
        self.assertEqual(status, ['OCI-repo1', 'OCI-repo2'])

        mock_exists.return_value = True
        mock_mktmp.return_value = '/tmp/imgdir'
        mock_mkdir.return_value = None
        mock_untar.return_value = True
        mock_remove.return_value = None
        mock_imgtype.return_value = ''
        status = LocalFileAPI(self.mock_lrepo).load('imgfile')
        self.assertTrue(mock_imgtype.called)
        self.assertEqual(status, [])

    @patch('udocker.localfile.DockerLocalFileAPI.save')
    def test_03_save(self, mock_dockersave):
        """Test03 LocalFileAPI().save."""
        mock_dockersave.return_value = True
        img_tag = ['tag1', 'tag2']
        status = LocalFileAPI(self.mock_lrepo).save(img_tag, 'imgfile')
        self.assertTrue(status)


if __name__ == '__main__':
    main()
