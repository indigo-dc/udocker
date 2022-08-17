# -*- coding: utf-8 -*-
"""Common Class for LocalFile API"""

import os
import time

from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil
from udocker.utils.uprocess import Uprocess
from udocker.helper.unique import Unique
from udocker.helper.hostinfo import HostInfo
from udocker.container.structure import ContainerStructure
from udocker.engine.execmode import ExecutionMode


class CommonLocalFileApi(object):
    """Common methods for Docker and OCI files"""

    def __init__(self, localrepo):
        self.localrepo = localrepo
        self._imagerepo = None

    def _move_layer_to_v1repo(self, filepath, layer_id, linkname=None):
        """Copy or rename an image layer file to a v1 repository"""
        if filepath.endswith("json"):
            target_file = self.localrepo.layersdir + '/' + layer_id + ".json"
        elif filepath.endswith("layer.tar"):
            target_file = self.localrepo.layersdir + '/' + layer_id + ".layer"
        elif ':' in layer_id:
            (dummy, layer_id) = layer_id.split(':', 1)
            target_file = self.localrepo.layersdir + '/' + layer_id + ".layer"
        else:
            return False
        try:
            os.rename(filepath, target_file)
        except(IOError, OSError):
            if not FileUtil(filepath).copyto(target_file):
                return False
        self.localrepo.add_image_layer(target_file, linkname)
        return True

    def _load_image_step2(self, structure, imagerepo, tag):
        """Implementation specific image load"""

    def _load_image(self, structure, imagerepo, tag):
        """Load a container image into a repository mimic docker load"""
        if self._imagerepo and self._imagerepo != imagerepo:
            cd_imagerepo = self._imagerepo
        else:
            cd_imagerepo = imagerepo

        if self.localrepo.cd_imagerepo(cd_imagerepo, tag):
            Msg().err("Error: repository and tag already exist",
                      cd_imagerepo, tag)
            return []

        self.localrepo.setup_imagerepo(cd_imagerepo)
        tag_dir = self.localrepo.setup_tag(tag)
        if not tag_dir:
            Msg().err("Error: setting up repository", cd_imagerepo, tag)
            return []

        if not self.localrepo.set_version("v1"):
            Msg().err("Error: setting repository version")
            return []

        return self._load_image_step2(structure, imagerepo, tag)

    def _untar_saved_container(self, tarfile, destdir):
        """Untar container created with docker save"""
        #umask 022
        verbose = ''
        if Msg.level >= Msg.VER:
            verbose = 'v'

        cmd = ["tar", "-C", destdir, "-x" + verbose,
               "--delay-directory-restore", "--one-file-system",
               "--no-same-owner", "--no-same-permissions", "--overwrite",
               "-f", tarfile]

        status = Uprocess().call(cmd, stderr=Msg.chlderr, close_fds=True)
        return not status

    def create_container_meta(self, layer_id, comment="created by udocker"):
        """Create metadata for a given container layer, used in import.
        A file for import is a tarball of a directory tree, does not contain
        metadata. This method creates minimal metadata.
        """
        container_json = {}
        container_json["id"] = layer_id
        container_json["comment"] = comment
        container_json["created"] = \
            time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")
        container_json["architecture"] = HostInfo().arch()
        container_json["os"] = HostInfo().osversion()
        layer_file = self.localrepo.layersdir + '/' + layer_id + ".layer"
        container_json["size"] = FileUtil(layer_file).size()
        if container_json["size"] == -1:
            container_json["size"] = 0
        container_json["container_config"] = {
            "Hostname": "",
            "Domainname": "",
            "User": "",
            "Memory": 0,
            "MemorySwap": 0,
            "CpusShares": 0,
            "Cpuset": "",
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "PortSpecs": None,
            "ExposedPorts": None,
            "Tty": False,
            "OpenStdin": False,
            "StdinOnce": False,
            "Env": None,
            "Cmd": None,
            "Image": "",
            "Volumes": None,
            "WorkingDir": "",
            "Entrypoint": None,
            "NetworkDisable": False,
            "MacAddress": "",
            "OnBuild": None,
            "Labels": None
        }
        container_json["config"] = {
            "Hostname": "",
            "Domainname": "",
            "User": "",
            "Memory": 0,
            "MemorySwap": 0,
            "CpusShares": 0,
            "Cpuset": "",
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "PortSpecs": None,
            "ExposedPorts": None,
            "Tty": False,
            "OpenStdin": False,
            "StdinOnce": False,
            "Env": None,
            "Cmd": None,
            "Image": "",
            "Volumes": None,
            "WorkingDir": "",
            "Entrypoint": None,
            "NetworkDisable": False,
            "MacAddress": "",
            "OnBuild": None,
            "Labels": None
        }
        return container_json

    def import_toimage(self, tarfile, imagerepo, tag, move_tarball=True):
        """Import a tar file containing a simple directory tree possibly
        created with Docker export and create local image"""
        if not os.path.exists(tarfile) and tarfile != '-':
            Msg().err("Error: tar file does not exist: ", tarfile)
            return False
        self.localrepo.setup_imagerepo(imagerepo)
        tag_dir = self.localrepo.cd_imagerepo(imagerepo, tag)
        if tag_dir:
            Msg().err("Error: tag already exists in repo:", tag)
            return False
        tag_dir = self.localrepo.setup_tag(tag)
        if not tag_dir:
            Msg().err("Error: creating repo and tag")
            return False
        if not self.localrepo.set_version("v1"):
            Msg().err("Error: setting repository version")
            return False
        layer_id = Unique().layer_v1()
        layer_file = self.localrepo.layersdir + '/' + layer_id + ".layer"
        json_file = self.localrepo.layersdir + '/' + layer_id + ".json"
        if move_tarball:
            try:
                os.rename(tarfile, layer_file)
            except(IOError, OSError):
                pass
        if not os.path.exists(layer_file):
            if not FileUtil(tarfile).copyto(layer_file):
                Msg().err("Error: in move/copy file", tarfile)
                return False
        self.localrepo.add_image_layer(layer_file)
        self.localrepo.save_json("ancestry", [layer_id])
        container_json = self.create_container_meta(layer_id)
        self.localrepo.save_json(json_file, container_json)
        self.localrepo.add_image_layer(json_file)
        Msg().out("Info: added layer", layer_id, l=Msg.INF)
        return layer_id

    def import_tocontainer(self, tarfile, imagerepo, tag, container_name):
        """Import a tar file containing a simple directory tree possibly
        created with Docker export and create local container ready to use"""
        if not imagerepo:
            imagerepo = "IMPORTED"
            tag = "latest"
        if not os.path.exists(tarfile) and tarfile != '-':
            Msg().err("Error: tar file does not exist:", tarfile)
            return False
        if container_name:
            if self.localrepo.get_container_id(container_name):
                Msg().err("Error: container name already exists:",
                          container_name)
                return False
        layer_id = Unique().layer_v1()
        container_json = self.create_container_meta(layer_id)
        container_id = ContainerStructure(self.localrepo).create_fromlayer(
            imagerepo, tag, tarfile, container_json)
        if container_name:
            self.localrepo.set_container_name(container_id, container_name)
        return container_id

    def import_clone(self, tarfile, container_name):
        """Import a tar file containing a clone of a udocker container
        created with export --clone and create local cloned container
        ready to use
        """
        if not os.path.exists(tarfile) and tarfile != '-':
            Msg().err("Error: tar file does not exist:", tarfile)
            return False
        if container_name:
            if self.localrepo.get_container_id(container_name):
                Msg().err("Error: container name already exists:",
                          container_name)
                return False
        container_id = ContainerStructure(self.localrepo).clone_fromfile(
            tarfile)
        if container_name:
            self.localrepo.set_container_name(container_id, container_name)
        return container_id

    def clone_container(self, container_id, container_name):
        """Clone/duplicate an existing container creating a complete
        copy including metadata, control files, and rootfs, The copy
        will have a new id.
        """
        if container_name:
            if self.localrepo.get_container_id(container_name):
                Msg().err("Error: container name already exists:",
                          container_name)
                return False
        dest_container_id = ContainerStructure(self.localrepo,
                                               container_id).clone()
        if container_name:
            self.localrepo.set_container_name(dest_container_id,
                                              container_name)
        exec_mode = ExecutionMode(self.localrepo, dest_container_id)
        xmode = exec_mode.get_mode()
        if xmode.startswith('F'):
            exec_mode.set_mode(xmode, True)
        return dest_container_id

    def _get_imagedir_type(self, tmp_imagedir):
        """Identify type of image from extracted image directory"""
        image_types_list = [(tmp_imagedir + "/oci-layout", "OCI"),
                            (tmp_imagedir + "/manifest.json", "Docker"), ]
        for (checkfile, imagetype) in image_types_list:
            if os.path.exists(checkfile):
                return imagetype
        return ""
