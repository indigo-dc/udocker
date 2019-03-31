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
from argparse import ArgumentParser

sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + '/../')
from udocker.cli import UdockerCLI
from udocker.container.localrepo import LocalRepository
from udocker.config import Config
from udocker.utils.fileutil import FileUtil


class Main(object):
    """Implements most of the command line interface.
    These methods correspond directly to the commands that can
    be invoked via the command line interface.
    """
    """Get options, parse and execute the command line"""

    def __init__(self):
        self.conf = Config().getconf()
        self.parser = ArgumentParser()
        self.localrepo = LocalRepository(self.conf['topdir'])
        self.cli = UdockerCLI(self.localrepo)

        '''
        self.cmdp = CmdParser()
        parseok = self.cmdp.parse(sys.argv)
        if not parseok and not self.cmdp.get("--version", "GEN_OPT"):
            Msg().err("Error: parsing command line, use: udocker help")
            sys.exit(1)
        if not (os.geteuid() or self.cmdp.get("--allow-root", "GEN_OPT")):
            Msg().err("Error: do not run as root !")
            sys.exit(1)
        Config().user_init(self.cmdp.get("--config=", "GEN_OPT")) # read config
        if (self.cmdp.get("--debug", "GEN_OPT") or
                self.cmdp.get("-D", "GEN_OPT")):
            Config.verbose_level = Msg.DBG
        elif (self.cmdp.get("--quiet", "GEN_OPT") or
              self.cmdp.get("-q", "GEN_OPT")):
            Config.verbose_level = Msg.MSG
        Msg().setlevel(Config.verbose_level)
        if self.cmdp.get("--insecure", "GEN_OPT"):
            Config.http_insecure = True
        if self.cmdp.get("--repo=", "GEN_OPT"):  # override repo root tree
            Config.topdir = self.cmdp.get("--repo=", "GEN_OPT")
            if not LocalRepository(Config.topdir).is_repo():
                Msg().err("Error: invalid udocker repository:",
                          Config.topdir)
                sys.exit(1)
        self.localrepo = LocalRepository(Config.topdir)
        if (self.cmdp.get("", "CMD") == "version" or
                self.cmdp.get("--version", "GEN_OPT")):
            Udocker(self.localrepo).do_version(self.cmdp)
            sys.exit(0)
        if not self.localrepo.is_repo():
            Msg().out("Info: creating repo: " + Config.topdir, l=Msg.INF)
            self.localrepo.create_repo()
        self.udocker = Udocker(self.localrepo)
        '''

    @staticmethod
    def do_help():
        """
        Print help information
        """

        print(
            """
Syntax:
  udocker  [general_options] <command>  [command_options]  <command_args>

  udocker [-h|--help|help]        :Display this help and exits
  udocker [-V|--version|version]  :Display udocker version and tarball version and exits

Commands:
  search <repo/image:tag>       :Search dockerhub for container images
  pull <repo/image:tag>         :Pull container image from dockerhub
  images                        :List container images
  create <repo/image:tag>       :Create container from a pulled image
  ps                            :List created containers
  rm  <container>               :Delete container
  run <container>               :Execute container
  inspect <container>           :Low level information on container
  name <container_id> <name>    :Give name to container
  rmname <name>                 :Delete name from container

  rmi <repo/image:tag>          :Delete image
  rm <container-id>             :Delete container
  import <tar> <repo/image:tag> :Import tar file (exported by docker)
  import - <repo/image:tag>     :Import from stdin (exported by docker)
  load -i <exported-image>      :Load image from file (saved by docker)
  load                          :Load image from stdin (saved by docker)
  export -o <tar> <container>   :Export container rootfs to file
  export - <container>          :Export container rootfs to stdin
  inspect <repo/image:tag>      :Return low level information on image
  verify <repo/image:tag>       :Verify a pulled image
  clone <container>             :duplicate container

  protect <repo/image:tag>      :Protect repository
  unprotect <repo/image:tag>    :Unprotect repository
  protect <container>           :Protect container
  unprotect <container>         :Unprotect container

  mkrepo <topdir>               :Create repository in another location
  setup                         :Change container execution settings
  login                         :Login into docker repository
  logout                        :Logout from docker repository

  help [command]                :Command specific help

Options common to all commands must appear before the command:
  -D                            :Debug
  --quiet                       :Less verbosity
  --repo=<directory>            :Use repository at directory

Examples:
  udocker search fedora
  udocker pull fedora
  udocker create --name=fed  fedora
  udocker run  fed  cat /etc/redhat-release
  udocker run --hostauth --hostenv --bindhome  fed
  udocker run --user=root  fed  yum install firefox
  udocker run --hostauth --hostenv --bindhome fed   firefox
  udocker run --hostauth --hostenv --bindhome fed   /bin/bash -i
  udocker run --user=root  fed  yum install cheese
  udocker run --hostauth --hostenv --bindhome --dri fed  cheese
  udocker --repo=/home/x/.udocker  images
  udocker -D run --user=1001:5001  fedora
  udocker export -o fedora.tar fedora
  udocker import fedora.tar myfedoraimage
  udocker create --name=myfedoracontainer myfedoraimage
  udocker export -o fedora_all.tar --clone fedora
  udocker import --clone fedora_all.tar

Notes:
  * by default the binaries, images and containers are placed in
       $HOME/.udocker
  * by default the following host directories are mounted in the
    container:
       /dev /proc /sys
       /etc/resolv.conf /etc/host.conf /etc/hostname
  * to prevent the mount of the above directories use:
       run  --nosysdirs  <container>
  * additional host directories to be mounted are specified with:
       run --volume=/data:/mnt --volume=/etc/hosts  <container>
       run --nosysdirs --volume=/dev --volume=/proc  <container>

See: https://github.com/indigo-dc/udocker/blob/master/SUMMARY.md
            """)
        return True

    def execute(self):
        """Command parsing and selection"""
        lhelp = ['-h', '--help', 'help']
        lversion = ['-V', '--version', 'version']
        if (len(sys.argv) == 1) or \
                (len(sys.argv) == 2 and sys.argv[1] in lhelp):
            self.do_help()
            return 0
        if sys.argv[1] in lversion:
            self.cli.do_version()
            return 0
        else:
            self.cli.onecmd(' '.join(sys.argv[1:]))

        '''
        if (self.cmdp.get("--help", "GEN_OPT") or
                self.cmdp.get("-h", "GEN_OPT")):
            self.udocker.do_help(self.cmdp)
            return 0
        else:
            command = self.cmdp.get("", "CMD")
            if command in cmds:
                if command != "install":
                    cmds["install"](None)
                if self.cmdp.get("--help") or self.cmdp.get("-h"):
                    self.udocker.do_help(self.cmdp, cmds)   # help on command
                    return 0
                status = cmds[command](self.cmdp)     # executes the command
                if self.cmdp.missing_options():
                    Msg().err("Error: syntax error at: %s" %
                              " ".join(self.cmdp.missing_options()))
                    return 1
                if isinstance(status, bool):
                    return not status
                elif isinstance(status, (int, long)):
                    return status                     # return command status
            else:
                Msg().err("Error: invalid command:", command, "\n")
                self.udocker.do_help(self.cmdp)
        return 1
        '''

    def start(self):
        """Program start and exception handling"""
        try:
            exit_status = self.execute()
        except (KeyboardInterrupt, SystemExit):
            FileUtil().cleanup()
            return 1
        except:
            FileUtil().cleanup()
            raise
        else:
            FileUtil().cleanup()
            return exit_status
