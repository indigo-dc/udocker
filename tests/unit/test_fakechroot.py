#!/usr/bin/env python
"""
udocker unit tests: FakechrootEngine
"""

from unittest import TestCase, main
from unittest.mock import patch, Mock
from udocker.config import Config
from udocker.engine.fakechroot import FakechrootEngine


class FakechrootEngineTestCase(TestCase):
    """Docker container execution engine using Fakechroot
    Provides a chroot like environment to run containers.
    Uses Fakechroot as chroot alternative.
    Inherits from ContainerEngine class
    """

    def setUp(self):
        Config().getconf()
        Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        Config().conf['cmd'] = "/bin/bash"
        Config().conf['cpu_affinity_exec_tools'] = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
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

    def test_01__init(self):
        """Test01 FakechrootEngine Constructor."""
        ufake = FakechrootEngine(self.local, self.xmode)
        self.assertEqual(ufake._fakechroot_so, "")
        self.assertIsNone(ufake._elfpatcher)

    @patch('udocker.engine.fakechroot.Msg')
    @patch('udocker.engine.fakechroot.sys.exit')
    @patch('udocker.engine.fakechroot.OSInfo')
    @patch('udocker.engine.fakechroot.os.path.realpath')
    @patch('udocker.engine.fakechroot.os.path.exists')
    @patch('udocker.engine.fakechroot.FileUtil')
    def test_02_select_fakechroot_so(self, mock_futil, mock_exists,
                                     mock_rpath, mock_osinfo, mock_sysex, mock_msg):
        """Test02 FakechrootEngine.select_fakechroot_so."""
        Config().conf['fakechroot_so'] = "/s/fake1"
        mock_msg.level = 0
        mock_exists.return_value = True
        mock_rpath.return_value = "/s/fake1"
        ufake = FakechrootEngine(self.local, self.xmode)
        out = ufake.select_fakechroot_so()
        self.assertEqual(out, "/s/fake1")

        Config().conf['fakechroot_so'] = ""
        mock_exists.return_value = True
        ufake = FakechrootEngine(self.local, self.xmode)
        out = ufake.select_fakechroot_so()
        self.assertEqual(out, "/libfakechroot.so")

        Config().conf['fakechroot_so'] = ""
        mock_exists.return_value = False
        mock_osinfo.return_value.arch.return_value = "amd64"
        mock_osinfo.return_value.osdistribution.return_value = \
            ("linux", "4.8.1")
        mock_futil.return_value.find_file_in_dir.return_value = ""
        mock_sysex.return_value = 1
        ufake = FakechrootEngine(self.local, self.xmode)
        out = ufake.select_fakechroot_so()
        self.assertTrue(mock_sysex.called)
        self.assertTrue(mock_futil.called)

        Config().conf['fakechroot_so'] = ""
        mock_exists.return_value = False
        mock_osinfo.return_value.arch.return_value = "amd64"
        mock_osinfo.return_value.osdistribution.return_value = \
            ("linux", "4.8.1")
        mock_futil.return_value.find_file_in_dir.return_value = \
            "/libfakechroot.so"
        ufake = FakechrootEngine(self.local, self.xmode)
        out = ufake.select_fakechroot_so()
        self.assertTrue(mock_futil.called)
        self.assertEqual(out, "/libfakechroot.so")

        Config().conf['fakechroot_so'] = ""
        mock_exists.return_value = False
        mock_osinfo.return_value.arch.return_value = "i386"
        mock_osinfo.return_value.osdistribution.return_value = \
            ("linux", "4.8.1")
        mock_futil.return_value.find_file_in_dir.return_value = \
            "/libfakechroot.so"
        ufake = FakechrootEngine(self.local, self.xmode)
        out = ufake.select_fakechroot_so()
        self.assertTrue(mock_futil.called)
        self.assertEqual(out, "/libfakechroot.so")

        Config().conf['fakechroot_so'] = ""
        mock_exists.return_value = False
        mock_osinfo.return_value.arch.return_value = "arm64"
        mock_osinfo.return_value.osdistribution.return_value = \
            ("linux", "4.8.1")
        mock_futil.return_value.find_file_in_dir.return_value = \
            "/libfakechroot.so"
        ufake = FakechrootEngine(self.local, self.xmode)
        out = ufake.select_fakechroot_so()
        self.assertTrue(mock_futil.called)
        self.assertEqual(out, "/libfakechroot.so")

    @patch('udocker.engine.fakechroot.ExecutionEngineCommon._setup_container_user_noroot')
    def test_03__setup_container_user(self, mock_cmm):
        """Test03 FakechrootEngine._setup_container_user()."""
        mock_cmm.return_value = True
        ufake = FakechrootEngine(self.local, self.xmode)
        status = ufake._setup_container_user("someuser")
        self.assertTrue(mock_cmm.called)
        self.assertTrue(status)

    @patch('udocker.engine.fakechroot.Msg')
    def test_04__uid_check(self, mock_msg):
        """Test04 FakechrootEngine._uid_check()."""
        mock_msg.level = 3
        ufake = FakechrootEngine(self.local, self.xmode)
        ufake.opt["user"] = "0"
        ufake._uid_check()
        self.assertTrue(mock_msg.return_value.out.called)

    def test_05__get_volume_bindings(self):
        """Test05 FakechrootEngine._get_volume_bindings()."""
        ufake = FakechrootEngine(self.local, self.xmode)
        ufake.opt["vol"] = ()
        status = ufake._get_volume_bindings()
        self.assertEqual(status, ('', ''))

        ufake = FakechrootEngine(self.local, self.xmode)
        ufake.opt["vol"] = ("/tmp", "/bin",)
        status = ufake._get_volume_bindings()
        self.assertEqual(status, ('', '/tmp!/tmp:/bin!/bin'))

    @patch('udocker.engine.fakechroot.os.path.exists')
    @patch('udocker.engine.fakechroot.FileUtil.cont2host')
    def test_06__get_access_filesok(self, mock_cont2host, mock_exists):
        """Test06 FakechrootEngine._get_access_filesok()."""
        Config.conf['access_files'] = ("/sys/infin",)
        mock_cont2host.return_value = "/c/sys/infin"
        mock_exists.return_value = False
        ufake = FakechrootEngine(self.local, self.xmode)
        out = ufake._get_access_filesok()
        self.assertEqual(out, "")

        Config.conf['access_files'] = ("/sys/infin",)
        mock_cont2host.return_value = "/c/sys/infin"
        mock_exists.return_value = True
        ufake = FakechrootEngine(self.local, self.xmode)
        ufake.opt["vol"] = ("/tmp",)
        out = ufake._get_access_filesok()
        self.assertTrue(mock_cont2host.called)
        self.assertTrue(mock_exists.called)
        self.assertEqual(out, "/sys/infin")

    @patch.object(FakechrootEngine, '_get_volume_bindings')
    @patch.object(FakechrootEngine, 'select_fakechroot_so')
    @patch.object(FakechrootEngine, '_get_access_filesok')
    @patch.object(FakechrootEngine, '_is_volume')
    @patch('udocker.engine.fakechroot.os.path.realpath')
    @patch('udocker.engine.fakechroot.ElfPatcher')
    @patch('udocker.engine.fakechroot.FileUtil')
    def test_07__fakechroot_env_set(self, mock_futil, mock_elf,
                                    mock_rpath, mock_isvol, mock_fok, mock_sel,
                                    mock_getvol):
        """Test07 FakechrootEngine._fakechroot_env_set()."""
        Config.conf['fakechroot_expand_symlinks'] = None
        mock_getvol.return_value = ('v1:v2', 'm1:m2')
        mock_sel.return_value = '/ROOT/lib/libfakechroot.so'
        mock_fok.return_value = "/sys/infin"
        mock_rpath.return_value = '/bin/fake.so'
        mock_elf.return_value.get_ld_library_path.return_value = '/a'
        mock_elf.return_value.get_container_loader.return_value = '/ROOT/elf'
        mock_futil.return_value.find_file_in_dir.return_value = True
        mock_isvol.return_value = False
        self.xmode.get_mode.return_value = 'F1'
        ufake = FakechrootEngine(self.local, self.xmode)
        ufake._elfpatcher = mock_elf
        ufake._fakechroot_env_set()
        self.assertTrue(self.xmode.get_mode.called)
        self.assertTrue(mock_getvol.called)
        self.assertTrue(mock_sel.called)
        self.assertTrue(mock_fok.called)
        self.assertTrue(mock_rpath.called)
        self.assertTrue(mock_isvol.called)

        Config.conf['fakechroot_expand_symlinks'] = None
        mock_getvol.return_value = ('v1:v2', 'm1:m2')
        mock_sel.return_value = '/ROOT/lib/libfakechroot.so'
        mock_fok.return_value = "/sys/infin"
        mock_rpath.return_value = '/bin/fake.so'
        mock_elf.return_value.get_ld_library_path.return_value = '/a'
        mock_elf.return_value.select_patchelf.return_value = '/ROOT/elf'
        mock_elf.return_value.get_patch_last_time.return_value = '/ROOT/elf'
        mock_elf.return_value.get_container_loader.return_value = '/ROOT/elf'
        mock_futil.return_value.find_file_in_dir.return_value = True
        mock_isvol.return_value = False
        self.xmode.get_mode.return_value = 'F4'
        ufake = FakechrootEngine(self.local, self.xmode)
        ufake._elfpatcher = mock_elf
        ufake._fakechroot_env_set()
        self.assertTrue(mock_getvol.called)
        self.assertTrue(mock_sel.called)
        self.assertTrue(mock_fok.called)
        self.assertTrue(mock_rpath.called)
        self.assertTrue(mock_isvol.called)

    @patch('udocker.engine.fakechroot.Msg')
    def test_08__run_invalid_options(self, mock_msg):
        """Test08 FakechrootEngine._run_invalid_options()"""
        mock_msg.level = 5
        ufake = FakechrootEngine(self.local, self.xmode)
        ufake.opt['netcoop'] = False
        ufake.opt['portsmap'] = True
        ufake._run_invalid_options()
        self.assertTrue(mock_msg.called)

    @patch('udocker.engine.fakechroot.FileUtil.get1stline')
    @patch('udocker.engine.fakechroot.FileUtil.cont2host')
    @patch('udocker.engine.fakechroot.FileUtil.find_exec')
    @patch('udocker.engine.fakechroot.OSInfo.get_filetype')
    @patch('udocker.engine.fakechroot.Msg')
    def test_09__run_add_script_support(self, mock_msg, mock_ftype,
                                        mock_findexe, mock_cont2host,
                                        mock_1stline):
        """Test09 FakechrootEngine._run_add_script_support()"""
        mock_msg.level = 3
        mock_ftype.return_value = "/bin/ls: ELF, x86-64, static"
        ufake = FakechrootEngine(self.local, self.xmode)
        status = ufake._run_add_script_support("/bin/ls")
        self.assertEqual(status, [])

        mock_msg.level = 3
        mock_ftype.return_value = "/bin/ls: xxx, x86-64, yyy"
        mock_findexe.side_effect = ["ls", ""]
        ufake = FakechrootEngine(self.local, self.xmode)
        status = ufake._run_add_script_support("/bin/ls")
        self.assertEqual(status, ["/ls"])

        mock_msg.level = 3
        mock_ftype.return_value = "/bin/ls: xxx, x86-64, yyy"
        mock_findexe.side_effect = ["", "ls"]
        mock_cont2host.return_value = "/bin/ls"
        mock_1stline.return_value = ""
        ufake = FakechrootEngine(self.local, self.xmode)
        ufake.container_root = "/ROOT"
        status = ufake._run_add_script_support("/bin/ls")
        self.assertEqual(status, ["/ROOT/ls"])

    @patch('udocker.engine.fakechroot.FileUtil.cont2host')
    @patch.object(FakechrootEngine, '_run_banner')
    @patch.object(FakechrootEngine, '_run_add_script_support')
    @patch.object(FakechrootEngine, '_set_cpu_affinity')
    @patch.object(FakechrootEngine, '_run_env_cleanup_list')
    @patch.object(FakechrootEngine, '_fakechroot_env_set')
    @patch.object(FakechrootEngine, '_run_env_set')
    @patch.object(FakechrootEngine, '_run_invalid_options')
    @patch.object(FakechrootEngine, '_run_init')
    @patch.object(FakechrootEngine, '_uid_check')
    @patch('udocker.engine.fakechroot.subprocess.call')
    @patch('udocker.engine.fakechroot.ElfPatcher')
    @patch('udocker.engine.fakechroot.Msg')
    def test_10_run(self, mock_msg, mock_elfp, mock_call, mock_uidc,
                    mock_rinit, mock_rinval, mock_renv, mock_fakeenv,
                    mock_renvclean, mock_setaff, mock_raddsup,
                    mock_runban, mock_cont2host):
        """Test10 FakechrootEngine.run()."""
        mock_uidc.return_value = None
        mock_rinit.return_value = ""
        ufake = FakechrootEngine(self.local, self.xmode)
        status = ufake.run("12345")
        self.assertEqual(status, 2)


        mock_uidc.return_value = None
        mock_rinit.return_value = '/bin/exec'
        mock_rinval.return_value = None
        self.xmode.get_mode.return_value = 'F1'
        mock_elfp.return_value.check_container_path.return_value = False
        mock_renv.return_value = None
        mock_fakeenv.return_value = None
        mock_renvclean.return_value = None
        mock_setaff.return_value = ['1', '2']
        mock_elfp.return_value.get_container_loader.return_value = '/ROOT/xx'
        mock_raddsup.return_value = ['/ROOT/xx.sh']
        mock_runban.return_value = None
        mock_cont2host.return_value = "/cont/ROOT"
        mock_call.return_value = 0
        ufake = FakechrootEngine(self.local, self.xmode)
        status = ufake.run("12345")
        self.assertEqual(status, 0)
        self.assertTrue(mock_uidc.called)
        self.assertTrue(mock_rinit.called)
        self.assertTrue(mock_msg.called)
        self.assertTrue(mock_call.called)


if __name__ == '__main__':
    main()
