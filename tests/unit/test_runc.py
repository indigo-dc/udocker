#!/usr/bin/env python
"""
udocker unit tests: RuncEngine
"""

from unittest import TestCase, main
from unittest.mock import Mock, patch, mock_open
from udocker.config import Config
from udocker.engine.runc import RuncEngine

BUILTINS = "builtins"
BOPEN = BUILTINS + '.open'


class RuncEngineTestCase(TestCase):
    """Test RuncEngine() containers execution with runC."""

    def setUp(self):
        Config().getconf()
        Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        Config().conf['cmd'] = "/bin/bash"
        Config().conf['cpu_affinity_exec_tools'] = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        Config().conf['runc_capabilities'] = [
            "CAP_KILL", "CAP_NET_BIND_SERVICE", "CAP_CHOWN", "CAP_DAC_OVERRIDE",
            "CAP_FOWNER", "CAP_FSETID", "CAP_KILL", "CAP_SETGID", "CAP_SETUID",
            "CAP_SETPCAP", "CAP_NET_BIND_SERVICE", "CAP_NET_RAW",
            "CAP_SYS_CHROOT", "CAP_MKNOD", "CAP_AUDIT_WRITE", "CAP_SETFCAP",
        ]
        Config().conf['valid_host_env'] = "HOME"
        Config().conf['username'] = "user"
        Config().conf['userhome'] = "/"
        Config().conf['oskernel'] = "4.8.13"
        Config().conf['location'] = ""
        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

        str_exmode = 'udocker.engine.execmode.ExecutionMode'
        self.execmode = patch(str_exmode)
        self.xmode = self.execmode.start()
        self.mock_execmode = Mock()
        self.xmode.return_value = self.mock_execmode

    def tearDown(self):
        self.lrepo.stop()
        self.execmode.stop()

    def test_01_init(self):
        """Test01 RuncEngine() constructor."""
        rcex = RuncEngine(self.local, self.xmode)
        self.assertEqual(rcex.executable, None)
        self.assertEqual(rcex.execution_id, None)

    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.engine.runc.HostInfo.arch')
    @patch('udocker.engine.runc.FileUtil.find_file_in_dir')
    @patch('udocker.engine.runc.FileUtil.find_exec')
    def test_02_select_runc(self, mock_findexe, mock_find,
                            mock_arch, mock_exists):
        """Test02 RuncEngine().select_runc()."""
        Config.conf['use_runc_executable'] = ""
        mock_findexe.return_value = "/bin/runc-arm"
        mock_exists.return_value = True
        rcex = RuncEngine(self.local, self.xmode)
        rcex.select_runc()
        self.assertTrue(mock_findexe.called)

        Config.conf['use_runc_executable'] = "UDOCKER"
        mock_arch.return_value = "amd64"
        mock_find.return_value = "runc-x86_64"
        mock_exists.return_value = True
        rcex = RuncEngine(self.local, self.xmode)
        rcex.select_runc()
        self.assertTrue(mock_arch.called)
        self.assertTrue(mock_find.called)

        Config.conf['use_runc_executable'] = "UDOCKER"
        mock_arch.return_value = "i386"
        mock_find.return_value = "runc-x86"
        mock_exists.return_value = True
        rcex = RuncEngine(self.local, self.xmode)
        rcex.select_runc()
        self.assertTrue(mock_arch.called)
        self.assertTrue(mock_find.called)

    @patch('udocker.engine.runc.json.load')
    @patch('udocker.engine.runc.FileUtil.register_prefix')
    @patch('udocker.engine.runc.FileUtil.remove')
    @patch('udocker.engine.runc.FileUtil.size')
    @patch('udocker.engine.runc.subprocess.call')
    @patch('udocker.engine.runc.os.path.realpath')
    def test_03__load_spec(self, mock_realpath, mock_call, mock_size,
                           mock_rm, mock_reg, mock_jload):
        """Test03 RuncEngine()._load_spec()."""
        mock_size.side_effect = [-1, -1]
        mock_realpath.return_value = "/container/ROOT"
        mock_call.return_value = 1
        mock_rm.return_value = None
        mock_reg.return_value = None
        rcex = RuncEngine(self.local, self.xmode)
        status = rcex._load_spec(False)
        self.assertFalse(mock_rm.called)
        self.assertFalse(mock_reg.called)
        self.assertTrue(mock_call.called)
        self.assertTrue(mock_realpath.called)
        self.assertFalse(status)

        jload = {"container": "cxxx", "parent": "dyyy",
                 "created": "2020-05-05T21:20:07.182447994Z",
                 "os": "linux",
                 "container_config": {"Tty": "false", "Cmd": ["/bin/sh"]},
                 "Image": "sha256:aa"
                }
        mock_size.side_effect = [100, 100]
        mock_realpath.return_value = "/container/ROOT"
        mock_call.return_value = 0
        mock_rm.return_value = None
        mock_reg.return_value = None
        mock_jload.return_value = jload
        with patch(BOPEN, mock_open()) as mopen:
            rcex = RuncEngine(self.local, self.xmode)
            status = rcex._load_spec(True)
            self.assertTrue(mopen.called)
            self.assertEqual(status, jload)
            self.assertTrue(mock_rm.called)
            self.assertTrue(mock_reg.called)

    @patch('udocker.engine.runc.json.dump')
    def test_04__save_spec(self, mock_jdump):
        """Test04 RuncEngine()._save_spec()."""
        jdump = {"container": "cxxx", "parent": "dyyy",
                 "created": "2020-05-05T21:20:07.182447994Z",
                 "os": "linux",
                 "container_config": {"Tty": "false", "Cmd": ["/bin/sh"]},
                 "Image": "sha256:aa"
                }
        mock_jdump.return_value = jdump
        with patch(BOPEN, mock_open()) as mopen:
            rcex = RuncEngine(self.local, self.xmode)
            status = rcex._save_spec()
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @patch('udocker.engine.runc.os.getgid')
    @patch('udocker.engine.runc.os.getuid')
    @patch('udocker.engine.runc.platform.node')
    @patch('udocker.engine.runc.os.path.realpath')
    def test_05__set_spec(self, mock_realpath, mock_node,
                          mock_getuid, mock_getgid):
        """Test05 RuncEngine()._set_spec()."""
        # rcex.opt["hostname"] has nodename
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = []
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = "node.domain"
        json_obj = rcex._set_spec()
        self.assertEqual(json_obj["hostname"], "node.domain")

        # empty rcex.opt["hostname"]
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = []
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertEqual(json_obj["hostname"], "nodename.local")

        # environment passes to container json
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = [("AA", "aa"), ("BB", "bb")]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertIn("AA=aa", json_obj["process"]["env"])

        # environment syntax error
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = [("BB", "bb")]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertNotIn("AA=aa", json_obj["process"]["env"])

        # uid and gid mappings
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        mock_getuid.return_value = 10000
        mock_getgid.return_value = 10000
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex._container_specjson["linux"]["uidMappings"]["XXX"] = 0
        rcex._container_specjson["linux"]["gidMappings"]["XXX"] = 0
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = [("AA", "aa"), ("BB", "bb")]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertFalse(mock_getuid.called)
        self.assertFalse(mock_getgid.called)

    @patch('udocker.engine.runc.Msg')
    def test_06__uid_check(self, mock_msg):
        """Test06 RuncEngine()._uid_check()."""
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex._uid_check()
        self.assertFalse(mock_msg.called)

        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex.opt["user"] = "root"
        rcex._uid_check()
        self.assertFalse(mock_msg.called)

        mock_msg.level = 3
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex.opt["user"] = "user01"
        rcex._uid_check()
        self.assertTrue(mock_msg.called)

    def test_07__add_capabilities_spec(self):
        """Test07 RuncEngine()._add_capabilities_spec()."""
        rcex = RuncEngine(self.local, self.xmode)
        Config.conf['runc_capabilities'] = ""
        self.assertEqual(rcex._add_capabilities_spec(), None)

        rcex = RuncEngine(self.local, self.xmode)
        Config.conf['runc_capabilities'] = ["CAP_KILL",
                                            "CAP_NET_BIND_SERVICE",
                                            "CAP_CHOWN"]
        rcex._container_specjson = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["process"]["capabilities"] = dict()
        rcex._container_specjson["process"]["capabilities"]["ambient"] = dict()
        rcex._add_capabilities_spec()
        res = rcex._container_specjson["process"]["capabilities"]["ambient"]
        self.assertEqual(res, Config.conf['runc_capabilities'])

    @patch('udocker.engine.runc.HostInfo')
    @patch('udocker.engine.runc.os.minor')
    @patch('udocker.engine.runc.os.major')
    @patch('udocker.engine.runc.stat.S_ISCHR')
    @patch('udocker.engine.runc.stat.S_ISBLK')
    @patch('udocker.engine.runc.os.path.exists')
    @patch('udocker.engine.runc.Msg')
    def test_08__add_device_spec(self, mock_msg, mock_exists,
                                 mock_blk, mock_chr, mock_osmaj,
                                 mock_osmin, mock_hi):
        """Test08 RuncEngine()._add_device_spec()."""
        mock_msg.level = 3
        mock_exists.return_value = False
        rcex = RuncEngine(self.local, self.xmode)
        status = rcex._add_device_spec("/dev/zero")
        self.assertTrue(mock_msg.return_value.err.called)
        self.assertFalse(status)

        mock_msg.level = 3
        mock_exists.return_value = True
        mock_blk.return_value = False
        mock_chr.return_value = False
        rcex = RuncEngine(self.local, self.xmode)
        status = rcex._add_device_spec("/dev/zero")
        self.assertTrue(mock_msg.return_value.err.called)
        self.assertFalse(status)

        mock_msg.level = 3
        mock_exists.return_value = True
        mock_blk.return_value = True
        mock_chr.return_value = False
        mock_osmaj.return_value = 0
        mock_osmin.return_value = 6
        mock_hi.uid = 0
        mock_hi.gid = 0
        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["devices"] = list()
        status = rcex._add_device_spec("/dev/zero")
        self.assertTrue(status)
        self.assertTrue(mock_osmaj.called)
        self.assertTrue(mock_osmin.called)

    @patch('udocker.engine.runc.NvidiaMode')
    @patch.object(RuncEngine, '_add_device_spec')
    def test_09__add_devices(self, mock_adddecspec, mock_nv):
        """Test09 RuncEngine()._add_devices()."""
        mock_adddecspec.side_effect = [True, True, True]
        mock_nv.return_value.get_mode.return_value = True
        mock_nv.return_value.get_devices.return_value = ['/dev/nvidia', ]
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex.opt["devices"] = ["/dev/open-mx", "/dev/myri0"]
        rcex._add_devices()
        self.assertTrue(mock_adddecspec.call_count, 3)
        self.assertTrue(mock_nv.return_value.get_mode.called)
        self.assertTrue(mock_nv.return_value.get_devices.called)

    def test_10__add_mount_spec(self):
        """Test10 RuncEngine()._add_mount_spec()."""
        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        rcex._add_mount_spec("/HOSTDIR", "/CONTDIR")
        mount = rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("ro", mount["options"])

        # rw
        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        rcex._add_mount_spec("/HOSTDIR", "/CONTDIR", True)
        mount = rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("rw", mount["options"])

    def test_11__del_mount_spec(self):
        """Test11 RuncEngine()._del_mount_spec()."""
        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "/HOSTDIR",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        # self.assertEqual(len(rcex._container_specjson["mounts"]), 0)

        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/XXXX",
                 "type": "none",
                 "source": "/HOSTDIR",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(rcex._container_specjson["mounts"]), 1)

        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "XXXX",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(rcex._container_specjson["mounts"]), 1)

    def test_12__sel_mount_spec(self):
        """Test12 RuncEngine()._sel_mount_spec()."""
        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "xxx",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        status = rcex._sel_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(status, None)

        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "/HOSTDIR",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        status = rcex._sel_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(status, 0)

    @patch.object(RuncEngine, '_sel_mount_spec')
    def test_13__mod_mount_spec(self, mock_selmount):
        """Test13 RuncEngine()._mod_mount_spec()."""
        optnew = {"options": ["a", "su"]}
        mock_selmount.return_value = None
        rcex = RuncEngine(self.local, self.xmode)
        status = rcex._mod_mount_spec("/HOSTDIR", "/CONTDIR", optnew)
        self.assertFalse(status)

        optnew = {"options": ["a", "su"]}
        mock_selmount.return_value = 0
        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "/HOSTDIR",
                 "options": ["a"], }
        rcex._container_specjson["mounts"].append(mount)
        status = rcex._mod_mount_spec("/HOSTDIR", "/CONTDIR", optnew)
        self.assertTrue(status)
        self.assertEqual(len(rcex._container_specjson["mounts"]), 1)

    @patch('udocker.engine.runc.Msg')
    @patch('udocker.engine.runc.os.path.isfile')
    @patch('udocker.engine.runc.os.path.isdir')
    @patch.object(RuncEngine, '_add_mount_spec')
    @patch('udocker.engine.runc.FileBind')
    def test_14__add_volume_bindings(self, mock_fbind,
                                     mock_add_mount_spec,
                                     mock_isdir, mock_isfile, mock_msg):
        """Test14 RuncEngine()._add_volume_bindings()."""
        mock_msg.level = 0
        mock_add_mount_spec.side_effect = [None, None]
        rcex = RuncEngine(self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        rcex.opt["vol"] = list()
        rcex._add_volume_bindings()
        self.assertTrue(mock_add_mount_spec.called)
        self.assertFalse(mock_isdir.called)

        mock_add_mount_spec.side_effect = [None, None]
        mock_isdir.return_value = False
        mock_isfile.return_value = False
        rcex = RuncEngine(self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        rcex.opt["vol"] = list()
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)

        mock_add_mount_spec.side_effect = [None, None]
        mock_isdir.return_value = True
        mock_isfile.return_value = False
        rcex = RuncEngine(self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        rcex.opt["vol"] = list()
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_add_mount_spec.call_count, 2)

        mock_add_mount_spec.side_effect = [None, None]
        mock_isdir.return_value = False
        mock_isfile.return_value = True
        rcex = RuncEngine(self.local, self.xmode)
        Config.conf['sysdirs_list'] = ["/HOSTDIR"]
        rcex._filebind = mock_fbind
        rcex._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        rcex._filebind.set_file.return_value = None
        rcex._filebind.add_file.return_value = None
        rcex.opt["vol"] = list()
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_add_mount_spec.call_count, 1)
        self.assertTrue(rcex._filebind.set_file.called)
        self.assertTrue(rcex._filebind.add_file.called)

    @patch('udocker.engine.runc.Msg')
    def test_15__run_invalid_options(self, mock_msg):
        """Test15 RuncEngine()._run_invalid_options()."""
        mock_msg.level = 0
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt['netcoop'] = False
        rcex.opt['portsmap'] = True
        rcex._run_invalid_options()
        self.assertTrue(mock_msg.called)

    @patch.object(RuncEngine, '_create_mountpoint')
    @patch('udocker.engine.runc.stat')
    @patch('udocker.engine.runc.FileUtil.chmod')
    @patch('udocker.engine.runc.FileBind')
    @patch('udocker.engine.runc.os.path.basename')
    @patch('udocker.engine.runc.PRootEngine')
    def test_16__proot_overlay(self, mock_proot, mock_base, mock_fbind,
                               mock_chmod, mock_stat, mock_crmpoint):
        """Test16 RuncEngine()._proot_overlay()."""
        self.xmode.get_mode.return_value = "R1"
        rcex = RuncEngine(self.local, self.xmode)
        status = rcex._proot_overlay("P2")
        self.assertFalse(status)

        self.xmode.get_mode.return_value = "R2"
        mock_proot.return_value.select_proot.return_value = None
        mock_base.return_value = "ls"
        mock_chmod.return_value = None
        mock_crmpoint.return_value = True
        mock_stat.return_value.S_IRUSR = 256
        mock_stat.return_value.S_IWUSR = 128
        mock_stat.return_value.S_IXUSR = 64
        rcex = RuncEngine(self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        rcex._filebind.set_file.return_value = None
        rcex._filebind.add_file.return_value = None
        rcex._container_specjson = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["process"]["env"] = []
        rcex._container_specjson["process"]["args"] = []
        status = rcex._proot_overlay("P2")
        self.assertTrue(status)
        self.assertTrue(mock_base.called)
        self.assertTrue(mock_chmod.called)
        self.assertTrue(mock_crmpoint.called)
        self.assertTrue(rcex._filebind.set_file.called)
        self.assertTrue(rcex._filebind.add_file.called)

    @patch('udocker.engine.runc.FileBind')
    @patch('udocker.engine.runc.Unique')
    @patch.object(RuncEngine, '_set_id_mappings')
    @patch.object(RuncEngine, '_del_namespace_spec')
    @patch.object(RuncEngine, '_del_mount_spec')
    @patch.object(RuncEngine, 'run_nopty')
    @patch.object(RuncEngine, 'run_pty')
    @patch.object(RuncEngine, '_run_invalid_options')
    @patch.object(RuncEngine, '_del_mount_spec')
    @patch.object(RuncEngine, '_run_banner')
    @patch.object(RuncEngine, '_add_devices')
    @patch.object(RuncEngine, '_add_volume_bindings')
    @patch.object(RuncEngine, '_set_spec')
    @patch.object(RuncEngine, '_save_spec')
    @patch.object(RuncEngine, '_proot_overlay')
    @patch.object(RuncEngine, '_run_env_set')
    @patch.object(RuncEngine, '_mod_mount_spec')
    @patch.object(RuncEngine, '_add_capabilities_spec')
    @patch.object(RuncEngine, '_uid_check')
    @patch.object(RuncEngine, '_run_env_cleanup_list')
    @patch.object(RuncEngine, '_load_spec')
    @patch.object(RuncEngine, 'select_runc')
    @patch.object(RuncEngine, '_run_init')
    def test_17_run(self, mock_run_init, mock_sel_runc,
                    mock_load_spec, mock_run_env_cleanup_list,
                    mock_uid_check, mock_addspecs, mock_modms,
                    mock_env_set, mock_prooto, mock_savespec,
                    mock_set_spec, mock_add_bindings, mock_add_dev,
                    mock_run_banner, mock_del_mount_spec, mock_inv_opt,
                    mock_pty, mock_nopty, mock_delmnt, mock_delns,
                    mock_setid,
                    mock_unique, mock_fbind):
        """Test17 RuncEngine().run()."""
        mock_run_init.return_value = False
        mock_delmnt.return_value = None
        mock_delns.return_value = None
        mock_setid.return_value = None
        mock_env_set.return_value = None
        rcex = RuncEngine(self.local, self.xmode)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 2)

        mock_run_init.return_value = True
        mock_inv_opt.return_value = None
        mock_load_spec.return_value = False
        mock_sel_runc.return_value = None
        mock_load_spec.return_value = False
        mock_delmnt.return_value = None
        mock_delns.return_value = None
        mock_setid.return_value = None
        rcex = RuncEngine(self.local, self.xmode)
        rcex.container_dir = "/container/ROOT"
        rcex._filebind = mock_fbind
        rcex._filebind.setup.return_value = None
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 4)

        jload = {"container": "cxxx", "parent": "dyyy",
                 "created": "2020-05-05T21:20:07.182447994Z",
                 "os": "linux",
                 "container_config": {"Tty": "false", "Cmd": ["/bin/sh"]},
                 "Image": "sha256:aa"
                }
        mock_run_init.return_value = True
        mock_inv_opt.return_value = None
        mock_load_spec.return_value = False
        mock_sel_runc.return_value = None
        mock_load_spec.return_value = jload
        mock_uid_check.return_value = None
        mock_run_env_cleanup_list.return_value = None
        mock_set_spec.return_value = None
        mock_del_mount_spec.return_value = None
        mock_add_bindings.return_value = None
        mock_add_dev.return_value = None
        mock_addspecs.return_value = None
        mock_modms.return_value = None
        mock_prooto.return_value = None
        mock_savespec.return_value = None
        mock_unique.return_value.uuid.return_value = "EXECUTION_ID"
        mock_run_banner.return_value = None
        mock_pty.return_value = 0
        mock_nopty.return_value = 0
        mock_delmnt.return_value = None
        mock_delns.return_value = None
        mock_setid.return_value = None
        rcex = RuncEngine(self.local, self.xmode)
        rcex.container_dir = "/container/ROOT"
        rcex._filebind = mock_fbind
        rcex._filebind.setup.return_value = None
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 0)

    @patch('udocker.engine.runc.FileBind')
    @patch('udocker.engine.runc.subprocess.call')
    def test_18_run_pty(self, mock_call, mock_fbind):
        """Test18 RuncEngine().run_pty()."""
        mock_call.return_value = 0
        rcex = RuncEngine(self.local, self.xmode)
        rcex.container_dir = "/container/ROOT"
        rcex._filebind = mock_fbind
        rcex._filebind.finish.return_value = None
        status = rcex.run_pty("CONTAINERID")
        self.assertEqual(status, 0)

    # def test_19_run_nopty(self):
    #     """Test19 RuncEngine().run_nopty()."""
    #     pass


if __name__ == '__main__':
    main()
