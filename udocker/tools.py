# -*- coding: utf-8 -*-
"""Tools for udocker"""

import os
import tarfile
import random
import json
import stat
from udocker import __version__, LOG, MSG
from udocker.config import Config
from udocker.utils.curl import GetURL
from udocker.utils.fileutil import FileUtil
from udocker.helper.osinfo import OSInfo


def _str(data):
    """Safe str for Python 3"""
    try:
        return data.decode()
    except (UnicodeDecodeError, AttributeError):
        pass

    return data


class UdockerTools:
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
        self._metajson = Config.conf['meta_json']
        self._install_json = {}
        self.curl = GetURL()

    def _instructions(self):
        """
        Udocker installation instructions are available at:

          https://indigo-dc.github.io/udocker/installation_manual.html

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
        msgout = "udocker command line interface version: " + __version__
        msgout = msgout + "\nrequires udockertools tarball release: " + self._tarball_release
        MSG.info(self._instructions.__doc__)
        MSG.info(msgout)

    def _version2int(self, version):
        """Convert version string to integer"""
        version_int = 0
        factor = 1000 * 1000
        for vitem in _str(version).strip().split('.'):
            try:
                version_int = version_int + (int(vitem) * factor)
            except (TypeError, ValueError):
                pass

            factor = int(factor / 1000)

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
        version_file = self.localrepo.libdir + "/VERSION"
        version = FileUtil(version_file).getdata('r').strip()
        return self._version_isok(version)

    def purge(self):
        """Remove existing files in bin, lib and doc"""
        for f_name in os.listdir(self.localrepo.bindir):
            f_path = self.localrepo.bindir + '/' + f_name
            FileUtil(f_path).register_prefix()
            FileUtil(f_path).remove(recursive=True)
            LOG.debug("removed file: %s", f_path)

        for f_name in os.listdir(self.localrepo.libdir):
            f_path = self.localrepo.libdir + '/' + f_name
            FileUtil(f_path).register_prefix()
            FileUtil(f_path).remove(recursive=True)
            LOG.debug("removed file: %s", f_path)

        for f_name in os.listdir(self.localrepo.docdir):
            f_path = self.localrepo.docdir + '/' + f_name
            FileUtil(f_path).register_prefix()
            FileUtil(f_path).remove(recursive=True)
            LOG.debug("removed file: %s", f_path)

    def _download(self, url, fileout=""):
        """Download a file """
        if fileout:
            download_file = fileout
        else:
            download_file = FileUtil("udockertools").mktmp()

        (hdr, dummy) = self.curl.get(url, ofile=download_file, follow=True)
        try:
            if "200" in hdr.data["X-ND-HTTPSTATUS"]:
                return download_file
        except (KeyError, TypeError, AttributeError):
            pass

        FileUtil(download_file).remove()
        return ""

    def _get_file(self, url, fileout=""):
        """Get file from list of possible locations file or internet,
        url: URL or local file
        fileout: full filename of downloaded file"""
        filename = ""
        if "://" in url:
            filename = self._download(url, fileout)
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

        # (mdavid) redo this part
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

    def _clean_install(self, tfile):
        """Remove files before install"""
        for tar_in in tfile.getmembers():
            basename = os.path.basename(tar_in.name)
            if tar_in.name.startswith("udocker_dir/bin/"):
                f_path = self.localrepo.bindir + '/' + basename
                FileUtil(f_path).register_prefix()
                FileUtil(f_path).remove(recursive=True)

            if tar_in.name.startswith("udocker_dir/lib/"):
                f_path = self.localrepo.libdir + '/' + basename
                FileUtil(f_path).register_prefix()
                FileUtil(f_path).remove(recursive=True)

            if tar_in.name.startswith("udocker_dir/doc/"):
                f_path = self.localrepo.docdir + '/' + basename
                FileUtil(f_path).register_prefix()
                FileUtil(f_path).remove(recursive=True)

    def _install(self, tarball_file):
        """Install the tarball"""
        if not (tarball_file and os.path.isfile(tarball_file)):
            return False

        FileUtil(self.localrepo.topdir).chmod()
        self.localrepo.create_repo()
        # (mdavid) redo this part
        try:
            tfile = tarfile.open(tarball_file, "r:gz")
            FileUtil(self.localrepo.bindir).rchmod()
            self._clean_install(tfile)
            for tar_in in tfile.getmembers():
                if tar_in.name.startswith("udocker_dir/bin/"):
                    tar_in.name = os.path.basename(tar_in.name)
                    LOG.debug("extracting %s", tar_in.name)
                    tfile.extract(tar_in, self.localrepo.bindir)

            FileUtil(self.localrepo.bindir).rchmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            FileUtil(self.localrepo.libdir).rchmod()
            for tar_in in tfile.getmembers():
                if tar_in.name.startswith("udocker_dir/lib/"):
                    tar_in.name = os.path.basename(tar_in.name)
                    LOG.debug("extracting %s", tar_in.name)
                    tfile.extract(tar_in, self.localrepo.libdir)

            FileUtil(self.localrepo.libdir).rchmod()
            FileUtil(self.localrepo.docdir).rchmod()
            for tar_in in tfile.getmembers():
                if tar_in.name.startswith("udocker_dir/doc/"):
                    tar_in.name = os.path.basename(tar_in.name)
                    LOG.debug("extrating %s", tar_in.name)
                    tfile.extract(tar_in, self.localrepo.docdir)

            FileUtil(self.localrepo.docdir).rchmod()
            tfile.close()
        except tarfile.TarError:
            return False

        return True

    def _get_mirrors(self, mirrors):
        """Get shuffled list of tarball mirrors"""
        if isinstance(mirrors, str):
            mirrors = mirrors.split('\n')

        try:
            random.shuffle(mirrors)
        except NameError:
            pass

        return mirrors

    def get_installinfo(self):
        """Get json containing installation info"""
        LOG.info("searching for messages:")
        for url in self._get_mirrors(self._installinfo):
            infofile = self._get_file(url)
            try:
                with open(infofile, 'r') as filep:
                    self._install_json = json.load(filep)

                for msg in self._install_json["messages"]:
                    MSG.info(msg)

            except (KeyError, AttributeError, ValueError, OSError):
                LOG.info("no messages: %s %s", infofile, url)

            return self._install_json

    def _install_logic(self, force=False):
        """Obtain random mirror, download, verify and install"""
        for url in self._get_mirrors(self._tarball):
            LOG.info("install using: %s", url)
            tarballfile = self._get_file(url)
            (status, version) = self._verify_version(tarballfile)
            if status:
                LOG.info("installing udockertools %s", version)
                status = self._install(tarballfile)
            elif force:
                LOG.info("forcing install of udockertools %s", version)
                status = self._install(tarballfile)
            else:
                LOG.error("version is %s for %s", version, url)

            if "://" in url and tarballfile:
                FileUtil(tarballfile).remove()
                LOG.debug("Removing tarfile: %s", tarballfile)

            if status:
                return True

        return False

    def install(self, force=False):
        """Get the udocker tools tarball and install the binaries"""
        if self.is_available() and not force:
            LOG.debug("tarball already installed, installation skipped")
            return True

        if not self._autoinstall and not force:
            LOG.warning("installation missing and autoinstall disabled")
            return None

        if not self._tarball:
            LOG.info("UDOCKER_TARBALL not set, installation skipped")
            return True

        LOG.info("udocker command line interface %s", __version__)
        LOG.info("searching for udockertools %s", self._tarball_release)
        retry = self._installretry
        while retry:
            if self._install_logic(force):
                self.get_installinfo()
                LOG.info("installation of udockertools successful")
                return True

            retry = retry - 1
            LOG.error("installation failure retrying ...")

        self._instructions()
        self.get_installinfo()
        LOG.error("installation of udockertools failed")
        return False

    def _get_metadata(self, force):
        """Download metadata file with modules and versions and output json"""
        fileout = Config.conf['topdir'] + "/" + "metadata.json"
        for urlmeta in self._get_mirrors(self._metajson):
            mjson = fileout
            if force or not os.path.isfile(fileout):
                LOG.info("url metadata json of modules: %s", urlmeta)
                mjson = self._get_file(urlmeta, fileout)

            LOG.info("metadata json: %s", mjson)
            try:
                with open(mjson, 'r') as filep:
                    metadict = json.load(filep)

                return metadict

            except (KeyError, AttributeError, ValueError, OSError):
                LOG.error("reading file: %s", mjson)
                continue

        return []

    def _match_mod(self, mod, arch, os_dist, os_ver, metadict):
        """matches a given module mod in the metadict metadata dictionary
        according to arch, os_dist and os_ver
        return the urls for the matched module"""
        for module in metadict:
            if (module['arch'] == arch) and (module['module'] == mod):
                if (module['os'] == os_dist) or (module['os'] == ''):
                    if (module['os_ver'] == os_ver) or (module['os_ver'] == ''):
                        LOG.debug('matched module: %s', module)
                        return module['urls']

        return []

    def select_tarnames(self, list_uid):
        """Get list of tarballs URL to download
        Check for default files based on the host OS and arch
        or download from the list of uids in list_uid"""
        force = True
        metadict = self._get_metadata(force)
        list_downl = []
        if list_uid:
            LOG.debug('list of uids: %s', list_uid)
            for uid in list_uid:
                for module in metadict:
                    if module['uid'] == uid:
                        LOG.debug('adding module urls: %s', module['urls'])
                        list_downl.append(module['urls'])
                        break
        else:
            LOG.debug('list of uids not given')
            osinfo = OSInfo('/')
            arch = osinfo.arch()
            (os_dist, os_ver) = osinfo.osdistribution()
            default_mod = ['proot', 'libfakechroot']
            for mod in default_mod:
                url_mod = self._match_mod(mod, arch, os_dist, os_ver, metadict)
                LOG.debug('download mod: %s, arch: %s, dist: %s, version: %s',
                          mod, arch, os_dist, os_ver)
                LOG.debug('adding module urls: %s', url_mod)
                list_downl.append(url_mod)

        LOG.info('list of modules to download: %s', list_downl)
        return list_downl

    def show_metadata(self, force):
        """Show available modules and versions"""
        metadict = self._get_metadata(force)
        if not metadict:
            return False

        for module in metadict:
            MSG.info(120*"_")
            MSG.info("UID:            %s", module["uid"])
            MSG.info("Module:         %s", module["module"])
            MSG.info("Filename:       %s", module["fname"])
            MSG.info("Version:        %s", module["version"])
            MSG.info("Architecture:   %s", module["arch"])
            MSG.info("Operating Sys:  %s", module["os"])
            MSG.info("OS version:     %s", module["os_ver"])
            MSG.info("Kernel version: %s", module["kernel_ver"])
            MSG.info("SHA256 sum:     %s", module["sha256sum"])
            MSG.info("URLs:")
            for url in module["urls"]:
                MSG.info("                %s", url)

            MSG.info("Documentation:")
            for url in module["docs_url"]:
                MSG.info("                %s", url)

            MSG.info("Dependencies:")
            for dep in module["dependencies"]:
                MSG.info("                %s", dep)

        return True
