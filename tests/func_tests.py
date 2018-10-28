#!/usr/bin/env python2
"""
========================
udocker functional tests
========================
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

__author__ = "udocker@lip.pt"
__credits__ = ["PRoot http://proot.me",
               "runC https://runc.io",
               "Fakechroot https://github.com/dex4er/fakechroot"
              ]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "1.1.0"
__date__ = "2016"

try:
    import udocker
except ImportError:
    sys.path.append(".")
    sys.path.append("..")
    import udocker

STDOUT = sys.stdout


def set_env():
    """Set environment variables"""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


def find_str(self, find_exp, where):
    """Find string in test ouput messages"""
    found = False
    for item in where:
        if find_exp in str(item):
            self.assertTrue(True)
            found = True
            break
    if not found:
        self.assertTrue(False)


def set_msglevels(mock_msg):
    """Set mock Msg() class message levels"""
    mock_msg.ERR = 0
    mock_msg.MSG = 1
    mock_msg.WAR = 2
    mock_msg.INF = 3
    mock_msg.VER = 4
    mock_msg.DBG = 5
    mock_msg.DEF = mock_msg.INF


class MainTestCase(unittest.TestCase):
    """Test most udocker capabilities"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    @mock.patch('udocker.sys.exit')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.UdockerTools')
    @mock.patch('udocker.Config.user_init')
    @mock.patch('udocker.Udocker.do_images')
    @mock.patch('udocker.Msg')
    def test_init(self, mock_msg, mock_images,
                  mock_user_init, mock_utools, mock_localrepo, mock_exit):
        """Test udocker global command line options"""
        set_msglevels(mock_msg)
        udocker.Msg = mock_msg
        t_argv = ['./udocker.py', "images"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main().start()
            self.assertTrue(mock_images.called)
        t_argv = ['./udocker.py', "--config=/myconf", "images"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main().start()
            self.assertTrue(mock_user_init.called_with("/myconf"))
        t_argv = ['./udocker.py', "--cofig=/myconf"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main().start()
            self.assertTrue(mock_exit.called)
        udocker.Config().verbose_level = 0
        t_argv = ['./udocker.py', "-D", "images"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main().start()
            self.assertEqual(udocker.Config().verbose_level, mock_msg.DBG)
        udocker.Config().verbose_level = 0
        t_argv = ['./udocker.py', "--debug"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main().start()
            self.assertEqual(udocker.Config().verbose_level, mock_msg.DBG)
        udocker.Config().verbose_level = 0
        t_argv = ['./udocker.py', "-q"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main().start()
            self.assertEqual(udocker.Config().verbose_level, mock_msg.MSG)
        udocker.Config().verbose_level = 0
        t_argv = ['./udocker.py', "--quiet"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main().start()
            self.assertEqual(udocker.Config().verbose_level, mock_msg.MSG)
        t_argv = ['./udocker.py', "--insecure"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main().start()
            self.assertEqual(udocker.Config().http_insecure, True)
        t_argv = ['./udocker.py', "--repo=/tmp"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main().start()
            self.assertEqual(udocker.Config().topdir, "/tmp")

    @mock.patch('udocker.UdockerTools')
    @mock.patch('udocker.Msg')
    def test_execute_help(self, mock_msg, mock_utools):
        """Test udocker help command"""
        udocker.msg = mock_msg
        udocker.conf = udocker.Config()
        t_argv = ['./udocker.py', "help"]
        with mock.patch.object(sys, 'argv', t_argv):
            main = udocker.Main()
            main.execute()
            find_str(self, "Examples", mock_msg.return_value.out.call_args)

    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.UdockerTools')
    @mock.patch('udocker.Msg')
    def test_do_search(self, mock_msg, mock_utools, mock_dockioapi):
        """Test udocker search command"""
        udocker.Msg = mock_msg
        udocker.conf = udocker.Config()
        t_argv = ['./udocker.py', "search", "-a", "iscampos"]
        with mock.patch.object(sys, 'argv', t_argv):
            mock_dockioapi.return_value.is_v2.return_value = False
            mock_dockioapi.return_value.set_v2_login_token.return_value = None
            mock_dockioapi.return_value.search_get_page.side_effect = [
                {u'num_results': 2, u'results': [
                    {u'is_automated': False, u'name': u'iscampos/openqcd',
                     u'star_count': 0, u'is_trusted': False,
                     u'is_official': False,
                     u'description': u'Containers for openQCD v1.4'},
                    {u'is_automated': False, u'name': u'iscampos/codemaster',
                     u'star_count': 0, u'is_trusted': False,
                     u'is_official': False, u'description': u''}],
                 u'page_size': 25, u'query': u'iscampos',
                 u'num_pages': '1', u'page': u'0'},
                {u'num_results': 2, u'results': [
                    {u'is_automated': False, u'name': u'iscampos/openqcd',
                     u'star_count': 0, u'is_trusted': False,
                     u'is_official': False,
                     u'description': u'Containers for openQCD v1.4'},
                    {u'is_automated': False, u'name': u'iscampos/codemaster',
                     u'star_count': 0, u'is_trusted': False,
                     u'is_official': False, u'description': u''}],
                 u'page_size': 25, u'query': u'iscampos',
                 u'num_pages': '1', u'page': u'1'},
                {}]
            main = udocker.Main()
            main.execute()
            find_str(self, "iscampos/codemaster",
                     mock_msg.return_value.out.call_args)

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.UdockerTools')
    @mock.patch('udocker.Msg')
    def test_do_images(self, mock_msg, mock_utools, mock_localrepo):
        """Test udocker images command"""
        udocker.Msg = mock_msg
        udocker.conf = udocker.Config()
        mock_localrepo.return_value.cd_imagerepo.return_value = \
            "/home/user/.udocker/repos/X/latest"
        mock_localrepo.return_value.get_imagerepos.return_value = [
            ('iscampos/openqcd', 'latest'), ('busybox', 'latest')]
        t_argv = ['./udocker.py', "images"]
        with mock.patch.object(sys, 'argv', t_argv):
            # Unprotected
            mock_localrepo.return_value.isprotected_imagerepo\
                .return_value = False
            main = udocker.Main()
            main.execute()
            msg_out = ("busybox:latest"
                       "                                               .")
            find_str(self, msg_out, mock_msg.return_value.out.call_args)
            # Protected
            mock_localrepo.return_value.isprotected_imagerepo\
                .return_value = True
            main.execute()
            msg_out = ("busybox:latest"
                       "                                               P")
            find_str(self, msg_out, mock_msg.return_value.out.call_args)
        t_argv = ['./udocker.py', "images", "-l"]
        with mock.patch.object(sys, 'argv', t_argv):
            main = udocker.Main()
            main.execute()
            msg_out = "  /home/user/.udocker/repos/X/latest"
            find_str(self, msg_out, mock_msg.return_value.out.call_args)
            #
            mock_localrepo.return_value.get_imagerepos.return_value = [
                ('busybox', 'latest')]
            mock_localrepo.return_value.get_layers.return_value = [
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 'sha256:385e281300cc6d88bdd155e0931fbdfbb1801c2b' +
                 '0265340a40481ee2b733ae66', 675992),
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 '56ed16bd6310cca65920c653a9bb22de6b235990dcaa174' +
                 '2ff839867aed730e5.layer', 675992),
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 '56ed16bd6310cca65920c653a9bb22de6b235990dcaa174' +
                 '2ff839867aed730e5.json', 1034),
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 'bc744c4ab376115cc45c610d53f529dd2d4249ae6b35e5d' +
                 '6e7a96e58863545aa.json', 1155),
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 'bc744c4ab376115cc45c610d53f529dd2d4249ae6b35e5d' +
                 '6e7a96e58863545aa.layer', 32),
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 'sha256:a3ed95caeb02ffe68cdd9fd84406680ae93d633c' +
                 'b16422d00e8a7c22955b46d4', 32)]
            main.execute()
            msg_out = '    /home/jorge/.udocker/repos/busybox/latest/' +\
                'sha256:a3ed95caeb02ffe68cdd9fd84406680ae93d633cb16' +\
                '422d00e8a7c22955b46d4 ('
            find_str(self, msg_out, mock_msg.return_value.out.call_args)


if __name__ == '__main__':
    unittest.main()
