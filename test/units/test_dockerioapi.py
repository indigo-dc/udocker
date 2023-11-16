#!/usr/bin/env python
"""
udocker unit tests: DockerIoAPI
"""
import io
import random
from io import BytesIO

import pytest

from udocker.config import Config
from udocker.docker import DockerIoAPI
from udocker.utils.chksum import ChkSUM
from udocker.utils.curl import GetURL
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


def test_01_init(mocker, dockerioapi, localrepo):
    """Test01 DockerIoAPI() constructor"""
    mock_get_url = mocker.patch('udocker.utils.curl.GetURL', return_value="http://example.com")

    assert dockerioapi.index_url == Config.conf['dockerio_index_url']
    assert dockerioapi.registry_url == Config.conf['dockerio_registry_url']
    assert dockerioapi.localrepo == localrepo
    assert dockerioapi.search_pause
    assert dockerioapi.search_page == 0
    assert not dockerioapi.search_ended
    assert dockerioapi.v1api is not None
    assert dockerioapi.v2api is not None
    # assert dockerioapi.v1_auth_header == ""
    # assert dockerioapi.v2_auth_header == ""
    # assert dockerioapi.v2_auth_token == ""
    assert mock_get_url.called
    assert dockerioapi.curl == mock_get_url.return_value




#         mock_geturl.return_value = None
#         doia = DockerIoAPI(self.local)
#         self.assertEqual(doia.index_url, Config.conf['dockerio_index_url'])
#         self.assertEqual(doia.registry_url, Config.conf['dockerio_registry_url'])
#         self.assertEqual(doia.v1_auth_header, "")
#         self.assertEqual(doia.v2_auth_header, "")
#         self.assertEqual(doia.v2_auth_token, "")
#         self.assertEqual(doia.localrepo, self.local)
#         self.assertTrue(doia.search_pause)
#         self.assertEqual(doia.search_page, 0)
#         self.assertFalse(doia.search_ended)
#         self.assertTrue(mock_geturl.called)
#
#     @patch('udocker.docker.GetURL')

@pytest.mark.parametrize("http_proxy", [
    ("socks5://user:pass@host:port", ),
    ("",),
    (None, ),
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
    # Scenario 1: Set valid index URL
    ("https://index.example.com", "Setting docker index: %s"),

    # Scenario 2: Set empty index URL
    ("", "Setting docker index: %s"),

    # Scenario 3: Set None as index URL
    (None, "Setting docker index: %s"),

    # Scenario 4: Set invalid index URL format
    ("invalidindexformat", "Setting docker index: %s"),
])
def test_04_set_index(mocker, dockerioapi, logger, index_url, expected_log_message):
    """Test04 DockerIoAPI().set_index()."""
    dockerioapi.set_index(index_url)
    logger.info.assert_called_once_with(expected_log_message, index_url)
    assert dockerioapi.index_url == index_url


#         doia = DockerIoAPI(self.local)
#         doia.set_index("https://index.docker.io/v1")
#         self.assertEqual(doia.index_url, "https://index.docker.io/v1")
@pytest.mark.parametrize("imagerepo, expected_result", [
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
def test_05_is_repo_name(dockerioapi, imagerepo, expected_result):
    """Test05 DockerIoAPI().is_repo_name()."""
    result = dockerioapi.is_repo_name(imagerepo)
    assert result == expected_result


@pytest.mark.parametrize("layername, expected_result", [
    # Scenario 1: Valid layer name
    ("abc123@sha256:1a2b3c4d5e", True),

    # Scenario 2: Invalid layer name - Special characters
    ("invalid*layer@sha256:1a2b3c", False),

    # Scenario 3: Invalid layer name - Incorrect format
    ("layername-without@hash", False),

    # Scenario 4: Empty string
    ("", False),

    # Scenario 5: None as input
    (None, False),
])
def test_06__is_layer_name(dockerioapi, layername, expected_result):
    """Test06 DockerIoAPI()._get_url()."""
    result = dockerioapi.is_layer_name(layername)
    assert result == expected_result


@pytest.mark.parametrize("initial_status_code, retry_count, follow_count, final_status_code, expected_result", [
    # Scenario 1: Successful HTTP request
    (200, 3, 3, 200, "Success"),

    # Scenario 2: Exhausted retries
    (500, 0, 3, 500, "Fail"),

    # Scenario 3: Follow redirects
    (302, 3, 1, 200, "Redirected"),

    # Scenario 4: Unauthorized request with retry
    (401, 2, 3, 200, "Authenticated"),

    # Scenario 5: Unauthorized request without valid 'www-authenticate'
    (401, 3, 3, 401, "Unauthorized"),
])
def test_07__get_url(mocker, dockerioapi, initial_status_code, retry_count, follow_count, final_status_code,
                     expected_result):
    """Test07 DockerIoAPI()._get_url()."""
    mock_curl_get = mocker.patch.object(dockerioapi.curl, 'get', side_effect=[
        (
            {"X-ND-HTTPSTATUS": initial_status_code, "location": "http://redirect.location"},
            BytesIO(b"Initial response")),
        ({"X-ND-HTTPSTATUS": final_status_code}, io.BytesIO(b"Final response"))
    ])
    mocker.patch.object(dockerioapi.curl, 'get_status_code', side_effect=lambda x: x)
    mocker.patch.object(dockerioapi.v2api, 'get_auth', return_value="Bearer token")
    mocker.patch.object(dockerioapi.v1api, 'get_auth', return_value="Basic auth")
    # mocker.patch.object(LOG, 'debug')

    url = "http://example.com"
    (hdr, buf) = dockerioapi.get_url(url, RETRY=retry_count, FOLLOW=follow_count)

    assert hdr.data["X-ND-HTTPSTATUS"] == final_status_code
    assert (expected_result in buf.getvalue().decode()) or (
            expected_result == "Unauthorized" and "www-authenticate" not in hdr.data)
    mock_curl_get.assert_called()


#         args = ["http://some1.org"]
#         kwargs = list()
#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase"}
#         buff = strio()
#         mock_get.return_value = (hdr, buff)
#         mock_getstatus.return_value = 200
#         doia = DockerIoAPI(self.local)
#         status = doia._get_url(args, kwargs)
#         self.assertEqual(status, (hdr, buff))
#
#         args = ["http://some1.org"]
#         kwargs = list()
#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0,
#                     "location": "http://some1.org"}
#         buff = strio()
#         mock_get.return_value = (hdr, buff)
#         mock_getstatus.return_value = 400
#         doia = DockerIoAPI(self.local)
#         status = doia._get_url(args, kwargs)
#         self.assertEqual(status, (hdr, buff))
#
#         args = ["http://some1.org"]
#         kwargs = {"RETRY": True, "FOLLOW": True}
#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0}
#         buff = strio()
#         mock_get.return_value = (hdr, buff)
#         mock_getstatus.return_value = 400
#         doia = DockerIoAPI(self.local)
#         status = doia._get_url(args, kwargs)
#         self.assertEqual(status, (hdr, buff))
#
#     @patch.object(DockerIoAPI, '_get_url')
#     @patch('udocker.docker.GetURL.get_status_code')
#     @patch('udocker.docker.FileUtil.size')
#     @patch('udocker.docker.GetURL.get_content_length')
#     @patch('udocker.docker.ChkSUM.hash')

@pytest.mark.parametrize(
    "filename, cache_mode, is_cached, download_status, remote_size, download_success, expected_result", [
        # Scenario 1: File already cached with matching checksum
        ("file@sha256:checksum", 0, True, 200, 100, True, True),

        # Scenario 2: File cached with same remote size
        ("file.txt", 1, False, 200, 100, True, True),
        ("file.txt", 3, False, 200, 100, True, True),

        # Scenario 3: File not cached and successfully downloaded
        ("file.txt", 0, False, 200, 100, True, True),

        # Scenario 4: Download failure with HTTP error
        ("file.txt", 0, False, 404, 100, False, False),

        # Scenario 5: File size mismatch after download
        ("file.txt", 0, False, 200, 100, False, False),

        # Scenario 6: Cache mode off, no size check
        ("file.txt", 0, False, 200, -1, True, True),
    ])
def test_09__get_file(mocker, dockerioapi, filename, cache_mode, is_cached, download_status, remote_size,
                      download_success, expected_result):
    """Test09 DockerIoAPI()._get_file()."""
    mocker.patch('re.search', return_value=is_cached)
    mocker.patch.object(ChkSUM, 'hash', return_value="checksum" if is_cached else "different")
    mocker.patch.object(dockerioapi.curl, 'cache_support', True)
    mocker.patch.object(dockerioapi.curl, 'get_content_length', return_value=remote_size)
    mocker.patch.object(dockerioapi.curl, 'get_status_code', return_value=download_status)
    mocker.patch.object(FileUtil, 'size', return_value=100 if is_cached else 50)
    mocker.patch.object(dockerioapi, 'get_url', return_value=({"X-ND-HTTPSTATUS": download_status}, BytesIO(b"")))
    mocker.patch.object(FileUtil, 'size', side_effect=lambda x: 100 if download_success else 50)
    # mocker.patch.object(LOG, 'error')

    url = "http://example.com/file"
    result = dockerioapi.get_file(url, filename, cache_mode)

    assert result == expected_result


#         cks = "af98ca7807fd3859c5bd876004fa7e960cecebddb342de1bc7f3b0e6f7dab415"
#         url = "http://some1.org/file1"
#         fname = "/sha256:" + cks
#         cache = 0
#         mock_hash.return_value = cks
#         doia = DockerIoAPI(self.local)
#         status = doia._get_file(url, fname, cache)
#         self.assertTrue(status)
#
#         cks = "af98ca7807fd3859c5bd876004fa7e960cecebddb342de1bc7f3b0e6f7dab415"
#         url = "http://some1.org/file1"
#         fname = ""
#         cache = 1
#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0}
#         buff = strio()
#         mock_hash.return_value = cks
#         mock_geturl.return_value = (hdr, buff)
#         mock_getlength.return_value = 123
#         mock_fusize.return_value = 123
#         doia = DockerIoAPI(self.local)
#         doia.curl.cache_support = True
#         status = doia._get_file(url, fname, cache)
#         self.assertTrue(status)
#
#         cks = "af98ca7807fd3859c5bd876004fa7e960cecebddb342de1bc7f3b0e6f7dab415"
#         url = "http://some1.org/file1"
#         fname = cks + ".layer"
#         cache = 0
#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0}
#         buff = strio()
#         mock_hash.return_value = cks
#         mock_geturl.return_value = (hdr, buff)
#         mock_getlength.return_value = 123
#         mock_fusize.return_value = 123
#         mock_status.return_value = 200
#         doia = DockerIoAPI(self.local)
#         doia.curl.cache_support = False
#         status = doia._get_file(url, fname, cache)
#         self.assertTrue(status)
#
def test_08__split_fields(mocker):
    """Test08 DockerIoAPI()._split_fields()."""


#         buff = 'k1="v1",k2="v2"'
#         doia = DockerIoAPI(self.local)
#         status = doia._split_fields(buff)
#         self.assertEqual(status, {"k1": "v1", "k2": "v2"})
#
#     @patch.object(DockerIoAPI, '_get_url')
def test_09_is_v1(mocker):
    """Test09 DockerIoAPI().is_v1()."""


#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0}
#         buff = strio()
#         mock_geturl.return_value = (hdr, buff)
#         doia = DockerIoAPI(self.local)
#         status = doia.is_v1()
#         self.assertTrue(status)
#
#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0}
#         buff = strio()
#         mock_geturl.return_value = (hdr, buff)
#         doia = DockerIoAPI(self.local)
#         status = doia.is_v1()
#         self.assertFalse(status)
#
#     @patch.object(DockerIoAPI, '_get_url')
def test_10_has_search_v1(mocker):
    """Test10 DockerIoAPI().has_search_v1()."""


#         url = "http://some1.org/file1"
#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0}
#         buff = strio()
#         mock_geturl.return_value = (hdr, buff)
#         doia = DockerIoAPI(self.local)
#         status = doia.has_search_v1(url)
#         self.assertTrue(status)
#
#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0}
#         buff = strio()
#         mock_geturl.return_value = (hdr, buff)
#         doia = DockerIoAPI(self.local)
#         status = doia.has_search_v1(url)
#         self.assertFalse(status)
#
#     @patch('udocker.docker.json.loads')
#     @patch.object(DockerIoAPI, '_get_url')
def test_11_get_v1_repo(self, mock_geturl, mock_jload):
    """Test11 DockerIoAPI().get_v1_repo"""


#         imagerepo = "REPO"
#         hdr = type('test', (object,), {})()
#         hdr.data = {"x-docker-token": "12345"}
#         buff = strio()
#         mock_geturl.return_value = (hdr, buff)
#         mock_jload.return_value = {"k1": "v1"}
#         doia = DockerIoAPI(self.local)
#         doia.index_url = "docker.io"
#         status = doia.get_v1_repo(imagerepo)
#         self.assertEqual(status, ({"x-docker-token": "12345"}, {"k1": "v1"}))
#
def test_12__get_v1_auth(self):
    """Test12 DockerIoAPI()._get_v1_auth"""


#         doia = DockerIoAPI(self.local)
#         doia.v1_auth_header = "Not Empty"
#         www_authenticate = ['Other Stuff']
#         out = doia._get_v1_auth(www_authenticate)
#         self.assertEqual(out, "")
#
#         www_authenticate = ['Token']
#         doia = DockerIoAPI(self.local)
#         doia.v1_auth_header = "Not Empty"
#         out = doia._get_v1_auth(www_authenticate)
#         self.assertEqual(out, "Not Empty")
#
#     @patch('udocker.utils.curl.CurlHeader')
#     @patch.object(DockerIoAPI, '_get_url')
def test_13_get_v1_image_tags(self, mock_dgu, mock_hdr):
    """Test13 DockerIoAPI().get_v1_image_tags"""


#         mock_dgu.return_value = (mock_hdr, [])
#         endpoint = "docker.io"
#         imagerepo = "REPO"
#         doia = DockerIoAPI(self.local)
#         out = doia.get_v1_image_tags(endpoint, imagerepo)
#         self.assertIsInstance(out, list)
#
#     @patch('udocker.utils.curl.CurlHeader')
#     @patch.object(DockerIoAPI, '_get_url')
def test_14_get_v1_image_tag(self, mock_dgu, mock_hdr):
    """Test14 DockerIoAPI().get_v1_image_tag"""


#         mock_dgu.return_value = (mock_hdr, [])
#         endpoint = "docker.io"
#         imagerepo = "REPO"
#         tag = "TAG"
#         doia = DockerIoAPI(self.local)
#         out = doia.get_v1_image_tag(endpoint, imagerepo, tag)
#         self.assertIsInstance(out, tuple)
#
#     @patch('udocker.utils.curl.CurlHeader')
#     @patch.object(DockerIoAPI, '_get_url')
def test_15_get_v1_image_ancestry(self, mock_dgu, mock_hdr):
    """Test15 DockerIoAPI().get_v1_image_ancestry"""


#         mock_dgu.return_value = (mock_hdr, [])
#         endpoint = "docker.io"
#         image_id = "IMAGEID"
#         doia = DockerIoAPI(self.local)
#         out = doia.get_v1_image_ancestry(endpoint, image_id)
#         self.assertIsInstance(out, tuple)
#
#     @patch.object(DockerIoAPI, '_get_file')
def test_16_get_v1_image_json(self, mock_dgf):
    """Test16 DockerIoAPI().get_v1_image_json"""
    #         mock_dgf.return_value = True
    #         endpoint = "docker.io"
    #         layer_id = "LAYERID"
    #         doia = DockerIoAPI(self.local)
    #         status = doia.get_v1_image_json(endpoint, layer_id)
    #         self.assertTrue(status)
    #
    #         mock_dgf.return_value = False
    #         doia = DockerIoAPI(self.local)
    #         status = doia.get_v1_image_json(endpoint, layer_id)
    #         self.assertFalse(status)
    #
    #     @patch.object(DockerIoAPI, '_get_file')


def test_17_get_v1_image_layer(self, mock_dgf):
    """Test17 DockerIoAPI().get_v1_image_layer"""
    #         mock_dgf.return_value = True
    #         endpoint = "docker.io"
    #         layer_id = "LAYERID"
    #         doia = DockerIoAPI(self.local)
    #         status = doia.get_v1_image_layer(endpoint, layer_id)
    #         self.assertTrue(status)
    #
    #         mock_dgf.return_value = False
    #         doia = DockerIoAPI(self.local)
    #         status = doia.get_v1_image_layer(endpoint, layer_id)
    #         self.assertFalse(status)
    #
    #     @patch.object(DockerIoAPI, '_get_file')


def test_18_get_v1_layers_all(self, mock_dgf):
    """Test18 DockerIoAPI().get_v1_layers_all"""
    #         mock_dgf.return_value = True
    #         endpoint = "docker.io"
    #         layer_list = []
    #         doia = DockerIoAPI(self.local)
    #         out = doia.get_v1_layers_all(endpoint, layer_list)
    #         self.assertEqual(out, [])
    #
    #         layer_list = ["a", "b"]
    #         doia = DockerIoAPI(self.local)
    #         out = doia.get_v1_layers_all(endpoint, layer_list)
    #         self.assertEqual(out, ['b.json', 'b.layer', 'a.json', 'a.layer'])
    #
    #     @patch.object(DockerIoAPI, '_get_url')
    #     @patch('udocker.utils.curl.CurlHeader')
    #     @patch('udocker.docker.json.loads')


def test_19__get_v2_auth(self, mock_jloads, mock_hdr, mock_dgu):
    """Test19 DockerIoAPI()._get_v2_auth"""
    #         fakedata = strio('token'.encode('utf-8'))
    #         www_authenticate = "Other Stuff"
    #         mock_dgu.return_value = (mock_hdr, fakedata)
    #         mock_jloads.return_value = {'token': 'YYY'}
    #         doia = DockerIoAPI(self.local)
    #         doia.v2_auth_header = "v2 Auth Header"
    #         doia.v2_auth_token = "v2 Auth Token"
    #         out = doia._get_v2_auth(www_authenticate, False)
    #         self.assertEqual(out, "")
    #
    #         www_authenticate = "Bearer realm=REALM"
    #         mock_dgu.return_value = (mock_hdr, fakedata)
    #         mock_jloads.return_value = {'token': 'YYY'}
    #         doia = DockerIoAPI(self.local)
    #         out = doia._get_v2_auth(www_authenticate, False)
    #         self.assertEqual(out, "Authorization: Bearer YYY")
    #
    #         www_authenticate = "BASIC realm=Sonatype Nexus Repository"
    #         mock_dgu.return_value = (mock_hdr, fakedata)
    #         mock_jloads.return_value = {'token': 'YYY'}
    #         doia = DockerIoAPI(self.local)
    #         out = doia._get_v2_auth(www_authenticate, False)
    #         self.assertEqual(out, "Authorization: Basic %s" % doia.v2_auth_token)
    #


def test_20_get_v2_login_token(self):
    """Test20 DockerIoAPI().get_v2_login_token"""
    #         doia = DockerIoAPI(self.local)
    #         out = doia.get_v2_login_token("username", "password")
    #         self.assertIsInstance(out, str)
    #
    #         doia = DockerIoAPI(self.local)
    #         out = doia.get_v2_login_token("", "")
    #         self.assertEqual(out, "")
    #


def test_21_set_v2_login_token(self):
    """Test21 DockerIoAPI().set_v2_login_token"""
    #         doia = DockerIoAPI(self.local)
    #         doia.set_v2_login_token("BIG-FAT-TOKEN")
    #         self.assertEqual(doia.v2_auth_token, "BIG-FAT-TOKEN")
    #
    #     @patch('udocker.utils.curl.CurlHeader')
    #     @patch.object(DockerIoAPI, '_get_url')


def test_22_is_v2(self, mock_dgu, mock_hdr):
    """Test22 DockerIoAPI().is_v2"""
    #         mock_dgu.return_value = (mock_hdr, [])
    #         doia = DockerIoAPI(self.local)
    #         doia.registry_url = "http://www.docker.io"
    #         out = doia.is_v2()
    #         self.assertFalse(out)
    #
    #         hdr = type('test', (object,), {})()
    #         hdr.data = {"content-length": 10,
    #                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
    #                     "X-ND-CURLSTATUS": 0}
    #         buff = strio()
    #         mock_dgu.return_value = (hdr, buff)
    #         doia = DockerIoAPI(self.local)
    #         doia.registry_url = "https://registry-1.docker.io"
    #         out = doia.is_v2()
    #         self.assertTrue(out)
    #
    # @patch.object(DockerIoAPI, '_get_url')


def test_23_has_search_v2(self, mock_dgu):
    """Test23 DockerIoAPI().has_search_v2"""


#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0}
#         buff = strio()
#         mock_dgu.return_value = (hdr, buff)
#         doia = DockerIoAPI(self.local)
#         doia.registry_url = "http://www.docker.io"
#         out = doia.has_search_v2()
#         self.assertFalse(out)
#
#         hdr = type('test', (object,), {})()
#         hdr.data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0}
#         buff = strio()
#         mock_dgu.return_value = (hdr, buff)
#         doia = DockerIoAPI(self.local)
#         doia.registry_url = "https://registry-1.docker.io"
#         out = doia.has_search_v2()
#         self.assertTrue(out)
#
#     @patch('udocker.docker.json.loads')
#     @patch.object(DockerIoAPI, '_get_url')


def test_24_get_v2_image_tags(self, mock_dgu, mock_jload):
    """Test24 DockerIoAPI().get_v2_image_tags"""
    #         imgrepo = "img1"
    #         hdr = type('test', (object,), {})()
    #         hdr.data = {"content-length": 10,
    #                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
    #                     "X-ND-CURLSTATUS": 0}
    #         buff = strio()
    #         mock_dgu.return_value = (hdr, buff)
    #         mock_jload.return_value = list()
    #         doia = DockerIoAPI(self.local)
    #         doia.registry_url = "https://registry-1.docker.io"
    #         out = doia.get_v2_image_tags(imgrepo)
    #         self.assertEqual(out, list())
    #
    #         imgrepo = "img1"
    #         hdr = type('test', (object,), {})()
    #         hdr.data = {"content-length": 10,
    #                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
    #                     "X-ND-CURLSTATUS": 0}
    #         buff = strio()
    #         mock_dgu.return_value = (hdr, buff)
    #         mock_jload.return_value = ["tag1", "tag2"]
    #         doia = DockerIoAPI(self.local)
    #         doia.registry_url = "https://registry-1.docker.io"
    #         out = doia.get_v2_image_tags(imgrepo)
    #         self.assertEqual(out, ["tag1", "tag2"])
    #
    #     @patch('udocker.utils.curl.CurlHeader')
    #     @patch.object(DockerIoAPI, '_get_url')


def test_25_get_v2_image_manifest(self, mock_dgu, mock_hdr):
    """Test25 DockerIoAPI().get_v2_image_manifest"""
    #         imagerepo = "REPO"
    #         tag = "TAG"
    #         mock_dgu.return_value = (mock_hdr, [])
    #         doia = DockerIoAPI(self.local)
    #         doia.registry_url = "https://registry-1.docker.io"
    #         out = doia.get_v2_image_manifest(imagerepo, tag)
    #         self.assertIsInstance(out, tuple)
    #
    #     @patch.object(DockerIoAPI, '_get_file')


def test_26_get_v2_image_layer(self, mock_dgf):
    """Test26 DockerIoAPI().get_v2_image_layer"""
    #         imagerepo = "REPO"
    #         layer_id = "LAYERID"
    #         doia = DockerIoAPI(self.local)
    #         doia.registry_url = "https://registry-1.docker.io"
    #
    #         mock_dgf.return_value = True
    #         doia = DockerIoAPI(self.local)
    #         out = doia.get_v2_image_layer(imagerepo, layer_id)
    #         self.assertTrue(out)
    #
    #         mock_dgf.return_value = False
    #         doia = DockerIoAPI(self.local)
    #         out = doia.get_v2_image_layer(imagerepo, layer_id)
    #         self.assertFalse(out)
    #
    #     @patch.object(DockerIoAPI, 'get_v2_image_layer')


def test_27_get_v2_layers_all(self, mock_v2il):
    """Test27 DockerIoAPI().get_v2_layers_all"""
    #         mock_v2il.return_value = False
    #         imagerepo = "REPO"
    #         fslayers = []
    #         doia = DockerIoAPI(self.local)
    #         out = doia.get_v2_layers_all(imagerepo, fslayers)
    #         self.assertEqual(out, [])
    #
    #         mock_v2il.return_value = True
    #         imagerepo = "REPO"
    #         fslayers = [{"blobSum": "foolayername"}]
    #         doia = DockerIoAPI(self.local)
    #         out = doia.get_v2_layers_all(imagerepo, fslayers)
    #         self.assertEqual(out, ['foolayername'])
    #
    #     @patch('udocker.docker.GetURL.get_status_code')
    #     @patch.object(DockerIoAPI, 'get_v2_image_manifest')
    #     @patch.object(DockerIoAPI, 'get_v2_layers_all')
    #     @patch.object(DockerIoAPI, '_get_url')


def test_28_get_v2(self, mock_dgu, mock_dgv2, mock_manif, mock_getstatus):
    """Test28 DockerIoAPI().get_v2"""
    #         imgrepo = "img1"
    #         hdr = type('test', (object,), {})()
    #         hdr_data = {"content-length": 10,
    #                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
    #                     "X-ND-CURLSTATUS": 0}
    #         hdr.data = hdr_data
    #         buff = strio()
    #         manifest = list()
    #         mock_dgu.return_value = (hdr, buff)
    #         mock_manif.return_value = (hdr_data, manifest)
    #         mock_dgv2.return_value = []
    #         mock_getstatus.return_value = 400
    #         tag = "TAG"
    #         doia = DockerIoAPI(self.local)
    #         doia.registry_url = "https://registry-1.docker.io"
    #         out = doia.get_v2(imgrepo, tag)
    #         self.assertEqual(out, [])
    #
    #         mock_dgu.return_value = (hdr, buff)
    #         mock_manif.return_value = (hdr_data, manifest)
    #         mock_dgv2.return_value = []
    #         mock_getstatus.return_value = 200
    #         self.local.setup_tag.return_value = False
    #         self.local.set_version.return_value = True
    #         doia = DockerIoAPI(self.local)
    #         doia.registry_url = "https://registry-1.docker.io"
    #         out = doia.get_v2(imgrepo, tag)
    #         self.assertEqual(out, [])
    #
    #         manifest = {
    #             "fsLayers": ({"blobSum": "foolayername"},),
    #             "history": ({"v1Compatibility": '["foojsonstring"]'},)
    #         }
    #         mock_dgu.return_value = (hdr, buff)
    #         mock_manif.return_value = (hdr_data, manifest)
    #         mock_dgv2.return_value = ["foolayername"]
    #         mock_getstatus.return_value = 200
    #         self.local.setup_tag.return_value = True
    #         self.local.set_version.return_value = True
    #         self.local.save_json.return_value = None
    #         doia = DockerIoAPI(self.local)
    #         doia.registry_url = "https://registry-1.docker.io"
    #         out = doia.get_v2(imgrepo, tag)
    #         self.assertEqual(out, ["foolayername"])
    #


def test_29__get_v1_id_from_tags(self):
    """Test29 DockerIoAPI()._get_v1_id_from_tags"""


#         tobj = {"tag1": "t1"}
#         tag = "tag1"
#         doia = DockerIoAPI(self.local)
#         out = doia._get_v1_id_from_tags(tobj, tag)
#         self.assertEqual(out, "t1")
#
#         tobj = [{"name": "tag1", "layer": "l1"}]
#         tag = "tag1"
#         doia = DockerIoAPI(self.local)
#         out = doia._get_v1_id_from_tags(tobj, tag)
#         self.assertEqual(out, "l1")
#
def test_30__get_v1_id_from_images(mocker):
    """Test30 DockerIoAPI()._get_v1_id_from_images"""


#         imgarr = list()
#         shortid = ""
#         doia = DockerIoAPI(self.local)
#         out = doia._get_v1_id_from_images(imgarr, shortid)
#         self.assertEqual(out, "")
#
#         imgarr = [{"id": "1234567890"}]
#         shortid = "12345678"
#         doia = DockerIoAPI(self.local)
#         out = doia._get_v1_id_from_images(imgarr, shortid)
#         self.assertEqual(out, "1234567890")
#
#     @patch('udocker.docker.GetURL.get_status_code')
#     @patch.object(DockerIoAPI, 'get_v1_layers_all')
#     @patch.object(DockerIoAPI, 'get_v1_image_ancestry')
#     @patch.object(DockerIoAPI, '_get_v1_id_from_images')
#     @patch.object(DockerIoAPI, '_get_v1_id_from_tags')
#     @patch.object(DockerIoAPI, 'get_v1_image_tags')
#     @patch.object(DockerIoAPI, 'get_v1_repo')
def test_31_get_v1(self, mock_dgv1repo, mock_v1imgtag, mock_v1idtag, mock_v1idimg, mock_v1ances,
                   mock_v1layer, mock_status):
    """Test31 DockerIoAPI().get_v1"""


#         imgarr = [{"id": "1234567890"}]
#         imagerepo = "REPO"
#         tag = "TAG"
#         hdr = type('test', (object,), {})()
#         hdr_data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0,
#                     "x-docker-endpoints": "https://registry-1.docker.io"}
#         hdr.data = hdr_data
#         mock_dgv1repo.return_value = (hdr_data, imgarr)
#         mock_status.return_value = 401
#         doia = DockerIoAPI(self.local)
#         out = doia.get_v1(imagerepo, tag)
#         self.assertEqual(out, [])
#
#         mock_v1imgtag.return_value = [{"name": "tag1"}]
#         mock_v1idtag.return_value = ""
#         mock_dgv1repo.return_value = (hdr_data, imgarr)
#         mock_status.return_value = 200
#         doia = DockerIoAPI(self.local)
#         out = doia.get_v1(imagerepo, tag)
#         self.assertEqual(out, [])
#
#         mock_v1imgtag.return_value = [{"name": "tag1"}]
#         mock_v1idtag.return_value = "123456"
#         mock_v1idimg.return_value = ""
#         mock_dgv1repo.return_value = (hdr_data, imgarr)
#         mock_status.return_value = 200
#         doia = DockerIoAPI(self.local)
#         out = doia.get_v1(imagerepo, tag)
#         self.assertEqual(out, [])
#
#         mock_v1imgtag.return_value = [{"name": "tag1"}]
#         mock_v1idtag.return_value = "123456"
#         mock_v1idimg.return_value = "123456789"
#         mock_dgv1repo.return_value = (hdr_data, imgarr)
#         mock_status.return_value = 200
#         self.local.setup_tag.return_value = False
#         self.local.set_version.return_value = True
#         doia = DockerIoAPI(self.local)
#         out = doia.get_v1(imagerepo, tag)
#         self.assertEqual(out, [])
#
#         mock_v1imgtag.return_value = [{"name": "tag1"}]
#         mock_v1idtag.return_value = "123456"
#         mock_v1idimg.return_value = "123456789"
#         mock_dgv1repo.return_value = (hdr_data, imgarr)
#         mock_status.return_value = 200
#         mock_v1ances.return_value = ("x", "")
#         self.local.setup_tag.return_value = True
#         self.local.set_version.return_value = True
#         self.local.save_json.return_value = None
#         doia = DockerIoAPI(self.local)
#         out = doia.get_v1(imagerepo, tag)
#         self.assertEqual(out, [])
#
#         mock_v1imgtag.return_value = [{"name": "tag1"}]
#         mock_v1idtag.return_value = "123456"
#         mock_v1idimg.return_value = "123456789"
#         mock_dgv1repo.return_value = (hdr_data, imgarr)
#         mock_status.return_value = 200
#         mock_v1ances.return_value = ("x", "123")
#         mock_v1layer.return_value = ["file1"]
#         self.local.setup_tag.return_value = True
#         self.local.set_version.return_value = True
#         self.local.save_json.return_value = None
#         doia = DockerIoAPI(self.local)
#         out = doia.get_v1(imagerepo, tag)
#         self.assertEqual(out, ["file1"])
#
def test_32__parse_imagerepo(self):
    """Test32 DockerIoAPI()._parse_imagerepo"""


#         imagerepo = "https://hub.docker.com/_/mysql"
#         doia = DockerIoAPI(self.local)
#         out = doia._parse_imagerepo(imagerepo)
#         self.assertEqual(out, (imagerepo, "https://hub.docker.com/_/mysql"))
#
#     @patch.object(DockerIoAPI, 'get_v1')
#     @patch.object(DockerIoAPI, 'get_v2')
#     @patch.object(DockerIoAPI, 'is_v2')
#     @patch.object(DockerIoAPI, '_parse_imagerepo')
def test_33_get(self, mock_parse, mock_isv2, mock_getv2, mock_getv1):
    """Test33 DockerIoAPI().get"""


#         imagerepo = "REPO"
#         tag = "TAG"
#         mock_parse.return_value = ("REPO", "https://registry-1.docker.io")
#         self.local.cd_imagerepo.return_value = False
#         self.local.setup_imagerepo.return_value = True
#         self.local.del_imagerepo.return_value = False
#         mock_isv2.return_value = False
#         mock_getv1.return_value = ["a", "b"]
#         doia = DockerIoAPI(self.local)
#         out = doia.get(imagerepo, tag)
#         self.assertEqual(out, ["a", "b"])
#
#         mock_parse.return_value = ("REPO", "https://registry-1.docker.io")
#         self.local.cd_imagerepo.return_value = True
#         self.local.setup_imagerepo.return_value = True
#         self.local.del_imagerepo.return_value = False
#         mock_isv2.return_value = True
#         mock_getv2.return_value = ["a", "b"]
#         doia = DockerIoAPI(self.local)
#         out = doia.get(imagerepo, tag)
#         self.assertEqual(out, ["a", "b"])
#
#     @patch.object(DockerIoAPI, 'get_v1_image_tags')
#     @patch.object(DockerIoAPI, 'get_v2_image_tags')
#     @patch.object(DockerIoAPI, 'is_v2')
def test_34_get_tags(self, mock_isv2, mock_getv2, mock_getv1):
    """Test34 DockerIoAPI().get_tags"""


#         imagerepo = "REPO"
#         mock_isv2.return_value = False
#         mock_getv1.return_value = ["a", "b"]
#         doia = DockerIoAPI(self.local)
#         out = doia.get_tags(imagerepo)
#         self.assertEqual(out, ["a", "b"])
#
#         mock_isv2.return_value = True
#         mock_getv2.return_value = ["a", "b"]
#         doia = DockerIoAPI(self.local)
#         out = doia.get_tags(imagerepo)
#         self.assertEqual(out, ["a", "b"])
#
def test_35_search_init(self):
    """Test35 DockerIoAPI().search_init"""


#         doia = DockerIoAPI(self.local)
#         doia.search_init("PAUSE")
#         self.assertEqual(doia.search_pause, "PAUSE")
#         self.assertEqual(doia.search_page, 0)
#         self.assertEqual(doia.search_ended, False)
#
#     @patch.object(DockerIoAPI, '_get_url')
#     @patch('udocker.docker.json.loads')
def test_36_search_get_page_v1(self, mock_jload, mock_dgu):
    """Test36 DockerIoAPI().set_index"""


#         hdr = type('test', (object,), {})()
#         hdr_data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0,
#                     "x-docker-endpoints": "https://registry-1.docker.io"}
#         hdr.data = hdr_data
#         buff = strio()
#         mock_dgu.return_value = (hdr, buff)
#         mock_jload.return_value = {"page": 1, "num_pages": 1}
#         url = "https://registry-1.docker.io"
#         doia = DockerIoAPI(self.local)
#         out = doia.search_get_page_v1("SOMETHING", url)
#         self.assertEqual(out, {"page": 1, "num_pages": 1})
#
#     @patch.object(DockerIoAPI, '_get_url')
#     @patch('udocker.docker.json.loads')
def test_37_search_get_page_v2(self, mock_jload, mock_dgu):
    """Test37 DockerIoAPI().search_get_page_v2"""


#         hdr = type('test', (object,), {})()
#         hdr_data = {"content-length": 10,
#                     "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
#                     "X-ND-CURLSTATUS": 0,
#                     "x-docker-endpoints": "https://registry-1.docker.io"}
#         hdr.data = hdr_data
#         buff = strio()
#         mock_dgu.return_value = (hdr, buff)
#         mock_jload.return_value = {"count": 1, "num_pages": 1}
#         url = "https://registry-1.docker.io"
#         doia = DockerIoAPI(self.local)
#         out = doia.search_get_page_v2("SOMETHING", url)
#         self.assertEqual(out, {"count": 1, "num_pages": 1})
#
#     @patch.object(DockerIoAPI, 'search_get_page_v1')
#     @patch.object(DockerIoAPI, 'search_get_page_v2')
#     @patch.object(DockerIoAPI, 'has_search_v1')
#     @patch.object(DockerIoAPI, 'has_search_v2')
def test_38_search_get_page(self, mock_searchv2, mock_searchv1,
                            mock_getv2, mock_getv1):
    """Test38 DockerIoAPI().search_get_page"""
#         mock_searchv2.return_value = True
#         mock_searchv1.return_value = False
#         mock_getv2.return_value = {"count": 1, "num_pages": 1}
#         mock_getv1.return_value = {"page": 1, "num_pages": 1}
#         doia = DockerIoAPI(self.local)
#         out = doia.search_get_page("SOMETHING")
#         self.assertEqual(out, {"count": 1, "num_pages": 1})
#
#         mock_searchv2.return_value = False
#         mock_searchv1.return_value = True
#         mock_getv2.return_value = {"count": 1, "num_pages": 1}
#         mock_getv1.return_value = {"page": 1, "num_pages": 1}
#         doia = DockerIoAPI(self.local)
#         out = doia.search_get_page("SOMETHING")
#         self.assertEqual(out, {"page": 1, "num_pages": 1})
#
#
# if __name__ == '__main__':
#     main()
