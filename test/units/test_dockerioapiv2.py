#!/usr/bin/env python
"""
udocker unit tests: DockerIoAPIv2
"""
import base64
import json
import random
from io import BytesIO

import pytest

from udocker.docker import DockerIoAPIv2, DockerIoAPI


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker, container_id):
    mocker_local_repo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mocker_local_repo.container_id = container_id
    mocker_local_repo.container_dir.return_value = "/.udocker/containers/" + container_id
    return mocker_local_repo


@pytest.fixture
def dockerioapi(localrepo):
    mocker_dockerioapi = DockerIoAPI(localrepo)
    mocker_dockerioapi.localrepo = localrepo
    return mocker_dockerioapi


@pytest.fixture
def dockerioapiv2(dockerioapi):
    return DockerIoAPIv2(dockerioapi)


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.docker.LOG')


def test_01_init(dockerioapi, dockerioapiv2):
    """Test01 DockerIoAPIv2().__init__()."""
    assert dockerioapiv2.dockerioapi == dockerioapi
    assert dockerioapiv2.v2_auth_header == ""
    assert dockerioapiv2.v2_auth_token == ""
    assert dockerioapiv2.localrepo == dockerioapi.localrepo
    assert dockerioapiv2.curl == dockerioapi.curl


@pytest.mark.parametrize("input_buf, expected_output", [
    ("field1=value1,field2=value2", {"field1": "value1", "field2": "value2"}),
    ("field1=value1,field2=\"value2\"", {"field1": "value1", "field2": "value2"}),
    ("field1=value1,field2=", {"field1": "value1", "field2": ""}),
    ("field1=value1=extra,field2=value2", {"field1": "value1=extra", "field2": "value2"}),
    ("", {}),
    ("field1,field2=value2", {"field2": "value2"}),
])
def test_02__split_fields(dockerioapiv2, input_buf, expected_output):
    """Test02 DockerIoAPIv2()._split_fields()."""
    result = dockerioapiv2._split_fields(input_buf)
    assert result == expected_output


@pytest.mark.parametrize(
    "www_authenticate, v2_auth_token, auth_url_response, retry, json_load_fails, expected_header", [
        ("Bearer realm=\"test\",service=\"docker.io\"", "validtoken", '{"token": "bearertoken"}', 3, False,
         "Authorization: Bearer bearertoken"),
        ("Bearer realm=\"test\",service=\"docker.io\"", "validtoken", '{"token": "bearertoken"}', 3, True,
         ""),
        ("Bearer realm=\"test\",service=\"docker.io\"", "validtoken", "invalidjson", 3, False, ""),
        ("Bearer realm=\"test\",service=\"docker.io\"", "", '{"token": "bearertoken"}', 3, False,
         "Authorization: Bearer bearertoken"),
        ("Basic realm=\"test\"", "validtoken", "", 3, False, "Authorization: Basic validtoken"),
        ("Basic realm=\"test\"", "", "", 3, False, "Authorization: Basic "),
        ("InvalidAuth realm=\"test\"", "validtoken", "", 3, False, ""),
    ])
def test_03_get_auth(mocker, dockerioapi, dockerioapiv2, www_authenticate, v2_auth_token, auth_url_response, retry,
                     json_load_fails, expected_header):
    """Test03 DockerIoAPIv2().get_auth()."""
    dockerioapiv2.v2_auth_token = v2_auth_token
    mocker.patch.object(dockerioapi, 'get_url', return_value=({}, BytesIO(auth_url_response.encode())))
    if json_load_fails:
        mocker.patch.object(json, 'loads', side_effect=ValueError)
    result = dockerioapiv2.get_auth(www_authenticate, retry)
    assert result == expected_header


@pytest.mark.parametrize("username, password,  log_call, error, expected_token", [
    ("user1", "pass1", True, False, base64.b64encode(b"user1:pass1").decode("ascii")),
    ("user1", "pass1", True, True, ""),  # FIXME: the exception is handled silencing the error
    (None, None, False, False, ""),
    ("user1", "", False, False, ""),
    ("", "pass1", False, False, ""),
    ("user:name", "pass:word", True, False, base64.b64encode(b"user:name:pass:word").decode("ascii")),
])
def test_04_get_login_token(mocker, dockerioapiv2, logger, username, password, log_call, error, expected_token):
    """ Test04 DockerIoAPIv2().get_login_token()."""
    if error:
        mocker.patch('base64.b64encode', side_effect=KeyError)

    token = dockerioapiv2.get_login_token(username, password)
    if log_call:
        logger.debug.assert_called_with("Auth token is: %s", dockerioapiv2.v2_auth_token)
    else:
        logger.debug.assert_not_called()

    assert token == expected_token


@pytest.mark.parametrize("token", [
    "token123",
    "",
    None,
], ids=["Valid token", "Empty token", "None token"])
def test_05_set_login_token(dockerioapiv2, token):
    """ Test05 DockerIoAPIv2().set_login_token()."""
    dockerioapiv2.set_login_token(token)
    assert dockerioapiv2.v2_auth_token == token


@pytest.mark.parametrize("http_status, expected_result", [
    ("200", True),
    ("401", True),
    ("404", False),
    ("500", False),
    ("NONE", False),
    (False, False),
])
def test_06_is_valid(mocker, dockerioapiv2, http_status, expected_result):
    """Test06 DockerIoAPIv2().is_valid()."""
    mock_hdr = mocker.Mock()
    mock_hdr.data = {"X-ND-HTTPSTATUS": http_status} if http_status else {}
    mocker.patch.object(dockerioapiv2.dockerioapi, 'get_url', return_value=(mock_hdr, None))

    result = dockerioapiv2.is_valid()

    assert result == expected_result


@pytest.mark.parametrize("http_status, expected", [
    ("200", True),
    ("401", True),
    ("404", False),
    ("500", False),
    ("NONE", False),
    (False, False),
])
def test_07_is_searchable(mocker, dockerioapiv2, http_status, expected):
    """ Test07 DockerIoAPIv2().is_searchable()."""
    mock_hdr = mocker.Mock()
    mock_hdr.data = {"X-ND-HTTPSTATUS": http_status} if http_status else {}
    mocker.patch.object(dockerioapiv2.dockerioapi, 'get_url', return_value=(mock_hdr, None))
    result = dockerioapiv2.is_searchable()
    assert result == expected


@pytest.mark.parametrize("response_content, tags_only, expected", [
    (b'{"tags": ["tag1", "tag2"]}', False, {"tags": ["tag1", "tag2"]}),
    (b'{"tags": ["tag1", "tag2"]}', True, ["tag1", "tag2"]),
    (b'', False, []),
    (b'invalid', False, []),
])
def test_08_get_image_tags(mocker, dockerioapiv2, response_content, tags_only, expected):
    """ Test08 DockerIoAPIv2().get_image_tags()."""
    imagerepo = "test/repo"
    mock_buf = BytesIO(response_content)
    mocker.patch.object(dockerioapiv2.dockerioapi, 'get_url', return_value=(mocker.Mock(), mock_buf))

    result = dockerioapiv2.get_image_tags(imagerepo, tags_only)
    assert result == expected


@pytest.mark.parametrize("image_index, platform, expected_digest", [
    ({"manifests": [{"platform": {"os": "linux", "architecture": "amd64"}, "digest": "digest1"}]},
     "linux/amd64", "digest1"),
    ({"manifests": [{"platform": {"os": "linux", "architecture": "amd64"}, "digest": "digest1"}]},
     "windows/amd64", ""),
    ("invalid", "linux/amd64", ""),
    ({}, "linux/amd64", ""),
    ({"manifests": [{"platform": {"os": "linux", "architecture": "amd64"}, "digest": "digest1"},
                    {"platform": {"os": "linux", "architecture": "arm64"}, "digest": "digest2"}]},
     "linux/arm64", "digest2"),
    ({"manifests": [{"platform": {"os": "linux", "architecture": "amd64", "variant": "v8"}, "digest": "digest1"},
                    {"platform": {"os": "linux", "architecture": "amd64", "variant": "v7"}, "digest": "digest2"}]},
     "linux/amd64/v7", "digest2"),
])
def test_09__get_digest_from_image_index(dockerioapiv2, image_index, platform, expected_digest):
    """ Test09 DockerIoAPIv2().get_digest_from_image_index()."""
    result = dockerioapiv2._get_digest_from_image_index(image_index, platform)
    assert result == expected_digest


@pytest.mark.parametrize("response_content, content_type, platform, call_digest_from_image, expected_manifest", [
    (b'{"config": {"digest": "digest1"}}', 'docker.distribution.manifest.v1', "", "",
     {"config": {"digest": "digest1"}}),
    (b'{"config": {"digest": "digest2"}}', 'docker.distribution.manifest.v2', "", "",
     {"config": {"digest": "digest2"}}),
    (b'{"schemaVersion": 1}', 'docker.distribution.manifest.v1+prettyjws', "", "",
     {"schemaVersion": 1}),
    (b'{"schemaVersion": 2}', 'oci.image.manifest.v1+json', "", "",
     {"schemaVersion": 2}),
    (b'{"schemaVersion": 2}', 'docker.distribution.manifest.list.v2', "", "",
     {"schemaVersion": 2}),
    (b'{"manifests": [{"platform": {"os": "linux", "architecture": "amd64"}, "digest": "digest3"}]}',
     'docker.distribution.manifest.list.v2', "linux/amd64", "", {}),
    (b'{"config": {"digest": "digest3"}}',
     'docker.distribution.manifest.list.v2', "linux/amd64", "digest3", {'config': {'digest': 'digest3'}}),
    (b'{"manifests": [{"platform": {"os": "linux", "architecture": "amd64"}, "digest": "digest3"}]}',
     'docker.distribution.manifest.list.v2', "", "",
     {"manifests": [{"platform": {"os": "linux", "architecture": "amd64"}, "digest": "digest3"}]}),
    (b'invalid', 'docker.distribution.manifest.v2', "", "", {}),
    (b'{"config": {"digest": "digest1"}}', 'unsupported', "", "", {}),
])
def test_10_image_manifest(mocker, dockerioapiv2, response_content, content_type, platform,
                           call_digest_from_image, expected_manifest):
    """ Test10 DockerIoAPIv2().get_image_manifest()."""
    imagerepo = "test/repo"
    tag = "latest"
    mock_hdr = mocker.Mock()
    mock_hdr.data = {'content-type': content_type}

    if call_digest_from_image:
        mock_recursive = mocker.Mock()
        mock_recursive.data = {'content-type': 'docker.distribution.manifest.v1'}
        mocker.patch.object(dockerioapiv2.dockerioapi, 'get_url', side_effect=[(mock_hdr, BytesIO(response_content)), (
            mock_recursive, BytesIO(response_content))])
    else:
        mocker.patch.object(dockerioapiv2.dockerioapi, 'get_url', return_value=(mock_hdr, BytesIO(response_content)))

    mocker.patch.object(dockerioapiv2, '_get_digest_from_image_index', return_value=call_digest_from_image)

    result = dockerioapiv2.get_image_manifest(imagerepo, tag, platform)

    if call_digest_from_image:
        assert result == (mock_recursive.data, expected_manifest)
    else:
        assert result == (mock_hdr.data, expected_manifest)


@pytest.mark.parametrize("get_file_response, expected_result", [
    (True, True),
    (False, False),
])
def test_11_get_image_layer(mocker, dockerioapi, dockerioapiv2, logger, get_file_response, expected_result):
    """ Test11 DockerIoAPIv2().get_image_layer()."""
    imagerepo = "test/repo"
    layer_id = "layer123"
    mocker.patch.object(dockerioapi, 'get_file', return_value=get_file_response)
    mocker.patch.object(dockerioapi, 'registry_url', "https://registry-1.docker.io")
    result = dockerioapiv2.get_image_layer(imagerepo, layer_id)
    logger.debug.assert_called_with("layer url: %s",
                                    "https://registry-1.docker.io/v2/" + imagerepo + "/blobs/" + layer_id)
    assert result == expected_result


@pytest.mark.parametrize("top_level, fslayers, get_image_layer_responses, expected_files", [
    ("digest", ["blob1", "blob2"], [True, True], ["blob2", "blob1"]),
    ("blobSum", ["blob1", "blob2"], [True, False], []),
    ("blobSum", ["blob1"], [True], ["blob1"]),
    ("blobSum", ["blob1"], [False], []),
    ("blobSum", [], [], []),
])
def test_12_get_layers_all(mocker, dockerioapiv2, logger, top_level, fslayers, get_image_layer_responses,
                           expected_files):
    """ Test12 DockerIoAPIv2().get_layers_all()."""
    imagerepo = "test/repo"
    mocker.patch.object(dockerioapiv2, 'get_image_layer', side_effect=get_image_layer_responses)
    fslayers = [{top_level: layer} for layer in fslayers]
    result = dockerioapiv2.get_layers_all(imagerepo, fslayers)
    logger.info.assert_has_calls(
        [mocker.call("downloading layer: %s", layer[top_level]) for layer in reversed(fslayers)])
    assert result == expected_files


@pytest.mark.parametrize(
    "get_image_manifest_return, http_status, setup_tag_return, expected_files, expected_logger_calls", [
        ({"fsLayers": ["blob1", "blob2"]}, 200, True, ["blob1", "blob2"], [("debug", "v2 layers: %s", "test/repo")]),
        ({"layers": ["blob1", "blob2"]}, 200, True, ["blob1", "blob2"], [("debug", "v2 layers: %s", "test/repo")]),
        ({"fsLayers": ["blob1", "blob2"]}, 200, False, [], [("error", "setting localrepo v2 tag and version")]),
        ({"layers": ["blob1", "blob2"], "config": "configBlob"}, 200, True, ["blob1", "blob2", "configBlob"],
         [("debug", "v2 layers: %s", "test/repo")]),
        ({}, 401, True, [], [("error", "manifest not found or not authorized")]),
        ({}, 500, True, [], [("error", "pulling manifest:")]),
        ({}, 200, True, [], [("error", "no manifest for given image and platform")]),
        ({"broken": "manifest"}, 200, True, [], [("error", "layers section missing in manifest")]),
        (None, 200, True, [], [("error", "no manifest for given image and platform")]),
    ])
def test_13_get(mocker, dockerioapi, dockerioapiv2, logger, get_image_manifest_return, http_status, setup_tag_return,
                expected_files, expected_logger_calls):
    """ Test13 DockerIoAPIv2().get()."""
    imagerepo = "test/repo"
    tag = "latest"
    platform = "linux/amd64"
    hdr_data = {"X-ND-HTTPSTATUS": http_status}
    mocker.patch.object(dockerioapiv2, 'get_image_manifest', return_value=(hdr_data, get_image_manifest_return))
    mocker.patch.object(dockerioapi.curl, 'get_status_code', return_value=http_status)
    mocker.patch.object(dockerioapiv2.localrepo, 'setup_tag', return_value=setup_tag_return)
    mocker.patch.object(dockerioapiv2.localrepo, 'save_json',
                        side_effect=lambda *args, **kwargs: KeyError() if get_image_manifest_return == {
                            "broken": "manifest"} and dockerioapiv2.localrepo.setup_tag(
                            tag) and dockerioapiv2.localrepo.set_version("v2") else None)
    mocker.patch.object(dockerioapiv2, 'get_layers_all',
                        side_effect=lambda repo, layers: layers if "blob1" in str(layers) else [])

    result = dockerioapiv2.get(imagerepo, tag, platform)
    assert result == expected_files

    for method, *args in expected_logger_calls:
        getattr(logger, method).assert_called_with(*args)

@pytest.mark.parametrize("expression, official, lines, http_response, expected", [
    ("test", None, 22, {"count": 1, "results": [{"name": "test/repo"}]},
     {"count": 1, "results": [{"name": "test/repo"}]}),
    ("", None, 22, {"count": 0, "results": []}, {"count": 0, "results": []}),
    ("test", True, 22, {"count": 1, "results": [{"name": "official/repo"}]},
     {"count": 1, "results": [{"name": "official/repo"}]}),
    ("test", False, 22, {"count": 1, "results": [{"name": "test/repo"}]},
     {"count": 1, "results": [{"name": "test/repo"}]}),
    ("test", None, 22, {}, []),
    (None, "something_elsel", 22, {}, []),
])
def test_14_search_get_page(mocker, dockerioapi, dockerioapiv2, expression, official, lines, http_response,
                            expected):
    """ Test14 DockerIoAPIv2().search_get_page()."""
    url = "https://hub.docker.com"
    mocker.patch.object(dockerioapi, 'get_url', return_value=({}, BytesIO(json.dumps(http_response).encode())))
    result = dockerioapiv2.search_get_page(expression, url, lines, official)
    assert result == expected
