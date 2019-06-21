# -*- coding: utf-8 -*-
"""Implements most of the command line interface."""

import sys
import os

from udocker.cli import UdockerCLI
from udocker.container.localrepo import LocalRepository
from udocker.config import Config
from udocker.utils.fileutil import FileUtil
from udocker.cmdparser import CmdParser
from udocker.msg import Msg


class UMain(object):
    """These methods correspond directly to the commands that can
    be invoked via the command line interface.
    """

    def __init__(self, argv):
        """Get options, parse and execute the command line"""
        self.argv = argv
        self.cmdp = CmdParser()
        self.cmdp.parse(argv)
        if not (os.geteuid() or self.cmdp.get("--allow-root", "GEN_OPT")):
            Msg().err("Error: do not run as root !")
            sys.exit(1)

        if self.cmdp.get("--config=", "GEN_OPT"):
            conf_file = self.cmdp.get("--config=", "GEN_OPT")
            self.conf = Config(conf_file).getconf()
        else:
            self.conf = Config().getconf()

        if (self.cmdp.get("--debug", "GEN_OPT") or
                self.cmdp.get("-D", "GEN_OPT")):
            self.conf['verbose_level'] = Msg.DBG
        elif (self.cmdp.get("--quiet", "GEN_OPT") or
              self.cmdp.get("-q", "GEN_OPT")):
            self.conf['verbose_level'] = Msg.MSG

        Msg().setlevel(self.conf['verbose_level'])
        if self.cmdp.get("--insecure", "GEN_OPT"):
            self.conf['http_insecure'] = True

        if self.cmdp.get("--repo=", "GEN_OPT"):  # override repo root tree
            self.conf['topdir'] = self.cmdp.get("--repo=", "GEN_OPT")
            if not LocalRepository(self.conf).is_repo():
                Msg().err("Error: invalid udocker repository:",
                          self.conf['topdir'])
                sys.exit(1)

        self.localrepo = LocalRepository(self.conf)
        if not self.localrepo.is_repo():
            Msg().out("Info: creating repo: " + self.conf['topdir'], l=Msg.INF)
            self.localrepo.create_repo()

        self.cli = UdockerCLI(self.localrepo, self.conf)

    def _execute(self):
        """Command parsing and selection"""
        exit_status = 0
        lhelp = ['-h', '--help', 'help']
        lversion = ['-V', '--version', 'version']
        cmds = {
            "search": self.cli.do_search, "help": self.cli.do_help,
            "images": self.cli.do_images, "pull": self.cli.do_pull,
            "create": self.cli.do_create, "ps": self.cli.do_ps,
            "run": self.cli.do_run, "version": self.cli.do_version,
            "rmi": self.cli.do_rmi, "mkrepo": self.cli.do_mkrepo,
            "import": self.cli.do_import, "load": self.cli.do_load,
            "export": self.cli.do_export, "clone": self.cli.do_clone,
            "protect": self.cli.do_protect, "rm": self.cli.do_rm,
            "name": self.cli.do_name, "rmname": self.cli.do_rmname,
            "verify": self.cli.do_verify, "logout": self.cli.do_logout,
            "unprotect": self.cli.do_unprotect,
            "listconf": self.cli.do_listconf,
            "inspect": self.cli.do_inspect, "login": self.cli.do_login,
            "setup": self.cli.do_setup, "install": self.cli.do_install,
        }

        if (len(self.argv) == 1) or \
                (len(self.argv) == 2 and self.argv[1] in lhelp):
            exit_status = self.cli.do_help()
            return exit_status

        if len(self.argv) > 2 and self.argv[1] in lhelp:
            cmd_help = self.argv[2]
            if cmd_help in cmds:
                text = cmds[cmd_help].__doc__
                Msg().out(text)
                return exit_status
            else:
                Msg().err("Error: command not found: %s" % cmd_help)
                exit_status = 1
                return exit_status

        if "listconf" in self.argv:
            exit_status = self.cli.do_listconf()
            return exit_status

        if self.argv[1] in lversion:
            exit_status = self.cli.do_version()
            return exit_status
        else:
            command = self.cmdp.get("", "CMD")
            if command != "install":
                self.cli.do_install(None)
            exit_status = cmds[command](self.cmdp)  # executes command
            if self.cmdp.missing_options():
                Msg().err("Error: syntax error at: %s" %
                          " ".join(self.cmdp.missing_options()))
                exit_status = 1

        return exit_status

    def start(self):
        """Program start and exception handling"""
        try:
            exit_status = self._execute()
        except (KeyboardInterrupt, SystemExit):
            FileUtil(self.conf).cleanup()
            return sys.exit(1)
        else:
            FileUtil(self.conf).cleanup()
            return exit_status
