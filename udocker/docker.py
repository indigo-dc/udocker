# -*- coding: utf-8 -*-
"""Docker API integration"""

import os
import re
import time
import base64
import subprocess
import json

from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil
from udocker.utils.curl import GetURL
from udocker.helper.unique import Unique
from udocker.container.structure import ContainerStructure
from udocker.engine.execmode import ExecutionMode


class DockerIoAPI(object):
    """Class to encapsulate the access to the Docker Hub service
    Allows to search and download images from Docker Hub
    """

    def __init__(self, localrepo, conf):
        self.conf = conf
        self.index_url = self.conf['dockerio_index_url']
        self.registry_url = self.conf['dockerio_registry_url']
        self.v1_auth_header = ""
        self.v2_auth_header = ""
        self.v2_auth_token = ""
        self.localrepo = localrepo
        self.curl = GetURL(self.conf)
        self.docker_registry_domain = "docker.io"
        self.search_link = ""
        self.search_pause = True
        self.search_page = 0
        self.search_lines = 25
        self.search_link = ""
        self.search_ended = False

    def set_proxy(self, http_proxy):
        """Select a socks http proxy for API access and file download"""
        self.curl.set_proxy(http_proxy)

    def set_registry(self, registry_url):
        """Change docker registry url"""
        self.registry_url = registry_url

    def set_index(self, index_url):
        """Change docker index url"""
        self.index_url = index_url

    def is_repo_name(self, imagerepo):
        """Check if name matches authorized characters for a docker repo"""
        if imagerepo and re.match("^[a-zA-Z0-9][a-zA-Z0-9-_./:]+$", imagerepo):
            return True
        Msg().err("Error: invalid repo name syntax")
        return False

    def _is_docker_registry(self):
        """Check if registry is dockerhub"""
        regexp = r"%s(\:\d+)?(\/)?$" % (self.docker_registry_domain)
        return re.search(regexp, self.registry_url)

    def _get_url(self, *args, **kwargs):
        """Encapsulates the call to GetURL.get() so that authentication
        for v1 and v2 repositories can be treated differently.
        Example:
             _get_url(url, ctimeout=5, timeout=5, header=[]):
        """
        url = str(args[0])
        if "RETRY" not in kwargs:
            kwargs["RETRY"] = 3
        kwargs["RETRY"] -= 1
        (hdr, buf) = self.curl.get(*args, **kwargs)
        Msg().err("header: %s" % (hdr.data), l=Msg.DBG)
        if   ("X-ND-HTTPSTATUS" in hdr.data and
              "401" in hdr.data["X-ND-HTTPSTATUS"]):
            if "www-authenticate" in hdr.data and hdr.data["www-authenticate"]:
                if "RETRY" in kwargs and kwargs["RETRY"]:
                    auth_header = ""
                    if "/v2/" in url:
                        auth_header = self._get_v2_auth(
                            hdr.data["www-authenticate"], kwargs["RETRY"])
                    elif "/v1/" in url:
                        auth_header = self._get_v1_auth(
                            hdr.data["www-authenticate"])
                    auth_kwargs = kwargs.copy()
                    auth_kwargs.update({"header": [auth_header]})
                    if "location" in hdr.data and hdr.data['location']:
                        args = hdr.data['location']
                    (hdr, buf) = self._get_url(*args, **auth_kwargs)
                else:
                    hdr.data["X-ND-CURLSTATUS"] = 13  # Permission denied
        return(hdr, buf)

    def _get_v1_auth(self, www_authenticate):
        """Authentication for v1 API"""
        if "Token" in www_authenticate:
            return self.v1_auth_header
        return ""

    def _get_file(self, url, filename, cache_mode):
        """Get a file and check its size. Optionally enable other
        capabilities such as caching to check if the
        file already exists locally and whether its size is the
        same to avoid downloaded it again.
        """
        hdr = ""
        match = re.search("/sha256:(\\S+)$", filename)
        if match:
            layer_f_chksum = self.localrepo.sha256(filename)
            if layer_f_chksum == match.group(1):
                return True             # is cached skip download
            else:
                cache_mode = 0
        if self.curl.cache_support and cache_mode:
            if cache_mode == 1:
                (hdr, dummy) = self._get_url(url, nobody=1)
            elif cache_mode == 3:
                (hdr, dummy) = self._get_url(url, sizeonly=True)
            remote_size = self.curl.get_content_length(hdr)
            if remote_size == FileUtil(self.conf, filename).size():
                return True             # is cached skip download
        else:
            remote_size = -1
        resume = False
        if filename.endswith("layer"):
            resume = True
        (hdr, dummy) = self._get_url(url, ofile=filename, resume=resume)
        if remote_size == -1:
            remote_size = self.curl.get_content_length(hdr)
        if (remote_size != FileUtil(self.conf, filename).size() and
                hdr.data["X-ND-CURLSTATUS"]):
            Msg().err("Error: file size mismatch:", filename,
                      remote_size, FileUtil(self.conf, filename).size())
            return False
        return True

    def _split_fields(self, buf):
        """Split  fields, used in the web authentication"""
        all_fields = dict()
        for field in buf.split(","):
            pair = field.split("=", 1)
            if len(pair) == 2:
                all_fields[pair[0]] = pair[1].strip('"')
        return all_fields

    def get_v1_repo(self, imagerepo):
        """Get list of images in a repo from Docker Hub"""
        url = self.index_url + "/v1/repositories/" + imagerepo + "/images"
        Msg().err("repo url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url, header=["X-Docker-Token: true"])
        try:
            self.v1_auth_header = "Authorization: Token " + \
                hdr.data["x-docker-token"]
            return hdr.data, json.loads(buf.getvalue())
        except (IOError, OSError, AttributeError,
                ValueError, TypeError, KeyError):
            self.v1_auth_header = ""
            return hdr.data, []

    def get_v1_image_tags(self, endpoint, imagerepo):
        """Get list of tags in a repo from Docker Hub"""
        url = endpoint + "/v1/repositories/" + imagerepo + "/tags"
        Msg().err("tags url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v1_image_tag(self, endpoint, imagerepo, tag):
        """Get list of tags in a repo from Docker Hub"""
        url = endpoint + "/v1/repositories/" + imagerepo + "/tags/" + tag
        Msg().err("tags url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v1_image_ancestry(self, endpoint, image_id):
        """Get the ancestry which is an ordered list of layers"""
        url = endpoint + "/v1/images/" + image_id + "/ancestry"
        Msg().err("ancestry url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v1_image_json(self, endpoint, layer_id):
        """Get the JSON metadata for a specific layer"""
        url = endpoint + "/v1/images/" + layer_id + "/json"
        Msg().err("json url:", url, l=Msg.DBG)
        filename = self.localrepo.layersdir + "/" + layer_id + ".json"
        if self._get_file(url, filename, 0):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v1_image_layer(self, endpoint, layer_id):
        """Get a specific layer data file (layer files are tarballs)"""
        url = endpoint + "/v1/images/" + layer_id + "/layer"
        Msg().err("layer url:", url, l=Msg.DBG)
        filename = self.localrepo.layersdir + "/" + layer_id + ".layer"
        if self._get_file(url, filename, 3):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v1_layers_all(self, endpoint, layer_list):
        """Using a layer list download data and metadata files"""
        files = []
        if layer_list:
            for layer_id in reversed(layer_list):
                Msg().err("Downloading layer:", layer_id, l=Msg.INF)
                filesize = self.get_v1_image_json(endpoint, layer_id)
                if not filesize:
                    return []
                files.append(layer_id + ".json")
                filesize = self.get_v1_image_layer(endpoint, layer_id)
                if not filesize:
                    return []
                files.append(layer_id + ".layer")
        return files

    def _get_v2_auth(self, www_authenticate, retry):
        """Authentication for v2 API"""
        auth_header = ""
        (bearer, auth_data) = www_authenticate.rsplit(" ", 1)
        if bearer == "Bearer":
            auth_fields = self._split_fields(auth_data)
            if "realm" in auth_fields:
                auth_url = auth_fields["realm"] + "?"
                for field in auth_fields:
                    if field != "realm":
                        auth_url += field + "=" + auth_fields[field] + "&"
                header = []
                if self.v2_auth_token:
                    header = ["Authorization: Basic %s" % (self.v2_auth_token)]
                (dum, auth_buf) = \
                    self._get_url(auth_url, header=header, RETRY=retry)
                token_buf = auth_buf.getvalue()
                if token_buf and "token" in token_buf:
                    try:
                        auth_token = json.loads(token_buf)
                    except (IOError, OSError, AttributeError,
                            ValueError, TypeError):
                        return auth_header
                    auth_header = "Authorization: Bearer " + \
                        auth_token["token"]
                    self.v2_auth_header = auth_header
        # PR #126
        elif 'BASIC' in bearer or 'Basic' in bearer:
            auth_header = "Authorization: Basic %s" %(self.v2_auth_token)
            self.v2_auth_header = auth_header
        return auth_header

    def get_v2_login_token(self, username, password):
        """Get a login token from username and password"""
        if not (username and password):
            return ""
        try:
            self.v2_auth_token = \
                base64.b64encode("%s:%s" % (username, password))
        except (KeyError, AttributeError, TypeError, ValueError, NameError):
            self.v2_auth_token = ""
        return self.v2_auth_token

    def set_v2_login_token(self, v2_auth_token):
        """Load previously created login token"""
        self.v2_auth_token = v2_auth_token

    def is_v2(self):
        """Check if registry is of type v2"""
        (hdr, dummy) = self._get_url(self.registry_url + "/v2/")
        try:
            if ("200" in hdr.data["X-ND-HTTPSTATUS"] or
                    "401" in hdr.data["X-ND-HTTPSTATUS"]):
                return True
        except (KeyError, AttributeError, TypeError):
            pass
        return False

    def get_v2_image_manifest(self, imagerepo, tag):
        """Get the image manifest which contains JSON metadata
        that is common to all layers in this image tag
        """
        if self._is_docker_registry() and "/" not in imagerepo:
            url = self.registry_url + "/v2/library/" + \
                imagerepo + "/manifests/" + tag
        else:
            url = self.registry_url + "/v2/" + imagerepo + \
                "/manifests/" + tag
        Msg().err("manifest url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v2_image_layer(self, imagerepo, layer_id):
        """Get one image layer data file (tarball)"""
        if self._is_docker_registry() and "/" not in imagerepo:
            url = self.registry_url + "/v2/library/" + \
                imagerepo + "/blobs/" + layer_id
        else:
            url = self.registry_url + "/v2/" + imagerepo + \
                "/blobs/" + layer_id
        Msg().err("layer url:", url, l=Msg.DBG)
        filename = self.localrepo.layersdir + "/" + layer_id
        if self._get_file(url, filename, 3):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v2_layers_all(self, imagerepo, fslayers):
        """Get all layer data files belonging to a image tag"""
        files = []
        if fslayers:
            for layer in reversed(fslayers):
                Msg().err("Downloading layer:", layer["blobSum"], l=Msg.INF)
                if not self.get_v2_image_layer(imagerepo, layer["blobSum"]):
                    return []
                files.append(layer["blobSum"])
        return files

    def get_v2(self, imagerepo, tag):
        """Pull container with v2 API"""
        files = []
        (dummy, manifest) = self.get_v2_image_manifest(imagerepo, tag)
        try:
            if not (self.localrepo.setup_tag(tag) and
                    self.localrepo.set_version("v2")):
                Msg().err("Error: setting localrepo v2 tag and version")
                return []
            self.localrepo.save_json("manifest", manifest)
            Msg().err("v2 layers: %s" % (imagerepo), l=Msg.DBG)
            files = self.get_v2_layers_all(imagerepo,
                                           manifest["fsLayers"])
        except (KeyError, AttributeError, IndexError, ValueError, TypeError):
            pass
        return files

    def _get_v1_id_from_tags(self, tags_obj, tag):
        """Get image id from array of tags"""
        if isinstance(tags_obj, dict):
            try:
                return tags_obj[tag]
            except KeyError:
                pass
        elif isinstance(tags_obj, []):
            try:
                for tag_dict in tags_obj:
                    if tag_dict["name"] == tag:
                        return tag_dict["layer"]
            except KeyError:
                pass
        return ""

    def _get_v1_id_from_images(self, images_array, short_id):
        """Get long image id from array of images using the short id"""
        try:
            for image_dict in images_array:
                if image_dict["id"][0:8] == short_id:
                    return image_dict["id"]
        except KeyError:
            pass
        return ""

    def get_v1(self, imagerepo, tag):
        """Pull container with v1 API"""
        Msg().err("v1 image id: %s" % (imagerepo), l=Msg.DBG)
        (hdr, images_array) = self.get_v1_repo(imagerepo)
        if not images_array:
            Msg().err("Error: image not found")
            return []
        try:
            endpoint = "http://" + hdr["x-docker-endpoints"]
        except KeyError:
            endpoint = self.index_url
        (dummy, tags_array) = self.get_v1_image_tags(endpoint, imagerepo)
        image_id = self._get_v1_id_from_tags(tags_array, tag)
        if not image_id:
            Msg().err("Error: image tag not found")
            return []
        if len(image_id) <= 8:
            image_id = self._get_v1_id_from_images(images_array, image_id)
            if not image_id:
                Msg().err("Error: image id not found")
                return []
        if not (self.localrepo.setup_tag(tag) and
                self.localrepo.set_version("v1")):
            Msg().err("Error: setting localrepo v1 tag and version")
            return []
        Msg().err("v1 ancestry: %s" % image_id, l=Msg.DBG)
        (dummy, ancestry) = self.get_v1_image_ancestry(endpoint, image_id)
        if not ancestry:
            Msg().err("Error: ancestry not found")
            return []
        self.localrepo.save_json("ancestry", ancestry)
        Msg().err("v1 layers: %s" % image_id, l=Msg.DBG)
        files = self.get_v1_layers_all(endpoint, ancestry)
        return files

    def _parse_imagerepo(self, imagerepo):
        """Parse imagerepo to extract registry"""
        remoterepo = imagerepo
        registry = ""
        registry_url = ""
        index_url = ""
        components = imagerepo.split("/")
        if '.' in components[0] and len(components) >= 2:
            registry = components[0]
            if components[1] == "library":
                remoterepo = "/".join(components[2:])
                del components[1]
                imagerepo = "/".join(components)
            else:
                remoterepo = "/".join(components[1:])
        else:
            if components[0] == "library" and len(components) >= 1:
                del components[0]
                remoterepo = "/".join(components)
                imagerepo = "/".join(components)
        if registry:
            try:
                registry_url = self.conf['docker_registries'][registry][0]
                index_url = self.conf['docker_registries'][registry][1]
            except (KeyError, NameError, TypeError):
                registry_url = "https://%s" % registry
                index_url = registry_url
            if registry_url:
                self.registry_url = registry_url
            if index_url:
                self.index_url = index_url
        return (imagerepo, remoterepo)

    def get(self, imagerepo, tag):
        """Pull a docker image from a v2 registry or v1 index"""
        Msg().err("get imagerepo: %s tag: %s" % (imagerepo, tag), l=Msg.DBG)
        (imagerepo, remoterepo) = self._parse_imagerepo(imagerepo)
        if self.localrepo.cd_imagerepo(imagerepo, tag):
            new_repo = False
        else:
            self.localrepo.setup_imagerepo(imagerepo)
            new_repo = True
        if self.is_v2():
            files = self.get_v2(remoterepo, tag)  # try v2
        else:
            files = self.get_v1(remoterepo, tag)  # try v1
        if new_repo and not files:
            self.localrepo.del_imagerepo(imagerepo, tag, False)
        return files

    def search_init(self, pause):
        """Setup new search"""
        self.search_pause = pause
        self.search_page = 0
        self.search_link = ""
        self.search_ended = False

    def search_get_page_v1(self, expression):
        """Get search results from Docker Hub using v1 API"""
        if expression:
            url = self.index_url + "/v1/search?q=" + expression
        else:
            url = self.index_url + "/v1/search?"
        url += "&page=" + str(self.search_page)
        (dummy, buf) = self._get_url(url)
        try:
            repo_list = json.loads(buf.getvalue())
            if repo_list["page"] == repo_list["num_pages"]:
                self.search_ended = True
            return repo_list
        except (IOError, OSError, AttributeError,
                ValueError, TypeError):
            self.search_ended = True
            return []

    def catalog_get_page_v2(self, lines):
        """Get search results from Docker Hub using v2 API"""
        url = self.registry_url + "/v2/_catalog"
        if self.search_pause:
            if self.search_page == 1:
                url += "?n=" + str(lines)
            else:
                url = self.registry_url + self.search_link
        (hdr, buf) = self._get_url(url)
        try:
            match = re.search(r"\<([^>]+)\>", hdr.data["link"])
            if match:
                self.search_link = match.group(1)
        except (AttributeError, NameError, KeyError):
            self.search_ended = True
        try:
            return json.loads(buf.getvalue())
        except (IOError, OSError, AttributeError,
                ValueError, TypeError):
            self.search_ended = True
            return []

    def search_get_page(self, expression):
        """Get search results from Docker Hub"""
        if self.search_ended:
            return []
        else:
            self.search_page += 1
        if self.is_v2() and not self._is_docker_registry():
            return self.catalog_get_page_v2(self.search_lines)
        return self.search_get_page_v1(expression)


class DockerLocalFileAPI(object):
    """Manipulate container and/or image files produced by Docker"""

    def __init__(self, localrepo, conf):
        self.conf = conf
        self.localrepo = localrepo

    def _load_structure(self, tmp_imagedir):
        """Load the structure of a Docker pulled image"""
        structure = dict()
        structure["layers"] = dict()
        if FileUtil(self.conf, tmp_imagedir).isdir():
            for fname in os.listdir(tmp_imagedir):
                f_path = tmp_imagedir + "/" + fname
                if fname == "repositories":
                    structure["repositories"] = (
                        self.localrepo.load_json(f_path))
                elif fname == "manifest.json":
                    pass
                elif len(fname) == 69 and fname.endswith(".json"):
                    pass
                elif len(fname) == 64 and FileUtil(self.conf, f_path).isdir():
                    layer_id = fname
                    structure["layers"][layer_id] = dict()
                    for layer_f in os.listdir(f_path):
                        layer_f_path = f_path + "/" + layer_f
                        if layer_f == "VERSION":
                            structure["layers"][layer_id]["VERSION"] = \
                                self.localrepo.load_json(layer_f_path)
                        elif layer_f == "json":
                            structure["layers"][layer_id]["json"] = \
                                self.localrepo.load_json(layer_f_path)
                            structure["layers"][layer_id]["json_f"] = (
                                layer_f_path)
                        elif "layer" in layer_f:
                            structure["layers"][layer_id]["layer_f"] = (
                                layer_f_path)
                        else:
                            Msg().err("Warning: unkwnon file in layer:",
                                      f_path, l=Msg.WAR)
                else:
                    Msg().err("Warning: unkwnon file in image:", f_path,
                              l=Msg.WAR)
        return structure

    def _copy_layer_to_repo(self, filepath, layer_id):
        """Move an image layer file to a repository (mv or cp)"""
        if filepath.endswith("json"):
            target_file = self.localrepo.layersdir + "/" + layer_id + ".json"
        elif filepath.endswith("layer.tar"):
            target_file = self.localrepo.layersdir + "/" + layer_id + ".layer"
        else:
            return False
        try:
            os.rename(filepath, target_file)
        except(IOError, OSError):
            if not FileUtil(self.conf, filepath).copyto(target_file):
                return False
        self.localrepo.add_image_layer(target_file)
        return True

    def _load_image(self, structure, imagerepo, tag):
        """Load a container image into a repository mimic docker load"""
        if self.localrepo.cd_imagerepo(imagerepo, tag):
            Msg().err("Error: repository and tag already exist",
                      imagerepo, tag)
            return []
        else:
            self.localrepo.setup_imagerepo(imagerepo)
            tag_dir = self.localrepo.setup_tag(tag)
            if not tag_dir:
                Msg().err("Error: setting up repository", imagerepo, tag)
                return []

            if not self.localrepo.set_version("v1"):
                Msg().err("Error: setting repository version")
                return []

            try:
                top_layer_id = structure["repositories"][imagerepo][tag]
            except (IndexError, NameError, KeyError):
                top_layer_id = self.localrepo.find_top_layer_id(structure)

            sort_lay = self.localrepo.sorted_layers(structure, top_layer_id)
            for layer_id in sort_lay:
                if str(structure["layers"][layer_id]["VERSION"]) != "1.0":
                    Msg().err("Error: layer version unknown")
                    return []

                for layer_item in ("json_f", "layer_f"):
                    filename = str(structure["layers"][layer_id][layer_item])
                    if not self._copy_layer_to_repo(filename, layer_id):
                        Msg().err("Error: copying %s file %s"
                                  % (layer_item[:-2], filename))
                        return []

            self.localrepo.save_json("ancestry", sort_lay)
            return [imagerepo + ":" + tag]

    def _load_repositories(self, structure):
        """Load other image repositories into this local repo"""
        if "repositories" not in structure:
            return False
        loaded_repositories = []
        for imagerepo in structure["repositories"]:
            for tag in structure["repositories"][imagerepo]:
                if imagerepo and tag:
                    if self._load_image(structure,
                                        imagerepo, tag):
                        loaded_repositories.append(imagerepo + ":" + tag)
        return loaded_repositories

    def _untar_saved_container(self, tarfile, destdir):
        """Untar container created with docker save"""
        cmd = "umask 022 ; tar -C " + \
            destdir + " -x --delay-directory-restore "
        if Msg.level >= Msg.VER:
            cmd += " -v "
        cmd += " --one-file-system --no-same-owner "
        cmd += " --no-same-permissions --overwrite -f " + tarfile
        status = subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                                 close_fds=True)
        return not status

    def load(self, imagefile):
        """Load a Docker file created with docker save, mimic Docker
        load. The file is a tarball containing several layers, each
        layer has metadata and data content (directory tree) stored
        as a tar file.
        """
        if not os.path.exists(imagefile) and imagefile != "-":
            Msg().err("Error: image file does not exist:", imagefile)
            return False
        tmp_imagedir = FileUtil(self.conf, "import").mktmp()
        try:
            os.makedirs(tmp_imagedir)
        except (IOError, OSError):
            return False
        if not self._untar_saved_container(imagefile, tmp_imagedir):
            Msg().err("Error: failed to extract container:", imagefile)
            FileUtil(self.conf, tmp_imagedir).remove()
            return False
        structure = self._load_structure(tmp_imagedir)
        if not structure:
            Msg().err("Error: failed to load image structure", imagefile)
            FileUtil(self.conf, tmp_imagedir).remove()
            return False
        else:
            if "repositories" in structure and structure["repositories"]:
                repositories = self._load_repositories(structure)
            else:
                imagerepo = Unique().imagename()
                tag = "latest"
                repositories = self._load_image(structure, imagerepo, tag)
            FileUtil(self.conf, tmp_imagedir).remove()
            return repositories

    def create_container_meta(self, layer_id, comment="created by udocker"):
        """Create metadata for a given container layer, used in import.
        A file for import is a tarball of a directory tree, does not contain
        metadata. This method creates minimal metadata.
        """
        cont_json = dict()
        cont_json["id"] = layer_id
        cont_json["comment"] = comment
        cont_json["created"] = time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")
        cont_json["architecture"] = self.conf['arch']
        cont_json["os"] = self.conf['osversion']
        layer_file = self.localrepo.layersdir + "/" + layer_id + ".layer"
        cont_json["size"] = FileUtil(self.conf, layer_file).size()
        if cont_json["size"] == -1:
            cont_json["size"] = 0
        cont_json["container_config"] = {
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
        cont_json["config"] = {
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
        return cont_json

    def import_toimage(self, tarfile, imagerepo, tag, move_tarball=True):
        """Import a tar file containing a simple directory tree possibly
        created with Docker export and create local image"""
        if not os.path.exists(tarfile) and tarfile != "-":
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
        layer_file = self.localrepo.layersdir + "/" + layer_id + ".layer"
        json_file = self.localrepo.layersdir + "/" + layer_id + ".json"
        if move_tarball:
            try:
                os.rename(tarfile, layer_file)
            except(IOError, OSError):
                pass
        if not os.path.exists(layer_file):
            if not FileUtil(self.conf, tarfile).copyto(layer_file):
                Msg().err("Error: in move/copy file", tarfile)
                return False
        self.localrepo.add_image_layer(layer_file)
        self.localrepo.save_json("ancestry", [layer_id])
        container_json = self.create_container_meta(layer_id)
        self.localrepo.save_json(json_file, container_json)
        self.localrepo.add_image_layer(json_file)
        Msg().out("Info: added layer", layer_id, l=Msg.INF)
        return layer_id

    def import_tocontainer(self, tarfile, imagerepo, tag, cont_name):
        """Import a tar file containing a simple directory tree possibly
        created with Docker export and create local container ready to use"""
        if not imagerepo:
            imagerepo = "IMPORTED"
            tag = "latest"
        if not os.path.exists(tarfile) and tarfile != "-":
            Msg().err("Error: tar file does not exist:", tarfile)
            return False
        if cont_name:
            if self.localrepo.get_container_id(cont_name):
                Msg().err("Error: container name already exists:",
                          cont_name)
                return False
        layer_id = Unique().layer_v1()
        cont_json = self.create_container_meta(layer_id)
        cont_str = ContainerStructure(self.localrepo, self.conf)
        cont_id = cont_str.create_fromlayer(imagerepo, tag, tarfile, cont_json)
        if cont_name:
            self.localrepo.set_container_name(cont_id, cont_name)
        return cont_id

    def import_clone(self, tarfile, cont_name):
        """Import a tar file containing a clone of a udocker container
        created with export --clone and create local cloned container
        ready to use
        """
        if not os.path.exists(tarfile) and tarfile != "-":
            Msg().err("Error: tar file does not exist:", tarfile)
            return False
        if cont_name:
            if self.localrepo.get_container_id(cont_name):
                Msg().err("Error: container name already exists:",
                          cont_name)
                return False

        cstruct = ContainerStructure(self.localrepo, self.conf)
        cont_id = cstruct.clone_fromfile(tarfile)
        if cont_name:
            self.localrepo.set_container_name(cont_id, cont_name)

        return cont_id

    def clone_container(self, cont_id, cont_name):
        """Clone/duplicate an existing container creating a complete
        copy including metadata, control files, and rootfs, The copy
        will have a new id.
        """
        if cont_name:
            if self.localrepo.get_container_id(cont_name):
                Msg().err("Error: container name already exists:",
                          cont_name)
                return False

        cont_str = ContainerStructure(self.localrepo, self.conf, cont_id)
        dest_cont_id = cont_str.clone()
        if cont_name:
            self.localrepo.set_container_name(dest_cont_id,
                                              cont_name)

        exec_mode = ExecutionMode(self.conf, self.localrepo,
                                  dest_cont_id)
        xmode = exec_mode.get_mode()
        if xmode.startswith("F"):
            exec_mode.set_mode(xmode, True)

        return dest_cont_id
