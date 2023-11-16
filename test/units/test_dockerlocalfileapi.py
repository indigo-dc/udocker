#!/usr/bin/env python
"""
udocker unit tests: DockerLocalFileAPI
"""
import os
import random

import pytest

from udocker.docker import DockerLocalFileAPI
from udocker.helper.unique import Unique
from udocker.utils.fileutil import FileUtil


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.docker.LOG')


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker, container_id):
    mocker_local_repo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mocker_local_repo.container_id = container_id
    mocker_local_repo.container_dir.return_value = "/.udocker/containers/" + container_id
    return mocker_local_repo


@pytest.fixture(autouse=True)
def docker_local_api(localrepo):
    return DockerLocalFileAPI(localrepo)


#
def test_01_init(docker_local_api, localrepo):
    """Test01 DockerLocalFileAPI() constructor."""
    assert docker_local_api.localrepo == localrepo
    assert docker_local_api._imagerepo is None


# FIXME: This test is broken
# @pytest.mark.parametrize("listdir_output, isdir_output, load_json_output, expected_structure", [
#     (["xx"], False, None, {"repolayers": {}, "repoconfigs": {}}),
#     (["repositories"], False, {"REPO": ""}, {"repolayers": {}, "repoconfigs": {}, "repositories": {"REPO": ""}}),
#     (["manifest.json"], False, {"REPO": ""}, {"repolayers": {}, "repoconfigs": {}, "manifest": {"REPO": ""}}),
#     (["x" * 70 + ".json"], False, {"k": "v"}, {"repolayers": {}, "repoconfigs": {
#         "x" * 70 + ".json": {"json": {"k": "v"}, "json_f": "/tmp/" + "x" * 70 + ".json"}}}),
#     (["x" * 64], True, {"k": "v"}, {"repolayers": {"x" * 64: {"VERSION": {"k": "v"}}}, "repoconfigs": {}}),
#     (["x" * 64], True, {"k": "v"},
#      {"repolayers": {"x" * 64: {"json": {"k": "v"}, "json_f": "/tmp/" + "x" * 64 + "/json"}}, "repoconfigs": {}}),
#     (
#             ["x" * 64], True, None,
#             {"repolayers": {"x" * 64: {"layer_f": "/tmp/" + "x" * 64 + "/layer1"}}, "repoconfigs": {}}),
# ])
# def test_02__load_structure(mocker, docker_local_api, localrepo, logger, listdir_output, isdir_output, load_json_output,
#                             expected_structure):
#     """Test02 DockerLocalFileAPI()._load_structure()."""
#     tmp_imagedir = "/tmp"
#     mocker.patch.object(os, 'listdir', return_value=listdir_output)
#     mocker.patch.object(FileUtil, 'isdir', return_value=isdir_output)
#     mocker.patch.object(localrepo, 'load_json', return_value=load_json_output)
#     structure = docker_local_api._load_structure(tmp_imagedir)
#
#     assert structure == expected_structure


#         res = {'repoconfigs': {}, 'repolayers': {}}
#         mock_ldir.return_value = ["xx"]
#         dlocapi = DockerLocalFileAPI(self.local)
#         structure = dlocapi._load_structure("/tmp")
#         self.assertEqual(structure, res)
#
#         mock_isdir.return_value = False
#         mock_ldir.return_value = ["repositories", ]
#         self.local.load_json.return_value = {"REPO": "", }
#         dlocapi = DockerLocalFileAPI(self.local)
#         structure = dlocapi._load_structure("/tmp")
#         res = {'repolayers': {}, 'repoconfigs': {},
#                'repositories': {'REPO': ''}}
#         self.assertEqual(structure, res)
#
#         mock_isdir.return_value = False
#         mock_ldir.return_value = ["manifest.json", ]
#         dlocapi = DockerLocalFileAPI(self.local)
#         structure = dlocapi._load_structure("/tmp")
#         res = {'repolayers': {}, 'repoconfigs': {},
#                'manifest': {'REPO': ''}}
#         self.assertEqual(structure, res)
#
#         jfname = "x" * 70 + ".json"
#         res = {"repolayers": {},
#                "repoconfigs": {jfname: {"json": {"k": "v"},
#                                         "json_f": "/tmp/"+jfname}}}
#         mock_isdir.return_value = False
#         mock_ldir.return_value = [jfname, ]
#         self.local.load_json.return_value = {"k": "v"}
#         dlocapi = DockerLocalFileAPI(self.local)
#         structure = dlocapi._load_structure("/tmp")
#         self.assertEqual(structure, res)
#
#         fname = "x" * 64
#         res = {"repolayers": {fname: {"VERSION": {"k": "v"}}},
#                "repoconfigs": dict()}
#         mock_isdir.return_value = True
#         mock_ldir.side_effect = [[fname, ], ["VERSION", ], ]
#         self.local.load_json.return_value = {"k": "v"}
#         dlocapi = DockerLocalFileAPI(self.local)
#         structure = dlocapi._load_structure("/tmp")
#         self.assertEqual(structure, res)
#
#         fname = "x" * 64
#         fulllayer = "/tmp/" + fname + "/json"
#         res = {"repolayers": {fname: {"json": {"k": "v"},
#                                       "json_f": fulllayer}},
#                "repoconfigs": dict()}
#         mock_isdir.return_value = True
#         mock_ldir.side_effect = [[fname, ], ["json", ], ]
#         self.local.load_json.return_value = {"k": "v"}
#         dlocapi = DockerLocalFileAPI(self.local)
#         structure = dlocapi._load_structure("/tmp")
#         self.assertEqual(structure, res)
#
#         fname = "x" * 64
#         fulllayer = "/tmp/" + fname + "/layer1"
#         res = {"repolayers": {fname: {"layer_f": fulllayer}},
#                "repoconfigs": dict()}
#         mock_isdir.return_value = True
#         mock_ldir.side_effect = [[fname, ], ["layer1", ], ]
#         self.local.load_json.return_value = {"k": "v"}
#         dlocapi = DockerLocalFileAPI(self.local)
#         structure = dlocapi._load_structure("/tmp")
#         self.assertEqual(structure, res)
#

# @pytest.mark.parametrize("structure, my_layer_id, expected_top_layer_id", [
#     # Empty repolayers
#     ({"repolayers": {}}, "", ""),
#
#     # Single layer
#     ({"repolayers": {"layer1": {"json": {}}}}, "", "layer1"),
#
#     # Multiple layers
#     ({"repolayers": {"layer1": {"json": {"parent": "layer2"}},
#                      "layer2": {"json": {}}}}, "", "layer2"),
#
#     # Non-existent my_layer_id
#     ({"repolayers": {"layer1": {"json": {}}}}, "layer3", ""),
#
#     # Specified my_layer_id
#     ({"repolayers": {"layer1": {"json": {"parent": "layer2"}},
#                      "layer2": {"json": {"parent": "layer3"}},
#                      "layer3": {"json": {}}}}, "layer1", "layer3"),
# ])
@pytest.mark.parametrize("structure, my_layer_id, expected_top_layer_id", [
    ({}, "", ""),
    ({"repolayers": {"12345": {"json": {"parent": "v1"}, "json_f": "/tmp/12345/json"}}, "repoconfigs": {}}, "v1",
     "12345"),
    ({"repolayers": {"layer1": {"json": {}}}, "repoconfigs": {}}, "", "layer1"),
    ({"repolayers": {"layer1": {"json": {"parent": "layer2"}},
                     "layer2": {"json": {}}}, "repoconfigs": {}}, "", "layer1"),
    ({"repolayers": {"layer1": {"json": {"parent": "layer2"}},
                     "layer2": {"json": {"parent": "layer3"}},
                     "layer3": {"json": {}}}, "repoconfigs": {}}, "layer1", "layer1"),
], ids=["empty_structure", "specific_layer_id_with_parent", "layer_with_no_parent", "nested_layers", "layer_chain"])
def test_03__find_top_layer_id(docker_local_api, structure, my_layer_id, expected_top_layer_id):
    """Test03 DockerLocalFileAPI()._find_top_layer_id()."""
    top_layer_id = docker_local_api._find_top_layer_id(structure, my_layer_id)
    assert top_layer_id == expected_top_layer_id


@pytest.mark.parametrize("structure, top_layer_id, expected_sorted_layers", [
    ({"repolayers": {"layer1": {"json": {}}}}, "layer1", ["layer1"]),
    ({"repolayers": {"layer1": {"json": {"parent": "layer2"}},
                     "layer2": {"json": {"parent": "layer3"}},
                     "layer3": {"json": {}}}}, "layer1", ["layer1", "layer2", "layer3"]),
    ({"repolayers": {"layer1": {"json": {"parent": "layer4"}},
                     "layer4": {"json": {"parent": {}}}}}, "layer1", ['layer1', 'layer4']),
    # ({"repolayers": {"layer1": {"json": {"parent": "layer4"}},
    #                  "layer2": {"json": {}}}}, "layer1", ["layer1"]),
    ({"repolayers": {"layer1": {"json": {}}}}, "layer1", ["layer1"]),
    ({"repolayers": {"layer1": {"json": {"parent": "layer2"}},
                     "layer2": {"json": {"parent": "layer3"}},
                     "layer3": {"json": {}}}}, "layer2", ["layer2", "layer3"]),
], ids=["single_layer", "multiple_layers", "non_existent_parent", "layer_with_no_parent", "multiple_layers_middle", ])
def test_04__sorted_layers(docker_local_api, structure, top_layer_id, expected_sorted_layers):
    """Test04 DockerLocalFileAPI()._sorted_layers()."""
    sorted_layers = docker_local_api._sorted_layers(structure, top_layer_id)
    assert sorted_layers == expected_sorted_layers


@pytest.mark.parametrize("structure, imagetag, expected_result", [
    ({}, "image:tag", ("", [])),
    ({"manifest": [{"RepoTags": ["IMAGE:tag"], "Layers": ["l1", "l2"], "Config": "conf"}]},
     "IMAGE:tag", ("conf", ["l2", "l1"])),
    ({"manifest": [{"RepoTags": ["other:image"], "Layers": ["l1", "l2"], "Config": "conf"}]},
     "IMAGE:tag", ("", [])),
    ({"manifest": [{"RepoTags": ["other:image"], "Layers": ["layer1/layer.tar"], "Config": "config.json"},
                   {"RepoTags": ["image:tag"], "Layers": ["layer2/layer.tar"], "Config": "config2.json"}]},
     "image:tag", ("config2.json", ["layer2/layer.tar"])),
], ids=["empty_structure", "valid_manifest", "non_matching_tag", "multiple_entries"])
def test_05__get_from_manifest(docker_local_api, structure, imagetag, expected_result):
    """Test05 DockerLocalFileAPI()._get_from_manifest()."""
    config, layers = docker_local_api._get_from_manifest(structure, imagetag)
    assert (config, layers) == expected_result


@pytest.mark.parametrize("from_manifest, structure, imagerepo, tag, move_layer_to_v1, expected", [
    ((None, None), {}, "img1", "tag1", [True, True], ['img1:tag1']),
    (("conf.json", ["l2"]),
     {"manifest": [{"RepoTags": ["IMAGE:tag"], "Layers": ["l2"], "Config": "conf.json"}],
      "repolayers": {
          "l2": {"json": {"layer": "l2"}, "json_f": "/tmp/l2/json", "layer_f": "/tmp/l2/layer", "VERSION": "1.0"}},
      "repoconfigs": {"conf.json": {"json": {"layer": "l2"}, "json_f": "/tmp/l2/json"}}},
     "img1", "tag1", [True, True, True], ["img1:tag1"]),
    (("conf.json", ["l2"]),
     {"manifest": [{"RepoTags": ["IMAGE:tag"], "Layers": ["l2"], "Config": "conf.json"}],
      "repolayers": {
          "l2": {"json": {"layer": "l2"}, "json_f": "/tmp/l2/json", "layer_f": "/tmp/l2/layer", "VERSION": "1.0"}},
      "repoconfigs": {"conf.json": {"json": {"layer": "l2"}, "json_f": "/tmp/l2/json"}}},
     "img1", "tag1", [True, True, False], []),
    (("conf.json", ["l2"]), {"manifest": [{"RepoTags": ["IMAGE:tag"], "Layers": ["l2"], "Config": "conf.json"}],
                             "repolayers": {
                                 "l2": {"json": {"layer": "l2"}, "json_f": "/tmp/l2/json", "VERSION": "2.0"}},
                             "repoconfigs": {"conf.json": {"json": {"layer": "l2"}, "json_f": "/tmp/l2/json"}}},
     "img1", "tag1", [True, True], []),
], ids=["empty_structure", "valid_manifest", "valid_manifest_failed_copy", "layer_version_mismatch"])
def test_06__load_image_step2(mocker, docker_local_api, from_manifest, structure, imagerepo, tag, move_layer_to_v1,
                              expected):
    """Test06 DockerLocalFileAPI()._load_image_step2()."""
    mocker.patch.object(docker_local_api, '_get_from_manifest', return_value=from_manifest)
    mocker.patch.object(docker_local_api, '_find_top_layer_id', return_value="l2")
    mocker.patch.object(docker_local_api, '_sorted_layers', return_value=["l2"] if structure else [])
    mocker.patch.object(docker_local_api, '_move_layer_to_v1repo', side_effect=move_layer_to_v1)
    mocker.patch.object(docker_local_api.localrepo, 'save_json', return_value=None)
    docker_local_api._imagerepo = imagerepo

    result = docker_local_api._load_image_step2(structure, imagerepo, tag)
    assert result == expected


@pytest.mark.parametrize("structure, expected_loaded_repositories", [
    ({}, False),
    ({"repositories": {}}, []),
    ({"repositories": {"repo1": ["tag1", "tag2"], "repo2": ["tag3"]}}, ["repo1:tag1", "repo1:tag2", "repo2:tag3"]),
    ({"repositories": {"": ["tag1"], "repo2": [""]}}, []),
], ids=["empty_structure", "valid_repositories", "invalid_repositories", "multiple_repositories"])
def test_07__load_repositories(mocker, docker_local_api, structure, expected_loaded_repositories):
    """Test07 DockerLocalFileAPI()._load_repositories()."""
    mocker.patch.object(docker_local_api, '_load_image', side_effect=lambda image, repo, tag: [f"{repo}:{tag}"])
    result = docker_local_api._load_repositories(structure)
    assert result == expected_loaded_repositories


@pytest.mark.parametrize("tmp_imagedir, imagerepo, load_structure_result, expected", [
    ("/tmp/img1", None, None, []),
    ("/tmp/img1", None, {"repositories": {"repo1": ["tag1"]}}, ["repo1:tag1"]),
    ("/tmp/img1", None, {"repoconfigs": {}, "repolayers": {}}, ["generated_imagerepo:generated_tag"]),
    ("/tmp/img1", "provided_repo", {"repoconfigs": {}, "repolayers": {}}, ["provided_repo:generated_tag"]),
], ids=["empty image structure", "structure with repositories",
        "structure without repositories, no provided image repo", "valid?"])
def test_08_load(mocker, docker_local_api, tmp_imagedir, imagerepo, load_structure_result, expected):
    """Test08 DockerLocalFileAPI().load()."""
    mocker.patch.object(docker_local_api, '_load_structure', return_value=load_structure_result)
    mocker.patch.object(docker_local_api, '_load_repositories', side_effect=lambda s: ["repo1:tag1"])
    mocker.patch.object(docker_local_api, '_load_image', side_effect=lambda s, r, t: [f"{r}:{t}"])
    mocker.patch.object(Unique, 'imagename', return_value="generated_imagerepo")
    mocker.patch.object(Unique, 'imagetag', return_value="generated_tag")

    result = docker_local_api.load(tmp_imagedir, imagerepo)
    assert result == expected


#         tmp_imgdir = "/tmp/img1"
#         mock_lstruct.return_value = dict()
#         dlocapi = DockerLocalFileAPI(self.local)
#         status = dlocapi.load(tmp_imgdir)
#         self.assertEqual(status, [])
#
#         tmp_imgdir = "/tmp/img1"
#         fname = "x" * 64
#         fulllayer = "/tmp/" + fname + "/layer1"
#         struc = {"repolayers": {fname: {"layer_f": fulllayer}},
#                  "repositories": ["repo1", "repo2"]}
#         mock_lstruct.return_value = struc
#         mock_lrepo.return_value = ["repo1", "repo2"]
#         dlocapi = DockerLocalFileAPI(self.local)
#         status = dlocapi.load(tmp_imgdir)
#         self.assertEqual(status, ["repo1", "repo2"])
#
#         struc = {"repolayers": {fname: {"layer_f": fulllayer}},
#                  "manifest": dict()}
#         mock_lstruct.return_value = struc
#         mock_unique.return_value.imagename.return_value = "xyz123"
#         mock_unique.return_value.imagetag.return_value = "tag1"
#         mock_loadimg.return_value = ["repo1", "repo2"]
#         dlocapi = DockerLocalFileAPI(self.local)
#         status = dlocapi.load(tmp_imgdir)
#         self.assertEqual(status, ["repo1", "repo2"])
#


# FIXME: This test is broken
# @pytest.mark.parametrize("save_json_results, copyto_result, putdata_result, expected_result", [
#     ([False], True, True, False), # save_json fails
#     ([True], False, True, False),  # copyto fails
#     ([True, True, False], True, True, False), # save JSON fails
#     ([True, True, True], True, False, False), # VERSION file
#     ([True, True, True], True, True, True), # Successful
# ])
# def test_09__save_image(mocker, docker_local_api, save_json_results, copyto_result, putdata_result, expected_result):
#     """Test09 DockerLocalFileAPI()._save_image()."""
#     mocker.patch.object(docker_local_api.localrepo, 'cd_imagerepo')
#     mocker.patch.object(docker_local_api.localrepo, 'get_image_attributes',
#                         return_value=("container_json", ["layer_f"]))
#     save_json_mock = mocker.patch.object(docker_local_api.localrepo, 'save_json', side_effect=save_json_results)
#     mocker.patch.object(FileUtil, 'rename')
#     copyto_mock = mocker.patch.object(FileUtil, 'copyto', return_value=copyto_result)
#     putdata_mock = mocker.patch.object(FileUtil, 'putdata', return_value=putdata_result)
#
#     imagerepo = "imagerepo"
#     tag = "tag"
#     structure = {"repositories": {}, "manifest": []}
#     tmp_imagedir = "/tmp/tmp_imagedir"
#
#     result = docker_local_api._save_image(imagerepo, tag, structure, tmp_imagedir)
#
#     assert result == expected_result


#         imgrepo = "img1"
#         tag = "tag1"
#         struct = dict()
#         tmp_imgdir = "/tmp/img1"
#         manifest = dict()
#         self.local.cd_imagerepo.return_value = None
#         self.local.get_image_attributes.return_value = (manifest, ['/cont/lname1.layer'])
#         self.local.save_json.side_effect = [False, True]
#         dlocapi = DockerLocalFileAPI(self.local)
#         status = dlocapi._save_image(imgrepo, tag, struct, tmp_imgdir)
#         self.assertFalse(status)
#
#         imgrepo = "IMAGE"
#         tag = "tag1"
#         fname = "x" * 64
#         fulllayer = "/tmp/" + fname + "/layer1"
#         struc = {"repolayers": {fname: {"layer_f": fulllayer}},
#                  "repositories": {"IMAGE": {"TAG": "tag1", }, }}
#         tmp_imgdir = "/tmp/img1"
#         manifest = {
#             "fsLayers": ({"blobSum": "foolayername"},),
#             "history": ({"v1Compatibility": '["foojsonstring"]'},)
#         }
#         mock_sha256.return_value = "8a29a15cefaeccf6545f7ecf11298f9672d2f0cdaf9e357a95133ac3ad3e1f07"
#         mock_rename.return_value = None
#         mock_osbase.return_value = "lname1.layer"
#         mock_exists.return_value = False
#         mock_mkdir.return_value = None
#         mock_copyto.return_value = False
#         self.local.cd_imagerepo.return_value = None
#         self.local.get_image_attributes.return_value = (manifest, ['/cont/lname1.layer'])
#         self.local.save_json.side_effect = [True, True]
#         dlocapi = DockerLocalFileAPI(self.local)
#         status = dlocapi._save_image(imgrepo, tag, struc, tmp_imgdir)
#         self.assertFalse(status)
#
#         imgrepo = "repo1"
#         tag = "tag1"
#         fname = "x" * 64
#         fulllayer = "/tmp/" + fname + "/lname1.layer"
#         manifest = {
#             "fsLayers": ({"blobSum": "foolayername"},),
#             "history": ({"v1Compatibility": '["foojsonstring"]'},)
#         }
#         struc = {"repolayers": {fname: {"layer_f": fulllayer}},
#                  "repositories": {"repo1": {"TAG": "tag1", }, },
#                  "manifest": [manifest]}
#         tmp_imgdir = "/tmp/img1"
#         mock_sha256.return_value = "8a29a15cefaeccf6545f7ecf11298f9672d2f0cdaf9e357a95133ac3ad3e1f07"
#         mock_rename.return_value = None
#         mock_osbase.return_value = "lname1.layer"
#         mock_exists.return_value = False
#         mock_mkdir.return_value = None
#         mock_copyto.return_value = True
#         mock_meta.return_value = dict()
#         self.local.save_json.return_value = True
#         mock_put.return_value = True
#         self.local.cd_imagerepo.return_value = None
#         self.local.get_image_attributes.return_value = (manifest, ['/cont/lname1.layer'])
#         self.local.save_json.side_effect = [True, True]
#         dlocapi = DockerLocalFileAPI(self.local)
#         status = dlocapi._save_image(imgrepo, tag, struc, tmp_imgdir)
#         self.assertTrue(status)
#
#     @patch.object(DockerLocalFileAPI, '_save_image')
#     @patch('udocker.docker.FileUtil.remove')
#     @patch('udocker.docker.FileUtil.tar')
#     @patch('udocker.docker.os.makedirs')
#     @patch('udocker.docker.FileUtil.mktmp')

@pytest.mark.parametrize("make_dirs_result, save_image_results, tar_result, imagetag_list, expected", [
    (False, [], True, [("imagerepo1", "tag1")], False),
    (None, [False], True, [("imagerepo1", "tag1")], False),
    (None, [True], False, [("imagerepo1", "tag1")], False),
    (None, [True], True, [("imagerepo1", "tag1")], True),
    (None, [], True, [], False),
], ids=["make_dirs_failure", "save_image_failure", "tar_failure", "successful_save", "empty_imagetag_list"])
def test_10_save(mocker, docker_local_api, logger, make_dirs_result, save_image_results, tar_result, imagetag_list,
                 expected):
    """Test10 DockerLocalFileAPI().save()."""
    mocker.patch.object(docker_local_api, '_save_image', side_effect=save_image_results)
    mocker.patch.object(FileUtil, 'tar', return_value=tar_result)
    mocker.patch.object(docker_local_api.localrepo, 'save_json')

    if make_dirs_result is False:
        mocker.patch.object(os, 'makedirs', side_effect=OSError)

    imagefile = "path/to/imagefile.tar"
    result = docker_local_api.save(imagetag_list, imagefile)
    assert result == expected
