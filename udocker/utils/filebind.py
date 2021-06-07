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

    def __init__(self, localrepo, container_id):
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
            if not FileUtil(self.container_orig_dir).mkdir():
                Msg().err("Error: creating dir:", self.container_orig_dir)
                return False
        if not os.path.isdir(self.container_bind_dir):
            if not FileUtil(self.container_bind_dir).mkdir():
                Msg().err("Error: creating dir:", self.container_bind_dir)
                return False
        return True

    def restore(self, force=False):
        """Restore container files after FileBind"""
        error = False
        if not os.path.isdir(self.container_orig_dir):
            return
        for f_name in os.listdir(self.container_orig_dir):
            orig_file = self.container_orig_dir + '/' + f_name
            if not os.path.isfile(orig_file):
                continue
            cont_file = os.path.basename(f_name).replace('#', '/')
            cont_file = self.container_root + '/' + cont_file
            if os.path.islink(cont_file):
                FileUtil(cont_file).register_prefix()
                FileUtil(cont_file).remove()
            elif os.path.exists(cont_file):
                continue
            if not FileUtil(orig_file).rename(cont_file):
                Msg().err("Error: restoring binded file:", cont_file)
                error = True
        if not error or force:
            FileUtil(self.container_orig_dir).remove(recursive=True)
        FileUtil(self.container_bind_dir).remove(recursive=True)

    def start(self, files_list=None):
        """Prepare host files to be made available inside container
        files_list: is the initial list of files to be made available
        returns: the directory that holds the files and that must be
                 binded inside the container
        """
        self.setup()
        self.host_bind_dir = FileUtil("BIND_FILES").mktmpdir()
        if files_list:
            self.set_list(files_list)
        return (self.host_bind_dir, self.bind_dir)

    def set_list(self, files_list):
        """setup links for a list of files"""
        for f_name in files_list:
            self.set_file(f_name, f_name)

    def set_file(self, host_file, cont_file):
        """Prepare individual file mapping"""
        if not os.path.isfile(host_file):
            return
        orig_file = cont_file.replace('/', '#')
        orig_file_path = self.container_orig_dir + '/' + orig_file
        cont_file_path = self.container_root + '/' + cont_file
        link_path = self.bind_dir + '/' + orig_file
        if not os.path.exists(orig_file_path):
            if os.path.isfile(cont_file_path):
                os.rename(cont_file_path, orig_file_path)
            else:
                return
            os.symlink(link_path, cont_file_path)
        FileUtil(orig_file_path).copyto(self.host_bind_dir)

    def add_file(self, host_file, cont_file):
        """Add file to be made available inside container"""
        replace_file = cont_file.replace('/', '#')
        replace_file = self.host_bind_dir + '/' + replace_file
        FileUtil(replace_file).remove()
        FileUtil(host_file).copyto(replace_file)

    def get_path(self, cont_file):
        """Get real path of file in container self.host_bind_dir"""
        replace_file = cont_file.replace('/', '#')
        return self.host_bind_dir + '/' + replace_file

    def finish(self):
        """Cleanup after run"""
        return
