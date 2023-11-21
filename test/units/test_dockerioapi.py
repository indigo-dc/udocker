#!/usr/bin/env python
"""
udocker unit tests: DockerIoAPI
"""
import random
from io import BytesIO

import pytest

from udocker.config import Config
from udocker.docker import DockerIoAPI
from udocker.utils.chksum import ChkSUM
from udocker.utils.fileutil import FileUtil


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
def logger(mocker):
    return mocker.patch('udocker.docker.LOG')


@pytest.mark.parametrize("patch_dict", [False, True], ids=["default_conf", "patched_conf"])
def test_01_init(mocker, dockerioapi, localrepo, patch_dict):
    """Test01 DockerIoAPI() constructor"""
    mocker_geturl = mocker.patch('udocker.docker.GetURL', return_value="url")
    if patch_dict:
        mocker.patch.dict('udocker.config.Config.conf', {'dockerio_index_url': "https://index.docker.io",
                                                         'dockerio_registry_url': "https://registry-1.docker.io"})
    dockerioapi = DockerIoAPI(localrepo)
    assert dockerioapi.index_url == Config.conf['dockerio_index_url']
    assert dockerioapi.registry_url == Config.conf['dockerio_registry_url']
    assert dockerioapi.localrepo == localrepo
    assert dockerioapi.search_pause
    assert dockerioapi.search_page == 0
    assert not dockerioapi.search_ended
    assert dockerioapi.v1api is not None
    assert dockerioapi.v2api is not None
    assert dockerioapi.curl == mocker_geturl.return_value
    assert mocker_geturl.called is True


@pytest.mark.parametrize("http_proxy", [
    ("socks5://user:pass@host:port",),
    ("",),
    (None,),
    ("invalidproxyformat",),
])
def test_02_set_proxy(mocker, dockerioapi, logger, http_proxy):
    """Test02 DockerIoAPI().set_proxy()."""
    mock_set_proxy = mocker.patch.object(dockerioapi.curl, 'set_proxy')
    dockerioapi.set_proxy(http_proxy)

    mock_set_proxy.assert_called_once_with(http_proxy)
    logger.info.assert_called_once_with("Setting proxy: %s", http_proxy)


@pytest.mark.parametrize("registry_url", [
    ("https://registry-1.docker.io",),
    ("",),
    (None,),
    ("invalidregistryformat",),
])
def test_03_set_registry(dockerioapi, logger, registry_url):
    """Test03 DockerIoAPI().set_registry()."""
    dockerioapi.set_registry(registry_url)
    logger.info.assert_called_once_with("Setting registry: %s", registry_url)
    assert dockerioapi.registry_url == registry_url


@pytest.mark.parametrize("index_url, expected_log_message", [
    ("https://index.example.com", "Setting docker index: %s"),
    ("", "Setting docker index: %s"),
    (None, "Setting docker index: %s"),
    ("invalidindexformat", "Setting docker index: %s"),
])
def test_04_set_index(dockerioapi, logger, index_url, expected_log_message):
    """Test04 DockerIoAPI().set_index()."""
    dockerioapi.set_index(index_url)
    logger.info.assert_called_once_with(expected_log_message, index_url)
    assert dockerioapi.index_url == index_url


@pytest.mark.parametrize("imagerepo, expected", [
    ("lipcomputing/os-cli-centos7", True),
    ("lipcomputing/os-cli-centos7:latest", True),
    ("os-cli-centos7", True),
    ("os-cli-centos7:latest", True),
    ("1233/fasdfasdf:sdfasfd", True),
    ("invalid*repo$name", False),
    ("/:", False),
    ("-invalid-repo", False),
    ("", False),
    (None, False),
])
def test_05_is_repo_name(dockerioapi, imagerepo, expected):
    """Test05 DockerIoAPI().is_repo_name()."""
    result = dockerioapi.is_repo_name(imagerepo)
    assert result == expected


@pytest.mark.parametrize("layername, expected", [
    ("abc123@sha256:1a2b3c4d5e", True),
    ("invalid*layer@sha256:1a2b3c", False),
    ("layername-without@hash", False),
    ("", False),
    (None, False),
])
def test_06__is_layer_name(dockerioapi, layername, expected):
    """Test06 DockerIoAPI()._is_layer_name()."""
    result = dockerioapi.is_layer_name(layername)
    assert result == expected


@pytest.mark.parametrize("params", [
    {'url': "http://some1.org/test", 'retry': 3, 'follow': 3, 'status_code': 200, 'www_authenticate': None,
     'retry_result': None, 'follow_result': None, 'location': None, 'header': None, 'expected_header': {},
     'expected_buffer': "response body", 'expected_status_code': 200},
    {'url': "http://some1.org/test", 'retry': -1, 'follow': -1, 'status_code': 200, 'www_authenticate': None,
     'retry_result': None, 'follow_result': None, 'location': None, 'header': None, 'expected_header': {},
     'expected_buffer': "response body", 'expected_status_code': 200},
    {'url': "http://some1.org/test", 'retry': 2, 'follow': None, 'status_code': 401, 'www_authenticate': None,
     'retry_result': None, 'follow_result': None, 'location': "http://some1.org/test", 'header': None,
     'expected_header': {}, 'expected_buffer': "response body", 'expected_status_code': 401},
    {'url': "http://some1.org/v1/test", 'retry': 3, 'follow': 3, 'status_code': 401, 'www_authenticate': "Token",
     'retry_result': None, 'follow_result': None, 'location': None, 'header': None,
     'expected_header': {'X-ND-HTTPSTATUS': 401, 'www-authenticate': 'Token'}, 'expected_buffer': "response body",
     'expected_status_code': 401},
    {'url': "http://some1.org/v1/test", 'retry': 3, 'follow': 3, 'status_code': 401, 'www_authenticate': "Token",
     'retry_result': None, 'follow_result': None, 'location': "http://some1.org/v1/test", 'header': None,
     'expected_header': {'X-ND-CURLSTATUS': 13, 'X-ND-HTTPSTATUS': 401, 'location': 'http://some1.org/v1/test',
                         'www-authenticate': 'Token'}, 'expected_buffer': "response body", 'expected_status_code': 401},
    {'url': "http://some1.org/v2/test", 'retry': 3, 'follow': 3, 'status_code': 401, 'www_authenticate': "Bearer",
     'retry_result': 2, 'follow_result': None, 'location': "http://some1.org/v1/test", 'header': None,
     'expected_header': {'X-ND-CURLSTATUS': 13, 'X-ND-HTTPSTATUS': 401, 'location': 'http://some1.org/v1/test',
                         'www-authenticate': 'Bearer'}, 'expected_buffer': "response body",
     'expected_status_code': 401},
    {'url': "http://some1.org/fail", 'retry': 1, 'follow': 3, 'status_code': 500, 'www_authenticate': None,
     'retry_result': 0, 'follow_result': None, 'location': None, 'header': None, 'expected_header': {},
     'expected_buffer': "error body", 'expected_status_code': 500},
    {'url': "http://some1.org/insufficient-scope", 'retry': 3, 'follow': 3, 'status_code': 401,
     'www_authenticate': 'error="insufficient_scope"', 'retry_result': None, 'follow_result': None, 'location': None,
     'header': None, 'expected_header': {}, 'expected_buffer': "error body", 'expected_status_code': 401},
    {'url': "http://some1.org/insufficient-scope/v1/", 'retry': 3, 'follow': 3, 'status_code': 401,
     'www_authenticate': 'error="insufficient_scope" realm="some-realm" header="header"', 'retry_result': None,
     'follow_result': None, 'location': None, 'header': None, 'expected_header': {}, 'expected_buffer': "error body",
     'expected_status_code': 401},
    {'url': "http://some1.org/insufficient-scope", 'retry': 3, 'follow': 3, 'status_code': 401,
     'www_authenticate': 'realm="some-realm" error="insufficient_scope"', 'retry_result': None, 'follow_result': None,
     'location': "http://some1.org/insufficient-scope/v1/", 'header': 'header', 'expected_header': {},
     'expected_buffer': "error body", 'expected_status_code': 401},
    {'url': "http://some1.org/insufficient-scope/v1/", 'retry': 3, 'follow': 3, 'status_code': 401,
     'www_authenticate': 'realm="some-realm" header="header"', 'retry_result': None, 'follow_result': None,
     'location': None, 'header': None, 'expected_header': {}, 'expected_buffer': "error body",
     'expected_status_code': 401},
    {'url': "http://some1.org/insufficient-scope/v2/", 'retry': 3, 'follow': 3, 'status_code': 401,
     'www_authenticate': 'realm="some-realm" header="header"', 'retry_result': None, 'follow_result': None,
     'location': None, 'header': None, 'expected_header': {}, 'expected_buffer': "error body",
     'expected_status_code': 401},
])
def test_07_get_url(mocker, dockerioapi, params):
    """Test07 DockerIoAPI()._get_url()."""
    mock_hdr = mocker.Mock()
    mock_hdr.data = {"X-ND-HTTPSTATUS": params['status_code'], "www-authenticate": params['www_authenticate']}

    if params['location']:
        mock_hdr.data.update({"location": params['location']})

    mock_curl_get = mocker.patch.object(dockerioapi.curl, 'get')
    mock_curl_get.return_value = (mock_hdr, BytesIO(params['expected_buffer'].encode()))

    mock_get_status_code = mocker.patch.object(dockerioapi.curl, 'get_status_code')
    mock_get_status_code.return_value = params['status_code']

    if params['retry'] == -1 and params['follow'] == -1:
        hdr, buf = dockerioapi.get_url(params['url'])
    elif params['header'] == 'header':
        hdr, buf = dockerioapi.get_url(params['url'], RETRY=params['retry'], FOLLOW=params['follow'],
                                       header=params['header'])
    else:
        hdr, buf = dockerioapi.get_url(params['url'], RETRY=params['retry'], FOLLOW=params['follow'])

    # Assertions
    assert mock_hdr.data["X-ND-HTTPSTATUS"] == params['expected_status_code']
    assert buf.getvalue().decode() == params['expected_buffer']
    if params['expected_header']:
        assert hdr.data == params['expected_header']
    if params['retry_result'] is not None:
        retry_calls = sum(
            1 for args, kwargs in mock_curl_get.call_args_list if kwargs.get('RETRY') == params['retry_result'])
        assert retry_calls > 0, "Retry logic not triggered as expected"

    if params['follow_result'] is not None:
        follow_calls = sum(
            1 for args, kwargs in mock_curl_get.call_args_list if kwargs.get('FOLLOW') == params['follow_result'])
        assert follow_calls > 0, "Follow logic not triggered as expected"


@pytest.mark.parametrize("filename, cache_mode, is_cached, download_status, remote_size, download_success, expected", [
    ("/path/to/file:1234", 0, True, 200, 100, True, True),
    ("/path/to/justAfile:info", 1, True, 200, 100, True, True),
    ("justAfile:info", 3, False, 200, 100, True, True),
    ("/path/to/justAfile:info", 0, False, 200, 100, True, True),
    ("/path/to/justAfile:info", 0, False, 200, -1, True, True),
    ("filelayer", 0, False, 200, 100, True, True),
    ("cachedFile.txt", 1, False, 200, 150, True, True),
    ("sizeMismatchFile.txt", 1, False, 200, 100, 1, False),
    ("/path/to/justAfile:info", 0, False, 500, 100, True, False),
    ("/path/to/justAfile:info", 0, False, 403, 100, True, False),
    ("nonChecksumFile.txt", 0, False, 200, 100, True, True),
], ids=[
    "checksum match & cached file",
    "checksum match & different cache mode",
    "non-cached file & specific cache mode",
    "non-cached file & default cache mode",
    "non-cached file & undefined remote size",
    "file with 'layer' suffix",
    "matching remote and local sizes (cache logic)",
    "file size mismatch & non-zero CURL status",
    "non-cached file & server error (500)",
    "non-cached file & forbidden error (403)",
    "file without checksum in filename"
])
def test_08__get_file(mocker, dockerioapi, filename, cache_mode, is_cached, download_status, remote_size,
                      download_success, expected):
    """Test08 DockerIoAPI()._get_file()."""
    mock_hdr = mocker.Mock()
    mock_hdr.data = {"X-ND-HTTPSTATUS": download_status, "X-ND-CURLSTATUS": cache_mode}
    mocker.patch.object(ChkSUM, 'hash', return_value="info" if is_cached else "different")
    mocker.patch.object(dockerioapi.curl, 'cache_support', True)
    mocker.patch.object(dockerioapi.curl, 'get_content_length', return_value=remote_size)
    mocker.patch.object(dockerioapi.curl, 'get_status_code', return_value=download_status)
    mocker.patch.object(FileUtil, 'size',
                        return_value=(remote_size + 100) if filename == 'sizeMismatchFile.txt' else remote_size)
    mocker.patch.object(dockerioapi, 'get_url', return_value=(mock_hdr, BytesIO(b"")))

    url = "http://some1.org/file1"
    result = dockerioapi.get_file(url, filename, cache_mode)

    assert result == expected


@pytest.mark.parametrize(
    "set_conf, imagerepo, expected_registry, expected_registry_url, expected_index_url, expected_remoterepo", [
        (True, "repo.com/myrepo/image", "repo.com", "https://registry_url.io", "https://index_url.io", "myrepo/image"),
        (False, "repo.com/myrepo/image", "repo.com", "https://repo.com", "https://repo.com", "myrepo/image"),
        (True, "myrepo/image", "", "https://registry-1.docker.io", "https://hub.docker.com", "myrepo/image"),
        (True, "image", "", "https://registry-1.docker.io", "https://hub.docker.com", "library/image"),
    ])
def test_09__parse_imagerepo(mocker, dockerioapi, set_conf, imagerepo, expected_registry, expected_registry_url,
                             expected_index_url, expected_remoterepo):
    """ Test09 DockerIoAPI()._parse_imagerepo() """
    config = {'docker_registries': {"repo.com": ["https://registry_url.io", "https://index_url.io"]}}
    mocker.patch.dict(Config.conf, config if set_conf else {})
    result = dockerioapi._parse_imagerepo(imagerepo)
    assert result == (imagerepo, expected_remoterepo)
    assert dockerioapi.registry_url == expected_registry_url
    assert dockerioapi.index_url == expected_index_url


@pytest.mark.parametrize("platform, v2_valid, local_repo_has_image, expected_files", [
    ("", True, False, ["file1", "file2"]),
    ("", True, False, []),
    ("", False, False, ["file1"]),
    ("", False, False, []),
    ("", True, True, []),
    ("linux", False, True, []),
    ("linux", False, False, ["file1"]),
    ("linux", False, False, [])
])
def test_10_get(dockerioapi, platform, v2_valid, local_repo_has_image, expected_files):
    """ Test10 DockerIoAPI().get() """
    imagerepo = "repo.com/repo/image"
    tag = "latest"

    dockerioapi.v2api = lambda: None
    dockerioapi.v2api.get = lambda repo, tag, platform: expected_files if v2_valid else []
    dockerioapi.v2api.is_valid = lambda: v2_valid

    dockerioapi.v1api = lambda: None
    dockerioapi.v1api.get = lambda repo, tag: [] if v2_valid else expected_files

    dockerioapi.localrepo = lambda: None
    dockerioapi.localrepo.cd_imagerepo = lambda repo, tag: local_repo_has_image
    dockerioapi.localrepo.setup_imagerepo = lambda repo: None
    dockerioapi.localrepo.del_imagerepo = lambda repo, tag, remove_files: None

    result = dockerioapi.get(imagerepo, tag, platform)

    assert result == expected_files


@pytest.mark.parametrize("imagerepo, tag, platform, is_valid, expected", [
    ("repo/image", "latest", "", True, {"manifest": "data"}),
    ("repo/image", "latest", "", True, {}),
    ("repo/image", "latest", "", False, ({}, {})),
])
def test_11_get_manifest(mocker, dockerioapi, logger, imagerepo, tag, platform, is_valid, expected):
    """ Test11 DockerIoAPI().get_manifest() """
    remoterepo = "repo/image"
    mocker.patch.object(dockerioapi, '_parse_imagerepo', return_value=("dummy", remoterepo))
    mocker.patch.object(dockerioapi.v2api, 'is_valid', return_value=is_valid)
    mocker_get_manifest = mocker.patch.object(dockerioapi.v2api, 'get_image_manifest', return_value=expected)

    result = dockerioapi.get_manifest(imagerepo, tag, platform)
    mocker_get_manifest.assert_called_with(remoterepo, tag,
                                           platform) if is_valid else mocker_get_manifest.assert_not_called()
    assert result == expected
    logger.debug.assert_called_once_with("get manifest imagerepo: %s tag: %s", imagerepo, tag)


@pytest.mark.parametrize("imagerepo, v2_valid, v2_tags, v1_tags, expected", [
    ("repo/image", True, ["v2_tag1", "v2_tag2"], [], ["v2_tag1", "v2_tag2"]),
    ("repo/image", False, [], ["v1_tag1", "v1_tag2"], ["v1_tag1", "v1_tag2"]),
    ("repo/image", False, [], [], []),
], ids=["v2_valid", "v1_valid", "none_valid"])
def test_12_get_tags(mocker, dockerioapi, imagerepo, v2_valid, v2_tags, v1_tags, expected):
    """ Test12 DockerIoAPI().get_tags() """
    mocker.patch.object(dockerioapi, '_parse_imagerepo', return_value=("dummy", imagerepo))
    mocker.patch.object(dockerioapi.v2api, 'is_valid', return_value=v2_valid)
    mocker.patch.object(dockerioapi.v2api, 'get_image_tags', return_value=v2_tags)
    mocker.patch.object(dockerioapi.v1api, 'get_image_tags', return_value=v1_tags)

    result = dockerioapi.get_tags(imagerepo)
    assert result == expected


@pytest.mark.parametrize("pause", [0, 5, 10])
def test_13_search_init(dockerioapi, pause):
    """Test13 DockerIoAPI().search_init()."""
    dockerioapi.search_init(pause)
    assert dockerioapi.search_pause == pause
    assert dockerioapi.search_page == 0
    assert not dockerioapi.search_ended


@pytest.mark.parametrize(
    "search_ended, v2_index_searchable, v1_index_searchable, v2_registry_searchable, v1_registry_searchable, expected",
    [
        (True, False, False, False, False, []),
        (False, True, False, False, False, ["result_v2_index"]),
        (False, False, True, False, False, ["result_v1_index"]),
        (False, False, False, True, False, ["result_v2_registry"]),
        (False, False, False, False, True, ["result_v1_registry"]),
        (False, False, False, False, False, []),
    ], ids=["search_ended", "v2_index_searchable", "v1_index_searchable", "v2_registry_searchable",
            "v1_registry_searchable", "no_api_searchable"])
def test_14_search_get_page(mocker, dockerioapi, search_ended, v2_index_searchable, v1_index_searchable,
                            v2_registry_searchable, v1_registry_searchable, expected):
    """Test14 DockerIoAPI().search_get_page()."""
    dockerioapi.search_ended = search_ended
    mocker.patch.object(dockerioapi.v2api, 'is_searchable', side_effect=[v2_index_searchable, v2_registry_searchable])
    mocker.patch.object(dockerioapi.v1api, 'is_searchable', side_effect=[v1_index_searchable, v1_registry_searchable])
    mocker.patch.object(dockerioapi.v2api, 'search_get_page',
                        return_value=["result_v2_index"] if v2_index_searchable else [
                            "result_v2_registry"] if v2_registry_searchable else [])
    mocker.patch.object(dockerioapi.v1api, 'search_get_page',
                        return_value=["result_v1_index"] if v1_index_searchable else [
                            "result_v1_registry"] if v1_registry_searchable else [])
    result = dockerioapi.search_get_page("expression")
    assert result == expected
