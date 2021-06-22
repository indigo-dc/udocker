#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: HostInfo
"""

import pwd
from unittest import TestCase, main
from unittest.mock import patch
from udocker.helper.hostinfo import HostInfo


class HostInfoTestCase(TestCase):
    """Test HostInfo"""

    @patch('udocker.helper.hostinfo.os.getgid')
    @patch('udocker.helper.hostinfo.os.getuid')
    @patch('udocker.helper.hostinfo.pwd.getpwuid')
    def test_01_username(self, mock_getpwuid, mock_uid, mock_gid):
        """Test01 HostInfo().username."""
        usr = pwd.struct_passwd(["root", "*", "0", "0", "root usr",
                                 "/root", "/bin/bash"])
        mock_uid.return_value = 0
        mock_gid.return_value = 0
        mock_getpwuid.return_value = usr
        name = HostInfo().username()
        self.assertEqual(name, usr.pw_name)

    @patch('udocker.helper.hostinfo.platform.architecture')
    @patch('udocker.helper.hostinfo.platform.machine')
    def test_02_arch(self, mock_mach, mock_arch):
        """Test02 HostInfo().arch."""
        mock_mach.return_value = "x86_64"
        mock_arch.return_value = ('64bit', '')
        result = HostInfo().arch()
        self.assertEqual(result, "amd64")

        mock_mach.return_value = "x86_64"
        mock_arch.return_value = ('32bit', '')
        result = HostInfo().arch()
        self.assertEqual(result, "i386")

        mock_mach.return_value = "arm"
        mock_arch.return_value = ('64bit', '')
        result = HostInfo().arch()
        self.assertEqual(result, "arm64")

        mock_mach.return_value = "arm"
        mock_arch.return_value = ('32bit', '')
        result = HostInfo().arch()
        self.assertEqual(result, "arm")

    @patch('udocker.helper.hostinfo.platform.system')
    def test_03_osversion(self, mock_sys):
        """Test03 HostInfo().osversion."""
        mock_sys.return_value = "linux"
        result = HostInfo().osversion()
        self.assertEqual(result, "linux")

    @patch('udocker.helper.hostinfo.platform.release')
    def test_04_oskernel(self, mock_rel):
        """Test04 HostInfo().oskernel."""
        mock_rel.return_value = "3.2.1"
        result = HostInfo().oskernel()
        self.assertEqual(result, "3.2.1")

    @patch.object(HostInfo, 'oskernel')
    def test_05_oskernel_isgreater(self, mock_kernel):
        """Test05 HostInfo().oskernel_isgreater."""
        mock_kernel.return_value = "1.1.2-"
        status = HostInfo().oskernel_isgreater([1, 1, 1])
        self.assertTrue(status)

        mock_kernel.return_value = "1.2.1-"
        status = HostInfo().oskernel_isgreater([1, 1, 1])
        self.assertTrue(status)

        mock_kernel.return_value = "1.0.0-"
        status = HostInfo().oskernel_isgreater([1, 1, 1])
        self.assertFalse(status)

    def test_06_cmd_has_option(self):
        """Test06 HostInfo().cmd_has_option."""
        status = HostInfo().cmd_has_option("ls", "-a")
        self.assertTrue(status)

        status = HostInfo().cmd_has_option("ls", "-z")
        self.assertFalse(status)

    @patch('udocker.helper.hostinfo.Uprocess.check_output')
    def test_07_termsize(self, mock_chkout):
        """Test07 HostInfo().termsize."""
        mock_chkout.return_value = "24 80"
        status = HostInfo().termsize()
        self.assertEqual(status, (24, 80))


if __name__ == '__main__':
    main()
