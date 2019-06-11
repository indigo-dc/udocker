#!/usr/bin/env python
"""
udocker unit tests: FakechrootEngine
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

sys.path.append('.')

from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.engine.fakechroot import FakechrootEngine


class FakechrootEngineTestCase(TestCase):
    """Docker container execution engine using Fakechroot
    Provides a chroot like environment to run containers.
    Uses Fakechroot as chroot alternative.
    Inherits from ContainerEngine class
    """

    def setUp(self):
        self.conf = Config().getconf()
        self.conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        self.conf['cmd'] = "/bin/bash"
        self.conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                                ["taskset", "-c", "%s", ])
        self.conf['valid_host_env'] = "HOME"
        self.conf['username'] = "user"
        self.conf['userhome'] = "/"
        self.conf['oskernel'] = "4.8.13"
        self.conf['location'] = ""

        self.local = LocalRepository(self.conf)
        self.xmode = "F1"

    def tearDown(self):
        pass

    def test_01__init(self):
        """Test FakechrootEngine Constructor."""
        ufake = FakechrootEngine(self.conf, self.local, self.xmode)
        self.assertEqual(ufake._fakechroot_so, "")
        self.assertIsNone(ufake._elfpatcher)

    # TODO: implement more tests/options
    @patch('udocker.engine.fakechroot.GuestInfo')
    @patch('udocker.engine.fakechroot.Msg.err')
    @patch('udocker.engine.fakechroot.os.path')
    @patch('udocker.engine.fakechroot.FileUtil')
    def test_02__select_fakechroot_so(self, mock_futil, mock_path,
                                      mock_msgerr, mock_guest):
        """Select fakechroot sharable object library."""
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.realpath.return_value = '/bin/xxx'
        mock_futil.return_value.find_file_in_dir.return_value = 'fake1'
        self.conf['fakechroot_so'] = ['/s/fake1', '/s/fake2']
        ufake = FakechrootEngine(self.conf, self.local, self.xmode)
        out = ufake._select_fakechroot_so()
        self.assertTrue(mock_msgerr.called)
        self.assertEqual(out, 'fake1')

    @patch('udocker.engine.fakechroot.ExecutionEngineCommon._setup_container_user_noroot')
    def test_03__setup_container_user(self, mock_cmm):
        """ Override method ExecutionEngineCommon._setup_container_user()."""
        mock_cmm.return_value = True
        ufake = FakechrootEngine(self.conf, self.local, self.xmode)
        status = ufake._setup_container_user("lalves")
        self.assertTrue(status)

    def test_04__get_volume_bindings(self):
        """Get the volume bindings string for fakechroot run."""
        ufake = FakechrootEngine(self.conf, self.local, self.xmode)
        out = ufake._get_volume_bindings()
        self.assertEqual(out, ("", ""))

    def test_05__get_access_filesok(self):
        """Circumvent mpi init issues when calling access().
        A list of certain existing files is provided
        """
        ufake = FakechrootEngine(self.conf, self.local, self.xmode)
        out = ufake._get_access_filesok()
        self.assertEqual(out, "")

    # TODO: implement WIP
    @patch.object(FakechrootEngine, '_get_volume_bindings')
    @patch.object(FakechrootEngine, '_select_fakechroot_so')
    @patch.object(FakechrootEngine, '_get_access_filesok')
    @patch.object(FakechrootEngine, '_is_volume')
    @patch('udocker.engine.fakechroot.os.path.realpath')
    @patch('udocker.engine.fakechroot.ElfPatcher.select_patchelf')
    @patch('udocker.engine.fakechroot.ElfPatcher.get_container_loader')
    @patch('udocker.engine.fakechroot.ElfPatcher.get_ld_library_path')
    @patch('udocker.engine.fakechroot.FileUtil')
    @patch('udocker.engine.fakechroot.Msg')
    def test_06__fakechroot_env_set(self, mock_msg, mock_futil, mock_elfldp,
                                    mock_elfload, mock_elfsel,
                                    mock_rpath, mock_isvol, mock_fok, mock_sel,
                                    mock_getvol):
        """fakechroot environment variables to set."""
        mock_getvol.return_value = ('v1:v2', 'm1:m2:m3')
        mock_sel.return_value = '/ROOT/lib/libfakechroot.so'
        mock_fok.return_value = 'a:b:c'
        mock_rpath.return_value = '/bin/fake.so'
        mock_elfldp.return_value = '/a:/b:/c'
        mock_elfload.return_value = '/ROOT/elf'
        mock_elfsel.return_value = '/bin/pelf'
        mock_futil.return_value.find_file_in_dir.return_value = True
        mock_isvol.return_value = True
        self.xmode = 'F1'
        # ufake = FakechrootEngine(self.conf, self.local, self.xmode)
        # ufake._fakechroot_env_set()
        # self.assertTrue(mock_eecom.return_value.exec_mode.called)

    def test_08__run_invalid_options(self):
        """FakechrootEngine._run_invalid_options()"""
        pass

    def test_09__run_add_script_support(self):
        """FakechrootEngine._run_add_script_support()"""
        pass

    # TODO: missing more tests/options here
    @patch.object(FakechrootEngine, '_cont2host')
    @patch.object(FakechrootEngine, '_run_banner')
    @patch.object(FakechrootEngine, '_run_add_script_support')
    @patch.object(FakechrootEngine, '_set_cpu_affinity')
    @patch.object(FakechrootEngine, '_run_env_cleanup_list')
    @patch.object(FakechrootEngine, '_check_env')
    @patch.object(FakechrootEngine, '_fakechroot_env_set')
    @patch.object(FakechrootEngine, '_run_env_set')
    @patch.object(FakechrootEngine, '_run_invalid_options')
    @patch.object(FakechrootEngine, '_run_init')
    @patch.object(FakechrootEngine, '_uid_check_noroot')
    @patch('udocker.engine.fakechroot.subprocess.call')
    @patch('udocker.engine.fakechroot.ElfPatcher')
    @patch('udocker.engine.fakechroot.Msg')
    def test_10_run(self, mock_msg, mock_elfp, mock_subp, mock_uidchk,
                    mock_rinit, mock_rinval, mock_renv, mock_fakeenv,
                    mock_chkenv, mock_renvclean, mock_setaff, mock_raddsup,
                    mock_rbanner, mock_c2host):
        """Execute a Docker container using Fakechroot.
        This is the main
        method invoked to run the a container with Fakechroot.
          * argument: container_id or name
          * options:  many via self.opt see the help
        """
        mock_rinit.return_value = '/bin/exec'
        mock_elfp.return_value.check_container_path.return_value = True
        mock_chkenv.return_value = True
        mock_setaff.return_value = ['1', '2']
        mock_elfp.return_value.get_container_loader.return_value = '/ROOT/xx'
        mock_raddsup.return_value = ['/ROOT/xx.sh']
        mock_c2host.return_value = '/yy/xx'
        mock_subp.return_value = 0
        ufake = FakechrootEngine(self.conf, self.local, self.xmode)
        status = ufake.run("container_id")
        self.assertEqual(status, 0)


if __name__ == '__main__':
    main()
