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
from StringIO import StringIO
try:
    import udocker
except ImportError:
    sys.path.append("..")
    import udocker

__author__ = "udocker@lip.pt"
__credits__ = ["PRoot http://proot.me"]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "0.0.1-1"
__date__ = "2016"

STDOUT = sys.stdout


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


class ConfigTestCase(unittest.TestCase):
    """Test case for the udocker configuration"""

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

    def test_init(self):
        """Test Config() constructor"""
        conf = udocker.Config()
        self._verify_config(conf)

    # pylint: disable=protected-access
    @mock.patch('udocker.platform')
    def test_platform(self, mock_platform):
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
    def test_user_init_good(self, mock_fileutil, mock_msg):
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
    def test_user_init_bad(self, mock_fileutil, mock_msg):
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

    def _verify_descriptors(self, msg):
        """Verify Msg() file descriptors"""
        self.assertIsInstance(msg.chlderr, file)
        self.assertIsInstance(msg.chldout, file)
        self.assertIsInstance(msg.chldnul, file)
        self.assertIsInstance(msg.stdout, file)
        self.assertIsInstance(msg.stderr, file)

    @mock.patch('__builtin__.open')
    def test_init(self, mock_open):
        """Test Msg() constructor"""
        mock_open.return_value = sys.stdin
        msg = udocker.Msg()
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 0)

    @mock.patch('__builtin__.open')
    def test_setlevel(self, mock_open):
        """Test Msg.setlevel() change of log level"""
        mock_open.return_value = sys.stdin
        msg = udocker.Msg(5)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 5)
        msg = udocker.Msg(0)
        msg.setlevel(7)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 7)

    @mock.patch('udocker.sys.stdout', new_callable=StringIO)
    def test_out(self, mock_stdout):
        """Test Msg.out() screen messages"""
        msg = udocker.Msg(0)
        msg.out("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stdout.getvalue())
        sys.stdout = STDOUT


class UniqueTestCase(unittest.TestCase):
    """Test Unique() class"""

    def test_init(self):
        """Test Unique() constructor"""
        uniq = udocker.Unique()
        self.assertEqual(uniq.def_name, "udocker")

    # pylint: disable=protected-access
    def test_rnd(self):
        """Test Unique._rnd()"""
        uniq = udocker.Unique()
        rand = uniq._rnd(64)
        self.assertIsInstance(rand, str)
        self.assertEqual(len(rand), 64)

    def test_uuid(self):
        """Test Unique.uuid()"""
        uniq = udocker.Unique()
        rand = uniq.uuid("zxcvbnm")
        self.assertEqual(len(rand), 36)
        rand = uniq.uuid(789)
        self.assertEqual(len(rand), 36)

    def test_imagename(self):
        """Test Unique.imagename()"""
        uniq = udocker.Unique()
        rand = uniq.imagename()
        self.assertEqual(len(rand), 16)

    def test_layer_v1(self):
        """Test Unique.layer_v1()"""
        uniq = udocker.Unique()
        rand = uniq.layer_v1()
        self.assertEqual(len(rand), 64)

    def test_filename(self):
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

    @mock.patch('udocker.Config')
    def test_init(self, mock_config):
        """Test FileUtil() constructor"""
        udocker.conf = mock_config
        futil = udocker.FileUtil("filename.txt")
        self.assertEqual(futil.filename, "filename.txt")
        self.assertTrue(udocker.conf.tmpdir)
        self.assertTrue(udocker.conf.def_topdir)

    def test_mktmp(self):
        """Test FileUtil.mktmp()"""
        udocker.conf.tmpdir = "/somewhere"
        tmp_file = udocker.FileUtil("filename2.txt").mktmp()
        self.assertTrue(tmp_file.endswith("-filename2.txt"))
        self.assertTrue(tmp_file.startswith("/somewhere/udocker-"))
        self.assertGreater(len(tmp_file.strip()), 68)

    @mock.patch('udocker.os.stat')
    def test_uid(self, mock_stat):
        """Test FileUtil.uid()"""
        mock_stat.return_value.st_uid = 1234
        uid = udocker.FileUtil("filename3.txt").uid()
        self.assertEqual(uid, 1234)

    # pylint: disable=unused-argument
    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.FileUtil.uid')
    def test_remove_file(self, mock_uid, mock_isfile,
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

    # pylint: disable=too-many-arguments
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.FileUtil.uid')
    def test_remove_dir(self, mock_uid, mock_isfile, mock_islink,
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

    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isfile')
    def test_verify_tar(self, mock_isfile, mock_call):
        """Test FileUtil.verify_tar() check tar file"""
        # NOT A FILE
        mock_isfile.return_value = False
        mock_call.return_value = 0
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertFalse(status)
        # IS FILE and TAR OK
        mock_isfile.return_value = True
        mock_call.return_value = 0
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertTrue(status)
        # IS FILE and TAR FAIL
        mock_isfile.return_value = True
        mock_call.return_value = 1
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertFalse(status)

    @mock.patch('udocker.Config')
    @mock.patch('udocker.FileUtil.remove')
    def test_cleanup(self, mock_remove, mock_config):
        """Test FileUtil.cleanup() delete tmp files"""
        udocker.conf = mock_config
        udocker.conf.tmptrash = {'file1.txt': None, 'file2.txt': None}
        udocker.FileUtil("").cleanup()
        self.assertEqual(mock_remove.call_count, 2)

    @mock.patch('udocker.os.path.isdir')
    def test_isdir(self, mock_isdir):
        """Test FileUtil.isdir()"""
        # is dir
        mock_isdir.return_value = True
        status = udocker.FileUtil("somedir").isdir()
        self.assertTrue(status)
        # not a dir
        mock_isdir.return_value = False
        status = udocker.FileUtil("somedir").isdir()
        self.assertFalse(status)

    @mock.patch('udocker.os.stat')
    def test_size(self, mock_stat):
        """Test FileUtil.size() get file size"""
        mock_stat.return_value.st_size = 4321
        size = udocker.FileUtil("somefile").size()
        self.assertEqual(size, 4321)

    def test_getdata(self):
        """Test FileUtil.size() get file content"""
        with mock.patch('__builtin__.open',
                        mock.mock_open(read_data='qwerty')):
            data = udocker.FileUtil("somefile").getdata()
            self.assertEqual(data, 'qwerty')

    # pylint: disable=unused-argument
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.FileUtil.remove')
    @mock.patch('udocker.FileUtil.getdata')
    @mock.patch('udocker.FileUtil.mktmp')
    def test_find_exec(self, mock_mktmp, mock_getdata, mock_remove, mock_call):
        """Test FileUtil.find_exec() find executable"""
        mock_mktmp.return_value.mktmp.return_value = "/tmp/tmpfile"
        with mock.patch('__builtin__.open', mock.mock_open()):
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
    def test_find_inpath(self, mock_exists):
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

    def test_copyto(self):
        """Test FileUtil.copyto() file copy"""
        with mock.patch('__builtin__.open', mock.mock_open()):
            status = udocker.FileUtil("source").copyto("dest")
            self.assertTrue(status)
            status = udocker.FileUtil("source").copyto("dest", "w")
            self.assertTrue(status)
            status = udocker.FileUtil("source").copyto("dest", "a")
            self.assertTrue(status)


class UdockerToolsTestCase(unittest.TestCase):
    """Test UdockerTools() download and setup of tools needed by udocker"""

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.Config')
    def test_init(self, mock_config, mock_localrepo):
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
    def test_is_available(self, mock_exists, mock_init):
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

    # pylint: disable=too-many-arguments,unused-argument
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.UdockerTools.__init__')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.FileUtil.mktmp')
    def test_download(self, mock_mktmp, mock_geturl, mock_call,
                      mock_fileutil, mock_init, mock_localrepo):
        """Test UdockerTools.download()"""
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
        mock_geturl.get.return_value = (hdr, None)
        status = utools.download()
        self.assertTrue(status)
        # GetURL returns OK, untar returns OK
        utools.proot = "fhkljfgsakfgjkasgf"
        mock_geturl.get.return_value = (hdr, None)
        mock_call.return_value = 0
        status = utools.download()
        self.assertTrue(status)
        # GetURL returns NOT OK
        mock_geturl.get.return_value = (hdr, None)
        mock_call.return_value = 0
        status = utools.download()
        self.assertTrue(status)
        # GetURL returns OK, untar returns NOT OK
        mock_geturl.get.return_value = (hdr, None)
        mock_call.return_value = 1
        status = utools.download()
        self.assertFalse(status)


class MainTestCase(unittest.TestCase):
    """Test most udocker capabilities"""

    # pylint: disable=unused-argument,too-many-arguments
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.UdockerTools')
    @mock.patch('udocker.Config.user_init')
    @mock.patch('udocker.import_modules')
    @mock.patch('udocker.Msg')
    def test_init(self, mock_msg, mock_import_modules,
                  mock_user_init, mock_utools, mock_localrepo):
        """Test udocker global command line options"""
        udocker.msg = mock_msg
        udocker.conf = udocker.Config()
        t_argv = ['./udocker.py']
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main()
            self.assertTrue(mock_import_modules.called)
        t_argv = ['./udocker.py', "images"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main()
            self.assertTrue(mock_import_modules.called)
        t_argv = ['./udocker.py', "--config=/myconf"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main()
            self.assertTrue(mock_import_modules.called)
            self.assertTrue(mock_user_init.called_with("/myconf"))
        t_argv = ['./udocker.py', "--cofig=/myconf"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main()
            self.assertTrue(mock_import_modules.called)
            self.assertTrue(mock_user_init.called_with(False))
        udocker.conf.verbose_level = 0
        t_argv = ['./udocker.py', "-D"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main()
            self.assertTrue(mock_import_modules.called)
            self.assertEqual(udocker.conf.verbose_level, 3)
        udocker.conf.verbose_level = 0
        t_argv = ['./udocker.py', "--debug"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main()
            self.assertTrue(mock_import_modules.called)
            self.assertEqual(udocker.conf.verbose_level, 3)
        t_argv = ['./udocker.py', "--insecure"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main()
            self.assertTrue(mock_import_modules.called)
            self.assertEqual(udocker.conf.http_insecure, True)
        t_argv = ['./udocker.py', "--repo=/home/user/.udocker"]
        with mock.patch.object(sys, 'argv', t_argv):
            udocker.Main()
            self.assertTrue(mock_import_modules.called)
            self.assertEqual(udocker.conf.def_topdir, "/home/user/.udocker")

    # pylint: disable=unused-argument
    @mock.patch('udocker.UdockerTools')
    @mock.patch('udocker.Msg')
    def test_execute_help(self, mock_msg, mock_utools):
        """Test udocker help command"""
        udocker.msg = mock_msg
        udocker.conf = udocker.Config()
        t_argv = ['./udocker.py', "--help"]
        with mock.patch.object(sys, 'argv', t_argv):
            main = udocker.Main()
            main.execute()
            find_str(self, "Examples", mock_msg.out.call_args)

    # pylint: disable=unused-argument
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.UdockerTools')
    @mock.patch('udocker.Msg')
    def test_do_search(self, mock_msg, mock_utools, mock_dockerioapi):
        """Test udocker search command"""
        udocker.msg = mock_msg
        udocker.conf = udocker.Config()
        t_argv = ['./udocker.py', "search", "-a", "iscampos"]
        with mock.patch.object(sys, 'argv', t_argv):
            mock_dockerioapi.return_value.search_get_page.side_effect = [
                {u'num_results': 2, u'results': [
                    {u'is_automated': False, u'name': u'iscampos/openqcd',
                     u'star_count': 0, u'is_trusted': False,
                     u'is_official': False,
                     u'description': u'Containers for openQCD v1.4'},
                    {u'is_automated': False, u'name': u'iscampos/codemaster',
                     u'star_count': 0, u'is_trusted': False,
                     u'is_official': False, u'description': u''}],
                 u'page_size': 25, u'query': u'iscampos',
                 u'num_pages': '1', u'page': u'0'},
                {u'num_results': 2, u'results': [
                    {u'is_automated': False, u'name': u'iscampos/openqcd',
                     u'star_count': 0, u'is_trusted': False,
                     u'is_official': False,
                     u'description': u'Containers for openQCD v1.4'},
                    {u'is_automated': False, u'name': u'iscampos/codemaster',
                     u'star_count': 0, u'is_trusted': False,
                     u'is_official': False, u'description': u''}],
                 u'page_size': 25, u'query': u'iscampos',
                 u'num_pages': '1', u'page': u'1'}]
            main = udocker.Main()
            main.execute()
            find_str(self, "iscampos/codemaster", mock_msg.out.call_args)

    # pylint: disable=unused-argument
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.UdockerTools')
    @mock.patch('udocker.Msg')
    def test_do_images(self, mock_msg, mock_utools, mock_localrepo):
        """Test udocker images command"""
        udocker.msg = mock_msg
        udocker.conf = udocker.Config()
        mock_localrepo.return_value.cd_imagerepo.return_value = \
            "/home/user/.udocker/repos/X/latest"
        mock_localrepo.return_value.get_imagerepos.return_value = [
            ('iscampos/openqcd', 'latest'), ('busybox', 'latest')]
        t_argv = ['./udocker.py', "images"]
        with mock.patch.object(sys, 'argv', t_argv):
            # Unprotected
            mock_localrepo.return_value.isprotected_imagerepo\
                .return_value = False
            main = udocker.Main()
            main.execute()
            msg_out = ("busybox:latest"
                       "                                               .")
            find_str(self, msg_out, mock_msg.out.call_args)
            # Protected
            mock_localrepo.return_value.isprotected_imagerepo\
                .return_value = True
            main.execute()
            msg_out = ("busybox:latest"
                       "                                               P")
            find_str(self, msg_out, mock_msg.out.call_args)
        t_argv = ['./udocker.py', "images", "-l"]
        with mock.patch.object(sys, 'argv', t_argv):
            main = udocker.Main()
            main.execute()
            msg_out = "  /home/user/.udocker/repos/X/latest"
            find_str(self, msg_out, mock_msg.out.call_args)
            #
            mock_localrepo.return_value.get_imagerepos.return_value = [
                ('busybox', 'latest')]
            mock_localrepo.return_value.get_layers.return_value = [
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 'sha256:385e281300cc6d88bdd155e0931fbdfbb1801c2b' +
                 '0265340a40481ee2b733ae66', 675992),
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 '56ed16bd6310cca65920c653a9bb22de6b235990dcaa174' +
                 '2ff839867aed730e5.layer', 675992),
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 '56ed16bd6310cca65920c653a9bb22de6b235990dcaa174' +
                 '2ff839867aed730e5.json', 1034),
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 'bc744c4ab376115cc45c610d53f529dd2d4249ae6b35e5d' +
                 '6e7a96e58863545aa.json', 1155),
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 'bc744c4ab376115cc45c610d53f529dd2d4249ae6b35e5d' +
                 '6e7a96e58863545aa.layer', 32),
                ('/home/jorge/.udocker/repos/busybox/latest/' +
                 'sha256:a3ed95caeb02ffe68cdd9fd84406680ae93d633c' +
                 'b16422d00e8a7c22955b46d4', 32)]
            main.execute()
            msg_out = '    /home/jorge/.udocker/repos/busybox/latest/' +\
                'sha256:a3ed95caeb02ffe68cdd9fd84406680ae93d633cb16' +\
                '422d00e8a7c22955b46d4 (1 MB)'
            find_str(self, msg_out, mock_msg.out.call_args)


if __name__ == '__main__':
    unittest.main()
