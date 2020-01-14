# -*- coding: utf-8 -*-
"""Alternative implementations for subprocess"""

import os
import sys
import subprocess
from udocker.msg import Msg
from udocker.config import Config
from udocker.utils.fileutil import FileUtil

# Python version major.minor
PY_VER = "%d.%d" % (sys.version_info[0], sys.version_info[1])


class Uprocess(object):
    """Provide alternative implementations for subprocess"""

    def _check_output(self, *popenargs, **kwargs):
        """Alternative to subprocess.check_output"""
        process = subprocess.Popen(*popenargs, stdout=subprocess.PIPE, **kwargs)
        output, dummy = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output

    def check_output(self, *popenargs, **kwargs):
        """Select check_output implementation"""
        chk_out = ""
        if PY_VER == "2.6":
            chk_out = self._check_output(*popenargs, **kwargs)
        elif PY_VER == "2.7":
            chk_out = subprocess.check_output(*popenargs, **kwargs)
        elif PY_VER >= "3":
            command = subprocess.check_output(*popenargs, **kwargs)
            chk_out = command.decode()

        return chk_out

    def get_output(self, cmd, ignore_error=False):
        """Execute a shell command and get its output"""
        if not cmd[0].startswith("/"):
            path = Config.conf["root_path"] + ":" + os.getenv("PATH", "")
            cmd[0] = FileUtil(cmd[0]).find_inpath(path)
        content = ""
        try:
            content = self.check_output(cmd, shell=False, stderr=Msg.chlderr,
                                        close_fds=True)
        except subprocess.CalledProcessError:
            if not ignore_error:
                return None
        return content.strip()

    def call(self, cmd, **kwargs):
        """Execute one shell command"""
        if not cmd[0].startswith("/"):
            path = Config.conf["root_path"] + ":" + os.getenv("PATH", "")
            cmd[0] = FileUtil(cmd[0]).find_inpath(path)
        kwargs["shell"] = False
        return subprocess.call(cmd, **kwargs)

    def pipe(self, cmd1, cmd2, **kwargs):
        """Pipe two shell commands"""
        path = Config.conf["root_path"] + ":" + os.getenv("PATH", "")
        if not cmd1[0].startswith("/"):
            cmd1[0] = FileUtil(cmd1[0]).find_inpath(path)
        if not cmd2[0].startswith("/"):
            cmd2[0] = FileUtil(cmd2[0]).find_inpath(path)
        try:
            proc_1 = subprocess.Popen(cmd1, stderr=Msg.chlderr, shell=False,
                                      stdout=subprocess.PIPE, **kwargs)
        except (OSError, ValueError):
            return False
        try:
            proc_2 = subprocess.Popen(cmd2, stderr=Msg.chlderr, shell=False,
                                      stdin=proc_1.stdout)
        except (OSError, ValueError):
            proc_1.kill()
            return False
        while proc_1.returncode is None or proc_2.returncode is None:
            proc_1.wait()
            proc_2.wait()
        return not (proc_1.returncode or proc_2.returncode)
