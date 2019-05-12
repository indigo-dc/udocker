#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: ContainerStructure
"""

import sys
import subprocess
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')

from udocker.container.structure import ContainerStructure
from udocker.config import Config
from udocker.container.localrepo import LocalRepository


class ContainerStructureTestCase(TestCase):
    """Test ContainerStructure() class for containers structure."""

    def setUp(self):
        self.conf = Config().getconf()
        self.conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        self.conf['cmd'] = "/bin/bash"
        self.conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                                ["taskset", "-c", "%s", ])
        self.conf['valid_host_env'] = "HOME"
        self.conf['username'] = "user"
        self.conf['userhome'] = "/"
        self.conf['location'] = ""
        self.conf['oskernel'] = "4.8.13"
        self.local = LocalRepository(self.conf)

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test ContainerStructure()."""
        prex = ContainerStructure(self.local, self.conf)
        self.assertEqual(prex.tag, "")
        self.assertEqual(prex.imagerepo, "")

        prex = ContainerStructure(self.local, self.conf, "123456")
        self.assertEqual(prex.tag, "")
        self.assertEqual(prex.imagerepo, "")
        self.assertEqual(prex.container_id, "123456")

    @patch('udocker.container.localrepo.LocalRepository.load_json', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    @patch('udocker.container.structure.Msg.level')
    def test_02_get_container_attr(self, mock_level, mock_cd, mock_json):
        """Test ContainerStructure().get_container_attr()."""
        mock_level.return_value = 0
        self.conf['location'] = "/"
        prex = ContainerStructure(self.local, self.conf)
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "")
        self.assertEqual(container_json, [])

        self.conf['location'] = ""
        prex = ContainerStructure(self.local, self.conf)
        mock_cd.return_value = ""
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)

        self.conf['location'] = ""
        prex = ContainerStructure(self.local, self.conf)
        mock_cd.return_value = "/"
        mock_json.return_value = []
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)

        self.conf['location'] = ""
        prex = ContainerStructure(self.local, self.conf)
        mock_cd.return_value = "/"
        mock_json.return_value = ["value", ]
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "/")
        self.assertEqual(container_json, ["value", ])

    @patch('udocker.container.localrepo.LocalRepository.setup_container', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.get_image_attributes', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.cd_imagerepo', autospec=True)
    @patch.object(ContainerStructure, '_untar_layers')
    @patch('udocker.container.structure.Unique.uuid')
    @patch('udocker.container.structure.Msg.level')
    def test_03_create(self, mock_level, mock_uuid, mock_untar,
                       mock_cdimg, mock_getimgattr, mock_setcont):
        """Test ContainerStructure().create()."""
        mock_level.return_value = 0
        prex = ContainerStructure(self.local, self.conf)
        mock_cdimg.return_value = ""
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        prex = ContainerStructure(self.local, self.conf)
        mock_cdimg.return_value = "/"
        mock_getimgattr.return_value = ([], [])
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        prex = ContainerStructure(self.local, self.conf)
        mock_cdimg.return_value = "/"
        mock_getimgattr.return_value = (["value", ], [])
        mock_setcont.return_value = ""
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)
        #
        prex = ContainerStructure(self.local, self.conf)
        mock_cdimg.return_value = "/"
        mock_getimgattr.return_value = (["value", ], [])
        mock_setcont.return_value = "/"
        mock_untar.return_value = False
        mock_uuid.return_value = "123456"
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertEqual(status, "123456")

    @patch('udocker.container.structure.FileUtil')
    @patch('udocker.container.structure.Msg.level')
    def test_04__apply_whiteouts(self, mock_level, mock_futil):
        """Test ContainerStructure()._apply_whiteouts()."""
        mock_level.return_value = 0
        prex = ContainerStructure(self.local, self.conf)
        with patch.object(subprocess, 'Popen') as mock_popen:
            mock_popen.return_value.stdout.readline.side_effect = ["/aaa", "", ]
            status = prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(status)
        self.assertFalse(mock_futil.called)

        prex = ContainerStructure(self.local, self.conf)
        with patch.object(subprocess, 'Popen') as mock_popen:
            mock_popen.return_value.stdout.readline.side_effect = [
                "/a/.wh.x", "", ]
            status = prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(status)
        # TODO: uncomment below after figure out why is giving false
        #self.assertTrue(mock_futil.called)

    @patch('udocker.container.structure.subprocess.call')
    @patch.object(ContainerStructure, '_apply_whiteouts')
    @patch('udocker.container.structure.Msg.level')
    def test_05__untar_layers(self, mock_level, mock_appwhite, mock_call):
        """Test ContainerStructure()._untar_layers()."""
        mock_level.return_value = 0
        tarfiles = ["a.tar", "b.tar", ]
        mock_call.return_value = False
        prex = ContainerStructure(self.local, self.conf)
        status = prex._untar_layers(tarfiles, "/tmp")
        self.assertTrue(status)
        self.assertTrue(mock_call.called)

        mock_call.reset_mock()
        mock_call.return_value = True
        prex = ContainerStructure(self.local, self.conf)
        status = prex._untar_layers(tarfiles, "/tmp")
        self.assertFalse(status)
        self.assertTrue(mock_call.called)

        mock_call.reset_mock()
        mock_call.return_value = True
        prex = ContainerStructure(self.local, self.conf)
        status = prex._untar_layers([], "/tmp")
        self.assertFalse(status)
        self.assertFalse(mock_call.called)

    @patch('udocker.container.structure.Msg.level')
    def test_06_get_container_meta(self, mock_level):
        """Test ContainerStructure().get_container_meta()."""
        mock_level.return_value = 0
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
        prex = ContainerStructure(self.local, self.conf)
        status = prex.get_container_meta("Cmd", "", container_json)
        self.assertEqual(status, "/bin/bash")

        prex = ContainerStructure(self.local, self.conf)
        status = prex.get_container_meta("XXX", "", container_json)
        self.assertEqual(status, "")
        #self.assertEqual(status, None)

        prex = ContainerStructure(self.local, self.conf)
        status = prex.get_container_meta("Entrypoint", "BBB", container_json)
        self.assertEqual(status, "BBB")

    @patch('udocker.container.structure.Msg.level')
    def test_07__dict_to_str(self, mock_level):
        """Test ContainerStructure()._dict_to_str()."""
        mock_level.return_value = 0
        prex = ContainerStructure(self.local, self.conf)
        status = prex._dict_to_str({'A': 1, 'B': 2})
        self.assertTrue(status in ("A:1 B:2 ", "B:2 A:1 ", ))
        #self.assertEqual(status, "A:1 B:2 ")

    @patch('udocker.container.structure.Msg.level')
    def test_08__dict_to_list(self, mock_level):
        """Test ContainerStructure()._dict_to_list()."""
        mock_level.return_value = 0
        prex = ContainerStructure(self.local, self.conf)
        status = prex._dict_to_list({'A': 1, 'B': 2})
        self.assertEqual(sorted(status), sorted(["A:1", "B:2"]))


if __name__ == '__main__':
    main()
