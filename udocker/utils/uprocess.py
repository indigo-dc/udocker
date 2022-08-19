# -*- coding: utf-8 -*-
"""Alternative implementations for subprocess"""

import os
import sys
import subprocess
import logging

from udocker import LOG
from udocker.config import Config


class Uprocess:
    """Provide alternative implementations for subprocess"""

    def get_stderr(self):
        """get stderr, dependent of log level"""
        stderror = subprocess.DEVNULL
        if Config.conf['verbose_level'] == logging.DEBUG:
            stderror = sys.stderr

        return stderror

    def find_inpath(self, filename, path, rootdir=""):
        """Find file in a path set such as PATH=/usr/bin:/bin"""
        if not (filename and path):
            return ""

        basename = os.path.basename(filename)
        LOG.debug("find file in path: %s", basename)
        if isinstance(path, str):
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
            output = subprocess.check_output(*popenargs, **kwargs)
            chk_out = output.decode()
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
            content = self.check_output(cmd, shell=False, stderr=self.get_stderr(), close_fds=True)
        except subprocess.CalledProcessError:
            if not ignore_error:
                return None

        return content.strip()

    def call(self, cmd, **kwargs):
        """Execute one shell command"""
        LOG.debug("executing: %s", cmd)
        if not cmd[0].startswith("/"):
            path = Config.conf["root_path"] + ":" + os.getenv("PATH", "")
            cmd[0] = self.find_inpath(cmd[0], path)

        kwargs["shell"] = False
        LOG.debug("call subprocess: %s", kwargs)
        return subprocess.call(cmd, **kwargs)

    def pipe(self, cmd1, cmd2, **kwargs):
        """Pipe two shell commands"""
        path = Config.conf["root_path"] + ":" + os.getenv("PATH", "")
        if not cmd1[0].startswith("/"):
            cmd1[0] = self.find_inpath(cmd1[0], path)

        if not cmd2[0].startswith("/"):
            cmd2[0] = self.find_inpath(cmd2[0], path)

        try:
            proc_1 = subprocess.Popen(cmd1, stderr=self.get_stderr(), shell=False,
                                      stdout=subprocess.PIPE, **kwargs)
        except (OSError, ValueError):
            return False

        try:
            proc_2 = subprocess.Popen(cmd2, stderr=self.get_stderr(),
                                      shell=False, stdin=proc_1.stdout)
        except (OSError, ValueError):
            proc_1.kill()
            return False

        while proc_1.returncode is None or proc_2.returncode is None:
            proc_1.wait()
            proc_2.wait()

        return not (proc_1.returncode or proc_2.returncode)
