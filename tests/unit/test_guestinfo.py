#!/usr/bin/env python
"""
udocker unit tests: GuestInfo
"""
import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')

from udocker.helper.guestinfo import GuestInfo
from udocker.config import Config


class GuestInfoTestCase(TestCase):
    """Test GuestInfo() class."""

    def setUp(self):
        self.conf = Config().getconf()
        self.rootdir = "~/.udocker/container/abcd0/ROOT"
        self.file = "/bin/ls"
        self.noosdist = ("", "xx")

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test GuestInfo() constructor."""
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.root_dir
        self.assertEqual(status, self.rootdir)
        self.assertIsInstance(ginfo.binarylist, list)

    @patch('udocker.helper.guestinfo.Uprocess.get_output')
    @patch('udocker.helper.guestinfo.os.path.isfile')
    def test_02_get_filetype(self, mock_isfile, mock_getout):
        """Test GuestInfo.get_filetype(filename)"""
        # full filepath exists
        ftype = "/bin/ls: yyy, x86-64, xxx"
        mock_isfile.return_value = True
        mock_getout.return_value = ftype
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.get_filetype(self.file)
        self.assertEqual(status, ftype)

        # file does not exist
        nofile = "ddd: cannot open"
        mock_isfile.return_value = False
        mock_getout.return_value = nofile
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.get_filetype(nofile)
        self.assertEqual(status, "")

    @patch.object(GuestInfo, 'get_filetype')
    def test_03_arch(self, mock_getftype):
        """Test GuestInfo.arch()"""
        # arch is x86_64
        ftype = "/bin/ls: yyy, x86-64, xxx"
        mock_getftype.return_value = ftype
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.arch()
        self.assertEqual(status, "amd64")

        # arch is i386
        ftype = "/bin/ls: yyy, 80386, xxx"
        mock_getftype.return_value = ftype
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.arch()
        self.assertEqual(status, "i386")

        # arch is arm 64
        ftype = "/bin/ls: yyy, ARM, 64-bit"
        mock_getftype.return_value = ftype
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.arch()
        self.assertEqual(status, "arm64")

        # arch is arm
        ftype = "/bin/ls: yyy, ARM, xxx"
        mock_getftype.return_value = ftype
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.arch()
        self.assertEqual(status, "arm")

    @patch('udocker.helper.guestinfo.os.path.exists')
    @patch('udocker.helper.guestinfo.FileUtil.match')
    @patch('udocker.helper.guestinfo.FileUtil.getdata')
    def test_04_osdistribution(self, mock_gdata, mock_match, mock_exists):
        """Test GuestInfo.osdistribution()"""
        self.lsbdata = "DISTRIB_ID=Ubuntu\n" \
                       "DISTRIB_RELEASE=16.04\n" \
                       "DISTRIB_CODENAME=xenial\n" \
                       "DISTRIB_DESCRIPTION=Ubuntu 16.04.5 LTS\n"
        mock_match.return_value = ["/etc/lsb-release"]
        osdist = ("Ubuntu", "16.04")
        mock_exists.return_value = True
        mock_gdata.return_value = self.lsbdata
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.osdistribution()
        self.assertEqual(status, osdist)

        reldata = "CentOS release 6.10 (Final)"
        mock_match.return_value = ["/etc/centos-release"]
        osdist = ("CentOS", "6")
        mock_exists.return_value = True
        mock_gdata.return_value = reldata
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.osdistribution()
        self.assertEqual(status, osdist)

    @patch.object(GuestInfo, 'osdistribution')
    def test_05_osversion(self, mock_osdist):
        """Test GuestInfo.osversion()"""
        # has osdistro
        osdist = ("Ubuntu", "16.04")
        mock_osdist.return_value = osdist
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.osversion()
        self.assertEqual(status, "linux")

        # has no osdistro
        mock_osdist.return_value = self.noosdist
        ginfo = GuestInfo(self.conf, self.rootdir)
        status = ginfo.osversion()
        self.assertEqual(status, "")


if __name__ == '__main__':
    main()
