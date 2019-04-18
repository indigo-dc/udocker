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
        self.doia = DockerLocalFileAPI(self.local, self.conf)

    def tearDown(self):
        pass

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local):
        """Test DockerLocalFileAPI() constructor."""
        self._init()
        dlocapi = DockerLocalFileAPI(mock_local)
        self.assertEqual(dlocapi.localrepo, mock_local)

    @mock.patch('os.listdir')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_02__load_structure(self, mock_local, mock_futil, mock_ldir):
        """Test DockerLocalFileAPI()._load_structure()."""
        self._init()
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = False
        structure = dlocapi._load_structure("/tmp")
        self.assertEqual(structure, {'layers': {}})
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.return_value = ["repositories", ]
        mock_local.load_json.return_value = {"REPO": "", }
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {}, 'repositories': {'REPO': ''}}
        self.assertEqual(structure, expected)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.return_value = ["manifest.json", ]
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {}}
        self.assertEqual(structure, expected)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.return_value = ["x" * 64 + ".json", ]
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {}}
        self.assertEqual(structure, expected)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["VERSION", ], ]
        mock_local.load_json.return_value = {"X": "", }
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {"x" * 64: {'VERSION': {'X': ''}}}}
        self.assertEqual(structure, expected)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["json", ], ]
        mock_local.load_json.return_value = {"X": "", }
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {"x" * 64: {'json': {'X': ''},
                                          'json_f': '/tmp/' + "x" * 64 + '/json'}}}
        self.assertEqual(structure, expected)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["layer", ], ]
        mock_local.load_json.return_value = {"X": "", }
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {"x" * 64: {
            'layer_f': '/tmp/' + "x" * 64 + '/layer'}}}
        self.assertEqual(structure, expected)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_03__find_top_layer_id(self, mock_local):
        """Test DockerLocalFileAPI()._find_top_layer_id()."""
        self._init()
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        structure = {}
        status = dlocapi._find_top_layer_id(structure)
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        structure = {'layers': {"LID": {"json": {}, }, }, }
        status = dlocapi._find_top_layer_id(structure)
        self.assertEqual(status, "LID")
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        structure = {'layers': {"LID": {"json": {"parent": "x", }, }, }, }
        status = dlocapi._find_top_layer_id(structure)
        self.assertEqual(status, "LID")

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_04__sorted_layers(self, mock_local):
        """Test DockerLocalFileAPI()._sorted_layers()."""
        self._init()
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        structure = {}
        status = dlocapi._sorted_layers(structure, "")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        structure = {'layers': {"LID": {"json": {"parent": {}, }, }, }, }
        status = dlocapi._sorted_layers(structure, "LID")
        self.assertEqual(status, ["LID"])

    @mock.patch('os.rename')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_05__copy_layer_to_repo(self, mock_local, mock_rename):
        """Test DockerLocalFileAPI()._copy_layer_to_repo()."""
        self._init()
        mock_local.layersdir = ""
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        status = dlocapi._copy_layer_to_repo("/", "LID")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        status = dlocapi._copy_layer_to_repo("/xxx.json", "LID")
        self.assertTrue(status)

    @mock.patch('udocker.docker.DockerLocalFileAPI._copy_layer_to_repo')
    @mock.patch('udocker.docker.DockerLocalFileAPI._sorted_layers')
    @mock.patch('udocker.docker.DockerLocalFileAPI._find_top_layer_id')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_06__load_image(self, mock_local, mock_msg, mock_findtop,
                            mock_slayers, mock_copylayer):
        """Test DockerLocalFileAPI()._load_image()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = True
        structure = {}
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = ""
        structure = {}
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = "/dir"
        mock_local.set_version.return_value = False
        structure = {}
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = "/dir"
        mock_local.set_version.return_value = True
        mock_findtop.return_value = "TLID"
        mock_slayers.return_value = []
        structure = {}
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertEqual(status, ['IMAGE:TAG'])
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = "/dir"
        mock_local.set_version.return_value = True
        mock_findtop.return_value = "TLID"
        mock_slayers.return_value = ["LID", ]
        mock_copylayer.return_value = False
        structure = {'layers': {'LID': {'VERSION': "1.0",
                                        'json_f': "f1",
                                        'layer_f': "f1", }, }, }
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = "/dir"
        mock_local.set_version.return_value = True
        mock_findtop.return_value = "TLID"
        mock_slayers.return_value = ["LID", ]
        mock_copylayer.return_value = True
        structure = {'layers': {'LID': {'VERSION': "1.0",
                                        'json_f': "f1",
                                        'layer_f': "f1", }, }, }
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertEqual(status, ['IMAGE:TAG'])

    @mock.patch('udocker.docker.DockerLocalFileAPI._load_image')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_07__load_repositories(self, mock_local, mock_msg, mock_loadi):
        """Test DockerLocalFileAPI()._load_repositories()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        structure = {}
        status = dlocapi._load_repositories(structure)
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_loadi.return_value = False
        status = dlocapi._load_repositories(structure)
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_loadi.return_value = True
        status = dlocapi._load_repositories(structure)
        self.assertTrue(status)

    @mock.patch('subprocess.call')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_08__untar_saved_container(self, mock_local, mock_msg, mock_call):
        """Test DockerLocalFileAPI()._untar_saved_container()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_call.return_value = True
        status = dlocapi._untar_saved_container("TARFILE", "DESTDIR")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_call.return_value = False
        status = dlocapi._untar_saved_container("TARFILE", "DESTDIR")
        self.assertTrue(status)

    @mock.patch('udocker.docker.DockerLocalFileAPI._load_repositories')
    @mock.patch('udocker.docker.DockerLocalFileAPI._load_structure')
    @mock.patch('udocker.docker.DockerLocalFileAPI._untar_saved_container')
    @mock.patch('os.makedirs')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_09_load(self, mock_local, mock_msg, mock_exists, mock_futil,
                     mock_makedirs, mock_untar, mock_lstruct, mock_lrepo):
        """Test DockerLocalFileAPI().load()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_exists.return_value = False
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        mock_untar.return_value = False
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        mock_untar.return_value = True
        structure = {}
        mock_lstruct.return_value = structure
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        mock_untar.return_value = True
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_lstruct.return_value = structure
        mock_lrepo.return_value = ["R1", "R2", ]
        status = dlocapi.load("IMAGEFILE")
        self.assertEqual(status, ["R1", "R2", ])

    @mock.patch('time.strftime')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_10_create_container_meta(self, mock_local, mock_msg, mock_futil,
                                      mock_stime):
        """Test DockerLocalFileAPI().create_container_meta()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_futil.return_value.size.return_value = 123
        mock_stime.return_value = "DATE"
        status = dlocapi.create_container_meta("LID")
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

    @mock.patch('udocker.helper.unique.Unique')
    @mock.patch('os.rename')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_11_import_toimage(self, mock_local, mock_msg, mock_exists,
                               mock_futil, mock_rename, mock_unique):
        """Test DockerLocalFileAPI().import_toimage()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_exists.return_value = False
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = "TAGDIR"
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = ""
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = "TAGDIR"
        mock_local.set_version.return_value = False
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = "TAGDIR"
        mock_local.set_version.return_value = True
        mock_unique.return_value.layer_v1.return_value = "LAYERID"
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertEqual(status, "LAYERID")
        self.assertTrue(mock_rename.called)
        #
        mock_rename.reset_mock()
        dlocapi = DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = "TAGDIR"
        mock_local.set_version.return_value = True
        mock_unique.return_value.layer_v1.return_value = "LAYERID"
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG", False)
        self.assertEqual(status, "LAYERID")
        self.assertFalse(mock_rename.called)


if __name__ == '__main__':
    unittest.main()
