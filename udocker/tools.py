# -*- coding: utf-8 -*-
"""Tools for udocker"""

import os
import tarfile
import random
import json

from udocker.utils.curl import GetURL
from udocker.utils.fileutil import FileUtil
from udocker.msg import Msg
from udocker import __version__


class UdockerTools(object):
    """Download and setup of the udocker supporting tools
    Includes: proot and alternative python modules, these
    are downloaded to facilitate the installation by the
    end-user.
    """

    def __init__(self, localrepo, conf):
        self.conf = conf
        self.localrepo = localrepo        # LocalRepository object
        self._autoinstall = self.conf['autoinstall']  # True / False
        self._tarball = self.conf['tarball']  # URL or file
        self._installinfo = self.conf['installinfo']  # URL or file
        self._tarball_release = self.conf['tarball_release']
        self._install_json = dict()
        self.curl = GetURL(self.conf)

    def _is_available(self):
        """Are the tools already installed"""
        fname = self.localrepo.libdir + "/VERSION"
        version = FileUtil(self.conf, fname).getdata("r").strip()
        return version and version == self._tarball_release

    def _download(self, url):
        """Download a file """
        download_file = FileUtil(self.conf, "udockertools").mktmp()
        if Msg.level <= Msg.DEF:
            Msg().setlevel(Msg.NIL)
        (hdr, dummy) = self.curl.get(url, ofile=download_file)
        if Msg.level == Msg.NIL:
            Msg().setlevel()
        try:
            if "200" in hdr.data["X-ND-HTTPSTATUS"]:
                return download_file
        except (KeyError, TypeError, AttributeError):
            pass
        FileUtil(self.conf, download_file).remove()
        return ""

    def _get_file(self, locations):
        """Get file from list of possible locations file or internet"""
        for url in locations:
            Msg().err("Info: getting file:", url, l=Msg.VER)
            filename = ""
            if "://" in url:
                filename = self._download(url)
            elif os.path.exists(url):
                filename = os.path.realpath(url)
            if filename and os.path.isfile(filename):
                return (filename, url)
        return ("", "")

    def _verify_version(self, tarball_file):
        """verify the tarball version"""
        status = False
        if not (tarball_file and os.path.isfile(tarball_file)):
            return status

        tfile = tarfile.open(tarball_file, "r:gz")
        for tar_in in tfile.getmembers():
            if tar_in.name.startswith("udocker_dir/lib/VERSION"):
                tar_in.name = os.path.basename(tar_in.name)
                tfile.extract(tar_in)
        tfile.close()

        with open("VERSION") as filep:
            tar_version = filep.readline().strip()

        Msg().err("Engine mode tarbal version", tar_version, l=Msg.DBG)
        Msg().err("tarball_release", self._tarball_release, l=Msg.DBG)
        status = (tar_version == self._tarball_release)
        os.remove("VERSION")
        Msg().err("Verify version status", status, l=Msg.DBG)
        return status

    def purge(self):
        """Remove existing files in bin and lib"""
        for f_name in os.listdir(self.localrepo.bindir):
            full_path = self.localrepo.bindir + "/" + f_name
            FileUtil(self.conf, full_path).register_prefix()
            FileUtil(self.conf, full_path).remove()
        for f_name in os.listdir(self.localrepo.libdir):
            full_path = self.localrepo.libdir + "/" + f_name
            FileUtil(self.conf, full_path).register_prefix()
            FileUtil(self.conf, full_path).remove()

    def _install(self, tarball_file):
        """Install the tarball"""
        if not (tarball_file and os.path.isfile(tarball_file)):
            return False

        tfile = tarfile.open(tarball_file, "r:gz")
        for tar_in in tfile.getmembers():
            if tar_in.name.startswith("udocker_dir/bin/"):
                tar_in.name = os.path.basename(tar_in.name)
                Msg().err("Extrating", tar_in.name, l=Msg.DBG)
                tfile.extract(tar_in, self.localrepo.bindir)
        for tar_in in tfile.getmembers():
            if tar_in.name.startswith("udocker_dir/lib/"):
                tar_in.name = os.path.basename(tar_in.name)
                Msg().err("Extrating", tar_in.name, l=Msg.DBG)
                tfile.extract(tar_in, self.localrepo.libdir)

        tfile.close()
        return True

    def _instructions(self):
        """
        Udocker installation instructions are available at:

          https://github.com/indigo-dc/udocker/tree/master/doc
          https://github.com/indigo-dc/udocker/tree/devel/doc

        Udocker requires additional tools to run. These are available
        in the udocker tarball. The tarballs are available at several
        locations. By default udocker will install from the locations
        defined in self.conf['tarball'].

        To install from files or other URLs use these instructions:

        1) set UDOCKER_TARBALL to a remote URL or local filename:

          $ export UDOCKER_TARBALL=http://host/path
          or
          $ export UDOCKER_TARBALL=/tmp/filename

        2) run udocker with the install command or optionally using
           the option --force to overwrite the local installation:

          ./udocker install
          or
          ./udocker install --force

        3) once installed the binaries and containers will be placed
           by default under $HOME/.udocker

        """
        Msg().out(self._instructions.__doc__, l=Msg.ERR)
        Msg().out("        udocker version:", __version__,
                  "requires tarball release:", self._tarball_release, l=Msg.ERR)

    def _get_mirrors(self, mirrors):
        """Get shuffled list of tarball mirrors"""
        if isinstance(mirrors, str):
            mirrors = mirrors.split(" ")
        try:
            random.shuffle(mirrors)
        except NameError:
            pass
        return mirrors

    def get_installinfo(self):
        """Get json containing installation info"""
        (infofile, dummy) = self._get_file(self._get_mirrors(self._installinfo))
        try:
            with open(infofile, "r") as filep:
                self._install_json = json.load(filep)
            for msg in self._install_json["messages"]:
                Msg().err("Info:", msg)
        except (KeyError, AttributeError, ValueError,
                OSError, IOError):
            Msg().err("Info: no messages available", l=Msg.VER)
        return self._install_json

    def install(self, force=False):
        """Get the udocker tarball and install the binaries"""
        if self._is_available() and not force:
            return True
        elif not self._autoinstall and not force:
            Msg().err("Warning: no engine available and autoinstall disabled",
                      l=Msg.WAR)
            return False
        elif not self._tarball:
            Msg().err("Error: UDOCKER_TARBALL not defined")
        else:
            Msg().err("Info: installing", self._tarball_release, l=Msg.INF)
            (tfile, url) = self._get_file(self._get_mirrors(self._tarball))
            if tfile:
                Msg().err("Info: installing from:", url, l=Msg.VER)
                status = False
                if not self._verify_version(tfile):
                    Msg().err("Error: wrong tarball version:", url)
                else:
                    status = self._install(tfile)
                if "://" in url:
                    FileUtil(self.conf, tfile).remove()
                    if status:
                        self.get_installinfo()
                if status:
                    return True
            Msg().err("Error: installing tarball:", self._tarball)
        self._instructions()
        return False
