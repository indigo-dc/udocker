#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: ContainerStructure
"""

from unittest import TestCase, main
from unittest.mock import patch, Mock
from udocker.container.structure import ContainerStructure
from udocker.config import Config


class ContainerStructureTestCase(TestCase):
    """Test ContainerStructure() class for containers structure."""

    def setUp(self):
        Config().getconf()
        Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        Config().conf['cmd'] = "/bin/bash"
        Config().conf['cpu_affinity_exec_tools'] = \
            (["numactl", "-C", "%s", "--", ],
             ["taskset", "-c", "%s", ])
        Config().conf['valid_host_env'] = "HOME"
        Config().conf['username'] = "user"
        Config().conf['userhome'] = "/"
        Config().conf['location'] = ""
        Config().conf['oskernel'] = "4.8.13"

        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

    def tearDown(self):
        self.lrepo.stop()

    def test_01_init(self):
        """Test01 ContainerStructure()."""
        prex = ContainerStructure(self.local)
        self.assertEqual(prex.tag, "")
        self.assertEqual(prex.imagerepo, "")
        self.assertEqual(prex.localrepo, self.local)

        prex = ContainerStructure(self.local, "123456")
        self.assertEqual(prex.tag, "")
        self.assertEqual(prex.imagerepo, "")
        self.assertEqual(prex.container_id, "123456")

    @patch('udocker.container.structure.Msg')
    def test_02_get_container_attr(self, mock_msg):
        """Test02 ContainerStructure().get_container_attr()."""
        mock_msg.return_value.level.return_value = 0
        Config().conf['location'] = "/"
        prex = ContainerStructure(self.local)
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "")
        self.assertEqual(container_json, [])

        Config().conf['location'] = ""
        self.local.cd_container.return_value = ""
        prex = ContainerStructure(self.local)
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)
        self.assertTrue(mock_msg.return_value.err.called)

        Config().conf['location'] = ""
        self.local.cd_container.return_value = "/"
        self.local.load_json.return_value = []
        prex = ContainerStructure(self.local)
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)
        self.assertTrue(mock_msg.return_value.err.called)

        Config().conf['location'] = ""
        self.local.cd_container.return_value = "/"
        self.local.load_json.return_value = ["value", ]
        prex = ContainerStructure(self.local)
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "/")
        self.assertEqual(container_json, ["value", ])

    def test_03_get_container_meta(self):
        """Test03 ContainerStructure().get_container_meta()."""
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
        prex = ContainerStructure(self.local)
        status = prex.get_container_meta("Cmd", "", container_json)
        self.assertEqual(status, "/bin/bash")

        prex = ContainerStructure(self.local)
        status = prex.get_container_meta("XXX", "", container_json)
        self.assertEqual(status, "")

        prex = ContainerStructure(self.local)
        status = prex.get_container_meta("Entrypoint", "BBB", container_json)
        self.assertEqual(status, "BBB")

    def test_04__dict_to_str(self):
        """Test04 ContainerStructure()._dict_to_str()."""
        prex = ContainerStructure(self.local)
        status = prex._dict_to_str({'A': 1, 'B': 2})
        self.assertTrue(status in ("A:1 B:2 ", "B:2 A:1 ", ))
        self.assertEqual(status, "A:1 B:2 ")

    def test_05__dict_to_list(self):
        """Test05 ContainerStructure()._dict_to_list()."""
        prex = ContainerStructure(self.local)
        status = prex._dict_to_list({'A': 1, 'B': 2})
        self.assertEqual(sorted(status), sorted(["A:1", "B:2"]))

    @patch('udocker.container.structure.os.path.exists')
    def test_06__chk_container_root(self, mock_exists):
        """Test06 ContainerStructure()._chk_container_root()."""
        self.local.cd_container.return_value = ""
        prex = ContainerStructure(self.local)
        status = prex._chk_container_root("12345")
        self.assertEqual(status, 0)

        self.local.cd_container.return_value = "/ROOT"
        mock_exists.side_effect = [True, True, False, True,
                                   True, False, False, False,
                                   True, False, True, True, False]
        prex = ContainerStructure(self.local)
        status = prex._chk_container_root()
        self.assertEqual(status, 7)

    @patch.object(ContainerStructure, '_untar_layers')
    @patch('udocker.container.structure.Unique.uuid')
    @patch('udocker.container.structure.Msg')
    def test_07_create_fromimage(self, mock_msg, mock_uuid, mock_untar):
        """Test07 ContainerStructure().create_fromimage()."""
        mock_msg.return_value.level.return_value = 0
        self.local.cd_imagerepo.return_value = ""
        prex = ContainerStructure(self.local)
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        self.local.cd_imagerepo.return_value = "/"
        self.local.get_image_attributes.return_value = ([], [])
        prex = ContainerStructure(self.local)
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        self.local.cd_imagerepo.return_value = "/"
        self.local.get_image_attributes.return_value = (["value", ], [])
        self.local.setup_container.return_value = ""
        prex = ContainerStructure(self.local)
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        self.local.cd_imagerepo.return_value = "/"
        self.local.get_image_attributes.return_value = (["value", ], [])
        self.local.setup_container.return_value = "/"
        mock_untar.return_value = False
        mock_uuid.return_value = "123456"
        prex = ContainerStructure(self.local)
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertEqual(status, "123456")

    @patch.object(ContainerStructure, '_chk_container_root')
    @patch.object(ContainerStructure, '_untar_layers')
    @patch('udocker.container.structure.Unique.uuid')
    @patch('udocker.container.structure.Msg')
    def test_08_create_fromlayer(self, mock_msg, mock_uuid,
                                 mock_untar, mock_chkcont):
        """Test08 ContainerStructure().create_fromlayer()."""
        # Empty container_json
        cont_json = dict()
        mock_msg.return_value.level.return_value = 0
        mock_uuid.return_value = "123456"
        prex = ContainerStructure(self.local)
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
        self.local.setup_container.return_value = ""
        prex = ContainerStructure(self.local)
        status = prex.create_fromlayer("imagerepo", "tag", "layer", cont_json)
        self.assertFalse(status)

        # Non-empty container_json, non empty cont dir
        mock_msg.return_value.level.return_value = 0
        mock_uuid.return_value = "123456"
        self.local.setup_container.return_value = "/ROOT"
        self.local.save_json.return_value = True
        mock_untar.return_value = True
        mock_chkcont.return_value = 3
        prex = ContainerStructure(self.local)
        status = prex.create_fromlayer("imagerepo", "tag", "layer", cont_json)
        self.assertEqual(status, "123456")

    @patch.object(ContainerStructure, '_chk_container_root')
    @patch.object(ContainerStructure, '_untar_layers')
    @patch('udocker.container.structure.Unique.uuid')
    @patch('udocker.container.structure.Msg')
    def test_09_clone_fromfile(self, mock_msg, mock_uuid,
                               mock_untar, mock_chkcont):
        """Test09 ContainerStructure().clone_fromfile()."""
        # Empty container_dir
        mock_msg.return_value.level.return_value = 0
        self.local.setup_container.return_value = ""
        mock_uuid.return_value = "123456"
        prex = ContainerStructure(self.local)
        status = prex.clone_fromfile("clone_file")
        self.assertFalse(status)

        # Non-empty container_dir
        mock_msg.return_value.level.return_value = 0
        self.local.setup_container.return_value = "/ROOT"
        mock_uuid.return_value = "123456"
        mock_untar.return_value = True
        mock_chkcont.return_value = 3
        prex = ContainerStructure(self.local)
        status = prex.clone_fromfile("clone_file")
        self.assertEqual(status, "123456")

    @patch('udocker.container.structure.os.listdir')
    @patch('udocker.container.structure.os.path.isdir')
    @patch('udocker.container.structure.os.path.dirname')
    @patch('udocker.container.structure.os.path.basename')
    @patch('udocker.container.structure.Uprocess.get_output')
    @patch('udocker.container.structure.HostInfo.cmd_has_option')
    @patch('udocker.container.structure.FileUtil.remove')
    def test_10__apply_whiteouts(self, mock_furm, mock_hinfocmd,
                                 mock_uprocget, mock_base, mock_dir,
                                 mock_isdir, mock_lsdir):
        """Test10 ContainerStructure()._apply_whiteouts()."""
        mock_hinfocmd.return_value = False
        mock_uprocget.return_value = ""
        prex = ContainerStructure(self.local)
        prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(mock_hinfocmd.called)
        self.assertTrue(mock_uprocget.called)

        mock_hinfocmd.return_value = False
        mock_uprocget.return_value = "/d1/.wh.aa\n/d1/.wh.bb\n"
        mock_base.side_effect = [".wh.aa", ".wh.bb", ".wh.aa", ".wh.bb"]
        mock_dir.side_effect = ["/d1", "/d2"]
        mock_isdir.side_effect = [True, True]
        mock_lsdir.side_effect = [".wh.aa", ".wh.bb"]
        mock_furm.side_effect = [None, None]
        prex = ContainerStructure(self.local)
        prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(mock_hinfocmd.called)
        self.assertTrue(mock_uprocget.called)
        self.assertTrue(mock_base.called)
        self.assertTrue(mock_dir.called)
        self.assertTrue(mock_furm.called)

    @patch('udocker.container.structure.HostInfo')
    @patch('udocker.container.structure.subprocess.call')
    @patch.object(ContainerStructure, '_apply_whiteouts')
    @patch('udocker.container.structure.Msg')
    def test_11__untar_layers(self, mock_msg, mock_appwhite, mock_call,
                              mock_hinfo):
        """Test11 ContainerStructure()._untar_layers()."""
        mock_msg.level = 0
        tarfiles = ["a.tar", "b.tar", ]
        mock_msg.VER = 3
        mock_hinfo.gid = "1000"
        mock_hinfo.return_value.cmd_has_option.return_value = False
        mock_appwhite.side_effect = [None, None]
        mock_call.side_effect = [1, 1, 1, 1]
        prex = ContainerStructure(self.local)
        status = prex._untar_layers(tarfiles, "/tmp")
        self.assertFalse(status)
        self.assertTrue(mock_call.call_count, 2)
        self.assertTrue(mock_appwhite.call_count, 2)

        mock_msg.level = 0
        tarfiles = ["a.tar", "b.tar", ]
        mock_msg.VER = 3
        mock_hinfo.gid = "1000"
        mock_hinfo.return_value.cmd_has_option.return_value = False
        mock_appwhite.side_effect = [None, None]
        mock_call.side_effect = [0, 0, 0, 0]
        prex = ContainerStructure(self.local)
        status = prex._untar_layers(tarfiles, "/tmp")
        self.assertTrue(status)
        self.assertTrue(mock_call.call_count, 2)
        self.assertTrue(mock_appwhite.call_count, 2)

    @patch('udocker.container.structure.FileUtil.tar')
    @patch('udocker.container.structure.Msg')
    def test_12_export_tofile(self, mock_msg, mock_futar):
        """Test12 ContainerStructure().export_tofile()."""
        # Empty container dir
        mock_msg.return_value.level.return_value = 0
        self.local.cd_container.return_value = ""
        mock_futar.return_value = False
        prex = ContainerStructure(self.local)
        status = prex.export_tofile("clone_file")
        self.assertFalse(status)

        # Non-empty container dir
        mock_msg.return_value.level.return_value = 0
        self.local.cd_container.return_value = "/ROOT"
        mock_futar.return_value = True
        prex = ContainerStructure(self.local, "123456")
        status = prex.export_tofile("clone_file")
        self.assertEqual(status, "123456")

    @patch('udocker.container.structure.FileUtil.tar')
    @patch('udocker.container.structure.Msg')
    def test_13_clone_tofile(self, mock_msg, mock_futar):
        """Test13 ContainerStructure().clone_tofile()."""
        # Empty container dir
        mock_msg.return_value.level.return_value = 0
        self.local.cd_container.return_value = ""
        mock_futar.return_value = False
        prex = ContainerStructure(self.local)
        status = prex.clone_tofile("clone_file")
        self.assertFalse(status)

        # Non-empty container dir
        mock_msg.return_value.level.return_value = 0
        self.local.cd_container.return_value = "/ROOT"
        mock_futar.return_value = True
        prex = ContainerStructure(self.local, "123456")
        status = prex.clone_tofile("clone_file")
        self.assertEqual(status, "123456")

    @patch.object(ContainerStructure, '_chk_container_root')
    @patch('udocker.container.structure.FileUtil.copydir')
    @patch('udocker.container.structure.Unique.uuid')
    @patch('udocker.container.structure.Msg')
    def test_14_clone(self, mock_msg, mock_uuid,
                      mock_fucpd, mock_chkcont):
        """Test14 ContainerStructure().clone()."""
        # Empty source container_dir
        mock_msg.return_value.level.return_value = 0
        self.local.cd_container.return_value = ""
        mock_uuid.return_value = "123456"
        prex = ContainerStructure(self.local)
        status = prex.clone()
        self.assertFalse(status)

        # Non-empty source container_dir
        mock_msg.return_value.level.return_value = 0
        self.local.cd_container.return_value = "/ROOT/src"
        self.local.setup_container.return_value = "/ROOT/dst"
        mock_uuid.return_value = "123456"
        mock_chkcont.return_value = 3
        mock_fucpd.return_value = False
        prex = ContainerStructure(self.local)
        status = prex.clone()
        self.assertFalse(status)

        mock_msg.return_value.level.return_value = 0
        self.local.cd_container.return_value = "/ROOT/src"
        self.local.setup_container.return_value = "/ROOT/dst"
        mock_uuid.return_value = "123456"
        mock_chkcont.return_value = False
        mock_fucpd.return_value = True
        prex = ContainerStructure(self.local)
        status = prex.clone()
        self.assertEqual(status, "123456")


if __name__ == '__main__':
    main()
