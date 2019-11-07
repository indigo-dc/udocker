#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: ContainerStructure
"""

import subprocess
from unittest import TestCase, main
from udocker.container.structure import ContainerStructure
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


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
    @patch('udocker.container.structure.Msg')
    def test_02_get_container_attr(self, mock_msg, mock_cd, mock_json):
        """Test ContainerStructure().get_container_attr()."""
        mock_msg.return_value.level.return_value = 0
        self.conf['location'] = "/"
        prex = ContainerStructure(self.local, self.conf)
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "")
        self.assertEqual(container_json, [])

        self.conf['location'] = ""
        mock_cd.return_value = ""
        prex = ContainerStructure(self.local, self.conf)
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)
        self.assertTrue(mock_msg.return_value.err.called)

        self.conf['location'] = ""
        mock_cd.return_value = "/"
        mock_json.return_value = []
        prex = ContainerStructure(self.local, self.conf)
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)
        self.assertTrue(mock_msg.return_value.err.called)

        self.conf['location'] = ""
        mock_cd.return_value = "/"
        mock_json.return_value = ["value", ]
        prex = ContainerStructure(self.local, self.conf)
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "/")
        self.assertEqual(container_json, ["value", ])

    @patch('udocker.container.localrepo.LocalRepository.setup_container', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.get_image_attributes', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.cd_imagerepo', autospec=True)
    @patch.object(ContainerStructure, '_untar_layers')
    @patch('udocker.container.structure.Unique.uuid')
    @patch('udocker.container.structure.Msg')
    def test_03_create_fromimage(self, mock_msg, mock_uuid, mock_untar,
                                 mock_cdimg, mock_getimgattr, mock_setcont):
        """Test ContainerStructure().create_fromimage()."""
        mock_msg.return_value.level.return_value = 0
        mock_cdimg.return_value = ""
        prex = ContainerStructure(self.local, self.conf)
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        mock_cdimg.return_value = "/"
        mock_getimgattr.return_value = ([], [])
        prex = ContainerStructure(self.local, self.conf)
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        mock_cdimg.return_value = "/"
        mock_getimgattr.return_value = (["value", ], [])
        mock_setcont.return_value = ""
        prex = ContainerStructure(self.local, self.conf)
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        mock_cdimg.return_value = "/"
        mock_getimgattr.return_value = (["value", ], [])
        mock_setcont.return_value = "/"
        mock_untar.return_value = False
        mock_uuid.return_value = "123456"
        prex = ContainerStructure(self.local, self.conf)
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertEqual(status, "123456")

    @patch.object(ContainerStructure, '_chk_container_root')
    @patch.object(ContainerStructure, '_untar_layers')
    @patch('udocker.container.localrepo.LocalRepository.save_json', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.setup_container', autospec=True)
    @patch('udocker.container.structure.Unique.uuid')
    @patch('udocker.container.structure.Msg')
    def test_04_create_fromlayer(self, mock_msg, mock_uuid, mock_setcont,
                                 mock_save, mock_untar, mock_chkcont):
        """Test ContainerStructure().create_fromlayer()."""
        # Empty container_json
        cont_json = dict()
        mock_msg.return_value.level.return_value = 0
        mock_uuid.return_value = "123456"
        prex = ContainerStructure(self.local, self.conf)
        status = prex.create_fromlayer("imagerepo", "tag", "layer", cont_json)
        self.assertFalse(status)

        # Non-empty container_json, empty cont dir
        cont_json = {
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
        mock_msg.return_value.level.return_value = 0
        mock_uuid.return_value = "123456"
        mock_setcont.return_value = ""
        prex = ContainerStructure(self.local, self.conf)
        status = prex.create_fromlayer("imagerepo", "tag", "layer", cont_json)
        self.assertFalse(status)

        # Non-empty container_json, non empty cont dir
        mock_msg.return_value.level.return_value = 0
        mock_uuid.return_value = "123456"
        mock_setcont.return_value = "/ROOT"
        mock_save.return_value = True
        mock_untar.return_value = True
        mock_chkcont.return_value = 3
        prex = ContainerStructure(self.local, self.conf)
        status = prex.create_fromlayer("imagerepo", "tag", "layer", cont_json)
        self.assertEqual(status, "123456")

    @patch.object(ContainerStructure, '_chk_container_root')
    @patch.object(ContainerStructure, '_untar_layers')
    @patch('udocker.container.localrepo.LocalRepository.setup_container', autospec=True)
    @patch('udocker.container.structure.Unique.uuid')
    @patch('udocker.container.structure.Msg')
    def test_05_clone_fromfile(self, mock_msg, mock_uuid, mock_setcont,
                               mock_untar, mock_chkcont):
        """Test ContainerStructure().clone_fromfile()."""
        # Empty container_dir
        mock_msg.return_value.level.return_value = 0
        mock_setcont.return_value = ""
        mock_uuid.return_value = "123456"
        prex = ContainerStructure(self.local, self.conf)
        status = prex.clone_fromfile("clone_file")
        self.assertFalse(status)

        # Non-empty container_dir
        mock_msg.return_value.level.return_value = 0
        mock_setcont.return_value = "/ROOT"
        mock_uuid.return_value = "123456"
        mock_untar.return_value = True
        mock_chkcont.return_value = 3
        prex = ContainerStructure(self.local, self.conf)
        status = prex.clone_fromfile("clone_file")
        self.assertEqual(status, "123456")

    def test_06_get_container_meta(self):
        """Test ContainerStructure().get_container_meta()."""
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
        self.assertEqual(status, '')

        prex = ContainerStructure(self.local, self.conf)
        status = prex.get_container_meta("Entrypoint", "BBB", container_json)
        self.assertEqual(status, "BBB")

    @patch.object(ContainerStructure, '_tar')
    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    @patch('udocker.container.structure.Msg')
    def test_07_export_tofile(self, mock_msg, mock_cdcont, mock_tar):
        """Test ContainerStructure().export_tofile()."""
        # Empty container dir
        mock_msg.return_value.level.return_value = 0
        mock_cdcont.return_value = ""
        mock_tar.return_value = True
        prex = ContainerStructure(self.local, self.conf)
        status = prex.export_tofile("clone_file")
        self.assertFalse(status)

        # Non-empty container dir
        mock_msg.return_value.level.return_value = 0
        mock_cdcont.return_value = "/ROOT"
        mock_tar.return_value = True
        prex = ContainerStructure(self.local, self.conf, "123456")
        status = prex.export_tofile("clone_file")
        self.assertEqual(status, "123456")

    @patch.object(ContainerStructure, '_tar')
    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    @patch('udocker.container.structure.Msg')
    def test_08_clone_tofile(self, mock_msg, mock_cdcont, mock_tar):
        """Test ContainerStructure().clone_tofile()."""
        # Empty container dir
        mock_msg.return_value.level.return_value = 0
        mock_cdcont.return_value = ""
        mock_tar.return_value = True
        prex = ContainerStructure(self.local, self.conf)
        status = prex.clone_tofile("clone_file")
        self.assertFalse(status)

        # Non-empty container dir
        mock_msg.return_value.level.return_value = 0
        mock_cdcont.return_value = "/ROOT"
        mock_tar.return_value = True
        prex = ContainerStructure(self.local, self.conf, "123456")
        status = prex.clone_tofile("clone_file")
        self.assertEqual(status, "123456")

    def test_09_clone(self):
        """Test ContainerStructure().clone()."""
        pass

    @patch('udocker.container.structure.FileUtil')
    def test_10__apply_whiteouts(self, mock_futil):
        """Test ContainerStructure()._apply_whiteouts()."""
        with patch.object(subprocess, 'Popen') as mock_popen:
            mock_popen.return_value.stdout.readline.side_effect = ["/aaa", "", ]
            prex = ContainerStructure(self.local, self.conf)
            status = prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(status)
        self.assertFalse(mock_futil.called)

        with patch.object(subprocess, 'Popen') as mock_popen:
            mock_popen.return_value.stdout.readline.side_effect = [
                "/a/.wh.x", "", ]
            prex = ContainerStructure(self.local, self.conf)
            status = prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(status)
        self.assertTrue(mock_futil.called)

    @patch('udocker.container.structure.subprocess.call')
    @patch.object(ContainerStructure, '_apply_whiteouts')
    @patch('udocker.container.structure.Msg')
    def test_11__untar_layers(self, mock_msg, mock_appwhite, mock_call):
        """Test ContainerStructure()._untar_layers()."""
        mock_msg.level = 0
        mock_msg.VER = 3
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

    def test_12__dict_to_str(self):
        """Test ContainerStructure()._dict_to_str()."""
        prex = ContainerStructure(self.local, self.conf)
        status = prex._dict_to_str({'A': 1, 'B': 2})
        self.assertTrue(status in ("A:1 B:2 ", "B:2 A:1 ", ))
        self.assertEqual(status, "A:1 B:2 ")

    def test_13__dict_to_list(self):
        """Test ContainerStructure()._dict_to_list()."""
        prex = ContainerStructure(self.local, self.conf)
        status = prex._dict_to_list({'A': 1, 'B': 2})
        self.assertEqual(sorted(status), sorted(["A:1", "B:2"]))


if __name__ == '__main__':
    main()
