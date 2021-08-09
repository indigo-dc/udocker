# -*- coding: utf-8 -*-
"""Basic unshare for udocker maintenance"""

import os
import ctypes
import subprocess

from udocker.msg import Msg
from udocker.helper.hostinfo import HostInfo
from udocker.helper.nixauth import NixAuthentication

class Unshare(object):
    """Place a process in a namespace"""

    CLONE_NEWNS = 0x20000
    CLONE_NEWUTS = 0x4000000
    CLONE_NEWIPC = 0x8000000
    CLONE_NEWUSER = 0x10000000
    CLONE_NEWPID = 0x20000000
    CLONE_NEWNET = 0x40000000

    def unshare(self, flags):
        """Python implementation of unshare"""
        try:
            _unshare = ctypes.CDLL("libc.so.6").unshare
        except OSError:
            Msg().err("Error: in unshare: mapping libc")
            return False

        _unshare.restype = ctypes.c_int
        _unshare.argtypes = (ctypes.c_int, )

        if _unshare(flags) == -1:
            Msg().err("Error: in unshare:", os.strerror(-1))
            return False
        return True

    def namespace_exec(self, method, flags=CLONE_NEWUSER):
        """Execute command in namespace"""
        (pread1, pwrite1) = os.pipe()
        (pread2, pwrite2) = os.pipe()
        cpid = os.fork()
        if cpid:
            os.close(pwrite1)
            os.read(pread1, 1)  # wait
            user = HostInfo().username()
            newidmap = ["newuidmap", str(cpid), "0", str(HostInfo.uid), "1"]
            for (subid, subcount) in NixAuthentication().user_in_subuid(user):
                newidmap.extend(["1", subid, subcount])

            subprocess.call(newidmap)
            newidmap = ["newgidmap", str(cpid), "0", str(HostInfo.uid), "1"]
            for (subid, subcount) in NixAuthentication().user_in_subgid(user):
                newidmap.extend(["1", subid, subcount])

            subprocess.call(newidmap)
            os.close(pwrite2)   # notify
            (dummy, status) = os.waitpid(cpid, 0)
            if status % 256:
                Msg().err("Error: namespace exec action failed")
                return False

            return True

        self.unshare(flags)
        os.close(pwrite2)
        os.close(pwrite1)   # notify
        os.read(pread2, 1)  # wait
        try:
            os.setgid(0)
            os.setuid(0)
            os.setgroups([0, 0, ])
        except OSError:
            Msg().err("Error: setting ids and groups")
            return False

        # pylint: disable=protected-access
        os._exit(int(method()))
        return True
