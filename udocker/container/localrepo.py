# -*- coding: utf-8 -*-
"""Local repository management for images, containers"""

import os
import re
import json
import hashlib

from udocker.config import Config
from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil


class LocalRepository(object):
    """Implements a basic repository for images and containers.
    The repository will be usually in the user home directory.
    The repository has a simple directory structure:
    1. layers    : one dir containing all image layers so that
                   layers shared among images are not duplicated
    2. containers: has inside one directory per container,
                   each dir has a ROOT with the extracted image
    3. repos:      has inside a directory tree of repos the
                   leaf repo dirs are called tags and contain the
                   image data (these are links both to layer tarballs
                   and json metadata files.
    4. bin:        contains executables (PRoot)
    5. lib:        contains python libraries
    """

    def __init__(self, topdir=None):
        self.topdir = topdir if topdir else Config.conf['topdir']
        self.bindir = Config.conf['bindir']
        self.libdir = Config.conf['libdir']
        self.reposdir = Config.conf['reposdir']
        self.layersdir = Config.conf['layersdir']
        self.containersdir = Config.conf['containersdir']
        self.homedir = Config.conf['homedir']

        if not self.bindir:
            self.bindir = self.topdir + "/bin"
        if not self.libdir:
            self.libdir = self.topdir + "/lib"
        if not self.reposdir:
            self.reposdir = self.topdir + "/repos"
        if not self.layersdir:
            self.layersdir = self.topdir + "/layers"
        if not self.containersdir:
            self.containersdir = self.topdir + "/containers"

        self.cur_repodir = ""
        self.cur_tagdir = ""
        self.cur_containerdir = ""

        FileUtil(self.reposdir).register_prefix()
        FileUtil(self.layersdir).register_prefix()
        FileUtil(self.containersdir).register_prefix()

    def setup(self, topdir=None):
        """change to a different localrepo"""
        self.__init__(topdir)

    def sha256(self, filename):
        """sha256 calculation using hashlib"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filename, "rb") as filep:
                for chunk in iter(lambda: filep.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (IOError, OSError):
            return ""

    def create_repo(self):
        """creates properties with pathnames for easy
        access to the several repository directories
        """
        try:
            if not os.path.exists(self.topdir):
                os.makedirs(self.topdir)
            if not os.path.exists(self.reposdir):
                os.makedirs(self.reposdir)
            if not os.path.exists(self.layersdir):
                os.makedirs(self.layersdir)
            if not os.path.exists(self.containersdir):
                os.makedirs(self.containersdir)
            if not os.path.exists(self.bindir):
                os.makedirs(self.bindir)
            if not os.path.exists(self.libdir):
                os.makedirs(self.libdir)
            if not (Config.conf['keystore'].startswith("/") or \
                    os.path.exists(self.homedir)):
                os.makedirs(self.homedir)
        except(IOError, OSError):
            return False
        else:
            return True

    def is_repo(self):
        """check if directory structure corresponds to a repo"""
        dirs_exist = [os.path.exists(self.reposdir),
                      os.path.exists(self.layersdir),
                      os.path.exists(self.containersdir),
                      os.path.exists(self.bindir),
                      os.path.exists(self.libdir),
                      os.path.exists(self.homedir)]
        return all(dirs_exist)

    def protect_container(self, container_id):
        """Protect a container directory against deletion"""
        return self._protect(self.cd_container(container_id))

    def unprotect_container(self, container_id):
        """Remove the protection against deletion"""
        return self._unprotect(self.cd_container(container_id))

    def isprotected_container(self, container_id):
        """See if a container directory is protected"""
        return self._isprotected(self.cd_container(container_id))

    def iswriteable_container(self, container_id):
        """See if a container root dir is writable by this user"""
        container_root = self.cd_container(container_id) + "/ROOT"
        if not os.path.exists(container_root):
            return 2
        if not os.path.isdir(container_root):
            return 3
        if os.access(container_root, os.W_OK):
            return 1
        return 0

    def get_containers_list(self, dir_only=True):
        """Get a list of all containers in the local repo
        dir_only: is optional and indicates
                  if True a summary list of container_ids and names
                  if False  an extended listing containing further
                  container information
        """
        containers_list = []
        if not os.path.isdir(self.containersdir):
            return []
        for fname in os.listdir(self.containersdir):
            container_dir = self.containersdir + "/" + fname
            if os.path.isdir(container_dir):
                try:
                    filep = open(container_dir + "/imagerepo.name", "r")
                except (IOError, OSError):
                    reponame = ""
                else:
                    reponame = filep.read()
                    filep.close()
                if dir_only:
                    containers_list.append(container_dir)
                elif not os.path.islink(container_dir):
                    names = self.get_container_name(fname)
                    if not names:
                        names = ""
                    containers_list.append((fname, reponame, str(names)))
        return containers_list

    def del_container(self, container_id):
        """Delete a container tree, the image layers are untouched"""
        container_dir = self.cd_container(container_id)
        if not container_dir:
            return False
        else:
            if container_dir in self.get_containers_list(True):
                for name in self.get_container_name(container_id):
                    self.del_container_name(name)  # delete aliases links
                if FileUtil(container_dir).remove():
                    self.cur_containerdir = ""
                    return True
        return False

    def cd_container(self, container_id):
        """Select a container directory for further operations"""
        container_dir = self.containersdir + "/" + str(container_id)
        if os.path.exists(container_dir):
            if container_dir in self.get_containers_list(True):
                return container_dir
        return ""

    def set_container_name(self, container_id, name):
        """Associates a name to a container id The container can
        then be referenced either by its id or by its name.
        """
        if self._name_is_valid(name):
            container_dir = self.cd_container(container_id)
            if container_dir:
                linkname = self.containersdir + "/" + name
                if os.path.exists(linkname):
                    return False
                return self._symlink(container_dir, linkname)
        return False

    def del_container_name(self, name):
        """Remove a name previously associated to a container"""
        if self._name_is_valid(name):
            linkname = self.containersdir + "/" + name
            if os.path.exists(linkname):
                return FileUtil(linkname).remove()
        return False

    def get_container_id(self, container_name):
        """From a container name obtain its container_id"""
        if container_name:
            pathname = self.containersdir + "/" + container_name
            if os.path.islink(pathname):
                return os.path.basename(os.readlink(pathname))
            elif os.path.isdir(pathname):
                return container_name
        return ""

    def get_container_name(self, container_id):
        """From a container_id obtain its name(s)"""
        if not os.path.isdir(self.containersdir):
            return []
        link_list = []
        for fname in os.listdir(self.containersdir):
            container = self.containersdir + "/" + fname
            if os.path.islink(container):
                real_container = os.readlink(container)
                if os.path.basename(real_container) == container_id:
                    link_list.append(fname)
        return link_list

    def setup_container(self, imagerepo, tag, container_id):
        """Create the directory structure for a container"""
        container_dir = self.containersdir + "/" + str(container_id)
        if os.path.exists(container_dir):
            return ""
        try:
            os.makedirs(container_dir + "/ROOT")
            out_imagerepo = open(container_dir + "/imagerepo.name", 'w')
        except (IOError, OSError):
            return None
        else:
            out_imagerepo.write(imagerepo + ":" + tag)
            out_imagerepo.close()
            self.cur_containerdir = container_dir
            return container_dir

    def protect_imagerepo(self, imagerepo, tag):
        """Protect an image repo TAG against deletion"""
        return self._protect(self.reposdir + "/" + imagerepo + "/" + tag)

    def unprotect_imagerepo(self, imagerepo, tag):
        """Removes the deletion protection"""
        return self._unprotect(self.reposdir + "/" + imagerepo + "/" + tag)

    def isprotected_imagerepo(self, imagerepo, tag):
        """See if this image TAG is protected against deletion"""
        return self._isprotected(self.reposdir + "/" + imagerepo + "/" + tag)

    def cd_imagerepo(self, imagerepo, tag):
        """Select an image TAG for further operations"""
        if imagerepo and tag:
            tag_dir = self.reposdir + "/" + imagerepo + "/" + tag
            if os.path.exists(tag_dir):
                if self._is_tag(tag_dir):
                    self.cur_repodir = self.reposdir + "/" + imagerepo
                    self.cur_tagdir = self.cur_repodir + "/" + tag
                    return self.cur_tagdir
        return ""

    def get_imagerepos(self):
        """get all images repositories with tags"""
        return self._get_tags(self.reposdir)

    def get_layers(self, imagerepo, tag):
        """Get all layers for a given image image tag"""
        layers_list = []
        tag_dir = self.cd_imagerepo(imagerepo, tag)
        if tag_dir:
            for fname in os.listdir(tag_dir):
                filename = tag_dir + "/" + fname
                if os.path.islink(filename):
                    size = FileUtil(filename).size()
                    layers_list.append((filename, size))
        return layers_list

    def add_image_layer(self, filename):
        """Add a layer to an image TAG"""
        if not (self.cur_repodir and self.cur_tagdir):
            return False
        if not os.path.exists(filename):
            return False
        if not os.path.exists(self.cur_repodir):
            return False
        if not os.path.exists(self.cur_tagdir):
            return False
        linkname = self.cur_tagdir + "/" + os.path.basename(filename)
        if os.path.islink(linkname):
            FileUtil(linkname).remove()
        self._symlink(filename, linkname)
        return True

    def setup_imagerepo(self, imagerepo):
        """Create directory for an image repository"""
        if not imagerepo:
            return None
        directory = self.reposdir + "/" + imagerepo
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.cur_repodir = directory
                return True
            else:
                self.cur_repodir = directory
                return False
        except (IOError, OSError):
            return None

    def setup_tag(self, tag):
        """Create directory structure for an image TAG
        to be invoked after setup_imagerepo()
        """
        directory = self.cur_repodir + "/" + tag
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            self.cur_tagdir = directory
            out_tag = open(directory + "/TAG", 'w')
        except (IOError, OSError):
            return False
        else:
            out_tag.write(self.cur_repodir + ":" + tag)
            out_tag.close()
        return True

    def set_version(self, version):
        """Set the version of the image TAG repository currently
        it supports Docker images with versions v1 and v2
        to be invoked after setup_tag()
        """
        if not (self.cur_repodir and self.cur_tagdir):
            return False
        if not os.path.exists(self.cur_repodir):
            return False
        if not os.path.exists(self.cur_tagdir):
            return False
        directory = self.cur_tagdir
        if (os.path.exists(directory + "/v1") and version != "v1" or
                os.path.exists(directory + "/v2") and version != "v2"):
            if len(os.listdir(directory)) == 1:
                try:
                    FileUtil(directory + "/v1").remove()
                    FileUtil(directory + "/v2").remove()
                except (IOError, OSError):
                    pass
                if os.listdir(directory):
                    return False
        try:
            # Create version file
            open(directory + "/" + version, 'a').close()
        except (IOError, OSError):
            return False
        return True

    def get_image_attributes(self):
        """Load attributes from image TAGs that have been previously
        selected via cd_imagerepo(). Supports images of type v1 and v2.
        Returns: (container JSON, list of layer files).
        """
        files = []
        directory = self.cur_tagdir
        if os.path.exists(directory + "/v1"):   # if dockerhub API v1
            layer_list = self.load_json("ancestry")
            if layer_list:
                for layer_id in reversed(layer_list):
                    f_layer = directory + "/" + layer_id + ".layer"
                    if not os.path.exists(f_layer):
                        return(None, None)
                    files.append(f_layer)
                json_file = directory + "/" + layer_list[0] + ".json"
                if os.path.exists(json_file):
                    container_json = self.load_json(json_file)
                    return(container_json, files)
        elif os.path.exists(directory + "/v2"):  # if dockerhub API v1
            manifest = self.load_json("manifest")
            if manifest and manifest["fsLayers"]:
                for layer in reversed(manifest["fsLayers"]):
                    f_layer = directory + "/" + layer["blobSum"]
                    if not os.path.exists(f_layer):
                        return(None, None)
                    files.append(f_layer)
                json_string = manifest["history"][0]["v1Compatibility"].strip()
                try:
                    container_json = json.loads(json_string)
                except (IOError, OSError, AttributeError,
                        ValueError, TypeError):
                    return(None, None)
                return(container_json, files)
        return(None, None)

    def save_json(self, filename, data):
        """Save container json to a file in the image TAG directory
        that has been previously selected via cd_imagerepo()
        or if the file starts with "/" to that specific file.
        """
        if filename.startswith("/"):
            out_filename = filename
        else:
            if not (self.cur_repodir and self.cur_tagdir):
                return False
            if not os.path.exists(self.cur_repodir):
                return False
            if not os.path.exists(self.cur_tagdir):
                return False
            out_filename = self.cur_tagdir + "/" + filename
        outfile = None
        try:
            outfile = open(out_filename, 'w')
            json.dump(data, outfile)
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            if outfile:
                outfile.close()
            return False
        outfile.close()
        return True

    def load_json(self, filename):
        """Load container json from a file in the image TAG directory
        that has been previously selected via cd_imagerepo()
        or if the file starts with "/" from that specific file.
        """
        if filename is None:
            Msg().err("Error: Empty filename")
            return False
        if filename.startswith("/"):
            in_filename = filename
        else:
            if not (self.cur_repodir and self.cur_tagdir):
                return False
            if not os.path.exists(self.cur_repodir):
                return False
            if not os.path.exists(self.cur_tagdir):
                return False
            in_filename = self.cur_tagdir + "/" + filename
        json_obj = None
        infile = None
        try:
            infile = open(in_filename)
            json_obj = json.load(infile)
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            pass
        if infile:
            infile.close()
        return json_obj

    def del_imagerepo(self, imagerepo, tag, force=False):
        """Delete an image repository and its layers"""
        tag_dir = self.cd_imagerepo(imagerepo, tag)
        if (tag_dir and self._remove_layers(tag_dir, force) and
                FileUtil(tag_dir).remove()):
            self.cur_repodir = ""
            self.cur_tagdir = ""
            return True
        return False

    def find_top_layer_id(self, structure, my_layer_id=""):
        """Find the id of the top layer of a given image tag in a
        structure produced by _load_structure()
        """
        if "layers" not in structure:
            return []
        else:
            if not my_layer_id:
                my_layer_id = list(structure["layers"].keys())[0]
            found = ""
            for layer_id in structure["layers"]:
                if "json" not in structure["layers"][layer_id]:   # v2
                    continue
                elif "parent" not in structure["layers"][layer_id]["json"]:
                    continue
                elif (my_layer_id ==
                      structure["layers"][layer_id]["json"]["parent"]):
                    found = self.find_top_layer_id(structure, layer_id)
                    break
            if not found:
                return my_layer_id
            return found

    def sorted_layers(self, structure, top_layer_id):
        """Return the image layers sorted"""
        sorted_layers = []
        next_layer = top_layer_id
        while next_layer:
            sorted_layers.append(next_layer)
            if "json" not in structure["layers"][next_layer]:   # v2
                break
            if "parent" not in structure["layers"][next_layer]["json"]:
                break
            else:
                next_layer = structure["layers"][next_layer]["json"]["parent"]
                if not next_layer:
                    break
        return sorted_layers

    def verify_image(self):
        """Verify the structure of an image repository"""
        Msg().out("Info: loading structure", l=Msg.INF)
        structure = self._load_structure(self.cur_tagdir)
        if not structure:
            Msg().err("Error: load of image tag structure failed")
            return False
        Msg().out("Info: finding top layer id", l=Msg.INF)
        top_layer_id = self.find_top_layer_id(structure)
        if not top_layer_id:
            Msg().err("Error: finding top layer id")
            return False
        Msg().out("Info: sorting layers", l=Msg.INF)
        layers_list = self.sorted_layers(structure, top_layer_id)
        status = True
        if "ancestry" in structure:
            layer = iter(layers_list)
            for ancestry_layer in structure["ancestry"]:
                verify_layer = layer.next()
                if ancestry_layer != verify_layer:
                    Msg().err("Error: ancestry and layers do not match",
                              ancestry_layer, verify_layer)
                    status = False
                    continue
        elif "manifest" in structure:
            for manifest_layer in structure["manifest"]["fsLayers"]:
                if manifest_layer["blobSum"] not in structure["layers"]:
                    Msg().err("Error: layer in manifest does not exist",
                              " in repo", manifest_layer)
                    status = False
                    continue
        for layer_id in structure["layers"]:
            if "layer_f" not in structure["layers"][layer_id]:
                Msg().err("Error: layer file not found in structure",
                          layer_id)
                status = False
                continue
            layer_status = self._verify_layer_file(structure, layer_id)
            if not layer_status:
                status = False
                continue
            Msg().out("Info: layer ok:", layer_id, l=Msg.INF)
        return status

    def _protect(self, directory):
        """Set the protection mark in a container or image tag"""
        try:
            # touch create version file
            open(directory + "/PROTECT", 'w').close()
            return True
        except (IOError, OSError):
            return False

    def _unprotect(self, directory):
        """Remove protection mark from container or image tag"""
        return FileUtil(directory + "/PROTECT").remove()

    def _isprotected(self, directory):
        """See if container or image tag are protected"""
        return os.path.exists(directory + "/PROTECT")

    def _symlink(self, existing_file, link_file):
        """Create relative symbolic links"""
        if os.path.exists(link_file):
            return False
        rel_path_to_existing = os.path.relpath(
            existing_file, os.path.dirname(link_file))
        try:
            os.symlink(rel_path_to_existing, link_file)
        except (IOError, OSError):
            return False
        return True

    def _name_is_valid(self, name):
        """Check name alias validity"""
        invalid_chars = ("/", ".", " ", "[", "]")
        if name and any(x in name for x in invalid_chars):
            return False
        return not len(name) > 2048

    def _is_tag(self, tag_dir):
        """Does this directory contain an image tag ?
        An image TAG indicates that this repo directory
        contains references to layers and metadata from
        which we can extract a container.
        """
        try:
            if os.path.isfile(tag_dir + "/TAG"):
                return True
        except (IOError, OSError):
            pass
        return False

    def _find(self, filename, in_dir):
        """is a specific layer filename referenced by another image TAG"""
        found_list = []
        if os.path.isdir(in_dir):
            for fullname in os.listdir(in_dir):
                f_path = in_dir + "/" + fullname
                if os.path.islink(f_path):
                    if filename in fullname:       # match .layer or .json
                        found_list.append(f_path)  # found reference to layer
                elif os.path.isdir(f_path):
                    found_list.extend(self._find(filename, f_path))
        return found_list

    def _inrepository(self, filename):
        """Check if a given file is in the repository"""
        return self._find(filename, self.reposdir)

    def _remove_layers(self, tag_dir, force):
        """Remove link to image layer and corresponding layer
        if not being used by other images
        """
        for fname in os.listdir(tag_dir):
            f_path = tag_dir + "/" + fname  # link to layer
            if os.path.islink(f_path):
                f_layer = tag_dir + "/" + os.readlink(f_path)
                if not FileUtil(f_path).remove() and not force:
                    return False
                if not self._inrepository(fname):
                    # removing actual layers not reference by other repos
                    if not FileUtil(f_layer).remove() and not force:
                        return False
        return True

    def _get_tags(self, tag_dir):
        """Get image tags from repository
        The tags identify actual usable containers
        """
        tag_list = []
        if os.path.isdir(tag_dir):
            for fname in os.listdir(tag_dir):
                f_path = tag_dir + "/" + fname
                if self._is_tag(f_path):
                    tag_list.append(
                        (tag_dir.replace(self.reposdir + "/", ""), fname))
                elif os.path.isdir(f_path):
                    tag_list.extend(self._get_tags(f_path))
        return tag_list

    def _load_structure(self, imagetagdir):
        """Scan the repository structure of a given image tag"""
        structure = {}
        structure["layers"] = dict()
        if os.path.isdir(imagetagdir):
            for fname in os.listdir(imagetagdir):
                f_path = imagetagdir + "/" + fname
                if fname == "ancestry":
                    structure["ancestry"] = self.load_json(f_path)
                elif fname == "manifest":
                    structure["manifest"] = self.load_json(f_path)
                elif len(fname) >= 64:
                    layer_id = fname.replace(".json", "").replace(".layer", "")
                    if layer_id not in structure["layers"]:
                        structure["layers"][layer_id] = dict()
                    if fname.endswith("json"):
                        structure["layers"][layer_id]["json"] = \
                            self.load_json(f_path)
                        structure["layers"][layer_id]["json_f"] = f_path
                    elif fname.endswith("layer"):
                        structure["layers"][layer_id]["layer_f"] = f_path
                    elif fname.startswith("sha"):
                        structure["layers"][layer_id]["layer_f"] = f_path
                    else:
                        Msg().err("Warning: unkwnon file in layer:", f_path,
                                  l=Msg.WAR)
                elif fname in ("TAG", "v1", "v2", "PROTECT"):
                    pass
                else:
                    Msg().err("Warning: unkwnon file in image:", f_path,
                              l=Msg.WAR)
        return structure

    def _verify_layer_file(self, structure, layer_id):
        """Verify layer file in repository"""
        layer_f = structure["layers"][layer_id]["layer_f"]
        if not (os.path.exists(layer_f) and
                os.path.islink(layer_f)):
            Msg().err("Error: layer data file symbolic link not found",
                      layer_id)
            return False
        if not os.path.exists(self.cur_tagdir + "/" +
                              os.readlink(layer_f)):
            Msg().err("Error: layer data file not found")
            return False
        if not FileUtil(layer_f).verify_tar():
            Msg().err("Error: layer file not ok:", layer_f)
            return False
        match = re.search("/sha256:(\\S+)$", layer_f)
        if match:
            layer_f_chksum = self.sha256(layer_f)
            if layer_f_chksum != match.group(1):
                Msg().err("Error: layer file chksum error:", layer_f)
                return False
        return True