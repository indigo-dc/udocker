#!/usr/bin/env python2
"""
udocker unit tests: GuestInfo
"""
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

from udocker.helper.guestinfo import GuestInfo


class GuestInfoTestCase(TestCase):
    """Test GuestInfo() class."""

    def _init(self):
        """Common variables."""
        self.rootdir = "~/.udocker/container/abcd0/ROOT"
        self.file = "/bin/ls"
        self.ftype = "/bin/ls: yyy, x86-64, xxx"
        self.nofile = "ddd: cannot open"
        self.osdist = ("Ubuntu", "16.04")
        self.noosdist = ("", "xx")

    def test_01_init(self):
        """Test GuestInfo() constructor."""
        self._init()
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo._root_dir, self.rootdir)

    @patch('udocker.utils.uprocess.Uprocess.get_output')
    @patch('udocker.helper.guestinfo.os.path.isfile')
    def test_02_get_filetype(self, mock_isfile, mock_getout):
        """Test GuestInfo.get_filetype(filename)"""
        self._init()
        # full filepath exists
        mock_isfile.return_value = True
        mock_getout.return_value = self.ftype
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo.get_filetype(self.file), self.ftype)
        # file does not exist
        mock_isfile.return_value = False
        mock_getout.return_value = self.nofile
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo.get_filetype(self.nofile), "")

    @patch('udocker.helper.guestinfo.GuestInfo.get_filetype')
    def test_03_arch(self, mock_getftype):
        """Test GuestInfo.arch()"""
        self._init()
        # arch is x86_64
        mock_getftype.return_value = self.ftype
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo.arch(), "amd64")

    #@patch('udocker.helper.guestinfo.os.path.exists')
    #@patch('udocker.utils.fileutil.FileUtil.match')
    #@patch('udocker.utils.fileutil.FileUtil.getdata')
    #def test_04_osdistribution(self, mock_gdata, mock_match, mock_exists):
    #    """Test GuestInfo.osdistribution()"""
    #    self._init()
    #    # has osdistro
    #    self.lsbdata = "DISTRIB_ID=Ubuntu\n" \
    #                   "DISTRIB_RELEASE=16.04\n" \
    #                   "DISTRIB_CODENAME=xenial\n" \
    #                   "DISTRIB_DESCRIPTION=Ubuntu 16.04.5 LTS\n"
    #    mock_match.return_value = ["/etc/lsb-release"]
    #    mock_exists.return_value = True
    #    mock_gdata.return_value = self.lsbdata
    #    ginfo = GuestInfo(self.rootdir)
    #    self.assertEqual(ginfo.osdistribution(), self.osdist)

    @patch('udocker.helper.guestinfo.GuestInfo.osdistribution')
    def test_05_osversion(self, mock_osdist):
        """Test GuestInfo.osversion()"""
        self._init()
        # has osdistro
        mock_osdist.return_value = self.osdist
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo.osversion(), "linux")
        # has no osdistro
        mock_osdist.return_value = self.noosdist
        ginfo = GuestInfo(self.rootdir)
        self.assertEqual(ginfo.osversion(), "")


if __name__ == '__main__':
    main()
