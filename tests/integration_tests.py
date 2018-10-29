#!/usr/bin/env python2
"""
=========================
udocker integration tests
=========================
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
import re
import sys
import uuid
import pwd
import unittest
import mock

__author__ = "udocker@lip.pt"
__credits__ = ["PRoot http://proot.me",
               "runC https://runc.io",
               "Fakechroot https://github.com/dex4er/fakechroot"
              ]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "1.1.0"
__date__ = "2016"

try:
    import udocker
except ImportError:
    sys.path.append(".")
    sys.path.append("..")
    import udocker

STDOUT = sys.stdout
DEVNULL = open("/dev/null", "w")
UDOCKER = "udocker.py"


def set_env():
    """Set environment variables"""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()
    return os.getenv("HOME")

HOME = set_env()

def match_str(find_exp, where):
    """find_exp regexp is present in buffer where"""
    for item in where:
        if re.search(find_exp, str(item)):
            return True
    return False

def not_match_str(find_exp, where):
    """find_exp regexp is not present in buffer where"""
    return not match_str(find_exp, where)


def find_str(find_exp, where):
    """find_exp is present in buffer where"""
    for item in where:
        if find_exp in str(item):
            return True
    return False


def choose_find(expect_prefix):
    """Choose which find method to use"""
    if expect_prefix == '=':
        find = match_str
    elif expect_prefix == '!':
        find = not_match_str
    else:
        find = find_str
    return find


def set_msglevels(mock_msg):
    """Set mock Msg() class message levels"""
    mock_msg.ERR = 0
    mock_msg.MSG = 1
    mock_msg.WAR = 2
    mock_msg.INF = 3
    mock_msg.VER = 4
    mock_msg.DBG = 5
    mock_msg.DEF = 3


def open_outfile(outfile):
    """Open file to collect stdout and stderr"""
    out_fd = os.open(outfile, os.O_WRONLY | os.O_CREAT)
    orig_stdout_fd = os.dup(1)
    orig_stderr_fd = os.dup(2)
    os.dup2(out_fd, 1)
    os.dup2(out_fd, 2)
    os.close(out_fd)
    return (orig_stdout_fd, orig_stderr_fd)


def close_outfile(orig_stdout_fd, orig_stderr_fd):
    """Close outfile and restore stdout and stderr"""
    sys.stderr.flush()
    sys.stdout.flush()
    out_fd = os.dup(1)
    os.dup2(orig_stdout_fd, 1)
    os.dup2(orig_stderr_fd, 2)
    os.close(out_fd)


def do_cmd(self, mock_msg, t_argv, expect_msg=None, outfile=None, debug=False):
    """Execute a udocker command as called in the command line"""
    set_msglevels(mock_msg)
    udocker.Msg = mock_msg
    udocker.Config()
    with mock.patch.object(sys, 'argv', t_argv):
        main = udocker.Main()
        udocker.Msg.chlderr = DEVNULL
        udocker.Msg.chldout = DEVNULL
        udocker.Msg.chldnul = DEVNULL
        udocker.Msg.level = 3
        udocker.Config.verbose_level = 3
        if outfile:
            (orig_stdout_fd, orig_stderr_fd) = open_outfile(outfile)
        status = main.start()  # start
        if outfile:
            close_outfile(orig_stdout_fd, orig_stderr_fd)
        if debug and expect_msg:
            print "out:" + str(mock_msg.return_value.out.call_args_list)
            print "err:" + str(mock_msg.return_value.err.call_args_list)
        if expect_msg is None and outfile is None:
            self.assertFalse(status, str(t_argv))
            return False
        elif expect_msg:
            find = choose_find(expect_msg[:1])
            if (find(expect_msg[1:],
                     mock_msg.return_value.out.call_args_list) or
                    find(expect_msg[1:],
                         mock_msg.return_value.err.call_args_list)):
                self.assertTrue(True, str(t_argv))
                return True
            else:
                self.assertTrue(False, str(t_argv))
                return False
        else:
            self.assertTrue(True, str(t_argv))
            return True


def do_run(self, mock_msg, t_argv, expect_msg=None, expect_out=None,
           debug=False):
    """Execute run a command and capture stdout"""
    output_file = str(uuid.uuid4())
    status = do_cmd(self, mock_msg, t_argv, expect_msg, output_file, debug)
    if status and expect_out:
        find = choose_find(expect_out[:1])
        with open(output_file) as output_fp:
            output = output_fp.read()
            if debug:
                print "file:" + str(output)
            if not find(expect_out[1:], [output]):
                self.assertTrue(False, str(t_argv))
                return False
    os.remove(output_file)
    return status


def do_action(t_argv):
    """Execute an action not part of a test i.e. setup and cleanup"""
    with mock.patch('udocker.Msg') as mock_msg:
        set_msglevels(mock_msg)
        udocker.Msg = mock_msg
        udocker.Config()
        with mock.patch.object(sys, 'argv', t_argv):
            main = udocker.Main()
            udocker.Msg.level = 3
            udocker.Config.verbose_level = 3
            return main.start()


def image_not_exists(image="busybox:latest"):
    """Check is the container image exists"""
    return do_action([UDOCKER, "inspect", image])


def container_not_exists(container="busyTEST"):
    """Check is the container exists"""
    return do_action([UDOCKER, "inspect", "-p", container])


class FuncTestBasic(unittest.TestCase):
    """Test basic capabilities, help and other simple commands"""

    @classmethod
    def setUpClass(cls):
        """Setup test"""
        set_env()

    @classmethod
    def tearDownClass(cls):
        """Cleanup test"""
        udocker.FileUtil().cleanup()

    def tearDown(self):
        """Cleanup test"""
        udocker.FileUtil().cleanup()

    @mock.patch('udocker.sys.exit')
    @mock.patch('udocker.Msg')
    def test_01_noargs(self, mock_msg, mock_exit):
        """Test invoke command without arguments"""
        do_cmd(self, mock_msg,
               [UDOCKER],
               "Error: invalid command")

    @mock.patch('udocker.Msg')
    def test_02_help(self, mock_msg):
        """Test invoke help command"""
        do_cmd(self, mock_msg,
               [UDOCKER, "help"],
               " Syntax")

    @mock.patch('udocker.sys.exit')
    @mock.patch('udocker.Msg')
    def test_03_help(self, mock_msg, mock_exit):
        """Test invoke --help option"""
        do_cmd(self, mock_msg,
               [UDOCKER, "--help"],
               " Syntax")

    @mock.patch('udocker.Msg')
    def test_04_help_about_command(self, mock_msg):
        """Test invoke --help option for the run command"""
        do_cmd(self, mock_msg,
               [UDOCKER, "run", "--help"],
               "=run: .*--")

    @mock.patch('udocker.sys.exit')
    @mock.patch('udocker.Msg')
    def test_05_help_content(self, mock_msg, mock_exit):
        """Test verify help content"""
        do_cmd(self, mock_msg,
               [UDOCKER, "help"],
               "=Commands.* search.* pull.* images.* create.* ps.* rm.* "
               "run.* inspect.* name.* rmname.* rmi.* rm.* import.* load.* "
               "verify.* protect.* unprotect.* protect.* unprotect.* "
               "mkrepo.* help.* Examples:.* Notes:")

    @mock.patch('udocker.Msg')
    def test_06_images(self, mock_msg):
        """Test invoke images command"""
        do_cmd(self, mock_msg,
               [UDOCKER, "images"],
               " REPOSITORY")

    @mock.patch('udocker.Msg')
    def test_07_ps(self, mock_msg):
        """Test invoke ps command"""
        do_cmd(self, mock_msg,
               [UDOCKER, "ps"],
               " CONTAINER ID")

    @mock.patch('udocker.Msg')
    def test_08_search(self, mock_msg):
        """Test invoke search command"""
        do_cmd(self, mock_msg,
               [UDOCKER, "search", "-a", "indigodatacloud"],
               " indigodatacloudapps/disvis")


class FuncTestRepo(unittest.TestCase):
    """Test the local repository"""

    @classmethod
    def setUpClass(cls):
        """Setup class"""
        set_env()
        do_action([UDOCKER, "rmi", "busybox:latest"])
        do_action([UDOCKER, "rm", "busyNAME"])
        do_action([UDOCKER, "rm", "busyTEST"])

    @classmethod
    def tearDownClass(cls):
        """Cleanup class"""
        do_action([UDOCKER, "rmi", "busybox:latest"])
        do_action([UDOCKER, "rm", "busyNAME"])
        do_action([UDOCKER, "rm", "busyTEST"])
        udocker.FileUtil().cleanup()

    def tearDown(self):
        """Cleanup test"""
        udocker.FileUtil().cleanup()

    @mock.patch('udocker.Msg')
    def test_00_pull_insecure(self, mock_msg):
        """Test pull image in insecure mode"""
        # unsafe ssl requests --insecure (regression of #31)
        do_cmd(self, mock_msg,
               [UDOCKER, "--insecure", "pull", "busybox:latest"],
               "!^Error:")
        do_action([UDOCKER, "rmi", "busybox:latest"])

    @mock.patch('udocker.Msg')
    def test_01_pull(self, mock_msg):
        """Test pull image"""
        do_cmd(self, mock_msg,
               [UDOCKER, "pull", "busybox"],
               "!^Error:")

    @mock.patch('udocker.Msg')
    def test_02_pull_again(self, mock_msg):
        """Test pull image again"""
        do_cmd(self, mock_msg,
               [UDOCKER, "pull", "busybox"],
               "!^Error:")

    @mock.patch('udocker.Msg')
    def test_03_rmi(self, mock_msg):
        """Test remove image"""
        if image_not_exists():
            self.skipTest("no image")
        do_cmd(self, mock_msg,
               [UDOCKER, "rmi", "busybox:latest"],
               "!^Error:")

    @mock.patch('udocker.Msg')
    def test_04_pull_with_index(self, mock_msg):
        """Test pull image specifying index and registry"""
        do_action([UDOCKER, "rmi", "busybox:latest"])
        do_cmd(self, mock_msg,
               [UDOCKER, "pull",
                "--index=https://index.docker.io/v1",
                "--registry=https://registry-1.docker.io",
                "busybox:latest"], "!^Error:")

    @mock.patch('udocker.Msg')
    def test_05_images_short(self, mock_msg):
        """Test images listing"""
        if image_not_exists():
            self.skipTest("no image")
        do_cmd(self, mock_msg,
               [UDOCKER, "images"],
               " busybox:")

    @mock.patch('udocker.Msg')
    def test_06_images_long(self, mock_msg):
        """Test images listing long format"""
        if image_not_exists():
            self.skipTest("no image")
        do_cmd(self, mock_msg,
               [UDOCKER, "images", "-l"],
               " MB)")

    @mock.patch('udocker.Msg')
    def test_07_inspect_image(self, mock_msg):
        """Test if image is present"""
        if image_not_exists():
            self.skipTest("no image")
        do_cmd(self, mock_msg,
               [UDOCKER, "inspect", "busybox"],
               "=architecture.*container.*created.*parent")

    @mock.patch('udocker.Msg')
    def test_08_verify_image(self, mock_msg):
        """Test verify image"""
        if image_not_exists():
            self.skipTest("no image")
        do_cmd(self, mock_msg,
               [UDOCKER, "verify", "busybox"],
               "mage Ok")

    @mock.patch('udocker.Msg')
    def test_09_create_and_rename(self, mock_msg):
        """Test creation and renaming of container"""
        if image_not_exists():
            self.skipTest("no image")
        if do_cmd(self, mock_msg,
                  [UDOCKER, "create", "busybox"], r"=(\w+)-(\w+)"):
            container_id = str(mock_msg.return_value.out.call_args)[6:42]
            do_cmd(self, mock_msg,
                   [UDOCKER, "name", container_id, "busyNAME"],
                   "!Error:")
            do_cmd(self, mock_msg,
                   [UDOCKER, "rmname", "busyNAME"],
                   "!Error:")
            do_cmd(self, mock_msg,
                   [UDOCKER, "rm", container_id],
                   "!Error:")

    @mock.patch('udocker.Msg')
    def test_10_create_with_name(self, mock_msg):
        """Test creation with name"""
        do_action([UDOCKER, "rm", "busyTEST"])
        do_cmd(self, mock_msg,
               [UDOCKER, "create", "--name=busyTEST",
                "busybox"], r"=(\w+)-(\w+)")

    @mock.patch('udocker.Msg')
    def test_11_ps_find_container(self, mock_msg):
        """Test ps and presence of container"""
        if container_not_exists():
            self.skipTest("no container")
        do_cmd(self, mock_msg,
               [UDOCKER, "ps"],
               " busyTEST")

    @mock.patch('udocker.Msg')
    def test_12_inspect_container(self, mock_msg):
        """Test inspect container"""
        if container_not_exists():
            self.skipTest("no container")
        do_cmd(self, mock_msg,
               [UDOCKER, "inspect", "busyTEST"],
               "=architecture.*container.*created.*parent")

    @mock.patch('udocker.Msg')
    def test_14_inspect_container_root(self, mock_msg):
        """Test inspect container obtain ROOT pathname"""
        if container_not_exists():
            self.skipTest("no container")
        do_cmd(self, mock_msg,
               [UDOCKER, "inspect", "-p", "busyTEST"],
               " /ROOT")

    @mock.patch('udocker.Msg')
    def test_15_create_with_large_name(self, mock_msg):
        """Test creation with name"""
        # create with long alphanumeric strings (regression of #52)
        do_action([UDOCKER, "rm", "busylonglongLONGlonglong1234name"])
        do_cmd(self, mock_msg,
               [UDOCKER, "create", "--name=busylonglongLONGlonglong1234name",
                "busybox"], r"=(\w+)-(\w+)")
        do_cmd(self, mock_msg,
               [UDOCKER, "rm", "busylonglongLONGlonglong1234name"], None)

    @mock.patch('udocker.Msg')
    def test_16_pull_with_registry(self, mock_msg):
        """Test pull with registry"""
        # disregard of --registry (regression of #29)
        do_cmd(self, mock_msg,
               [UDOCKER, "pull", "--registry=xxx://127.0.0.1:1",
                "busybox:latest"], " not found")


class FuncTestRun(unittest.TestCase):
    """Test container execution"""

    @classmethod
    def setUpClass(cls):
        """Setup class"""
        set_env()
        do_action([UDOCKER, "rm", "busyTMP"])
        do_action([UDOCKER, "rm", "busyRUN"])
        do_action([UDOCKER, "rm", "busyTEST"])
        do_action([UDOCKER, "pull", "busybox"])
        do_action([UDOCKER, "create", "--name=busyRUN", "busybox"])

    @classmethod
    def tearDownClass(cls):
        """Cleanup class"""
        do_action([UDOCKER, "rm", "busyTMP"])
        do_action([UDOCKER, "rm", "busyRUN"])
        do_action([UDOCKER, "rm", "busyTEST"])
        udocker.FileUtil().cleanup()

    def tearDown(self):
        """Cleanup test"""
        udocker.FileUtil().cleanup()

    @mock.patch('udocker.Msg')
    def test_01_run_helloworld(self, mock_msg):
        """Test container execution"""
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        do_run(self, mock_msg,
               [UDOCKER, "run", "busyRUN", "/bin/echo", "'hello world'"],
               None, " hello")

    @mock.patch('udocker.Msg')
    def test_02_run_volume_validation(self, mock_msg):
        """Test run volume validation"""
        # discrepancy of -v (regression of #43)
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        do_run(self, mock_msg,
               [UDOCKER, "run", "-v", "/tmp:aaa", "busyRUN",
                "/bin/echo", "'hello'"], " Error", None)

    @mock.patch('udocker.Msg')
    def test_03_run_volume_validation(self, mock_msg):
        """Test run volume validation"""
        # discrepancy of -v (regression of #43)
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        do_run(self, mock_msg,
               [UDOCKER, "run", "-v", "/tmp:/aaa/tmp", "busyRUN",
                "/bin/ls", "-d", "/aaa/tmp"], None, "!Error")

    @mock.patch('udocker.Msg')
    def test_04_run_env(self, mock_msg):
        """Test run environment variables"""
        # blank on env var (regression of #48)
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        do_run(self, mock_msg,
               [UDOCKER, "run", "-e", "AAA='BBB CCC'", "busyRUN",
                "/bin/env"], None, " BBB CCC")
        do_run(self, mock_msg,
               [UDOCKER, "run", "--env='AAA=BBB CCC'", "busyRUN",
                "/bin/env"], None, " BBB CCC")

    @mock.patch('udocker.Msg')
    def test_05_run_quiet(self, mock_msg):
        """Test quiet"""
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        do_run(self, mock_msg,
               [UDOCKER, "-q", "run", "busyRUN", "/bin/echo", "'hello'"],
               None, r"!\*\*")

    @mock.patch('udocker.Msg')
    def test_06_run_debug(self, mock_msg):
        """Test debug"""
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        do_run(self, mock_msg,
               [UDOCKER, "-D", "run", "busyRUN", "/bin/echo", "'hello'"],
               " CMD =", None)

    @mock.patch('udocker.Msg')
    def test_07_host_env(self, mock_msg):
        """Test passing of host env"""
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        os.environ["UDOCKER_EXPORTED_VAR"] = "udocker exported var"
        do_run(self, mock_msg,
               [UDOCKER, "run", "--hostenv", "busyRUN", "/bin/env"],
               None, " udocker exported var")
        os.unsetenv("UDOCKER_EXPORTED_VAR")

    @mock.patch('udocker.Msg')
    def test_08_host_env(self, mock_msg):
        """Test binding of home dir"""
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        if not HOME:
            self.skipTest("no HOME dir")
        udocker_test_dir = HOME + "/UDOCKER.TEST"
        udocker.FileUtil(udocker_test_dir).mkdir()
        do_run(self, mock_msg,
               [UDOCKER, "run", "--bindhome", "busyRUN", "/bin/ls", "-d",
                udocker_test_dir],
               None, "!ls:")
        udocker.FileUtil(udocker_test_dir).remove()

    @mock.patch('udocker.Msg')
    def test_09_run_chdir(self, mock_msg):
        """Test run change dir"""
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        do_run(self, mock_msg,
               [UDOCKER, "run", "--workdir=/bin", "busyRUN", "/bin/pwd"],
               None, " /bin")

    @mock.patch('udocker.Msg')
    def test_10_run_chdir_to_vol(self, mock_msg):
        """Test run change dir to volume"""
        # workdir cannot be set to a volume (regression of #51)
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        udocker_test_dir = "/tmp/UDOCKER.TEST"
        udocker.FileUtil(udocker_test_dir).mkdir()
        do_run(self, mock_msg,
               [UDOCKER, "run", "--workdir=/aaa/tmp/UDOCKER.TEST",
                "-v", "/tmp:/aaa/tmp", "busyRUN", "/bin/pwd"],
               None, " /aaa/tmp/UDOCKER.TEST")
        udocker.FileUtil(udocker_test_dir).remove()

    @mock.patch('udocker.Msg')
    def test_11_run_novol(self, mock_msg):
        """Test run --novol"""
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        do_run(self, mock_msg,
               [UDOCKER, "run", "-v", "/tmp:/aaa/tmp", "--novol=/tmp",
                "busyRUN", "/bin/ls", "/aaa"],
               None, " ls:")

    @mock.patch('udocker.Msg')
    def test_12_run_chdir_to_vol(self, mock_msg):
        """Test run change dir to volume"""
        # workdir cannot be set to a volume (regression of #51)
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        udocker_test_dir = "/tmp/UDOCKER.TEST"
        udocker.FileUtil(udocker_test_dir).mkdir()
        do_run(self, mock_msg,
               [UDOCKER, "run", "--workdir=/aaa/tmp/UDOCKER.TEST",
                "-v", "/tmp:/aaa/tmp", "busyRUN", "/bin/pwd"],
               None, " /aaa/tmp/UDOCKER.TEST")
        udocker.FileUtil(udocker_test_dir).remove()

    @mock.patch('udocker.Msg')
    def test_14_run_rm(self, mock_msg):
        """Test run --rm"""
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        do_run(self, mock_msg,
               [UDOCKER, "run", "--rm", "busyRUN", "/bin/ls"], None, None)
        do_cmd(self, mock_msg,
               [UDOCKER, "inspect", "-p", "busyRUN"], "")

    @mock.patch('udocker.Msg')
    def test_15_run_name(self, mock_msg):
        """Test run --name"""
        do_run(self, mock_msg,
               [UDOCKER, "run", "--name=busyRUN", "busybox", "/bin/ls"],
               None, None)
        do_cmd(self, mock_msg,
               [UDOCKER, "inspect", "-p", "busyRUN"], " /ROOT")

    @mock.patch('udocker.Msg')
    def test_16_run_user_fullname(self, mock_msg):
        """Test run --user"""
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        user = pwd.getpwuid(os.getuid()).pw_name
        do_run(self, mock_msg,
               [UDOCKER, "run", "--user=" + user, "busyRUN", "/bin/id"],
               None, " " + user)

    # run with basenames failing (regression of #89)
    @mock.patch('udocker.Msg')
    def test_16_run_user_basename(self, mock_msg):
        """Test run --user"""
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        user = pwd.getpwuid(os.getuid()).pw_name
        do_run(self, mock_msg,
               [UDOCKER, "run", "--user=" + user, "busyRUN", "id"],
               None, " " + user)

    @mock.patch('udocker.Msg')
    def test_17_run_quotes(self, mock_msg):
        """Test run /bin/bash -c "'/bin/id; /bin/id'" """
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        user = pwd.getpwuid(os.getuid()).pw_name
        # issue #87
        do_run(self, mock_msg,
               [UDOCKER, "run", "--user=" + user, "busyRUN",
                "/bin/sh", "-c", "/bin/id; /bin/id"],
               None, " " + user)
        # issue #98
        do_run(self, mock_msg,
               [UDOCKER, "run", "--user=" + user, "busyRUN",
                "/bin/sh", "-c", "/bin/echo \"test\" + 'test'"],
               None, " test + test")

    @mock.patch('udocker.Msg')
    def test_18_run_mode_f1(self, mock_msg):
        """Test setup --execmode=F1 --force; run """
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        user = pwd.getpwuid(os.getuid()).pw_name
        do_run(self, mock_msg,
               [UDOCKER, "setup", "--execmode=F1", "--force", "busyRUN"],
               None, "!Error")
        do_run(self, mock_msg,
               [UDOCKER, "setup", "busyRUN"],
               " F1", None)
        do_run(self, mock_msg,
               [UDOCKER, "run", "--user=" + user, "busyRUN",
                "/bin/id"],
               None, " " + user)

    @mock.patch('udocker.Msg')
    def test_19_run_mode_r1(self, mock_msg):
        """Test setup --execmode=R1 --force; run """
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        user = pwd.getpwuid(os.getuid()).pw_name
        do_run(self, mock_msg,
               [UDOCKER, "setup", "--execmode=R1", "--force", "busyRUN"],
               None, "!Error")
        do_run(self, mock_msg,
               [UDOCKER, "setup", "busyRUN"],
               " R1", None)
        do_run(self, mock_msg,
               [UDOCKER, "run", "--user=root", "busyRUN",
                "/bin/id"],
               None, " root")

    @mock.patch('udocker.Msg')
    def test_20_run_mode_p2(self, mock_msg):
        """Test setup --execmode=P2 --force; run """
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        user = pwd.getpwuid(os.getuid()).pw_name
        do_run(self, mock_msg,
               [UDOCKER, "setup", "--execmode=P2", "--force", "busyRUN"],
               None, "!Error")
        do_run(self, mock_msg,
               [UDOCKER, "setup", "busyRUN"],
               " P2", None)
        do_run(self, mock_msg,
               [UDOCKER, "run", "--user=" + user, "busyRUN",
                "/bin/id"],
               None, " " + user)

    @mock.patch('udocker.Msg')
    def test_21_run_mode_p1(self, mock_msg):
        """Test setup --execmode=P1 --force; run """
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        user = pwd.getpwuid(os.getuid()).pw_name
        do_run(self, mock_msg,
               [UDOCKER, "setup", "--execmode=P1", "--force", "busyRUN"],
               None, "!Error")
        do_run(self, mock_msg,
               [UDOCKER, "setup", "busyRUN"],
               " P1", None)
        do_run(self, mock_msg,
               [UDOCKER, "run", "--user=" + user, "busyRUN",
                "/bin/id"],
               None, " " + user)

    @mock.patch('udocker.Msg')
    def test_22_run_mode_p1_force(self, mock_msg):
        """Test setup --execmode=P1 --force; run """
        if container_not_exists("busyRUN"):
            self.skipTest("no container")
        user = pwd.getpwuid(os.getuid()).pw_name
        do_run(self, mock_msg,
               [UDOCKER, "setup", "--execmode=P1", "--force", "busyRUN"],
               None, "!Error")
        do_run(self, mock_msg,
               [UDOCKER, "setup", "busyRUN"],
               " P1", None)
        do_run(self, mock_msg,
               [UDOCKER, "run", "--user=" + user, "busyRUN",
                "/bin/id"],
               None, " " + user)

    @mock.patch('udocker.Msg')
    def test_23_run_reg50(self, mock_msg):
        """Test create, ps, rm"""
        os.environ["UDOCKER_CONTAINERS"] = "/tmp/udocker_containers"
        do_action([UDOCKER, "rm", "busyTMP"])
        do_run(self, mock_msg,
               [UDOCKER, "create", "--name=busyTMP", "busybox"], None, None)
        do_run(self, mock_msg,
               [UDOCKER, "ps"], " busyTMP", None)
        do_run(self, mock_msg,
               [UDOCKER, "ps"], "!busyRUN", None)
        # delete not owner (regression of #50)
        do_run(self, mock_msg,
               [UDOCKER, "rm", "busyTMP"], "!Error", None)
        os.unsetenv("UDOCKER_CONTAINERS")


if __name__ == '__main__':
    unittest.main()
