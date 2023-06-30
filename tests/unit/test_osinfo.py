#!/usr/bin/env python
"""
udocker unit tests: OSInfo
"""

from unittest import TestCase, main
from unittest.mock import patch
from udocker.helper.osinfo import OSInfo
from udocker.config import Config
import collections

collections.Callable = collections.abc.Callable


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
        self.assertEqual(ginfo._root_dir, self.rootdir)

    @patch('udocker.helper.osinfo.os.path.islink')
    @patch('udocker.helper.osinfo.Uprocess.get_output')
    @patch('udocker.helper.osinfo.os.path.isfile')
    def test_02_get_filetype(self, mock_isfile, mock_getout, mock_islink):
        """Test02 OSInfo.get_filetype(filename)"""
        # file does not exist
        ftype = "/bin/ls: yyy, x86-64, xxx"
        mock_islink.return_value = False
        mock_isfile.return_value = False
        mock_getout.return_value = ftype
        ginfo = OSInfo(self.rootdir)
        status = ginfo.get_filetype(self.file)
        self.assertEqual(status, ("", ""))

        # full filepath exists
        ftype = "/bin/ls: yyy, x86-64, xxx"
        mock_islink.return_value = False
        mock_isfile.return_value = True
        mock_getout.return_value = ftype
        ginfo = OSInfo(self.rootdir)
        status = ginfo.get_filetype(self.file)
        self.assertEqual(status, ("readelf", ftype))

        # file type data not returned
        mock_isfile.return_value = False
        mock_isfile.return_value = True
        mock_getout.return_value = ""
        ginfo = OSInfo(self.rootdir)
        status = ginfo.get_filetype(self.file)
        self.assertEqual(status, ("", ""))

    @patch.object(OSInfo, 'arch_from_binaries')
    @patch.object(OSInfo, 'arch_from_metadata')
    def test_03_arch(self, mock_frommeta, mock_frombin):
        """Test03 OSInfo.arch()"""
        # arch from metadata is amd64
        mock_frommeta.return_value = "amd64"
        ginfo = OSInfo(self.rootdir)
        status = ginfo.arch()

        # arch  from metadata is empty from bin is amd64
        mock_frommeta.return_value = ""
        mock_frombin.return_value = "amd64"
        ginfo = OSInfo(self.rootdir)
        status = ginfo.arch()
        self.assertEqual(status, "amd64")

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
