# -*- coding: utf-8 -*-
"""Tools to manage the container structure"""

import os
import subprocess

from udocker import is_genstr
from udocker.config import Config
from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil
from udocker.utils.uprocess import Uprocess
from udocker.helper.unique import Unique
from udocker.helper.hostinfo import HostInfo


class ContainerStructure(object):
    """Docker container structure.
    Creation of a container filesystem from a repository image.
    Creation of a container filesystem from a layer tar file.
    Access to container metadata.
    """

    def __init__(self, localrepo, container_id=None):
        self.localrepo = localrepo
        self.container_id = container_id
        self.tag = ""
        self.imagerepo = ""

    def get_container_attr(self):
        """Get container directory and JSON metadata by id or name"""
        if Config.conf['location']:
            container_dir = ""
            container_json = []
        else:
            container_dir = self.localrepo.cd_container(self.container_id)
            if not container_dir:
                Msg().err("Error: container id or name not found")
                return(False, False)

            fjson = container_dir + "/container.json"
            container_json = self.localrepo.load_json(fjson)
            if not container_json:
                Msg().err("Error: invalid container json metadata")
                return(False, False)

        return(container_dir, container_json)

    def get_container_meta(self, param, default, container_json):
        """Get the container metadata from the container"""
        confidx = ""
        if "config" in container_json:
            confidx = "config"
        elif "container_config" in container_json:
            confidx = "container_config"
        if container_json[confidx]  and param in container_json[confidx]:
            if container_json[confidx][param] is None:
                pass
            elif (is_genstr(container_json[confidx][param]) and
                  (isinstance(default, (list, tuple)))):
                return container_json[confidx][param].strip().split()
            elif (is_genstr(default) and (
                    isinstance(container_json[confidx][param], (list, tuple)))):
                return " ".join(container_json[confidx][param])
            elif (is_genstr(default) and (
                    isinstance(container_json[confidx][param], dict))):
                return self._dict_to_str(container_json[confidx][param])
            elif (isinstance(default, list) and (
                    isinstance(container_json[confidx][param], dict))):
                return self._dict_to_list(container_json[confidx][param])
            else:
                return container_json[confidx][param]
        return default

    # DEBUG
    def _dict_to_str(self, in_dict):
        """Convert dict to str"""
        out_str = ""
        for (key, val) in in_dict.items():
            out_str += f"{str(key)}:{str(val)} "
        return out_str

    def _dict_to_list(self, in_dict):
        """Convert dict to list"""
        out_list = []
        for (key, val) in in_dict.items():
            out_list.append(f"{str(key)}:{str(val)}")
        return out_list

    def _chk_container_root(self, container_id=None):
        """Check container ROOT sanity"""
        if container_id:
            container_dir = self.localrepo.cd_container(container_id)
        else:
            container_dir = self.localrepo.cd_container(self.container_id)
        if not container_dir:
            return 0
        container_root = container_dir + "/ROOT"
        check_list = ["/lib", "/bin", "/etc", "/tmp", "/var", "/usr", "/sys",
                      "/dev", "/data", "/home", "/system", "/root", "/proc", ]
        found = 0
        for f_path in check_list:
            if os.path.exists(container_root + f_path):
                found += 1
        return found

    def create_fromimage(self, imagerepo, tag):
        """Create a container from an image in the repository.
        Since images are stored as layers in tar files, this
        step consists in extracting those layers into a ROOT
        directory in the appropriate sequence.
        first argument: imagerepo
        second argument: image tag in that repo
        """
        self.imagerepo = imagerepo
        self.tag = tag
        image_dir = self.localrepo.cd_imagerepo(self.imagerepo, self.tag)
        if not image_dir:
            Msg().err("Error: create container: imagerepo is invalid")
            return False

        (container_json, layer_files) = self.localrepo.get_image_attributes()
        if not container_json:
            Msg().err("Error: create container: getting layers or json")
            return False

        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))

        container_dir = self.localrepo.setup_container(
            self.imagerepo, self.tag, self.container_id)
        if not container_dir:
            Msg().err("Error: create container: setting up container")
            return False

        self.localrepo.save_json(
            container_dir + "/container.json", container_json)
        status = self._untar_layers(layer_files, container_dir + "/ROOT")
        if not status:
            Msg().err("Error: creating container:", self.container_id)
        elif not self._chk_container_root():
            Msg().out("Warning: check container content:", self.container_id,
                      l=Msg.WAR)

        return self.container_id

    def create_fromlayer(self, imagerepo, tag, layer_file, container_json):
        """Create a container from a layer file exported by Docker.
        """
        self.imagerepo = imagerepo
        self.tag = tag
        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))

        if not container_json:
            Msg().err("Error: create container: getting json")
            return False

        container_dir = self.localrepo.setup_container(
            self.imagerepo, self.tag, self.container_id)
        if not container_dir:
            Msg().err("Error: create container: setting up")
            return False

        fjson = container_dir + "/container.json"
        self.localrepo.save_json(fjson, container_json)
        status = self._untar_layers([layer_file, ], container_dir + "/ROOT")
        if not status:
            Msg().err("Error: creating container:", self.container_id)
        elif not self._chk_container_root():
            Msg().out("Warning: check container content:", self.container_id,
                      l=Msg.WAR)

        return self.container_id

    def clone_fromfile(self, clone_file):
        """Create a cloned container from a file containing a cloned container
        exported by udocker.
        """
        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))

        container_dir = self.localrepo.setup_container(
            "CLONING", "inprogress", self.container_id)
        if not container_dir:
            Msg().err("Error: create container: setting up")
            return False

        status = self._untar_layers([clone_file, ], container_dir)
        if not status:
            Msg().err("Error: creating container clone:", self.container_id)
        elif not self._chk_container_root():
            Msg().out("Warning: check container content:", self.container_id,
                      l=Msg.WAR)

        return self.container_id

    def _apply_whiteouts(self, tarf, destdir):
        """The layered filesystem of docker uses whiteout files
        to identify files or directories to be removed.
        The format is .wh.<filename>
        """
        verbose = ""
        if Msg.level >= Msg.VER:
            verbose = 'v'
            Msg().out("Info: applying whiteouts:", tarf, l=Msg.INF)
        wildcards = ["--wildcards", ]
        if not HostInfo().cmd_has_option("tar", wildcards[0]):
            wildcards = []
        cmd = ["tar", "t" + verbose] + wildcards + ["-f", tarf, r"*/.wh.*"]
        whiteouts = Uprocess().get_output(cmd, True)
        if not whiteouts:
            return
        for wh_filename in whiteouts.split('\n'):
            if wh_filename:
                wh_basename = os.path.basename(wh_filename.strip())
                wh_dirname = os.path.dirname(wh_filename)
                if wh_basename == ".wh..wh..opq":
                    if not os.path.isdir(destdir + '/' + wh_dirname):
                        continue
                    for f_name in os.listdir(destdir + '/' + wh_dirname):
                        rm_filename = destdir + '/' \
                            + wh_dirname + '/' + f_name
                        FileUtil(rm_filename).remove(recursive=True)
                elif wh_basename.startswith(".wh."):
                    rm_filename = destdir + '/' \
                        + wh_dirname + '/' \
                        + wh_basename.replace(".wh.", "", 1)
                    FileUtil(rm_filename).remove(recursive=True)
        return

    def _untar_layers(self, tarfiles, destdir):
        """Untar all container layers. Each layer is extracted
        and permissions are changed to avoid file permission
        issues when extracting the next layer.
        """
        if not (tarfiles and destdir):
            return False
        status = True
        gid = str(HostInfo.gid)
        optional_flags = ["--wildcards", "--delay-directory-restore", ]
        for option in optional_flags:
            if not HostInfo().cmd_has_option("tar", option):
                optional_flags.remove(option)
        for tarf in tarfiles:
            if tarf != '-':
                self._apply_whiteouts(tarf, destdir)
            verbose = ''
            if Msg.level >= Msg.VER:
                verbose = 'v'
                Msg().out("Info: extracting:", tarf, l=Msg.INF)
            cmd = ["tar", "-C", destdir, "-x" + verbose,
                   "--one-file-system", "--no-same-owner", "--overwrite",
                   "--exclude=dev/*", "--exclude=etc/udev/devices/*",
                   "--no-same-permissions", r"--exclude=.wh.*",
                   ] + optional_flags + ["-f", tarf]
            if subprocess.call(cmd, stderr=Msg.chlderr, close_fds=True):
                Msg().err("Error: while extracting image layer")
                status = False
            cmd = ["find", destdir,
                   "(", "-type", "d", "!", "-perm", "-u=x", "-exec",
                   "chmod", "u+x", "{}", ";", ")", ",",
                   "(", "!", "-perm", "-u=w", "-exec", "chmod",
                   "u+w", "{}", ";", ")", ",",
                   "(", "!", "-perm", "-u=r", "-exec", "chmod",
                   "u+r", "{}", ";", ")", ",",
                   "(", "!", "-gid", gid, "-exec", "chgrp", gid,
                   "{}", ";", ")", ",",
                   "(", "-name", ".wh.*", "-exec", "rm", "-f",
                   "--preserve-root", "{}", ";", ")"]
            if subprocess.call(cmd, stderr=Msg.chlderr, close_fds=True):
                status = False
                Msg().err("Error: while modifying attributes of image layer")
        return status

    def export_tofile(self, clone_file):
        """Export a container creating a tar file of the rootfs
        """
        cont_dir = self.localrepo.cd_container(self.container_id)
        if not cont_dir:
            Msg().err("Error: container not found:", self.container_id)
            return False

        status = FileUtil(cont_dir + "/ROOT").tar(clone_file)
        if not status:
            Msg().err("Error: exporting container file system:",
                      self.container_id)

        return self.container_id

    def clone_tofile(self, clone_file):
        """Create a cloned container tar file containing both the rootfs
        and all udocker control files. This is udocker specific.
        """
        container_dir = self.localrepo.cd_container(self.container_id)
        if not container_dir:
            Msg().err("Error: container not found:", self.container_id)
            return False

        status = FileUtil(container_dir).tar(clone_file)
        if not status:
            Msg().err("Error: export container as clone:", self.container_id)

        return self.container_id

    def clone(self):
        """Clone a container by creating a complete copy
        """
        source_container_dir = self.localrepo.cd_container(self.container_id)
        if not source_container_dir:
            Msg().err("Error: source container not found:", self.container_id)
            return False

        dest_container_id = Unique().uuid(os.path.basename(self.imagerepo))
        dest_container_dir = self.localrepo.setup_container(
            "CLONING", "inprogress", dest_container_id)
        if not dest_container_dir:
            Msg().err("Error: create destination container: setting up")
            return False

        status = FileUtil(source_container_dir).copydir(dest_container_dir)
        if not status:
            Msg().err("Error: creating container:", dest_container_id)
            return False

        if not self._chk_container_root(dest_container_id):
            Msg().out("Warning: check container content:", dest_container_id,
                      l=Msg.WAR)

        return dest_container_id
