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


@pytest.mark.parametrize("top_listdir, sub_listdir, isdir, load_json_output, log_warning, expected_struct", [
    ([], [], False, None, None, {"repolayers": {}, "repoconfigs": {}}),
    (["xx"], [], False, None, None, {'repoconfigs': {}, 'repolayers': {'xx': {}}}),
    (["repositories"], [], False, {"REPO": ""}, None,
     {"repolayers": {}, "repoconfigs": {}, "repositories": {"REPO": ""}}),
    (["manifest.json"], [], False, {"REPO": ""}, None, {"repolayers": {}, "repoconfigs": {}, "manifest": {"REPO": ""}}),
    (["x" * 70 + ".json"], [], False, {"k": "v"}, None, {"repolayers": {}, "repoconfigs": {
        "x" * 70 + ".json": {"json": {"k": "v"}, "json_f": "/tmp/" + "x" * 70 + ".json"}}}),
    (["x" * 64], [], True, None, None, {"repolayers": {"x" * 64: {}}, "repoconfigs": {}}),
    (["x" * 64], ["random_file"], True, None, "unknown file in layer: %s", {"repolayers": {"x" * 64: {}}, "repoconfigs": {}}),
    (["x" * 64], ["VERSION", "json"], True, {"k": "v"}, None,
     {"repolayers": {"x" * 64: {"VERSION": {"k": "v"}, "json": {"k": "v"}, "json_f": "/tmp/" + "x" * 64 + "/json"}},
      "repoconfigs": {}}),
    (["x" * 64], ["json"], True, {"k": "v"}, None,
     {"repolayers": {"x" * 64: {"json": {"k": "v"}, "json_f": "/tmp/" + "x" * 64 + "/json"}}, "repoconfigs": {}}),
    (["x" * 64], ["repolayer1"], True, None, None,
     {"repolayers": {"x" * 64: {"layer_f": "/tmp/" + "x" * 64 + "/repolayer1"}}, "repoconfigs": {}}),
    (["x" * 64], ["VERSION", "json", "repolayer1"], True, {"k": "v"}, None, {"repolayers": {
        "x" * 64: {"VERSION": {"k": "v"}, "json": {"k": "v"}, "json_f": "/tmp/" + "x" * 64 + "/json",
                   "layer_f": "/tmp/" + "x" * 64 + "/repolayer1"}}, "repoconfigs": {}}),
])
def test_02__load_structure(mocker, docker_local_api, logger, top_listdir, sub_listdir, isdir, load_json_output,
                            log_warning, expected_struct):
    """Test02 DockerLocalFileAPI()._load_structure()."""
    tmp_imagedir = "/tmp"
    mocker.patch('os.listdir', side_effect=[top_listdir, sub_listdir])
    mocker.patch.object(FileUtil, 'isdir', return_value=lambda path: path in top_listdir and isdir)
    mocker.patch.object(FileUtil, 'isfile', return_value=lambda x: True if x.endswith('.json') else False)
    mocker.patch.object(docker_local_api.localrepo, 'load_json', return_value=load_json_output)
    structure = docker_local_api._load_structure(tmp_imagedir)

    assert structure == expected_struct
    if log_warning:
        logger.warning.assert_called_with(log_warning, mocker.ANY)

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


@pytest.mark.parametrize("get_image_attributes, save_json, dict_returns, expected", [
    ((None, None), [False, True],
     {"cd_imagerepo": None, "copyto": True, "putdata": True, "rename": True, "os_exists": False}, False),
    (("/cont/lname1.layer", ["layer_f"]), [False, True],
     {"cd_imagerepo": None, "copyto": True, "putdata": True, "rename": True, "os_exists": False}, False),
    (("/cont/lname1.layer", ["lname1.layer"]), [True, True],
     {"cd_imagerepo": None, "copyto": False, "putdata": True, "rename": True, "os_exists": False}, False),
    (("/layer_f", ["layer_f"]), [True, True],
     {"cd_imagerepo": None, "copyto": False, "putdata": True, "rename": True, "os_exists": False}, False),
    (("/cont/lname1.layer", ["lname1.layer"]), [True, False],
     {"cd_imagerepo": None, "copyto": True, "putdata": True, "rename": True, "os_exists": False}, False),
    (("/cont/lname1.layer", ["lname1.layer"]), [True, True],
     {"cd_imagerepo": None, "copyto": True, "putdata": False, "rename": True, "os_exists": False}, False),
    (("/cont/lname1.layer", ["lname1.layer"]), [True, True],
     {"cd_imagerepo": None, "copyto": False, "putdata": True, "rename": True, "os_exists": True}, True),
    (("/cont/lname1.layer", ["lname1.layer"]), [True, True],
     {"cd_imagerepo": None, "copyto": True, "putdata": True, "rename": True, "os_exists": False}, True),
])
def test_09__save_image(mocker, docker_local_api, get_image_attributes, save_json, dict_returns, expected):
    """Test09 DockerLocalFileAPI()._save_image()."""
    imagerepo = "imagerepo"
    tag = "tag"
    structure = {"repositories": {}, "manifest": []}
    tmp_imagedir = "/tmp/tmp_imagedir"

    mocker.patch.object(docker_local_api.localrepo, 'cd_imagerepo', return_value=dict_returns['cd_imagerepo'])
    mocker.patch.object(docker_local_api.localrepo, 'get_image_attributes', return_value=get_image_attributes)
    mocker.patch.object(docker_local_api.localrepo, 'save_json', side_effect=save_json)
    mocker.patch.object(FileUtil, 'rename', return_value=dict_returns['rename'])
    mocker.patch.object(FileUtil, 'copyto', return_value=dict_returns['copyto'])
    mocker.patch.object(FileUtil, 'putdata', return_value=dict_returns['putdata'])
    mocker.patch('os.path.exists', return_value=dict_returns['os_exists'])

    result = docker_local_api._save_image(imagerepo, tag, structure, tmp_imagedir)

    assert result == expected

    if result:
        assert structure["manifest"]
        for manifest_item in structure["manifest"]:
            assert manifest_item["Config"].endswith(".json")
            assert isinstance(manifest_item["Layers"], list)
            assert manifest_item["RepoTags"] == [f"{imagerepo}:{tag}"]
    else:
        assert not structure["manifest"]


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
