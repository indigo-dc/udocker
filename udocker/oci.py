# -*- coding: utf-8 -*-
"""Docker API integration"""

import os

from udocker.msg import Msg
from udocker.commonlocalfile import CommonLocalFileApi
from udocker.utils.fileutil import FileUtil
from udocker.helper.unique import Unique


class OciLocalFileAPI(CommonLocalFileApi):
    """Manipulate OCI container and/or image files"""

    def __init__(self, localrepo):
        CommonLocalFileApi.__init__(self, localrepo)

    def _load_structure(self, tmp_imagedir):
        """Load OCI image structure"""
        structure = {}
        structure["repolayers"] = {}
        structure["manifest"] = {}
        f_path = tmp_imagedir + '/'
        structure["oci-layout"] = \
                self.localrepo.load_json(f_path + "oci-layout")
        structure["index"] = \
                self.localrepo.load_json(f_path + "index.json")
        if not (structure["index"] and structure["oci-layout"]):
            return {}
        for fname in os.listdir(tmp_imagedir + "/blobs"):
            f_path = tmp_imagedir + "/blobs/" + fname
            if FileUtil(f_path).isdir():
                layer_algorithm = fname
                for layer_f in os.listdir(f_path):
                    layer_id = layer_algorithm + ':' + layer_f
                    structure["repolayers"][layer_id] = {}
                    structure["repolayers"][layer_id]["layer_f"] = \
                            f_path + '/' + layer_f
                    structure["repolayers"][layer_id]["layer_a"] = \
                            layer_algorithm
                    structure["repolayers"][layer_id]["layer_h"] = \
                            layer_f
        return structure

    def _get_from_manifest(self, structure, imagetag):
        """Search for OCI manifest and return Config and layer ids"""
        try:
            config_layer = \
                    structure["manifest"][imagetag]["json"]["config"]["digest"]
        except (KeyError, ValueError, TypeError):
            config_layer = ""
        try:
            layers = []
            for layer in structure["manifest"][imagetag]["json"]["layers"]:
                layers.append(layer["digest"])
            layers.reverse()
            return (config_layer, layers)
        except (KeyError, ValueError, TypeError):
            return (config_layer, [])

    def _load_manifest(self, structure, manifest):
        """Load OCI manifest"""
        try:
            tag = manifest["annotations"]["org.opencontainers.image.ref.name"]
        except KeyError:
            tag = Unique().imagetag()
        if '/' in tag and ':' in tag:
            (imagerepo, tag) = tag.split(':', 1)
        else:
            imagerepo = Unique().imagename()
        if self._imagerepo:
            imagerepo = self._imagerepo
        imagetag = imagerepo + ':' + tag
        structure["manifest"][imagetag] = {}
        structure["manifest"][imagetag]["json"] = \
                self.localrepo.load_json(structure["repolayers"]\
                [manifest["digest"]]["layer_f"])
        structure["manifest"][imagetag]["json_f"] = \
                structure["repolayers"][manifest["digest"]]["layer_f"]
        return self._load_image(structure, imagerepo, tag)

    def _load_repositories(self, structure):
        """Load OCI image repositories"""
        loaded_repositories = []
        for manifest in structure["index"]["manifests"]:
            if manifest["mediaType"] == \
                    "application/vnd.oci.image.manifest.v1+json":
                loaded_repositories.append(
                    self._load_manifest(structure, manifest))
            elif manifest["mediaType"] == \
                    "application/vnd.oci.image.index.v1+json":
                loaded_repositories.extend(self._load_repositories(
                    self.localrepo.load_json(
                        structure["repolayers"]
                        [manifest["digest"]]["layer_f"])))
        return loaded_repositories

    def _load_image_step2(self, structure, imagerepo, tag):
        """Prepare load of OCI image"""
        imagetag = imagerepo + ':' + tag
        (config_layer_id, layers) = \
                self._get_from_manifest(structure, imagetag)
        if config_layer_id:
            json_file = structure["repolayers"][config_layer_id]["layer_f"]
            self._move_layer_to_v1repo(json_file, config_layer_id,
                                       "container.json")
        layer_hash_list = []
        for layer_id in layers:
            Msg().out("Info: adding layer:", layer_id, l=Msg.INF)
            filename = str(structure["repolayers"][layer_id]["layer_f"])
            if not self._move_layer_to_v1repo(filename, layer_id):
                Msg().err("Error: copying layer file", filename, l=Msg.VER)
                return []
            layer_hash_list.append(structure["repolayers"][layer_id]["layer_h"])
        self.localrepo.save_json("ancestry", layer_hash_list)
        return [imagetag]

    def load(self, tmp_imagedir, imagerepo=None):
        """Load an OCI image file The file is a tarball containing several
        layers, each layer has metadata and data content (directory tree)
        stored as a tar file.
        """
        self._imagerepo = imagerepo
        structure = self._load_structure(tmp_imagedir)
        if not structure:
            Msg().err("Error: failed to load image structure")
            return []
        return self._load_repositories(structure)
