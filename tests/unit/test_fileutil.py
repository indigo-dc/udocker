#!/usr/bin/env python2
"""
udocker unit tests: FileUtil
"""
import sys
import os
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

sys.path.append('.')

from udocker.utils.fileutil import FileUtil
from udocker.config import Config

STDOUT = sys.stdout
STDERR = sys.stderr
UDOCKER_TOPDIR = "test_topdir"

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def find_str(self, find_exp, where):
    """Find string in test output messages."""
    found = False
    for item in where:
        if find_exp in str(item):
            self.assertTrue(True)
            found = True
            break
    if not found:
        self.assertTrue(False)


def is_writable_file(obj):
    """Check if obj is a file."""
    try:
        obj.write("")
    except(AttributeError, OSError, IOError):
        return False
    else:
        return True


class FileUtilTestCase(TestCase):
    """Test FileUtil(self.conf) file manipulation methods."""

    def _init(self):
        """Configure variables."""
        cnf = Config()
        self.conf = cnf.getconf()

    def test_01_init(self):
        """Test FileUtil(self.conf) constructor."""
        self._init()
        self.conf['tmpdir'] = "/tmp"
        futil = FileUtil(self.conf, "filename.txt")
        self.assertEqual(futil.filename, os.path.abspath("filename.txt"))
        self.assertTrue(self.conf['tmpdir'])

        #mock_config.side_effect = AttributeError("abc")
        #futil = FileUtil(self.conf)
        #self.assertEqual(futil.filename, None)

    def test_02_mktmp(self):
        """Test FileUtil.mktmp()."""
        self._init()
        self.conf['tmpdir'] = "/somewhere"
        tmp_file = FileUtil(self.conf, "filename2.txt").mktmp()
        self.assertTrue(tmp_file.endswith("-filename2.txt"))
        self.assertTrue(tmp_file.startswith("/somewhere/udocker-"))
        self.assertGreater(len(tmp_file.strip()), 68)

    @patch('udocker.config.Config._oskernel')
    @patch('udocker.config.Config._osdistribution')
    @patch('udocker.config.Config._osversion')
    @patch('udocker.config.Config._arch')
    @patch('udocker.config.Config._username')
    @patch('udocker.config.Config.os.getgid')
    @patch('udocker.config.Config.os.getuid')
    @patch('udocker.config.Config.os.path.expanduser')
    @patch('udocker.utils.fileutil.os.stat')
    def test_03_uid(self, mock_stat, mock_expand, mock_uid, mock_gid, mock_user,
                    mock_arch, mock_osver, mock_osdist, mock_oskern):
        """Test FileUtil.uid()."""
        self._init()
        mock_stat.return_value.st_uid = 1234
        uid = FileUtil(self.conf, "filename3.txt").uid()
        self.assertEqual(uid, 1234)

    @patch('udocker.utils.fileutil.os.path.realpath')
    @patch('udocker.utils.fileutil.os.path.exists')
    @patch('udocker.msg.Msg')
    @patch('udocker.utils.fileutil.os.remove')
    @patch('udocker.utils.fileutil.os.path.islink')
    @patch('udocker.utils.fileutil.os.path.isfile')
    @patch('udocker.utils.fileutil.os.path.isdir')
    @patch('udocker.utils.fileutil.FileUtil.uid')
    @patch('udocker.utils.fileutil.FileUtil._is_safe_prefix')
    def test_04_remove_file(self, mock_safe, mock_uid, mock_isdir,
                            mock_isfile, mock_islink, mock_remove, mock_msg,
                            mock_exists, mock_realpath):
        """Test FileUtil.remove() with plain files."""
        self._init()
        mock_uid.return_value = 1000
        # file does not exist (regression of #50)
        mock_isdir.return_value = True
        mock_isfile.return_value = True
        mock_exists.return_value = True
        mock_safe.return_value = True
        self.conf['uid'] = 1000
        self.conf['tmpdir'] = "/tmp"
        mock_realpath.return_value = "/tmp"
        # under /
        futil = FileUtil(self.conf, "/filename4.txt")
        status = futil.remove()
        self.assertFalse(status)
        # wrong uid
        mock_uid.return_value = 1001
        futil = FileUtil(self.conf, "/tmp/filename4.txt")
        status = futil.remove()
        self.assertFalse(status)
        # under /tmp
        mock_uid.return_value = 1000
        futil = FileUtil(self.conf, "/tmp/filename4.txt")
        status = futil.remove()
        self.assertTrue(status)
        # under user home
        futil = FileUtil(self.conf, "/home/user/.udocker/filename4.txt")
        futil.safe_prefixes.append("/home/user/.udocker")
        status = futil.remove()
        self.assertTrue(status)
        # outside of scope 1
        mock_safe.return_value = False
        futil = FileUtil(self.conf, "/etc/filename4.txt")
        futil.safe_prefixes = []
        status = futil.remove()
        self.assertFalse(status)

    @patch('udocker.utils.fileutil.os.path.exists')
    @patch('udocker.msg.Msg')
    @patch('udocker.utils.fileutil.subprocess.call')
    @patch('udocker.utils.fileutil.os.path.isdir')
    @patch('udocker.utils.fileutil.os.path.islink')
    @patch('udocker.utils.fileutil.os.path.isfile')
    @patch('udocker.utils.fileutil.FileUtil.uid')
    @patch('udocker.utils.fileutil.FileUtil._is_safe_prefix')
    def test_05_remove_dir(self, mock_safe, mock_uid, mock_isfile,
                           mock_islink, mock_isdir, mock_call,
                           mock_msg, mock_exists):
        """Test FileUtil.remove() with directories."""
        self._init()
        mock_uid.return_value = 1000
        mock_isfile.return_value = False
        mock_islink.return_value = False
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_safe.return_value = True
        mock_call.return_value = 0
        self.conf['uid'] = 1000
        self.conf['tmpdir'] = "/tmp"
        # remove directory under /tmp OK
        futil = FileUtil(self.conf, "/tmp/directory")
        status = futil.remove()
        self.assertTrue(status)
        # remove directory under /tmp NOT OK
        mock_call.return_value = 1
        futil = FileUtil(self.conf, "/tmp/directory")
        status = futil.remove()
        self.assertFalse(status)

    @patch('udocker.msg.Msg')
    @patch('udocker.utils.fileutil.subprocess.call')
    @patch('udocker.utils.fileutil.os.path.isfile')
    def test_06_verify_tar01(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file - 01."""
        self._init()
        mock_msg.level = 0
        mock_isfile.return_value = False
        mock_call.return_value = 0
        status = FileUtil(self.conf, "tarball.tar").verify_tar()
        self.assertFalse(status)

    @patch('udocker.msg.Msg')
    @patch('udocker.utils.fileutil.subprocess.call')
    @patch('udocker.utils.fileutil.os.path.isfile')
    def test_07_verify_tar02(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file. - 02"""
        self._init()
        mock_msg.level = 0
        mock_isfile.return_value = True
        mock_call.return_value = 0
        status = FileUtil(self.conf, "tarball.tar").verify_tar()
        self.assertTrue(status)

    @patch('udocker.msg.Msg')
    @patch('udocker.utils.fileutil.subprocess.call')
    @patch('udocker.utils.fileutil.os.path.isfile')
    def test_08_verify_tar03(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file. - 03"""
        self._init()
        mock_msg.level = 0
        mock_isfile.return_value = True
        mock_call.return_value = 1
        status = FileUtil(self.conf, "tarball.tar").verify_tar()
        self.assertFalse(status)

    @patch('udocker.utils.fileutil.FileUtil.remove')
    def test_09_cleanup(self, mock_remove):
        """Test FileUtil.cleanup() delete tmp files."""
        self._init()
        self.conf['tmpdir'] = "/tmp"
        FileUtil.tmptrash = {'file1.txt': None, 'file2.txt': None}
        FileUtil(self.conf, "").cleanup()
        self.assertEqual(mock_remove.call_count, 2)

    @patch('udocker.utils.fileutil.os.path.isdir')
    def test_10_isdir(self, mock_isdir):
        """Test FileUtil.isdir()."""
        self._init()
        mock_isdir.return_value = True
        status = FileUtil(self.conf, "somedir").isdir()
        self.assertTrue(status)
        mock_isdir.return_value = False
        status = FileUtil(self.conf, "somedir").isdir()
        self.assertFalse(status)

    @patch('udocker.utils.fileutil.os.stat.st_size')
    def test_11_size(self, mock_stat):
        """Test FileUtil.size() get file size."""
        self._init()
        mock_stat.return_value = 4321
        size = FileUtil(self.conf, "somefile").size()
        self.assertEqual(size, 4321)

    def test_12_getdata(self):
        """Test FileUtil.size() get file content."""
        self._init()
        with patch(BUILTINS + '.open', mock_open(read_data='qwerty')):
            data = FileUtil(self.conf, "somefile").getdata()
            self.assertEqual(data, 'qwerty')

    @patch('udocker.utils.uprocess.Uprocess.get_output')
    def test_13_find_exec(self, mock_gout):
        """Test FileUtil.find_exec() find executable."""
        self._init()
        mock_gout.return_value = None
        filename = FileUtil(self.conf, "executable").find_exec()
        self.assertEqual(filename, "")
        #
        mock_gout.return_value = "/bin/ls"
        filename = FileUtil(self.conf, "executable").find_exec()
        self.assertEqual(filename, "/bin/ls")
        #
        mock_gout.return_value = "not found"
        filename = FileUtil(self.conf, "executable").find_exec()
        self.assertEqual(filename, "")

    @patch('udocker.utils.fileutil.os.path.lexists')
    def test_14_find_inpath(self, mock_exists):
        """Test FileUtil.find_inpath() file is in a path."""
        # exist
        self._init()
        mock_exists.return_value = True
        filename = FileUtil(self.conf, "exec").find_inpath("/bin:/usr/bin")
        self.assertEqual(filename, "/bin/exec")
        # does not exist
        mock_exists.return_value = False
        filename = FileUtil(self.conf, "exec").find_inpath("/bin:/usr/bin")
        self.assertEqual(filename, "")
        # exist PATH=
        mock_exists.return_value = True
        filename = FileUtil(self.conf, "exec").find_inpath("PATH=/bin:/usr/bin")
        self.assertEqual(filename, "/bin/exec")
        # does not exist PATH=
        mock_exists.return_value = False
        filename = FileUtil(self.conf, "exec").find_inpath("PATH=/bin:/usr/bin")
        self.assertEqual(filename, "")

    def test_15_copyto(self):
        """Test FileUtil.copyto() file copy."""
        self._init()
        with patch(BUILTINS + '.open', mock_open()):
            status = FileUtil(self.conf, "source").copyto("dest")
            self.assertTrue(status)
            status = FileUtil(self.conf, "source").copyto("dest", "w")
            self.assertTrue(status)
            status = FileUtil(self.conf, "source").copyto("dest", "a")
            self.assertTrue(status)

    @patch('udocker.utils.fileutil.os.makedirs')
    @patch('udocker.utils.fileutil.FileUtil')
    def test_16_mkdir(self, mock_mkdirs, mock_futil):
        """Create directory"""
        mock_mkdirs.return_value = True
        status = mock_futil.mkdir()
        self.assertTrue(status)

        mock_mkdirs.side_effect = OSError("fail")
        status = mock_futil.mkdir()
        self.assertTrue(status)

    @patch('udocker.utils.fileutil.os.umask')
    def test_17_umask(self, mock_umask):
        """Test FileUtil.umask()."""
        self._init()
        mock_umask.return_value = 0
        futil = FileUtil(self.conf, "somedir")
        status = futil.umask()
        self.assertTrue(status)
        #
        mock_umask.return_value = 0
        futil = FileUtil(self.conf, "somedir")
        FileUtil.orig_umask = 0
        status = futil.umask(1)
        self.assertTrue(status)
        self.assertEqual(FileUtil.orig_umask, 0)
        #
        mock_umask.return_value = 0
        futil = FileUtil(self.conf, "somedir")
        FileUtil.orig_umask = None
        status = futil.umask(1)
        self.assertTrue(status)
        self.assertEqual(FileUtil.orig_umask, 0)

    @patch('udocker.utils.fileutil.FileUtil.mktmp')
    @patch('udocker.utils.fileutil.FileUtil.mkdir')
    def test_18_mktmpdir(self, mock_umkdir, mock_umktmp):
        """Test FileUtil.mktmpdir()."""
        self._init()
        mock_umktmp.return_value = "/dir"
        mock_umkdir.return_value = True
        futil = FileUtil(self.conf, "somedir")
        status = futil.mktmpdir()
        self.assertEqual(status, "/dir")
        #
        mock_umktmp.return_value = "/dir"
        mock_umkdir.return_value = False
        futil = FileUtil(self.conf, "somedir")
        status = futil.mktmpdir()
        self.assertEqual(status, None)

    @patch('udocker.utils.fileutil.FileUtil.mktmp')
    @patch('udocker.utils.fileutil.FileUtil.mkdir')
    def test_19__is_safe_prefix(self, mock_umkdir, mock_umktmp):
        """Test FileUtil._is_safe_prefix()."""
        self._init()
        futil = FileUtil(self.conf, "somedir")
        FileUtil.safe_prefixes = []
        status = futil._is_safe_prefix("/AAA")
        self.assertFalse(status)
        #
        futil = FileUtil(self.conf, "somedir")
        FileUtil.safe_prefixes = ["/AAA", ]
        status = futil._is_safe_prefix("/AAA")
        self.assertTrue(status)

    def test_20_putdata(self):
        """Test FileUtil.putdata()"""
        self._init()
        futil = FileUtil(self.conf, "somefile")
        futil.filename = ""
        data = futil.putdata("qwerty")
        self.assertFalse(data)
        #
        with patch(BUILTINS + '.open', mock_open()):
            data = FileUtil(self.conf, "somefile").putdata("qwerty")
            self.assertEqual(data, 'qwerty')

    @patch('udocker.utils.fileutil.os.rename')
    def test_21_rename(self, mock_rename):
        """Test FileUtil.rename()."""
        self._init()
        status = FileUtil(self.conf, "somefile").rename("otherfile")
        self.assertTrue(status)

    @patch('udocker.utils.fileutil.os.path.exists')
    def test_22_find_file_in_dir(self, mock_exists):
        """Test FileUtil.find_file_in_dir()."""
        self._init()
        file_list = []
        status = FileUtil(self.conf, "/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "")
        #
        file_list = ["F1", "F2"]
        mock_exists.side_effect = [False, False]
        status = FileUtil(self.conf, "/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "")
        #
        file_list = ["F1", "F2"]
        mock_exists.side_effect = [False, True]
        status = FileUtil(self.conf, "/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "/dir/F2")

    @patch('udocker.utils.fileutil.os.symlink')
    @patch('udocker.utils.fileutil.os.remove')
    @patch('udocker.utils.fileutil.os.stat')
    @patch('udocker.utils.fileutil.os.chmod')
    @patch('udocker.utils.fileutil.os.access')
    @patch('udocker.utils.fileutil.os.path.dirname')
    @patch('udocker.utils.fileutil.os.path.realpath')
    @patch('udocker.utils.fileutil.os.readlink')
    def test_23__link_change_apply(self, mock_readlink,
                                   mock_realpath, mock_dirname,
                                   mock_access, mock_chmod, mock_stat,
                                   mock_remove, mock_symlink):
        """Actually apply the link convertion."""
        self._init()
        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_access.return_value = True
        FileUtil(self.conf, "/con")._link_change_apply("/con/lnk_new", "/con/lnk", False)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)

        mock_access.return_value = False
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        FileUtil(self.conf, "/con")._link_change_apply("/con/lnk_new", "/con/lnk", True)
        self.assertTrue(mock_chmod.called)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)

    @patch('udocker.utils.fileutil.os.symlink')
    @patch('udocker.utils.fileutil.os.remove')
    @patch('udocker.utils.fileutil.os.stat')
    @patch('udocker.utils.fileutil.os.chmod')
    @patch('udocker.utils.fileutil.os.access')
    @patch('udocker.utils.fileutil.os.path.dirname')
    @patch('udocker.utils.fileutil.os.path.realpath')
    @patch('udocker.utils.fileutil.os.readlink')
    def test_24__link_set(self, mock_readlink, mock_realpath, mock_dirname,
                          mock_access, mock_chmod, mock_stat, mock_remove,
                          mock_symlink):
        """Test FileUtil._link_set()."""
        self._init()
        mock_readlink.return_value = "X"
        status = FileUtil(self.conf, "/con")._link_set("/con/lnk", "", "/con", False)
        self.assertFalse(status)
        #
        mock_readlink.return_value = "/con"
        status = FileUtil(self.conf, "/con")._link_set("/con/lnk", "", "/con", False)
        self.assertFalse(status)
        #
        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = FileUtil(self.conf, "/con")._link_set("/con/lnk", "", "/con", False)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)
        self.assertFalse(mock_chmod.called)
        self.assertTrue(status)
        #
        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_access.return_value = True
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = FileUtil(self.conf, "/con")._link_set("/con/lnk", "", "/con", True)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)
        self.assertFalse(mock_chmod.called)
        self.assertTrue(status)
        #
        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_access.return_value = False
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = FileUtil(self.conf, "/con")._link_set("/con/lnk", "", "/con", True)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)
        self.assertTrue(mock_chmod.called)
        self.assertTrue(status)

    @patch('udocker.utils.fileutil.os.symlink')
    @patch('udocker.utils.fileutil.os.remove')
    @patch('udocker.utils.fileutil.os.stat')
    @patch('udocker.utils.fileutil.os.chmod')
    @patch('udocker.utils.fileutil.os.access')
    @patch('udocker.utils.fileutil.os.path.dirname')
    @patch('udocker.utils.fileutil.os.path.realpath')
    @patch('udocker.utils.fileutil.os.readlink')
    def test_25__link_restore(self, mock_readlink, mock_realpath, mock_dirname,
                              mock_access, mock_chmod, mock_stat, mock_remove,
                              mock_symlink):
        """Test FileUtil._link_restore()."""
        self._init()
        mock_readlink.return_value = "/con/AAA"
        status = FileUtil(self.conf, "/con")._link_restore("/con/lnk", "/con",
                                                           "/root", False)
        self.assertTrue(status)
        #
        mock_readlink.return_value = "/con/AAA"
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = FileUtil(self.conf, "/con")._link_restore("/con/lnk", "/con",
                                                "/root", False)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/AAA"))
        #
        mock_readlink.return_value = "/root/BBB"
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = FileUtil(self.conf, "/con")._link_restore("/con/lnk", "/con",
                                                "/root", False)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/BBB"))
        #
        mock_readlink.return_value = "/XXX"
        status = FileUtil(self.conf, "/con")._link_restore("/con/lnk", "/con",
                                                "/root", False)
        self.assertFalse(status)
        #
        mock_readlink.return_value = "/root/BBB"
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = FileUtil(self.conf, "/con")._link_restore("/con/lnk", "/con",
                                                "/root", True)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/BBB"))
        self.assertFalse(mock_chmod.called)
        #
        mock_readlink.return_value = "/root/BBB"
        mock_access.return_value = False
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = FileUtil(self.conf, "/con")._link_restore("/con/lnk", "",
                                                "/root", True)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/BBB"))
        self.assertTrue(mock_chmod.called)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)

    @patch('udocker.utils.fileutil.FileUtil._link_restore')
    @patch('udocker.utils.fileutil.FileUtil._link_set')
    @patch('udocker.msg.Msg')
    @patch('udocker.utils.fileutil.FileUtil._is_safe_prefix')
    @patch('udocker.utils.fileutil.os.lstat.st_uid')
    @patch('udocker.utils.fileutil.os.path.islink')
    @patch('udocker.utils.fileutil.os.walk')
    @patch('udocker.utils.fileutil.os.path.realpath')
    def test_26_links_conv(self, mock_realpath, mock_walk, mock_islink,
                           mock_lstat, mock_is_safe_prefix, mock_msg,
                           mock_link_set, mock_link_restore):
        """Test FileUtil.links_conv()."""
        self._init()
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = False
        status = FileUtil(self.conf, "/ROOT").links_conv(False, True, "")
        self.assertEqual(status, None)
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_walk.return_value = []
        status = FileUtil(self.conf, "/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_walk.return_value = [("/", [], []), ]
        status = FileUtil(self.conf, "/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = False
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = FileUtil(self.conf, "/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value = 1
        self._init()
        self.conf['uid'] = 0
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = FileUtil(self.conf, "/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value = 1
        mock_link_set.reset_mock()
        mock_link_restore.reset_mock()
        self._init()
        self.conf['uid'] = 1
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = FileUtil(self.conf, "/ROOT").links_conv(False, True, "")
        self.assertTrue(mock_link_set.called)
        self.assertFalse(mock_link_restore.called)
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value = 1
        mock_link_set.reset_mock()
        mock_link_restore.reset_mock()
        self._init()
        self.conf['uid'] = 1
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = FileUtil(self.conf, "/ROOT").links_conv(False, False, "")
        self.assertFalse(mock_link_set.called)
        self.assertTrue(mock_link_restore.called)


if __name__ == '__main__':
    main()
