#!/usr/bin/env python
"""
udocker unit tests: DockerIoAPI
"""

from unittest import TestCase, main
from unittest.mock import patch, Mock
from io import BytesIO as strio
from udocker.docker import DockerIoAPI
from udocker.config import Config


class DockerIoAPITestCase(TestCase):
    """Test DockerIoAPITest().
    Class to encapsulate the access to the Docker Hub service.
    Allows to search and download images from Docker Hub.
    """

    def setUp(self):
        Config().getconf()
        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

    def tearDown(self):
        self.lrepo.stop()

    @patch('udocker.docker.GetURL')
    def test_01_init(self, mock_geturl):
        """Test01 DockerIoAPI() constructor"""
        mock_geturl.return_value = None
        doia = DockerIoAPI(self.local)
        self.assertEqual(doia.index_url,
                         Config.conf['dockerio_index_url'])
        self.assertEqual(doia.registry_url,
                         Config.conf['dockerio_registry_url'])
        self.assertEqual(doia.v1_auth_header, "")
        self.assertEqual(doia.v2_auth_header, "")
        self.assertEqual(doia.v2_auth_token, "")
        self.assertEqual(doia.localrepo, self.local)
        self.assertTrue(doia.search_pause)
        self.assertEqual(doia.search_page, 0)
        self.assertFalse(doia.search_ended)
        self.assertTrue(mock_geturl.called)

    @patch('udocker.docker.GetURL')
    def test_02_set_proxy(self, mock_geturl):
        """Test02 DockerIoAPI().set_proxy()."""
        url = "socks5://user:pass@host:port"
        doia = DockerIoAPI(self.local)
        doia.set_proxy(url)
        self.assertTrue(mock_geturl.return_value.set_proxy.called_with(url))

    def test_03_set_registry(self):
        """Test03 DockerIoAPI().set_registry()."""
        doia = DockerIoAPI(self.local)
        doia.set_registry("https://registry-1.docker.io")
        self.assertEqual(doia.registry_url, "https://registry-1.docker.io")

    def test_04_set_index(self):
        """Test04 DockerIoAPI().set_index()."""
        doia = DockerIoAPI(self.local)
        doia.set_index("https://index.docker.io/v1")
        self.assertEqual(doia.index_url, "https://index.docker.io/v1")

    def test_05_is_repo_name(self):
        """Test05 DockerIoAPI().is_repo_name()."""
        doia = DockerIoAPI(self.local)
        self.assertFalse(doia.is_repo_name(""))
        self.assertFalse(doia.is_repo_name("socks5://user:pass@host:port"))
        self.assertFalse(doia.is_repo_name("/:"))
        self.assertTrue(doia.is_repo_name("1233/fasdfasdf:sdfasfd"))
        self.assertTrue(doia.is_repo_name("os-cli-centos7"))
        self.assertTrue(doia.is_repo_name("os-cli-centos7:latest"))
        self.assertTrue(doia.is_repo_name("lipcomputing/os-cli-centos7"))
        self.assertTrue(doia.is_repo_name("lipcomputing/os-cli-centos7:latest"))

    @patch('udocker.docker.GetURL.get_status_code')
    @patch('udocker.docker.GetURL.get')
    def test_06__get_url(self, mock_get, mock_getstatus):
        """Test06 DockerIoAPI()._get_url()."""
        args = ["http://some1.org"]
        kwargs = list()
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase"}
        buff = strio()
        mock_get.return_value = (hdr, buff)
        mock_getstatus.return_value = 200
        doia = DockerIoAPI(self.local)
        status = doia._get_url(args, kwargs)
        self.assertEqual(status, (hdr, buff))

        args = ["http://some1.org"]
        kwargs = list()
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0,
                    "location": "http://some1.org"}
        buff = strio()
        mock_get.return_value = (hdr, buff)
        mock_getstatus.return_value = 400
        doia = DockerIoAPI(self.local)
        status = doia._get_url(args, kwargs)
        self.assertEqual(status, (hdr, buff))

        args = ["http://some1.org"]
        kwargs = {"RETRY": True, "FOLLOW": True}
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_get.return_value = (hdr, buff)
        mock_getstatus.return_value = 400
        doia = DockerIoAPI(self.local)
        status = doia._get_url(args, kwargs)
        self.assertEqual(status, (hdr, buff))

    @patch.object(DockerIoAPI, '_get_url')
    @patch('udocker.docker.GetURL.get_status_code')
    @patch('udocker.docker.FileUtil.size')
    @patch('udocker.docker.GetURL.get_content_length')
    @patch('udocker.docker.ChkSUM.hash')
    def test_07__get_file(self, mock_hash, mock_getlength,
                          mock_fusize, mock_status, mock_geturl):
        """Test07 DockerIoAPI()._get_file()."""
        cks = "af98ca7807fd3859c5bd876004fa7e960cecebddb342de1bc7f3b0e6f7dab415"
        url = "http://some1.org/file1"
        fname = "/sha256:" + cks
        cache = 0
        mock_hash.return_value = cks
        doia = DockerIoAPI(self.local)
        status = doia._get_file(url, fname, cache)
        self.assertTrue(status)

        cks = "af98ca7807fd3859c5bd876004fa7e960cecebddb342de1bc7f3b0e6f7dab415"
        url = "http://some1.org/file1"
        fname = ""
        cache = 1
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_hash.return_value = cks
        mock_geturl.return_value = (hdr, buff)
        mock_getlength.return_value = 123
        mock_fusize.return_value = 123
        doia = DockerIoAPI(self.local)
        doia.curl.cache_support = True
        status = doia._get_file(url, fname, cache)
        self.assertTrue(status)

        cks = "af98ca7807fd3859c5bd876004fa7e960cecebddb342de1bc7f3b0e6f7dab415"
        url = "http://some1.org/file1"
        fname = cks + ".layer"
        cache = 0
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_hash.return_value = cks
        mock_geturl.return_value = (hdr, buff)
        mock_getlength.return_value = 123
        mock_fusize.return_value = 123
        mock_status.return_value = 200
        doia = DockerIoAPI(self.local)
        doia.curl.cache_support = False
        status = doia._get_file(url, fname, cache)
        self.assertTrue(status)

    def test_08__split_fields(self):
        """Test08 DockerIoAPI()._split_fields()."""
        buff = 'k1="v1",k2="v2"'
        doia = DockerIoAPI(self.local)
        status = doia._split_fields(buff)
        self.assertEqual(status, {"k1": "v1", "k2": "v2"})

    @patch.object(DockerIoAPI, '_get_url')
    def test_09_is_v1(self, mock_geturl):
        """Test09 DockerIoAPI().is_v1()."""
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_geturl.return_value = (hdr, buff)
        doia = DockerIoAPI(self.local)
        status = doia.is_v1()
        self.assertTrue(status)

        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_geturl.return_value = (hdr, buff)
        doia = DockerIoAPI(self.local)
        status = doia.is_v1()
        self.assertFalse(status)

    @patch.object(DockerIoAPI, '_get_url')
    def test_10_has_search_v1(self, mock_geturl):
        """Test10 DockerIoAPI().has_search_v1()."""
        url = "http://some1.org/file1"
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_geturl.return_value = (hdr, buff)
        doia = DockerIoAPI(self.local)
        status = doia.has_search_v1(url)
        self.assertTrue(status)

        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_geturl.return_value = (hdr, buff)
        doia = DockerIoAPI(self.local)
        status = doia.has_search_v1(url)
        self.assertFalse(status)

    @patch('udocker.docker.json.loads')
    @patch.object(DockerIoAPI, '_get_url')
    def test_11_get_v1_repo(self, mock_geturl, mock_jload):
        """Test11 DockerIoAPI().get_v1_repo"""
        imagerepo = "REPO"
        hdr = type('test', (object,), {})()
        hdr.data = {"x-docker-token": "12345"}
        buff = strio()
        mock_geturl.return_value = (hdr, buff)
        mock_jload.return_value = {"k1": "v1"}
        doia = DockerIoAPI(self.local)
        doia.index_url = "docker.io"
        status = doia.get_v1_repo(imagerepo)
        self.assertEqual(status, ({"x-docker-token": "12345"}, {"k1": "v1"}))

    def test_12__get_v1_auth(self):
        """Test12 DockerIoAPI()._get_v1_auth"""
        doia = DockerIoAPI(self.local)
        doia.v1_auth_header = "Not Empty"
        www_authenticate = ['Other Stuff']
        out = doia._get_v1_auth(www_authenticate)
        self.assertEqual(out, "")

        www_authenticate = ['Token']
        doia = DockerIoAPI(self.local)
        doia.v1_auth_header = "Not Empty"
        out = doia._get_v1_auth(www_authenticate)
        self.assertEqual(out, "Not Empty")

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_13_get_v1_image_tags(self, mock_dgu, mock_hdr, mock_msg):
        """Test13 DockerIoAPI().get_v1_image_tags"""
        mock_msg.level = 0
        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        imagerepo = "REPO"
        doia = DockerIoAPI(self.local)
        out = doia.get_v1_image_tags(endpoint, imagerepo)
        self.assertIsInstance(out, list)

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_14_get_v1_image_tag(self, mock_dgu, mock_hdr, mock_msg):
        """Test14 DockerIoAPI().get_v1_image_tag"""
        mock_msg.level = 0
        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(self.local)
        out = doia.get_v1_image_tag(endpoint, imagerepo, tag)
        self.assertIsInstance(out, tuple)

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_15_get_v1_image_ancestry(self, mock_dgu, mock_hdr, mock_msg):
        """Test15 DockerIoAPI().get_v1_image_ancestry"""
        mock_msg.level = 0
        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        image_id = "IMAGEID"
        doia = DockerIoAPI(self.local)
        out = doia.get_v1_image_ancestry(endpoint, image_id)
        self.assertIsInstance(out, tuple)

    @patch('udocker.docker.Msg')
    @patch.object(DockerIoAPI, '_get_file')
    def test_16_get_v1_image_json(self, mock_dgf, mock_msg):
        """Test16 DockerIoAPI().get_v1_image_json"""
        mock_msg.level = 0
        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_id = "LAYERID"
        doia = DockerIoAPI(self.local)
        status = doia.get_v1_image_json(endpoint, layer_id)
        self.assertTrue(status)

        mock_dgf.return_value = False
        doia = DockerIoAPI(self.local)
        status = doia.get_v1_image_json(endpoint, layer_id)
        self.assertFalse(status)

    @patch('udocker.docker.Msg')
    @patch.object(DockerIoAPI, '_get_file')
    def test_17_get_v1_image_layer(self, mock_dgf, mock_msg):
        """Test17 DockerIoAPI().get_v1_image_layer"""
        mock_msg.level = 0
        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_id = "LAYERID"
        doia = DockerIoAPI(self.local)
        status = doia.get_v1_image_layer(endpoint, layer_id)
        self.assertTrue(status)

        mock_dgf.return_value = False
        doia = DockerIoAPI(self.local)
        status = doia.get_v1_image_layer(endpoint, layer_id)
        self.assertFalse(status)

    @patch('udocker.docker.Msg')
    @patch.object(DockerIoAPI, '_get_file')
    def test_18_get_v1_layers_all(self, mock_dgf, mock_msg):
        """Test18 DockerIoAPI().get_v1_layers_all"""
        mock_msg.level = 0
        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_list = []
        doia = DockerIoAPI(self.local)
        out = doia.get_v1_layers_all(endpoint, layer_list)
        self.assertEqual(out, [])

        layer_list = ["a", "b"]
        doia = DockerIoAPI(self.local)
        out = doia.get_v1_layers_all(endpoint, layer_list)
        self.assertEqual(out, ['b.json', 'b.layer', 'a.json', 'a.layer'])

    @patch.object(DockerIoAPI, '_get_url')
    @patch('udocker.utils.curl.CurlHeader')
    @patch('udocker.docker.json.loads')
    def test_19__get_v2_auth(self, mock_jloads, mock_hdr, mock_dgu):
        """Test19 DockerIoAPI()._get_v2_auth"""
        fakedata = strio('token'.encode('utf-8'))
        www_authenticate = "Other Stuff"
        mock_dgu.return_value = (mock_hdr, fakedata)
        mock_jloads.return_value = {'token': 'YYY'}
        doia = DockerIoAPI(self.local)
        doia.v2_auth_header = "v2 Auth Header"
        doia.v2_auth_token = "v2 Auth Token"
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "")

        www_authenticate = "Bearer realm=REALM"
        mock_dgu.return_value = (mock_hdr, fakedata)
        mock_jloads.return_value = {'token': 'YYY'}
        doia = DockerIoAPI(self.local)
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "Authorization: Bearer YYY")

        www_authenticate = "BASIC realm=Sonatype Nexus Repository"
        mock_dgu.return_value = (mock_hdr, fakedata)
        mock_jloads.return_value = {'token': 'YYY'}
        doia = DockerIoAPI(self.local)
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "Authorization: Basic %s" % doia.v2_auth_token)

    def test_20_get_v2_login_token(self):
        """Test20 DockerIoAPI().get_v2_login_token"""
        doia = DockerIoAPI(self.local)
        out = doia.get_v2_login_token("username", "password")
        self.assertIsInstance(out, str)

        doia = DockerIoAPI(self.local)
        out = doia.get_v2_login_token("", "")
        self.assertEqual(out, "")

    def test_21_set_v2_login_token(self):
        """Test21 DockerIoAPI().set_v2_login_token"""
        doia = DockerIoAPI(self.local)
        doia.set_v2_login_token("BIG-FAT-TOKEN")
        self.assertEqual(doia.v2_auth_token, "BIG-FAT-TOKEN")

    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_22_is_v2(self, mock_dgu, mock_hdr):
        """Test22 DockerIoAPI().is_v2"""
        mock_dgu.return_value = (mock_hdr, [])
        doia = DockerIoAPI(self.local)
        doia.registry_url = "http://www.docker.io"
        out = doia.is_v2()
        self.assertFalse(out)

        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_dgu.return_value = (hdr, buff)
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.is_v2()
        self.assertTrue(out)

    @patch.object(DockerIoAPI, '_get_url')
    def test_23_has_search_v2(self, mock_dgu):
        """Test23 DockerIoAPI().has_search_v2"""
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 400 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_dgu.return_value = (hdr, buff)
        doia = DockerIoAPI(self.local)
        doia.registry_url = "http://www.docker.io"
        out = doia.has_search_v2()
        self.assertFalse(out)

        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_dgu.return_value = (hdr, buff)
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.has_search_v2()
        self.assertTrue(out)

    @patch('udocker.docker.json.loads')
    @patch.object(DockerIoAPI, '_get_url')
    def test_24_get_v2_image_tags(self, mock_dgu, mock_jload):
        """Test24 DockerIoAPI().get_v2_image_tags"""
        imgrepo = "img1"
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_dgu.return_value = (hdr, buff)
        mock_jload.return_value = list()
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2_image_tags(imgrepo)
        self.assertEqual(out, list())

        imgrepo = "img1"
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        buff = strio()
        mock_dgu.return_value = (hdr, buff)
        mock_jload.return_value = ["tag1", "tag2"]
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2_image_tags(imgrepo)
        self.assertEqual(out, ["tag1", "tag2"])

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_25_get_v2_image_manifest(self, mock_dgu, mock_hdr, mock_msg):
        """Test25 DockerIoAPI().get_v2_image_manifest"""
        mock_msg.level = 0
        imagerepo = "REPO"
        tag = "TAG"
        mock_dgu.return_value = (mock_hdr, [])
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2_image_manifest(imagerepo, tag)
        self.assertIsInstance(out, tuple)

    @patch('udocker.docker.Msg')
    @patch.object(DockerIoAPI, '_get_file')
    def test_26_get_v2_image_layer(self, mock_dgf, mock_msg):
        """Test26 DockerIoAPI().get_v2_image_layer"""
        mock_msg.level = 0
        imagerepo = "REPO"
        layer_id = "LAYERID"
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"

        mock_dgf.return_value = True
        doia = DockerIoAPI(self.local)
        out = doia.get_v2_image_layer(imagerepo, layer_id)
        self.assertTrue(out)

        mock_dgf.return_value = False
        doia = DockerIoAPI(self.local)
        out = doia.get_v2_image_layer(imagerepo, layer_id)
        self.assertFalse(out)

    @patch('udocker.docker.Msg')
    @patch.object(DockerIoAPI, 'get_v2_image_layer')
    def test_27_get_v2_layers_all(self, mock_v2il, mock_msg):
        """Test27 DockerIoAPI().get_v2_layers_all"""
        mock_msg.level = 0
        mock_v2il.return_value = False
        imagerepo = "REPO"
        fslayers = []
        doia = DockerIoAPI(self.local)
        out = doia.get_v2_layers_all(imagerepo, fslayers)
        self.assertEqual(out, [])

        mock_msg.level = 0
        mock_v2il.return_value = True
        imagerepo = "REPO"
        fslayers = [{"blobSum": "foolayername"}]
        doia = DockerIoAPI(self.local)
        out = doia.get_v2_layers_all(imagerepo, fslayers)
        self.assertEqual(out, ['foolayername'])

    @patch('udocker.docker.Msg')
    @patch('udocker.docker.GetURL.get_status_code')
    @patch.object(DockerIoAPI, 'get_v2_image_manifest')
    @patch.object(DockerIoAPI, 'get_v2_layers_all')
    @patch.object(DockerIoAPI, '_get_url')
    def test_28_get_v2(self, mock_dgu, mock_dgv2, mock_manif,
                       mock_getstatus, mock_msg):
        """Test28 DockerIoAPI().get_v2"""
        imgrepo = "img1"
        hdr = type('test', (object,), {})()
        hdr_data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0}
        hdr.data = hdr_data
        buff = strio()
        manifest = list()
        mock_msg.level = 0
        mock_dgu.return_value = (hdr, buff)
        mock_manif.return_value = (hdr_data, manifest)
        mock_dgv2.return_value = []
        mock_getstatus.return_value = 400
        tag = "TAG"
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2(imgrepo, tag)
        self.assertEqual(out, [])

        mock_dgu.return_value = (hdr, buff)
        mock_manif.return_value = (hdr_data, manifest)
        mock_dgv2.return_value = []
        mock_getstatus.return_value = 200
        self.local.setup_tag.return_value = False
        self.local.set_version.return_value = True
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2(imgrepo, tag)
        self.assertEqual(out, [])

        manifest = {
            "fsLayers": ({"blobSum": "foolayername"},),
            "history": ({"v1Compatibility": '["foojsonstring"]'},)
        }
        mock_dgu.return_value = (hdr, buff)
        mock_manif.return_value = (hdr_data, manifest)
        mock_dgv2.return_value = ["foolayername"]
        mock_getstatus.return_value = 200
        self.local.setup_tag.return_value = True
        self.local.set_version.return_value = True
        self.local.save_json.return_value = None
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2(imgrepo, tag)
        self.assertEqual(out, ["foolayername"])

    def test_29__get_v1_id_from_tags(self):
        """Test29 DockerIoAPI()._get_v1_id_from_tags"""
        tobj = {"tag1": "t1"}
        tag = "tag1"
        doia = DockerIoAPI(self.local)
        out = doia._get_v1_id_from_tags(tobj, tag)
        self.assertEqual(out, "t1")

        tobj = [{"name": "tag1", "layer": "l1"}]
        tag = "tag1"
        doia = DockerIoAPI(self.local)
        out = doia._get_v1_id_from_tags(tobj, tag)
        self.assertEqual(out, "l1")

    def test_30__get_v1_id_from_images(self):
        """Test30 DockerIoAPI()._get_v1_id_from_images"""
        imgarr = list()
        shortid = ""
        doia = DockerIoAPI(self.local)
        out = doia._get_v1_id_from_images(imgarr, shortid)
        self.assertEqual(out, "")

        imgarr = [{"id": "1234567890"}]
        shortid = "12345678"
        doia = DockerIoAPI(self.local)
        out = doia._get_v1_id_from_images(imgarr, shortid)
        self.assertEqual(out, "1234567890")

    @patch('udocker.docker.Msg')
    @patch('udocker.docker.GetURL.get_status_code')
    @patch.object(DockerIoAPI, 'get_v1_layers_all')
    @patch.object(DockerIoAPI, 'get_v1_image_ancestry')
    @patch.object(DockerIoAPI, '_get_v1_id_from_images')
    @patch.object(DockerIoAPI, '_get_v1_id_from_tags')
    @patch.object(DockerIoAPI, 'get_v1_image_tags')
    @patch.object(DockerIoAPI, 'get_v1_repo')
    def test_31_get_v1(self, mock_dgv1repo, mock_v1imgtag,
                       mock_v1idtag, mock_v1idimg, mock_v1ances,
                       mock_v1layer, mock_status, mock_msg):
        """Test31 DockerIoAPI().get_v1"""
        imgarr = [{"id": "1234567890"}]
        imagerepo = "REPO"
        tag = "TAG"
        hdr = type('test', (object,), {})()
        hdr_data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0,
                    "x-docker-endpoints": "https://registry-1.docker.io"}
        hdr.data = hdr_data
        mock_msg.level = 0
        mock_dgv1repo.return_value = (hdr_data, imgarr)
        mock_status.return_value = 401
        doia = DockerIoAPI(self.local)
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

        mock_v1imgtag.return_value = [{"name": "tag1"}]
        mock_v1idtag.return_value = ""
        mock_dgv1repo.return_value = (hdr_data, imgarr)
        mock_status.return_value = 200
        doia = DockerIoAPI(self.local)
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

        mock_v1imgtag.return_value = [{"name": "tag1"}]
        mock_v1idtag.return_value = "123456"
        mock_v1idimg.return_value = ""
        mock_dgv1repo.return_value = (hdr_data, imgarr)
        mock_status.return_value = 200
        doia = DockerIoAPI(self.local)
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

        mock_v1imgtag.return_value = [{"name": "tag1"}]
        mock_v1idtag.return_value = "123456"
        mock_v1idimg.return_value = "123456789"
        mock_dgv1repo.return_value = (hdr_data, imgarr)
        mock_status.return_value = 200
        self.local.setup_tag.return_value = False
        self.local.set_version.return_value = True
        doia = DockerIoAPI(self.local)
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

        mock_v1imgtag.return_value = [{"name": "tag1"}]
        mock_v1idtag.return_value = "123456"
        mock_v1idimg.return_value = "123456789"
        mock_dgv1repo.return_value = (hdr_data, imgarr)
        mock_status.return_value = 200
        mock_v1ances.return_value = ("x", "")
        self.local.setup_tag.return_value = True
        self.local.set_version.return_value = True
        self.local.save_json.return_value = None
        doia = DockerIoAPI(self.local)
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

        mock_v1imgtag.return_value = [{"name": "tag1"}]
        mock_v1idtag.return_value = "123456"
        mock_v1idimg.return_value = "123456789"
        mock_dgv1repo.return_value = (hdr_data, imgarr)
        mock_status.return_value = 200
        mock_v1ances.return_value = ("x", "123")
        mock_v1layer.return_value = ["file1"]
        self.local.setup_tag.return_value = True
        self.local.set_version.return_value = True
        self.local.save_json.return_value = None
        doia = DockerIoAPI(self.local)
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, ["file1"])

    def test_32__parse_imagerepo(self):
        """Test32 DockerIoAPI()._parse_imagerepo"""
        imagerepo = "https://hub.docker.com/_/mysql"
        doia = DockerIoAPI(self.local)
        out = doia._parse_imagerepo(imagerepo)
        self.assertEqual(out, (imagerepo, "https://hub.docker.com/_/mysql"))

    @patch.object(DockerIoAPI, 'get_v1')
    @patch.object(DockerIoAPI, 'get_v2')
    @patch.object(DockerIoAPI, 'is_v2')
    @patch.object(DockerIoAPI, '_parse_imagerepo')
    def test_33_get(self, mock_parse, mock_isv2, mock_getv2, mock_getv1):
        """Test33 DockerIoAPI().get"""
        imagerepo = "REPO"
        tag = "TAG"
        mock_parse.return_value = ("REPO", "https://registry-1.docker.io")
        self.local.cd_imagerepo.return_value = False
        self.local.setup_imagerepo.return_value = True
        self.local.del_imagerepo.return_value = False
        mock_isv2.return_value = False
        mock_getv1.return_value = ["a", "b"]
        doia = DockerIoAPI(self.local)
        out = doia.get(imagerepo, tag)
        self.assertEqual(out, ["a", "b"])

        mock_parse.return_value = ("REPO", "https://registry-1.docker.io")
        self.local.cd_imagerepo.return_value = True
        self.local.setup_imagerepo.return_value = True
        self.local.del_imagerepo.return_value = False
        mock_isv2.return_value = True
        mock_getv2.return_value = ["a", "b"]
        doia = DockerIoAPI(self.local)
        out = doia.get(imagerepo, tag)
        self.assertEqual(out, ["a", "b"])

    @patch.object(DockerIoAPI, 'get_v1_image_tags')
    @patch.object(DockerIoAPI, 'get_v2_image_tags')
    @patch.object(DockerIoAPI, 'is_v2')
    def test_34_get_tags(self, mock_isv2, mock_getv2, mock_getv1):
        """Test34 DockerIoAPI().get_tags"""
        imagerepo = "REPO"
        mock_isv2.return_value = False
        mock_getv1.return_value = ["a", "b"]
        doia = DockerIoAPI(self.local)
        out = doia.get_tags(imagerepo)
        self.assertEqual(out, ["a", "b"])

        mock_isv2.return_value = True
        mock_getv2.return_value = ["a", "b"]
        doia = DockerIoAPI(self.local)
        out = doia.get_tags(imagerepo)
        self.assertEqual(out, ["a", "b"])

    def test_35_search_init(self):
        """Test35 DockerIoAPI().search_init"""
        doia = DockerIoAPI(self.local)
        doia.search_init("PAUSE")
        self.assertEqual(doia.search_pause, "PAUSE")
        self.assertEqual(doia.search_page, 0)
        self.assertEqual(doia.search_ended, False)

    @patch.object(DockerIoAPI, '_get_url')
    @patch('udocker.docker.json.loads')
    def test_36_search_get_page_v1(self, mock_jload, mock_dgu):
        """Test36 DockerIoAPI().set_index"""
        hdr = type('test', (object,), {})()
        hdr_data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0,
                    "x-docker-endpoints": "https://registry-1.docker.io"}
        hdr.data = hdr_data
        buff = strio()
        mock_dgu.return_value = (hdr, buff)
        mock_jload.return_value = {"page": 1, "num_pages": 1}
        url = "https://registry-1.docker.io"
        doia = DockerIoAPI(self.local)
        out = doia.search_get_page_v1("SOMETHING", url)
        self.assertEqual(out, {"page": 1, "num_pages": 1})

    @patch.object(DockerIoAPI, '_get_url')
    @patch('udocker.docker.json.loads')
    def test_37_search_get_page_v2(self, mock_jload, mock_dgu):
        """Test37 DockerIoAPI().search_get_page_v2"""
        hdr = type('test', (object,), {})()
        hdr_data = {"content-length": 10,
                    "X-ND-HTTPSTATUS": "HTTP-Version 200 Reason-Phrase",
                    "X-ND-CURLSTATUS": 0,
                    "x-docker-endpoints": "https://registry-1.docker.io"}
        hdr.data = hdr_data
        buff = strio()
        mock_dgu.return_value = (hdr, buff)
        mock_jload.return_value = {"count": 1, "num_pages": 1}
        url = "https://registry-1.docker.io"
        doia = DockerIoAPI(self.local)
        out = doia.search_get_page_v2("SOMETHING", url)
        self.assertEqual(out, {"count": 1, "num_pages": 1})

    @patch.object(DockerIoAPI, 'search_get_page_v1')
    @patch.object(DockerIoAPI, 'search_get_page_v2')
    @patch.object(DockerIoAPI, 'has_search_v1')
    @patch.object(DockerIoAPI, 'has_search_v2')
    def test_38_search_get_page(self, mock_searchv2, mock_searchv1,
                                mock_getv2, mock_getv1):
        """Test38 DockerIoAPI().search_get_page"""
        mock_searchv2.return_value = True
        mock_searchv1.return_value = False
        mock_getv2.return_value = {"count": 1, "num_pages": 1}
        mock_getv1.return_value = {"page": 1, "num_pages": 1}
        doia = DockerIoAPI(self.local)
        out = doia.search_get_page("SOMETHING")
        self.assertEqual(out, {"count": 1, "num_pages": 1})

        mock_searchv2.return_value = False
        mock_searchv1.return_value = True
        mock_getv2.return_value = {"count": 1, "num_pages": 1}
        mock_getv1.return_value = {"page": 1, "num_pages": 1}
        doia = DockerIoAPI(self.local)
        out = doia.search_get_page("SOMETHING")
        self.assertEqual(out, {"page": 1, "num_pages": 1})

if __name__ == '__main__':
    main()
