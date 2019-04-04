#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
========
udocker
========
Wrapper to execute basic docker containers without using docker.
This tool is a last resort for the execution of docker containers
where docker is unavailable. It only provides a limited set of
functionalities.

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
import sys
import os

from udocker.cli import UdockerCLI
from udocker.container.localrepo import LocalRepository
from udocker.config import Config
from udocker.utils.fileutil import FileUtil
from udocker.cmdparser import CmdParser
from udocker.msg import Msg


class Main(object):
    """Implements most of the command line interface.
    These methods correspond directly to the commands that can
    be invoked via the command line interface.
    """
    """Get options, parse and execute the command line"""

    def __init__(self, argv):
        self.argv = argv
        self.cmdp = CmdParser()
        parseok = self.cmdp.parse(argv)
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
        lhelp = ['-h', '--help', 'help']
        lversion = ['-V', '--version', 'version']
        cmds = {
            "search": self.cli.do_search, "listconf": self.cli.do_listconf,
            "images": self.cli.do_images, "pull": self.cli.do_pull,
            "create": self.cli.do_create, "ps": self.cli.do_ps,
            "run": self.cli.do_run,
            "rmi": self.cli.do_rmi, "mkrepo": self.cli.do_mkrepo,
            "import": self.cli.do_import, "load": self.cli.do_load,
            "export": self.cli.do_export, "clone": self.cli.do_clone,
            "protect": self.cli.do_protect, "rm": self.cli.do_rm,
            "name": self.cli.do_name, "rmname": self.cli.do_rmname,
            "verify": self.cli.do_verify, "logout": self.cli.do_logout,
            "unprotect": self.cli.do_unprotect,
            "inspect": self.cli.do_inspect, "login": self.cli.do_login,
            "setup": self.cli.do_setup, "install": self.cli.do_install,
        }

        if (len(self.argv) == 1) or \
                (len(self.argv) == 2 and self.argv[1] in lhelp):
            self.cli.do_help(None)
            sys.exit(0)
        if self.argv[1] in lversion:
            self.cli.do_version(None)
            sys.exit(0)
        else:
            command = self.cmdp.get("", "CMD")
            if command != "install":
                self.cli.do_install(None)
            status = cmds[command](self.cmdp)  # executes command
            if self.cmdp.missing_options():
                Msg().err("Error: syntax error at: %s" %
                          " ".join(self.cmdp.missing_options()))
                sys.exit(1)
            if isinstance(status, bool):
                return not status
            elif isinstance(status, int):
                return sys.exit(status)  # return command status

    def start(self):
        """Program start and exception handling"""
        try:
            exit_status = self._execute()
        except (KeyboardInterrupt, SystemExit):
            FileUtil().cleanup()
            return sys.exit(1)
        except:
            FileUtil().cleanup()
            raise
        else:
            FileUtil().cleanup()
            return exit_status
