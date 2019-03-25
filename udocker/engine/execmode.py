# -*- coding: utf-8 -*-
import os

from udocker.config import Config
from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil
from udocker.utils.filebind import FileBind
from udocker.helper.elfpatcher import ElfPatcher
from udocker.engine.fakechroot import FakechrootEngine
from udocker.engine.proot import PRootEngine
from udocker.engine.runc import RuncEngine
from udocker.engine.singularity import SingularityEngine


class ExecutionMode(object):
    """Generic execution engine class to encapsulate the specific
    execution engines and their execution modes.
    P1: proot with seccomp
    P2: proot without seccomp (slower)
    F1: fakeroot running executables via direct loader invocation
    F2: similar to F1 with protected environment and modified ld.so
    F3: fakeroot patching the executables elf headers
    F4: similar to F3 with support to newly created executables
        dynamic patching of elf headers
    S1: singularity
    """

    def __init__(self, localrepo, container_id):
        self.localrepo = localrepo               # LocalRepository object
        self.container_id = container_id         # Container id
        self.container_dir = self.localrepo.cd_container(container_id)
        self.container_root = self.container_dir + "/ROOT"
        self.container_execmode = self.container_dir + "/execmode"
        self.container_orig_root = self.container_dir + "/root.path"
        self.exec_engine = None
        self.valid_modes = ("P1", "P2", "F1", "F2", "F3", "F4", "R1", "S1")

    def get_mode(self):
        """Get execution mode"""
        xmode = FileUtil(self.container_execmode).getdata().strip()
        if not xmode:
            xmode = Config.default_execution_mode
        return xmode

    def set_mode(self, xmode, force=False):
        """Set execution mode"""
        status = False
        prev_xmode = self.get_mode()
        elfpatcher = ElfPatcher(self.localrepo, self.container_id)
        filebind = FileBind(self.localrepo, self.container_id)
        orig_path = FileUtil(self.container_orig_root).getdata().strip()
        if xmode not in self.valid_modes:
            Msg().err("Error: invalid execmode:", xmode)
            return status
        if not (force or xmode != prev_xmode):
            return True
        if prev_xmode in ("R1", "S1") and xmode not in ("R1", "S1"):
            filebind.restore()
        if xmode.startswith("F"):
            if force or prev_xmode[0] in ("P", "R", "S"):
                status = (FileUtil(self.container_root).links_conv(force, True,
                                                                   orig_path)
                          and elfpatcher.get_ld_libdirs(force))
        if xmode in ("P1", "P2", "F1", "R1", "S1"):
            if prev_xmode in ("P1", "P2", "F1", "R1", "S1"):
                status = True
            elif force or prev_xmode in ("F2", "F3", "F4"):
                status = ((elfpatcher.restore_ld() or force) and
                          elfpatcher.restore_binaries())
            if xmode in ("R1", "S1"):
                filebind.setup()
        elif xmode in ("F2", ):
            if force or prev_xmode in ("F3", "F4"):
                status = elfpatcher.restore_binaries()
            if force or prev_xmode in ("P1", "P2", "F1", "R1", "S1"):
                status = elfpatcher.patch_ld()
        elif xmode in ("F3", "F4"):
            if force or prev_xmode in ("P1", "P2", "F1", "F2", "R1", "S1"):
                status = (elfpatcher.patch_ld() and
                          elfpatcher.patch_binaries())
            elif prev_xmode in ("F3", "F4"):
                status = True
        if xmode[0] in ("P", "R", "S"):
            if force or (status and prev_xmode.startswith("F")):
                status = FileUtil(self.container_root).links_conv(force, False,
                                                                  orig_path)
        if status or force:
            status = FileUtil(self.container_execmode).putdata(xmode)
        if status or force:
            status = FileUtil(self.container_orig_root).putdata(
                os.path.realpath(self.container_root))
        if (not status) and (not force):
            Msg().err("Error: container setup failed")
        return status

    def get_engine(self):
        """get execution engine instance"""
        xmode = self.get_mode()
        if xmode.startswith("P"):
            self.exec_engine = PRootEngine(self.localrepo, xmode)
        elif xmode.startswith("F"):
            self.exec_engine = FakechrootEngine(self.localrepo, xmode)
        elif xmode.startswith("R"):
            self.exec_engine = RuncEngine(self.localrepo, xmode)
        elif xmode.startswith("S"):
            self.exec_engine = SingularityEngine(self.localrepo, xmode)
        return self.exec_engine
