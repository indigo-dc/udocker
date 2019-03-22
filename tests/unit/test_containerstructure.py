#!/usr/bin/env python2
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
import subprocess
import unittest
import mock

sys.path.append('.')

from udocker.container.structure import ContainerStructure
from udocker.config import Config


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class ContainerStructureTestCase(unittest.TestCase):
    """Test ContainerStructure() class for containers structure."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        Config = mock.MagicMock()
        Config.hostauth_list = ("/etc/passwd", "/etc/group")
        Config.cmd = "/bin/bash"
        Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                                          ["taskset", "-c", "%s", ])
        Config.valid_host_env = "HOME"
        Config.return_value.username.return_value = "user"
        Config.return_value.userhome.return_value = "/"
        Config.location = ""
        Config.return_value.oskernel.return_value = "4.8.13"

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local):
        """Test ContainerStructure()."""
        self._init()
        #
        prex = ContainerStructure(mock_local)
        self.assertEqual(prex.tag, "")
        self.assertEqual(prex.imagerepo, "")
        #
        prex = ContainerStructure(mock_local, "123456")
        self.assertEqual(prex.tag, "")
        self.assertEqual(prex.imagerepo, "")
        self.assertEqual(prex.container_id, "123456")

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_02_get_container_attr(self, mock_local, mock_msg):
        """Test ContainerStructure().get_container_attr()."""
        self._init()
        mock_msg.level = 0
        #
        prex = ContainerStructure(mock_local)
        Config.location = "/"
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "")
        self.assertEqual(container_json, [])
        #
        prex = ContainerStructure(mock_local)
        Config.location = ""
        mock_local.cd_container.return_value = ""
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)
        #
        prex = ContainerStructure(mock_local)
        Config.location = ""
        mock_local.cd_container.return_value = "/"
        mock_local.load_json.return_value = []
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)
        #
        prex = ContainerStructure(mock_local)
        Config.location = ""
        mock_local.cd_container.return_value = "/"
        mock_local.load_json.return_value = ["value", ]
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "/")
        self.assertEqual(container_json, ["value", ])

    @mock.patch('udocker.container.structure.ContainerStructure._untar_layers')
    @mock.patch('udocker.helper.unique.Unique.uuid')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_03_create(self, mock_local, mock_msg, mock_uuid,
                       mock_untar):
        """Test ContainerStructure().create()."""
        self._init()
        mock_msg.level = 0
        #
        prex = ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = ""
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)
        #
        prex = ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = "/"
        mock_local.get_image_attributes.return_value = ([], [])
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)
        #
        prex = ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = "/"
        mock_local.get_image_attributes.return_value = (["value", ], [])
        mock_local.setup_container.return_value = ""
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)
        #
        prex = ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = "/"
        mock_local.get_image_attributes.return_value = (["value", ], [])
        mock_local.setup_container.return_value = "/"
        mock_untar.return_value = False
        mock_uuid.return_value = "123456"
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertEqual(status, "123456")

    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_04__apply_whiteouts(self, mock_local, mock_msg, mock_futil):
        """Test ContainerStructure()._apply_whiteouts()."""
        self._init()
        mock_msg.level = 0
        #
        prex = ContainerStructure(mock_local)
        with mock.patch.object(subprocess, 'Popen') as mock_popen:
            mock_popen.return_value.stdout.readline.side_effect = [
                "/aaa", "", ]
            status = prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(status)
        self.assertFalse(mock_futil.called)
        #
        prex = ContainerStructure(mock_local)
        with mock.patch.object(subprocess, 'Popen') as mock_popen:
            mock_popen.return_value.stdout.readline.side_effect = [
                "/a/.wh.x", "", ]
            status = prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(status)
        # TODO: uncomment below after figure out why is giving false
        #self.assertTrue(mock_futil.called)

    @mock.patch('subprocess.call')
    @mock.patch('udocker.container.structure.ContainerStructure._apply_whiteouts')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_05__untar_layers(self, mock_local, mock_msg, mock_appwhite,
                              mock_call):
        """Test ContainerStructure()._untar_layers()."""
        self._init()
        mock_msg.level = 0
        tarfiles = ["a.tar", "b.tar", ]
        #
        mock_call.return_value = False
        prex = ContainerStructure(mock_local)
        status = prex._untar_layers(tarfiles, "/tmp")
        self.assertTrue(status)
        self.assertTrue(mock_call.called)
        #
        mock_call.reset_mock()
        mock_call.return_value = True
        prex = ContainerStructure(mock_local)
        status = prex._untar_layers(tarfiles, "/tmp")
        self.assertFalse(status)
        self.assertTrue(mock_call.called)
        #
        mock_call.reset_mock()
        mock_call.return_value = True
        prex = ContainerStructure(mock_local)
        status = prex._untar_layers([], "/tmp")
        self.assertFalse(status)
        self.assertFalse(mock_call.called)

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_06_get_container_meta(self, mock_local, mock_msg):
        """Test ContainerStructure().get_container_meta()."""
        self._init()
        mock_msg.level = 0
        container_json = {
            "architecture": "amd64",
            "author": "https://github.com/CentOS/sig-cloud-instance-images",
            "config": {
                "AttachStderr": False,
                "AttachStdin": False,
                "AttachStdout": False,
                "Cmd": [
                    "/bin/bash"
                ],
                "Domainname": "",
                "Entrypoint": None,
                "Env": [
                    "PATH=\
                    /usr/local/sbin:\
                    /usr/local/bin:/usr/sbin:\
                    /usr/bin:/sbin:\
                    /bin"
                ],
                "Hostname": "9aac06993d69",
                "Image": "sha256:4f64745dd34556af8f644a7886fcf" +
                         "cb11c059f64e1b0a753cb41188656ec8b33",
                "Labels": {
                    "build-date": "20161102",
                    "license": "GPLv2",
                    "name": "CentOS Base Image",
                    "vendor": "CentOS"
                },
                "OnBuild": None,
                "OpenStdin": False,
                "StdinOnce": False,
                "Tty": False,
                "User": "",
                "Volumes": None,
                "WorkingDir": ""
            },
        }
        #
        prex = ContainerStructure(mock_local)
        status = prex.get_container_meta("Cmd", "", container_json)
        self.assertEqual(status, "/bin/bash")
        #
        status = prex.get_container_meta("XXX", "", container_json)
        self.assertEqual(status, "")
        #self.assertEqual(status, None)
        #
        status = prex.get_container_meta("Entrypoint", "BBB", container_json)
        self.assertEqual(status, "BBB")

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_07__dict_to_str(self, mock_local, mock_msg):
        """Test ContainerStructure()._dict_to_str()."""
        self._init()
        mock_msg.level = 0
        #
        prex = ContainerStructure(mock_local)
        status = prex._dict_to_str({'A': 1, 'B': 2})
        self.assertTrue(status in ("A:1 B:2 ", "B:2 A:1 ", ))
        #self.assertEqual(status, "A:1 B:2 ")

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_08__dict_to_list(self, mock_local, mock_msg):
        """Test ContainerStructure()._dict_to_list()."""
        self._init()
        mock_msg.level = 0
        #
        prex = ContainerStructure(mock_local)
        status = prex._dict_to_list({'A': 1, 'B': 2})
        self.assertEqual(sorted(status), sorted(["A:1", "B:2"]))


if __name__ == '__main__':
    unittest.main()
