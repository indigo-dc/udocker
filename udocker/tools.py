# -*- coding: utf-8 -*-
"""Tools for udocker"""

import os
import tarfile
import random
import json
import stat
import shutil
from udocker import __version__, LOG, MSG
from udocker.config import Config
from udocker.utils.curl import GetURL
from udocker.utils.fileutil import FileUtil
from udocker.helper.hostinfo import HostInfo
from udocker.utils.chksum import ChkSUM


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

    # This method is from the old install, in the new install there is download of metadata.json
    # with latest tarball version
    # def _version_isok(self, version):
    #     """Is version >= than the minimum required tarball release"""
    #     if not (version and self._tarball_release):
    #         return False

    #     tarball_version_int = self._version2int(version)
    #     required_version_int = self._version2int(self._tarball_release)
    #     return tarball_version_int >= required_version_int

    # TO BE Removed/deprecated, the other downloadtar methods already verify this
    # def is_available(self):
    #     """Are the tools already installed"""
    #     version_file = self.localrepo.libdir + "/VERSION"
    #     version = FileUtil(version_file).getdata('r').strip()
    #     return self._version_isok(version)

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
            LOG.debug("get %s from %s.", fileout, url)
            filename = self._download(url, fileout)
        elif os.path.exists(url):
            LOG.debug("file %s exists.", url)
            filename = os.path.realpath(url)
            if fileout:
                LOG.debug("copy file %s to %s.", filename, fileout)
                shutil.copy2(filename, fileout)

        if filename and os.path.isfile(filename):
            return filename

        return ""

    # This method is from the old install, in the new install_mods the verification is the sha256sum
    # def _verify_version(self, tarball_file):
    #     """verify the tarball version"""
    #     if not (tarball_file and os.path.isfile(tarball_file)):
    #         return (False, "")

    #     tmpdir = FileUtil("VERSION").mktmpdir()
    #     if not tmpdir:
    #         return (False, "")

    #     # (mdavid) redo this part
    #     try:
    #         tfile = tarfile.open(tarball_file, "r:gz")
    #         for tar_in in tfile.getmembers():
    #             if tar_in.name.startswith("udocker_dir/lib/VERSION"):
    #                 tar_in.name = os.path.basename(tar_in.name)
    #                 tfile.extract(tar_in, path=tmpdir)

    #         tfile.close()
    #     except tarfile.TarError:
    #         FileUtil(tmpdir).remove(recursive=True)
    #         return (False, "")

    #     tarball_version = FileUtil(tmpdir + "/VERSION").getdata('r').strip()
    #     status = self._version_isok(tarball_version)
    #     FileUtil(tmpdir).remove(recursive=True)
    #     return (status, tarball_version)

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

    # This method has never been used, we may seek better way to give important info
    # def get_installinfo(self):
    #     """Get json containing installation info"""
    #     LOG.info("searching for messages:")
    #     for url in self._get_mirrors(self._installinfo):
    #         infofile = self._get_file(url)
    #         try:
    #             with open(infofile, 'r', encoding='utf-8') as filep:
    #                 self._install_json = json.load(filep)

    #             for msg in self._install_json["messages"]:
    #                 MSG.info(msg)

    #         except (KeyError, AttributeError, ValueError, OSError):
    #             LOG.info("no messages: %s %s", infofile, url)

    #         return self._install_json

    # This method is from the old install and should removed
    # def _install_logic(self, force=False):
    #     """Obtain random mirror, download, verify and install"""
    #     for url in self._get_mirrors(self._tarball):
    #         LOG.info("install using: %s", url)
    #         tarballfile = self._get_file(url)
    #         (status, version) = self._verify_version(tarballfile)
    #         if status:
    #             LOG.info("installing udockertools %s", version)
    #             status = self._install(tarballfile)
    #         elif force:
    #             LOG.info("forcing install of udockertools %s", version)
    #             status = self._install(tarballfile)
    #         else:
    #             LOG.error("version is %s for %s", version, url)

    #         if "://" in url and tarballfile:
    #             FileUtil(tarballfile).remove()
    #             LOG.debug("Removing tarfile: %s", tarballfile)

    #         if status:
    #             return True

    #     return False

    # This is the OLD method to be removed
    # def install_old(self, force=False):
        # """Get the udocker tools tarball and install the binaries"""

        # if self.is_available() and not force:
        #     LOG.debug("tarball already installed, installation skipped")
        #     return True

        # Implemented in the new install_mods
        # if not self._autoinstall and not force:
        #     LOG.warning("installation missing and autoinstall disabled")
        #     return None

        # if not self._tarball:
        #     LOG.info("UDOCKER_TARBALL not set, installation skipped")
        #     return True

        # LOG.info("udocker command line interface %s", __version__)
        # LOG.info("searching for udockertools %s", self._tarball_release)
        # retry = self._installretry
        # while retry:
        #     if self._install_logic(force):
        #         self.get_installinfo()
        #         LOG.info("installation of udockertools successful")
        #         return True

        #     retry = retry - 1
        #     LOG.error("installation failure retrying ...")

        # self._instructions()
        # self.get_installinfo()
        # LOG.error("installation of udockertools failed")
        # return False

    def get_metadata(self, force):
        """Download metadata file with modules and versions and output json"""
        fileout = Config.conf['metadata_file']
        for urlmeta in self._get_mirrors(Config.conf['metadata_url']):
            mjson = fileout
            if force or not os.path.isfile(fileout):
                LOG.info("url metadata json of modules: %s", urlmeta)
                mjson = self._get_file(urlmeta, fileout)

            LOG.debug("metadata json: %s", mjson)
            try:
                with open(mjson, 'r', encoding='utf-8') as filep:
                    metadict = json.load(filep)

                return metadict

            except (KeyError, AttributeError, ValueError, OSError):
                LOG.error("reading file: %s", mjson)
                continue

        return []

    def _select_modules(self, list_uid, list_names):
        """Get the list of modules from a list of UIDs, or a list of module names"""
        force = True
        metadict = self.get_metadata(force)
        list_modules = []
        if list_names:
            LOG.debug('list of module names: %s', list_names)
            for name in list_names:
                for module in metadict:
                    if module['name'] == name:
                        list_modules.append(module)
                        break

            return list_modules

        if list_uid:
            LOG.debug('list of uids: %s', list_uid)
            for uid in list_uid:
                for module in metadict:
                    if module['uid'] == uid:
                        list_modules.append(module)
                        break
        else:
            for module in metadict:
                tarname = module['fname']
                if tarname in ('libfakechroot.tgz', 'patchelf-x86_64.tgz'):
                    LOG.debug('matched module: %s', module)
                    list_modules.append(module)

            hostinfo = HostInfo()
            arch = hostinfo.arch()
            for module in metadict:
                mod_module = module['module']
                mod_arch = module['arch']
                mod_krnver = module['kernel_ver']
                if (mod_module == 'proot') and (mod_arch == arch):
                    if hostinfo.oskernel_isgreater([4, 8, 0]) and (mod_krnver == '>=4.8.0'):
                        LOG.debug('matched module: %s', module)
                        list_modules.append(module)

                    if not hostinfo.oskernel_isgreater([4, 8, 0]) and (mod_krnver == '<4.8.0'):
                        LOG.debug('matched module: %s', module)
                        list_modules.append(module)

        return list_modules

    def verify_sha(self, lmodules, dst_dir):
        """Verify if the list of downloaded modules have correct sha256sum"""
        validation = True
        for modul in lmodules:
            tarballfile = dst_dir + "/" + modul['fname']
            sha_metadata = modul['sha256sum']
            sha_file = ChkSUM().sha256(tarballfile)
            LOG.debug("sha256sum of %s match. Correct %s, Calculated %s",
                     tarballfile, sha_metadata, sha_file)
            if sha_metadata != sha_file:
                LOG.error("sha256sum of %s does not match. Correct %s, Calculated %s",
                          tarballfile, sha_metadata, sha_file)
                validation = validation and False

        return validation

    def download_tarballs(self, list_uid, dst_dir, from_locat, force):
        """Download list of tarballs from the list of UIDs
        Check for default files based on the host OS and arch
        or download from the list of uids in list_uid"""
        lmodules = self._select_modules(list_uid, [])
        for modul in lmodules:
            locations = modul['urls']
            tarballfile = dst_dir + "/" + modul['fname']
            if from_locat:
                locations = [from_locat + "/" + modul['fname']]

            LOG.debug("locations: %s", locations)
            LOG.debug("tarball output: %s", tarballfile)
            for url in locations:
                LOG.debug("downloading from: %s", url)
                if not force and os.path.isfile(tarballfile):
                    LOG.info("tarball already downloaded")
                    break

                outfile = self._get_file(url, tarballfile)
                if outfile:
                    LOG.info('module downloaded: %s - %s', modul['module'], outfile)
                    break

                LOG.error("download failed: %s", modul)

        if self.verify_sha(lmodules, dst_dir):
            return True

        LOG.error("failure in one or more downloaded modules")
        return False

    def show_metadata(self, force):
        """Show available modules and versions"""
        metadict = self.get_metadata(force)
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

    def _installmod_logic(self, list_uid, top_dir, tar_dir, force):
        """Logics for installation of modules"""
        lmodules = self._select_modules(list_uid, [])
        for modul in lmodules:
            tarballfile = tar_dir + '/' + modul['fname']
            if modul['installdir'] == 'bin/' and not top_dir:
                mod_dir = self.localrepo.bindir
            elif modul['installdir'] == 'lib/' and not top_dir:
                mod_dir = self.localrepo.libdir
            elif top_dir:
                mod_dir = top_dir + '/' + modul['installdir']
            else:
                LOG.error('unknown installation dir %s.', modul['installdir'])

            try:
                with tarfile.open(tarballfile, "r:gz") as tar_file:
                    list_files = tar_file.getnames()
                    mods_exists = False
                    for tar_member in list_files:
                        full_path = mod_dir + tar_member
                        if not force and os.path.isfile(full_path):
                            mods_exists = True
                            LOG.debug('module already installed: %s', full_path)
                        else:
                            mods_exists = False
                            break

                    if not mods_exists:
                        LOG.info('installing tarfile: %s - in: %s', tarballfile, mod_dir)
                        tar_file.extractall(path=mod_dir)

            except tarfile.TarError:
                LOG.error('failed to install module: %s.', tarballfile)
                continue

        return True

    def install_modules(self, list_uid, top_dir, from_locat, force=False):
        """Install modules"""
        tar_dir = self.localrepo.tardir
        if from_locat:
            tar_dir = from_locat

        # Get version of tarball from module "all"
        mod_all = self._select_modules([], ['all'])
        tools_version = mod_all[0]['version']
        if not self._autoinstall and not force:
            LOG.warning("installation missing and autoinstall disabled")
            return None

        if not self._tarball:
            LOG.info("UDOCKER_TARBALL not set, installation skipped")
            return True

        LOG.info("udocker command line interface %s", __version__)
        LOG.info("searching for udockertools %s", tools_version)
        retry = self._installretry
        while retry:
            flag_download = self.download_tarballs(list_uid, tar_dir, "", False)
            flag_install = self._installmod_logic(list_uid, top_dir, tar_dir, force)
            if flag_download and flag_install:
                LOG.info("installation of udockertools successful")
                return True

            retry = retry - 1
            LOG.error("installation failure retrying ...")

        self._instructions()
        LOG.error("installation of udockertools failed")
        return False
