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
import mock
import unittest
import subprocess
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

__author__ = "udocker@lip.pt"
__credits__ = ["PRoot http://proot.me"]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "0.0.1-1"
__date__ = "2016"

try:
    import udocker
except ImportError:
    sys.path.append(".")
    sys.path.append("..")
    import udocker

STDOUT = sys.stdout
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

        self.assertIsInstance(conf.def_topdir, str)
        self.assertIsInstance(conf.config_file, str)

        self.assertIsInstance(conf.tmpdir, str)
        self.assertIsInstance(conf.tmptrash, dict)

        self.assertIsInstance(conf.tarball_url, str)

        self.assertIsInstance(conf.osver, str)
        self.assertIsInstance(conf.arch, str)
        self.assertIsInstance(conf.proot_exec, str)
        self.assertIsInstance(conf.kernel, str)

        self.assertIsInstance(conf.cmd, list)
        self.assertIsInstance(conf.sysdirs_list, tuple)
        self.assertIsInstance(conf.hostauth_list, tuple)
        self.assertIsInstance(conf.dri_list, tuple)
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
        arch = conf._sysarch()
        self.assertEqual("amd64", arch, "Config._sysarch x86_64")
        mock_platform.machine.return_value = "i586"
        arch = conf._sysarch()
        self.assertEqual("i386", arch, "Config._sysarchi i586")
        mock_platform.machine.return_value = "xpto"
        arch = conf._sysarch()
        self.assertEqual("", arch, "Config._sysarchi i586")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileUtil')
    def test_03_user_init_good(self, mock_fileutil, mock_msg):
        """Test Config.user_init() with good data"""
        udocker.msg = mock_msg
        conf = udocker.Config()
        mock_fileutil.return_value.size.return_value = 10
        conf_data = '# comment\nverbose_level = 100\n'
        conf_data += 'tmpdir = "/xpto"\ncmd = ["/bin/ls", "-l"]\n'
        mock_fileutil.return_value.getdata.return_value = conf_data
        status = conf.user_init("filename.conf")
        self.assertTrue(status, "Config.user_init good config")
        self._verify_config(conf)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileUtil')
    def test_04_user_init_bad(self, mock_fileutil, mock_msg):
        """Test Config.user_init() with bad config data"""
        udocker.msg = mock_msg
        conf = udocker.Config()
        conf_data = 'hh +=* ffhdklfh\n'
        mock_fileutil.return_value.size.return_value = 10
        mock_fileutil.return_value.getdata.return_value = conf_data
        status = conf.user_init("filename.conf")
        self.assertFalse(status, "Config.user_init bad config")


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
        self.assertTrue(is_writable_file(msg.stdout))
        self.assertTrue(is_writable_file(msg.stderr))

    def test_01_init(self):
        """Test Msg() constructor"""
        msg = udocker.Msg(0)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 0)
        msg.nullfp.close()

    def test_02_setlevel(self):
        """Test Msg.setlevel() change of log level"""
        msg = udocker.Msg(5)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 5)
        msg.nullfp.close()
        msg = udocker.Msg(0)
        msg.setlevel(7)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 7)
        msg.nullfp.close()

    @mock.patch('udocker.sys.stdout', new_callable=StringIO)
    def test_03_out(self, mock_stdout):
        """Test Msg.out() screen messages"""
        msg = udocker.Msg(0)
        msg.out("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stdout.getvalue())
        sys.stdout = STDOUT
        msg.nullfp.close()


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
        udocker.conf = mock_config
        futil = udocker.FileUtil("filename.txt")
        self.assertEqual(futil.filename, "filename.txt")
        self.assertTrue(udocker.conf.tmpdir)
        self.assertTrue(udocker.conf.def_topdir)

    def test_02_mktmp(self):
        """Test FileUtil.mktmp()"""
        udocker.conf.tmpdir = "/somewhere"
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

    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.FileUtil.uid')
    def test_04_remove_file(self, mock_uid, mock_isfile,
                            mock_islink, mock_remove):
        """Test FileUtil.remove() with plain files"""
        mock_uid.return_value = os.getuid()
        mock_isfile.return_value = True
        # under /tmp
        futil = udocker.FileUtil("/tmp/filename4.txt")
        futil.topdir = "/home/user/.udocker"
        futil.tmpdir = "/tmp"
        status = futil.remove()
        self.assertTrue(status)
        # under user home
        futil = udocker.FileUtil("/home/user/.udocker/filename4.txt")
        futil.topdir = "/home/user/.udocker"
        futil.tmpdir = "/tmp"
        status = futil.remove()
        self.assertTrue(status)
        # outside of scope 1
        futil = udocker.FileUtil("/etc/filename4.txt")
        futil.topdir = "/home/user/.udocker"
        futil.tmpdir = "/tmp"
        status = futil.remove()
        self.assertFalse(status)

    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.FileUtil.uid')
    def test_05_remove_dir(self, mock_uid, mock_isfile, mock_islink,
                           mock_isdir, mock_call):
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

    @mock.patch('udocker.msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isfile')
    def test_06_verify_tar01(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file"""
        mock_msg.level = 0
        mock_isfile.return_value = False
        mock_call.return_value = 0
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertFalse(status)

    @mock.patch('udocker.msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isfile')
    def test_07_verify_tar02(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file"""
        mock_msg.level = 0
        mock_isfile.return_value = True
        mock_call.return_value = 0
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertTrue(status)

    @mock.patch('udocker.msg')
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
        udocker.conf = mock_config
        udocker.conf.tmptrash = {'file1.txt': None, 'file2.txt': None}
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
        udocker.conf = mock_config
        udocker.conf.tmpdir = "/tmp"
        udocker.conf.proot_exec = "proot"
        localrepo = mock_localrepo
        localrepo.bindir = "/bindir"
        utools = udocker.UdockerTools(localrepo)
        self.assertEqual(utools.localrepo, localrepo)
        self.assertEqual(utools.tmpdir, "/tmp")
        self.assertEqual(utools.proot, "/bindir/proot")

    @mock.patch('udocker.UdockerTools.__init__')
    @mock.patch('udocker.os.path.exists')
    def test_02_is_available(self, mock_exists, mock_init):
        """Test UdockerTools.is_available() is already downloaded"""
        # available
        mock_exists.return_value = True
        mock_init.return_value = None
        utools = udocker.UdockerTools(None)
        utools.proot = "/bindir/proot"
        status = utools.is_available()
        self.assertTrue(status)
        # not available
        mock_exists.return_value = False
        mock_init.return_value = None
        utools = udocker.UdockerTools(None)
        utools.proot = "/bindir/proot"
        status = utools.is_available()
        self.assertFalse(status)

    @mock.patch('udocker.msg')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.UdockerTools.__init__')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.FileUtil.mktmp')
    @mock.patch.object(udocker.UdockerTools, 'is_available')
    def test_03_download(self, mock_is, mock_mktmp, mock_geturl, mock_call,
                         mock_fileutil, mock_init, mock_localrepo, mock_msg):
        """Test UdockerTools.download()"""
        mock_msg.level = 0
        mock_fileutil.return_value.mktmp.return_value = "filename_tmp"
        mock_init.return_value = None
        utools = udocker.UdockerTools(mock_localrepo)
        utools.localrepo = mock_localrepo
        utools.curl = mock_geturl
        utools.tarball_url = "http://node.domain/filename.tgz"
        utools.localrepo.topdir = "/home/user/.udocker"
        utools.proot = "/"
        hdr = udocker.CurlHeader()
        # IS AVAILABLE NO DOWNLOAD
        mock_is.return_value = True
        mock_geturl.get.return_value = (hdr, None)
        status = utools.download()
        self.assertTrue(status)
        # GetURL returns OK, untar returns OK
        mock_is.return_value = False
        utools.proot = "fhkljfgsakfgjkasgf"
        mock_geturl.get.return_value = (hdr, None)
        mock_call.return_value = 0
        status = utools.download()
        self.assertTrue(status)
        # GetURL returns NOT OK
        mock_is.return_value = False
        mock_geturl.get.return_value = (hdr, None)
        mock_call.return_value = 0
        status = utools.download()
        self.assertTrue(status)
        # GetURL returns OK, untar returns NOT OK
        mock_is.return_value = False
        mock_geturl.get.return_value = (hdr, None)
        mock_call.return_value = 1
        status = utools.download()
        self.assertFalse(status)


class LocalRepositoryTestCase(unittest.TestCase):
    """Test LocalRepositoryTestCase() management of local repository
    of container images and extracted containers
    """

    def _localrepo(self, topdir):
        """Instantiate a local repository class"""
        topdir_path = os.getenv("HOME") + "/" + topdir
        udocker.conf = mock.patch('udocker.Config').start()
        udocker.conf.tmpdir = "/tmp"
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
        self.assertTrue(localrepo.def_reposdir)
        self.assertTrue(localrepo.def_layersdir)
        self.assertTrue(localrepo.def_containersdir)
        self.assertTrue(localrepo.def_bindir)
        self.assertTrue(localrepo.def_libdir)
        self.assertTrue(localrepo.reposdir)
        self.assertTrue(localrepo.layersdir)
        self.assertTrue(localrepo.containersdir)
        self.assertTrue(localrepo.bindir)
        self.assertTrue(localrepo.libdir)
        self.assertTrue(localrepo.tmpdir)
        self.assertEqual(localrepo.tmpdir, udocker.conf.tmpdir)
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
        self.assertTrue(os.path.exists(localrepo.tmpdir))
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

    def test_11_unprotect_container(self):
        """Test LocalRepository().isprotected_container()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch('os.remove') as mremove:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            localrepo.unprotect_container(container_id)
            self.assertTrue(mremove.called)
            self.assertEqual(mremove.call_args, mock.call('/PROTECT'))

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

    def test_14_unprotect_imagerepo(self):
        """Test LocalRepository().isprotected_imagerepo()"""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch('os.remove') as mremove:
            localrepo.unprotect_imagerepo("IMAGE", "TAG")
            self.assertTrue(mremove.called)
            protect = localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mremove.call_args, mock.call(protect))

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

    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.os.path.exists')
    def test_16_del_container_name(self, mock_exists, mock_remove):
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

    @mock.patch('udocker.os.remove')
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
        self.assertTrue(status)
        #
        mock_exists.return_value = False
        status = localrepo.setup_imagerepo("IMAGE")
        expected_directory = localrepo.reposdir + "/IMAGE"
        self.assertTrue(mock_makedirs.called)
        self.assertEqual(localrepo.cur_repodir, expected_directory)
        self.assertTrue(status)

if __name__ == '__main__':
    unittest.main()()
