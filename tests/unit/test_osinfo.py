#!/usr/bin/env python
"""
udocker unit tests: OSInfo
"""

from unittest import TestCase, main
from unittest.mock import patch
from udocker.helper.osinfo import OSInfo
from udocker.config import Config


class GuestInfoTestCase(TestCase):
    """Test OSInfo() class."""

    def setUp(self):
        Config().getconf()
        self.rootdir = "~/.udocker/container/abcd0/ROOT"
        self.file = "/bin/ls"
        self.noosdist = ("", "xx")

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test01 OSInfo() constructor."""
        ginfo = OSInfo(self.rootdir)
        self.assertIsInstance(ginfo._binarylist, list)

    @patch('udocker.helper.osinfo.Uprocess.get_output')
    @patch('udocker.helper.osinfo.os.path.isfile')
    def test_02_get_filetype(self, mock_isfile, mock_getout):
        """Test02 OSInfo.get_filetype(filename)"""
        # full filepath exists
        ftype = "/bin/ls: yyy, x86-64, xxx"
        mock_isfile.return_value = True
        mock_getout.return_value = ftype
        ginfo = OSInfo(self.rootdir)
        status = ginfo.get_filetype(self.file)
        self.assertEqual(status, ftype)

        # file does not exist
        nofile = "ddd: cannot open"
        mock_isfile.return_value = False
        mock_getout.return_value = nofile
        ginfo = OSInfo(self.rootdir)
        status = ginfo.get_filetype(nofile)
        self.assertEqual(status, "")

    @patch.object(OSInfo, 'get_filetype')
    def test_03_arch(self, mock_getftype):
        """Test03 OSInfo.arch()"""
        # arch is x86_64
        ftype = "/bin/ls: yyy, x86-64, xxx"
        mock_getftype.return_value = ftype
        ginfo = OSInfo(self.rootdir)
        status = ginfo.arch()
        self.assertEqual(status, "amd64")

        # arch is i386
        ftype = "/bin/ls: yyy, Intel 80386, xxx"
        mock_getftype.return_value = ftype
        ginfo = OSInfo(self.rootdir)
        status = ginfo.arch()
        self.assertEqual(status, "i386")

        # arch is arm 64
        ftype = "/bin/ls: yyy, aarch64"
        mock_getftype.return_value = ftype
        ginfo = OSInfo(self.rootdir)
        status = ginfo.arch()
        self.assertEqual(status, "arm64")

        # arch is arm
        ftype = "/bin/ls: yyy, ARM, xxx"
        mock_getftype.return_value = ftype
        ginfo = OSInfo(self.rootdir)
        status = ginfo.arch()
        self.assertEqual(status, "arm")

    @patch('udocker.helper.osinfo.os.path.exists')
    @patch('udocker.helper.osinfo.FileUtil.match')
    @patch('udocker.helper.osinfo.FileUtil.getdata')
    def test_04_osdistribution(self, mock_gdata, mock_match, mock_exists):
        """Test04 OSInfo.osdistribution()"""
        lsbdata = "DISTRIB_ID=Ubuntu\n" \
                  "DISTRIB_RELEASE=16.04\n" \
                  "DISTRIB_CODENAME=xenial\n" \
                  "DISTRIB_DESCRIPTION=Ubuntu 16.04.5 LTS\n"
        mock_match.return_value = ["/etc/lsb-release"]
        osdist = ("Ubuntu", "16")
        mock_exists.return_value = True
        mock_gdata.return_value = lsbdata
        ginfo = OSInfo(self.rootdir)
        status = ginfo.osdistribution()
        self.assertEqual(status, osdist)

        reldata = "CentOS release 6.10 (Final)"
        mock_match.return_value = ["/etc/centos-release"]
        osdist = ("CentOS", "6")
        mock_exists.return_value = True
        mock_gdata.return_value = reldata
        ginfo = OSInfo(self.rootdir)
        status = ginfo.osdistribution()
        self.assertEqual(status, osdist)

    @patch.object(OSInfo, 'osdistribution')
    def test_05_osversion(self, mock_osdist):
        """Test05 OSInfo.osversion()"""
        # has osdistro
        osdist = ("Ubuntu", "16.04")
        mock_osdist.return_value = osdist
        ginfo = OSInfo(self.rootdir)
        status = ginfo.osversion()
        self.assertEqual(status, "linux")

        # has no osdistro
        mock_osdist.return_value = self.noosdist
        ginfo = OSInfo(self.rootdir)
        status = ginfo.osversion()
        self.assertEqual(status, "")


if __name__ == '__main__':
    main()
