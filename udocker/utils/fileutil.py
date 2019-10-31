# -*- coding: utf-8 -*-
"""File utilities"""

import os
import sys
import stat
import re
import subprocess

from udocker.msg import Msg
from udocker.helper.unique import Unique
from udocker.utils.uprocess import Uprocess


class FileUtil(object):
    """Some utilities to manipulate files"""

    tmptrash = dict()
    safe_prefixes = []
    orig_umask = None

    def __init__(self, conf, filename=None):
        self.conf = conf
        self._tmpdir = self.conf['tmpdir']
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
        if prefix not in FileUtil.safe_prefixes:
            filename = prefix
            if os.path.isdir(filename) and not filename.endswith("/"):
                FileUtil.safe_prefixes.append(filename + "/")
                FileUtil.safe_prefixes.append(os.path.realpath(filename) + "/")
            else:
                FileUtil.safe_prefixes.append(filename)
                FileUtil.safe_prefixes.append(os.path.realpath(filename))

    def register_prefix(self):
        """Register self.filename as prefix where remove() is allowed"""
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
            tmp_file = self._tmpdir + "/" + Unique().filename(self.basename)
            if not os.path.exists(tmp_file):
                FileUtil.tmptrash[tmp_file] = True
                self.filename = tmp_file
                return tmp_file

    def mkdir(self):
        """Create directory"""
        try:
            os.makedirs(self.filename)
        except (OSError, IOError, AttributeError):
            return False
        return True

    def mktmpdir(self):
        """Create temporary directory"""
        dirname = self.mktmp()
        if FileUtil(self.conf, dirname).mkdir():
            return dirname
        return None

    def uid(self):
        """Get the file owner user id"""
        try:
            return os.stat(self.filename).st_uid
        except (IOError, OSError):
            return -1

    def _is_safe_prefix(self, filename):
        """Check if file prefix falls under valid prefixes"""
        for safe_prefix in FileUtil.safe_prefixes:
            if filename.startswith(safe_prefix):
                return True
        return False

    def remove(self, force=False):
        """Delete files or directories"""
        if not os.path.exists(self.filename):
            pass
        elif self.filename.count("/") < 2:
            Msg().err("Error: delete pathname too short: ", self.filename)
            return False
        elif self.uid() != self.conf['uid']:
            Msg().err("Error: delete not owner: ", self.filename)
            return False
        elif (not force) and (not self._is_safe_prefix(self.filename)):
            Msg().err("Error: delete outside of directory tree: ",
                      self.filename)
            return False
        elif os.path.isfile(self.filename) or os.path.islink(self.filename):
            try:
                os.remove(self.filename)
            except (IOError, OSError):
                Msg().err("Error: deleting file: ", self.filename)
                return False
        elif os.path.isdir(self.filename):
            cmd = "/bin/rm -Rf %s || /bin/chmod -R u+w %s && /bin/rm -Rf %s" % \
                  (self.filename, self.filename, self.filename)
            if subprocess.call(cmd, stderr=Msg.chlderr, shell=True,
                               close_fds=True, env=None):
                Msg().err("Error: deleting directory: ", self.filename)
                return False
        if self.filename in dict(FileUtil.tmptrash):
            del FileUtil.tmptrash[self.filename]
        return True

    # TODO: tarfile is part of the standard lib
    def verify_tar(self):
        """Verify a tar file: tar tvf file.tar"""
        if not os.path.isfile(self.filename):
            return False
        else:
            cmd = "tar t"
            if Msg.level >= Msg.VER:
                cmd += "v"
            cmd += "f " + self.filename
            if subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                               stdout=Msg.chldnul, close_fds=True):
                return False
            return True

    def cleanup(self):
        """Delete all temporary files"""
        tmptrash_copy = dict(FileUtil.tmptrash)
        for filename in tmptrash_copy:
            FileUtil(self.conf, filename).remove()

    def isdir(self):
        """Is filename a directory"""
        try:
            if os.path.isdir(self.filename):
                return True
        except (IOError, OSError, TypeError):
            pass
        return False

    def size(self):
        """File size in bytes"""
        try:
            fstat = os.stat(self.filename)
            return fstat.st_size
        except (IOError, OSError, TypeError):
            return -1

    def getdata(self, mode="rb"):
        """Read file content to a buffer"""
        try:
            with open(self.filename, mode) as filep:
                buf = filep.read()
            Msg().err("Read buf:", buf, l=Msg.DBG)
            return buf
        except (IOError, OSError, TypeError):
            return ""

    def get1stline(self, mode="rb"):
        """Read file 1st line to a buffer"""
        try:
            filep = open(self.filename, mode)
        except (IOError, OSError, TypeError):
            return ""
        else:
            buf = filep.readline().strip()
            filep.close()
            return buf

    def putdata(self, buf, mode="wb"):
        """Write buffer to file"""
        try:
            with open(self.filename, mode) as filep:
                filep.write(buf)
            return buf
        except (IOError, OSError, TypeError):
            return ""

    def _find_exec(self, cmd_to_use):
        """This method is called by find_exec() invokes a command like
        /bin/which or type to obtain the full pathname of an executable
        """
        exec_pathname = Uprocess().get_output(cmd_to_use)
        Msg().err("Search exec_pathname:", exec_pathname, l=Msg.DBG)
        if exec_pathname is None:
            Msg().err("exec_pathname is None")
            return ""
        if "not found" in exec_pathname:
            Msg().err("exec_pathname not found")
            return ""
        if exec_pathname and exec_pathname.startswith("/"):
            return exec_pathname.strip()
        return ""

    def find_exec(self):
        """Find an executable pathname by using which or type -p"""
        cmd = self._find_exec("which " + self.basename)
        if cmd:
            return cmd
        cmd = self._find_exec("type -p " + self.basename)
        if cmd:
            return cmd
        return ""

    def find_inpath(self, path, rootdir=""):
        """Find file in a path set such as PATH=/usr/bin:/bin"""
        if isinstance(path, str):
            if "=" in path:
                path = "".join(path.split("=", 1)[1:])
            path = path.split(":")
        if isinstance(path, (list, tuple)):
            for directory in path:
                full_path = rootdir + directory + "/" + self.basename
                if os.path.lexists(full_path):
                    return directory + "/" + self.basename
            return ""
        return ""

    def list_inpath(self, path, rootdir=""):
        """List files with path PATH=/usr/bin:/bin prepended"""
        full_path_list = []
        if isinstance(path, str):
            if "=" in path:
                path = "".join(path.split("=", 1)[1:])
            path = path.split(":")
        if isinstance(path, (list, tuple)):
            for directory in path:
                full_path_list.append(rootdir + directory + "/" + self.basename)
        return full_path_list

    def rename(self, dest_filename):
        """Rename/move file"""
        try:
            os.rename(self.filename, dest_filename)
        except (IOError, OSError):
            return False
        return True

    def _stream2file(self, dest_filename, mode="w"):
        """Copy from stdin to another file. We avoid shutil to have
        the fewest possible dependencies on other Python modules.
        """
        try:
            fpdst = open(dest_filename, mode + "b")
        except (IOError, OSError):
            return False
        while True:
            copy_buffer = sys.stdin.read(1024 * 1024)
            if not copy_buffer:
                break
            fpdst.write(copy_buffer)
        fpdst.close()
        return True

    def _file2stream(self):
        """Copy self.filename to stdout. We avoid shutil to have
        the fewest possible dependencies on other Python modules.
        """
        try:
            fpsrc = open(self.filename, "rb")
        except (IOError, OSError):
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
        try:
            fpsrc = open(self.filename, "rb")
        except (IOError, OSError):
            return False
        try:
            fpdst = open(dest_filename, mode + "b")
        except (IOError, OSError):
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
        elif self.filename != "-" and dest_filename == "-":
            return self._file2stream()
        elif self.filename != "-" and dest_filename != "-":
            return self._file2file(dest_filename, mode)
        else:
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
        """Actually apply the link convertion"""
        p_path = os.path.realpath(os.path.dirname(f_path))
        if force and not os.access(p_path, os.W_OK):
            os.chmod(p_path,
                     stat.S_IMODE(os.stat(p_path).st_mode) | stat.S_IWUSR)
            os.remove(f_path)
            os.symlink(new_l_path, f_path)
            os.chmod(p_path,
                     stat.S_IMODE(os.stat(p_path).st_mode) & ~stat.S_IWUSR)
        else:
            os.remove(f_path)
            os.symlink(new_l_path, f_path)

    def _link_set(self, f_path, orig_path, root_path, force):
        """Convertion to container specific symbolic link"""
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
        if   (orig_path and
              l_path.startswith(orig_path) and
              orig_path != root_path):
            new_l_path = l_path.replace(orig_path, root_path, 1)
        elif not l_path.startswith(root_path):
            new_l_path = root_path + l_path
        if new_l_path:
            self._link_change_apply(new_l_path, f_path, force)
            return True
        return False

    def _link_restore(self, f_path, orig_path, root_path, force):
        """Convertion for host specific symbolic link"""
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
        """ Convert absolute symbolic links to relative symbolic links
        """
        root_path = os.path.realpath(self.filename)
        links = []
        if not self._is_safe_prefix(root_path):
            Msg().err("Error: links convertion outside of directory tree: ",
                      root_path)
            return None
        for dir_path, dirs, files in os.walk(root_path):
            for f_name in files + dirs:
                try:
                    f_path = dir_path + "/" + f_name
                    if not os.path.islink(f_path):
                        continue
                    if os.lstat(f_path).st_uid != self.conf['uid']:
                        continue
                    if to_container:
                        if self._link_set(f_path, orig_path, root_path, force):
                            links.append(f_path)
                    else:
                        if self._link_restore(f_path, orig_path,
                                              root_path, force):
                            links.append(f_path)
                except OSError:
                    continue
        return links

    def match(self):
        """Find matching file with wildcard matching expression"""
        directory = os.path.dirname(self.filename)
        matching_expression = os.path.basename(self.filename)
        matching_files = []
        if not os.path.isdir(directory):
            return []
        for f_name in os.listdir(directory):
            if re.match(matching_expression, f_name):
                matching_files.append(directory + "/" + f_name)
        return matching_files
