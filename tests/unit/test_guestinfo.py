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
        conf = Config().getconf()
        self.rootdir = "~/.udocker/container/abcd0/ROOT"
        self.file = "/bin/ls"
        self.ftype = "/bin/ls: yyy, x86-64, xxx"
        self.nofile = "ddd: cannot open"
        self.osdist = ("Ubuntu", "16.04")
        self.noosdist = ("", "xx")
        self.ginfo = GuestInfo(conf, self.rootdir)

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test GuestInfo() constructor."""
        status = self.ginfo._root_dir
        self.assertEqual(status, self.rootdir)
        self.assertIsInstance(self.ginfo.binarylist, list)

    @patch('udocker.utils.uprocess.Uprocess.get_output')
    @patch('udocker.helper.guestinfo.os.path.isfile')
    def test_02_get_filetype(self, mock_isfile, mock_getout):
        """Test GuestInfo.get_filetype(filename)"""
        # full filepath exists
        mock_isfile.return_value = True
        mock_getout.return_value = self.ftype
        status = self.ginfo.get_filetype(self.file)
        self.assertEqual(status, self.ftype)

        # file does not exist
        mock_isfile.return_value = False
        mock_getout.return_value = self.nofile
        status = self.ginfo.get_filetype(self.nofile)
        self.assertEqual(status, "")

    @patch('udocker.helper.guestinfo.GuestInfo.get_filetype')
    def test_03_arch(self, mock_getftype):
        """Test GuestInfo.arch()"""
        # arch is x86_64
        mock_getftype.return_value = self.ftype
        status = self.ginfo.arch()
        self.assertEqual(status, "amd64")

    @patch('udocker.helper.guestinfo.os.path.exists')
    @patch('udocker.utils.fileutil.FileUtil.match')
    @patch('udocker.utils.fileutil.FileUtil.getdata')
    def test_04_osdistribution(self, mock_gdata, mock_match, mock_exists):
        """Test GuestInfo.osdistribution()"""
        self.lsbdata = "DISTRIB_ID=Ubuntu\n" \
                       "DISTRIB_RELEASE=16.04\n" \
                       "DISTRIB_CODENAME=xenial\n" \
                       "DISTRIB_DESCRIPTION=Ubuntu 16.04.5 LTS\n"
        mock_match.return_value = ["/etc/lsb-release"]
        mock_exists.return_value = True
        mock_gdata.return_value = self.lsbdata
        status = self.ginfo.osdistribution()
        self.assertEqual(status, self.osdist)

    @patch('udocker.helper.guestinfo.GuestInfo.osdistribution')
    def test_05_osversion(self, mock_osdist):
        """Test GuestInfo.osversion()"""
        # has osdistro
        mock_osdist.return_value = self.osdist
        status = self.ginfo.osversion()
        self.assertEqual(status, "linux")
        # has no osdistro
        mock_osdist.return_value = self.noosdist
        status = self.ginfo.osversion()
        self.assertEqual(status, "")


if __name__ == '__main__':
    main()
