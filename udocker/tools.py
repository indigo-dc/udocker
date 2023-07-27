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
    '''Safe str for Python 3'''
    try:
        return data.decode()
    except (UnicodeDecodeError, AttributeError):
        pass

    return data


class UdockerTools:
    ''' Download and setup of the udocker supporting tools
        Includes: proot and alternative python modules, these
        are downloaded to facilitate the installation by the
        end-user.
    '''

    def __init__(self, localrepo):
        self.localrepo = localrepo                       # LocalRepository object
        self._autoinstall = Config.conf['autoinstall']   # True / False
        self._tarball_release = Config.conf['tarball_release']
        self._installretry = Config.conf['installretry']
        self._install_json = {}
        self.curl = GetURL()

    # TODO Review instructions
    def _instructions(self):
        '''
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
        '''

        msgout = "udocker command line interface version: " + __version__
        msgout = msgout + "\nrequires udocker tool modules from: " + self._tarball_release
        MSG.info(self._instructions.__doc__)
        MSG.info(msgout)

    def _version2int(self, version):
        '''Convert version string to integer'''
        version_int = 0
        factor = 1000 * 1000
        for vitem in _str(version).strip().split('.'):
            try:
                version_int = version_int + (int(vitem) * factor)
            except (TypeError, ValueError):
                pass

            factor = int(factor / 1000)

        return int(version_int)

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

    def _download(self, url, fileout=''):
        '''Download a file'''
        if fileout:
            download_file = fileout
        else:
            download_file = FileUtil('udockertools').mktmp()

        (hdr, dummy) = self.curl.get(url, ofile=download_file, follow=True)
        try:
            if '200' in hdr.data['X-ND-HTTPSTATUS']:
                return download_file
        except (KeyError, TypeError, AttributeError):
            pass

        FileUtil(download_file).remove()
        return ""

    def _get_file(self, url, fileout=""):
        ''' Get file from list of possible locations file or internet,
            url: URL or local file
            fileout: full filename of downloaded file
        '''
        filename = ''
        if '://' in url:
            LOG.debug('get %s from %s.', fileout, url)
            filename = self._download(url, fileout)
        elif os.path.exists(url):
            LOG.debug('file %s exists.', url)
            filename = os.path.realpath(url)
            if fileout:
                LOG.debug('copy file %s to %s.', filename, fileout)
                shutil.copy2(filename, fileout)

        if filename and os.path.isfile(filename):
            return filename

        return ''

    def _clean_install(self, tfile):
        '''Remove files before install'''
        for tar_in in tfile.getmembers():
            basename = os.path.basename(tar_in.name)
            if tar_in.name.startswith('udocker_dir/bin/'):
                f_path = self.localrepo.bindir + '/' + basename
                FileUtil(f_path).register_prefix()
                FileUtil(f_path).remove(recursive=True)

            if tar_in.name.startswith('udocker_dir/lib/'):
                f_path = self.localrepo.libdir + '/' + basename
                FileUtil(f_path).register_prefix()
                FileUtil(f_path).remove(recursive=True)

            if tar_in.name.startswith('udocker_dir/doc/'):
                f_path = self.localrepo.docdir + '/' + basename
                FileUtil(f_path).register_prefix()
                FileUtil(f_path).remove(recursive=True)

    def _get_mirrors(self, mirrors):
        '''Get shuffled list of tarball mirrors'''
        if isinstance(mirrors, str):
            mirrors = mirrors.split('\n')

        try:
            random.shuffle(mirrors)
        except NameError:
            pass

        return mirrors

    def get_metadata(self, force):
        ''' Download metadata file with modules and versions and output json
        '''
        fileout = Config.conf['installdir'] + '/' + Config.conf['metadata_json']
        LOG.debug('metadata full path: %s', fileout)
        for urlmeta in self._get_mirrors(Config.conf['metadata_url']):
            mjson = fileout
            if force or not os.path.isfile(fileout):
                LOG.debug('url metadata json of modules: %s', urlmeta)
                mjson = self._get_file(urlmeta, fileout)

            LOG.debug('metadata json: %s', mjson)
            try:
                with open(mjson, 'r', encoding='utf-8') as filep:
                    metadict = json.load(filep)

                return metadict

            except (KeyError, AttributeError, ValueError, OSError):
                LOG.error('reading file: %s', mjson)
                continue

        return []

    def _select_modules(self, list_uid, list_names):
        '''Get the list of modules from a list of UIDs, or a list of module names
        '''
        force = True
        metadict = self.get_metadata(force)
        list_modules = []
        if list_names:
            LOG.debug('list of module names: %s', list_names)
            for name in list_names:
                for module in metadict:
                    if module['module'] == name:
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
        '''Verify if the list of downloaded modules have correct sha256sum'''
        validation = True
        for modul in lmodules:
            tarfile = dst_dir + '/' + modul['fname']
            sha_meta = modul['sha256sum']
            sha_file = ChkSUM().sha256(tarfile)
            LOG.debug('sha256sum of %s match. Correct %s, Calc %s', tarfile, sha_meta, sha_file)
            if sha_meta != sha_file:
                LOG.error('sha256sum of %s does not match. Correct %s, Calc %s',
                          tarfile, sha_meta, sha_file)
                validation = validation and False

        return validation

    def download_tarballs(self, list_uid, dst_dir, from_locat, force):
        ''' Download list of tarballs from the list of UIDs
            Check for default files based on the host OS and arch
            or download from the list of uids in list_uid
        '''
        lmodules = self._select_modules(list_uid, [])
        for modul in lmodules:
            locations = modul['urls']
            tarballfile = dst_dir + "/" + modul['fname']
            if from_locat:
                locations = [from_locat + '/' + modul['fname']]

            LOG.debug('locations: %s - outuput: %s', locations, tarballfile)
            for url in locations:
                LOG.debug('downloading from: %s', url)
                if not force and os.path.isfile(tarballfile):
                    LOG.info('tarball already downloaded: %s', tarballfile)
                    break

                outfile = self._get_file(url, tarballfile)
                if outfile:
                    LOG.info('module downloaded: %s - %s', modul['module'], outfile)
                    break

                LOG.error('download failed: %s', modul)

        if self.verify_sha(lmodules, dst_dir):
            return True

        LOG.error('failure in one or more downloaded modules')
        return False

    def delete_tarballs(self, list_uid, dst_dir):
        ''' Delete tarballs corresponding to modules list_uid'''
        ret_value = True
        force = False
        if list_uid:
            lmodules = self._select_modules(list_uid, [])
        else:
            lmodules = self.get_metadata(force)

        for module in lmodules:
            if os.path.exists(dst_dir + '/' + module['fname']):
                try:
                    os.remove(dst_dir + '/' + module['fname'])
                    LOG.info('module %s - file %s removed', module['uid'], module['fname'])
                except OSError as oserr:
                    LOG.error('Error: %s - %s.', oserr.filename, oserr.strerror)
                    ret_value = False

        return ret_value

    def download_licenses(self, dst_dir, from_locat, force):
        '''Download Licenses'''
        mod_all = self._select_modules([], ['all'])
        locations = mod_all[0]['docs_url']
        tballfile = dst_dir + '/' + mod_all[0]['docs']
        if from_locat:
            locations = [from_locat + '/' + mod_all[0]['docs']]

        LOG.debug('licenses locations: %s - outuput: %s', locations, tballfile)
        for url in locations:
            LOG.debug('downloading from: %s', url)
            if not force and os.path.isfile(tballfile):
                LOG.info('tarball with licenses already downloaded')
                return True

            outfile = self._get_file(url, tballfile)
            if outfile:
                LOG.info('licenses downloaded: %s', outfile)
                return True

        LOG.error('download failed: %s', tballfile)
        return False

    def show_metadata(self, metadict, long=False):
        '''Show available modules and versions'''
        if long:
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

        for module in metadict:
            MSG.info(120*"_")
            MSG.info("UID = %s\tModule = %s\tFilename = %s",
                     module["uid"], module["module"], module["fname"])

        return True

    def _installmod_logic(self, list_uid, top_dir, tar_dir, force):
        '''Logics for installation of modules'''
        lmodules = self._select_modules(list_uid, [])
        mod_dir = ''
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
                with tarfile.open(tarballfile, 'r:gz') as tar_file:
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
                        self._clean_install(tar_file)
                        tar_file.extractall(path=mod_dir)

            except tarfile.TarError:
                LOG.error('failed to install module: %s.', tarballfile)
                continue

        FileUtil(self.localrepo.bindir).rchmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        FileUtil(self.localrepo.libdir).rchmod()
        return True

    def _install_licenses(self, mod_all, top_dir, tar_dir, force):
        ''' Install all licenses in docs directory
        '''
        tarballfile = tar_dir + '/' + mod_all['docs']
        doc_dir = self.localrepo.docdir
        if top_dir:
            doc_dir = top_dir + '/doc/'

        try:
            with tarfile.open(tarballfile, 'r:gz') as tar_file:
                list_files = tar_file.getnames()
                licenses_exists = False
                for tar_member in list_files:
                    full_path = doc_dir + tar_member
                    if not force and os.path.isfile(full_path):
                        licenses_exists = True
                        LOG.debug('licenses already installed: %s', full_path)
                    else:
                        licenses_exists = False
                        break

                if not licenses_exists:
                    LOG.info('installing licenses: %s - in: %s', tarballfile, doc_dir)
                    tar_file.extractall(path=doc_dir)

        except tarfile.TarError:
            LOG.error('failed to install licenses: %s.', tarballfile)
            return False

        FileUtil(self.localrepo.docdir).rchmod()
        return True

    def install_modules(self, list_uid, install_dir, from_locat, force=False):
        ''' Install modules
        '''
        tar_dir = self.localrepo.tardir
        if from_locat:
            tar_dir = from_locat

        # Get version of tarball from module "all"
        mod_all = self._select_modules([], ['all'])[0]
        tools_version = mod_all['version']
        if not self._autoinstall and not force:
            LOG.warning('installation missing and autoinstall disabled')
            return None

        LOG.info('udocker command line interface %s', __version__)
        LOG.info('searching for udockertools %s', tools_version)
        retry = self._installretry
        while retry:
            flag_download = self.download_tarballs(list_uid, tar_dir, "", False)
            flag_download_lic = self.download_licenses(tar_dir, "", False)
            flag_install = self._installmod_logic(list_uid, install_dir, tar_dir, force)
            flag_licenses = self._install_licenses(mod_all, install_dir, tar_dir, force)
            if flag_download_lic and flag_licenses:
                LOG.info('licenses installed successful')
            else:
                LOG.error('install of licenses failed, check %s, or retry', mod_all['docs_url'])

            if flag_download and flag_install:
                LOG.info('installation of udockertools successful')
                return True

            retry = retry - 1
            LOG.error('installation failure retrying ...')

        self._instructions()
        LOG.error('installation of udockertools failed')
        return False

    def get_modules(self, list_uid, action, prefix):
        ''' Get and manage installed modules through the file installed.json
            list_uid: List of UIds of installed modules
            action: update, delete, show (update also creates if the json does not exist)
            prefix: directory where modules are installed
        '''
        mod_inst = []
        new_mods = []
        install_json = Config.conf['installdir'] + '/' + Config.conf['installed_json']
        if prefix:
            install_json = prefix + '/' + Config.conf['installed_json']

        LOG.debug('action = %s\tlist of uids = %s', action, list_uid)
        json_exists = os.path.isfile(install_json)
        if json_exists:
            try:
                with open(install_json, 'r', encoding='utf-8') as filep:
                    mod_inst = json.load(filep)

            except (KeyError, AttributeError, ValueError, OSError):
                LOG.error('reading file: %s', install_json)
                return mod_inst

        if action == 'show':
            return mod_inst

        if action in ('update'):
            new_mods = self._select_modules(list_uid, [])
            for nmod in new_mods:
                if nmod not in mod_inst:
                    mod_inst.append(nmod)
                else:
                    LOG.warning('module %s already installed', nmod)

        if action == 'delete':
            del_mods = self._select_modules(list_uid, [])
            for dmod in del_mods:
                if dmod in mod_inst:
                    mod_inst.remove(dmod)
                else:
                    LOG.warning('module to be removed not installed: %s', dmod)

        try:
            with open(install_json, 'w', encoding='utf-8') as filep:
                json.dump(mod_inst, filep)

        except (KeyError, AttributeError, ValueError, OSError):
            LOG.error('writing file: %s', install_json)

        return mod_inst
