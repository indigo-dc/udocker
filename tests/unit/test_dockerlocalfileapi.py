#!/usr/bin/env python
"""
udocker unit tests: DockerLocalFileAPI
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

sys.path.append('.')

from udocker.docker import DockerLocalFileAPI
from udocker.config import Config
from udocker.container.localrepo import LocalRepository


class DockerLocalFileAPITestCase(TestCase):
    """Test DockerLocalFileAPI() manipulate Docker images."""

    def setUp(self):
        self.conf = Config().getconf()
        self.conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        self.conf['cmd'] = "/bin/bash"
        self.conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                                ["taskset", "-c", "%s", ])
        self.conf['valid_host_env'] = "HOME"
        self.conf['username'] = "user"
        self.conf['userhome'] = "/"
        self.conf['oskernel'] = "4.8.13"
        self.conf['location'] = ""
        self.conf['keystore'] = "KEYSTORE"
        self.conf['osversion'] = "OSVERSION"
        self.conf['arch'] = "ARCH"

        self.local = LocalRepository(self.conf)
        self.dlocapi = DockerLocalFileAPI(self.local, self.conf)

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test DockerLocalFileAPI() constructor."""
        self.assertEqual(self.dlocapi.localrepo, self.local)

    @patch('udocker.docker.os.listdir')
    @patch('udocker.utils.fileutil.FileUtil.isdir')
    @patch('udocker.container.localrepo.LocalRepository.load_json')
    def test_02__load_structure(self, mock_ljson, mock_isdir, mock_ldir):
        """Test DockerLocalFileAPI()._load_structure()."""
        mock_isdir.return_value = False
        structure = self.dlocapi._load_structure("/tmp")
        self.assertEqual(structure, {'layers': {}})

        mock_isdir.return_value = True
        mock_ldir.return_value = ["repositories", ]
        mock_ljson.return_value = {"REPO": "", }
        structure = self.dlocapi._load_structure("/tmp")
        expected = {'layers': {}, 'repositories': {'REPO': ''}}
        self.assertEqual(structure, expected)
        #
        mock_isdir.return_value = True
        mock_ldir.return_value = ["manifest.json", ]
        structure = self.dlocapi._load_structure("/tmp")
        expected = {'layers': {}}
        self.assertEqual(structure, expected)
        #
        mock_isdir.return_value = True
        mock_ldir.return_value = ["x" * 64 + ".json", ]
        structure = self.dlocapi._load_structure("/tmp")
        expected = {'layers': {}}
        self.assertEqual(structure, expected)
        #
        mock_isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["VERSION", ], ]
        mock_ljson.return_value = {"X": "", }
        structure = self.dlocapi._load_structure("/tmp")
        expected = {'layers': {"x" * 64: {'VERSION': {'X': ''}}}}
        self.assertEqual(structure, expected)
        #
        mock_isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["json", ], ]
        mock_ljson.return_value = {"X": "", }
        structure = self.dlocapi._load_structure("/tmp")
        expected = {'layers': {"x" * 64: {'json': {'X': ''},
                                          'json_f': '/tmp/' + "x" * 64 + '/json'}}}
        self.assertEqual(structure, expected)
        #
        mock_isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["layer", ], ]
        mock_ljson.return_value = {"X": "", }
        structure = self.dlocapi._load_structure("/tmp")
        expected = {'layers': {"x" * 64: {
            'layer_f': '/tmp/' + "x" * 64 + '/layer'}}}
        self.assertEqual(structure, expected)

    def test_03__find_top_layer_id(self):
        """Test DockerLocalFileAPI()._find_top_layer_id()."""
        structure = {}
        status = self.dlocapi._find_top_layer_id(structure)
        self.assertFalse(status)
        #
        structure = {'layers': {"LID": {"json": {}, }, }, }
        status = self.dlocapi._find_top_layer_id(structure)
        self.assertEqual(status, "LID")
        #
        structure = {'layers': {"LID": {"json": {"parent": "x", }, }, }, }
        status = self.dlocapi._find_top_layer_id(structure)
        self.assertEqual(status, "LID")

    def test_04__sorted_layers(self):
        """Test DockerLocalFileAPI()._sorted_layers()."""
        structure = {}
        status = self.dlocapi._sorted_layers(structure, "")
        self.assertFalse(status)
        #
        structure = {'layers': {"LID": {"json": {"parent": {}, }, }, }, }
        status = self.dlocapi._sorted_layers(structure, "LID")
        self.assertEqual(status, ["LID"])

    @patch('udocker.docker.os.rename')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_05__copy_layer_to_repo(self, mock_local, mock_rename):
        """Test DockerLocalFileAPI()._copy_layer_to_repo()."""
        mock_local.layersdir = ""
        status = self.dlocapi._copy_layer_to_repo("/", "LID")
        self.assertFalse(status)
        #
        status = self.dlocapi._copy_layer_to_repo("/xxx.json", "LID")
        self.assertTrue(status)

    @patch('udocker.docker.DockerLocalFileAPI._copy_layer_to_repo')
    @patch('udocker.docker.DockerLocalFileAPI._sorted_layers')
    @patch('udocker.docker.DockerLocalFileAPI._find_top_layer_id')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_06__load_image(self, mock_local, mock_findtop,
                            mock_slayers, mock_copylayer):
        """Test DockerLocalFileAPI()._load_image()."""
        # mock_local.cd_imagerepo.return_value = True
        # structure = {}
        # status = self.dlocapi._load_image(structure, "IMAGE", "TAG")
        # self.assertFalse(status)
        #
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = ""
        structure = {}
        status = self.dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = "/dir"
        mock_local.set_version.return_value = False
        structure = {}
        status = self.dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        # mock_local.cd_imagerepo.return_value = False
        # mock_local.setup_tag.return_value = "/dir"
        # mock_local.set_version.return_value = True
        # mock_findtop.return_value = "TLID"
        # mock_slayers.return_value = []
        # structure = {}
        # status = self.dlocapi._load_image(structure, "IMAGE", "TAG")
        # self.assertEqual(status, ['IMAGE:TAG'])
        #
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = "/dir"
        mock_local.set_version.return_value = True
        mock_findtop.return_value = "TLID"
        mock_slayers.return_value = ["LID", ]
        mock_copylayer.return_value = False
        structure = {'layers': {'LID': {'VERSION': "1.0",
                                        'json_f': "f1",
                                        'layer_f': "f1", }, }, }
        status = self.dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        # mock_local.cd_imagerepo.return_value = False
        # mock_local.setup_tag.return_value = "/dir"
        # mock_local.set_version.return_value = True
        # mock_findtop.return_value = "TLID"
        # mock_slayers.return_value = ["LID", ]
        # mock_copylayer.return_value = True
        # structure = {'layers': {'LID': {'VERSION': "1.0",
        #                                 'json_f': "f1",
        #                                 'layer_f': "f1", }, }, }
        # status = self.dlocapi._load_image(structure, "IMAGE", "TAG")
        # self.assertEqual(status, ['IMAGE:TAG'])

    @patch('udocker.docker.DockerLocalFileAPI._load_image')
    def test_07__load_repositories(self, mock_loadi):
        """Test DockerLocalFileAPI()._load_repositories()."""
        structure = {}
        status = self.dlocapi._load_repositories(structure)
        self.assertFalse(status)
        #
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_loadi.return_value = False
        status = self.dlocapi._load_repositories(structure)
        self.assertFalse(status)
        #
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_loadi.return_value = True
        status = self.dlocapi._load_repositories(structure)
        self.assertTrue(status)

    @patch('udocker.docker.subprocess.call')
    def test_08__untar_saved_container(self, mock_call):
        """Test DockerLocalFileAPI()._untar_saved_container()."""
        mock_call.return_value = True
        status = self.dlocapi._untar_saved_container("TARFILE", "DESTDIR")
        self.assertFalse(status)
        #
        mock_call.return_value = False
        status = self.dlocapi._untar_saved_container("TARFILE", "DESTDIR")
        self.assertTrue(status)

    @patch('udocker.docker.DockerLocalFileAPI._load_repositories')
    @patch('udocker.docker.DockerLocalFileAPI._load_structure')
    @patch('udocker.docker.DockerLocalFileAPI._untar_saved_container')
    @patch('udocker.docker.os.makedirs')
    @patch('udocker.utils.fileutil.FileUtil.mktmp')
    @patch('udocker.docker.os.path.exists')
    def test_09_load(self, mock_exists, mock_mktmp,
                     mock_makedirs, mock_untar, mock_lstruct, mock_lrepo):
        """Test DockerLocalFileAPI().load()."""
        mock_exists.return_value = False
        mock_mktmp.return_value = "tmpfile"
        status = self.dlocapi.load("IMAGEFILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        mock_mktmp.return_value = "tmpfile"
        mock_untar.return_value = False
        status = self.dlocapi.load("IMAGEFILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        mock_mktmp.return_value = "tmpfile"
        mock_untar.return_value = True
        structure = {}
        mock_lstruct.return_value = structure
        status = self.dlocapi.load("IMAGEFILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        mock_mktmp.return_value = "tmpfile"
        mock_untar.return_value = True
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_lstruct.return_value = structure
        mock_lrepo.return_value = ["R1", "R2", ]
        status = self.dlocapi.load("IMAGEFILE")
        self.assertEqual(status, ["R1", "R2", ])

    @patch('udocker.docker.time.strftime')
    @patch('udocker.utils.fileutil.FileUtil.size')
    def test_10_create_container_meta(self, mock_size, mock_stime):
        """Test DockerLocalFileAPI().create_container_meta()."""
        mock_size.return_value = 123
        mock_stime.return_value = "DATE"
        status = self.dlocapi.create_container_meta("LID")
        meta = {'comment': 'created by udocker',
                'created': 'DATE',
                'config': {'Env': None, 'Hostname': '', 'Entrypoint': None,
                           'PortSpecs': None, 'Memory': 0, 'OnBuild': None,
                           'OpenStdin': False, 'MacAddress': '', 'Cpuset': '',
                           'NetworkDisable': False, 'User': '',
                           'AttachStderr': False, 'AttachStdout': False,
                           'Cmd': None, 'StdinOnce': False, 'CpusShares': 0,
                           'WorkingDir': '', 'AttachStdin': False,
                           'Volumes': None, 'MemorySwap': 0, 'Tty': False,
                           'Domainname': '', 'Image': '', 'Labels': None,
                           'ExposedPorts': None},
                'container_config': {'Env': None, 'Hostname': '',
                                     'Entrypoint': None, 'PortSpecs': None,
                                     'Memory': 0, 'OnBuild': None,
                                     'OpenStdin': False, 'MacAddress': '',
                                     'Cpuset': '', 'NetworkDisable': False,
                                     'User': '', 'AttachStderr': False,
                                     'AttachStdout': False, 'Cmd': None,
                                     'StdinOnce': False, 'CpusShares': 0,
                                     'WorkingDir': '', 'AttachStdin': False,
                                     'Volumes': None, 'MemorySwap': 0,
                                     'Tty': False, 'Domainname': '',
                                     'Image': '', 'Labels': None,
                                     'ExposedPorts': None},
                'architecture': 'ARCH', 'os': 'OSVERSION',
                'id': 'LID', 'size': 123}
        self.assertEqual(status, meta)

    @patch('udocker.helper.unique.Unique.layer_v1')
    @patch('udocker.docker.os.rename')
    @patch('udocker.utils.fileutil.FileUtil')
    @patch('udocker.docker.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_11_import_toimage(self, mock_local, mock_exists,
                               mock_futil, mock_rename, mock_v1):
        """Test DockerLocalFileAPI().import_toimage()."""
        mock_exists.return_value = False
        status = self.dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = "TAGDIR"
        status = self.dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = ""
        status = self.dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = "TAGDIR"
        mock_local.set_version.return_value = False
        status = self.dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        # mock_exists.return_value = True
        # mock_local.cd_imagerepo.return_value = ""
        # mock_local.setup_tag.return_value = "TAGDIR"
        # mock_local.set_version.return_value = True
        # mock_v1.return_value = "LAYERID"
        # status = self.dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        # self.assertEqual(status, "LAYERID")
        # self.assertTrue(mock_rename.called)
        # #
        # mock_rename.reset_mock()
        # mock_exists.return_value = True
        # mock_local.cd_imagerepo.return_value = ""
        # mock_local.setup_tag.return_value = "TAGDIR"
        # mock_local.set_version.return_value = True
        # mock_v1.return_value = "LAYERID"
        # status = self.dlocapi.import_toimage("TARFILE", "IMAGE", "TAG", False)
        # self.assertEqual(status, "LAYERID")
        # self.assertFalse(mock_rename.called)


if __name__ == '__main__':
    main()
