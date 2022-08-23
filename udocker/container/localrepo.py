# -*- coding: utf-8 -*-
"""Local repository management for images, containers"""

import os
import re
import sys
import stat
import json

from udocker import is_genstr
from udocker.config import Config
from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil
from udocker.utils.chksum import ChkSUM
from udocker.utils.uprocess import Uprocess
from udocker.helper.osinfo import OSInfo


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
        self.docdir = Config.conf['docdir']
        self.reposdir = Config.conf['reposdir']
        self.layersdir = Config.conf['layersdir']
        self.containersdir = Config.conf['containersdir']
        self.homedir = Config.conf['homedir']

        if not self.bindir:
            self.bindir = self.topdir + "/bin"
        if not self.libdir:
            self.libdir = self.topdir + "/lib"
        if not self.docdir:
            self.docdir = self.topdir + "/doc"
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
            if not os.path.exists(self.docdir):
                os.makedirs(self.docdir)
            if not (Config.conf['keystore'].startswith("/") or \
                    os.path.exists(self.homedir)):
                os.makedirs(self.homedir)
        except(IOError, OSError):
            return False
        return True

    def is_repo(self):
        """check if directory structure corresponds to a repo"""
        dirs_exist = [os.path.exists(self.reposdir),
                      os.path.exists(self.layersdir),
                      os.path.exists(self.containersdir),
                      os.path.exists(self.bindir),
                      os.path.exists(self.libdir)]
        return all(dirs_exist)

    def is_container_id(self, obj):
        """Verify if the provided object matches the format of a
        local container id.
        """
        if not is_genstr(obj):
            return False
        match = re.match(
            "^[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+$", obj)
        if match:
            return True
        return False

    def protect_container(self, container_id):
        """Protect a container directory against deletion"""
        return self._protect(self.cd_container(container_id))

    def unprotect_container(self, container_id):
        """Remove the protection against deletion"""
        return self._unprotect(self.cd_container(container_id))

    def isprotected_container(self, container_id):
        """See if a container directory is protected"""
        return self._isprotected(self.cd_container(container_id))

    def _protect(self, directory):
        """Set the protection mark in a container or image tag"""
        try:
            # touch create version file
            open(directory + "/PROTECT", 'w', encoding='utf-8').close()
            return True
        except (IOError, OSError):
            return False

    def _unprotect(self, directory):
        """Remove protection mark from container or image tag"""
        return FileUtil(directory + "/PROTECT").remove()

    def _isprotected(self, directory):
        """See if container or image tag are protected"""
        return os.path.exists(directory + "/PROTECT")

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

    def get_size(self, container_id):
        """See if a container root dir is writable by this user"""
        container_root = self.cd_container(container_id) + "/ROOT"
        try:
            size, dummy = Uprocess().get_output(["du", "-s", "-m", "-x",
                                                 container_root]).split()
            return int(size)
        except (ValueError, NameError, AttributeError):
            return -1

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
            container_dir = self.containersdir + '/' + fname
            if os.path.isdir(container_dir):
                try:
                    filep = open(container_dir + "/imagerepo.name", 'r',
                                 encoding='utf-8')
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

    def del_container(self, container_id, force=False):
        """Delete a container tree, the image layers are untouched"""
        container_dir = self.cd_container(container_id)
        if not container_dir:
            return False

        if container_dir in self.get_containers_list(True):
            for name in self.get_container_name(container_id):
                self.del_container_name(name)  # delete aliases links
            if force:
                FileUtil(container_dir).rchmod(stat.S_IWUSR | stat.S_IRUSR,
                                                stat.S_IWUSR | stat.S_IRUSR |
                                                stat.S_IXUSR)
            if FileUtil(container_dir).remove(recursive=True):
                self.cur_containerdir = ""
                return True

        return False

    def cd_container(self, container_id):
        """Select a container directory for further operations"""
        container_dir = self.containersdir + '/' + str(container_id)
        if os.path.exists(container_dir):
            if container_dir in self.get_containers_list(True):
                return container_dir
        return ""

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

    def set_container_name(self, container_id, name):
        """Associates a name to a container id The container can
        then be referenced either by its id or by its name.
        """
        if self._name_is_valid(name):
            container_dir = self.cd_container(container_id)
            if container_dir:
                linkname = os.path.realpath(self.containersdir + '/' + name)
                if os.path.exists(linkname):
                    return False
                real_container_dir = os.path.realpath(container_dir)
                return self._symlink(real_container_dir, linkname)
        return False

    def del_container_name(self, name):
        """Remove a name previously associated to a container"""
        if self._name_is_valid(name):
            linkname = self.containersdir + '/' + name
            if os.path.islink(linkname):
                return FileUtil(linkname).remove()
        return False

    def get_container_id(self, container_name):
        """From a container name obtain its container_id"""
        if container_name:
            pathname = self.containersdir + "/" + container_name
            if os.path.islink(pathname):
                return os.path.basename(os.readlink(pathname))
            if os.path.isdir(pathname):
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
            out_imagerepo = open(container_dir + "/imagerepo.name", 'w',
                                 encoding='utf-8')
        except (IOError, OSError):
            return None
        else:
            out_imagerepo.write(imagerepo + ":" + tag)
            out_imagerepo.close()
            self.cur_containerdir = container_dir
            return container_dir

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

    def _find(self, filename, in_dir):
        """is a specific layer filename referenced by another image TAG"""
        found_list = []
        if FileUtil(in_dir).isdir():
            for fullname in os.listdir(in_dir):
                f_path = in_dir + '/' + fullname
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
            f_path = tag_dir + '/' + fname  # link to layer
            if os.path.islink(f_path):
                linkname = os.readlink(f_path)
                layer_file = tag_dir + '/' + linkname
                if not FileUtil(f_path).remove() and not force:
                    return False
                if not self._inrepository(os.path.basename(linkname)):
                    # removing actual layers not reference by other repos
                    if not FileUtil(layer_file).remove() and not force:
                        return False
        return True

    def del_imagerepo(self, imagerepo, tag, force=False):
        """Delete an image repository and its layers"""
        tag_dir = self.cd_imagerepo(imagerepo, tag)
        if (tag_dir and
                self._remove_layers(tag_dir, force) and
                FileUtil(tag_dir).remove(recursive=True)):
            self.cur_repodir = ""
            self.cur_tagdir = ""
            while imagerepo:
                FileUtil(self.reposdir + '/' + imagerepo).rmdir()
                imagerepo = "/".join(imagerepo.split("/")[:-1])
            return True
        return False

    def _get_tags(self, tag_dir):
        """Get image tags from repository
        The tags identify actual usable containers
        """
        tag_list = []
        if FileUtil(tag_dir).isdir():
            for fname in os.listdir(tag_dir):
                f_path = tag_dir + '/' + fname
                if self._is_tag(f_path):
                    tag_list.append(
                        (tag_dir.replace(self.reposdir + '/', ""), fname))
                elif os.path.isdir(f_path):
                    tag_list.extend(self._get_tags(f_path))
        return tag_list

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

    def add_image_layer(self, filename, linkname=None):
        """Add a layer to an image TAG"""
        if not self.cur_tagdir:
            return False
        if not os.path.exists(filename):
            return False
        if not os.path.exists(self.cur_tagdir):
            return False
        if linkname:
            linkname = self.cur_tagdir + '/' + os.path.basename(linkname)
        else:
            linkname = self.cur_tagdir + '/' + os.path.basename(filename)
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
            out_tag = open(directory + "/TAG", 'w', encoding='utf-8')
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
            open(directory + "/" + version, 'a', encoding='utf-8').close()
        except (IOError, OSError):
            return False
        return True

    def _get_image_attributes_v1(self, directory):
        """Get image attributes from image directory in v1 format"""
        files = []
        layer_list = self.load_json("ancestry")
        if layer_list:
            for layer_id in reversed(layer_list):
                layer_file = directory + '/' + layer_id + ".layer"
                if not os.path.exists(layer_file):
                    return (None, None)
                files.append(layer_file)
            json_file_list = [directory + "/container.json",
                              directory + '/' + layer_list[0] + ".json", ]
            for json_file in json_file_list:
                if os.path.exists(json_file):
                    container_json = self.load_json(json_file)
                    return (container_json, files)
        return (None, None)

    def _get_image_attributes_v2_s1(self, directory, manifest):
        """Get image attributes from image directory in v2 schema 1 format"""
        files = []
        for layer in reversed(manifest["fsLayers"]):
            layer_file = directory + '/' + layer["blobSum"]
            if not os.path.exists(layer_file):
                return (None, None)
            files.append(layer_file)
        try:
            json_string = manifest["history"][0]["v1Compatibility"].strip()
            container_json = json.loads(json_string)
        except (IOError, OSError, AttributeError, ValueError, TypeError,
                IndexError, KeyError):
            return (None, files)
        return (container_json, files)

    def _get_image_attributes_v2_s2(self, directory, manifest):
        """Get image attributes from image directory in v2 schema 2 format"""
        files = []
        for layer in manifest["layers"]:
            layer_file = directory + '/' + layer["digest"]
            if not os.path.exists(layer_file):
                return (None, None)
            files.append(layer_file)
        try:
            json_file = directory + '/' + manifest["config"]["digest"]
            container_json = json.loads(FileUtil(json_file).getdata('r'))
        except (IOError, OSError, AttributeError, ValueError, TypeError,
                IndexError, KeyError):
            return (None, files)
        return (container_json, files)

    def get_image_attributes(self):
        """Load attributes from image TAGs that have been previously
        selected via cd_imagerepo(). Supports images of type v1 and v2.
        Returns: (container JSON, list of layer files).
        """
        directory = self.cur_tagdir
        if os.path.exists(directory + "/v1"):   # if dockerhub API v1
            return self._get_image_attributes_v1(directory)

        if os.path.exists(directory + "/v2"):  # if dockerhub API v1
            manifest = self.load_json("manifest")
            if manifest and "fsLayers" in manifest:
                return self._get_image_attributes_v2_s1(directory, manifest)
            if manifest and "layers" in manifest:
                return self._get_image_attributes_v2_s2(directory, manifest)

        return (None, None)

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
            outfile = open(out_filename, 'w', encoding='utf-8')
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
        or if the file starts with '/' from that specific file.
        """
        if filename.startswith('/'):
            in_filename = filename
        else:
            if not (self.cur_repodir and self.cur_tagdir):
                return False
            if not os.path.exists(self.cur_repodir):
                return False
            if not os.path.exists(self.cur_tagdir):
                return False
            in_filename = self.cur_tagdir + '/' + filename
        json_obj = None
        infile = None
        try:
            infile = open(in_filename, 'r', encoding='utf-8')
            json_obj = json.load(infile)
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            pass
        if infile:
            infile.close()
        return json_obj

    def _load_structure(self, imagetagdir):
        """Scan the repository structure of a given image tag"""
        structure = {}
        structure["repolayers"] = {}
        if FileUtil(imagetagdir).isdir():
            for fname in os.listdir(imagetagdir):
                f_path = imagetagdir + '/' + fname
                if fname == "ancestry":
                    structure["ancestry"] = self.load_json(f_path)

                if fname == "manifest":
                    structure["manifest"] = self.load_json(f_path)

                if len(fname) >= 64:
                    layer_id = fname.replace(".json", "").replace(".layer", "")
                    if layer_id not in structure["repolayers"]:
                        structure["repolayers"][layer_id] = {}
                    if fname.endswith("json"):
                        structure["repolayers"][layer_id]["json"] = \
                            self.load_json(f_path)
                        structure["repolayers"][layer_id]["json_f"] = f_path
                        structure["has_json_f"] = True
                    elif fname.endswith("layer"):
                        structure["repolayers"][layer_id]["layer_f"] = f_path
                    elif ':' in fname:
                        structure["repolayers"][layer_id]["layer_f"] = f_path
                    else:
                        Msg().out("Warning: unkwnon file in layer:", f_path,
                                  l=Msg.WAR)
                elif fname in ("TAG", "v1", "v2", "PROTECT", "container.json"):
                    pass

                else:
                    Msg().out("Warning: unkwnon file in image:", f_path, l=Msg.WAR)

        return structure

    def _find_top_layer_id(self, structure, my_layer_id=""):
        """Find the id of the top layer of a given image tag in a
        structure produced by _load_structure()
        """
        if "repolayers" not in structure:
            return ""

        if not my_layer_id:
            if sys.version_info[0] >= 3:
                my_layer_id = list(structure["repolayers"].keys())[0]
            else:
                my_layer_id = structure["repolayers"].keys()[0]

        found = ""
        for layer_id in structure["repolayers"]:
            if "json" not in structure["repolayers"][layer_id]:   # v2
                continue
            if "parent" not in structure["repolayers"][layer_id]["json"]:
                continue
            if (my_layer_id ==
                    structure["repolayers"][layer_id]["json"]["parent"]):
                found = self._find_top_layer_id(structure, layer_id)
                break

        if not found:
            return my_layer_id

        return found

    def _sorted_layers(self, structure, top_layer_id):
        """Return the image layers sorted"""
        sorted_layers = []
        next_layer = top_layer_id
        while next_layer:
            sorted_layers.append(next_layer)
            if "json" not in structure["repolayers"][next_layer]:   # v2
                break

            if "parent" not in structure["repolayers"][next_layer]["json"]:
                break

            next_layer = structure["repolayers"][next_layer]["json"]["parent"]
            if not next_layer:
                break

        return sorted_layers

    def _split_layer_id(self, layer_id):
        """Split layer_id (sha256:xxxxx)"""
        if ':' in layer_id:
            return layer_id.split(":", 1)

        return ("", layer_id)

    def _verify_layer_file(self, structure, layer_id):
        """Verify layer file in repository"""
        (layer_algorithm, layer_hash) = self._split_layer_id(layer_id)
        layer_f = structure["repolayers"][layer_id]["layer_f"]
        if not (os.path.exists(layer_f) and
                os.path.islink(layer_f)):
            Msg().err("Error: layer data file symbolic link not found",
                      layer_id)
            return False
        if not os.path.exists(self.cur_tagdir + '/' +
                              os.readlink(layer_f)):
            Msg().err("Error: layer data file not found")
            return False
        if "gzip" in OSInfo('/').get_filetype(layer_f):
            if not FileUtil(layer_f).verify_tar():
                Msg().err("Error: layer tar verify failed:", layer_f)
                return False
        if layer_algorithm:
            layer_f_chksum = ChkSUM().hash(layer_f, layer_algorithm)
            if layer_f_chksum and layer_f_chksum != layer_hash:
                Msg().err("Error: layer file chksum failed:", layer_f)
                return False
        return True

    def _verify_image_v1(self, structure):
        """Verify the structure of a v1 image repository"""
        Msg().out("Info: finding top layer id", l=Msg.INF)
        top_layer_id = self._find_top_layer_id(structure)
        if not top_layer_id:
            Msg().err("Error: finding top layer id")
            return False
        layers_list = self._sorted_layers(structure, top_layer_id)
        layer = iter(layers_list)
        status = True
        for ancestry_layer in structure["ancestry"]:
            if sys.version_info[0] >= 3:
                verify_layer = next(layer)
            else:
                verify_layer = layer.next()
            if ancestry_layer != verify_layer:
                Msg().err("Error: ancestry and layers do not match",
                          ancestry_layer, verify_layer)
                status = False
                continue
        return status

    def _verify_image_v2_s1(self, structure):
        """Verify the structure of a v2 schema 1 image repository"""
        status = True
        for manifest_layer in structure["manifest"]["fsLayers"]:
            if manifest_layer["blobSum"] not in structure["repolayers"]:
                Msg().err("Error: layer in manifest does not exist",
                          "in repo", manifest_layer["blobSum"])
                status = False
                continue
        return status

    def _verify_image_v2_s2(self, structure):
        """Verify the structure of a v2 schema 2 image repository"""
        status = True
        for manifest_layer in structure["manifest"]["layers"]:
            if manifest_layer["digest"] not in structure["repolayers"]:
                Msg().err("Error: layer in manifest does not exist",
                          "in repo", manifest_layer["blobSum"])
                status = False
                continue
        return status

    def verify_image(self):
        """Verify the structure of an image repository"""
        Msg().out("Info: loading structure", l=Msg.INF)
        structure = self._load_structure(self.cur_tagdir)
        if not structure:
            Msg().err("Error: load of image tag structure failed")
            return False
        Msg().out("Info: verifying layers", l=Msg.INF)
        status = True
        if "ancestry" in structure and "has_json_f" in structure:
            status = self._verify_image_v1(structure)
        elif "manifest" in structure:
            if "fsLayers" in structure["manifest"]:
                status = self._verify_image_v2_s1(structure)
            elif "layers" in structure["manifest"]:
                status = self._verify_image_v2_s2(structure)
        for layer_id in structure["repolayers"]:
            if "layer_f" not in structure["repolayers"][layer_id]:
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
