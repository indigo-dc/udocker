#!/usr/bin/env python
"""
udocker unit tests: DockerLocalFileAPI
"""

from unittest import TestCase, main
from udocker.docker import DockerLocalFileAPI
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class DockerLocalFileAPITestCase(TestCase):
    """Test DockerLocalFileAPI() manipulate Docker images."""

    def setUp(self):
        self.conf = Config().getconf()
        # self.conf['cmd'] = "/bin/bash"
        # self.conf['cpu_affinity_exec_tools'] = \
        #     (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        # self.conf['valid_host_env'] = "HOME"
        # self.conf['username'] = "user"
        # self.conf['userhome'] = "/"
        # self.conf['oskernel'] = "4.8.13"
        # self.conf['location'] = ""
        # self.conf['keystore'] = "KEYSTORE"
        # self.conf['osversion'] = "OSVERSION"
        # self.conf['arch'] = "ARCH"
        self.local = LocalRepository(self.conf)

    def tearDown(self):
        pass

    # @patch('udocker.docker.CommonLocalFileApi')
    # def test_01_init(self, mock_common):
    #     """Test01 DockerLocalFileAPI() constructor."""
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     self.assertTrue(mock_common.called)

    @patch('udocker.docker.os.listdir')
    @patch('udocker.docker.os.path.isdir')
    @patch('udocker.container.localrepo.LocalRepository.load_json', autospec=True)
    def test_02__load_structure(self, mock_ljson, mock_isdir, mock_ldir):
        """Test02 DockerLocalFileAPI()._load_structure()."""
        mock_isdir.return_value = False
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        self.assertEqual(structure, {'repoconfigs': {}, 'repolayers': {}})

        mock_isdir.return_value = True
        mock_ldir.return_value = ["repositories", ]
        mock_ljson.return_value = {"REPO": "", }
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        expected = {'repolayers': {}, 'repoconfigs': {}, 'repositories': {'REPO': ''}}
        self.assertEqual(structure, expected)

        mock_isdir.return_value = True
        mock_ldir.return_value = ["manifest.json", ]
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        expected = {'repolayers': {}, 'repoconfigs': {}, 'manifest': {'REPO': ''}}
        self.assertEqual(structure, expected)

        mock_isdir.return_value = True
        mock_ldir.return_value = ["x" * 64 + ".json", ]
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        # expected = {'layers': {}}
        # self.assertEqual(structure, expected)

        mock_isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["VERSION", ], ]
        mock_ljson.return_value = {"X": "", }
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        # expected = {'layers': {"x" * 64: {'VERSION': {'X': ''}}}}
        # self.assertEqual(structure, expected)

        mock_isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["json", ], ]
        mock_ljson.return_value = {"X": "", }
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        # expected = {'layers': {"x" * 64: {'json': {'X': ''},
        #                                   'json_f': '/tmp/' + "x" * 64 + '/json'}}}
        # self.assertEqual(structure, expected)

        mock_isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["layer", ], ]
        mock_ljson.return_value = {"X": "", }
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        # expected = {'layers': {"x" * 64: {
        #     'layer_f': '/tmp/' + "x" * 64 + '/layer'}}}
        # self.assertEqual(structure, expected)

    # def test_03__find_top_layer_id(self):
    #     """Test03 DockerLocalFileAPI()._find_top_layer_id()."""
    #     dlocapi = DockerLocalFileAPI(self.local)

    # def test_04__sorted_layers(self):
    #     """Test04 DockerLocalFileAPI()._sorted_layers()."""
    #     dlocapi = DockerLocalFileAPI(self.local)

    # def test_05__get_from_manifest(self):
    #     """Test05 DockerLocalFileAPI()._get_from_manifest()."""
    #     dlocapi = DockerLocalFileAPI(self.local)

    # def test_06__load_image_step2(self):
    #     """Test06 DockerLocalFileAPI()._load_image_step2()."""
    #     dlocapi = DockerLocalFileAPI(self.local)

    @patch.object(DockerLocalFileAPI, '_load_image')
    def test_07__load_repositories(self, mock_loadi):
        """Test07 DockerLocalFileAPI()._load_repositories()."""
        structure = {}
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._load_repositories(structure)
        self.assertFalse(status)

        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_loadi.return_value = False
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._load_repositories(structure)
        self.assertFalse(status)

        # structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        # mock_loadi.return_value = True
        # dlocapi = DockerLocalFileAPI(self.local)
        # status = dlocapi._load_repositories(structure)
        # self.assertTrue(status)

    @patch.object(DockerLocalFileAPI, '_load_repositories')
    @patch.object(DockerLocalFileAPI, '_load_structure')
    @patch.object(DockerLocalFileAPI, '_untar_saved_container')
    @patch('udocker.docker.os.makedirs')
    @patch('udocker.docker.FileUtil.mktmp')
    @patch('udocker.docker.os.path.exists')
    def test_08_load(self, mock_exists, mock_mktmp,
                     mock_makedirs, mock_untar, mock_lstruct, mock_lrepo):
        """Test08 DockerLocalFileAPI().load()."""
        mock_exists.return_value = False
        mock_mktmp.return_value = "tmpfile"
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)

        mock_exists.return_value = True
        mock_mktmp.return_value = "tmpfile"
        mock_untar.return_value = False
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)

        mock_exists.return_value = True
        mock_mktmp.return_value = "tmpfile"
        mock_untar.return_value = True
        structure = {}
        mock_lstruct.return_value = structure
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)

        mock_exists.return_value = True
        mock_mktmp.return_value = "tmpfile"
        mock_untar.return_value = True
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_lstruct.return_value = structure
        mock_lrepo.return_value = ["R1", "R2", ]
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi.load("IMAGEFILE")
        self.assertEqual(status, ["R1", "R2", ])

    # def test_09__save_image(self):
    #     """Test09 DockerLocalFileAPI()._save_image()."""
    #     dlocapi = DockerLocalFileAPI(self.local)

    # def test_10_save(self):
    #     """Test10 DockerLocalFileAPI().save()."""
    #     dlocapi = DockerLocalFileAPI(self.local)






    ### NON existent methods, removed or moved to another class
    # @patch('udocker.docker.os.rename')
    # def test_05__copy_layer_to_repo(self, mock_rename):
    #     """Test DockerLocalFileAPI()._copy_layer_to_repo()."""
    #     self.local.layersdir = ""
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi._copy_layer_to_repo("/", "LID")
    #     self.assertFalse(status)

    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi._copy_layer_to_repo("/xxx.json", "LID")
    #     self.assertTrue(status)

    # @patch('udocker.container.localrepo.LocalRepository.set_version', autospec=True)
    # @patch('udocker.container.localrepo.LocalRepository.setup_tag', autospec=True)
    # @patch('udocker.container.localrepo.LocalRepository.cd_imagerepo', autospec=True)
    # @patch('udocker.container.localrepo.LocalRepository.sorted_layers', autospec=True)
    # @patch('udocker.container.localrepo.LocalRepository.find_top_layer_id', autospec=True)
    # @patch.object(DockerLocalFileAPI, '_copy_layer_to_repo')
    # def test_06__load_image(self, mock_copylayer, mock_findtop, mock_slayers, 
    #                         mock_cdimg, mock_settag, mock_setversion):
    #     """Test DockerLocalFileAPI()._load_image()."""
    #     mock_cdimg.return_value = True
    #     structure = {}
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi._load_image(structure, "IMAGE", "TAG")
    #     # self.assertFalse(status)

    #     mock_cdimg.return_value = False
    #     mock_settag.return_value = ""
    #     structure = {}
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi._load_image(structure, "IMAGE", "TAG")
    #     self.assertFalse(status)

    #     mock_cdimg.return_value = False
    #     mock_settag.return_value = "/dir"
    #     mock_setversion.return_value = False
    #     structure = {}
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi._load_image(structure, "IMAGE", "TAG")
    #     self.assertFalse(status)

    #     mock_cdimg.return_value = False
    #     mock_settag.return_value = "/dir"
    #     mock_setversion.return_value = True
    #     mock_findtop.return_value = "TLID"
    #     mock_slayers.return_value = []
    #     structure = {}
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi._load_image(structure, "IMAGE", "TAG")
    #     self.assertEqual(status, ['IMAGE:TAG'])

    #     mock_cdimg.return_value = False
    #     mock_settag.return_value = "/dir"
    #     mock_setversion.return_value = True
    #     mock_findtop.return_value = "TLID"
    #     mock_slayers.return_value = ["LID", ]
    #     mock_copylayer.return_value = False
    #     structure = {'layers': {'LID': {'VERSION': "1.0",
    #                                     'json_f': "f1",
    #                                     'layer_f': "f1", }, }, }
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi._load_image(structure, "IMAGE", "TAG")
    #     self.assertFalse(status)

    #     mock_cdimg.return_value = False
    #     mock_settag.return_value = "/dir"
    #     mock_setversion.return_value = True
    #     mock_findtop.return_value = "TLID"
    #     mock_slayers.return_value = ["LID", ]
    #     mock_copylayer.return_value = True
    #     structure = {'layers': {'LID': {'VERSION': "1.0",
    #                                     'json_f': "f1",
    #                                     'layer_f': "f1", }, }, }
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi._load_image(structure, "IMAGE", "TAG")
    #     self.assertEqual(status, ['IMAGE:TAG'])


    # @patch('udocker.docker.subprocess.call')
    # def test_08__untar_saved_container(self, mock_call):
    #     """Test DockerLocalFileAPI()._untar_saved_container()."""
    #     mock_call.return_value = True
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi._untar_saved_container("TARFILE", "DESTDIR")
    #     self.assertFalse(status)

    #     mock_call.return_value = False
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi._untar_saved_container("TARFILE", "DESTDIR")
    #     self.assertTrue(status)


    # @patch('udocker.docker.time.strftime')
    # @patch('udocker.docker.FileUtil.size')
    # def test_10_create_container_meta(self, mock_size, mock_stime):
    #     """Test DockerLocalFileAPI().create_container_meta()."""
    #     mock_size.return_value = 123
    #     mock_stime.return_value = "DATE"
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi.create_container_meta("LID")
    #     meta = {'comment': 'created by udocker',
    #             'created': 'DATE',
    #             'config': {'Env': None, 'Hostname': '', 'Entrypoint': None,
    #                        'PortSpecs': None, 'Memory': 0, 'OnBuild': None,
    #                        'OpenStdin': False, 'MacAddress': '', 'Cpuset': '',
    #                        'NetworkDisable': False, 'User': '',
    #                        'AttachStderr': False, 'AttachStdout': False,
    #                        'Cmd': None, 'StdinOnce': False, 'CpusShares': 0,
    #                        'WorkingDir': '', 'AttachStdin': False,
    #                        'Volumes': None, 'MemorySwap': 0, 'Tty': False,
    #                        'Domainname': '', 'Image': '', 'Labels': None,
    #                        'ExposedPorts': None},
    #             'container_config': {'Env': None, 'Hostname': '',
    #                                  'Entrypoint': None, 'PortSpecs': None,
    #                                  'Memory': 0, 'OnBuild': None,
    #                                  'OpenStdin': False, 'MacAddress': '',
    #                                  'Cpuset': '', 'NetworkDisable': False,
    #                                  'User': '', 'AttachStderr': False,
    #                                  'AttachStdout': False, 'Cmd': None,
    #                                  'StdinOnce': False, 'CpusShares': 0,
    #                                  'WorkingDir': '', 'AttachStdin': False,
    #                                  'Volumes': None, 'MemorySwap': 0,
    #                                  'Tty': False, 'Domainname': '',
    #                                  'Image': '', 'Labels': None,
    #                                  'ExposedPorts': None},
    #             'architecture': 'ARCH', 'os': 'OSVERSION',
    #             'id': 'LID', 'size': 123}
    #     self.assertEqual(status, meta)

    # @patch('udocker.container.localrepo.LocalRepository.set_version', autospec=True)
    # @patch('udocker.container.localrepo.LocalRepository.setup_tag', autospec=True)
    # @patch('udocker.container.localrepo.LocalRepository.cd_imagerepo', autospec=True)
    # @patch('udocker.docker.Unique.layer_v1')
    # @patch('udocker.docker.os.rename')
    # @patch('udocker.docker.FileUtil')
    # @patch('udocker.docker.os.path.exists')
    # def test_11_import_toimage(self, mock_exists, mock_futil, mock_rename,
    #                            mock_v1, mock_cdimg, mock_settag,
    #                            mock_setversion):
    #     """Test DockerLocalFileAPI().import_toimage()."""
    #     mock_exists.return_value = False
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
    #     self.assertFalse(status)

    #     mock_exists.return_value = True
    #     mock_cdimg.return_value = "TAGDIR"
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
    #     self.assertFalse(status)

    #     mock_exists.return_value = True
    #     mock_cdimg.return_value = ""
    #     mock_settag.return_value = ""
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
    #     self.assertFalse(status)

    #     mock_exists.return_value = True
    #     mock_cdimg.return_value = ""
    #     mock_settag.return_value = "TAGDIR"
    #     mock_setversion.return_value = False
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
    #     self.assertFalse(status)

    #     mock_exists.return_value = True
    #     mock_cdimg.return_value = ""
    #     mock_settag.return_value = "TAGDIR"
    #     mock_setversion.return_value = True
    #     mock_v1.return_value = "LAYERID"
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
    #     self.assertEqual(status, "LAYERID")
    #     self.assertTrue(mock_rename.called)

    #     mock_rename.reset_mock()
    #     mock_exists.return_value = True
    #     mock_cdimg.return_value = ""
    #     mock_settag.return_value = "TAGDIR"
    #     mock_setversion.return_value = True
    #     mock_v1.return_value = "LAYERID"
    #     dlocapi = DockerLocalFileAPI(self.local)
    #     status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG", False)
    #     self.assertEqual(status, "LAYERID")
    #     self.assertFalse(mock_rename.called)


if __name__ == '__main__':
    main()
