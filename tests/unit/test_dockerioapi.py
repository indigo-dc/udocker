#!/usr/bin/env python
"""
udocker unit tests: DockerIoAPI
"""

from unittest import TestCase, main
from udocker.docker import DockerIoAPI
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


class DockerIoAPITestCase(TestCase):
    """Test DockerIoAPITest().
    Class to encapsulate the access to the Docker Hub service.
    Allows to search and download images from Docker Hub.
    """

    def setUp(self):
        self.conf = Config().getconf()
        self.local = LocalRepository(self.conf)

    def tearDown(self):
        pass

    @patch('udocker.docker.GetURL')
    def test_01_init(self, mock_geturl):
        """Test01 DockerIoAPI() constructor"""
        mock_geturl.return_value = None
        doia = DockerIoAPI(self.local)
        # self.assertEqual(doia.index_url, self.conf['dockerio_index_url'])
        # self.assertEqual(doia.registry_url, self.conf['dockerio_registry_url'])
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

    @patch('udocker.docker.Msg')
    def test_05_is_repo_name(self, mock_msg):
        """Test05 DockerIoAPI().is_repo_name()."""
        mock_msg.level = 0
        doia = DockerIoAPI(self.local)
        self.assertFalse(doia.is_repo_name(""))
        self.assertFalse(doia.is_repo_name("socks5://user:pass@host:port"))
        self.assertFalse(doia.is_repo_name("/:"))
        self.assertTrue(doia.is_repo_name("1233/fasdfasdf:sdfasfd"))
        self.assertTrue(doia.is_repo_name("os-cli-centos7"))
        self.assertTrue(doia.is_repo_name("os-cli-centos7:latest"))
        self.assertTrue(doia.is_repo_name("lipcomputing/os-cli-centos7"))
        self.assertTrue(doia.is_repo_name("lipcomputing/os-cli-centos7:latest"))

    # @patch('udocker.docker.Msg')
    # def test_06__get_url(self, mock_msg):
    #     """Test06 DockerIoAPI()._get_url()."""
    #     mock_msg.level = 0
    #     doia = DockerIoAPI(self.local)

    # @patch('udocker.docker.Msg')
    # def test_07__get_file(self, mock_msg):
    #     """Test07 DockerIoAPI()._get_file()."""
    #     mock_msg.level = 0
    #     doia = DockerIoAPI(self.local)

    # @patch('udocker.docker.Msg')
    # def test_08__split_fields(self, mock_msg):
    #     """Test08 DockerIoAPI()._split_fields()."""
    #     mock_msg.level = 0
    #     doia = DockerIoAPI(self.local)

    # @patch('udocker.docker.Msg')
    # def test_09_is_v1(self, mock_msg):
    #     """Test09 DockerIoAPI().is_v1()."""
    #     mock_msg.level = 0
    #     doia = DockerIoAPI(self.local)

    # @patch('udocker.docker.Msg')
    # def test_10_has_search_v1(self, mock_msg):
    #     """Test10 DockerIoAPI().has_search_v1()."""
    #     mock_msg.level = 0
    #     doia = DockerIoAPI(self.local)

    # @patch('udocker.docker.Msg')
    # @patch('udocker.utils.curl.CurlHeader')
    # @patch.object(DockerIoAPI, '_get_url')
    # def test_11_get_v1_repo(self, mock_dgu, mock_hdr, mock_msg):
    #     """Test11 DockerIoAPI().get_v1_repo"""
    #     mock_msg.level = 0
    #     mock_dgu.return_value = (mock_hdr, [])
    #     imagerepo = "REPO"
    #     doia = DockerIoAPI(self.local)
    #     doia.index_url = "docker.io"
    #     out = doia.get_v1_repo(imagerepo)
    #     self.assertIsInstance(out, tuple)

    def test_12__get_v1_auth(self):
        """Test12 DockerIoAPI()._get_v1_auth"""
        doia = DockerIoAPI(self.local)
        doia.v1_auth_header = "Not Empty"
        www_authenticate = ['Other Stuff']
        out = doia._get_v1_auth(www_authenticate)
        self.assertEqual(out, "")

        www_authenticate = ['Token']
        doia = DockerIoAPI(self.local)
        out = doia._get_v1_auth(www_authenticate)
        # self.assertEqual(out, "Not Empty")

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

    # @patch.object(DockerIoAPI, '_get_url')
    # @patch('udocker.utils.curl.CurlHeader')
    # @patch('udocker.docker.json.loads')
    # def test_19__get_v2_auth(self, mock_jloads, mock_hdr, mock_dgu):
    #     """Test19 DockerIoAPI()._get_v2_auth"""
    #     fakedata = StringIO('token')
    #     mock_dgu.return_value = (mock_hdr, fakedata)
    #     mock_jloads.return_value = {'token': 'YYY'}
    #     doia = DockerIoAPI(self.local)
    #     doia.v2_auth_header = "v2 Auth Header"
    #     doia.v2_auth_token = "v2 Auth Token"
    #     www_authenticate = "Other Stuff".encode("utf8")
    #     out = doia._get_v2_auth(www_authenticate, False)
    #     self.assertEqual(out, "")

    #     www_authenticate = "Bearer realm=REALM".encode("utf8")
    #     doia = DockerIoAPI(self.local)
    #     out = doia._get_v2_auth(www_authenticate, False)
    #     self.assertEqual(out, "Authorization: Bearer YYY")

    #     www_authenticate = "BASIC realm=Sonatype Nexus Repository".encode("utf8")
    #     doia = DockerIoAPI(self.local)
    #     out = doia._get_v2_auth(www_authenticate, False)
    #     self.assertEqual(out, "Authorization: Basic %s" % doia.v2_auth_token)

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

        # needs auth to be working before
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.is_v2()
        # self.assertTrue(out)

    # def test_23_has_search_v2(self):
    #     """Test23 DockerIoAPI().has_search_v2"""
    #     doia = DockerIoAPI(self.local)

    # def test_24_get_v2_image_tags(self):
    #     """Test24 DockerIoAPI().get_v2_image_tags"""
    #     doia = DockerIoAPI(self.local)

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
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_file')
    def test_26_get_v2_image_layer(self, mock_dgf, mock_hdr, mock_msg):
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
        fslayers = ["a", "b"]
        doia = DockerIoAPI(self.local)
        # out = doia.get_v2_layers_all(imagerepo, fslayers)
        # self.assertEqual(out, ['b.json', 'b.layer', 'a.json', 'a.layer'])

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, 'get_v2_layers_all')
    @patch.object(DockerIoAPI, '_get_url')
    def test_28_get_v2(self, mock_dgu, mock_dgv2, mock_hdr, mock_msg):
        """Test28 DockerIoAPI().get_v2"""
        mock_msg.level = 0
        mock_dgv2.return_value = []
        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2(imagerepo, tag)
        self.assertEqual(out, [])

        mock_dgv2.return_value = ["a", "b"]
        doia = DockerIoAPI(self.local)
        out = doia.get_v2(imagerepo, tag)
        self.assertEqual(out, [])

    # def test_29__get_v1_id_from_tags(self):
    #     """Test29 DockerIoAPI()._get_v1_id_from_tags"""
    #     doia = DockerIoAPI(self.local)

    # def test_30__get_v1_id_from_images(self):
    #     """Test30 DockerIoAPI()._get_v1_id_from_images"""
    #     doia = DockerIoAPI(self.local)

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, 'get_v2_layers_all')
    @patch.object(DockerIoAPI, '_get_url')
    def test_31_get_v1(self, mock_dgu, mock_dgv1, mock_hdr, mock_msg):
        """Test31 DockerIoAPI().get_v1"""
        mock_msg.level = 0
        mock_dgv1.return_value = []
        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(self.local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

        mock_dgv1.return_value = ["a", "b"]
        doia = DockerIoAPI(self.local)
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

    # def test_32__parse_imagerepo(self):
    #     """Test32 DockerIoAPI()._parse_imagerepos"""
    #     doia = DockerIoAPI(self.local)

    @patch.object(DockerIoAPI, 'get_v1')
    @patch.object(DockerIoAPI, 'get_v2')
    @patch.object(DockerIoAPI, 'is_v2')
    @patch.object(DockerIoAPI, '_parse_imagerepo')
    @patch('udocker.utils.curl.CurlHeader')
    @patch('udocker.container.localrepo.LocalRepository.del_imagerepo', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.setup_imagerepo', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.cd_imagerepo', autospec=True)
    @patch('udocker.docker.Msg')
    def test_33_get(self, mock_msg, mock_cdir, mock_setup, mock_del,
                    mock_hdr, mock_parse, mock_isv2, mock_getv2, mock_getv1):
        """Test33 DockerIoAPI().get"""
        mock_msg.level = 0
        mock_parse.return_value = ("REPO", "https://registry-1.docker.io")
        mock_cdir.return_value = False
        mock_setup.return_value = True
        mock_isv2.return_value = False
        mock_getv1.return_value = ["a", "b"]
        mock_del.return_value = False
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(self.local)
        out = doia.get(imagerepo, tag)
        self.assertEqual(out, ["a", "b"])

        mock_isv2.return_value = True
        mock_getv2.return_value = ["a", "b"]
        mock_del.return_value = False
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(self.local)
        out = doia.get(imagerepo, tag)
        self.assertEqual(out, ["a", "b"])

    # def test_34_get_tags(self):
    #     """Test34 DockerIoAPI().get_tags"""
    #     doia = DockerIoAPI(self.local)

    def test_35_search_init(self):
        """Test35 DockerIoAPI().search_init"""
        doia = DockerIoAPI(self.local)
        doia.search_init("PAUSE")
        self.assertEqual(doia.search_pause, "PAUSE")
        self.assertEqual(doia.search_page, 0)
        self.assertEqual(doia.search_ended, False)

    @patch.object(DockerIoAPI, '_get_url')
    @patch('udocker.utils.curl.CurlHeader')
    def test_36_search_get_page_v1(self, mock_hdr, mock_dgu):
        """Test36 DockerIoAPI().set_index"""
        mock_dgu.return_value = (mock_hdr, [])
        doia = DockerIoAPI(self.local)
        doia.set_index("index.docker.io")
        url = "https://registry-1.docker.io"
        out = doia.search_get_page_v1("SOMETHING", url)
        self.assertEqual(out, [])

    # @patch.object(DockerIoAPI, '_get_url')
    # @patch('udocker.utils.curl.CurlHeader')
    # def test_37_search_get_page_v2(self, mock_hdr, mock_dgu):
    #     """Test37 DockerIoAPI().search_get_page_v2"""
    #     mock_dgu.return_value = (mock_hdr, [])
    #     doia = DockerIoAPI(self.local)
    #     doia.set_index("index.docker.io")
    #     out = doia.search_get_page_v2("lines")
    #     self.assertEqual(out, [])

    @patch.object(DockerIoAPI, '_get_url')
    @patch('udocker.utils.curl.CurlHeader')
    def test_38_search_get_page(self, mock_hdr, mock_dgu):
        """Test38 DockerIoAPI().search_get_page"""
        mock_dgu.return_value = (mock_hdr, [])
        doia = DockerIoAPI(self.local)
        doia.set_index("index.docker.io")
        out = doia.search_get_page("SOMETHING")
        self.assertEqual(out, [])


if __name__ == '__main__':
    main()
