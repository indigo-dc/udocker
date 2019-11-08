# -*- coding: utf-8 -*-
"""File bind inside containers"""

import os

from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil


class FileBind(object):
    """Alternative method to allow host files to be visible inside
    a container when binding of files is not possible such as when
    using rootless namespaces.
    """

    bind_dir = "/.bind_host_files"
    orig_dir = "/.bind_orig_files"

    def __init__(self, conf, localrepo, container_id):
        self.conf = conf
        self.localrepo = localrepo               # LocalRepository object
        self.container_id = container_id         # Container id
        self.container_dir = \
            os.path.realpath(self.localrepo.cd_container(container_id))
        self.container_root = self.container_dir + "/ROOT"
        self.container_bind_dir = self.container_root + self.bind_dir
        self.container_orig_dir = self.container_dir + self.orig_dir
        self.host_bind_dir = None

    def setup(self):
        """Prepare container for FileBind"""
        if not os.path.isdir(self.container_orig_dir):
            if not FileUtil(self.conf, self.container_orig_dir).mkdir():
                Msg().err("Error: creating dir:", self.container_orig_dir)
                return False
        if not os.path.isdir(self.container_bind_dir):
            if not FileUtil(self.conf, self.container_bind_dir).mkdir():
                Msg().err("Error: creating dir:", self.container_bind_dir)
                return False
        return True

    def restore(self):
        """Restore container files after FileBind"""
        error = False
        if not os.path.isdir(self.container_orig_dir):
            return
        for f_name in os.listdir(self.container_orig_dir):
            orig_file = self.container_orig_dir + "/" + f_name
            if not os.path.isfile(orig_file):
                continue
            cont_file = os.path.basename(f_name).replace('#', '/')
            cont_file = self.container_root + "/" + cont_file

            if os.path.islink(cont_file):
                FileUtil(self.conf, cont_file).remove()
            elif os.path.exists(cont_file):
                continue

            try:
                os.rename(orig_file, cont_file)
                bool_rename = True
            except (IOError, OSError):
                bool_rename = False
            if not bool_rename:
                Msg().err("Error: restoring binded file:", cont_file)
                error = True

        if not error:
            FileUtil(self.conf, self.container_orig_dir).remove()

        FileUtil(self.conf, self.container_bind_dir).remove()

    def start(self, files_list):
        """Prepare host files to be made available inside container
        files_list: is the initial list of files to be made available
        returns: the directory that holds the files and that must be
                 binded inside the container
        """
        self.host_bind_dir = FileUtil(self.conf, "BIND_FILES").mktmpdir()
        for f_name in files_list:
            if not os.path.isfile(f_name):
                continue
            orig_file = f_name.replace('/', '#')
            orig_file_path = self.container_orig_dir + "/" + orig_file
            cont_file = self.container_root + "/" + f_name
            link_path = self.bind_dir + "/" + orig_file
            if not os.path.exists(orig_file_path):
                if os.path.exists(cont_file):
                    os.rename(cont_file, orig_file_path)
                else:
                    FileUtil(self.conf, orig_file_path).putdata("", "w")
                os.symlink(link_path, cont_file)
            FileUtil(self.conf, orig_file_path).copyto(self.host_bind_dir)
        return (self.host_bind_dir, self.bind_dir)

    def finish(self):
        """Cleanup after run"""
        pass
        #return FileUtil(self.conf, self.host_bind_dir).remove()

    def add(self, host_file, cont_file):
        """Add file to be made available inside container"""
        replace_file = cont_file.replace('/', '#')
        replace_file = self.host_bind_dir + "/" + replace_file
        FileUtil(self.conf, replace_file).remove()
        FileUtil(self.conf, host_file).copyto(replace_file)
