#!/usr/bin/env python
"""
udocker unit tests: DockerLocalFileAPI
"""

from unittest import TestCase, main
from unittest.mock import patch, Mock
from udocker.docker import DockerLocalFileAPI
from udocker.config import Config


class DockerLocalFileAPITestCase(TestCase):
    """Test DockerLocalFileAPI() manipulate Docker images."""

    def setUp(self):
        Config().getconf()
        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

    def tearDown(self):
        self.lrepo.stop()

    def test_01_init(self):
        """Test01 DockerLocalFileAPI() constructor."""
        dlocapi = DockerLocalFileAPI(self.local)
        self.assertEqual(dlocapi.localrepo, self.local)

    @patch('udocker.docker.os.listdir')
    @patch('udocker.docker.FileUtil.isdir')
    def test_02__load_structure(self, mock_isdir, mock_ldir):
        """Test02 DockerLocalFileAPI()._load_structure()."""
        res = {'repoconfigs': {}, 'repolayers': {}}
        mock_ldir.return_value = ["xx"]
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        self.assertEqual(structure, res)

        mock_isdir.return_value = False
        mock_ldir.return_value = ["repositories", ]
        self.local.load_json.return_value = {"REPO": "", }
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        res = {'repolayers': {}, 'repoconfigs': {},
               'repositories': {'REPO': ''}}
        self.assertEqual(structure, res)

        mock_isdir.return_value = False
        mock_ldir.return_value = ["manifest.json", ]
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        res = {'repolayers': {}, 'repoconfigs': {},
               'manifest': {'REPO': ''}}
        self.assertEqual(structure, res)

        jfname = "x" * 70 + ".json"
        res = {"repolayers": {},
               "repoconfigs": {jfname: {"json": {"k": "v"},
                                        "json_f": "/tmp/"+jfname}}}
        mock_isdir.return_value = False
        mock_ldir.return_value = [jfname, ]
        self.local.load_json.return_value = {"k": "v"}
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        self.assertEqual(structure, res)

        fname = "x" * 64
        res = {"repolayers": {fname: {"VERSION": {"k": "v"}}},
               "repoconfigs": dict()}
        mock_isdir.return_value = True
        mock_ldir.side_effect = [[fname, ], ["VERSION", ], ]
        self.local.load_json.return_value = {"k": "v"}
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        self.assertEqual(structure, res)

        fname = "x" * 64
        fulllayer = "/tmp/" + fname + "/json"
        res = {"repolayers": {fname: {"json": {"k": "v"},
                                      "json_f": fulllayer}},
               "repoconfigs": dict()}
        mock_isdir.return_value = True
        mock_ldir.side_effect = [[fname, ], ["json", ], ]
        self.local.load_json.return_value = {"k": "v"}
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        self.assertEqual(structure, res)

        fname = "x" * 64
        fulllayer = "/tmp/" + fname + "/layer1"
        res = {"repolayers": {fname: {"layer_f": fulllayer}},
               "repoconfigs": dict()}
        mock_isdir.return_value = True
        mock_ldir.side_effect = [[fname, ], ["layer1", ], ]
        self.local.load_json.return_value = {"k": "v"}
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._load_structure("/tmp")
        self.assertEqual(structure, res)

    def test_03__find_top_layer_id(self):
        """Test03 DockerLocalFileAPI()._find_top_layer_id()."""
        fname = "x" * 64
        fulllayer = "/tmp/" + fname + "/layer1"
        structure = dict()
        dlocapi = DockerLocalFileAPI(self.local)
        structure = dlocapi._find_top_layer_id(structure)
        self.assertEqual(structure, "")

        lid = "12345"
        fulllayer = "/tmp/" + lid + "/json"
        struc = {"repolayers": {lid: {"json": {"parent": "v1"},
                                      "json_f": fulllayer}},
                 "repoconfigs": dict()}
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._find_top_layer_id(struc, "v1")
        self.assertEqual(status, lid)

    def test_04__sorted_layers(self):
        """Test04 DockerLocalFileAPI()._sorted_layers()."""
        lid = "12345"
        fulllayer = "/tmp/" + lid + "/json"
        struc = {"repolayers": {lid: {"json": {"layer": lid},
                                      "json_f": fulllayer}},
                 "repoconfigs": dict()}
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._sorted_layers(struc, lid)
        self.assertEqual(status, [lid])

    def test_05__get_from_manifest(self):
        """Test05 DockerLocalFileAPI()._get_from_manifest()."""
        struc = dict()
        imgtag = "image:tag"
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._get_from_manifest(struc, imgtag)
        self.assertEqual(status, ("", []))

        imgtag = "IMAGE"
        struc = {"manifest": [{"RepoTags": {"IMAGE": {"TAG": "tag"}},
                               "Layers": ["l1", "l2"],
                               "Config": "conf"}]}
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._get_from_manifest(struc, imgtag)
        self.assertEqual(status, ("conf", ["l2", "l1"]))

    @patch('udocker.docker.Msg')
    @patch('udocker.docker.CommonLocalFileApi._move_layer_to_v1repo')
    @patch.object(DockerLocalFileAPI, '_sorted_layers')
    @patch.object(DockerLocalFileAPI, '_find_top_layer_id')
    @patch.object(DockerLocalFileAPI, '_get_from_manifest')
    def test_06__load_image_step2(self, mock_manif, mock_findtop,
                                  mock_sort, mock_mvlayer, mock_msg):
        """Test06 DockerLocalFileAPI()._load_image_step2()."""
        struc = dict()
        imgrepo = "img1"
        tag = "tag1"
        mock_msg.level = 0
        mock_manif.return_value = ("", [])
        mock_findtop.return_value = ""
        mock_sort.return_value = list()
        self.local.save_json.return_value = None
        dlocapi = DockerLocalFileAPI(self.local)
        dlocapi._imagerepo = imgrepo
        status = dlocapi._load_image_step2(struc, imgrepo, tag)
        self.assertEqual(status, ["img1:tag1"])

        lid = "l2"
        fulllayer = "/tmp/" + lid + "/json"
        struc = {"manifest": [{"RepoTags": {"IMAGE": {"TAG": "tag"}},
                               "Layers": ["l2"],
                               "Config": "conf"}],
                 "repolayers": {lid: {"json": {"layer": lid},
                                      "json_f": fulllayer,
                                      "VERSION": "2.0"}},
                 "repoconfigs": {"conf.json": {"json": {"layer": lid},
                                               "json_f": fulllayer}}}
        imgrepo = "img1"
        tag = "tag1"
        mock_manif.return_value = ("conf.json", ["l2"])
        mock_findtop.return_value = "l2"
        mock_sort.return_value = ["l2"]
        mock_mvlayer.side_effect = [True, True]
        self.local.save_json.return_value = None
        dlocapi = DockerLocalFileAPI(self.local)
        dlocapi._imagerepo = imgrepo
        status = dlocapi._load_image_step2(struc, imgrepo, tag)
        self.assertEqual(status, [])

    @patch('udocker.docker.CommonLocalFileApi._load_image')
    def test_07__load_repositories(self, mock_loadi):
        """Test07 DockerLocalFileAPI()._load_repositories()."""
        struct = dict()
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._load_repositories(struct)
        self.assertFalse(status)

        struct = {"repositories": dict()}
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._load_repositories(struct)
        self.assertEqual(status, list())

        structure = {"repositories": {"IMAGE": {"TAG": "tag", }, }, }
        mock_loadi.return_value = ["image:tag"]
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._load_repositories(structure)
        self.assertEqual(status, ["image:tag"])

    @patch('udocker.docker.Msg')
    @patch.object(DockerLocalFileAPI, '_load_repositories')
    @patch.object(DockerLocalFileAPI, '_load_structure')
    @patch('udocker.docker.CommonLocalFileApi._load_image')
    @patch('udocker.docker.Unique')
    def test_08_load(self, mock_unique, mock_loadimg,
                     mock_lstruct, mock_lrepo, mock_msg):
        """Test08 DockerLocalFileAPI().load()."""
        tmp_imgdir = "/tmp/img1"
        mock_msg.level = 0
        mock_lstruct.return_value = dict()
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi.load(tmp_imgdir)
        self.assertEqual(status, [])

        tmp_imgdir = "/tmp/img1"
        fname = "x" * 64
        fulllayer = "/tmp/" + fname + "/layer1"
        struc = {"repolayers": {fname: {"layer_f": fulllayer}},
                 "repositories": ["repo1", "repo2"]}
        mock_lstruct.return_value = struc
        mock_lrepo.return_value = ["repo1", "repo2"]
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi.load(tmp_imgdir)
        self.assertEqual(status, ["repo1", "repo2"])

        struc = {"repolayers": {fname: {"layer_f": fulllayer}},
                 "manifest": dict()}
        mock_lstruct.return_value = struc
        mock_unique.return_value.imagename.return_value = "xyz123"
        mock_unique.return_value.imagetag.return_value = "tag1"
        mock_loadimg.return_value = ["repo1", "repo2"]
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi.load(tmp_imgdir)
        self.assertEqual(status, ["repo1", "repo2"])

    @patch('udocker.docker.FileUtil.putdata')
    @patch('udocker.docker.CommonLocalFileApi.create_container_meta')
    @patch('udocker.docker.FileUtil.copyto')
    @patch('udocker.docker.FileUtil.mkdir')
    @patch('udocker.docker.os.path.exists')
    @patch('udocker.docker.os.path.basename')
    @patch('udocker.docker.FileUtil.rename')
    @patch('udocker.docker.ChkSUM.sha256')
    def test_09__save_image(self, mock_sha256, mock_rename, mock_osbase,
                            mock_exists, mock_mkdir, mock_copyto,
                            mock_meta, mock_put):
        """Test09 DockerLocalFileAPI()._save_image()."""
        imgrepo = "img1"
        tag = "tag1"
        struct = dict()
        tmp_imgdir = "/tmp/img1"
        manifest = dict()
        self.local.cd_imagerepo.return_value = None
        self.local.get_image_attributes.return_value = \
            (manifest, ['/cont/lname1.layer'])
        self.local.save_json.side_effect = [False, True]
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._save_image(imgrepo, tag, struct, tmp_imgdir)
        self.assertFalse(status)

        imgrepo = "IMAGE"
        tag = "tag1"
        fname = "x" * 64
        fulllayer = "/tmp/" + fname + "/layer1"
        struc = {"repolayers": {fname: {"layer_f": fulllayer}},
                 "repositories": {"IMAGE": {"TAG": "tag1", }, }}
        tmp_imgdir = "/tmp/img1"
        manifest = {
            "fsLayers": ({"blobSum": "foolayername"},),
            "history": ({"v1Compatibility": '["foojsonstring"]'},)
        }
        mock_sha256.return_value = \
            "8a29a15cefaeccf6545f7ecf11298f9672d2f0cdaf9e357a95133ac3ad3e1f07"
        mock_rename.return_value = None
        mock_osbase.return_value = "lname1.layer"
        mock_exists.return_value = False
        mock_mkdir.return_value = None
        mock_copyto.return_value = False
        self.local.cd_imagerepo.return_value = None
        self.local.get_image_attributes.return_value = \
            (manifest, ['/cont/lname1.layer'])
        self.local.save_json.side_effect = [True, True]
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._save_image(imgrepo, tag, struc, tmp_imgdir)
        self.assertFalse(status)

        imgrepo = "repo1"
        tag = "tag1"
        fname = "x" * 64
        fulllayer = "/tmp/" + fname + "/lname1.layer"
        manifest = {
            "fsLayers": ({"blobSum": "foolayername"},),
            "history": ({"v1Compatibility": '["foojsonstring"]'},)
        }
        struc = {"repolayers": {fname: {"layer_f": fulllayer}},
                 "repositories": {"repo1": {"TAG": "tag1", }, },
                 "manifest": [manifest]}
        tmp_imgdir = "/tmp/img1"
        mock_sha256.return_value = \
            "8a29a15cefaeccf6545f7ecf11298f9672d2f0cdaf9e357a95133ac3ad3e1f07"
        mock_rename.return_value = None
        mock_osbase.return_value = "lname1.layer"
        mock_exists.return_value = False
        mock_mkdir.return_value = None
        mock_copyto.return_value = True
        mock_meta.return_value = dict()
        self.local.save_json.return_value = True
        mock_put.return_value = True
        self.local.cd_imagerepo.return_value = None
        self.local.get_image_attributes.return_value = \
            (manifest, ['/cont/lname1.layer'])
        self.local.save_json.side_effect = [True, True]
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi._save_image(imgrepo, tag, struc, tmp_imgdir)
        self.assertTrue(status)

    @patch('udocker.docker.Msg')
    @patch.object(DockerLocalFileAPI, '_save_image')
    @patch('udocker.docker.FileUtil.remove')
    @patch('udocker.docker.FileUtil.tar')
    @patch('udocker.docker.os.makedirs')
    @patch('udocker.docker.FileUtil.mktmp')
    def test_10_save(self, mock_mktmp, mock_mkdir, mock_tar,
                     mock_rm, mock_svimg, mock_msg):
        """Test10 DockerLocalFileAPI().save()."""
        imglist = list()
        imgfile = ""
        mock_msg.level = 0
        mock_mktmp.return_value = "/tmp/img1"
        mock_mkdir.return_value = None
        mock_rm.return_value = None
        self.local.save_json.side_effect = [True, True]
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi.save(imglist, imgfile)
        self.assertFalse(status)

        imglist = [("/img1", "tag1"),]
        imgfile = ""
        mock_mktmp.return_value = "/tmp/img1"
        mock_mkdir.return_value = None
        mock_rm.return_value = None
        mock_svimg.return_value = True
        mock_tar.return_value = False
        self.local.save_json.side_effect = [True, True]
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi.save(imglist, imgfile)
        self.assertFalse(status)

        imglist = [("/img1", "tag1"),]
        imgfile = ""
        mock_mktmp.return_value = "/tmp/img1"
        mock_mkdir.return_value = None
        mock_rm.return_value = None
        mock_svimg.return_value = True
        mock_tar.return_value = True
        self.local.save_json.side_effect = [True, True]
        dlocapi = DockerLocalFileAPI(self.local)
        status = dlocapi.save(imglist, imgfile)
        self.assertTrue(status)


if __name__ == '__main__':
    main()
