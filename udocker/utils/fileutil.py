# -*- coding: utf-8 -*-
"""File utilities"""

import os
import sys
import stat
import re
import logging

from udocker import LOG
from udocker.config import Config
from udocker.helper.unique import Unique
from udocker.helper.hostinfo import HostInfo
from udocker.utils.uprocess import Uprocess
from udocker.utils.uvolume import Uvolume


class FileUtil:
    """Some utilities to manipulate files"""

    tmptrash = {}
    safe_prefixes = []
    orig_umask = None

    def __init__(self, filename=None):
        self._tmpdir = Config.conf['tmpdir']
        self.orig_filename = filename
        if filename == "-":
            self.filename = "-"
            self.basename = "-"
            return

        try:
            self.filename = os.path.abspath(filename)
            self.basename = os.path.basename(self.filename)
        except (AttributeError, TypeError):
            self.filename = filename
            self.basename = filename

        self._register_prefix(self._tmpdir)

    def _register_prefix(self, prefix):
        """Register directory prefixes where remove() is allowed"""
        if os.path.islink(prefix):
            prefix = os.path.realpath(os.path.dirname(prefix)) + "/" + os.path.basename(prefix)
        else:
            prefix = os.path.realpath(prefix)

        if prefix not in FileUtil.safe_prefixes:
            if os.path.isdir(prefix) and not prefix.endswith('/'):
                FileUtil.safe_prefixes.append(prefix + '/')
                FileUtil.safe_prefixes.append(os.path.realpath(prefix) + '/')
            else:
                FileUtil.safe_prefixes.append(prefix)
                FileUtil.safe_prefixes.append(os.path.realpath(prefix))

    def register_prefix(self):
        """Register directory prefixes where remove() is allowed"""
        self._register_prefix(self.filename)

    def umask(self, new_umask=None):
        """Set umask"""
        if new_umask is not None:
            try:
                old_umask = os.umask(new_umask)
            except (TypeError, ValueError):
                return False

            if FileUtil.orig_umask is None:
                FileUtil.orig_umask = old_umask
        else:
            try:
                os.umask(FileUtil.orig_umask)
            except (TypeError, ValueError):
                return False

        return True

    def mktmp(self):
        """Generate a temporary filename"""
        while True:
            tmp_file = self._tmpdir + '/' + Unique().filename(self.basename)
            if not os.path.exists(tmp_file):
                FileUtil.tmptrash[tmp_file] = True
                self.filename = tmp_file
                return tmp_file

    def mkdir(self):
        """Create directory"""
        try:
            os.makedirs(self.filename)
        except (OSError, AttributeError):
            return False

        return True

    def rmdir(self):
        """Remove an empty directory"""
        try:
            os.rmdir(self.filename)
        except (OSError, AttributeError):
            return False

        return True

    def mktmpdir(self):
        """Create temporary directory"""
        dirname = self.mktmp()
        if FileUtil(dirname).mkdir():
            return dirname

        return None

    def uid(self):
        """Get the file owner user id"""
        try:
            return os.lstat(self.filename).st_uid
        except OSError:
            return -1

    def _is_safe_prefix(self, fname):
        """Check if file prefix falls under valid prefixes"""
        if os.path.islink(fname):
            fname = os.path.realpath(os.path.dirname(fname)) + "/" + os.path.basename(fname)
        else:
            fname = os.path.realpath(fname)

        if os.path.isdir(fname):
            fname += '/'
        for safe_prefix in FileUtil.safe_prefixes:
            if fname.startswith(safe_prefix):
                return True

            if fname.startswith(os.path.realpath(safe_prefix)):
                return True

        return False

    def chown(self, uid=0, gid=0, recursive=False):
        """Change ownership of file or directory"""
        try:
            if recursive:
                for dir_path, dirs, files in os.walk(self.filename):
                    for f_name in dirs + files:
                        os.lchown(dir_path + '/' + f_name, uid, gid)
            else:
                os.lchown(self.filename, uid, gid)

        except OSError:
            return False

        return True

    def rchown(self, uid=0, gid=0):
        """Change ownership recursively"""
        return self.chown(uid, gid, recursive=True)

    def _chmod(self, filename, filemode=0o600, dirmode=0o700, mask=0o755):
        """chmod file or directory"""
        try:
            filestat = os.lstat(filename).st_mode
            if stat.S_ISREG(filestat) and filemode:
                mode = (stat.S_IMODE(filestat) & mask) | filemode
                os.chmod(filename, mode)
            elif stat.S_ISDIR(filestat) and dirmode:
                mode = (stat.S_IMODE(filestat) & mask) | dirmode
                os.chmod(filename, mode)
            elif stat.S_ISLNK(filestat) and filemode:
                pass
            elif filemode:
                mode = (stat.S_IMODE(filestat) & mask) | filemode
                os.chmod(filename, mode)

        except OSError:
            LOG.error("changing permissions of: %s", filename)

    def chmod(self, filemode=0o600, dirmode=0o700, mask=0o755, recursive=False):
        """chmod directory recursively"""
        try:
            if recursive:
                for dir_path, dirs, files in os.walk(self.filename):
                    for f_name in files:
                        self._chmod(dir_path + '/' + f_name, filemode, None, mask)

                    for f_name in dirs:
                        self._chmod(dir_path + '/' + f_name, None, dirmode, mask)

            # TODO: should be an else here, but needs test and confirmation
            self._chmod(self.filename, filemode, dirmode, mask)

        except OSError:
            return False

        return True

    def rchmod(self, filemode=0o600, dirmode=0o700, mask=0o755):
        """chmod directory recursively"""
        self.chmod(filemode, dirmode, mask, True)

    def _removedir(self):
        """Delete directory recursively"""
        try:
            for dir_path, dirs, files in os.walk(self.filename, topdown=False, followlinks=False):
                for f_name in files:
                    f_path = dir_path + '/' + f_name
                    if not os.path.islink(f_path):
                        os.chmod(f_path, stat.S_IWUSR | stat.S_IRUSR)

                    os.unlink(f_path)

                for f_name in dirs:
                    f_path = dir_path + '/' + f_name
                    if os.path.islink(f_path):
                        os.unlink(f_path)
                        continue

                    os.chmod(f_path, stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
                    os.rmdir(f_path)

            os.chmod(self.filename, stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
            os.rmdir(self.filename)

        except OSError:
            LOG.error("removing: %s", self.filename)
            return False

        return True

    def remove(self, force=False, recursive=False):
        """Delete files or directories"""
        if not os.path.lexists(self.filename):
            pass
        elif self.filename.count("/") < 2:
            LOG.error("delete pathname too short: %s", self.filename)
            return False
        elif self.uid() != HostInfo.uid:
            LOG.error("delete not owner: %s", self.filename)
            return False
        elif (not force) and (not self._is_safe_prefix(self.filename)):
            LOG.error("delete outside of directory tree: %s", self.filename)
            return False
        elif os.path.isfile(self.filename) or os.path.islink(self.filename):
            try:
                os.remove(self.filename)
            except OSError:
                LOG.error("deleting file: %s", self.filename)
                return False
        elif os.path.isdir(self.filename):
            if recursive:
                status = self._removedir()
            else:
                status = self.rmdir()

            if not status:
                LOG.error("deleting directory: %s", self.filename)
                return False

        if self.filename in dict(FileUtil.tmptrash):
            del FileUtil.tmptrash[self.filename]

        return True

    def verify_tar(self):
        """Verify a tar file: tar tvf file.tar"""
        if not os.path.isfile(self.filename):
            return False

        verbose = ""
        if Config.conf['verbose_level'] == logging.DEBUG:
            verbose = "v"
        cmd = ["tar", "t" + verbose + "f", self.filename]
        stderror = Uprocess().get_stderr()
        if Uprocess().call(cmd, stderr=stderror, stdout=stderror, close_fds=True):
            return False

        return True

    def tar(self, tarfile, sourcedir=None):
        """Create a tar file for a given sourcedir"""
        if sourcedir is None:
            sourcedir = self.filename

        verbose = ""
        if Config.conf['verbose_level'] == logging.DEBUG:
            verbose = "v"
        cmd = ["tar", "-C", sourcedir, "-c" + verbose, "--one-file-system",
               "-S", "--xattrs", "-f", tarfile, "."]
        stderror = Uprocess().get_stderr()
        status = Uprocess().call(cmd, stderr=stderror, close_fds=True)
        if status:
            LOG.error("creating tar file: %s", tarfile)
        return not status

    def copydir(self, destdir, sourcedir=None):
        """Copy directories"""
        if sourcedir is None:
            sourcedir = self.filename

        verbose = ''
        if Config.conf['verbose_level'] == logging.DEBUG:
            verbose = 'v'

        cmd_tarc = ["tar", "-C", sourcedir, "-c" + verbose,
                    "--one-file-system", "-S", "--xattrs", "-f", "-", "."]
        cmd_tarx = ["tar", "-C", destdir, "-x" + verbose, "-f", "-"]
        status = Uprocess().pipe(cmd_tarc, cmd_tarx)
        if not status:
            LOG.error("copying %s to %s", sourcedir, destdir)
        return status

    def cleanup(self):
        """Delete all temporary files"""
        tmptrash_copy = dict(FileUtil.tmptrash)
        for filename in tmptrash_copy:
            FileUtil(filename).remove(recursive=True)

    def isexecutable(self):
        """Check if execute bit is set"""
        try:
            return os.access(self.filename, os.X_OK)
        except (IOError, OSError, TypeError):
            return False

    def iswriteable(self):
        """Check if execute bit is set"""
        try:
            return os.access(self.filename, os.W_OK)
        except (IOError, OSError, TypeError):
            return False

    def isdir(self):
        """Is filename a directory"""
        try:
            if os.path.isdir(self.filename):
                return True
        except (OSError, TypeError):
            pass

        return False

    def isfile(self):
        """Is filename a plain file"""
        try:
            if os.path.isfile(self.filename):
                return True
        except (IOError, OSError, TypeError):
            pass

        return False

    def size(self):
        """File size in bytes"""
        try:
            fstat = os.stat(self.filename)
            return fstat.st_size
        except (OSError, TypeError):
            return -1

    def getdata(self, mode="rb", size=-1):
        """Read file content to a buffer"""
        try:
            with open(self.filename, mode) as filep:
                if size == -1:
                    buf = filep.read()
                else:
                    buf = filep.read(size)
            LOG.debug("read buf: %s", buf)
            return buf
        except (OSError, TypeError):
            return ""

    def get1stline(self, mode="rb"):
        """Read file 1st line to a buffer"""
        # TODO: (mdavid) refactor this part
        try:
            filep = open(self.filename, mode)
        except (OSError, TypeError):
            return ""
        buf = filep.readline().strip()
        filep.close()
        return buf

    def putdata(self, buf, mode="wb"):
        """Write buffer to file"""
        try:
            with open(self.filename, mode) as filep:
                filep.write(buf)

            return buf
        except (OSError, TypeError):
            return ""

    def getvalid_path(self):
        """Get the portion of a pathname that exists"""
        f_path = self.filename
        while f_path:
            if os.path.exists(f_path):
                return f_path

            (f_path, dummy) = os.path.split(f_path)

        return f_path

    def _cont2host(self, pathname, container_root, volumes=""):
        """Auxiliary translate container path to host path"""
        if not (pathname and pathname.startswith('/')):
            return ""

        if not volumes:
            volumes = []

        path = ""
        real_container_root = os.path.realpath(container_root)
        pathname = re.sub("/+", '/', os.path.normpath(pathname))
        for vol in volumes:
            (host_path, cont_path) = Uvolume(vol).split()
            if cont_path != host_path:
                if pathname.startswith(cont_path):
                    path = host_path + pathname[len(cont_path):]
                    break
            elif pathname.startswith(host_path):
                path = pathname
                break

        if not path:
            path = real_container_root + '/' + pathname

        f_path = ""
        for d_comp in path.split('/')[1:]:
            f_path = f_path + '/' + d_comp
            while os.path.islink(f_path):
                real_path = os.readlink(f_path)
                if real_path.startswith('/'):
                    if f_path.startswith(real_container_root):  # in container
                        if real_path.startswith(real_container_root):
                            f_path = real_path
                        else:
                            f_path = real_container_root + real_path
                    else:
                        f_path = real_path
                else:
                    f_path = os.path.dirname(f_path) + '/' + real_path

        return os.path.realpath(f_path)

    def cont2host(self, container_path, volumes=""):
        """Translate container relative path to host path"""
        return self._cont2host(container_path, self.orig_filename, volumes)

    def _find_exec(self, path, rootdir="", volumes="", workdir="", cont2host=False):
        """Find file in a path set such as PATH=/usr/bin:/bin"""
        for directory in path:
            if not directory:
                continue

            if directory == "." and workdir:
                directory = workdir
            elif directory == ".." and workdir:
                directory = workdir + "/.."

            if self.orig_filename.startswith("/"):
                exec_path = self.orig_filename
            else:
                exec_path = directory + "/" + self.orig_filename

            host_path = exec_path
            if rootdir:
                host_path = self._cont2host(exec_path, rootdir, volumes)

            if os.path.isfile(host_path) and os.access(host_path, os.X_OK):
                return host_path if cont2host else exec_path

        return ""

    def find_exec(self, path="", rootdir="", volumes="", workdir="", cont2host=False):
        """Find an executable pathname"""
        if not path:
            path = os.getenv("PATH") + ":" + Config.conf['root_path']

        if rootdir:
            rootdir += "/"

        if isinstance(path, str):
            if "=" in path:
                path = "".join(path.split("=", 1)[1:])

            path = path.split(":")

        if not isinstance(path, (list, tuple)):
            return ""

        return self._find_exec(path, rootdir, volumes, workdir, cont2host)

    def rename(self, dest_filename):
        """Rename/move file"""
        try:
            os.rename(self.filename, dest_filename)
        except OSError:
            return False

        return True

    def _stream2file(self, dest_filename, mode="w"):
        """Copy from stdin to another file. We avoid shutil to have
        the fewest possible dependencies on other Python modules.
        """
        # (mdavid) refactor this part
        try:
            fpdst = open(dest_filename, mode + "b")
        except OSError:
            return False

        while True:
            copy_buffer = sys.stdin.buffer.read(1024 * 1024)
            if not copy_buffer:
                break

            fpdst.write(copy_buffer)

        fpdst.close()
        return True

    def _file2stream(self):
        """Copy self.filename to stdout. We avoid shutil to have
        the fewest possible dependencies on other Python modules.
        """
        # (mdavid) refactor this part
        try:
            fpsrc = open(self.filename, "rb")
        except OSError:
            return False

        while True:
            copy_buffer = fpsrc.read(1024 * 1024)
            if not copy_buffer:
                break

            sys.stdout.write(copy_buffer)

        fpsrc.close()
        return True

    def _file2file(self, dest_filename, mode="w"):
        """Copy self.filename to another file. We avoid shutil to have
        the fewest possible dependencies on other Python modules.
        """
        # (mdavid) refactor this part
        try:
            fpsrc = open(self.filename, "rb")
        except OSError:
            return False

        try:
            fpdst = open(dest_filename, mode + "b")
        except OSError:
            fpsrc.close()
            return False

        while True:
            copy_buffer = fpsrc.read(1024 * 1024)
            if not copy_buffer:
                break

            fpdst.write(copy_buffer)

        fpsrc.close()
        fpdst.close()
        return True

    def copyto(self, dest_filename, mode="w"):
        """Copy self.filename to another file. We avoid shutil to have
        the fewest possible dependencies on other Python modules.
        """
        if self.filename == "-" and dest_filename != "-":
            return self._stream2file(dest_filename, mode)

        if self.filename != "-" and dest_filename == "-":
            return self._file2stream()

        if self.filename != "-" and dest_filename != "-":
            return self._file2file(dest_filename, mode)

        return False

    def find_file_in_dir(self, image_list):
        """Find and return first file of list in dir"""
        path_prefix = self.filename
        for image in image_list:
            image_path = path_prefix + "/" + image
            if os.path.exists(image_path):
                return image_path

        return ""

    def _link_change_apply(self, new_l_path, f_path, force):
        """Actually apply the link conversion"""
        p_path = os.path.realpath(os.path.dirname(f_path))
        if force and not os.access(p_path, os.W_OK):
            os.chmod(p_path, stat.S_IMODE(os.stat(p_path).st_mode) | stat.S_IWUSR)
            os.remove(f_path)
            os.symlink(new_l_path, f_path)
            os.chmod(p_path, stat.S_IMODE(os.stat(p_path).st_mode) & ~stat.S_IWUSR)
        else:
            os.remove(f_path)
            os.symlink(new_l_path, f_path)

    def _link_set(self, f_path, orig_path, root_path, force):
        """Conversion to container specific symbolic link"""
        l_path = os.readlink(f_path)
        if not l_path.startswith("/"):
            return False

        new_l_path = ""
        regexp_id = "[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+"
        recomp = re.compile("(/.*/containers/" + regexp_id + "/ROOT)(/.*)")
        if orig_path == "":
            match = recomp.match(l_path)
            if match:
                orig_path = match.group(1)

        if orig_path and l_path.startswith(orig_path) and orig_path != root_path:
            new_l_path = l_path.replace(orig_path, root_path, 1)
        elif not l_path.startswith(root_path):
            new_l_path = root_path + l_path

        if new_l_path:
            self._link_change_apply(new_l_path, f_path, force)
            return True

        return False

    def _link_restore(self, f_path, orig_path, root_path, force):
        """Conversion for host specific symbolic link"""
        l_path = os.readlink(f_path)
        new_l_path = ""
        if not l_path.startswith("/"):
            return False

        regexp_id = "[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+"
        recomp = re.compile("(/.*/containers/" + regexp_id + "/ROOT)(/.*)")
        if orig_path and l_path.startswith(orig_path):
            new_l_path = l_path.replace(orig_path, "", 1)
        elif l_path.startswith(root_path):
            new_l_path = l_path.replace(root_path, "", 1)
        elif orig_path == "":
            match = recomp.match(l_path)
            if match:
                new_l_path = l_path.replace(match.group(1), "", 1)

        if new_l_path:
            self._link_change_apply(new_l_path, f_path, force)
            return True

        return False

    def links_conv(self, force=False, to_container=True, orig_path=""):
        """ Convert absolute symbolic links to relative symbolic links"""
        root_path = os.path.realpath(self.filename)
        links = []
        if not self._is_safe_prefix(root_path):
            LOG.error("links conversion outside of dir tree: %s", root_path)
            return links     # DONE: return target, changed by mdavid
        for dir_path, dirs, files in os.walk(root_path):
            for f_name in files + dirs:
                try:
                    f_path = dir_path + "/" + f_name
                    if not os.path.islink(f_path):
                        continue

                    if os.lstat(f_path).st_uid != HostInfo.uid:
                        continue

                    if to_container:
                        if self._link_set(f_path, orig_path, root_path, force):
                            links.append(f_path)
                    elif self._link_restore(f_path, orig_path, root_path, force):
                        links.append(f_path)

                except OSError:
                    continue

        return links

    def match(self):
        """Find file with wildcard matching expression"""
        directory = os.path.dirname(self.filename)
        matching_expression = os.path.basename(self.filename)
        matching_files = []
        if not os.path.isdir(directory):
            return []

        for f_name in os.listdir(directory):
            if re.match(matching_expression, f_name):
                matching_files.append(directory + "/" + f_name)

        return matching_files

    def match_recursive(self, filetype='FL'):
        """Recursively find file with wildcard matching expression"""
        directory = os.path.dirname(self.filename)
        matching_expression = os.path.basename(self.filename)
        matching_files = []
        if not os.path.isdir(directory):
            return []

        for dir_path, dirs, files in os.walk(directory):
            f_list = []
            if 'F' in filetype:
                f_list += files
            if 'D' in filetype:
                f_list += dirs
            for f_name in f_list:
                f_path = dir_path + "/" + f_name
                if os.path.islink(f_path) and 'L' not in filetype:
                    continue
                if re.match(matching_expression, f_name):
                    matching_files.append(f_path)

        return matching_files
