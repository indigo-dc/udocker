#!/usr/bin/env python
"""
udocker unit tests: DockerIoAPI
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

sys.path.append('.')

from udocker.docker import DockerIoAPI
from udocker.config import Config
from udocker.container.localrepo import LocalRepository


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
        """Test DockerIoAPI() constructor"""
        mock_geturl.return_value = None
        doia = DockerIoAPI(self.local, self.conf)
        self.assertEqual(doia.index_url, self.conf['dockerio_index_url'])
        self.assertEqual(doia.registry_url, self.conf['dockerio_registry_url'])
        self.assertEqual(doia.v1_auth_header, "")
        self.assertEqual(doia.v2_auth_header, "")
        self.assertEqual(doia.v2_auth_token, "")
        self.assertEqual(doia.localrepo, self.local)
        self.assertEqual(doia.docker_registry_domain, "docker.io")
        self.assertEqual(doia.search_link, "")
        self.assertTrue(doia.search_pause)
        self.assertEqual(doia.search_page, 0)
        self.assertEqual(doia.search_lines, 25)
        self.assertEqual(doia.search_link, "")
        self.assertFalse(doia.search_ended)
        self.assertTrue(mock_geturl.called)

    @patch('udocker.docker.GetURL')
    def test_02_set_proxy(self, mock_geturl):
        """Test DockerIoAPI().set_proxy()."""
        url = "socks5://user:pass@host:port"
        doia = DockerIoAPI(self.local, self.conf)
        doia.set_proxy(url)
        self.assertTrue(mock_geturl.return_value.set_proxy.called_with(url))

    def test_03_set_registry(self):
        """Test DockerIoAPI().set_registry()."""
        doia = DockerIoAPI(self.local, self.conf)
        doia.set_registry("https://registry-1.docker.io")
        self.assertEqual(doia.registry_url, "https://registry-1.docker.io")

    def test_04_set_index(self):
        """Test DockerIoAPI().set_index()."""
        doia = DockerIoAPI(self.local, self.conf)
        doia.set_index("https://index.docker.io/v1")
        self.assertEqual(doia.index_url, "https://index.docker.io/v1")

    @patch('udocker.docker.Msg')
    def test_05_is_repo_name(self, mock_msg):
        """Test DockerIoAPI().is_repo_name()."""
        mock_msg.level = 0
        doia = DockerIoAPI(self.local, self.conf)
        self.assertFalse(doia.is_repo_name(""))
        self.assertFalse(doia.is_repo_name("socks5://user:pass@host:port"))
        self.assertFalse(doia.is_repo_name("/:"))
        self.assertTrue(doia.is_repo_name("1233/fasdfasdf:sdfasfd"))
        self.assertTrue(doia.is_repo_name("os-cli-centos7"))
        self.assertTrue(doia.is_repo_name("os-cli-centos7:latest"))
        self.assertTrue(doia.is_repo_name("lipcomputing/os-cli-centos7"))
        self.assertTrue(doia.is_repo_name("lipcomputing/os-cli-centos7:latest"))

    def test_06__is_docker_registry(self):
        """Test DockerIoAPI().is_docker_registry()."""
        doia = DockerIoAPI(self.local, self.conf)
        doia.set_registry("https://registry-1.docker.io")
        self.assertTrue(doia._is_docker_registry())

        doia = DockerIoAPI(self.local, self.conf)
        doia.set_registry("")
        self.assertFalse(doia._is_docker_registry())

        doia = DockerIoAPI(self.local, self.conf)
        doia.set_registry("https://registry-1.docker.pt")
        self.assertFalse(doia._is_docker_registry())

        doia = DockerIoAPI(self.local, self.conf)
        doia.set_registry("docker.io")
        self.assertTrue(doia._is_docker_registry())

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_07_get_v1_repo(self, mock_dgu, mock_hdr, mock_msg):
        """Test DockerIoAPI().get_v1_repo"""
        mock_msg.level = 0
        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        doia = DockerIoAPI(self.local, self.conf)
        doia.index_url = "docker.io"
        out = doia.get_v1_repo(imagerepo)
        self.assertIsInstance(out, tuple)

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_08_get_v1_image_tags(self, mock_dgu, mock_hdr, mock_msg):
        """Test DockerIoAPI().get_v1_image_tags"""
        mock_msg.level = 0
        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        imagerepo = "REPO"
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v1_image_tags(endpoint, imagerepo)
        self.assertIsInstance(out, tuple)

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_09_get_v1_image_tag(self, mock_dgu, mock_hdr, mock_msg):
        """Test DockerIoAPI().get_v1_image_tag"""
        mock_msg.level = 0
        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v1_image_tag(endpoint, imagerepo, tag)
        self.assertIsInstance(out, tuple)

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_10_get_v1_image_ancestry(self, mock_dgu, mock_hdr, mock_msg):
        """Test DockerIoAPI().get_v1_image_ancestry"""
        mock_msg.level = 0
        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        image_id = "IMAGEID"
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v1_image_ancestry(endpoint, image_id)
        self.assertIsInstance(out, tuple)

    @patch('udocker.docker.Msg')
    @patch.object(DockerIoAPI, '_get_file')
    def test_11_get_v1_image_json(self, mock_dgf, mock_msg):
        """Test DockerIoAPI().get_v1_image_json"""
        mock_msg.level = 0
        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_id = "LAYERID"
        doia = DockerIoAPI(self.local, self.conf)
        status = doia.get_v1_image_json(endpoint, layer_id)
        self.assertTrue(status)

        mock_dgf.return_value = False
        doia = DockerIoAPI(self.local, self.conf)
        status = doia.get_v1_image_json(endpoint, layer_id)
        self.assertFalse(status)

    @patch('udocker.docker.Msg')
    @patch.object(DockerIoAPI, '_get_file')
    def test_12_get_v1_image_layer(self, mock_dgf, mock_msg):
        """Test DockerIoAPI().get_v1_image_layer"""
        mock_msg.level = 0
        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_id = "LAYERID"
        doia = DockerIoAPI(self.local, self.conf)
        status = doia.get_v1_image_layer(endpoint, layer_id)
        self.assertTrue(status)

        mock_dgf.return_value = False
        doia = DockerIoAPI(self.local, self.conf)
        status = doia.get_v1_image_layer(endpoint, layer_id)
        self.assertFalse(status)

    @patch('udocker.docker.Msg')
    @patch.object(DockerIoAPI, '_get_file')
    def test_13_get_v1_layers_all(self, mock_dgf, mock_msg):
        """Test DockerIoAPI().get_v1_layers_all"""
        mock_msg.level = 0
        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_list = []
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v1_layers_all(endpoint, layer_list)
        self.assertEqual(out, [])

        layer_list = ["a", "b"]
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v1_layers_all(endpoint, layer_list)
        self.assertEqual(out, ['b.json', 'b.layer', 'a.json', 'a.layer'])

    def test_14_get_v2_login_token(self):
        """Test DockerIoAPI().get_v2_login_token"""
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v2_login_token("username", "password")
        self.assertIsInstance(out, str)

        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v2_login_token("", "")
        self.assertEqual(out, "")

    def test_15_set_v2_login_token(self):
        """Test DockerIoAPI().set_v2_login_token"""
        doia = DockerIoAPI(self.local, self.conf)
        doia.set_v2_login_token("BIG-FAT-TOKEN")
        self.assertEqual(doia.v2_auth_token, "BIG-FAT-TOKEN")

    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_16_is_v2(self, mock_dgu, mock_hdr):
        """Test DockerIoAPI().is_v2"""
        mock_dgu.return_value = (mock_hdr, [])
        doia = DockerIoAPI(self.local, self.conf)
        doia.registry_url = "http://www.docker.io"
        out = doia.is_v2()
        self.assertFalse(out)

        # needs auth to be working before
        doia = DockerIoAPI(self.local, self.conf)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.is_v2()
        # self.assertTrue(out)

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_url')
    def test_17_get_v2_image_manifest(self, mock_dgu, mock_hdr, mock_msg):
        """Test DockerIoAPI().get_v2_image_manifest"""
        mock_msg.level = 0
        imagerepo = "REPO"
        tag = "TAG"
        mock_dgu.return_value = (mock_hdr, [])
        doia = DockerIoAPI(self.local, self.conf)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2_image_manifest(imagerepo, tag)
        self.assertIsInstance(out, tuple)

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, '_get_file')
    def test_18_get_v2_image_layer(self, mock_dgf, mock_hdr, mock_msg):
        """Test DockerIoAPI().get_v2_image_layer"""
        mock_msg.level = 0
        imagerepo = "REPO"
        layer_id = "LAYERID"
        doia = DockerIoAPI(self.local, self.conf)
        doia.registry_url = "https://registry-1.docker.io"

        mock_dgf.return_value = True
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v2_image_layer(imagerepo, layer_id)
        self.assertTrue(out)

        mock_dgf.return_value = False
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v2_image_layer(imagerepo, layer_id)
        self.assertFalse(out)

    @patch('udocker.docker.Msg')
    @patch.object(DockerIoAPI, '_get_file')
    def test_19_get_v2_layers_all(self, mock_dgf, mock_msg):
        """Test DockerIoAPI().get_v2_layers_all"""
        mock_msg.level = 0
        mock_dgf.return_value = True
        endpoint = "docker.io"
        fslayers = []
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v2_layers_all(endpoint, fslayers)
        self.assertEqual(out, [])

        # fslayers = ["a", "b"]
        # doia = DockerIoAPI(self.local, self.conf)
        # out = doia.get_v2_layers_all(endpoint, fslayers)
        # self.assertEqual(out, ['b.json', 'b.layer', 'a.json', 'a.layer'])

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, 'get_v2_layers_all')
    @patch.object(DockerIoAPI, '_get_url')
    def test_20_get_v2(self, mock_dgu, mock_dgv2, mock_hdr, mock_msg):
        """Test DockerIoAPI().get_v2"""
        mock_msg.level = 0
        mock_dgv2.return_value = []
        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(self.local, self.conf)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2(imagerepo, tag)
        self.assertEqual(out, [])

        mock_dgv2.return_value = ["a", "b"]
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v2(imagerepo, tag)
        self.assertEqual(out, [])

    @patch('udocker.docker.Msg')
    @patch('udocker.utils.curl.CurlHeader')
    @patch.object(DockerIoAPI, 'get_v2_layers_all')
    @patch.object(DockerIoAPI, '_get_url')
    def test_21_get_v1(self, mock_dgu, mock_dgv1, mock_hdr, mock_msg):
        """Test DockerIoAPI().get_v1"""
        mock_msg.level = 0
        mock_dgv1.return_value = []
        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(self.local, self.conf)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

        mock_dgv1.return_value = ["a", "b"]
        doia = DockerIoAPI(self.local, self.conf)
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

    # @patch('udocker.docker.Msg')
    # @patch.object(DockerIoAPI, '_get_url')
    # @patch('udocker.utils.curl.CurlHeader')
    # @patch.object(DockerIoAPI, '_parse_imagerepo')
    # @patch('udocker.container.localrepo.LocalRepository.cd_imagerepo', autospec=True)
    # def test_22_get(self, mock_cdir, mock_parse,
    #                 mock_hdr, mock_dgu, mock_msg):
    #     """Test DockerIoAPI().get"""
    #     mock_msg.level = 0
    #     mock_cdir.return_value = False
    #     mock_parse.return_value = ()
    #     mock_dgu.return_value = (mock_hdr, [])
    #     imagerepo = "REPO"
    #     tag = "TAG"
    #     doia = DockerIoAPI(self.local, self.conf)
    #     doia.registry_url = "https://registry-1.docker.io"
    #     out = doia.get(imagerepo, tag)
    #     self.assertEqual(out, [])

    def test_23_search_init(self):
        """Test DockerIoAPI().search_init"""
        doia = DockerIoAPI(self.local, self.conf)
        doia.search_init("PAUSE")
        self.assertEqual(doia.search_pause, "PAUSE")
        self.assertEqual(doia.search_page, 0)
        self.assertEqual(doia.search_link, "")
        self.assertEqual(doia.search_ended, False)

    @patch.object(DockerIoAPI, '_get_url')
    @patch('udocker.utils.curl.CurlHeader')
    def test_24_search_get_page_v1(self, mock_hdr, mock_dgu):
        """Test DockerIoAPI().set_index"""
        mock_dgu.return_value = (mock_hdr, [])
        doia = DockerIoAPI(self.local, self.conf)
        doia.set_index("index.docker.io")
        out = doia.search_get_page_v1("SOMETHING")
        self.assertEqual(out, [])

    # @patch.object(DockerIoAPI, '_get_url')
    # @patch('udocker.utils.curl.CurlHeader')
    # def test_25_catalog_get_page_v2(self, mock_hdr, mock_dgu):
    #     """Test DockerIoAPI().catalog_get_page_v2"""
    #     mock_dgu.return_value = (mock_hdr, [])
    #     doia = DockerIoAPI(self.local, self.conf)
    #     doia.set_index("index.docker.io")
    #     out = doia.catalog_get_page_v2("lines")
    #     self.assertEqual(out, [])

    @patch.object(DockerIoAPI, '_get_url')
    @patch('udocker.utils.curl.CurlHeader')
    def test_26_search_get_page(self, mock_hdr, mock_dgu):
        """Test DockerIoAPI().search_get_page"""
        mock_dgu.return_value = (mock_hdr, [])
        doia = DockerIoAPI(self.local, self.conf)
        doia.set_index("index.docker.io")
        out = doia.search_get_page("SOMETHING")
        self.assertEqual(out, [])

    # @patch.object(DockerIoAPI, '_get_url')
    # @patch('udocker.docker.GetURL')
    # @patch('udocker.utils.curl.CurlHeader')
    # def test_27__get_url(self, mock_hdr,
    #                      mock_geturl, mock_dgu):
    #     """Test DockerIoAPI()._get_url"""
    #     pass
    #     # mock_dgu.return_value = (mock_hdr, [])

    # @patch.object(DockerIoAPI, '_get_url')
    # @patch('udocker.docker.GetURL')
    # @patch('udocker.utils.curl.CurlHeader')
    # def test_28__get_file(self, mock_hdr,
    #                       mock_geturl, mock_dgu):
    #     """Test DockerIoAPI()._get_file"""
    #     pass
    #     # mock_dgu.return_value = (mock_hdr, [])

    # def test_29__get_v1_auth(self):
    #     """Test DockerIoAPI()._get_v1_auth"""
    #     doia = DockerIoAPI(self.local, self.conf)
    #     doia.v1_auth_header = "Not Empty"
    #     www_authenticate = ['Other Stuff']
    #     out = doia._get_v1_auth(www_authenticate)
    #     self.assertEqual(out, "")
    #
    #     www_authenticate = ['Token']
    #     doia = DockerIoAPI(self.local, self.conf)
    #     out = doia._get_v1_auth(www_authenticate)
    #     self.assertEqual(out, "Not Empty")

    @patch.object(DockerIoAPI, '_get_url')
    @patch('udocker.utils.curl.CurlHeader')
    @patch('udocker.docker.json.loads')
    def test_30__get_v2_auth(self, mock_jloads, mock_hdr, mock_dgu):
        """Test DockerIoAPI()._get_v2_auth"""
        fakedata = StringIO('token')
        mock_dgu.return_value = (mock_hdr, fakedata)
        mock_jloads.return_value = {'token': 'YYY'}
        doia = DockerIoAPI(self.local, self.conf)
        doia.v2_auth_header = "v2 Auth Header"
        doia.v2_auth_token = "v2 Auth Token"
        www_authenticate = 'Other Stuff'
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "")

        www_authenticate = "Bearer realm=REALM"
        doia = DockerIoAPI(self.local, self.conf)
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "Authorization: Bearer YYY")

        www_authenticate = "BASIC realm=Sonatype Nexus Repository"
        doia = DockerIoAPI(self.local, self.conf)
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "Authorization: Basic %s" % doia.v2_auth_token)


if __name__ == '__main__':
    main()
