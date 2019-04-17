#!/usr/bin/env python
"""
udocker unit tests.
Unit tests for udocker, a wrapper to execute basic docker containers
without using docker.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
import unittest
import mock
from StringIO import StringIO

sys.path.append('.')

from udocker.docker import DockerIoAPI
from udocker.config import Config


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class DockerIoAPITestCase(unittest.TestCase):
    """Test DockerIoAPITest().

    Class to encapsulate the access to the Docker Hub service.
    Allows to search and download images from Docker Hub.
    """

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        Config = mock.MagicMock()
        # udocker.Config.http_proxy

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local, mock_geturl):
        """Test DockerIoAPI() constructor"""
        self._init()
        #
        uia = DockerIoAPI(mock_local)
        self.assertEqual(uia.index_url, Config.dockerio_index_url)
        self.assertEqual(uia.registry_url,
                         Config.dockerio_registry_url)
        self.assertEqual(uia.v1_auth_header, "")
        self.assertEqual(uia.v2_auth_header, "")
        self.assertEqual(uia.v2_auth_token, "")
        self.assertEqual(uia.localrepo, mock_local)
        self.assertEqual(uia.docker_registry_domain, "docker.io")
        self.assertEqual(uia.search_link, "")
        self.assertTrue(uia.search_pause)
        self.assertEqual(uia.search_page, 0)
        self.assertEqual(uia.search_lines, 25)
        self.assertEqual(uia.search_link, "")
        self.assertFalse(uia.search_ended)
        #self.assertTrue(mock_geturl.called)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_02_set_proxy(self, mock_local, mock_geturl):
        """Test DockerIoAPI().set_proxy()."""
        self._init()
        #
        uia = DockerIoAPI(mock_local)
        url = "socks5://user:pass@host:port"
        uia.set_proxy(url)
        self.assertTrue(mock_geturl.return_value.set_proxy.called_with(url))

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_03_set_registry(self, mock_local, mock_geturl):
        """Test DockerIoAPI().set_registry()."""
        self._init()
        #
        uia = DockerIoAPI(mock_local)
        uia.set_registry("https://registry-1.docker.io")
        self.assertEqual(uia.registry_url, "https://registry-1.docker.io")

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_04_set_index(self, mock_local, mock_geturl):
        """Test DockerIoAPI().set_index()."""
        self._init()
        #
        uia = DockerIoAPI(mock_local)
        uia.set_index("https://index.docker.io/v1")
        self.assertEqual(uia.index_url, "https://index.docker.io/v1")

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_05_is_repo_name(self, mock_local, mock_msg, mock_geturl):
        """Test DockerIoAPI().is_repo_name()."""
        self._init()
        mock_msg.level = 0
        #
        uia = DockerIoAPI(mock_local)
        self.assertFalse(uia.is_repo_name(""))
        self.assertFalse(uia.is_repo_name("socks5://user:pass@host:port"))
        self.assertFalse(uia.is_repo_name("/:"))
        self.assertTrue(uia.is_repo_name("1233/fasdfasdf:sdfasfd"))
        self.assertTrue(uia.is_repo_name("os-cli-centos7"))
        self.assertTrue(uia.is_repo_name("os-cli-centos7:latest"))
        self.assertTrue(uia.is_repo_name("lipcomputing/os-cli-centos7"))
        self.assertTrue(uia.is_repo_name("lipcomputing/os-cli-centos7:latest"))

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_06__is_docker_registry(self, mock_local, mock_geturl):
        """Test DockerIoAPI().is_docker_registry()."""
        self._init()
        #
        uia = DockerIoAPI(mock_local)
        uia.set_registry("https://registry-1.docker.io")
        self.assertTrue(uia._is_docker_registry())
        #
        uia.set_registry("")
        self.assertFalse(uia._is_docker_registry())
        #
        uia.set_registry("https://registry-1.docker.pt")
        self.assertFalse(uia._is_docker_registry())
        #
        uia.set_registry("docker.io")
        self.assertTrue(uia._is_docker_registry())

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_07_get_v1_repo(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test DockerIoAPI().get_v1_repo"""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        doia = DockerIoAPI(mock_local)
        doia.index_url = "docker.io"
        out = doia.get_v1_repo(imagerepo)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_08_get_v1_image_tags(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test DockerIoAPI().get_v1_image_tags"""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        imagerepo = "REPO"
        doia = DockerIoAPI(mock_local)
        out = doia.get_v1_image_tags(endpoint, imagerepo)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_09_get_v1_image_tag(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test DockerIoAPI().get_v1_image_tag"""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(mock_local)
        out = doia.get_v1_image_tag(endpoint, imagerepo, tag)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_10_get_v1_image_ancestry(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test DockerIoAPI().get_v1_image_ancestry"""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        image_id = "IMAGEID"
        doia = DockerIoAPI(mock_local)
        out = doia.get_v1_image_ancestry(endpoint, image_id)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.docker.DockerIoAPI._get_file')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_11_get_v1_image_json(self, mock_local, mock_dgf, mock_geturl):
        """Test DockerIoAPI().get_v1_image_json"""
        self._init()

        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_id = "LAYERID"
        doia = DockerIoAPI(mock_local)
        status = doia.get_v1_image_json(endpoint, layer_id)
        self.assertTrue(status)

        mock_dgf.return_value = False
        status = doia.get_v1_image_json(endpoint, layer_id)
        self.assertFalse(status)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.docker.DockerIoAPI._get_file')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_12_get_v1_image_layer(self, mock_local, mock_dgf, mock_geturl):
        """Test DockerIoAPI().get_v1_image_layer"""
        self._init()

        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_id = "LAYERID"
        doia = DockerIoAPI(mock_local)
        status = doia.get_v1_image_layer(endpoint, layer_id)
        self.assertTrue(status)

        mock_dgf.return_value = False
        status = doia.get_v1_image_layer(endpoint, layer_id)
        self.assertFalse(status)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.docker.DockerIoAPI._get_file')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_13_get_v1_layers_all(self, mock_local, mock_dgf, mock_msg, mock_geturl):
        """Test DockerIoAPI().get_v1_layers_all"""
        self._init()

        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_list = []
        doia = DockerIoAPI(mock_local)
        out = doia.get_v1_layers_all(endpoint, layer_list)
        self.assertEqual(out, [])

        layer_list = ["a", "b"]
        doia = DockerIoAPI(mock_local)
        out = doia.get_v1_layers_all(endpoint, layer_list)
        self.assertEqual(out, ['b.json', 'b.layer', 'a.json', 'a.layer'])

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_14_get_v2_login_token(self, mock_local, mock_geturl):
        """Test DockerIoAPI().get_v2_login_token"""
        self._init()

        doia = DockerIoAPI(mock_local)
        out = doia.get_v2_login_token("username", "password")
        self.assertIsInstance(out, str)

        out = doia.get_v2_login_token("", "")
        self.assertEqual(out, "")

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_15_set_v2_login_token(self, mock_local, mock_geturl):
        """Test DockerIoAPI().set_v2_login_token"""
        self._init()

        doia = DockerIoAPI(mock_local)
        doia.set_v2_login_token("BIG-FAT-TOKEN")
        self.assertEqual(doia.v2_auth_token, "BIG-FAT-TOKEN")

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_16_is_v2(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test DockerIoAPI().is_v2"""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])
        doia = DockerIoAPI(mock_local)
        doia.registry_url = "http://www.docker.io"
        out = doia.is_v2()
        self.assertFalse(out)

        # needs auth to be working before
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.is_v2()
        # self.assertTrue(out)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_17_get_v2_image_manifest(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test DockerIoAPI().get_v2_image_manifest"""
        self._init()
        imagerepo = "REPO"
        tag = "TAG"

        mock_dgu.return_value = (mock_hdr, [])
        doia = DockerIoAPI(mock_local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2_image_manifest(imagerepo, tag)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.docker.DockerIoAPI._get_file')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_18_get_v2_image_layer(self, mock_local, mock_dgf, mock_hdr, mock_geturl):
        """Test DockerIoAPI().get_v2_image_layer"""
        self._init()
        imagerepo = "REPO"
        layer_id = "LAYERID"
        doia = DockerIoAPI(mock_local)
        doia.registry_url = "https://registry-1.docker.io"

        mock_dgf.return_value = True
        out = doia.get_v2_image_layer(imagerepo, layer_id)
        self.assertTrue(out)

        mock_dgf.return_value = False
        out = doia.get_v2_image_layer(imagerepo, layer_id)
        self.assertFalse(out)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.docker.DockerIoAPI._get_file')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_19_get_v2_layers_all(self, mock_local, mock_dgf, mock_msg, mock_geturl):
        """Test DockerIoAPI().get_v2_layers_all"""
        self._init()

        mock_dgf.return_value = True
        endpoint = "docker.io"
        fslayers = []
        doia = DockerIoAPI(mock_local)
        out = doia.get_v2_layers_all(endpoint, fslayers)
        self.assertEqual(out, [])

        # fslayers = ["a", "b"]
        # doia = udocker.DockerIoAPI(mock_local)
        # out = doia.get_v2_layers_all(endpoint, fslayers)
        # self.assertEqual(out, ['b.json', 'b.layer', 'a.json', 'a.layer'])

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.docker.DockerIoAPI.get_v2_layers_all')
    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_20_get_v2(self, mock_local, mock_dgu, mock_dgv2,
                       mock_msg, mock_hdr, mock_geturl):
        """Test DockerIoAPI().get_v2"""
        self._init()

        mock_dgv2.return_value = []
        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(mock_local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2(imagerepo, tag)
        self.assertEqual(out, [])

        # mock_dgv2.return_value = ["a", "b"]
        # out = doia.get_v2(imagerepo, tag)
        # self.assertEqual(out, [])

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.docker.DockerIoAPI.get_v1_layers_all')
    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_21_get_v1(self, mock_local, mock_dgu, mock_dgv1,
                       mock_msg, mock_hdr, mock_geturl):
        """Test DockerIoAPI().get_v1"""
        self._init()

        mock_dgv1.return_value = []
        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        tag = "TAG"
        doia = DockerIoAPI(mock_local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

        # mock_dgv1.return_value = ["a", "b"]
        # out = doia.get_v1(imagerepo, tag)
        # self.assertEqual(out, [])

    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.docker.DockerIoAPI._parse_imagerepo')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.container.localrepo.LocalRepository.cd_imagerepo')
    def test_22_get(self, mock_cdir, mock_local, mock_parse,
                    mock_msg, mock_hdr, mock_geturl, mock_dgu):
        """Test DockerIoAPI().get"""
        self._init()

        # mock_cdir.return_value = False
        # mock_parse.return_value = ()
        # mock_dgu.return_value = (mock_hdr, [])
        #
        # imagerepo = "REPO"
        # tag = "TAG"
        # doia = udocker.DockerIoAPI(mock_local)
        # doia.registry_url = "https://registry-1.docker.io"
        # out = doia.get(imagerepo, tag)
        # self.assertEqual(out, [])

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_23_search_init(self, mock_local, mock_geturl):
        """Test DockerIoAPI().search_init"""
        self._init()

        doia = DockerIoAPI(mock_local)
        doia.search_init("PAUSE")
        self.assertEqual(doia.search_pause, "PAUSE")
        self.assertEqual(doia.search_page, 0)
        self.assertEqual(doia.search_link, "")
        self.assertEqual(doia.search_ended, False)

    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_24_search_get_page_v1(self, mock_local, mock_msg, mock_hdr,
                                   mock_geturl, mock_dgu):
        """Test DockerIoAPI().set_index"""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])

        doia = DockerIoAPI(mock_local)
        doia.set_index("index.docker.io")
        out = doia.search_get_page_v1("SOMETHING")
        self.assertEqual(out, [])

    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_25_catalog_get_page_v2(self, mock_local, mock_msg, mock_hdr,
                                    mock_geturl, mock_dgu):
        """Test DockerIoAPI().catalog_get_page_v2"""
        self._init()

        # mock_dgu.return_value = (mock_hdr, [])
        #
        # doia = udocker.DockerIoAPI(mock_local)
        # doia.set_index("index.docker.io")
        # out = doia.catalog_get_page_v2("lines")
        # self.assertEqual(out, [])

    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_26_search_get_page(self, mock_local, mock_msg, mock_hdr,
                                mock_geturl, mock_dgu):
        """Test DockerIoAPI().search_get_page"""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])

        doia = DockerIoAPI(mock_local)
        doia.set_index("index.docker.io")
        out = doia.search_get_page("SOMETHING")
        self.assertEqual(out, [])

    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_27__get_url(self, mock_local, mock_msg, mock_hdr,
                         mock_geturl, mock_dgu):
        """Test DockerIoAPI()._get_url"""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])

        doia = DockerIoAPI(mock_local)

    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_28__get_file(self, mock_local, mock_msg, mock_hdr,
                          mock_geturl, mock_dgu):
        """Test DockerIoAPI()._get_file"""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])

        doia = DockerIoAPI(mock_local)


    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_29__get_v1_auth(self, mock_local, mock_msg, mock_geturl):
        """Test DockerIoAPI()._get_v1_auth"""
        self._init()

        doia = DockerIoAPI(mock_local)
        doia.v1_auth_header = "Not Empty"

        www_authenticate = ['Other Stuff']
        out = doia._get_v1_auth(www_authenticate)
        self.assertEqual(out, "")

        www_authenticate = ['Token']
        out = doia._get_v1_auth(www_authenticate)
        self.assertEqual(out, "Not Empty")

    @mock.patch('udocker.docker.DockerIoAPI._get_url')
    @mock.patch('udocker.utils.curl.CurlHeader')
    @mock.patch('json.loads')
    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_30__get_v2_auth(self, mock_local, mock_msg, mock_geturl,
                             mock_jloads, mock_hdr, mock_dgu):
        """Test DockerIoAPI()._get_v2_auth"""
        self._init()

        fakedata = StringIO('token')
        mock_dgu.return_value = (mock_hdr, fakedata)
        mock_jloads.return_value = {'token': 'YYY'}
        doia = DockerIoAPI(mock_local)
        doia.v2_auth_header = "v2 Auth Header"
        doia.v2_auth_token = "v2 Auth Token"

        www_authenticate = 'Other Stuff'
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "")

        www_authenticate = "Bearer realm=REALM"
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "Authorization: Bearer YYY")

        www_authenticate = "BASIC realm=Sonatype Nexus Repository"
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "Authorization: Basic %s" %doia.v2_auth_token)


if __name__ == '__main__':
    unittest.main()
