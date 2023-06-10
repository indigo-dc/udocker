# -*- coding: utf-8 -*-
"""Docker API integration"""

import os
import re
import base64
import json

from udocker import LOG
from udocker.config import Config
from udocker.commonlocalfile import CommonLocalFileApi
from udocker.utils.fileutil import FileUtil
from udocker.utils.curl import GetURL
from udocker.utils.chksum import ChkSUM
from udocker.helper.unique import Unique
from udocker.helper.hostinfo import HostInfo

class DockerIoAPIv1:
    """API v1 for Docker Hub"""

    def __init__(self, dockerioapi):
        self.dockerioapi = dockerioapi
        self.v1_auth_header = ""
        self.localrepo = dockerioapi.localrepo
        self.curl = dockerioapi.curl

    def is_valid(self):
        """API v1 Check if registry is of type v1"""
        for prefix in ("/v1", "/v1/_ping"):
            (hdr, dummy) = self.dockerioapi.get_url(self.dockerioapi.index_url + prefix)
            try:
                httpstatus = hdr.data["X-ND-HTTPSTATUS"]
                if ("200" in httpstatus or "401" in httpstatus):
                    return True
            except (KeyError, AttributeError, TypeError):
                pass

        return False

    def is_searchable(self, url=None):
        """API v1 Check if registry has search capabilities"""
        if url is None:
            url = self.dockerioapi.index_url

        (hdr, dummy) = self.dockerioapi.get_url(url + "/v1/search")
        try:
            httpstatus = hdr.data["X-ND-HTTPSTATUS"]
            if ("200" in httpstatus or "401" in httpstatus):
                return True
        except (KeyError, AttributeError, TypeError):
            pass

        return False

    def get_repo(self, imagerepo):
        """API v1 Get list of images in a repo from Docker Hub"""
        url = self.dockerioapi.index_url + "/v1/repositories/" + imagerepo + "/images"
        LOG.debug("repo url: %s", url)
        (hdr, buf) = self.dockerioapi.get_url(url, header=["X-Docker-Token: true"])
        try:
            self.v1_auth_header = "Authorization: Token " + hdr.data["x-docker-token"]
            return hdr.data, json.loads(buf.getvalue().decode())
        except (OSError, AttributeError, ValueError, TypeError, KeyError):
            self.v1_auth_header = ""
            return hdr.data, []

    def get_auth(self, www_authenticate):
        """API v1 Get authentication token"""
        if "Token" in www_authenticate:
            return self.v1_auth_header

        return ""

    def get_image_tags(self, imagerepo, tags_only=False):
        """API v1 Get list of tags in a repo from Docker Hub"""
        (hdr_data, dummy) = self.get_repo(imagerepo)
        try:
            endpoint = "http://" + hdr_data["x-docker-endpoints"]
        except KeyError:
            endpoint = self.dockerioapi.index_url

        url = endpoint + "/v1/repositories/" + imagerepo + "/tags"
        LOG.debug("tags url: %s", url)
        (dummy, buf) = self.dockerioapi.get_url(url)
        tags = []
        try:
            if tags_only:
                for tag in json.loads(buf.getvalue().decode()):
                    tags.append(tag["name"])
                return tags

            return json.loads(buf.getvalue().decode())
        except (OSError, AttributeError, ValueError, TypeError):
            return []

    def get_image_tag(self, endpoint, imagerepo, tag):
        """API v1 Get list of tags in a repo from Docker Hub"""
        url = endpoint + "/v1/repositories/" + imagerepo + "/tags/" + tag
        LOG.debug("tags url: %s", url)
        (hdr, buf) = self.dockerioapi.get_url(url)
        try:
            return (hdr.data, json.loads(buf.getvalue().decode()))
        except (OSError, AttributeError, ValueError, TypeError):
            return (hdr.data, [])

    def get_image_ancestry(self, endpoint, image_id):
        """API v1 Get the ancestry which is an ordered list of layers"""
        url = endpoint + "/v1/images/" + image_id + "/ancestry"
        LOG.debug("ancestry url: %s", url)
        (hdr, buf) = self.dockerioapi.get_url(url)
        try:
            return (hdr.data, json.loads(buf.getvalue().decode()))
        except (OSError, AttributeError, ValueError, TypeError):
            return (hdr.data, [])

    def get_image_json(self, endpoint, layer_id):
        """API v1 Get the JSON metadata for a specific layer"""
        url = endpoint + "/v1/images/" + layer_id + "/json"
        LOG.debug("json url: %s", url)
        filename = self.localrepo.layersdir + '/' + layer_id + ".json"
        if self.dockerioapi.get_file(url, filename, 0):
            self.localrepo.add_image_layer(filename)
            return True

        return False

    def get_image_layer(self, endpoint, layer_id):
        """API v1 Get a specific layer data file (layer files are tarballs)"""
        url = endpoint + "/v1/images/" + layer_id + "/layer"
        LOG.debug("layer url: %s", url)
        filename = self.localrepo.layersdir + '/' + layer_id + ".layer"
        if self.dockerioapi.get_file(url, filename, 3):
            self.localrepo.add_image_layer(filename)
            return True

        return False

    def get_layers_all(self, endpoint, layer_list):
        """API v1 Using a layer list download data and metadata files"""
        files = []
        if layer_list:
            for layer_id in reversed(layer_list):
                LOG.info("downloading layer: %s", layer_id)
                filesize = self.get_image_json(endpoint, layer_id)
                if not filesize:
                    return []

                files.append(layer_id + ".json")
                filesize = self.get_image_layer(endpoint, layer_id)
                if not filesize:
                    return []

                files.append(layer_id + ".layer")

        return files

    def _get_id_from_tags(self, tags_obj, tag):
        """API v1 Get image id from array of tags"""
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

    def _get_id_from_images(self, images_array, short_id):
        """API v1 Get long image id from array of images using the short id"""
        try:
            for image_dict in images_array:
                if image_dict["id"][0:8] == short_id:
                    return image_dict["id"]
        except KeyError:
            pass

        return ""

    def get(self, imagerepo, tag):
        """API v1 Pull container with v1 API"""
        LOG.debug("v1 image id: %s", imagerepo)
        (hdr_data, images_array) = self.get_repo(imagerepo)
        status = self.curl.get_status_code(hdr_data["X-ND-HTTPSTATUS"])
        if status == 401 or not images_array:
            LOG.error("image not found or not authorized")
            return []

        try:
            endpoint = "http://" + hdr_data["x-docker-endpoints"]
        except KeyError:
            endpoint = self.dockerioapi.index_url

        (tags_array) = self.get_image_tags(endpoint, imagerepo)
        image_id = self._get_id_from_tags(tags_array, tag)
        if not image_id:
            LOG.error("image tag not found")
            return []

        if len(image_id) <= 8:
            image_id = self._get_id_from_images(images_array, image_id)
            if not image_id:
                LOG.error("image id not found")
                return []

        if not (self.localrepo.setup_tag(tag) and self.localrepo.set_version("v1")):
            LOG.error("setting localrepo v1 tag and version")
            return []

        LOG.debug("v1 ancestry: %s", image_id)
        (dummy, ancestry) = self.get_image_ancestry(endpoint, image_id)
        if not ancestry:
            LOG.error("ancestry not found")
            return []

        self.localrepo.save_json("ancestry", ancestry)
        LOG.debug("v1 layers: %s", image_id)
        files = self.get_layers_all(endpoint, ancestry)
        return files

    def search_get_page(self, expression, url):
        """API v1 Get search results from Docker Hub using v1 API"""
        if expression:
            url = url + "/v1/search?q=%s" % expression
        else:
            url = url + "/v1/search?"

        url += f'&page={str(self.dockerioapi.search_page)}'
        (dummy, buf) = self.dockerioapi.get_url(url)
        try:
            repo_list = json.loads(buf.getvalue().decode())
            if repo_list["page"] == repo_list["num_pages"]:
                self.dockerioapi.search_ended = True

            LOG.debug(repo_list)
            return repo_list
        except (OSError, AttributeError, ValueError, TypeError):
            self.dockerioapi.search_ended = True
            return []


class DockerIoAPIv2:
    """API v2 for Docker Hub"""

    def __init__(self, dockerioapi):
        self.dockerioapi = dockerioapi
        self.v2_auth_header = ""
        self.v2_auth_token = ""
        self.localrepo = dockerioapi.localrepo
        self.curl = dockerioapi.curl

    def _split_fields(self, buf):
        """API v2 Split  fields, used in the web authentication"""
        all_fields = {}
        for field in buf.split(','):
            pair = field.split('=', 1)
            if len(pair) == 2:
                all_fields[pair[0]] = pair[1].strip('"')

        return all_fields

    def get_auth(self, www_authenticate, retry):
        """API v2 Authentication"""
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
                    header = [f'Authorization: Basic {self.v2_auth_token}']

                (dummy, auth_buf) = self.dockerioapi.get_url(auth_url, header=header,
                                                             RETRY=retry)
                token_buf = auth_buf.getvalue().decode()
                if token_buf and "token" in token_buf:
                    try:
                        auth_token = json.loads(token_buf)
                    except (OSError, AttributeError, ValueError, TypeError):
                        return auth_header

                    auth_header = "Authorization: Bearer " + auth_token["token"]
                    self.v2_auth_header = auth_header
        # PR #126
        elif 'BASIC' in bearer or 'Basic' in bearer:
            auth_header = "Authorization: Basic %s" % self.v2_auth_token
            self.v2_auth_header = auth_header

        return auth_header

    def get_login_token(self, username, password):
        """API v2 Get a login token from username and password"""
        if not (username and password):
            return ""

        try:
            userpass = (f'{username}:{password}').encode("utf-8")
            self.v2_auth_token = base64.b64encode(userpass).decode("ascii")
        except (KeyError, AttributeError, TypeError, ValueError, NameError):
            self.v2_auth_token = ""

        LOG.debug("Auth token is: %s", self.v2_auth_token)
        return self.v2_auth_token

    def set_login_token(self, v2_auth_token):
        """API v2 Load previously created login token"""
        self.v2_auth_token = v2_auth_token

    def is_valid(self):
        """API v2 Check if registry is of type v2"""
        (hdr, dummy) = self.dockerioapi.get_url(self.dockerioapi.registry_url + "/v2/")
        try:
            httpstatus = hdr.data["X-ND-HTTPSTATUS"]
            if ("200" in httpstatus or "401" in httpstatus):
                return True
        except (KeyError, AttributeError, TypeError):
            pass

        return False

    def is_searchable(self, url=None):
        """API v2 Check if registry has search capabilities"""
        if url is None:
            url = self.dockerioapi.registry_url

        (hdr, dummy) = self.dockerioapi.get_url(url + "/v2/search/repositories")
        try:
            httpstatus = hdr.data["X-ND-HTTPSTATUS"]
            if ("200" in httpstatus or "401" in httpstatus):
                return True
        except (KeyError, AttributeError, TypeError):
            pass

        return False

    def get_image_tags(self, imagerepo, tags_only=False):
        """API v2 Get list of tags in a repo from Docker Hub"""
        url = self.dockerioapi.registry_url + "/v2/" + imagerepo + "/tags/list"
        LOG.debug("tags url: %s", url)
        (dummy, buf) = self.dockerioapi.get_url(url)
        tags = []
        try:
            if tags_only:
                for tag in json.loads(buf.getvalue().decode())["tags"]:
                    tags.append(tag)

                return tags

            return json.loads(buf.getvalue().decode())
        except (OSError, AttributeError, ValueError, TypeError):
            return []

    def _get_digest_from_image_index(self, image_index, platform):
        """Get OCI or docker manifest from an image index"""
        if isinstance(image_index, dict):
            index_list = image_index
        else:
            try:
                index_list = json.loads(image_index.decode())
            except (OSError, AttributeError, ValueError, TypeError):
                return ""
        (p_os, p_architecture, p_variant) = HostInfo().parse_platform(platform)
        try:
            for manifest in index_list["manifests"]:
                if (p_os and
                    (manifest["platform"]["os"]).lower() != p_os):
                    continue
                if (p_architecture and
                    (manifest["platform"]["architecture"]).lower() != p_architecture):
                    continue
                if (p_variant and
                    (manifest["platform"]["variant"]).lower() != p_variant):
                    continue
                return manifest["digest"]
        except (KeyError, AttributeError, ValueError, TypeError):
            pass
        return ""

    def get_image_manifest(self, imagerepo, tag, platform=""):
        """API v2 Get the image manifest which contains JSON metadata
        that is common to all layers in this image tag
        """
        reqhdr = ['Accept: application/vnd.docker.distribution.manifest.v2+json',
                  'Accept: application/vnd.docker.distribution.manifest.v1+prettyjws',
                  'Accept: application/json',
                  'Accept: application/vnd.docker.distribution.manifest.list.v2+json',
                  'Accept: application/vnd.oci.image.manifest.v1+json',
                  'Accept: application/vnd.oci.image.index.v1+json', ]
        url = self.dockerioapi.registry_url + "/v2/" + imagerepo + "/manifests/" + tag
        LOG.debug("manifest url: %s", url)
        (hdr, buf) = self.dockerioapi.get_url(url, header=reqhdr)

        try:
            if "docker.distribution.manifest.v1" in hdr.data['content-type']:
                return (hdr.data, json.loads(buf.getvalue().decode()))
            if "docker.distribution.manifest.v2" in hdr.data['content-type']:
                return (hdr.data, json.loads(buf.getvalue().decode()))
            if "oci.image.manifest.v1+json" in hdr.data['content-type']:
                return (hdr.data, json.loads(buf.getvalue().decode()))
            if ("docker.distribution.manifest.list.v2" in hdr.data['content-type'] or
                "oci.image.index.v1+json" in hdr.data['content-type']):
                image_index = json.loads(buf.getvalue().decode())
                if not platform:
                    return (hdr.data, image_index)

                digest = self._get_digest_from_image_index(image_index, platform)
                if not digest:
                    LOG.error("no image found in manifest for platform (%s)",
                              HostInfo().platform_to_str(platform))
                else:
                    return self.get_image_manifest(imagerepo, digest, platform)
        except (OSError, KeyError, AttributeError, ValueError, TypeError):
            pass
        return (hdr.data, {})

    def get_image_layer(self, imagerepo, layer_id):
        """API v2 Get one image layer data file (tarball)"""
        url = self.dockerioapi.registry_url + "/v2/" + imagerepo + "/blobs/" + layer_id
        LOG.debug("layer url: %s", url)
        filename = self.localrepo.layersdir + '/' + layer_id
        if self.dockerioapi.get_file(url, filename, 3):
            self.localrepo.add_image_layer(filename)
            return True

        return False

    def get_layers_all(self, imagerepo, fslayers):
        """API v2 Get all layer data files belonging to a image tag"""
        files = []
        blob = ""
        if fslayers:
            for layer in reversed(fslayers):
                if "blobSum" in layer:
                    blob = layer["blobSum"]
                elif "digest" in layer:
                    blob = layer["digest"]

                LOG.info("downloading layer: %s", blob)
                if not self.get_image_layer(imagerepo, blob):
                    return []

                files.append(blob)

        return files

    def get(self, imagerepo, tag, platform=""):
        """API v2 Pull container"""
        files = []
        (hdr_data, manifest) = self.get_image_manifest(imagerepo, tag, platform)
        status = self.curl.get_status_code(hdr_data["X-ND-HTTPSTATUS"])
        if status == 401:
            LOG.error("manifest not found or not authorized")
            return []

        if status != 200:
            LOG.error("pulling manifest:")
            return []

        if not manifest:
            LOG.error("no manifest for given image and platform")
            return []

        try:
            if not (self.localrepo.setup_tag(tag) and self.localrepo.set_version("v2")):
                LOG.error("setting localrepo v2 tag and version")
                return []

            self.localrepo.save_json("manifest", manifest)
            LOG.debug("v2 layers: %s", imagerepo)
            if "fsLayers" in manifest:
                files = self.get_layers_all(imagerepo, manifest["fsLayers"])
            elif "layers" in manifest:
                if "config" in manifest:
                    manifest["layers"].append(manifest["config"])

                files = self.get_layers_all(imagerepo, manifest["layers"])
            else:
                LOG.error("layers section missing in manifest")

        except (KeyError, AttributeError, IndexError, ValueError, TypeError):
            pass

        return files

    def search_get_page(self, expression, url, lines=22, official=None):
        """API v2 Search results from Docker Hub"""
        if not expression:
            expression = '*'
        if expression and official is None:
            url = url + "/v2/search/repositories?query=%s" % (expression)
        elif expression and official is True:
            url = url + "/v2/search/repositories?query=%s&is_official=%s" % (expression, "true")
        elif expression and official is False:
            url = url + "/v2/search/repositories?query=%s&is_official=%s" % (expression, "false")
        else:
            return []

        url += f"&page_size={str(lines)}"
        if self.dockerioapi.search_page != 1:
            url += "&page=%d" % (self.dockerioapi.search_page)
        (dummy, buf) = self.dockerioapi.get_url(url)
        try:
            repo_list = json.loads(buf.getvalue().decode())
            if repo_list["count"] == self.dockerioapi.search_page:
                self.dockerioapi.search_ended = True

            LOG.debug(repo_list)
            return repo_list
        except (OSError, AttributeError, KeyError, ValueError, TypeError):
            self.dockerioapi.search_ended = True
            return []




class DockerIoAPI:
    """Class to encapsulate the access to the Docker Hub service
    Allows to search and download images from Docker Hub
    """

    def __init__(self, localrepo):
        self.index_url = Config.conf['dockerio_index_url']
        self.registry_url = Config.conf['dockerio_registry_url']
        self.localrepo = localrepo
        self.curl = GetURL()
        self.search_pause = True
        self.search_page = 0
        self.search_ended = False
        self.v1api = DockerIoAPIv1(self)
        self.v2api = DockerIoAPIv2(self)

    def set_proxy(self, http_proxy):
        """Select a socks http proxy for API access and file download"""
        LOG.info("Setting proxy: %s", http_proxy)
        self.curl.set_proxy(http_proxy)

    def set_registry(self, registry_url):
        """Change docker registry url"""
        LOG.info("Setting registry: %s", registry_url)
        self.registry_url = registry_url

    def set_index(self, index_url):
        """Change docker index url"""
        LOG.info("Setting docker index: %s", index_url)
        self.index_url = index_url

    def is_repo_name(self, imagerepo):
        """Check if name matches authorized characters for a docker repo"""
        if imagerepo and re.match("^[a-zA-Z0-9][a-zA-Z0-9-_./:]+$", imagerepo):
            return True

        return False

    def is_layer_name(self, layername):
        """Check if name matches authorized characters for a docker layer"""
        if layername and re.match("^[a-zA-Z0-9]+@[a-z0-9]+:[a-z0-9]+$", layername):
            return True
        return False

    def get_url(self, *args, **kwargs):
        """Encapsulates the call to GetURL.get() so that authentication
        for v1 and v2 repositories can be treated differently.
        Example:
             get_url(url, ctimeout=5, timeout=5, header=[]):
        """
        url = str(args[0])
        if "RETRY" not in kwargs:
            kwargs["RETRY"] = 3

        if "FOLLOW" not in kwargs:
            kwargs["FOLLOW"] = 3

        kwargs["RETRY"] -= 1
        (hdr, buf) = self.curl.get(*args, **kwargs)
        LOG.debug("header: %s", (hdr.data))
        LOG.debug("buffer: %s", (buf.getvalue().decode()))
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
                if "realm" not in www_authenticate:
                    return (hdr, buf)

                if 'error="insufficient_scope"' in www_authenticate:
                    return (hdr, buf)

                auth_header = ""
                if "/v2/" in url:
                    auth_header = self.v2api.get_auth(www_authenticate, kwargs["RETRY"])

                if "/v1/" in url:
                    auth_header = self.v1api.get_auth(www_authenticate)

                # OCI and multiplatform, prevent removal of header attributes
                try:
                    auth_kwargs["header"].append(auth_header)
                except KeyError:
                    auth_kwargs.update({"header": [auth_header]})

        (hdr, buf) = self.get_url(*args, **auth_kwargs)
        return (hdr, buf)

    def get_file(self, url, filename, cache_mode):
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
                (hdr, dummy) = self.get_url(url, nobody=1)
            elif cache_mode == 3:
                (hdr, dummy) = self.get_url(url, sizeonly=True)

            remote_size = self.curl.get_content_length(hdr)
            if remote_size == FileUtil(filename).size():
                return True             # is cached skip download
        else:
            remote_size = -1

        resume = False
        if filename.endswith("layer"):
            resume = True

        (hdr, dummy) = self.get_url(url, ofile=filename, resume=resume)
        if self.curl.get_status_code(hdr.data["X-ND-HTTPSTATUS"]) != 200:
            return False

        if remote_size == -1:
            remote_size = self.curl.get_content_length(hdr)

        if (remote_size != FileUtil(filename).size() and hdr.data["X-ND-CURLSTATUS"]):
            fsize = FileUtil(filename).size()
            LOG.error("file size mismatch: %s %s %s", filename, remote_size, fsize)
            return False

        return True

    def _parse_imagerepo(self, imagerepo):
        """Parse imagerepo to extract registry"""
        registry = ""
        registry_url = ""
        index_url = ""
        components = imagerepo.split('/')
        if '.' in components[0] and len(components) >= 2:
            registry = components[0]
            del components[0]

        if ('.' not in components[0] and components[0] != "library" and len(components) == 1):
            components.insert(0, "library")

        remoterepo = '/'.join(components)
        if registry:
            try:
                registry_url = Config.conf['docker_registries'][registry][0]
                index_url = Config.conf['docker_registries'][registry][1]
            except (KeyError, NameError, TypeError):
                registry_url = registry
                if "://" not in registry:
                    registry_url = "https://%s" % registry
                index_url = registry_url

            if registry_url:
                self.registry_url = registry_url

            if index_url:
                self.index_url = index_url

        return (imagerepo, remoterepo)

    def get(self, imagerepo, tag, platform=""):
        """Pull a docker image from a v2 registry or v1 index"""
        LOG.debug("get imagerepo: %s tag: %s", imagerepo, tag)
        (imagerepo, remoterepo) = self._parse_imagerepo(imagerepo)
        if self.localrepo.cd_imagerepo(imagerepo, tag):
            new_repo = False
        else:
            self.localrepo.setup_imagerepo(imagerepo)
            new_repo = True

        if self.v2api.is_valid():
            if not platform:
                platform = HostInfo().platform()
            files = self.v2api.get(remoterepo, tag, platform)  # try v2
        else:
            files = self.v1api.get(remoterepo, tag)  # try v1

        if new_repo and not files:
            self.localrepo.del_imagerepo(imagerepo, tag, False)

        return files

    def get_manifest(self, imagerepo, tag, platform=""):
        """Get image manifest"""
        LOG.debug("get manifest imagerepo: %s tag: %s", imagerepo, tag)
        (dummy, remoterepo) = self._parse_imagerepo(imagerepo)
        if self.v2api.is_valid():
            return self.v2api.get_image_manifest(remoterepo, tag, platform)
        return ({}, {})

    def get_tags(self, imagerepo):
        """List tags from a v2 or v1 repositories"""
        LOG.debug("get tags: %s", imagerepo)
        (dummy, remoterepo) = self._parse_imagerepo(imagerepo)
        if self.v2api.is_valid():
            return self.v2api.get_image_tags(remoterepo, True)  # try v2

        return self.v1api.get_image_tags(remoterepo, True)  # try v1

    def search_init(self, pause):
        """Setup new search"""
        self.search_pause = pause
        self.search_page = 0
        self.search_ended = False

    def search_get_page(self, expression, lines=22):
        """Get search results from Docker Hub"""
        if self.search_ended:
            return []

        self.search_page += 1
        if self.v2api.is_searchable(self.index_url):
            return self.v2api.search_get_page(expression, self.index_url, lines)

        if self.v1api.is_searchable():
            return self.v1api.search_get_page(expression, self.index_url)

        if self.v2api.is_searchable(self.registry_url):
            return self.v2api.search_get_page(expression, self.registry_url, lines)

        if self.v1api.is_searchable(self.registry_url):
            return self.v1api.search_get_page(expression, self.registry_url)

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
                structure["repositories"] = self.localrepo.load_json(f_path)
            elif fname == "manifest.json":
                structure["manifest"] = self.localrepo.load_json(f_path)
            elif len(fname) >= 69 and fname.endswith(".json"):
                structure["repoconfigs"][fname] = {}
                structure["repoconfigs"][fname]["json"] = self.localrepo.load_json(f_path)
                structure["repoconfigs"][fname]["json_f"] = f_path
            elif len(fname) >= 64 and FileUtil(f_path).isdir():
                layer_id = fname
                structure["repolayers"][layer_id] = {}
                for layer_f in os.listdir(f_path):
                    layer_f_path = f_path + '/' + layer_f
                    if layer_f == "VERSION":
                        ljson = self.localrepo.load_json(layer_f_path)
                        structure["repolayers"][layer_id]["VERSION"] = ljson
                    elif layer_f == "json":
                        ljson = self.localrepo.load_json(layer_f_path)
                        structure["repolayers"][layer_id]["json"] = ljson
                        structure["repolayers"][layer_id]["json_f"] = layer_f_path
                    elif "layer" in layer_f:
                        structure["repolayers"][layer_id]["layer_f"] = layer_f_path
                    else:
                        LOG.warning("unknown file in layer: %s", f_path)

        return structure

    def _find_top_layer_id(self, structure, my_layer_id=""):
        """Find the top layer within a Docker image"""
        if "repolayers" not in structure:
            return ""

        if not my_layer_id:
            my_layer_id = list(structure["repolayers"].keys())[0]

        found = ""
        for layer_id in structure["repolayers"]:
            if "parent" not in structure["repolayers"][layer_id]["json"]:
                continue
            if my_layer_id == structure["repolayers"][layer_id]["json"]["parent"]:
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
                        # layers.append(layer_file.replace("/layer.tar", ""))
                        layers.append(layer_file)

                    layers.reverse()
                    return (repotag["Config"], layers)

        return ("", [])

    def _load_image_step2(self, structure, imagerepo, tag):
        """Load a container image into a repository mimic docker load"""
        imagetag = imagerepo + ':' + tag
        (json_config_file, layers) = self._get_from_manifest(structure, imagetag)
        LOG.debug("json config file: %s", json_config_file)
        if json_config_file:
            layer_id = json_config_file.replace(".json", "")
            LOG.debug("Layer ID: %s", layer_id)
            LOG.debug("JSON Structure: %s", str(structure))
            json_file = structure["repoconfigs"][json_config_file]["json_f"]
            self._move_layer_to_v1repo(json_file, layer_id, "container.json")

        top_layer_id = self._find_top_layer_id(structure)
        layers = self._sorted_layers(structure, top_layer_id)
        for layer_id in layers:
            LOG.info("adding layer: %s", layer_id)
            if str(structure["repolayers"][layer_id]["VERSION"]) != "1.0":
                LOG.error("layer version unknown")
                return []

            for layer_item in ("json_f", "layer_f"):
                filename = str(structure["repolayers"][layer_id][layer_item])
                if not self._move_layer_to_v1repo(filename, layer_id):
                    LOG.error("copying %s file %s", layer_item[:-2], filename)
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
            LOG.error("failed to load image structure")
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
            if not FileUtil(layer_f).copyto(tmp_imagedir + "/" + layer_id + "/layer.tar"):
                return False

            manifest_item["Layers"].append(layer_id + "/layer.tar")
            json_string = self.create_container_meta(layer_id)
            if parent_layer_id:
                json_string["parent"] = parent_layer_id
            else:
                structure["repositories"][imagerepo][tag] = layer_id

            parent_layer_id = layer_id
            if not self.localrepo.save_json(tmp_imagedir + "/" + layer_id + "/json", json_string):
                return False

            if not FileUtil(tmp_imagedir + "/" + layer_id + "/VERSION").putdata("1.0", 'w'):
                return False

        structure["manifest"].append(manifest_item)
        return True

    def save(self, imagetag_list, imagefile):
        """Save a set of image tags to a file similarly to docker save
        """
        tmp_imagedir = FileUtil("save").mktmp()
        try:
            os.makedirs(tmp_imagedir)
        except OSError:
            return False

        structure = {}
        structure["manifest"] = []
        structure["repositories"] = {}
        status = False
        for (imagerepo, tag) in imagetag_list:
            status = self._save_image(imagerepo, tag, structure, tmp_imagedir)
            if not status:
                LOG.error("save image failed: %s", imagerepo + ':' + tag)
                break

        if status:
            self.localrepo.save_json(tmp_imagedir + "/manifest.json", structure["manifest"])
            self.localrepo.save_json(tmp_imagedir + "/repositories", structure["repositories"])
            if not FileUtil(tmp_imagedir).tar(imagefile):
                LOG.error("save image failed in writing tar: %s", imagefile)
                status = False
        else:
            LOG.error("no images specified")

        FileUtil(tmp_imagedir).remove(recursive=True)
        return status
