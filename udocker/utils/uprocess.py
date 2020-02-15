# -*- coding: utf-8 -*-
"""Alternative implementations for subprocess"""

import os
import sys
import subprocess

from udocker import is_genstr
from udocker.msg import Msg
from udocker.config import Config


class Uprocess(object):
    """Provide alternative implementations for subprocess"""

    def find_inpath(self, filename, path, rootdir=""):
        """Find file in a path set such as PATH=/usr/bin:/bin"""
        if not (filename and path):
            return ""
        basename = os.path.basename(filename)
        if is_genstr(path):
            if "=" in path:
                path = "".join(path.split("=", 1)[1:])
            path = path.split(":")
        if isinstance(path, (list, tuple)):
            for directory in path:
                full_path = rootdir + directory + "/" + basename
                if os.path.lexists(full_path):
                    return directory + "/" + basename
            return ""
        return ""

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
        try:
            # if Python 3
            if sys.version_info[0] >= 3:
                output = subprocess.check_output(*popenargs, **kwargs)
                chk_out = output.decode()
            # if Python >= 2.7
            elif sys.version_info[0] >= 2 and sys.version_info[1] >= 7:
                chk_out = subprocess.check_output(*popenargs, **kwargs)
            # if Python < 2.7
            else:
                chk_out = self._check_output(*popenargs, **kwargs)
        except OSError:
            return ""

        return chk_out

    def get_output(self, cmd, ignore_error=False):
        """Execute a shell command and get its output"""
        if not cmd[0].startswith("/"):
            path = Config.conf["root_path"] + ":" + os.getenv("PATH", "")
            cmd_path = self.find_inpath(cmd[0], path)
            if cmd_path:
                cmd[0] = cmd_path
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
            cmd[0] = self.find_inpath(cmd[0], path)
        kwargs["shell"] = False
        return subprocess.call(cmd, **kwargs)

    def pipe(self, cmd1, cmd2, **kwargs):
        """Pipe two shell commands"""
        path = Config.conf["root_path"] + ":" + os.getenv("PATH", "")
        if not cmd1[0].startswith("/"):
            cmd1[0] = self.find_inpath(cmd1[0], path)
        if not cmd2[0].startswith("/"):
            cmd2[0] = self.find_inpath(cmd2[0], path)
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
