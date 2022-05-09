# -*- coding: utf-8 -*-
"""Docker API integration"""

import os
import sys
import re
import base64
import json

from udocker.config import Config
from udocker.msg import Msg
from udocker.commonlocalfile import CommonLocalFileApi
from udocker.utils.fileutil import FileUtil
from udocker.utils.curl import GetURL
from udocker.utils.chksum import ChkSUM
from udocker.helper.unique import Unique


class DockerIoAPI(object):
    """Class to encapsulate the access to the Docker Hub service
    Allows to search and download images from Docker Hub
    """

    def __init__(self, localrepo):
        self.index_url = Config.conf['dockerio_index_url']
        self.registry_url = Config.conf['dockerio_registry_url']
        self.v1_auth_header = ""
        self.v2_auth_header = ""
        self.v2_auth_token = ""
        self.localrepo = localrepo
        self.curl = GetURL()
        self.search_pause = True
        self.search_page = 0
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
        return False

    def _get_url(self, *args, **kwargs):
        """Encapsulates the call to GetURL.get() so that authentication
        for v1 and v2 repositories can be treated differently.
        Example:
             _get_url(url, ctimeout=5, timeout=5, header=[]):
        """
        url = str(args[0])
        if "RETRY" not in kwargs:
            kwargs["RETRY"] = 3
        if "FOLLOW" not in kwargs:
            kwargs["FOLLOW"] = 3
        kwargs["RETRY"] -= 1
        (hdr, buf) = self.curl.get(*args, **kwargs)
        Msg().out(f"Info: header: {hdr.data}", l=Msg.DBG)
        Msg().out(f"Info: buffer: {buf.getvalue()}", l=Msg.DBG)
        status_code = self.curl.get_status_code(hdr.data["X-ND-HTTPSTATUS"])
        if status_code == 200:
            return (hdr, buf)
        if not kwargs["RETRY"]:
            hdr.data["X-ND-CURLSTATUS"] = 13  # Permission denied
            return (hdr, buf)
        auth_kwargs = kwargs.copy()
        if "location" not in hdr.data:
            kwargs["FOLLOW"] = 3
        if "location" in hdr.data and hdr.data['location']:
            if not kwargs["FOLLOW"]:
                hdr.data["X-ND-CURLSTATUS"] = 13
                return (hdr, buf)
            kwargs["FOLLOW"] -= 1
            args = [hdr.data['location']]
            if "header" in auth_kwargs:
                del auth_kwargs["header"]
        elif status_code == 401:
            if "www-authenticate" in hdr.data:
                www_authenticate = hdr.data["www-authenticate"]
                if not "realm" in www_authenticate:
                    return (hdr, buf)
                if 'error="insufficient_scope"' in www_authenticate:
                    return (hdr, buf)
                auth_header = ""
                if "/v2/" in url:
                    auth_header = self._get_v2_auth(www_authenticate,
                                                    kwargs["RETRY"])
                if "/v1/" in url:
                    auth_header = self._get_v1_auth(www_authenticate)
                auth_kwargs.update({"header": [auth_header]})
        (hdr, buf) = self._get_url(*args, **auth_kwargs)
        return (hdr, buf)

    def _get_file(self, url, filename, cache_mode):
        """Get a file and check its size. Optionally enable other
        capabilities such as caching to check if the
        file already exists locally and whether its size is the
        same to avoid downloaded it again.
        """
        match = re.search("/([^/:]+):(\\S+)$", filename)
        if match:
            layer_f_chksum = ChkSUM().hash(filename, match.group(1))
            if layer_f_chksum == match.group(2):
                return True             # is cached skip download
            cache_mode = 0
        if self.curl.cache_support and cache_mode:
            if cache_mode == 1:
                (hdr, dummy) = self._get_url(url, nobody=1)
            elif cache_mode == 3:
                (hdr, dummy) = self._get_url(url, sizeonly=True)
            remote_size = self.curl.get_content_length(hdr)
            if remote_size == FileUtil(filename).size():
                return True             # is cached skip download
        else:
            remote_size = -1
        resume = False
        if filename.endswith("layer"):
            resume = True
        (hdr, dummy) = self._get_url(url, ofile=filename, resume=resume)
        if self.curl.get_status_code(hdr.data["X-ND-HTTPSTATUS"]) != 200:
            return False
        if remote_size == -1:
            remote_size = self.curl.get_content_length(hdr)
        if (remote_size != FileUtil(filename).size() and
                hdr.data["X-ND-CURLSTATUS"]):
            Msg().err("Error: file size mismatch:", filename,
                      remote_size, FileUtil(filename).size())
            return False
        return True

    def _split_fields(self, buf):
        """Split  fields, used in the web authentication"""
        all_fields = {}
        for field in buf.split(','):
            pair = field.split('=', 1)
            if len(pair) == 2:
                all_fields[pair[0]] = pair[1].strip('"')
        return all_fields

    def is_v1(self):
        """Check if registry is of type v1"""
        for prefix in ("/v1", "/v1/_ping"):
            (hdr, dummy) = self._get_url(self.index_url + prefix)
            try:
                if ("200" in hdr.data["X-ND-HTTPSTATUS"] or
                        "401" in hdr.data["X-ND-HTTPSTATUS"]):
                    return True
            except (KeyError, AttributeError, TypeError):
                pass
        return False

    def has_search_v1(self, url=None):
        """Check if registry has search capabilities in v1"""
        if url is None:
            url = self.index_url
        (hdr, dummy) = self._get_url(url + "/v1/search")
        try:
            if ("200" in hdr.data["X-ND-HTTPSTATUS"] or
                    "401" in hdr.data["X-ND-HTTPSTATUS"]):
                return True
        except (KeyError, AttributeError, TypeError):
            pass
        return False

    def get_v1_repo(self, imagerepo):
        """Get list of images in a repo from Docker Hub"""
        url = self.index_url + "/v1/repositories/" + imagerepo + "/images"
        Msg().out("Info: repo url", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url, header=["X-Docker-Token: true"])
        try:
            self.v1_auth_header = "Authorization: Token " + \
                hdr.data["x-docker-token"]
            return hdr.data, json.loads(buf.getvalue())
        except (IOError, OSError, AttributeError,
                ValueError, TypeError, KeyError):
            self.v1_auth_header = ""
            return hdr.data, []

    def _get_v1_auth(self, www_authenticate):
        """Authentication for v1 API"""
        if "Token" in www_authenticate:
            return self.v1_auth_header
        return ""

    def get_v1_image_tags(self, imagerepo, tags_only=False):
        """Get list of tags in a repo from Docker Hub"""
        (hdr_data, dummy) = self.get_v1_repo(imagerepo)
        try:
            endpoint = "http://" + hdr_data["x-docker-endpoints"]
        except KeyError:
            endpoint = self.index_url
        url = endpoint + "/v1/repositories/" + imagerepo + "/tags"
        Msg().out("Info: tags url", url, l=Msg.DBG)
        (dummy, buf) = self._get_url(url)
        tags = []
        try:
            if tags_only:
                for tag in json.loads(buf.getvalue()):
                    tags.append(tag["name"])
                return tags

            return json.loads(buf.getvalue())
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return []

    def get_v1_image_tag(self, endpoint, imagerepo, tag):
        """Get list of tags in a repo from Docker Hub"""
        url = endpoint + "/v1/repositories/" + imagerepo + "/tags/" + tag
        Msg().out("Info: tags url", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return (hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return (hdr.data, [])

    def get_v1_image_ancestry(self, endpoint, image_id):
        """Get the ancestry which is an ordered list of layers"""
        url = endpoint + "/v1/images/" + image_id + "/ancestry"
        Msg().out("Info: ancestry url", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return (hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return (hdr.data, [])

    def get_v1_image_json(self, endpoint, layer_id):
        """Get the JSON metadata for a specific layer"""
        url = endpoint + "/v1/images/" + layer_id + "/json"
        Msg().out("Info: json url", url, l=Msg.DBG)
        filename = self.localrepo.layersdir + '/' + layer_id + ".json"
        if self._get_file(url, filename, 0):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v1_image_layer(self, endpoint, layer_id):
        """Get a specific layer data file (layer files are tarballs)"""
        url = endpoint + "/v1/images/" + layer_id + "/layer"
        Msg().out("Info: layer url", url, l=Msg.DBG)
        filename = self.localrepo.layersdir + '/' + layer_id + ".layer"
        if self._get_file(url, filename, 3):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v1_layers_all(self, endpoint, layer_list):
        """Using a layer list download data and metadata files"""
        files = []
        if layer_list:
            for layer_id in reversed(layer_list):
                Msg().out("Info: downloading layer", layer_id, l=Msg.INF)
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
        (bearer, auth_data) = www_authenticate.rsplit(' ', 1)
        if bearer == "Bearer":
            auth_fields = self._split_fields(auth_data)
            if "realm" in auth_fields:
                auth_url = auth_fields["realm"] + '?'
                for (field, value) in auth_fields.items():
                    if field != "realm":
                        auth_url += field + '=' + value + '&'
                header = []
                if self.v2_auth_token:
                    header = [f"Authorization: Basic {self.v2_auth_token}"]
                (dummy, auth_buf) = self._get_url(auth_url, header=header,
                                                  RETRY=retry)
                if sys.version_info[0] >= 3:
                    token_buf = auth_buf.getvalue().decode()
                else:
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
            auth_header = f"Authorization: Basic {self.v2_auth_token}"
            self.v2_auth_header = auth_header
        return auth_header

    def get_v2_login_token(self, username, password):
        """Get a login token from username and password"""
        if not (username and password):
            return ""
        try:
            self.v2_auth_token = \
                base64.b64encode((f"{username}:{password}").encode("utf-8")).decode("ascii")
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

    def has_search_v2(self, url=None):
        """Check if registry has search capabilities in v2"""
        if url is None:
            url = self.registry_url
        (hdr, dummy) = self._get_url(url + "/v2/search/repositories")
        try:
            if ("200" in hdr.data["X-ND-HTTPSTATUS"] or
                    "401" in hdr.data["X-ND-HTTPSTATUS"]):
                return True
        except (KeyError, AttributeError, TypeError):
            pass
        return False

    def get_v2_image_tags(self, imagerepo, tags_only=False):
        """Get list of tags in a repo from Docker Hub"""
        url = self.registry_url + "/v2/" + imagerepo + "/tags/list"
        Msg().out("Info: tags url", url, l=Msg.DBG)
        (dummy, buf) = self._get_url(url)
        tags = []
        try:
            if tags_only:
                for tag in json.loads(buf.getvalue())["tags"]:
                    tags.append(tag)
                return tags

            return json.loads(buf.getvalue())
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return []

    def get_v2_image_manifest(self, imagerepo, tag):
        """Get the image manifest which contains JSON metadata
        that is common to all layers in this image tag
        """
        url = self.registry_url + "/v2/" + imagerepo + \
            "/manifests/" + tag
        Msg().out("Info: manifest url", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return (hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return (hdr.data, [])

    def get_v2_image_layer(self, imagerepo, layer_id):
        """Get one image layer data file (tarball)"""
        url = self.registry_url + "/v2/" + imagerepo + \
            "/blobs/" + layer_id
        Msg().out("Info: layer url", url, l=Msg.DBG)
        filename = self.localrepo.layersdir + '/' + layer_id
        if self._get_file(url, filename, 3):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v2_layers_all(self, imagerepo, fslayers):
        """Get all layer data files belonging to a image tag"""
        files = []
        blob = ""
        if fslayers:
            for layer in reversed(fslayers):
                if "blobSum" in layer:
                    blob = layer["blobSum"]
                elif "digest" in layer:
                    blob = layer["digest"]
                Msg().out("Info: downloading layer", blob, l=Msg.INF)
                if not self.get_v2_image_layer(imagerepo, blob):
                    return []
                files.append(blob)
        return files

    def get_v2(self, imagerepo, tag):
        """Pull container with v2 API"""
        files = []
        (hdr_data, manifest) = self.get_v2_image_manifest(imagerepo, tag)
        status = self.curl.get_status_code(hdr_data["X-ND-HTTPSTATUS"])
        if status == 401:
            Msg().err("Error: manifest not found or not authorized")
            return []
        if status != 200:
            Msg().err("Error: pulling manifest:")
            return []
        try:
            if not (self.localrepo.setup_tag(tag) and
                    self.localrepo.set_version("v2")):
                Msg().err("Error: setting localrepo v2 tag and version")
                return []
            self.localrepo.save_json("manifest", manifest)
            Msg().out(f"Info: v2 layers: {imagerepo}", l=Msg.DBG)
            if "fsLayers" in manifest:
                files = self.get_v2_layers_all(imagerepo,
                                               manifest["fsLayers"])
            elif "layers" in manifest:
                if "config" in manifest:
                    manifest["layers"].append(manifest["config"])
                files = self.get_v2_layers_all(imagerepo,
                                               manifest["layers"])
            else:
                Msg().err("Error: layers section missing in manifest")
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
        elif isinstance(tags_obj, list):
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
        Msg().out(f"Info: v1 image id: {imagerepo}", l=Msg.DBG)
        (hdr_data, images_array) = self.get_v1_repo(imagerepo)
        status = self.curl.get_status_code(hdr_data["X-ND-HTTPSTATUS"])
        if status == 401 or not images_array:
            Msg().err("Error: image not found or not authorized")
            return []
        try:
            endpoint = "http://" + hdr_data["x-docker-endpoints"]
        except KeyError:
            endpoint = self.index_url
        (tags_array) = self.get_v1_image_tags(endpoint, imagerepo)
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
        Msg().out("Info: v1 ancestry", image_id, l=Msg.DBG)
        (dummy, ancestry) = self.get_v1_image_ancestry(endpoint, image_id)
        if not ancestry:
            Msg().err("Error: ancestry not found")
            return []
        self.localrepo.save_json("ancestry", ancestry)
        Msg().out("Info: v1 layers", image_id, l=Msg.DBG)
        files = self.get_v1_layers_all(endpoint, ancestry)
        return files

    def _parse_imagerepo(self, imagerepo):
        """Parse imagerepo to extract registry"""
        remoterepo = imagerepo
        registry = ""
        registry_url = ""
        index_url = ""
        components = imagerepo.split('/')
        if '.' in components[0] and len(components) >= 2:
            registry = components[0]
            del components[0]
        elif ('.' not in components[0] and
              components[0] != "library" and len(components) == 1):
            components.insert(0, "library")
        remoterepo = '/'.join(components)
        if registry:
            try:
                registry_url = Config.conf['docker_registries'][registry][0]
                index_url = Config.conf['docker_registries'][registry][1]
            except (KeyError, NameError, TypeError):
                registry_url = registry
                if "://" not in registry:
                    registry_url = f"https://{registry}"
                index_url = registry_url
            if registry_url:
                self.registry_url = registry_url
            if index_url:
                self.index_url = index_url
        return (imagerepo, remoterepo)

    def get(self, imagerepo, tag):
        """Pull a docker image from a v2 registry or v1 index"""
        Msg().out(f"Info: get imagerepo: {imagerepo} tag: {tag}", l=Msg.DBG)
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

    def get_tags(self, imagerepo):
        """List tags from a v2 or v1 repositories"""
        Msg().out("Info: get tags", imagerepo, l=Msg.DBG)
        (dummy, remoterepo) = self._parse_imagerepo(imagerepo)
        if self.is_v2():
            return self.get_v2_image_tags(remoterepo, True)  # try v2
        return self.get_v1_image_tags(remoterepo, True)  # try v1

    def search_init(self, pause):
        """Setup new search"""
        self.search_pause = pause
        self.search_page = 0
        self.search_ended = False

    def search_get_page_v1(self, expression, url):
        """Get search results from Docker Hub using v1 API"""
        if expression:
            url = url + f"/v1/search?q={expression}"
        else:
            url = url + "/v1/search?"
        url += f"&page={str(self.search_page)}"
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

    def search_get_page_v2(self, expression, url, lines=22, official=None):
        """Search results from Docker Hub using v2 API"""
        if not expression:
            expression = '*'
        if expression and official is None:
            url = url + f"/v2/search/repositories?query={expression}"
        elif expression and official is True:
            url = url + f"/v2/search/repositories?query={expression}&is_official=true"
        elif expression and official is False:
            url = url + f"/v2/search/repositories?query={expression}&is_official=false"
        else:
            return []
        url += f"&page_size={str(lines)}"
        if self.search_page != 1:
            url += f"&page={str(self.search_page)}"
        (dummy, buf) = self._get_url(url)
        try:
            repo_list = json.loads(buf.getvalue())
            if repo_list["count"] == self.search_page:
                self.search_ended = True
            return repo_list
        except (IOError, OSError, AttributeError, KeyError,
                ValueError, TypeError):
            self.search_ended = True
            return []

    def search_get_page(self, expression, lines=22):
        """Get search results from Docker Hub"""
        if self.search_ended:
            return []
        self.search_page += 1
        if self.has_search_v2(self.index_url):
            return self.search_get_page_v2(expression, self.index_url, lines)
        if self.has_search_v1():
            return self.search_get_page_v1(expression, self.index_url)
        if self.has_search_v2(self.registry_url):
            return self.search_get_page_v2(expression, self.registry_url, lines)
        if self.has_search_v1(self.registry_url):
            return self.search_get_page_v1(expression, self.registry_url)
        return []


class DockerLocalFileAPI(CommonLocalFileApi):
    """Manipulate Docker container and/or image files"""

    def __init__(self, localrepo):
        CommonLocalFileApi.__init__(self, localrepo)

    def _load_structure(self, tmp_imagedir):
        """Load the structure of a Docker image"""
        structure = {}
        structure["repolayers"] = {}
        structure["repoconfigs"] = {}
        for fname in os.listdir(tmp_imagedir):
            f_path = tmp_imagedir + '/' + fname
            if fname == "repositories":
                structure["repositories"] = \
                        self.localrepo.load_json(f_path)
            elif fname == "manifest.json":
                structure["manifest"] = \
                        self.localrepo.load_json(f_path)
            elif len(fname) >= 69 and fname.endswith(".json"):
                structure["repoconfigs"][fname] = {}
                structure["repoconfigs"][fname]["json"] = \
                        self.localrepo.load_json(f_path)
                structure["repoconfigs"][fname]["json_f"] = \
                        f_path
            elif len(fname) >= 64 and FileUtil(f_path).isdir():
                layer_id = fname
                structure["repolayers"][layer_id] = {}
                for layer_f in os.listdir(f_path):
                    layer_f_path = f_path + '/' + layer_f
                    if layer_f == "VERSION":
                        structure["repolayers"][layer_id]["VERSION"] = \
                                self.localrepo.load_json(layer_f_path)
                    elif layer_f == "json":
                        structure["repolayers"][layer_id]["json"] = \
                                self.localrepo.load_json(layer_f_path)
                        structure["repolayers"][layer_id]["json_f"] = \
                                layer_f_path
                    elif "layer" in layer_f:
                        structure["repolayers"][layer_id]["layer_f"] = \
                                layer_f_path
                    else:
                        Msg().out("Info: warning: unkwnon file in layer:",
                                  f_path, l=Msg.WAR)
        return structure

    def _find_top_layer_id(self, structure, my_layer_id=""):
        """Find the top layer within a Docker image"""
        if "repolayers" not in structure:
            return ""

        if not my_layer_id:
            # if Python 3 TypeError: 'dict_keys' object is not subscriptable
            if sys.version_info[0] >= 3:
                my_layer_id = list(structure["repolayers"].keys())[0]
            else:
                my_layer_id = structure["repolayers"].keys()[0]

        found = ""
        for layer_id in structure["repolayers"]:
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
        """Return the layers sorted"""
        sorted_layers = []
        next_layer = top_layer_id
        while next_layer:
            sorted_layers.append(next_layer)
            if "parent" not in structure["repolayers"][next_layer]["json"]:
                break

            next_layer = structure["repolayers"][next_layer]["json"]["parent"]
            if not next_layer:
                break

        return sorted_layers

    def _get_from_manifest(self, structure, imagetag):
        """Search for image:tag in manifest and return Config and layer ids"""
        if "manifest" in structure:
            for repotag in structure["manifest"]:
                if imagetag in repotag["RepoTags"]:
                    layers = []
                    for layer_file in repotag["Layers"]:
                        #layers.append(layer_file.replace("/layer.tar", ""))
                        layers.append(layer_file)
                    layers.reverse()
                    return (repotag["Config"], layers)
        return ("", [])

    def _load_image_step2(self, structure, imagerepo, tag):
        """Load a container image into a repository mimic docker load"""
        imagetag = imagerepo + ':' + tag
        (json_config_file, layers) = \
                self._get_from_manifest(structure, imagetag)
        if json_config_file:
            layer_id = json_config_file.replace(".json", "")
            json_file = structure["repoconfigs"][json_config_file]["json_f"]
            self._move_layer_to_v1repo(json_file, layer_id, "container.json")
        top_layer_id = self._find_top_layer_id(structure)
        layers = self._sorted_layers(structure, top_layer_id)
        for layer_id in layers:
            Msg().out("Info: adding layer:", layer_id, l=Msg.INF)
            if str(structure["repolayers"][layer_id]["VERSION"]) != "1.0":
                Msg().err("Error: layer version unknown")
                return []
            for layer_item in ("json_f", "layer_f"):
                filename = str(structure["repolayers"][layer_id][layer_item])
                if not self._move_layer_to_v1repo(filename, layer_id):
                    Msg().err(f"Error: copying {layer_item[:-2]} file {filename}", l=Msg.VER)
                    return []
        self.localrepo.save_json("ancestry", layers)
        if self._imagerepo:
            imagetag = self._imagerepo + ':' + tag
        return [imagetag]

    def _load_repositories(self, structure):
        """Load other image repositories into this local repo"""
        if "repositories" not in structure:
            return False
        loaded_repositories = []
        for imagerepo in structure["repositories"]:
            for tag in structure["repositories"][imagerepo]:
                if imagerepo and tag:
                    loaded_repo = self._load_image(structure, imagerepo, tag)
                    if loaded_repo:
                        loaded_repositories.extend(loaded_repo)
        return loaded_repositories

    def load(self, tmp_imagedir, imagerepo=None):
        """Load a Docker file created with docker save, mimic Docker
        load. The file is a tarball containing several layers, each
        layer has metadata and data content (directory tree) stored
        as a tar file.
        """
        self._imagerepo = imagerepo
        structure = self._load_structure(tmp_imagedir)
        if not structure:
            Msg().err("Error: failed to load image structure")
            return []
        if "repositories" in structure and structure["repositories"]:
            repositories = self._load_repositories(structure)
        else:
            if not imagerepo:
                imagerepo = Unique().imagename()
            tag = Unique().imagetag()
            repositories = self._load_image(structure, imagerepo, tag)
        return repositories

    def _save_image(self, imagerepo, tag, structure, tmp_imagedir):
        """Prepare structure with metadata for the image"""
        self.localrepo.cd_imagerepo(imagerepo, tag)
        (container_json, layer_files) = self.localrepo.get_image_attributes()
        json_file = tmp_imagedir + "/container.json"
        if (not container_json) or \
           (not self.localrepo.save_json(json_file, container_json)):
            return False
        config_layer_file = str(ChkSUM().sha256(json_file)) + ".json"
        FileUtil(json_file).rename(tmp_imagedir + '/' + config_layer_file)
        manifest_item = {}
        manifest_item["Config"] = config_layer_file
        manifest_item["RepoTags"] = [imagerepo + ':' + tag, ]
        manifest_item["Layers"] = []
        if imagerepo not in structure["repositories"]:
            structure["repositories"][imagerepo] = {}
        parent_layer_id = ""
        for layer_f in layer_files:
            try:
                layer_id = re.search(r"^(?:[^:]+:)?([a-z0-9]+)(?:\.layer)?$",
                                     os.path.basename(layer_f)).group(1)
            except AttributeError:
                return False
            if os.path.exists(tmp_imagedir + "/" + layer_id):
                continue
            FileUtil(tmp_imagedir + "/" + layer_id).mkdir()
            if not FileUtil(layer_f).copyto(tmp_imagedir + "/"
                                            + layer_id + "/layer.tar"):
                return False
            manifest_item["Layers"].append(layer_id + "/layer.tar")
            json_string = self.create_container_meta(layer_id)
            if parent_layer_id:
                json_string["parent"] = parent_layer_id
            else:
                structure["repositories"][imagerepo][tag] = layer_id
            parent_layer_id = layer_id
            if not self.localrepo.save_json(tmp_imagedir + "/"
                                            + layer_id + "/json", json_string):
                return False
            if not FileUtil(tmp_imagedir + "/" +
                            layer_id + "/VERSION").putdata("1.0", 'w'):
                return False
        structure["manifest"].append(manifest_item)
        return True

    def save(self, imagetag_list, imagefile):
        """Save a set of image tags to a file similarly to docker save
        """
        tmp_imagedir = FileUtil("save").mktmp()
        try:
            os.makedirs(tmp_imagedir)
        except (IOError, OSError):
            return False
        structure = {}
        structure["manifest"] = []
        structure["repositories"] = {}
        status = False
        for (imagerepo, tag) in imagetag_list:
            status = self._save_image(imagerepo, tag, structure, tmp_imagedir)
            if not status:
                Msg().err("Error: save image failed:", imagerepo + ':' + tag)
                break
        if status:
            self.localrepo.save_json(tmp_imagedir + "/manifest.json",
                                     structure["manifest"])
            self.localrepo.save_json(tmp_imagedir + "/repositories",
                                     structure["repositories"])
            if not FileUtil(tmp_imagedir).tar(imagefile):
                Msg().err("Error: save image failed in writing tar", imagefile)
                status = False
        else:
            Msg().err("Error: no images specified")
        FileUtil(tmp_imagedir).remove(recursive=True)
        return status
