# -*- coding: utf-8 -*-
import subprocess
import sys


class Uprocess(object):
    """Provide alternative implementations for subprocess"""

    @staticmethod
    def _check_output(*popenargs, **kwargs):
        """Select check_output implementation"""
        return subprocess.check_output(*popenargs, **kwargs)

    def get_output(self, cmd):
        """Execute a shell command and get its output"""
        try:
            content = self._check_output(cmd, shell=True,
                                         stderr=sys.stderr,
                                         close_fds=True)
        except subprocess.CalledProcessError:
            return None
        return content.strip()
