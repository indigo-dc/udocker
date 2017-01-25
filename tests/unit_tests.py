#!/usr/bin/env python
"""
==================
udocker unit tests
==================
Unit tests for udocker, a wrapper to execute basic docker containers
without using docker.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
import pwd
import grp
import subprocess
import unittest
import mock

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

__author__ = "udocker@lip.pt"
__credits__ = ["PRoot http://proot.me"]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "0.0.2-1"
__date__ = "2016"

try:
    import udocker
except ImportError:
    sys.path.append(".")
    sys.path.append("..")
    import udocker

STDOUT = sys.stdout
STDERR = sys.stderr
UDOCKER_TOPDIR = "test_topdir"

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def set_env():
    """Set environment variables"""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


def find_str(self, find_exp, where):
    """Find string in test ouput messages"""
    found = False
    for item in where:
        if find_exp in str(item):
            self.assertTrue(True)
            found = True
            break
    if not found:
        self.assertTrue(False)


def is_writable_file(obj):
    """Check if obj is a file"""
    try:
        obj.write("")
    except(AttributeError, OSError, IOError):
        return False
    else:
        return True


class ConfigTestCase(unittest.TestCase):
    """Test case for the udocker configuration"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    def _verify_config(self, conf):
        """Verify config parameters"""
        self.assertIsInstance(conf.verbose_level, int)

        self.assertIsInstance(conf.topdir, str)
        self.assertIs(conf.bindir, None)
        self.assertIs(conf.libdir, None)
        self.assertIs(conf.reposdir, None)
        self.assertIs(conf.layersdir, None)
        self.assertIs(conf.containersdir, None)
        self.assertIsInstance(conf.homedir, str)
        self.assertIsInstance(conf.config, str)
        self.assertIsInstance(conf.keystore, str)
        self.assertIsInstance(conf.tmpdir, str)
        self.assertIsInstance(conf.tarball, str)
        self.assertIsInstance(conf.cmd, list)
        self.assertIsInstance(conf.sysdirs_list, tuple)
        self.assertIsInstance(conf.hostauth_list, tuple)
        self.assertIsInstance(conf.dri_list, tuple)
        self.assertIsInstance(conf.valid_host_env, str)
        self.assertIsInstance(conf.cpu_affinity_exec_tools, tuple)
        self.assertIsInstance(conf.location, str)

        self.assertIsInstance(conf.http_proxy, str)
        self.assertIsInstance(conf.timeout, int)
        self.assertIsInstance(conf.download_timeout, int)
        self.assertIsInstance(conf.ctimeout, int)
        self.assertIsInstance(conf.http_agent, str)
        self.assertIsInstance(conf.http_insecure, bool)

        self.assertIsInstance(conf.dockerio_index_url, str)
        self.assertIsInstance(conf.dockerio_registry_url, str)

    def test_01_init(self):
        """Test Config() constructor"""
        conf = udocker.Config()
        self._verify_config(conf)

    @mock.patch('udocker.platform')
    def test_02_platform(self, mock_platform):
        """Test Config.platform()"""
        conf = udocker.Config()
        mock_platform.machine.return_value = "x86_64"
        arch = conf.arch()
        self.assertEqual("amd64", arch, "Config._sysarch x86_64")
        mock_platform.machine.return_value = "i586"
        arch = conf.arch()
        self.assertEqual("i386", arch, "Config._sysarchi i586")
        mock_platform.machine.return_value = "xpto"
        arch = conf.arch()
        self.assertEqual("", arch, "Config._sysarchi i586")
        #
        mock_platform.system.return_value = "linux"
        osver = conf.osversion()
        self.assertEqual(osver, "linux")
        #
        mock_platform.release.return_value = "release"
        osver = conf.oskernel()
        self.assertEqual(osver, "release")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileUtil')
    def test_03_user_init_good(self, mock_fileutil, mock_msg):
        """Test Config.user_init() with good data"""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        mock_fileutil.return_value.size.return_value = 10
        conf_data = '# comment\nverbose_level = 100\n'
        conf_data += 'tmpdir = "/xpto"\ncmd = ["/bin/ls", "-l"]\n'
        mock_fileutil.return_value.getdata.return_value = conf_data
        status = conf.user_init("filename.conf")
        self.assertTrue(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.sys.exit')
    def test_04_user_init_bad(self, mock_exit, mock_fileutil, mock_msg):
        """Test Config.user_init() with bad config data"""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        conf_data = 'hh +=* ffhdklfh\n'
        mock_fileutil.return_value.size.return_value = 10
        mock_fileutil.return_value.getdata.return_value = conf_data
        conf.user_init("filename.conf")
        self.assertTrue(mock_exit.called)

    @mock.patch('udocker.Msg')
    def test_05_username(self, mock_msg):
        """Test Config._username()"""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        user = conf.username()
        self.assertEqual(user, pwd.getpwuid(os.getuid()).pw_name)

    @mock.patch('udocker.Config.oskernel')
    @mock.patch('udocker.Msg')
    def test_06_oskernel_isgreater(self, mock_msg, mock_oskern):
        """Test Config.oskernel_isgreater()"""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        #
        mock_oskern.return_value = "1.1.2-"
        status = conf.oskernel_isgreater([1, 1, 1])
        self.assertTrue(status)
        #
        mock_oskern.return_value = "1.2.1-"
        status = conf.oskernel_isgreater([1, 1, 1])
        self.assertTrue(status)
        #
        mock_oskern.return_value = "1.0.1-"
        status = conf.oskernel_isgreater([1, 1, 1])
        self.assertFalse(status)


class MsgTestCase(unittest.TestCase):
    """Test Msg() class screen error and info messages"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    def _verify_descriptors(self, msg):
        """Verify Msg() file descriptors"""
        self.assertTrue(is_writable_file(msg.chlderr))
        self.assertTrue(is_writable_file(msg.chldout))
        self.assertTrue(is_writable_file(msg.chldnul))

    def test_01_init(self):
        """Test Msg() constructor"""
        msg = udocker.Msg(0)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 0)

    def test_02_setlevel(self):
        """Test Msg.setlevel() change of log level"""
        msg = udocker.Msg(5)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 5)
        msg = udocker.Msg(0)
        msg.setlevel(7)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 7)

    @mock.patch('udocker.sys.stdout', new_callable=StringIO)
    def test_03_out(self, mock_stdout):
        """Test Msg.out() screen messages"""
        msg = udocker.Msg(udocker.Msg.MSG)
        msg.out("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stdout.getvalue())
        sys.stdout = STDOUT
        sys.stderr = STDERR

    @mock.patch('udocker.sys.stderr', new_callable=StringIO)
    def test_04_err(self, mock_stderr):
        """Test Msg.err() screen messages"""
        msg = udocker.Msg(udocker.Msg.ERR)
        msg.err("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stderr.getvalue())
        sys.stdout = STDOUT
        sys.stderr = STDERR


class UniqueTestCase(unittest.TestCase):
    """Test Unique() class"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    def test_01_init(self):
        """Test Unique() constructor"""
        uniq = udocker.Unique()
        self.assertEqual(uniq.def_name, "udocker")

    def test_02_rnd(self):
        """Test Unique._rnd()"""
        uniq = udocker.Unique()
        rand = uniq._rnd(64)
        self.assertIsInstance(rand, str)
        self.assertEqual(len(rand), 64)

    def test_03_uuid(self):
        """Test Unique.uuid()"""
        uniq = udocker.Unique()
        rand = uniq.uuid("zxcvbnm")
        self.assertEqual(len(rand), 36)
        rand = uniq.uuid(789)
        self.assertEqual(len(rand), 36)

    def test_04_imagename(self):
        """Test Unique.imagename()"""
        uniq = udocker.Unique()
        rand = uniq.imagename()
        self.assertEqual(len(rand), 16)

    def test_05_layer_v1(self):
        """Test Unique.layer_v1()"""
        uniq = udocker.Unique()
        rand = uniq.layer_v1()
        self.assertEqual(len(rand), 64)

    def test_06_filename(self):
        """Test Unique.filename()"""
        uniq = udocker.Unique()
        rand = uniq.filename("zxcvbnmasdf")
        self.assertTrue(rand.endswith("zxcvbnmasdf"))
        self.assertTrue(rand.startswith("udocker"))
        self.assertGreater(len(rand.strip()), 56)
        rand = uniq.filename(12345)
        self.assertTrue(rand.endswith("12345"))
        self.assertTrue(rand.startswith("udocker"))
        self.assertGreater(len(rand.strip()), 50)


class FileUtilTestCase(unittest.TestCase):
    """Test FileUtil() file manipulation methods"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    @mock.patch('udocker.Config')
    def test_01_init(self, mock_config):
        """Test FileUtil() constructor"""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        futil = udocker.FileUtil("filename.txt")
        self.assertEqual(futil.filename, "filename.txt")
        self.assertTrue(udocker.Config.tmpdir)

    def test_02_mktmp(self):
        """Test FileUtil.mktmp()"""
        udocker.Config.tmpdir = "/somewhere"
        tmp_file = udocker.FileUtil("filename2.txt").mktmp()
        self.assertTrue(tmp_file.endswith("-filename2.txt"))
        self.assertTrue(tmp_file.startswith("/somewhere/udocker-"))
        self.assertGreater(len(tmp_file.strip()), 68)

    @mock.patch('udocker.os.stat')
    def test_03_uid(self, mock_stat):
        """Test FileUtil.uid()"""
        mock_stat.return_value.st_uid = 1234
        uid = udocker.FileUtil("filename3.txt").uid()
        self.assertEqual(uid, 1234)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.FileUtil.uid')
    def test_04_remove_file(self, mock_uid, mock_isfile,
                            mock_islink, mock_remove, mock_msg):
        """Test FileUtil.remove() with plain files"""
        mock_uid.return_value = os.getuid()
        mock_isfile.return_value = True
        # under /
        futil = udocker.FileUtil("/filename4.txt")
        futil.topdir = "/home/user/.udocker"
        futil.tmpdir = "/tmp"
        status = futil.remove()
        self.assertFalse(status)
        # wrong uid
        mock_uid.return_value = os.getuid() + 1
        futil = udocker.FileUtil("/tmp/filename4.txt")
        futil.topdir = "/home/user/.udocker"
        futil.tmpdir = "/tmp"
        status = futil.remove()
        self.assertFalse(status)
        # under /tmp
        mock_uid.return_value = os.getuid()
        futil = udocker.FileUtil("/tmp/filename4.txt")
        futil.topdir = "/home/user/.udocker"
        futil.tmpdir = "/tmp"
        status = futil.remove()
        self.assertTrue(status)
        # under user home
        futil = udocker.FileUtil("/home/user/.udocker/filename4.txt")
        futil.topdir = "/home/user/.udocker"
        futil.tmpdir = "/tmp"
        futil.safe_prefixes.append(futil.topdir)
        status = futil.remove()
        self.assertTrue(status)
        # outside of scope 1
        futil = udocker.FileUtil("/etc/filename4.txt")
        futil.topdir = "/home/user/.udocker"
        futil.tmpdir = "/tmp"
        futil.safe_prefixes = []
        status = futil.remove()
        self.assertFalse(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.FileUtil.uid')
    def test_05_remove_dir(self, mock_uid, mock_isfile, mock_islink,
                           mock_isdir, mock_call, mock_msg):
        """Test FileUtil.remove() with directories"""
        mock_uid.return_value = os.getuid()
        mock_isfile.return_value = False
        mock_islink.return_value = False
        mock_isdir.return_value = True
        mock_call.return_value = 0
        # remove directory under /tmp OK
        futil = udocker.FileUtil("/tmp/directory")
        futil.topdir = "/home/user/.udocker"
        futil.tmpdir = "/tmp"
        status = futil.remove()
        self.assertTrue(status)
        # remove directory under /tmp NOT OK
        mock_call.return_value = 1
        futil = udocker.FileUtil("/tmp/directory")
        futil.topdir = "/home/user/.udocker"
        futil.tmpdir = "/tmp"
        status = futil.remove()
        self.assertFalse(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isfile')
    def test_06_verify_tar01(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file"""
        mock_msg.level = 0
        mock_isfile.return_value = False
        mock_call.return_value = 0
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertFalse(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isfile')
    def test_07_verify_tar02(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file"""
        mock_msg.level = 0
        mock_isfile.return_value = True
        mock_call.return_value = 0
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertTrue(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isfile')
    def test_08_verify_tar03(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file"""
        mock_msg.level = 0
        mock_isfile.return_value = True
        mock_call.return_value = 1
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertFalse(status)

    @mock.patch('udocker.Config')
    @mock.patch('udocker.FileUtil.remove')
    def test_09_cleanup(self, mock_remove, mock_config):
        """Test FileUtil.cleanup() delete tmp files"""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        udocker.FileUtil.tmptrash = {'file1.txt': None, 'file2.txt': None}
        udocker.FileUtil("").cleanup()
        self.assertEqual(mock_remove.call_count, 2)

    @mock.patch('udocker.os.path.isdir')
    def test_10_isdir(self, mock_isdir):
        """Test FileUtil.isdir()"""
        mock_isdir.return_value = True
        status = udocker.FileUtil("somedir").isdir()
        self.assertTrue(status)
        mock_isdir.return_value = False
        status = udocker.FileUtil("somedir").isdir()
        self.assertFalse(status)

    @mock.patch('udocker.os.stat')
    def test_11_size(self, mock_stat):
        """Test FileUtil.size() get file size"""
        mock_stat.return_value.st_size = 4321
        size = udocker.FileUtil("somefile").size()
        self.assertEqual(size, 4321)

    def test_12_getdata(self):
        """Test FileUtil.size() get file content"""
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='qwerty')):
            data = udocker.FileUtil("somefile").getdata()
            self.assertEqual(data, 'qwerty')

    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.FileUtil.remove')
    @mock.patch('udocker.FileUtil.getdata')
    @mock.patch('udocker.FileUtil.mktmp')
    def test_13_find_exec(self, mock_mktmp, mock_getdata,
                          mock_remove, mock_call):
        """Test FileUtil.find_exec() find executable"""
        mock_mktmp.return_value.mktmp.return_value = "/tmp/tmpfile"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            # executable found
            mock_getdata.return_value = "/bin/executable"
            filename = udocker.FileUtil("executable").find_exec()
            self.assertEqual(filename, "/bin/executable")
            # executable not found
            mock_getdata.return_value = "not found"
            filename = udocker.FileUtil("executable").find_exec()
            self.assertEqual(filename, "")
            # executable not found
            mock_getdata.return_value = "xxxxx"
            filename = udocker.FileUtil("executable").find_exec()
            self.assertEqual(filename, "")

    @mock.patch('udocker.os.path.exists')
    def test_14_find_inpath(self, mock_exists):
        """Test FileUtil.find_inpath() file is in a path"""
        # exist
        mock_exists.return_value = True
        filename = udocker.FileUtil("exec").find_inpath("/bin:/usr/bin")
        self.assertEqual(filename, "/bin/exec")
        # does not exist
        mock_exists.return_value = False
        filename = udocker.FileUtil("exec").find_inpath("/bin:/usr/bin")
        self.assertEqual(filename, "")
        # exist PATH=
        mock_exists.return_value = True
        filename = udocker.FileUtil("exec").find_inpath("PATH=/bin:/usr/bin")
        self.assertEqual(filename, "/bin/exec")
        # does not exist PATH=
        mock_exists.return_value = False
        filename = udocker.FileUtil("exec").find_inpath("PATH=/bin:/usr/bin")
        self.assertEqual(filename, "")

    def test_15_copyto(self):
        """Test FileUtil.copyto() file copy"""
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = udocker.FileUtil("source").copyto("dest")
            self.assertTrue(status)
            status = udocker.FileUtil("source").copyto("dest", "w")
            self.assertTrue(status)
            status = udocker.FileUtil("source").copyto("dest", "a")
            self.assertTrue(status)


class KeyStoreTestCase(unittest.TestCase):
    """Test KeyStore() local basic credentials storage"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    def _init(self):
        """Common variables"""
        self.url = u'https://xxx'
        self.email = u'user@domain'
        self.auth = u'xxx'
        self.credentials = {self.url: {u'email': self.email,
                                       u'auth': self.auth}}

    def test_01_init(self):
        """Test KeyStore() constructor"""
        kstore = udocker.KeyStore("filename")
        self.assertEqual(kstore.keystore_file, "filename")

    @mock.patch('udocker.json.load')
    def test_02_read_all(self, mock_jload):
        """Test KeyStore()._read_all() read credentials"""
        self._init()
        mock_jload.return_value = self.credentials
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertEqual(self.credentials, kstore._read_all())

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    def test_02_shred(self, mock_config, mock_verks):
        """Test KeyStore()._shred() erase file content"""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertFalse(kstore._shred())

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.os.stat')
    def test_03_shred(self, mock_stat, mock_config, mock_verks):
        """Test KeyStore()._shred() erase file content"""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_stat.return_value.st_size = 123
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertTrue(kstore._shred())

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.json.dump')
    @mock.patch('udocker.os.umask')
    def test_04_write_all(self, mock_umask, mock_jdump,
                          mock_config, mock_verks):
        """Test KeyStore()._write_all() write all credentials to file"""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_umask.return_value = 077
        mock_jdump.side_effect = IOError('json dump')
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertFalse(kstore._write_all(self.credentials))

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.KeyStore._read_all')
    def test_05_get(self, mock_readall, mock_config, mock_verks):
        """Test KeyStore().get() get credential for url from file"""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_readall.return_value = self.credentials
        kstore = udocker.KeyStore("filename")
        self.assertTrue(kstore.get(self.url))
        self.assertFalse(kstore.get("NOT EXISTING ENTRY"))

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.KeyStore._shred')
    @mock.patch('udocker.KeyStore._write_all')
    @mock.patch('udocker.KeyStore._read_all')
    def test_06_put(self, mock_readall, mock_writeall, mock_shred,
                    mock_config, mock_verks):
        """Test KeyStore().put() put credential for url to file"""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        kstore = udocker.KeyStore("filename")
        self.assertFalse(kstore.put("", "", ""))
        mock_readall.return_value = dict()
        kstore.put(self.url, self.auth, self.email)
        mock_writeall.assert_called_once_with(self.credentials)

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.KeyStore._shred')
    @mock.patch('udocker.KeyStore._write_all')
    @mock.patch('udocker.KeyStore._read_all')
    def test_07_delete(self, mock_readall, mock_writeall, mock_shred,
                       mock_config, mock_verks):
        """Test KeyStore().delete() delete credential for url from file"""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_readall.return_value = self.credentials
        kstore = udocker.KeyStore("filename")
        kstore.delete(self.url)
        mock_writeall.assert_called_once_with({})

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.os.unlink')
    @mock.patch('udocker.KeyStore._shred')
    def test_07_erase(self, mock_shred, mock_unlink,
                      mock_config, mock_verks):
        """Test KeyStore().erase() erase credentials file"""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        kstore = udocker.KeyStore("filename")
        self.assertTrue(kstore.erase())
        mock_unlink.assert_called_once_with("filename")


class UdockerToolsTestCase(unittest.TestCase):
    """Test UdockerTools() download and setup of tools needed by udocker"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.Config')
    def test_01_init(self, mock_config, mock_localrepo, mock_geturl):
        """Test UdockerTools() constructor"""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        udocker.Config.tarball = "/tmp/xxx"
        localrepo = mock_localrepo
        localrepo.bindir = "/bindir"
        utools = udocker.UdockerTools(localrepo)
        self.assertEqual(utools.localrepo, localrepo)

    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.UdockerTools.__init__')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.FileUtil.mktmp')
    @mock.patch.object(udocker.UdockerTools, '_install')
    @mock.patch.object(udocker.UdockerTools, '_verify_version')
    @mock.patch.object(udocker.UdockerTools, '_instructions')
    @mock.patch.object(udocker.UdockerTools, '_download')
    @mock.patch.object(udocker.UdockerTools, 'is_available')
    def test_03_install(self, mock_is, mock_down, mock_instr, mock_ver,
                        mock_install,
                        mock_mktmp, mock_geturl, mock_call, mock_futil,
                        mock_init, mock_localrepo, mock_msg, mock_exists):
        """Test UdockerTools.install()"""
        mock_msg.level = 0
        mock_futil.return_value.mktmp.return_value = "filename_tmp"
        mock_init.return_value = None
        utools = udocker.UdockerTools(mock_localrepo)
        utools.localrepo = mock_localrepo
        utools.curl = mock_geturl
        utools.localrepo.topdir = "/home/user/.udocker"
        udocker.CurlHeader()
        # IS AVAILABLE NO DOWNLOAD
        mock_is.return_value = True
        status = utools.install()
        self.assertTrue(status)
        # NO AUTOINSTALL
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._autoinstall = False
        status = utools.install()
        self.assertEqual(status, None)
        # NO TARBALL
        mock_is.return_value = False
        utools._tarball = ""
        utools._autoinstall = True
        status = utools.install()
        self.assertFalse(status)
        # _download fails
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        mock_down.return_value = ""
        status = utools.install()
        self.assertTrue(mock_instr.called)
        self.assertFalse(status)
        # _download ok _verify_version fails
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = False
        status = utools.install()
        self.assertTrue(mock_instr.called)
        self.assertTrue(mock_futil.return_value.remove.called)
        self.assertFalse(status)
        # _download ok _verify_version ok install ok
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = True
        mock_install.return_value = True
        status = utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(status)
        # _download ok _verify_version ok install fail
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = True
        mock_install.return_value = False
        status = utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(mock_instr.called)
        self.assertTrue(mock_futil.return_value.remove.called)
        self.assertFalse(status)
        # file not exists no download
        mock_is.return_value = False
        mock_exists.return_value = False
        utools._tarball = "filename.tgz"
        utools._tarball_file = ""
        status = utools.install()
        self.assertTrue(mock_instr.called)
        self.assertFalse(mock_futil.remove.called)
        self.assertFalse(status)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.UdockerTools.__init__')
    def test_04_download(self, mock_init, mock_futil, mock_gurl):
        """Test UdockerTools.download()"""
        mock_init.return_value = None
        utools = udocker.UdockerTools(None)
        utools.curl = mock_gurl
        utools._tarball = "http://node.domain/filename.tgz"
        hdr = udocker.CurlHeader()
        hdr.data["X-ND-CURLSTATUS"] = 0
        mock_futil.return_value.mktmp.return_value = "tmptarball"
        mock_gurl.get.return_value = (hdr, "")
        status = utools._download()
        self.assertEqual(status, "tmptarball")
        #
        hdr.data["X-ND-CURLSTATUS"] = 1
        status = utools._download()
        self.assertEqual(status, "")

    @mock.patch('udocker.UdockerTools._version_isequal')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.UdockerTools.__init__')
    def test_04_verify_version(self, mock_init, mock_futil, mock_call,
                               mock_msg, mock_versioneq):
        """Test UdockerTools._verify_version()"""
        mock_init.return_value = None
        utools = udocker.UdockerTools(None)
        mock_futil.return_value.mktmp.return_value = ""
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_msg.level = 0
        mock_call.return_value = 1
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        mock_versioneq.return_value = False
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        mock_versioneq.return_value = True
        status = utools._verify_version("tarballfile")
        self.assertTrue(status)

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.UdockerTools.__init__')
    def test_04__install(self, mock_init, mock_call, mock_msg, mock_local):
        """Test UdockerTools._install()"""
        mock_init.return_value = None
        utools = udocker.UdockerTools(None)
        utools.localrepo = mock_local
        mock_local.bindir = ""
        mock_msg.level = 0
        mock_call.return_value = 1
        status = utools._install("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        status = utools._install("tarballfile")
        self.assertTrue(status)


class LocalRepositoryTestCase(unittest.TestCase):
    """Test LocalRepositoryTestCase() management of local repository
    of container images and extracted containers
    Tests not yet implemented:
    _load_structure
    _find_top_layer_id
    _sorted_layers
    verify_image
    """

    def _localrepo(self, topdir):
        """Instantiate a local repository class"""
        topdir_path = os.getenv("HOME") + "/" + topdir
        udocker.Config = mock.patch('udocker.Config').start()
        udocker.Config.tmpdir = "/tmp"
        udocker.Config.homedir = "/tmp"
        udocker.Config.bindir = ""
        udocker.Config.libdir = ""
        udocker.Config.reposdir = ""
        udocker.Config.layersdir = ""
        udocker.Config.containersdir = ""
        localrepo = udocker.LocalRepository(topdir_path)
        return localrepo

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    def test_01_init(self):
        """Test LocalRepository() constructor"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        self.assertTrue(localrepo.topdir)
        self.assertTrue(localrepo.reposdir)
        self.assertTrue(localrepo.layersdir)
        self.assertTrue(localrepo.containersdir)
        self.assertTrue(localrepo.bindir)
        self.assertTrue(localrepo.libdir)
        self.assertTrue(localrepo.homedir)
        self.assertEqual(localrepo.cur_repodir, "")
        self.assertEqual(localrepo.cur_tagdir, "")
        self.assertEqual(localrepo.cur_containerdir, "")

    def test_02_setup(self):
        """Test LocalRepository().setup()"""
        localrepo = self._localrepo("XXXX")
        self.assertEqual(os.path.basename(localrepo.topdir), "XXXX")
        localrepo.setup("YYYY")
        self.assertEqual(os.path.basename(localrepo.topdir), "YYYY")

    def test_03_create_repo(self):
        """Test LocalRepository().create_repo()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])
        self.assertFalse(os.path.exists(localrepo.topdir))
        localrepo.create_repo()
        self.assertTrue(os.path.exists(localrepo.topdir))
        self.assertTrue(os.path.exists(localrepo.reposdir))
        self.assertTrue(os.path.exists(localrepo.layersdir))
        self.assertTrue(os.path.exists(localrepo.containersdir))
        self.assertTrue(os.path.exists(localrepo.bindir))
        self.assertTrue(os.path.exists(localrepo.libdir))
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])

    def test_04_is_repo(self):
        """Test LocalRepository().is_repo()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])
        localrepo.create_repo()
        self.assertTrue(localrepo.is_repo())
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])

    def test_05_is_container_id(self):
        """Test LocalRepository().is_container_id"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        self.assertTrue(localrepo.is_container_id(
            "10860ac1-6962-3a9b-a5f8-63bcfb67ce39"))
        self.assertFalse(localrepo.is_container_id(
            "10860ac1-6962-3a9b-a5f863bcfb67ce37"))
        self.assertFalse(localrepo.is_container_id(
            "10860ac1-6962--3a9b-a5f863bcfb67ce37"))
        self.assertFalse(localrepo.is_container_id(
            "-6962--3a9b-a5f863bcfb67ce37"))
        self.assertFalse(localrepo.is_container_id(
            12345678))

    def test_06_get_container_name(self):
        """Test LocalRepository().get_container_name()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir = mock.patch('os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = mock.patch('os.listdir').start()
        mock_listdir.return_value = ['LINK']
        mock_islink = mock.patch('os.path.islink').start()
        mock_islink.return_value = True
        mock_readlink = mock.patch('os.readlink').start()
        mock_readlink.return_value = "/a/b/IMAGE:TAG"
        name_list = localrepo.get_container_name("IMAGE:TAG")
        self.assertEqual(name_list, ["LINK"])

    def test_07a_get_containers_list(self):
        """Test LocalRepository().get_containers_list()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir = mock.patch('os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = mock.patch('os.listdir').start()
        mock_listdir.return_value = ['LINK']
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='REPONAME')):
            containers_list = localrepo.get_containers_list()
            self.assertEqual(os.path.basename(containers_list[0]), "LINK")

    @mock.patch.object(udocker.LocalRepository, 'get_container_name')
    def test_07b_get_containers_list(self, mock_getname):
        """Test LocalRepository().get_containers_list()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir = mock.patch('os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = mock.patch('os.listdir').start()
        mock_listdir.return_value = ['LINK']
        mock_islink = mock.patch('os.path.islink').start()
        mock_islink.return_value = False
        mock_getname.return_value = ["NAME1", "NAME2"]
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='REPONAME')):
            containers_list = localrepo.get_containers_list(False)
            self.assertEqual(os.path.basename(containers_list[0][1]),
                             "REPONAME")

    @mock.patch.object(udocker.LocalRepository, 'get_containers_list')
    def test_08_cd_container(self, mock_getlist):
        """Test LocalRepository().cd_container()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists = mock.patch('os.path.exists').start()
        mock_exists.return_value = True
        mock_getlist.return_value = [localrepo.containersdir +
                                     "/CONTAINERNAME"]
        container_path = localrepo.cd_container("CONTAINERNAME")
        self.assertEqual(container_path, mock_getlist.return_value[0])

    def test_09_protect_container(self):
        """Test LocalRepository().protect_container()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            localrepo.protect_container(container_id)
            self.assertTrue(mopen.called)
            self.assertEqual(mopen.call_args, mock.call('/PROTECT', 'w'))

    def test_10_isprotected_container(self):
        """Test LocalRepository().isprotected_container()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch('os.path.exists') as mexists:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            localrepo.isprotected_container(container_id)
            self.assertTrue(mexists.called)
            self.assertEqual(mexists.call_args, mock.call('/PROTECT'))

    @mock.patch('udocker.FileUtil.remove')
    @mock.patch('udocker.os.path.exists')
    def test_11_unprotect_container(self, mock_exists, mock_remove):
        """Test LocalRepository().isprotected_container()"""
        mock_exists.return_value = True
        mock_remove.return_value = False
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        localrepo.unprotect_container(container_id)
        self.assertTrue(mock_remove.called)

    def test_12_protect_imagerepo(self):
        """Test LocalRepository().protect_imagerepo()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            localrepo.protect_imagerepo("IMAGE", "TAG")
            self.assertTrue(mopen.called)
            protect = localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mopen.call_args, mock.call(protect, 'w'))

    def test_13_isprotected_imagerepo(self):
        """Test LocalRepository().isprotected_imagerepo()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch('os.path.exists') as mexists:
            localrepo.isprotected_imagerepo("IMAGE", "TAG")
            self.assertTrue(mexists.called)
            protect = localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mexists.call_args, mock.call(protect))

    @mock.patch('udocker.FileUtil.remove')
    def test_14_unprotect_imagerepo(self, mock_remove):
        """Test LocalRepository().unprotected_imagerepo()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.unprotect_imagerepo("IMAGE", "TAG")
        self.assertTrue(mock_remove.called)

    @mock.patch('udocker.os.access')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.exists')
    @mock.patch.object(udocker.LocalRepository, 'cd_container')
    def test_15_iswriteable_container(self, mock_cd, mock_exists,
                                      mock_isdir, mock_access):
        """Test LocalRepository().iswriteable_container()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_exists.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 2)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 3)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = True
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 1)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 0)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.os.path.exists')
    def test_16_del_container_name(self, mock_exists, mock_remove, mock_msg):
        """Test LocalRepository().del_container_name()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = False
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertTrue(status)

    @mock.patch('udocker.os.symlink')
    @mock.patch('udocker.os.path.exists')
    def test_17_symlink(self, mock_exists, mock_symlink):
        """Test LocalRepository()._symlink()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = True
        status = localrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = False
        status = localrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertTrue(status)

    @mock.patch('udocker.os.path.exists')
    @mock.patch.object(udocker.LocalRepository, '_symlink')
    @mock.patch.object(udocker.LocalRepository, 'cd_container')
    def test_18_set_container_name(self, mock_cd, mock_slink, mock_exists):
        """Test LocalRepository().set_container_name()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        status = localrepo.set_container_name(container_id, "WRONG[/")
        self.assertFalse(status)
        #
        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = True
        status = localrepo.set_container_name(container_id, "RIGHT")
        self.assertFalse(status)
        #
        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = False
        status = localrepo.set_container_name(container_id, "RIGHT")
        self.assertTrue(status)

    @mock.patch('udocker.os.readlink')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.islink')
    def test_19_get_container_id(self, mock_islink,
                                 mock_isdir, mock_readlink):
        """Test LocalRepository().get_container_id()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        status = localrepo.get_container_id(None)
        self.assertEqual(status, "")
        #
        mock_islink.return_value = True
        mock_readlink.return_value = "BASENAME"
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "BASENAME")
        #
        mock_islink.return_value = False
        mock_isdir.return_value = False
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "")
        #
        mock_islink.return_value = False
        mock_isdir.return_value = True
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "ALIASNAM")

    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_20_setup_container(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_container()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = True
        status = localrepo.setup_container("REPO", "TAG", "ID")
        self.assertEqual(status, "")
        #
        mock_exists.return_value = False
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = localrepo.setup_container("REPO", "TAG", "ID")
            self.assertEqual(status, localrepo.containersdir + "/ID")
            self.assertEqual(localrepo.cur_containerdir,
                             localrepo.containersdir + "/ID")

    @mock.patch('udocker.os.readlink')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.FileUtil')
    @mock.patch.object(udocker.LocalRepository, '_inrepository')
    def test_21_remove_layers(self, mock_in, mock_futil,
                              mock_listdir, mock_islink, mock_readlink):
        """Test LocalRepository()._remove_layers()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_listdir.return_value = []
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        mock_listdir.return_value = ["FILE1,", "FILE2"]
        mock_islink.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        mock_islink.return_value = True
        mock_readlink.return_value = "REALFILE"
        mock_futil.return_value.remove.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)
        #
        mock_futil.return_value.remove.return_value = True
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        mock_futil.return_value.remove.return_value = True
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)
        #
        mock_futil.return_value.remove.return_value = False
        mock_in.return_value = False
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)
        #
        mock_futil.return_value.remove.return_value = False
        mock_in.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)
        #
        mock_futil.return_value.remove.return_value = False
        mock_in.return_value = True
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch.object(udocker.LocalRepository, '_remove_layers')
    @mock.patch.object(udocker.LocalRepository, 'cd_imagerepo')
    def test_22_del_imagerepo(self, mock_cd, mock_rmlayers, mock_futil):
        """Test LocalRepository()._del_imagerepo()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_cd.return_value = False
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertFalse(status)
        #
        mock_cd.return_value = True
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertTrue(status)
        #
        mock_rmlayers = True
        localrepo.cur_repodir = "XXXX"
        localrepo.cur_tagdir = "XXXX"
        mock_futil.return_value.remove.return_value = True
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertEqual(localrepo.cur_repodir, "")
        self.assertEqual(localrepo.cur_tagdir, "")
        self.assertTrue(status)

    def _sideffect_test_23(self, arg):
        """Side effect for isdir on test 23 _get_tags()"""
        if self.iter < 3:
            self.iter += 1
            return False
        else:
            return True

    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.FileUtil')
    @mock.patch.object(udocker.LocalRepository, '_is_tag')
    def test_23_get_tags(self, mock_is, mock_futil,
                         mock_listdir, mock_isdir):
        """Test LocalRepository()._get_tags()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_futil.return_value.isdir.return_value = False
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = []
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        mock_isdir.return_value = False
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = True
        status = localrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(status, expected_status)
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        self.iter = 0
        mock_isdir.side_effect = self._sideffect_test_23
        status = localrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(self.iter, 2)
        self.assertEqual(status, [])

    @mock.patch('udocker.FileUtil.remove')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.exists')
    @mock.patch.object(udocker.LocalRepository, '_symlink')
    def test_24_add_image_layer(self, mock_slink, mock_exists,
                                mock_islink, mock_remove):
        """Test LocalRepository().add_image_layer()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        localrepo.cur_repodir = ""
        localrepo.cur_tagdir = ""
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(status)
        #
        localrepo.cur_repodir = "IMAGE"
        localrepo.cur_tagdir = "TAG"
        status = localrepo.add_image_layer("FILE")
        self.assertTrue(status)
        #
        mock_exists.return_value = False
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        mock_islink.return_value = True
        status = localrepo.add_image_layer("FILE")
        self.assertTrue(mock_remove.called)
        self.assertTrue(status)
        #
        mock_remove.called = None
        mock_islink.return_value = False
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(mock_remove.called)
        self.assertTrue(status)

    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_25_setup_imagerepo(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_imagerepo()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.setup_imagerepo("")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        status = localrepo.setup_imagerepo("IMAGE")
        expected_directory = localrepo.reposdir + "/IMAGE"
        self.assertEqual(localrepo.cur_repodir, expected_directory)
        self.assertFalse(status)
        #
        mock_exists.return_value = False
        status = localrepo.setup_imagerepo("IMAGE")
        expected_directory = localrepo.reposdir + "/IMAGE"
        self.assertTrue(mock_makedirs.called)
        self.assertEqual(localrepo.cur_repodir, expected_directory)
        self.assertTrue(status)

    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_26_setup_tag(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_tag()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_exists.return_value = False
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.setup_tag("NEWTAG")
            self.assertTrue(mock_makedirs.called)
            expected_directory = localrepo.reposdir + "/IMAGE/NEWTAG"
            self.assertEqual(localrepo.cur_tagdir, expected_directory)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_27_set_version(self, mock_exists, mock_makedirs, mock_listdir):
        """Test LocalRepository().set_version()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.set_version("v1")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.set_version("v1")
        self.assertFalse(mock_listdir.called)
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.set_version("v1")
            self.assertTrue(mock_listdir.called)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @mock.patch.object(udocker.LocalRepository, 'save_json')
    @mock.patch.object(udocker.LocalRepository, 'load_json')
    @mock.patch('udocker.os.path.exists')
    def test_28_get_image_attributes(self, mock_exists, mock_loadjson,
                                     mock_savejson):
        """Test LocalRepository().get_image_attributes()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_exists.return_value = True
        mock_loadjson.return_value = None
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, False]
        mock_loadjson.side_effect = [("foolayername", ), ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, True, False]
        mock_loadjson.side_effect = [("foolayername", ), "foojson"]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, True, True]
        mock_loadjson.side_effect = [("foolayername", ), "foojson"]
        status = localrepo.get_image_attributes()
        self.assertEqual(('foojson', ['/foolayername.layer']), status)
        #
        mock_exists.side_effect = [False, True]
        mock_loadjson.side_effect = [None, ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [False, True, False]
        manifest = {
            "fsLayers": ({"blobSum": "foolayername"}, ),
            "history": ({"v1Compatibility": '["foojsonstring"]'}, )
        }
        mock_loadjson.side_effect = [manifest, ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [False, True, True]
        mock_loadjson.side_effect = [manifest, ]
        status = localrepo.get_image_attributes()
        self.assertEqual(([u'foojsonstring'], ['/foolayername']), status)

    @mock.patch('udocker.json.dump')
    @mock.patch('udocker.os.path.exists')
    def test_29_save_json(self, mock_exists, mock_jsondump):
        """Test LocalRepository().save_json()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.save_json("filename", "data")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.save_json("filename", "data")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertTrue(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            status = localrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @mock.patch('udocker.json.load')
    @mock.patch('udocker.os.path.exists')
    def test_30_load_json(self, mock_exists, mock_jsonload):
        """Test LocalRepository().load_json()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.load_json("filename")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.load_json("filename")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertTrue(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            status = localrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertFalse(status)


class CurlHeaderTestCase(unittest.TestCase):
    """Test CurlHeader() http header parser"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    def test_01_init(self):
        """Test CurlHeader() constructor"""
        curl_header = udocker.CurlHeader()
        self.assertFalse(curl_header.sizeonly)
        self.assertIsInstance(curl_header.data, dict)
        self.assertEqual("", curl_header.data["X-ND-HTTPSTATUS"])
        self.assertEqual("", curl_header.data["X-ND-CURLSTATUS"])

    def test_02_write(self):
        """Test CurlHeader().write()"""
        buff = ["HTTP/1.1 200 OK",
                "Content-Type: application/octet-stream",
                "Content-Length: 32", ]
        curl_header = udocker.CurlHeader()
        for line in buff:
            curl_header.write(line)
        self.assertEqual(curl_header.data["content-type"],
                         "application/octet-stream")
        self.assertEqual(curl_header.data["X-ND-HTTPSTATUS"],
                         "HTTP/1.1 200 OK")
        #
        curl_header = udocker.CurlHeader()
        for line in buff:
            curl_header.write(line)
        buff_out = curl_header.getvalue()
        self.assertEqual(buff_out[0:37],
                         "{'X-ND-HTTPSTATUS': 'HTTP/1.1 200 OK'")
        #
        line = ""
        curl_header = udocker.CurlHeader()
        curl_header.sizeonly = True
        self.assertEqual(-1, curl_header.write(line))

    @mock.patch('udocker.CurlHeader.write')
    def test_03_setvalue_from_file(self, mock_write):
        """Test CurlHeader().setvalue_from_file()"""
        fakedata = StringIO('XXXX')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = \
                lambda self: iter(fakedata.readline, '')
            curl_header = udocker.CurlHeader()
            self.assertTrue(curl_header.setvalue_from_file("filename"))
            mock_write.assert_called_with('XXXX')

    def test_04_getvalue(self):
        """Test CurlHeader().getvalue()"""
        curl_header = udocker.CurlHeader()
        curl_header.data = "XXXX"
        self.assertEqual(curl_header.getvalue(), curl_header.data)


class GetURLTestCase(unittest.TestCase):
    """Test GetURL() perform http operations portably"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    def _init(self):
        """Configure variables"""
        udocker.Config = mock.patch('udocker.Config').start()
        udocker.Config.timeout = 1
        udocker.Config.ctimeout = 1
        udocker.Config.download_timeout = 1
        udocker.Config.http_agent = ""
        udocker.Config.http_proxy = ""
        udocker.Config.http_insecure = 0

    def _get(self, *args, **kwargs):
        """mock for pycurl.get"""
        return args[0]

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURL._select_implementation')
    def test_01_init(self, mock_simplement, mock_msg):
        """Test GetURL() constructor"""
        self._init()
        geturl = udocker.GetURL()
        self.assertEqual(geturl.ctimeout, udocker.Config.ctimeout)
        self.assertEqual(geturl.insecure, udocker.Config.http_insecure)
        self.assertEqual(geturl.cache_support, False)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLexeCurl')
    @mock.patch('udocker.GetURLpyCurl')
    def test_02_select_implementation(self, mock_gupycurl,
                                      mock_guexecurl, mock_msg):
        """Test GetURL()._select_implementation()"""
        self._init()
        mock_gupycurl.return_value.is_available.return_value = True
        geturl = udocker.GetURL()
        geturl._select_implementation()
        self.assertEqual(geturl.cache_support, True)
        #
        mock_gupycurl.return_value.is_available.return_value = False
        geturl = udocker.GetURL()
        geturl._select_implementation()
        self.assertEqual(geturl.cache_support, False)
        #
        mock_guexecurl.return_value.is_available.return_value = False
        with self.assertRaises(NameError):
            udocker.GetURL()

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLexeCurl')
    @mock.patch('udocker.GetURLpyCurl')
    def test_03_get_content_length(self, mock_gupycurl,
                                   mock_guexecurl, mock_msg):
        """Test GetURL().get_content_length()"""
        self._init()
        geturl = udocker.GetURL()
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10, }
        self.assertEqual(geturl.get_content_length(hdr), 10)
        hdr.data = {"content-length": dict(), }
        self.assertEqual(geturl.get_content_length(hdr), -1)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLexeCurl')
    @mock.patch('udocker.GetURLpyCurl')
    def test_04_set_insecure(self, mock_gupycurl,
                             mock_guexecurl, mock_msg):
        """Test GetURL().set_insecure()"""
        self._init()
        geturl = udocker.GetURL()
        geturl.set_insecure()
        self.assertEqual(geturl.insecure, True)
        #
        geturl.set_insecure(False)
        self.assertEqual(geturl.insecure, False)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLexeCurl')
    @mock.patch('udocker.GetURLpyCurl')
    def test_05_set_proxy(self, mock_gupycurl,
                          mock_guexecurl, mock_msg):
        """Test GetURL().set_proxy()"""
        self._init()
        geturl = udocker.GetURL()
        geturl.set_proxy("http://host")
        self.assertEqual(geturl.http_proxy, "http://host")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLexeCurl')
    @mock.patch('udocker.GetURLpyCurl')
    def test_06_get(self, mock_gupycurl,
                    mock_guexecurl, mock_msg):
        """Test GetURL().get() generic get"""
        self._init()
        geturl = udocker.GetURL()
        self.assertRaises(TypeError, geturl.get)
        #
        geturl = udocker.GetURL()
        geturl._geturl = type('test', (object,), {})()
        geturl._geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLexeCurl')
    @mock.patch('udocker.GetURLpyCurl')
    def test_07_post(self, mock_gupycurl,
                     mock_guexecurl, mock_msg):
        """Test GetURL().post() generic post"""
        self._init()
        geturl = udocker.GetURL()
        self.assertRaises(TypeError, geturl.post)
        self.assertRaises(TypeError, geturl.post, "http://host")
        #
        geturl = udocker.GetURL()
        geturl._geturl = type('test', (object,), {})()
        geturl._geturl.get = self._get
        self.assertEqual(geturl.post("http://host",
                                     {"DATA": 1, }), "http://host")


class ChkSUMTestCase(unittest.TestCase):
    """Test ChkSUM() performs checksums portably"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    def _init(self):
        """Configure variables"""
        pass

    @mock.patch('udocker.hashlib.sha256')
    @mock.patch('udocker.Msg')
    def test_01_init(self, mock_msg, mock_hashlib_sha):
        """Test ChkSUM() constructor"""
        self._init()
        mock_hashlib_sha.return_value = True
        cksum = udocker.ChkSUM()
        self.assertEqual(cksum._sha256_call, cksum._hashlib_sha256)

    @mock.patch('udocker.Msg')
    def test_01_sha256(self, mock_msg):
        """Test ChkSUM().sha256()"""
        self._init()
        mock_call = mock.MagicMock()
        cksum = udocker.ChkSUM()
        #
        mock_call.return_value = True
        cksum._sha256_call = mock_call
        status = cksum.sha256("filename")
        self.assertTrue(status)
        #
        mock_call.return_value = False
        cksum._sha256_call = mock_call
        status = cksum.sha256("filename")
        self.assertFalse(status)

    @mock.patch('udocker.Msg')
    def test_02_hashlib_sha256(self, mock_msg):
        """Test ChkSUM()._hashlib_sha256()"""
        sha256sum = \
            "9ceece10cf8b97d1f1924dae5d14c137fd144ce999ede85f48be6d7582e2dd23"
        self._init()
        cksum = udocker.ChkSUM()
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='qwerty\n')):
            status = cksum._hashlib_sha256("filename")
            self.assertEqual(status, sha256sum)

    @mock.patch('udocker.subprocess.check_output')
    @mock.patch('udocker.Msg')
    def test_03_openssl_sha256(self, mock_msg, mock_subproc):
        """Test ChkSUM()._openssl_sha256()"""
        self._init()
        udocker.Msg = mock_msg
        udocker.Msg.return_value.chlderr = open("/dev/null", "w")
        udocker.Msg.chlderr = open("/dev/null", "w")
        mock_subproc.return_value = "123456 "
        cksum = udocker.ChkSUM()
        status = cksum._openssl_sha256("filename")
        self.assertEqual(status, "123456")


class NixAuthenticationTestCase(unittest.TestCase):
    """Test NixAuthentication() *nix authentication portably"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    def _init(self):
        """Configure variables"""
        pass

    def test_01_init(self):
        """Test NixAuthentication() constructor"""
        self._init()
        auth = udocker.NixAuthentication()
        self.assertEqual(auth.passwd_file, None)
        self.assertEqual(auth.group_file, None)
        #
        auth = udocker.NixAuthentication("passwd", "group")
        self.assertEqual(auth.passwd_file, "passwd")
        self.assertEqual(auth.group_file, "group")

    @mock.patch('udocker.pwd')
    def test_01__get_user_from_host(self, mock_pwd):
        """Test NixAuthentication()._get_user_from_host()"""
        self._init()
        usr = pwd.struct_passwd(["root", "*", "0", "0", "root usr",
                                 "/root", "/bin/bash"])
        mock_pwd.getpwuid.return_value = usr
        auth = udocker.NixAuthentication()
        (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host(0)
        self.assertEqual(name, usr.pw_name)
        self.assertEqual(uid, usr.pw_uid)
        self.assertEqual(gid, str(usr.pw_gid))
        self.assertEqual(gecos, usr.pw_gecos)
        self.assertEqual(_dir, usr.pw_dir)
        self.assertEqual(shell, usr.pw_shell)
        #
        mock_pwd.getpwnam.return_value = usr
        auth = udocker.NixAuthentication()
        (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host("root")
        self.assertEqual(name, usr.pw_name)
        self.assertEqual(uid, usr.pw_uid)
        self.assertEqual(gid, str(usr.pw_gid))
        self.assertEqual(gecos, usr.pw_gecos)
        self.assertEqual(_dir, usr.pw_dir)

    @mock.patch('udocker.pwd')
    def test_02__get_group_from_host(self, mock_pwd):
        """Test NixAuthentication()._get_group_from_host()"""
        self._init()
        hgr = grp.struct_group(["root", "*", "0", str([])])
        mock_pwd.getgrgid.return_value = hgr
        auth = udocker.NixAuthentication()
        (name, gid, mem) = auth._get_group_from_host(0)
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)
        #
        mock_pwd.getgrnam.return_value = hgr
        auth = udocker.NixAuthentication()
        (name, gid, mem) = auth._get_group_from_host("root")
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)

    def test_03__get_user_from_file(self):
        """Test NixAuthentication()._get_user_from_file()"""
        self._init()
        auth = udocker.NixAuthentication()
        auth.passwd_file = "passwd"
        passwd_line = StringIO('root:x:0:0:root:/root:/bin/bash')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = \
                lambda self: iter(passwd_line.readline, '')
            (name, uid, gid,
             gecos, _dir, shell) = auth._get_user_from_file("root")
            self.assertEqual(name, "root")
            self.assertEqual(uid, "0")
            self.assertEqual(gid, "0")
            self.assertEqual(gecos, "root")
            self.assertEqual(_dir, "/root")
            self.assertEqual(shell, "/bin/bash")
            #
        passwd_line = StringIO('root:x:0:0:root:/root:/bin/bash')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = \
                lambda self: iter(passwd_line.readline, '')
            (name, uid, gid,
             gecos, _dir, shell) = auth._get_user_from_file(0)
            self.assertEqual(name, "root")
            self.assertEqual(uid, "0")
            self.assertEqual(gid, "0")
            self.assertEqual(gecos, "root")
            self.assertEqual(_dir, "/root")
            self.assertEqual(shell, "/bin/bash")

    def test_04__get_group_from_file(self):
        """Test NixAuthentication()._get_group_from_file()"""
        self._init()
        auth = udocker.NixAuthentication()
        auth.passwd_file = "passwd"
        group_line = StringIO('root:x:0:a,b,c')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = \
                lambda self: iter(group_line.readline, '')
            (name, gid, mem) = auth._get_group_from_file("root")
            self.assertEqual(name, "root")
            self.assertEqual(gid, "0")
            self.assertEqual(mem, "a,b,c")
            #
        group_line = StringIO('root:x:0:a,b,c')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = \
                lambda self: iter(group_line.readline, '')
            (name, gid, mem) = auth._get_group_from_file(0)
            self.assertEqual(name, "root")
            self.assertEqual(gid, "0")
            self.assertEqual(mem, "a,b,c")

    def test_05_add_user(self):
        """Test NixAuthentication().add_user()"""
        self._init()
        auth = udocker.NixAuthentication()
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = auth.add_user("root", "pw", 0, 0, "gecos",
                                   "/home", "/bin/bash")
            self.assertTrue(status)

    def test_06_add_group(self):
        """Test NixAuthentication().add_group()"""
        self._init()
        auth = udocker.NixAuthentication()
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = auth.add_group("root", 0)
            self.assertTrue(status)

    @mock.patch('udocker.NixAuthentication._get_user_from_host')
    @mock.patch('udocker.NixAuthentication._get_user_from_file')
    def test_07_get_user(self, mock_file, mock_host):
        """Test NixAuthentication().get_user()"""
        self._init()
        auth = udocker.NixAuthentication()
        auth.passwd_file = ""
        auth.get_user("user")
        self.assertTrue(mock_host.called)
        self.assertFalse(mock_file.called)
        #
        mock_host.reset_mock()
        mock_file.reset_mock()
        auth.passwd_file = "passwd"
        auth.get_user("user")
        self.assertFalse(mock_host.called)
        self.assertTrue(mock_file.called)

    @mock.patch('udocker.NixAuthentication._get_group_from_host')
    @mock.patch('udocker.NixAuthentication._get_group_from_file')
    def test_08_get_group(self, mock_file, mock_host):
        """Test NixAuthentication().get_group()"""
        self._init()
        auth = udocker.NixAuthentication()
        auth.group_file = ""
        auth.get_group("group")
        self.assertTrue(mock_host.called)
        self.assertFalse(mock_file.called)
        #
        mock_host.reset_mock()
        mock_file.reset_mock()
        auth.group_file = "group"
        auth.get_group("group")
        self.assertFalse(mock_host.called)
        self.assertTrue(mock_file.called)


class ExecutionEngine(unittest.TestCase):
    """Test ExecutionEngine() parent class for containers execution"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    def _init(self):
        """Configure variables"""
        udocker.Config = type('test', (object,), {})()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        udocker.Config.cpu_affinity_exec_tools = ("taskset -c ", "numactl -C ")

    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local):
        """Test ExecutionEngine()"""
        self._init()
        ex_eng = udocker.ExecutionEngine(mock_local)
        self.assertEqual(ex_eng.container_id, "")
        self.assertEqual(ex_eng.container_root, "")
        self.assertEqual(ex_eng.container_names, [])
        self.assertEqual(ex_eng.opt["nometa"], False)
        self.assertEqual(ex_eng.opt["nosysdirs"], False)
        self.assertEqual(ex_eng.opt["dri"], False)
        self.assertEqual(ex_eng.opt["bindhome"], False)
        self.assertEqual(ex_eng.opt["hostenv"], False)
        self.assertEqual(ex_eng.opt["hostauth"], False)
        self.assertEqual(ex_eng.opt["novol"], [])
        self.assertEqual(ex_eng.opt["env"], [])
        self.assertEqual(ex_eng.opt["vol"], [])
        self.assertEqual(ex_eng.opt["cpuset"], "")
        self.assertEqual(ex_eng.opt["user"], "")
        self.assertEqual(ex_eng.opt["cwd"], "")
        self.assertEqual(ex_eng.opt["entryp"], "")
        self.assertEqual(ex_eng.opt["cmd"], udocker.Config.cmd)
        self.assertEqual(ex_eng.opt["hostname"], "")
        self.assertEqual(ex_eng.opt["domain"], "")
        self.assertEqual(ex_eng.opt["volfrom"], [])

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_02__check_exposed_ports(self, mock_local, mock_msg):
        """Test ExecutionEngine()._check_exposed_ports()"""
        self._init()
        ex_eng = udocker.ExecutionEngine(mock_local)
        status = ex_eng._check_exposed_ports(("1024", "2048/tcp", "23000/udp"))
        self.assertFalse(status)
        #
        status = ex_eng._check_exposed_ports(("1023", "2048/tcp", "23000/udp"))
        self.assertTrue(status)
        #
        status = ex_eng._check_exposed_ports(("1024", "80/tcp", "23000/udp"))
        self.assertTrue(status)
        #
        status = ex_eng._check_exposed_ports(("1024", "2048/tcp", "23/udp"))
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_03__set_cpu_affinity(self, mock_local, mock_futil):
        """Test ExecutionEngine()._set_cpu_affinity()"""
        self._init()
        ex_eng = udocker.ExecutionEngine(mock_local)
        mock_futil.return_value.find_exec.return_value = ""
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, " ")
        #
        mock_futil.return_value.find_exec.return_value = "/bin/taskset"
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, " ")
        #
        mock_futil.return_value.find_exec.return_value = "/bin/taskset"
        ex_eng.opt["cpuset"] = "1-2"
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, " /bin/taskset -C  '1-2' ")

    @mock.patch('udocker.LocalRepository')
    def test_04__is_in_volumes(self, mock_local):
        """Test ExecutionEngine()._is_in_volumes()"""
        self._init()
        ex_eng = udocker.ExecutionEngine(mock_local)
        ex_eng.opt["vol"] = ("/opt/xxx:/mnt", )
        status = ex_eng._is_in_volumes("/opt")
        self.assertTrue(status)
        #
        ex_eng.opt["vol"] = ("/var/xxx:/mnt", )
        status = ex_eng._is_in_volumes("/opt")
        self.assertFalse(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.ExecutionEngine._is_in_volumes')
    @mock.patch('udocker.ExecutionEngine._getenv')
    @mock.patch('udocker.LocalRepository')
    def test_05__check_paths(self, mock_local, mock_getenv, mock_isinvol,
                             mock_exists, mock_isdir, mock_msg):
        """Test ExecutionEngine()._check_paths()"""
        self._init()
        ex_eng = udocker.ExecutionEngine(mock_local)
        mock_getenv.return_value = ""
        mock_isinvol.return_value = False
        mock_exists.return_value = False
        mock_isdir.return_value = False
        ex_eng.opt["uid"] = "0"
        ex_eng.opt["cwd"] = ""
        ex_eng.opt["home"] = "/home/user"
        status = ex_eng._check_paths("/containers/123/ROOT")
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["env"][-1],
                         "PATH=/usr/sbin:/sbin:/usr/bin:/bin")
        self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])
        #
        ex_eng.opt["uid"] = "1000"
        status = ex_eng._check_paths("/containers/123/ROOT")
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["env"][-1],
                         "PATH=/usr/bin:/bin")
        self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        status = ex_eng._check_paths("/containers/123/ROOT")
        self.assertTrue(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.access')
    @mock.patch('udocker.os.readlink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.ExecutionEngine._getenv')
    @mock.patch('udocker.LocalRepository')
    def test_06__check_executable(self, mock_local, mock_getenv,
                                  mock_exists, mock_islink, mock_isfile,
                                  mock_readlink, mock_access, mock_msg):
        """Test ExecutionEngine()._check_executable()"""
        self._init()
        ex_eng = udocker.ExecutionEngine(mock_local)
        mock_getenv.return_value = ""
        ex_eng.opt["entryp"] = "/bin/shell -x -v"
        mock_islink.return_value = False
        mock_exists.return_value = False
        status = ex_eng._check_executable("/containers/123/ROOT")
        self.assertFalse(status)
        #
        mock_islink.return_value = False
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_access.return_value = True
        status = ex_eng._check_executable("/containers/123/ROOT")
        self.assertTrue(status)
        #
        ex_eng.opt["entryp"] = ["/bin/shell", "-x", "-v"]
        ex_eng.opt["cmd"] = ""
        status = ex_eng._check_executable("/containers/123/ROOT")
        self.assertEqual(ex_eng.opt["cmd"], ex_eng.opt["entryp"])
        #
        ex_eng.opt["entryp"] = ["/bin/shell", ]
        ex_eng.opt["cmd"] = ["-x", "-v"]
        status = ex_eng._check_executable("/containers/123/ROOT")
        self.assertEqual(ex_eng.opt["cmd"], ["/bin/shell", "-x", "-v"])

    @mock.patch('udocker.ContainerStructure')
    @mock.patch('udocker.ExecutionEngine._check_exposed_ports')
    @mock.patch('udocker.ExecutionEngine._getenv')
    @mock.patch('udocker.LocalRepository')
    def test_07__run_load_metadata(self, mock_local, mock_getenv,
                                   mock_chkports, mock_cstruct):
        """Test ExecutionEngine()._run_load_metadata()"""
        self._init()
        ex_eng = udocker.ExecutionEngine(mock_local)
        mock_getenv.return_value = ""
        udocker.Config.location = "/tmp/container"
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("", []))
        #
        udocker.Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("", [])
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, (None, None))
        #
        udocker.Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("/x", [])
        ex_eng.opt["nometa"] = True
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))
        #
        udocker.Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("/x", [])
        ex_eng.opt["nometa"] = False
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))

    @mock.patch('udocker.LocalRepository')
    def test_08__getenv(self, mock_local):
        """Test ExecutionEngine()._getenv()"""
        self._init()
        ex_eng = udocker.ExecutionEngine(mock_local)
        ex_eng.opt["env"] = ["HOME=/home/user", "PATH=/bin:/usr/bin"]
        status = ex_eng._getenv("")
        self.assertEqual(status, None)
        #
        status = ex_eng._getenv("XXX")
        self.assertEqual(status, None)
        #
        status = ex_eng._getenv("HOME")
        self.assertEqual(status, "/home/user")
        #
        status = ex_eng._getenv("PATH")
        self.assertEqual(status, "/bin:/usr/bin")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_09__uid_gid_from_str(self, mock_local, mock_msg):
        """Test ExecutionEngine()._uid_gid_from_str()"""
        self._init()
        ex_eng = udocker.ExecutionEngine(mock_local)
        status = ex_eng._uid_gid_from_str("")
        self.assertEqual(status, (None, None))
        #
        status = ex_eng._uid_gid_from_str("0:0")
        self.assertEqual(status, ('0', '0'))
        #
        status = ex_eng._uid_gid_from_str("100:100")
        self.assertEqual(status, ('100', '100'))


if __name__ == '__main__':
    unittest.main()
