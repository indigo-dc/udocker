# -*- coding: utf-8 -*-
"""LocalFile API integration for Docker and OCI file manipulation"""

import os

from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil

from udocker.docker import DockerLocalFileAPI
from udocker.oci import OciLocalFileAPI
from udocker.commonlocalfile import CommonLocalFileApi


class LocalFileAPI(CommonLocalFileApi):
    """Generic manipulation of containers and/or image files"""

    def __init__(self, localrepo):
        CommonLocalFileApi.__init__(self, localrepo)

    def load(self, imagefile, imagerepo=None):
        """Generic load of image tags to a file"""
        if not os.path.exists(imagefile) and imagefile != '-':
            Msg().err("Error: image file does not exist:", imagefile)
            return False
        tmp_imagedir = FileUtil("load").mktmp()
        try:
            os.makedirs(tmp_imagedir)
        except (IOError, OSError):
            return False
        if not self._untar_saved_container(imagefile, tmp_imagedir):
            Msg().err("Error: failed to extract container:", imagefile)
            FileUtil(tmp_imagedir).remove(recursive=True)
            return False
        imagetype = self._get_imagedir_type(tmp_imagedir)
        if imagetype == "Docker":
            repositories = DockerLocalFileAPI(
                self.localrepo).load(tmp_imagedir, imagerepo)
        elif imagetype == "OCI":
            repositories = OciLocalFileAPI(
                self.localrepo).load(tmp_imagedir, imagerepo)
        else:
            repositories = []
        FileUtil(tmp_imagedir).remove(recursive=True)
        return repositories

    def save(self, imagetag_list, imagefile):
        """Generic save of image tags to a file"""
        return DockerLocalFileAPI(self.localrepo).save(
            imagetag_list, imagefile)
