#!/usr/bin/env python
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

    def setUp(self):
        self.conf = Config().getconf()

    def tearDown(self):
        pass

    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_01_init(self, mock_regpre, mock_base, mock_absp):
        """Test FileUtil(self.conf) constructor."""
        self.conf['tmpdir'] = '/tmp'
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        futil = FileUtil(self.conf, 'filename.txt')
        self.assertEqual(futil.filename, os.path.abspath('filename.txt'))
        self.assertTrue(mock_regpre.called)

        futil = FileUtil(self.conf, '-')
        self.assertEqual(futil.filename, '-')
        self.assertEqual(futil.basename, '-')

    def test_02_register_prefix(self):
        """Test FileUtil.register_prefix()."""
        pass

    @patch('udocker.utils.fileutil.os.umask')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_03_umask(self, mock_regpre, mock_base, mock_absp, mock_umask):
        """Test FileUtil.umask()."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_umask.return_value = 0
        futil = FileUtil(self.conf, "somedir")
        status = futil.umask()
        self.assertTrue(status)

        mock_umask.return_value = 0
        futil = FileUtil(self.conf, "somedir")
        FileUtil.orig_umask = 0
        status = futil.umask(1)
        self.assertTrue(status)
        self.assertEqual(FileUtil.orig_umask, 0)

        mock_umask.return_value = 0
        futil = FileUtil(self.conf, "somedir")
        FileUtil.orig_umask = None
        status = futil.umask(1)
        self.assertTrue(status)
        self.assertEqual(FileUtil.orig_umask, 0)

    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_04_mktmp(self, mock_regpre, mock_base, mock_absp):
        """Test FileUtil.mktmp()."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename2.txt'
        mock_absp.return_value = '/tmp/filename2.txt'
        self.conf['tmpdir'] = '/somewhere'
        tmp_file = FileUtil(self.conf, 'filename2.txt').mktmp()
        self.assertTrue(tmp_file.endswith('-filename2.txt'))
        self.assertTrue(tmp_file.startswith('/somewhere/udocker-'))
        self.assertGreater(len(tmp_file.strip()), 68)

    @patch('udocker.utils.fileutil.os.makedirs')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_05_mkdir(self, mock_regpre, mock_base, mock_absp, mock_mkdirs):
        """Create directory"""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_mkdirs.return_value = True
        status = FileUtil(self.conf, "somedir").mkdir()
        self.assertTrue(status)

        mock_mkdirs.side_effect = OSError("fail")
        status = FileUtil(self.conf, "somedir").mkdir()
        self.assertFalse(status)

    @patch.object(FileUtil, 'mktmp')
    @patch.object(FileUtil, 'mkdir')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_06_mktmpdir(self, mock_regpre, mock_base, mock_absp, mock_umkdir, mock_umktmp):
        """Test FileUtil.mktmpdir()."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_umktmp.return_value = "/dir"
        mock_umkdir.return_value = True
        status = FileUtil(self.conf, "somedir").mktmpdir()
        self.assertEqual(status, "/dir")

        mock_umktmp.return_value = "/dir"
        mock_umkdir.return_value = False
        status = FileUtil(self.conf, "somedir").mktmpdir()
        self.assertEqual(status, None)

    @patch('udocker.utils.fileutil.os.stat')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_07_uid(self, mock_regpre, mock_base, mock_absp, mock_stat):
        """Test FileUtil.uid()."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_stat.return_value.st_uid = 1234
        self.conf['tmpdir'] = "/tmp"
        futil = FileUtil(self.conf, "filename.txt")
        uid = futil.uid()
        self.assertEqual(uid, 1234)

    @patch.object(FileUtil, 'mktmp')
    @patch.object(FileUtil, 'mkdir')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_08__is_safe_prefix(self, mock_regpre, mock_base, mock_absp, mock_umkdir, mock_umktmp):
        """Test FileUtil._is_safe_prefix()."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        futil = FileUtil(self.conf, "somedir")
        FileUtil.safe_prefixes = []
        status = futil._is_safe_prefix("/AAA")
        self.assertFalse(status)

        futil = FileUtil(self.conf, "somedir")
        FileUtil.safe_prefixes = ["/AAA", ]
        status = futil._is_safe_prefix("/AAA")
        self.assertTrue(status)

    @patch('udocker.utils.fileutil.os.path.realpath')
    @patch('udocker.utils.fileutil.os.path.exists')
    @patch('udocker.utils.fileutil.Msg')
    @patch('udocker.utils.fileutil.os.remove')
    @patch('udocker.utils.fileutil.os.path.islink')
    @patch('udocker.utils.fileutil.os.path.isfile')
    @patch('udocker.utils.fileutil.os.path.isdir')
    @patch.object(FileUtil, 'uid')
    @patch.object(FileUtil, '_is_safe_prefix')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_09_remove_file(self, mock_regpre, mock_base, mock_absp, mock_safe, mock_uid, mock_isdir,
                            mock_isfile, mock_islink, mock_remove, mock_msg,
                            mock_exists, mock_realpath):
        """Test FileUtil.remove() with plain files."""
        mock_regpre.return_value = None
        mock_base.return_value = '/filename4.txt'
        mock_absp.return_value = '/filename4.txt'
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
        mock_base.return_value = 'filename4.txt'
        mock_absp.return_value = '/tmp/filename4.txt'
        mock_uid.return_value = 1001
        futil = FileUtil(self.conf, "/tmp/filename4.txt")
        status = futil.remove()
        self.assertFalse(status)

        # under /tmp
        mock_base.return_value = 'filename4.txt'
        mock_absp.return_value = '/tmp/filename4.txt'
        mock_uid.return_value = 1000
        futil = FileUtil(self.conf, "/tmp/filename4.txt")
        status = futil.remove()
        self.assertTrue(status)

        # under user home
        mock_base.return_value = 'filename4.txt'
        mock_absp.return_value = '/home/user/.udocker/filename4.txt'
        futil = FileUtil(self.conf, "/home/user/.udocker/filename4.txt")
        futil.safe_prefixes.append("/home/user/.udocker")
        status = futil.remove()
        self.assertTrue(status)

        # outside of scope 1
        mock_base.return_value = 'filename4.txt'
        mock_absp.return_value = '/etc/filename4.txt'
        mock_safe.return_value = False
        futil = FileUtil(self.conf, "/etc/filename4.txt")
        futil.safe_prefixes = []
        status = futil.remove()
        self.assertFalse(status)

    @patch('udocker.utils.fileutil.os.path.exists')
    @patch('udocker.utils.fileutil.Msg')
    @patch('udocker.utils.fileutil.subprocess.call')
    @patch('udocker.utils.fileutil.os.path.isdir')
    @patch('udocker.utils.fileutil.os.path.islink')
    @patch('udocker.utils.fileutil.os.path.isfile')
    @patch.object(FileUtil, 'uid')
    @patch.object(FileUtil, '_is_safe_prefix')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_10_remove_dir(self, mock_regpre, mock_base, mock_absp, mock_safe, mock_uid, mock_isfile,
                           mock_islink, mock_isdir, mock_call,
                           mock_msg, mock_exists):
        """Test FileUtil.remove() with directories."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
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

    @patch('udocker.utils.fileutil.Msg')
    @patch('udocker.utils.fileutil.subprocess.call')
    @patch('udocker.utils.fileutil.os.path.isfile')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_11_verify_tar(self, mock_regpre, mock_base, mock_absp, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_msg.level = 0
        mock_msg.VER = 4
        mock_isfile.return_value = False
        mock_call.return_value = 0
        status = FileUtil(self.conf, "tarball.tar").verify_tar()
        self.assertFalse(status)

        mock_isfile.return_value = True
        mock_call.return_value = 0
        status = FileUtil(self.conf, "tarball.tar").verify_tar()
        self.assertTrue(status)

        mock_isfile.return_value = True
        mock_call.return_value = 1
        status = FileUtil(self.conf, "tarball.tar").verify_tar()
        self.assertFalse(status)

    @patch.object(FileUtil, 'remove')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_12_cleanup(self, mock_regpre, mock_base, mock_absp, mock_remove):
        """Test FileUtil.cleanup() delete tmp files."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        self.conf['tmpdir'] = "/tmp"
        FileUtil.tmptrash = {'file1.txt': None, 'file2.txt': None}
        FileUtil(self.conf, "").cleanup()
        self.assertEqual(mock_remove.call_count, 2)

    @patch('udocker.utils.fileutil.os.stat')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_14_size(self, mock_regpre, mock_base, mock_absp, mock_stat):
        """Test FileUtil.size() get file size."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_stat.return_value.st_size = 4321
        size = FileUtil(self.conf, "somefile").size()
        self.assertEqual(size, 4321)

    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_15_getdata(self, mock_regpre, mock_base, mock_absp):
        """Test FileUtil.size() get file content."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        with patch(BUILTINS + '.open', mock_open(read_data='qwerty')):
            data = FileUtil(self.conf, "somefile").getdata()
            self.assertEqual(data, 'qwerty')

    def test_16_get1stline(self):
        """Test FileUtil.get1stline()."""
        pass

    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_17_putdata(self, mock_regpre, mock_base, mock_absp):
        """Test FileUtil.putdata()"""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        futil = FileUtil(self.conf, "somefile")
        futil.filename = ""
        data = futil.putdata("qwerty")
        self.assertFalse(data)

        with patch(BUILTINS + '.open', mock_open()):
            data = FileUtil(self.conf, "somefile").putdata("qwerty")
            self.assertEqual(data, 'qwerty')

    @patch('udocker.utils.fileutil.Uprocess.get_output')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_18_find_exec(self, mock_regpre, mock_base, mock_absp, mock_gout):
        """Test FileUtil.find_exec() find executable."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_gout.return_value = None
        filename = FileUtil(self.conf, "executable").find_exec()
        self.assertEqual(filename, "")

        mock_gout.return_value = "/bin/ls"
        filename = FileUtil(self.conf, "executable").find_exec()
        self.assertEqual(filename, "/bin/ls")

        mock_gout.return_value = "not found"
        filename = FileUtil(self.conf, "executable").find_exec()
        self.assertEqual(filename, "")

    @patch('udocker.utils.fileutil.os.path.lexists')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_19_find_inpath(self, mock_regpre, mock_base, mock_absp, mock_exists):
        """Test FileUtil.find_inpath() file is in a path."""
        # exist
        mock_regpre.return_value = None
        mock_base.return_value = 'exec'
        mock_absp.return_value = '/bin/exec'
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

    def test_20_list_inpath(self):
        """Test FileUtil.list_inpath()."""
        pass

    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_22_copyto(self, mock_regpre, mock_base, mock_absp):
        """Test FileUtil.copyto() file copy."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        with patch(BUILTINS + '.open', mock_open()):
            status = FileUtil(self.conf, "source").copyto("dest")
            self.assertTrue(status)

            status = FileUtil(self.conf, "source").copyto("dest", "w")
            self.assertTrue(status)

            status = FileUtil(self.conf, "source").copyto("dest", "a")
            self.assertTrue(status)

    @patch('udocker.utils.fileutil.os.path.exists')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_23_find_file_in_dir(self, mock_regpre, mock_base, mock_absp, mock_exists):
        """Test FileUtil.find_file_in_dir()."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/dir'
        file_list = []
        status = FileUtil(self.conf, "/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "")

        file_list = ["F1", "F2"]
        mock_exists.side_effect = [False, False]
        status = FileUtil(self.conf, "/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "")

        file_list = ["F1", "F2"]
        mock_exists.side_effect = [False, True]
        status = FileUtil(self.conf, "/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "/dir/F2")

    @patch('udocker.utils.fileutil.os.stat')
    @patch('udocker.utils.fileutil.os.symlink')
    @patch('udocker.utils.fileutil.os.remove')
    @patch('udocker.utils.fileutil.os.chmod')
    @patch('udocker.utils.fileutil.os.access')
    @patch('udocker.utils.fileutil.os.path.realpath')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_24__link_change_apply(self, mock_regpre, mock_base, mock_absp,
                                   mock_realpath, mock_access, mock_chmod,
                                   mock_remove, mock_symlink, mock_stat):
        """Actually apply the link convertion."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_realpath.return_value = "/HOST/DIR"
        mock_access.return_value = True
        futil = FileUtil(self.conf, "/con")
        futil._link_change_apply("/con/lnk_new", "/con/lnk", False)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)

        mock_access.return_value = False
        mock_chmod.return_value = None
        mock_remove.return_value = None
        mock_symlink.return_value = None
        mock_realpath.return_value = "/HOST/DIR"
        futil = FileUtil(self.conf, "/con")
        futil._link_change_apply("/con/lnk_new", "/con/lnk", True)
        self.assertTrue(mock_chmod.called)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)

    @patch('udocker.utils.fileutil.os.access')
    @patch('udocker.utils.fileutil.os.readlink')
    @patch.object(FileUtil, '_link_change_apply', return_value=None)
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_25__link_set(self, mock_regpre, mock_base, mock_absp, mock_lnchange,
                          mock_readlink, mock_access):
        """Test FileUtil._link_set()."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_readlink.return_value = "X"
        futil = FileUtil(self.conf, "/con")
        status = futil._link_set("/con/lnk", "", "/con", False)
        self.assertFalse(status)

        mock_readlink.return_value = "/con"
        futil = FileUtil(self.conf, "/con")
        status = futil._link_set("/con/lnk", "", "/con", False)
        self.assertFalse(status)

        mock_readlink.return_value = "/HOST/DIR"
        futil = FileUtil(self.conf, "/con")
        status = futil._link_set("/con/lnk", "", "/con", False)
        self.assertTrue(mock_lnchange.called)
        self.assertTrue(status)

        mock_readlink.return_value = "/HOST/DIR"
        mock_access.return_value = True
        futil = FileUtil(self.conf, "/con")
        status = futil._link_set("/con/lnk", "", "/con", True)
        self.assertTrue(mock_lnchange.called)
        self.assertTrue(status)

        mock_readlink.return_value = "/HOST/DIR"
        mock_access.return_value = False
        futil = FileUtil(self.conf, "/con")
        status = futil._link_set("/con/lnk", "", "/con", True)
        self.assertTrue(mock_lnchange.called)
        self.assertTrue(status)

    @patch('udocker.utils.fileutil.os.access')
    @patch('udocker.utils.fileutil.os.readlink')
    @patch.object(FileUtil, '_link_change_apply', return_value=None)
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_26__link_restore(self, mock_regpre, mock_base, mock_absp, mock_lnchange,
                              mock_readlink, mock_access):
        """Test FileUtil._link_restore()."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_readlink.return_value = "/con/AAA"
        futil = FileUtil(self.conf, "/con")
        status = futil._link_restore("/con/lnk", "/con", "/root", False)
        self.assertTrue(status)

        mock_readlink.return_value = "/con/AAA"
        futil = FileUtil(self.conf, "/con")
        status = futil._link_restore("/con/lnk", "/con", "/root", False)
        self.assertTrue(mock_lnchange.called)
        self.assertTrue(status)

        mock_readlink.return_value = "/root/BBB"
        futil = FileUtil(self.conf, "/con")
        status = futil._link_restore("/con/lnk", "/con", "/root", False)
        self.assertTrue(mock_lnchange.called)
        self.assertTrue(status)

        mock_readlink.return_value = "/XXX"
        futil = FileUtil(self.conf, "/con")
        status = futil._link_restore("/con/lnk", "/con", "/root", False)
        self.assertTrue(mock_lnchange.called)
        self.assertFalse(status)

        mock_readlink.return_value = "/root/BBB"
        futil = FileUtil(self.conf, "/con")
        status = futil._link_restore("/con/lnk", "/con", "/root", True)
        self.assertTrue(mock_lnchange.called)
        self.assertTrue(status)

        mock_readlink.return_value = "/root/BBB"
        mock_access.return_value = False
        futil = FileUtil(self.conf, "/con")
        status = futil._link_restore("/con/lnk", "", "/root", True)
        self.assertTrue(mock_lnchange.called)
        self.assertTrue(status)

    @patch.object(FileUtil, '_link_restore')
    @patch.object(FileUtil, '_link_set')
    @patch('udocker.utils.fileutil.Msg')
    @patch.object(FileUtil, '_is_safe_prefix')
    @patch('udocker.utils.fileutil.os.lstat')
    @patch('udocker.utils.fileutil.os.path.islink')
    @patch('udocker.utils.fileutil.os.walk')
    @patch('udocker.utils.fileutil.os.path.realpath')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_27_links_conv(self, mock_regpre, mock_base, mock_absp,
                           mock_realpath, mock_walk, mock_islink,
                           mock_lstat, mock_is_safe_prefix, mock_msg,
                           mock_link_set, mock_link_restore):
        """Test FileUtil.links_conv()."""
        mock_regpre.return_value = None
        mock_base.return_value = 'filename.txt'
        mock_absp.return_value = '/tmp/filename.txt'
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = False
        futil = FileUtil(self.conf, "/ROOT")
        status = futil.links_conv(False, True, "")
        self.assertEqual(status, None)

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_walk.return_value = []
        futil = FileUtil(self.conf, "/ROOT")
        status = futil.links_conv(False, True, "")
        self.assertEqual(status, [])

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_walk.return_value = [("/", [], []), ]
        futil = FileUtil(self.conf, "/ROOT")
        status = futil.links_conv(False, True, "")
        self.assertEqual(status, [])

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = False
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        futil = FileUtil(self.conf, "/ROOT")
        status = futil.links_conv(False, True, "")
        self.assertEqual(status, [])

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value.st_uid = 1
        self.conf['uid'] = 0
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        futil = FileUtil(self.conf, "/ROOT")
        status = futil.links_conv(False, True, "")
        self.assertEqual(status, [])

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value.st_uid = 1
        mock_link_set.reset_mock()
        mock_link_restore.reset_mock()
        self.conf['uid'] = 1
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        futil = FileUtil(self.conf, "/ROOT")
        status = futil.links_conv(False, True, "")
        self.assertTrue(mock_link_set.called)
        self.assertFalse(mock_link_restore.called)

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value.st_uid = 1
        mock_link_set.reset_mock()
        mock_link_restore.reset_mock()
        self.conf['uid'] = 1
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        futil = FileUtil(self.conf, "/ROOT")
        status = futil.links_conv(False, False, "")
        self.assertFalse(mock_link_set.called)
        self.assertTrue(mock_link_restore.called)

    @patch('udocker.utils.fileutil.os.listdir')
    @patch('udocker.utils.fileutil.os.path.isdir')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch('udocker.utils.fileutil.os.path.dirname')
    @patch('udocker.utils.fileutil.os.path.abspath')
    @patch('udocker.utils.fileutil.os.path.basename')
    @patch.object(FileUtil, '_register_prefix')
    def test_28_match(self, mock_regpre, mock_base, mock_absp,
                      mock_osdir, mock_osbase, mock_isdir, mock_osls):
        """Test FileUtil.match()."""
        pass


if __name__ == '__main__':
    main()
