# -*- coding: utf-8 -*-
"""Tools for udocker"""

import os
import sys
import tarfile
import random
import json
import stat

from udocker import is_genstr
from udocker.config import Config
from udocker.utils.curl import GetURL
from udocker.utils.fileutil import FileUtil
from udocker.msg import Msg
from udocker import __version__

def _str(data):
    """Safe str for Python 3 and Python 2"""
    if sys.version_info[0] >= 3:
        try:
            return data.decode()
        except (UnicodeDecodeError, AttributeError):
            pass
    return data


class UdockerTools(object):
    """Download and setup of the udocker supporting tools
    Includes: proot and alternative python modules, these
    are downloaded to facilitate the installation by the
    end-user.
    """

    def __init__(self, localrepo):
        self.localrepo = localrepo        # LocalRepository object
        self._autoinstall = Config.conf['autoinstall']  # True / False
        self._tarball = Config.conf['tarball']  # URL or file
        self._installinfo = Config.conf['installinfo']  # URL or file
        self._tarball_release = Config.conf['tarball_release']
        self._installretry = Config.conf['installretry']
        self._install_json = {}
        self.curl = GetURL()

    def _instructions(self):
        """
        Udocker installation instructions are available at:

          https://github.com/indigo-dc/udocker/tree/master/doc
          https://github.com/indigo-dc/udocker/tree/devel/doc

        Udocker requires additional tools to run. These are available
        in the udocker tarball. The tarballs are available at several
        locations. By default udocker will install from the locations
        defined in Config.tarball.

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
        Msg().out("udocker command line interface version:", __version__,
                  "\nrequires udockertools tarball release :",
                  self._tarball_release, l=Msg.ERR)

    def _version2int(self, version):
        """Convert version string to integer"""
        version_int = 0
        factor = 1000 * 1000
        for vitem in _str(version).strip().split('.'):
            try:
                version_int = version_int + (int(vitem) * factor)
            except (TypeError, ValueError):
                pass
            factor = factor / 1000
        return int(version_int)

    def _version_isok(self, version):
        """Is version >= than the minimum required tarball release"""
        if not (version and self._tarball_release):
            return False
        tarball_version_int = self._version2int(version)
        required_version_int = self._version2int(self._tarball_release)
        return tarball_version_int >= required_version_int

    def is_available(self):
        """Are the tools already installed"""
        version = \
            FileUtil(self.localrepo.libdir + "/VERSION").getdata('r').strip()
        return self._version_isok(version)

    def purge(self):
        """Remove existing files in bin, lib and doc"""
        for f_name in os.listdir(self.localrepo.bindir):
            f_path = self.localrepo.bindir + '/' + f_name
            FileUtil(f_path).register_prefix()
            FileUtil(f_path).remove(recursive=True)
        for f_name in os.listdir(self.localrepo.libdir):
            f_path = self.localrepo.libdir + '/' + f_name
            FileUtil(f_path).register_prefix()
            FileUtil(f_path).remove(recursive=True)
        for f_name in os.listdir(self.localrepo.docdir):
            f_path = self.localrepo.docdir + '/' + f_name
            FileUtil(f_path).register_prefix()
            FileUtil(f_path).remove(recursive=True)

    def _download(self, url):
        """Download a file """
        download_file = FileUtil("udockertools").mktmp()
        if Msg.level <= Msg.DEF:
            Msg().setlevel(Msg.NIL)
        (hdr, dummy) = self.curl.get(url, ofile=download_file, follow=True)
        if Msg.level == Msg.NIL:
            Msg().setlevel()
        try:
            if "200" in hdr.data["X-ND-HTTPSTATUS"]:
                return download_file
        except (KeyError, TypeError, AttributeError):
            pass
        FileUtil(download_file).remove()
        return ""

    def _get_file(self, url):
        """Get file from list of possible locations file or internet"""
        filename = ""
        if "://" in url:
            filename = self._download(url)
        elif os.path.exists(url):
            filename = os.path.realpath(url)
        if filename and os.path.isfile(filename):
            return filename
        return ""

    def _verify_version(self, tarball_file):
        """verify the tarball version"""
        if not (tarball_file and os.path.isfile(tarball_file)):
            return (False, "")

        tmpdir = FileUtil("VERSION").mktmpdir()
        if not tmpdir:
            return (False, "")

        try:
            tfile = tarfile.open(tarball_file, "r:gz")
            for tar_in in tfile.getmembers():
                if tar_in.name.startswith("udocker_dir/lib/VERSION"):
                    tar_in.name = os.path.basename(tar_in.name)
                    tfile.extract(tar_in, path=tmpdir)
            tfile.close()
        except tarfile.TarError:
            FileUtil(tmpdir).remove(recursive=True)
            return (False, "")
        tarball_version = FileUtil(tmpdir + "/VERSION").getdata('r').strip()
        status = self._version_isok(tarball_version)
        FileUtil(tmpdir).remove(recursive=True)
        return (status, tarball_version)

    def _install(self, tarball_file):
        """Install the tarball"""
        if not (tarball_file and os.path.isfile(tarball_file)):
            return False
        FileUtil(self.localrepo.topdir).chmod()
        self.localrepo.create_repo()

        try:
            tfile = tarfile.open(tarball_file, "r:gz")
            FileUtil(self.localrepo.bindir).rchmod()
            for tar_in in tfile.getmembers():
                if tar_in.name.startswith("udocker_dir/bin/"):
                    tar_in.name = os.path.basename(tar_in.name)
                    Msg().out("Info: extrating", tar_in.name, l=Msg.DBG)
                    tfile.extract(tar_in, self.localrepo.bindir)
            FileUtil(self.localrepo.bindir).rchmod(stat.S_IRUSR |
                                                   stat.S_IWUSR |
                                                   stat.S_IXUSR)

            FileUtil(self.localrepo.libdir).rchmod()
            for tar_in in tfile.getmembers():
                if tar_in.name.startswith("udocker_dir/lib/"):
                    tar_in.name = os.path.basename(tar_in.name)
                    Msg().out("Info: extrating", tar_in.name, l=Msg.DBG)
                    tfile.extract(tar_in, self.localrepo.libdir)
            FileUtil(self.localrepo.libdir).rchmod()

            FileUtil(self.localrepo.docdir).rchmod()
            for tar_in in tfile.getmembers():
                if tar_in.name.startswith("udocker_dir/doc/"):
                    tar_in.name = os.path.basename(tar_in.name)
                    Msg().out("Info: extrating", tar_in.name, l=Msg.DBG)
                    tfile.extract(tar_in, self.localrepo.docdir)
            FileUtil(self.localrepo.docdir).rchmod()
            tfile.close()
        except tarfile.TarError:
            return False
        return True

    def _get_mirrors(self, mirrors):
        """Get shuffled list of tarball mirrors"""
        if is_genstr(mirrors):
            mirrors = mirrors.split(' ')
        try:
            random.shuffle(mirrors)
        except NameError:
            pass
        return mirrors

    def get_installinfo(self):
        """Get json containing installation info"""
        Msg().out("Info: searching for messages:", l=Msg.VER)
        for url in self._get_mirrors(self._installinfo):
            infofile = self._get_file(url)
            try:
                with open(infofile, 'r', encoding='utf-8') as filep:
                    self._install_json = json.load(filep)
                for msg in self._install_json["messages"]:
                    Msg().out("Info:", msg)
            except (KeyError, AttributeError, ValueError,
                    OSError, IOError):
                Msg().out("Info: no messages:", infofile, url, l=Msg.VER)
            return self._install_json

    def _install_logic(self, force=False):
        """Obtain random mirror, download, verify and install"""
        for url in self._get_mirrors(self._tarball):
            Msg().out("Info: install using:", url, l=Msg.VER)
            tarballfile = self._get_file(url)
            (status, version) = self._verify_version(tarballfile)
            if status:
                Msg().out("Info: installing udockertools", version)
                status = self._install(tarballfile)
            elif force:
                Msg().out("Info: forcing install of udockertools", version)
                status = self._install(tarballfile)
            else:
                Msg().err("Error: version is", version, "for", url, l=Msg.VER)
            if "://" in url and tarballfile:
                FileUtil(tarballfile).remove()
            if status:
                return True
        return False

    def install(self, force=False):
        """Get the udocker tools tarball and install the binaries"""
        if self.is_available() and not force:
            return True

        if not self._autoinstall and not force:
            Msg().out("Warning: installation missing and autoinstall disabled",
                      l=Msg.WAR)
            return None

        if not self._tarball:
            Msg().out("Info: UDOCKER_TARBALL not set, installation skipped",
                      l=Msg.VER)
            return True

        Msg().out("Info: udocker command line interface", __version__)
        Msg().out("Info: searching for udockertools",
                  self._tarball_release, l=Msg.INF)
        retry = self._installretry
        while  retry:
            if self._install_logic(force):
                self.get_installinfo()
                Msg().out("Info: installation of udockertools successful")
                return True

            retry = retry - 1
            Msg().err("Error: installation failure retrying ...", l=Msg.VER)

        self._instructions()
        self.get_installinfo()
        Msg().err("Error: installation of udockertools failed")
        return False
