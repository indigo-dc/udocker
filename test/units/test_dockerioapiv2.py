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
    ("field1=value1,field2=value2", {"field1": "value1", "field2": "value2"}),  # Basic case
    ("field1=value1,field2=\"value2\"", {"field1": "value1", "field2": "value2"}),  # Quoted value
    ("field1=value1,field2=", {"field1": "value1", "field2": ""}),  # Empty value
    ("field1=value1=extra,field2=value2", {"field1": "value1=extra", "field2": "value2"}),  # Value with equals sign
    ("", {}),  # Empty buffer
    ("field1,field2=value2", {"field2": "value2"}),  # Missing equals sign
])
def test_02_split_fields(dockerioapiv2, input_buf, expected_output):
    """Test02 DockerIoAPIv2()._split_fields()."""
    result = dockerioapiv2._split_fields(input_buf)
    assert result == expected_output


@pytest.mark.parametrize("www_authenticate, v2_auth_token, auth_url_response, retry, expected_header", [
    ("Bearer realm=\"test\",service=\"docker.io\"", "validtoken", '{"token": "bearertoken"}', 3,
     "Authorization: Bearer bearertoken"),
    ("Bearer realm=\"test\",service=\"docker.io\"", "validtoken", "invalidjson", 3, ""),
    ("Bearer realm=\"test\",service=\"docker.io\"", "", '{"token": "bearertoken"}', 3,
     "Authorization: Bearer bearertoken"),
    ("Basic realm=\"test\"", "validtoken", "", 3, "Authorization: Basic validtoken"),
    ("Basic realm=\"test\"", "", "", 3, "Authorization: Basic "),
    ("InvalidAuth realm=\"test\"", "validtoken", "", 3, ""),
], ids=[
    "Bearer token with valid auth token",
    "Bearer token with invalid JSON response",
    "Bearer token without auth token",
    "Basic authentication with auth token",
    "Basic authentication without auth token",
    "Invalid authentication header",
])
def test_03_get_auth(mocker, dockerioapi, dockerioapiv2, www_authenticate, v2_auth_token, auth_url_response, retry,
                     expected_header):
    """Test03 DockerIoAPIv2().get_auth()."""
    dockerioapiv2.v2_auth_token = v2_auth_token
    mocker.patch.object(dockerioapi, 'get_url', return_value=({}, BytesIO(auth_url_response.encode())))

    result = dockerioapiv2.get_auth(www_authenticate, retry)

    assert result == expected_header


@pytest.mark.parametrize("username, password, expected_token", [
    ("user1", "pass1", base64.b64encode(b"user1:pass1").decode("ascii")),
    ("", "", ""),
    (None, None, ""),
    ("user1", "", ""),
    ("", "pass1", ""),
    ("user:name", "pass:word", base64.b64encode(b"user:name:pass:word").decode("ascii")),
])
def test_get_login_token(dockerioapiv2, username, password, expected_token):
    token = dockerioapiv2.get_login_token(username, password)
    assert token == expected_token


@pytest.mark.parametrize("token", [
    "token123",
    "",
    None,
], ids=["Valid token", "Empty token", "None token"])
def test_04_set_login_token(dockerioapiv2, token):
    dockerioapiv2.set_login_token(token)
    assert dockerioapiv2.v2_auth_token == token


@pytest.mark.parametrize("http_status, expected_result", [
    ("200", True),
    ("401", True),
    ("404", False),
    ("500", False),
    ("X-ND-HTTPSTATUS", False),
])
def test_05_is_valid(mocker, dockerioapiv2, http_status, expected_result):
    mock_hdr = mocker.Mock()
    mock_hdr.data = {"X-ND-HTTPSTATUS": http_status}
    mocker.patch.object(dockerioapiv2.dockerioapi, 'get_url', return_value=(mock_hdr, None))

    result = dockerioapiv2.is_valid()

    assert result == expected_result


@pytest.mark.parametrize("http_status, expected_result", [
    ("200", True),
    ("401", True),
    ("404", False),
    ("500", False),
    ("X-ND-HTTPSTATUS", False),
])
def test_06_is_searchable(mocker, dockerioapiv2, http_status, expected_result):
    mock_hdr = mocker.Mock()
    mock_hdr.data = {"X-ND-HTTPSTATUS": http_status}
    mocker.patch.object(dockerioapiv2.dockerioapi, 'get_url', return_value=(mock_hdr, None))

    result = dockerioapiv2.is_searchable()

    assert result == expected_result


@pytest.mark.parametrize("response_content, tags_only, expected_result", [
    (b'{"tags": ["tag1", "tag2"]}', False, {"tags": ["tag1", "tag2"]}),
    (b'{"tags": ["tag1", "tag2"]}', True, ["tag1", "tag2"]),
    (b'', False, []),
    (b'invalid', False, []),
])
def test_07_get_image_tags(mocker, dockerioapiv2, response_content, tags_only, expected_result):
    imagerepo = "test/repo"
    mock_buf = BytesIO(response_content)
    mocker.patch.object(dockerioapiv2.dockerioapi, 'get_url', return_value=(mocker.Mock(), mock_buf))

    result = dockerioapiv2.get_image_tags(imagerepo, tags_only)

    assert result == expected_result


@pytest.mark.parametrize("image_index, platform, expected_digest", [
    ({"manifests": [{"platform": {"os": "linux", "architecture": "amd64"}, "digest": "digest1"}]},
     "linux/amd64", "digest1"),
    ({"manifests": [{"platform": {"os": "linux", "architecture": "amd64"}, "digest": "digest1"}]},
     "windows/amd64", ""),
    ("invalid", "linux/amd64", ""),
    ({}, "linux/amd64", ""),
], ids=[
    "Valid image index and platform",
    "Platform not in image index",
    "Invalid image index format",
    "Empty image index"
])
def test_08_get_digest_from_image_index(dockerioapiv2, image_index, platform, expected_digest):
    result = dockerioapiv2._get_digest_from_image_index(image_index, platform)
    assert result == expected_digest


@pytest.mark.parametrize("response_content, content_type, platform, expected_manifest", [
    (b'{"config": {"digest": "digest1"}}', 'docker.distribution.manifest.v2', "",
     {"config": {"digest": "digest1"}}),
    (b'{"schemaVersion": 1}', 'docker.distribution.manifest.v1+prettyjws', "",
     {"schemaVersion": 1}),
    (b'{"schemaVersion": 2}', 'oci.image.manifest.v1+json', "",
     {"schemaVersion": 2}),
    (b'invalid', 'docker.distribution.manifest.v2', "", {}),
    (b'{"config": {"digest": "digest1"}}', 'unsupported', "", {}),
])
def test_get_image_manifest(mocker, dockerioapiv2, response_content, content_type, platform, expected_manifest):
    imagerepo = "test/repo"
    tag = "latest"
    mock_hdr = mocker.Mock()
    mock_hdr.data = {'content-type': content_type}
    mocker.patch.object(dockerioapiv2.dockerioapi, 'get_url',
                        return_value=(mock_hdr, BytesIO(response_content)))

    result = dockerioapiv2.get_image_manifest(imagerepo, tag, platform)

    assert result == (mock_hdr.data, expected_manifest)


@pytest.mark.parametrize("get_file_response, expected_result", [
    (True, True),
    (False, False),
])
def test_get_image_layer(mocker, dockerioapi, dockerioapiv2, get_file_response, expected_result):
    imagerepo = "test/repo"
    layer_id = "layer123"
    mocker.patch.object(dockerioapi, 'get_file', return_value=get_file_response)

    result = dockerioapiv2.get_image_layer(imagerepo, layer_id)

    assert result == expected_result


# @pytest.mark.parametrize("fslayers, get_image_layer_responses, expected_files", [
#     (["blob1", "blob2"], [True, True], ["blob1", "blob2"]),
#     (["blob1", "blob2"], [True, False], []),
#     (["blob1"], [True], ["blob1"]),
#     (["blob1"], [False], []),
#     ([], [], []),
# ])
# def test_get_layers_all(mocker, dockerioapiv2, fslayers, get_image_layer_responses, expected_files):
#     imagerepo = "test/repo"
#     mocker.patch.object(dockerioapiv2, 'get_image_layer', side_effect=get_image_layer_responses)
#
#     result = dockerioapiv2.get_layers_all(imagerepo, [{"digest": layer} for layer in fslayers])
#
#     assert result == expected_files


# @pytest.mark.parametrize("get_image_manifest_return, http_status, manifest_content, setup_tag_return, expected_files", [
#     (({}, {"fsLayers": ["blob1", "blob2"]}), "200", True, ["blob1", "blob2"]),
#     (({}, {"layers": ["blob1", "blob2"]}), "200", True, ["blob1", "blob2"]),
#     (({}, {}), "401", True, []),
#     (({}, {}), "500", True, []),
#     (({}, {}), "200", True, []),
#     (({}, {"fsLayers": ["blob1", "blob2"]}), "200", False, []),
# ])
# def test_get(mocker, dockerioapi, dockerioapiv2, get_image_manifest_return, http_status, setup_tag_return,
#              manifest_content, expected_files):
#     imagerepo = "test/repo"
#     tag = "latest"
#     platform = "linux/amd64"
#     mocker.patch.object(dockerioapiv2, 'get_image_manifest', return_value=get_image_manifest_return)
#     mocker.patch.object(dockerioapi.curl, 'get_status_code', return_value=http_status)
#     mocker.patch.object(dockerioapiv2.localrepo, 'setup_tag', return_value=setup_tag_return)
#     mocker.patch.object(dockerioapiv2.localrepo, 'save_json')
#     mocker.patch.object(dockerioapiv2, 'get_layers_all', return_value=expected_files)
#
#     result = dockerioapiv2.get(imagerepo, tag, platform)
#
#     assert result == expected_files


@pytest.mark.parametrize("expression, official, lines, http_response, expected_result", [
    # Successful search
    ("test", None, 22, {"count": 1, "results": [{"name": "test/repo"}]},
     {"count": 1, "results": [{"name": "test/repo"}]}),
    # Empty expression
    ("", None, 22, {"count": 0, "results": []}, {"count": 0, "results": []}),
    # Official repository search
    ("test", True, 22, {"count": 1, "results": [{"name": "official/repo"}]},
     {"count": 1, "results": [{"name": "official/repo"}]}),
    # Non-official repository search
    ("test", False, 22, {"count": 1, "results": [{"name": "test/repo"}]},
     {"count": 1, "results": [{"name": "test/repo"}]}),
    # # Failed search
    # ("test", None, 22, {}, {}),
])
def test_search_get_page(mocker, dockerioapi, dockerioapiv2, expression, official, lines, http_response,
                         expected_result):
    url = "https://hub.docker.com"
    mocker.patch.object(dockerioapi, 'get_url', return_value=({}, BytesIO(json.dumps(http_response).encode())))

    result = dockerioapiv2.search_get_page(expression, url, lines, official)

    assert result == expected_result
