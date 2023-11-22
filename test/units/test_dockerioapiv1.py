#!/usr/bin/env python
"""
udocker unit tests: DockerIoAPIv1
"""
import json
import random
from io import BytesIO

import pytest

from udocker.docker import DockerIoAPIv1, DockerIoAPI


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
def dockerioapiv1(dockerioapi):
    return DockerIoAPIv1(dockerioapi)


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.docker.LOG')


def test_01_init(dockerioapi, dockerioapiv1):
    """Test01 DockerIoAPIv1.__init__"""
    assert dockerioapiv1.dockerioapi == dockerioapi
    assert dockerioapiv1.v1_auth_header == ""
    assert dockerioapiv1.localrepo == dockerioapi.localrepo
    assert dockerioapiv1.curl == dockerioapi.curl


@pytest.mark.parametrize("http_responses, expected", [
    (["200", "200"], True),
    (["401", "401"], True),
    (["404", "404"], False),
    (["500", "500"], False),
    (["X-ND-HTTPSTATUS", "X-ND-HTTPSTATUS"], False),
    ("raise_error", False),
])
def test_02_is_valid(mocker, dockerioapiv1, http_responses, expected):
    """ Test02 DockerIoAPIv1.is_valid() """
    mock_responses = []
    mock_hdr = mocker.Mock()
    if http_responses == "raise_error":
        mock_hdr.pop('data', None)
        mock_responses = [(mock_hdr, None), (mock_hdr, None)]
    else:
        for status in http_responses:
            mock_hdr.data = {"X-ND-HTTPSTATUS": status}
            mock_responses.append((mock_hdr, None))

    mocker.patch.object(dockerioapiv1.dockerioapi, 'get_url', side_effect=mock_responses)

    result = dockerioapiv1.is_valid()
    assert result == expected


@pytest.mark.parametrize("url, http_responses, expected", [
    ("https://registry-1.docker.io", ["200"], True),
    (None, ["200"], True),
    ("https://registry-1.docker.io", ["401"], True),
    ("https://registry-1.docker.io", ["404"], False),
    ("https://registry-1.docker.io", ["500"], False),
    ("https://registry-1.docker.io", ["X-ND-HTTPSTATUS"], False),
    ("https://registry-1.docker.io", "raise_OSError", False),
])
def test_03_is_searchable(mocker, dockerioapiv1, url, http_responses, expected):
    """ Test03 DockerIoAPIv1.is_searchable() """
    mock_hdr = mocker.Mock()
    mock_responses = []
    if http_responses == "raise_OSError":
        mock_hdr.pop('data', None)
        mock_responses = [(mock_hdr, None)]
    else:
        for status in http_responses:
            mock_hdr.data = {"X-ND-HTTPSTATUS": status}
            mock_responses.append((mock_hdr, None))

    mocker.patch.object(dockerioapiv1.dockerioapi, 'get_url', side_effect=mock_responses)
    result = dockerioapiv1.is_searchable(url)
    assert result == expected


@pytest.mark.parametrize("http_status, response_content, response_header, expected_result", [
    (200, b'{"id": "image1"}', {"x-docker-token": "token123"},
     ({'X-ND-HTTPSTATUS': '200', 'x-docker-token': 'token123'}, {"id": "image1"})),
    (401, b'', {}, ({"X-ND-HTTPSTATUS": "401"}, [])),
    (500, b'', {}, ({"X-ND-HTTPSTATUS": "500"}, [])),
    (200, b'[{"id": "image1"}]', {}, ({"X-ND-HTTPSTATUS": "200"}, [])),
    (200, b'', {"x-docker-token": "token123"}, ({'X-ND-HTTPSTATUS': '200', 'x-docker-token': 'token123'}, [])),
    (200, b'invalid', {"x-docker-token": "token123"}, ({"x-docker-token": "token123", "X-ND-HTTPSTATUS": "200"}, []))
])
def test_04_get_repo(mocker, dockerioapiv1, http_status, response_content, response_header, expected_result):
    """Test04 DockerIoAPIv1.get_repo()"""
    imagerepo = "test/repo"
    mock_hdr = mocker.Mock()
    mock_hdr.data = {"X-ND-HTTPSTATUS": str(http_status), **response_header}
    mock_buff = BytesIO(response_content)
    mocker.patch.object(dockerioapiv1.dockerioapi, 'get_url', return_value=(mock_hdr, mock_buff))

    result = dockerioapiv1.get_repo(imagerepo)

    assert result == expected_result
    if "x-docker-token" in response_header:
        expected_auth_header = "Authorization: Token " + response_header["x-docker-token"]
        try:
            json.loads(response_content)
            assert dockerioapiv1.v1_auth_header == expected_auth_header
        except (OSError, AttributeError, ValueError, TypeError, KeyError):
            assert dockerioapiv1.v1_auth_header == ""
    else:
        assert dockerioapiv1.v1_auth_header == ""


@pytest.mark.parametrize("www_authenticate, v1_auth_header, expected_result", [
    ("Bearer realm=\"https://auth.docker.io\",service=\"registry.docker.io\",Token=\"TestToken\"", "AuthToken123",
     "AuthToken123"),
    ("Bearer realm=\"https://auth.docker.io\",service=\"registry.docker.io\"", "AuthToken123", "")
])
def test_05_get_auth(dockerioapiv1, www_authenticate, v1_auth_header, expected_result):
    """ Test05 DockerIoAPIv1.get_auth() """
    dockerioapiv1.v1_auth_header = v1_auth_header

    result = dockerioapiv1.get_auth(www_authenticate)
    assert result == expected_result


@pytest.mark.parametrize("imagerepo, tags_only, http_status, response_content, x_docker_endpoints, expected", [
    ("test/repo", False, "200", b'[{"name": "tag1"}, {"name": "tag2"}]', "docker-endpoint.com",
     [{'name': 'tag1'}, {'name': 'tag2'}]),
    ("test/repo", True, "200", b'[{"name": "tag1"}, {"name": "tag2"}]', "docker-endpoint.com", ['tag1', 'tag2']),
    ("test/repo", False, "200", b'invalid json', "docker-endpoint.com", []),
    ("test/repo", False, "500", b'[]', "docker-endpoint.com", []),
    ("test/repo", False, "200", b'[{"name": "tag1"}]', None, [{'name': 'tag1'}]),  # No x-docker-endpoints in hdr_data
    ("test/repo", False, "404", b'[]', "docker-endpoint.com", []),  # Not found
])
def test_06_get_image_tags(mocker, dockerioapiv1, imagerepo, tags_only, http_status, response_content,
                           x_docker_endpoints, expected):
    """ Test06 DockerIoAPIv1.get_image_tags() """
    mock_hdr = {"X-ND-HTTPSTATUS": http_status}
    if x_docker_endpoints:
        mock_hdr["x-docker-endpoints"] = x_docker_endpoints

    mocker.patch.object(dockerioapiv1, 'get_repo', return_value=(mock_hdr, BytesIO(response_content)))
    url = dockerioapiv1.dockerioapi.index_url if not x_docker_endpoints else "http://" + x_docker_endpoints
    url += "/v1/repositories/" + imagerepo + "/tags"
    mocker.patch.object(dockerioapiv1.dockerioapi, 'get_url', return_value=(mock_hdr, BytesIO(response_content)))

    result = dockerioapiv1.get_image_tags(imagerepo, tags_only)
    assert result == expected


@pytest.mark.parametrize("endpoint, imagerepo, tag, http_status, response_content, expected", [
    ("http://docker-endpoint.com", "test/repo", "latest", "200", b'{"id": "image1"}',
     ({"X-ND-HTTPSTATUS": "200"}, {"id": "image1"})),
    ("http://docker-endpoint.com", "test/repo", "latest", "401", b'', ({"X-ND-HTTPSTATUS": "401"}, [])),
    ("http://docker-endpoint.com", "test/repo", "latest", "500", b'', ({"X-ND-HTTPSTATUS": "500"}, [])),
    ("http://docker-endpoint.com", "test/repo", "latest", "200", b'invalid json', ({"X-ND-HTTPSTATUS": "200"}, [])),
    ("http://docker-endpoint.com", "test/repo", "latest", "404", b'', ({"X-ND-HTTPSTATUS": "404"}, [])),
])
def test_07_get_image_tag(mocker, dockerioapiv1, logger, endpoint, imagerepo, tag, http_status, response_content,
                          expected):
    """ Test07 DockerIoAPIv1.get_image_tag() """
    mock_hdr = mocker.Mock()
    mock_hdr.data = {"X-ND-HTTPSTATUS": http_status}
    mocker.patch.object(dockerioapiv1.dockerioapi, 'get_url', return_value=(mock_hdr, BytesIO(response_content)))
    url = f"{endpoint}/v1/repositories/{imagerepo}/tags/{tag}"
    result = dockerioapiv1.get_image_tag(endpoint, imagerepo, tag)
    assert result == expected
    logger.debug.assert_called_once_with("tags url: %s", url)


@pytest.mark.parametrize("endpoint, image_id, http_status, response_content, expected", [
    ("http://docker-endpoint.com", "image1", "200", b'["layer1", "layer2"]',
     ({"X-ND-HTTPSTATUS": "200"}, ["layer1", "layer2"])),
    ("http://docker-endpoint.com", "image1", "401", b'', ({"X-ND-HTTPSTATUS": "401"}, [])),
    ("http://docker-endpoint.com", "image1", "500", b'', ({"X-ND-HTTPSTATUS": "500"}, [])),
    ("http://docker-endpoint.com", "image1", "200", b'invalid json', ({"X-ND-HTTPSTATUS": "200"}, [])),
    ("http://docker-endpoint.com", "image1", "404", b'', ({"X-ND-HTTPSTATUS": "404"}, [])),
])
def test_08_get_image_ancestry(mocker, dockerioapiv1, logger, endpoint, image_id, http_status, response_content,
                               expected):
    """ Test08 DockerIoAPIv1.get_image_ancestry() """
    mock_hdr = mocker.Mock()
    mock_hdr.data = {"X-ND-HTTPSTATUS": http_status}
    mocker.patch.object(dockerioapiv1.dockerioapi, 'get_url', return_value=(mock_hdr, BytesIO(response_content)))
    url = f"{endpoint}/v1/images/{image_id}/ancestry"
    result = dockerioapiv1.get_image_ancestry(endpoint, image_id)
    assert result == expected
    logger.debug.assert_called_once_with("ancestry url: %s", url)


@pytest.mark.parametrize("endpoint, layer_id, get_file_success, expected", [
    ("http://docker-endpoint.com", "layer1", True, True),
    ("http://docker-endpoint.com", "layer1", False, False),
    ("http://docker-endpoint.com", "layer2", True, True),
    ("http://docker-endpoint.com", "layer2", False, False),
])
def test_09_get_image_json(mocker, dockerioapiv1, logger, endpoint, layer_id, get_file_success, expected):
    """ Test09 DockerIoAPIv1.get_image_json() """
    url = f"{endpoint}/v1/images/{layer_id}/json"
    filename = dockerioapiv1.localrepo.layersdir + '/' + layer_id + ".json"
    mocker.patch.object(dockerioapiv1.dockerioapi, 'get_file', return_value=get_file_success)
    mocker.patch.object(dockerioapiv1.localrepo, 'add_image_layer')

    result = dockerioapiv1.get_image_json(endpoint, layer_id)

    assert result == expected
    logger.debug.assert_called_once_with("json url: %s", url)
    if get_file_success:
        dockerioapiv1.localrepo.add_image_layer.assert_called_once_with(filename)


@pytest.mark.parametrize("endpoint, layer_id, get_file_success, expected", [
    ("http://docker-endpoint.com", "layer1", True, True),
    ("http://docker-endpoint.com", "layer1", False, False),
    ("http://docker-endpoint.com", "layer2", True, True),
    ("http://docker-endpoint.com", "layer2", False, False),
])
def test_10_get_image_layer(mocker, dockerioapiv1, logger, endpoint, layer_id, get_file_success, expected):
    """ Test10 DockerIoAPIv1.get_image_layer() """
    url = f"{endpoint}/v1/images/{layer_id}/layer"
    filename = dockerioapiv1.localrepo.layersdir + '/' + layer_id + ".layer"

    mocker.patch.object(dockerioapiv1.dockerioapi, 'get_file', return_value=get_file_success)
    mocker.patch.object(dockerioapiv1.localrepo, 'add_image_layer')
    result = dockerioapiv1.get_image_layer(endpoint, layer_id)

    assert result == expected
    logger.debug.assert_called_once_with("layer url: %s", url)

    if get_file_success:
        dockerioapiv1.localrepo.add_image_layer.assert_called_once_with(filename)


@pytest.mark.parametrize(
    "endpoint, layer_list, get_image_json_results, get_image_layer_results, calls_count, expected", [
        ("http://docker-endpoint.com", ["layer1", "layer2"],
         [True, True], [True, True], {'get_image_json': 2, 'get_image_layer': 2},
         ["layer2.json", "layer2.layer", "layer1.json", "layer1.layer"]),
        ("http://docker-endpoint.com", ["layer1", "layer2"],
         [False, True], [True, True], {'get_image_json': 1, 'get_image_layer': 0}, []),
        ("http://docker-endpoint.com", ["layer1", "layer2"],
         [True, False], [False, True], {'get_image_json': 1, 'get_image_layer': 1}, []),
        ("http://docker-endpoint.com", [], [False, False], [False, False],
         {'get_image_json': 0, 'get_image_layer': 0}, []),
    ])
def test_11_get_layers_all(mocker, dockerioapiv1, endpoint, layer_list, get_image_json_results, get_image_layer_results,
                           calls_count, expected):
    """ Test11 DockerIoAPIv1.get_layers_all() """
    mocker.patch.object(dockerioapiv1, 'get_image_json', side_effect=get_image_json_results)
    mocker.patch.object(dockerioapiv1, 'get_image_layer', side_effect=get_image_layer_results)
    result = dockerioapiv1.get_layers_all(endpoint, layer_list)
    assert result == expected
    assert dockerioapiv1.get_image_json.call_count == calls_count['get_image_json']
    assert dockerioapiv1.get_image_layer.call_count == calls_count['get_image_layer']


@pytest.mark.parametrize("tags_obj, tag, expected_result", [
    ({"tag1": "id1", "tag2": "id2"}, "tag1", "id1"),
    ({"tag1": "id1", "tag2": "id2"}, "tag3", ""),
    ([{"name": "tag1", "layer": "id1"}, {"name": "tag2", "layer": "id2"}], "tag1", "id1"),
    ([{"name": "tag1", "layer": "id1"}, {"name": "tag2", "layer": "id2"}], "tag3", ""),
    ("invalid_tags_object", "tag1", ""),
    ([{"name": "tag1", "layer": "id1"}, {"name": "tag2"}], "tag2", ""),
])
def test_12__get_id_from_tags(dockerioapiv1, tags_obj, tag, expected_result):
    """ Test12 DockerIoAPIv1._get_id_from_tags() """
    result = dockerioapiv1._get_id_from_tags(tags_obj, tag)
    assert result == expected_result


@pytest.mark.parametrize("images_array, short_id, expected_result", [
    ([{"id": "abcd1234imageid"}, {"id": "efgh5678imageid"}], "abcd1234", "abcd1234imageid"),
    ([{"id": "abcd1234imageid"}, {"id": "efgh5678imageid"}], "ijkl9012", ""),
    ([], "abcd1234", ""),
    ([{"not_id": "abcd1234imageid"}], "abcd1234", ""),
    ([{"id": "abcd1234imageid"}, {"id": "abcd1234anotherid"}], "abcd1234", "abcd1234imageid"),
])
def test_13__get_id_from_images(dockerioapiv1, images_array, short_id, expected_result):
    """ Test13 DockerIoAPIv1._get_id_from_images() """
    result = dockerioapiv1._get_id_from_images(images_array, short_id)
    assert result == expected_result


@pytest.mark.parametrize("images_array, short_id, expected_result", [
    ([{"id": "abcd1234imageid"}, {"id": "efgh5678imageid"}], "abcd1234", "abcd1234imageid"),
    ([{"id": "abcd1234imageid"}, {"id": "efgh5678imageid"}], "ijkl9012", ""),
    ([], "abcd1234", ""),
    ([{"not_id": "abcd1234imageid"}], "abcd1234", ""),
    ([{"id": "abcd1234imageid"}, {"id": "abcd1234anotherid"}], "abcd1234", "abcd1234imageid"),
])
def test_14__get_id_from_images(dockerioapiv1, images_array, short_id, expected_result):
    """ Test14 DockerIoAPIv1._get_id_from_images() """
    result = dockerioapiv1._get_id_from_images(images_array, short_id)
    assert result == expected_result


@pytest.mark.parametrize(
    "image, status, image_tags, from_tags, from_images, setup_tag, ancestry, layers, expected_files, logger_calls",
    [
        (["image1"], 200, {}, "image_id", "image_id", True, ["layer1", "layer2"],
         ["layer1.json", "layer1.layer", "layer2.json", "layer2.layer"],
         ["layer1.json", "layer1.layer", "layer2.json", "layer2.layer"],
         [("debug", "v1 image id: %s", "test/repo"),
          ("debug", "v1 ancestry: %s", "image_id"),
          ("debug", "v1 layers: %s", "image_id")]),
        ([None], 401, {}, "", "", True, None, None, [], [("error", "image not found or not authorized")]),
        (["image1"], 200, {}, "", "", True, None, None, [], [("error", "image tag not found")]),
        (["image1"], 200, {}, "short_id", "", True, None, None, [], [("error", "image id not found")]),
        (["image1"], 200, {}, "image_id", "image_id", False, None, None, [],
         [("error", "setting localrepo v1 tag and version")]),
        (["image1"], 200, {}, "image_id", "image_id", True, None, None, [], [("error", "ancestry not found")]),
        (["image1"], 200, {}, "image_id", "image_id", True, ["layer1", "layer2"], None, None,
         [("debug", "v1 layers: %s", "image_id")]),
    ]
)
def test_15_get(mocker, dockerioapiv1, logger, image, status, image_tags, from_tags, from_images, setup_tag, ancestry,
                layers, expected_files, logger_calls):
    """ Test15 DockerIoAPIv1.get() """
    imagerepo = "test/repo"
    tag = "latest"
    hdr_data = {"X-ND-HTTPSTATUS": status}
    mocker.patch.object(dockerioapiv1, 'get_repo', return_value=(hdr_data, image))
    mocker.patch.object(dockerioapiv1.curl, 'get_status_code', return_value=status)
    mocker.patch.object(dockerioapiv1, 'get_image_tags', return_value=image_tags)
    mocker.patch.object(dockerioapiv1, '_get_id_from_tags', return_value=from_tags)
    mocker.patch.object(dockerioapiv1, '_get_id_from_images', return_value=from_images)
    mocker.patch.object(dockerioapiv1.localrepo, 'setup_tag', return_value=setup_tag)
    mocker.patch.object(dockerioapiv1, 'get_image_ancestry', return_value=(None, ancestry))
    mocker.patch.object(dockerioapiv1, 'get_layers_all', return_value=layers)

    result = dockerioapiv1.get(imagerepo, tag)

    assert result == expected_files

    for method, *args in logger_calls:
        getattr(logger, method).assert_any_call(*args)


@pytest.mark.parametrize("expression, api_response, buffer_data, expected_result, expected_search_ended", [
    ("docker", {"status": "200"}, json.dumps({"page": 1, "num_pages": 2}), {"page": 1, "num_pages": 2}, False),
    ("docker", {"status": "200"}, json.dumps({"page": 2, "num_pages": 2}), {"page": 2, "num_pages": 2}, True),
    (None, {"status": "200"}, json.dumps({"page": 2, "num_pages": 2}), {"page": 2, "num_pages": 2}, True),
    ("docker", {"status": "404"}, "Invalid JSON", [], True),
])
def test_16_search_get_page(mocker, dockerioapi, dockerioapiv1, expression, api_response, buffer_data, expected_result,
                            expected_search_ended):
    """ Test16 DockerIoAPIv1.search_get_page() """
    url = "http://example.com"
    mocker.patch.object(dockerioapi, 'get_url', return_value=(api_response, BytesIO(buffer_data.encode())))
    result = dockerioapiv1.search_get_page(expression, url)

    assert result == expected_result
    assert dockerioapi.search_ended == expected_search_ended
