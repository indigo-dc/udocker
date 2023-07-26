# -*- coding: utf-8 -*-
"""Implements most of the command line interface."""

import os
import sys
import logging
from udocker import LOG, MSG
from udocker.cmdparser import CmdParser
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.cli import UdockerCLI


class UMain:
    """These methods correspond directly to the commands that can
    be invoked via the command line interface.
    """

    STATUS_OK = 0
    STATUS_ERROR = 1

    def __init__(self, argv):
        """Initialize variables of the class"""
        self.argv = argv
        self.cmdp = None
        self.localrepo = None
        self.cli = None

    def _prepare_exec(self):
        """Prepare configuration, parse and execute the command line"""
        self.cmdp = CmdParser()
        self.cmdp.parse(self.argv)
        allow_root = self.cmdp.get("--allow-root", "GEN_OPT")
        if not (os.geteuid() or allow_root):
            LOG.error("do not run as root!")
            sys.exit(self.STATUS_ERROR)

        if self.cmdp.get("--config=", "GEN_OPT"):
            conf_file = self.cmdp.get("--config=", "GEN_OPT")
            Config().getconf(conf_file)
        else:
            Config().getconf()

        if (self.cmdp.get("--debug", "GEN_OPT") or self.cmdp.get("-D", "GEN_OPT")):
            Config.conf['verbose_level'] = logging.DEBUG
        elif (self.cmdp.get("--quiet", "GEN_OPT") or self.cmdp.get("-q", "GEN_OPT")):
            Config.conf['verbose_level'] = logging.NOTSET

        LOG.setLevel(Config.conf['verbose_level'])
        if self.cmdp.get("--insecure", "GEN_OPT"):
            Config.conf['http_insecure'] = True

        topdir = self.cmdp.get("--repo=", "GEN_OPT")
        if topdir:  # override repo root tree
            Config.conf['topdir'] = topdir

        self.localrepo = LocalRepository()
        if not self.localrepo.is_repo():
            if topdir:
                LOG.error("invalid udocker repository: %s", topdir)
                sys.exit(self.STATUS_ERROR)
            else:
                LOG.info("creating repo: %s", Config.conf['topdir'])
                self.localrepo.create_repo()

        self.cli = UdockerCLI(self.localrepo)

    def execute(self):
        """Command parsing and selection"""
        self._prepare_exec()
        cmds = {
            'clone': self.cli.do_clone,
            'create': self.cli.do_create,
            'export': self.cli.do_export,
            'images': self.cli.do_images,
            'import': self.cli.do_import,
            'inspect': self.cli.do_inspect,
            'load': self.cli.do_load,
            'login': self.cli.do_login,
            'logout': self.cli.do_logout,
            'mkrepo': self.cli.do_mkrepo,
            'name': self.cli.do_name,
            'protect': self.cli.do_protect,
            'ps': self.cli.do_ps,
            'pull': self.cli.do_pull,
            'rename': self.cli.do_rename,
            'rm': self.cli.do_rm,
            'rmi': self.cli.do_rmi,
            'rmname': self.cli.do_rmname,
            'run': self.cli.do_run,
            'save': self.cli.do_save,
            'search': self.cli.do_search,
            'setup': self.cli.do_setup,
            'showconf': self.cli.do_showconf,
            'unprotect': self.cli.do_unprotect,
            'verify': self.cli.do_verify,
            'version': self.cli.do_version,
            'help': self.cli.do_help,
            'install': self.cli.do_install,
            'rmmod': self.cli.do_rmmod,
            'availmod': self.cli.do_availmod,
            'rmmeta': self.cli.do_rmmeta,
            'downloadtar': self.cli.do_downloadtar,
            'rmtar': self.cli.do_rmtar,
            'showmod': self.cli.do_showmod,
            'verifytar': self.cli.do_verifytar,
            'tag': self.cli.do_tag,
            'manifest': self.cli.do_manifest,
        }

        cmd_no_install = ['help', 'version', 'showconf', 'availmod', 'downloadtar', 'verifytar',
                          'rmmeta', 'rmtar', 'showmod']

        larg = len(self.argv)
        if ((larg == 1) or self.cmdp.get('-h', 'GEN_OPT') or self.cmdp.get('--help', 'GEN_OPT')):
            return self.cli.do_help(self.cmdp)

        if (self.cmdp.get("-V", "GEN_OPT") or self.cmdp.get("--version", "GEN_OPT")):
            return self.cli.do_version(self.cmdp)

        command = self.cmdp.get("", "CMD")
        if command in cmds:
            if self.cmdp.get("--help", "CMD_OPT"):
                MSG.info(cmds[command].__doc__)
                return self.STATUS_OK

            if command in cmd_no_install:
                return cmds[command](self.cmdp)

            if command != "install":
                self.cli.do_install(self.cmdp)

            exit_status = cmds[command](self.cmdp)  # executes command
            if self.cmdp.missing_options():
                LOG.error("Syntax error at: %s", " ".join(self.cmdp.missing_options()))
                return self.STATUS_ERROR

            return exit_status

        LOG.error("invalid command: %s\n", command)
        return self.STATUS_ERROR
