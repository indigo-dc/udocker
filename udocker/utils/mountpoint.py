# -*- coding: utf-8 -*-
"""Create, store and reset container mountpoints"""

import os
import stat

from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil


class MountPoint(object):
    """Create, store and reset container mountpoints"""

    orig_dir = "/.mountpoints"

    def __init__(self, localrepo, container_id):
        self.localrepo = localrepo               # LocalRepository object
        self.container_id = container_id         # Container id
        self.mountpoints = {}
        self.container_dir = \
            os.path.realpath(self.localrepo.cd_container(container_id))
        self.container_root = self.container_dir + "/ROOT"
        self.mountpoints_orig_dir = self.container_dir + self.orig_dir
        self.setup()

    def setup(self):
        """Prepare container for mountpoints"""
        if not os.path.isdir(self.mountpoints_orig_dir):
            if not FileUtil(self.mountpoints_orig_dir).mkdir():
                Msg().err("Error: creating dir:", self.mountpoints_orig_dir)
                return False
        return True

    def add(self, cont_path):
        """Add a container relative pathname as destination mountpoint"""
        mountpoint = self.container_root + '/' + cont_path
        orig_mpath = FileUtil(mountpoint).getvalid_path()
        if orig_mpath:
            self.mountpoints[cont_path] = \
                orig_mpath.replace(self.container_root, "", 1)
        if not self.mountpoints[cont_path]:
            self.mountpoints[cont_path] = "/"

    def delete(self, cont_path):
        """Delete container mountpoint"""
        if cont_path not in self.mountpoints or not self.container_root:
            return False
        container_root = os.path.realpath(self.container_root)
        mountpoint = container_root + '/' + cont_path
        orig_mpath = container_root + '/' + self.mountpoints[cont_path]
        mountpoint = os.path.normpath(mountpoint)
        orig_mpath = os.path.normpath(orig_mpath)
        while mountpoint != orig_mpath:
            if mountpoint.startswith(container_root):
                if not FileUtil(mountpoint).remove():
                    Msg().err("Error: while deleting:", cont_path)
                    return False
                link_path = self.mountpoints[cont_path].replace('/', '#')
                FileUtil(self.mountpoints_orig_dir + '/' + link_path).remove()
                mountpoint = os.path.dirname(mountpoint)
        del self.mountpoints[cont_path]
        return True

    def delete_all(self):
        """Delete all mountpoints"""
        for cont_path in dict(self.mountpoints):
            self.delete(cont_path)

    def create(self, host_path, cont_path):
        """Create mountpoint"""
        status = True
        mountpoint = self.container_root + '/' + cont_path
        if os.path.exists(mountpoint):
            if (stat.S_IFMT(os.stat(mountpoint).st_mode) ==
                    stat.S_IFMT(os.stat(host_path).st_mode)):
                return True
            Msg().err("Error: host and container volume paths not same type:",
                      host_path, cont_path)
            return False
        self.add(cont_path)
        if os.path.isfile(host_path):
            FileUtil(os.path.dirname(mountpoint)).mkdir()
            FileUtil(mountpoint).putdata("", "w")
            status = os.path.isfile(mountpoint) or os.path.islink(mountpoint)
        elif os.path.isdir(host_path):
            status = FileUtil(mountpoint).mkdir()
        if not status:
            Msg().err("Error: creating container mountpoint:", cont_path)
            self.delete(cont_path)
            return False
        return True

    def save(self, cont_path):
        """Save one mountpoint"""
        if cont_path not in self.mountpoints:
            return True
        orig_mountpoint = self.mountpoints[cont_path].replace('/', '#')
        curr_mountpoint = cont_path.replace('/', '#')
        curr_mountpoint = self.mountpoints_orig_dir + '/' + curr_mountpoint
        try:
            if not os.path.exists(curr_mountpoint):
                os.symlink(orig_mountpoint, curr_mountpoint)
        except (IOError, OSError):
            return False
        return True

    def save_all(self):
        """Save all mountpoints"""
        for cont_path in self.mountpoints:
            self.save(cont_path)

    def load_all(self):
        """Load all mountpoints"""
        for f_name in os.listdir(self.mountpoints_orig_dir):
            orig_mpath = os.readlink(self.mountpoints_orig_dir + '/' + f_name)
            orig_mpath = orig_mpath.replace('#', '/')
            cont_path = f_name.replace('#', '/')
            self.mountpoints[cont_path] = orig_mpath

    def restore(self):
        """Restore container reverting mountpoints"""
        self.save_all()
        self.load_all()
        self.delete_all()
        FileUtil(self.mountpoints_orig_dir).remove(recursive=True)
