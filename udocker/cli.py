# -*- coding: utf-8 -*-
"""udocker Command Line Interface implementation"""

import os
import sys
import string
import json
from getpass import getpass

from udocker import __version__
from udocker.config import Config
from udocker.msg import Msg
from udocker.docker import DockerIoAPI
from udocker.localfile import LocalFileAPI
from udocker.helper.keystore import KeyStore
from udocker.helper.hostinfo import HostInfo
from udocker.helper.unshare import Unshare
from udocker.container.structure import ContainerStructure
from udocker.engine.execmode import ExecutionMode
from udocker.engine.nvidia import NvidiaMode
from udocker.tools import UdockerTools
from udocker.utils.fileutil import FileUtil
from udocker.utils.filebind import FileBind
from udocker.utils.mountpoint import MountPoint

# if Python 3
if sys.version_info[0] >= 3:
    BUILTIN = "builtins"
    GET_INPUT = input
else:
    BUILTIN = "__builtin__"
    # pylint: disable=undefined-variable
    GET_INPUT = raw_input


class UdockerCLI(object):
    """Implements most of the command line interface.
    These methods correspond directly to the commands that can
    be invoked via the command line interface.
    """

    STATUS_OK = 0
    STATUS_ERROR = 1

    def __init__(self, localrepo):
        self.localrepo = localrepo
        self.dockerioapi = DockerIoAPI(self.localrepo)
        self.localfileapi = LocalFileAPI(self.localrepo)
        if Config.conf['keystore'].startswith("/"):
            self.keystore = KeyStore(Config.conf['keystore'])
        else:
            self.keystore = KeyStore(self.localrepo.homedir + "/" +
                                     Config.conf['keystore'])

    def _cdrepo(self, cmdp):
        """Select the top directory of a local repository"""
        topdir = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return False

        if not FileUtil(topdir).isdir():
            Msg().out("Warning: localrepo directory is invalid: ",
                      topdir, l=Msg.WAR)
            return False

        self.localrepo.setup(topdir)
        return True

    def _check_imagespec(self, imagespec, def_imagespec=None):
        """Check image:tag syntax"""
        if (not imagespec) and def_imagespec:
            imagespec = def_imagespec

        try:
            (imagerepo, tag) = imagespec.rsplit(":", 1)
        except (ValueError, AttributeError):
            imagerepo = imagespec
            tag = "latest"

        if not (imagerepo and tag and
                self.dockerioapi.is_repo_name(imagespec)):
            Msg().err("Error: must specify image:tag or repository/image:tag")
            return(None, None)

        return imagerepo, tag

    def _check_imagerepo(self, imagerepo, def_imagerepo=None):
        """Check image repository syntax"""
        if (not imagerepo) and def_imagerepo:
            imagerepo = def_imagerepo

        if not (imagerepo and
                self.dockerioapi.is_repo_name(imagerepo)):
            Msg().err("Error: enter image or repository/image without tag")
            return None

        return imagerepo

    def _set_repository(self, registry_url, index_url=None,
                        imagerepo=None, http_proxy=None):
        """Select docker respository"""
        transport = "https:"
        if http_proxy:
            self.dockerioapi.set_proxy(http_proxy)

        if registry_url:
            if "://" not in registry_url:
                registry_url = "https://" + registry_url
            self.dockerioapi.set_registry(registry_url)
            if not index_url:
                self.dockerioapi.set_index("")

        if index_url:
            if "://" not in index_url:
                index_url = "https://" + index_url
            self.dockerioapi.set_index(index_url)
            if not registry_url:
                self.dockerioapi.set_registry("")

        if not (registry_url or index_url):
            try:
                if "://" in imagerepo:
                    (transport, dummy, hostname) = imagerepo.split('/')[:3]
                else:
                    (hostname, dummy) = imagerepo.split('/')[:2]
            except (ValueError, IndexError, TypeError):
                return False
            if "." in hostname:
                try:
                    self.dockerioapi.set_registry( \
                            Config.conf['docker_registries'][hostname][0])
                    self.dockerioapi.set_index( \
                            Config.conf['docker_registries'][hostname][1])
                except (KeyError, NameError, TypeError):
                    self.dockerioapi.set_registry(transport + "//" + hostname)
                    self.dockerioapi.set_index(transport + "//" + hostname)

        return True

    def _split_imagespec(self, imagerepo):
        """Split image repo into hostname, repo, tag"""
        if not imagerepo:
            return ("", "", "", "")
        transport = ""
        hostname = ""
        image = imagerepo
        tag = ""
        try:
            if "://" in imagerepo:
                (transport, dummy, hostname, image) = imagerepo.split('/', 4)
            elif '/' in imagerepo:
                (hostname, image) = imagerepo.split('/', 1)
        except (ValueError, IndexError, TypeError):
            pass
        if hostname and '.' not in hostname:
            image = hostname + '/' + image
            hostname = ""
        if ':' in image:
            (image, tag) = image.split(':', 1)
        return (transport, hostname, image, tag)

    def do_mkrepo(self, cmdp):
        """
        mkrepo: create a local repository in a specified directory
        mkrepo <directory>
        """
        topdir = cmdp.get("P1")
        if cmdp.missing_options():
            return self.STATUS_ERROR
        if not os.path.exists(topdir):
            self.localrepo.setup(topdir)
            if not self.localrepo.create_repo():
                Msg().err("Error: localrepo creation failure: ", topdir)
                return self.STATUS_ERROR
        else:
            Msg().err("Error: localrepo directory already exists: ", topdir)
            return self.STATUS_ERROR

        return self.STATUS_OK

    def _search_print_lines(self, repo_list, lines, fmt):
        """Print search results from v1 or v2 API"""
        for repo in repo_list["results"]:
            if "is_official" in repo and repo["is_official"]:
                is_official = "[OK]"
            else:
                is_official = "----"
            description = ""
            for dfield in ("description", "short_description"):
                if dfield in repo and repo[dfield] is not None:
                    for char in repo[dfield]:
                        if char == '\n':
                            break
                        if char in string.printable:
                            description += char
                    break
            name = ""
            for nfield in ("name", "repo_name"):
                if nfield in repo and repo[nfield] is not None:
                    name = repo[nfield]
                    break
            stars = ""
            if "star_count" in repo and repo["star_count"] is not None:
                stars = str(repo["star_count"])
            Msg().out(fmt % (name, is_official, description, stars))
            lines -= 1
            if not lines:
                break

    def _search_repositories(self, expression, pause="", no_trunc=""):
        """Print search header and loop over search results"""
        term_lines, dummy = HostInfo().termsize()
        term_lines -= 2
        fmt = "%-55.80s %8.8s %-70.70s %5.5s"
        if no_trunc:
            fmt = "%-55s %8s %-70s %5s"
        while True:
            lines = term_lines
            while lines > 0:
                repo_list = \
                        self.dockerioapi.search_get_page(expression, term_lines)
                if not repo_list:
                    return self.STATUS_OK
                if lines == term_lines:
                    Msg().out(fmt % \
                        ("NAME", "OFFICIAL", "DESCRIPTION", "STARS"), l=Msg.INF)
                if len(repo_list["results"]) > lines:
                    print_lines = lines
                else:
                    print_lines = len(repo_list["results"])
                lines -= print_lines
                self._search_print_lines(repo_list, print_lines, fmt)
            if pause and not self.dockerioapi.search_ended:
                if GET_INPUT("[return or q to quit]") in ('q', 'Q', 'e', 'E'):
                    return self.STATUS_OK

    def _list_tags(self, expression):
        """List tags for repository"""
        try:
            for tag in self.dockerioapi.get_tags(expression):
                Msg().out(tag)
            return self.STATUS_OK
        except (KeyError, TypeError, ValueError):
            return self.STATUS_ERROR

    def do_search(self, cmdp):
        """
                search: search dockerhub for container images
        search [options]  <expression>
        -a                                              :do not pause
        --no-trunc                                      :do not trunc lines
        --list-tags                                     :list repository tags
        --index=<url>                ex. https://index.docker.io/v1
        --registry=<url>             ex. https://registry-1.docker.io
        --httpproxy=socks4://user:pass@host:port        :use http proxy
        --httpproxy=socks5://user:pass@host:port        :use http proxy
        --httpproxy=socks4://host:port                  :use http proxy
        --httpproxy=socks5://host:port                  :use http proxy
        --httpproxy=socks4a://user:pass@host:port       :use http proxy
        --httpproxy=socks5h://user:pass@host:port       :use http proxy
        --httpproxy=socks4a://host:port                 :use http proxy
        --httpproxy=socks5h://host:port                 :use http proxy
        """
        pause = not cmdp.get("-a")
        index_url = cmdp.get("--index=")
        registry_url = cmdp.get("--registry=")
        http_proxy = cmdp.get("--httpproxy=")
        no_trunc = cmdp.get("--no-trunc")
        list_tags = cmdp.get("--list-tags")
        expression = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR
        self._set_repository(registry_url, index_url, expression, http_proxy)
        (dum1, dum2, expression, dum3) = self._split_imagespec(expression)
        self.dockerioapi.search_init(pause)
        v2_auth_token = self.keystore.get(self.dockerioapi.registry_url)
        self.dockerioapi.set_v2_login_token(v2_auth_token)
        if list_tags:
            return self._list_tags(expression)

        return self._search_repositories(expression, pause, no_trunc)

    def do_load(self, cmdp):
        """
        load: load an  image saved by docker with 'docker save'
        load [options] <repo/image>
        --input=<image-file>        :load image file saved by docker
        -i <image-file>             :load image file saved by docker
        """
        imagefile = cmdp.get("--input=")
        if not imagefile:
            imagefile = cmdp.get("-i=")
            if not imagefile:
                imagefile = '-'
        from_stdin = cmdp.get('-')
        if from_stdin:
            imagefile = '-'
            cmdp.get("-i")
        imagerepo = cmdp.get("P1")
        if imagerepo == '-':
            imagefile = '-'
            imagerepo = cmdp.get("P2")
        if cmdp.missing_options():  # syntax error
            return self.STATUS_ERROR
        if not imagefile:
            Msg().err("Error: must specify filename of docker exported image")
            return self.STATUS_ERROR
        if imagerepo and not self._check_imagerepo(imagerepo):
            return self.STATUS_ERROR
        repos = self.localfileapi.load(imagefile, imagerepo)
        if not repos:
            Msg().err("Error: load failed")
            return self.STATUS_ERROR
        for repo_item in repos:
            Msg().out(repo_item)
        return self.STATUS_OK

    def do_save(self, cmdp):
        """
        save: save an image to file
        save [options] IMAGE
        --output=<image-file>       :save image to file
        -o <image-file>             :save image to file
        """
        imagefile = cmdp.get("--output=")
        if not imagefile:
            imagefile = cmdp.get("-o=")
            if not imagefile:
                imagefile = '-'
        from_stdin = cmdp.get('-')
        imagespec_list = cmdp.get("P*")
        if from_stdin:
            del imagespec_list[0]
            imagefile = '-'
            cmdp.get("-o")
        if cmdp.missing_options():  # syntax error
            return self.STATUS_ERROR
        if imagefile != '-':
            if os.path.exists(imagefile):
                Msg().err("Error: output file already exists:", imagefile)
                return self.STATUS_ERROR
        imagetag_list = []
        for imagespec in imagespec_list:
            (imagerepo, tag) = self._check_imagespec(imagespec)
            if not imagerepo:
                return self.STATUS_ERROR
            imagetag_list.append((imagerepo, tag))
        if not imagefile:
            Msg().err("Error: must specify filename of image file for output")
            return self.STATUS_ERROR
        if not self.localfileapi.save(imagetag_list, imagefile):
            return self.STATUS_ERROR
        return self.STATUS_OK

    def do_import(self, cmdp):
        """
        import : import image (directory tree) from tar file or stdin
        import <tar-file> <repo/image:tag>
        import - <repo/image:tag>
        --mv                      :if possible move tar-file instead of copy
        --tocontainer             :import to container, no image is created
        --clone                   :import udocker container format with metadata
        --name=<container-name>   :with --tocontainer or --clone to add an alias
        """
        move_tarball = cmdp.get("--mv")
        to_container = cmdp.get("--tocontainer")
        name = cmdp.get("--name=")
        clone = cmdp.get("--clone")
        from_stdin = cmdp.get('-')
        if from_stdin:
            tarfile = '-'
            imagespec = cmdp.get("P1")
            move_tarball = False
        else:
            tarfile = cmdp.get("P1")
            imagespec = cmdp.get("P2")
        if cmdp.missing_options():  # syntax error
            return self.STATUS_ERROR
        if not tarfile:
            Msg().err("Error: must specify tar filename")
            return self.STATUS_ERROR
        if to_container or clone:
            if clone:
                container_id = self.localfileapi.import_clone(
                    tarfile, name)
            else:
                (imagerepo, tag) = self._check_imagespec(imagespec,
                                                         "IMPORTED:unknown")
                container_id = self.localfileapi.import_tocontainer(
                    tarfile, imagerepo, tag, name)
            if container_id:
                Msg().out(container_id)
                return self.STATUS_OK
        else:
            (imagerepo, tag) = self._check_imagespec(imagespec)
            if not imagerepo:
                return self.STATUS_ERROR
            if self.localfileapi.import_toimage(tarfile, imagerepo, tag,
                                                move_tarball):
                return self.STATUS_OK
        Msg().err("Error: importing")
        return self.STATUS_ERROR

    def do_export(self, cmdp):
        """
        export : export container (directory tree) to a tar file or stdin
        export -o <tar-file> <container-id>
        export - <container-id>
        -o                         :export to file, instead of stdout
        --clone                    :export in clone (udocker) format
        """
        to_file = cmdp.get("-o")
        clone = cmdp.get("--clone")
        if to_file:
            tarfile = cmdp.get("P1")
            container_id = cmdp.get("P2")
        else:
            tarfile = "-"
            container_id = cmdp.get("P1")
        if cmdp.missing_options():  # syntax error
            return self.STATUS_ERROR
        container_id = self.localrepo.get_container_id(container_id)
        if not container_id:
            Msg().err("Error: invalid container id", container_id)
            return self.STATUS_ERROR
        if not tarfile:
            Msg().err("Error: invalid output file name", tarfile)
            return self.STATUS_ERROR
        if to_file:
            Msg().out("Info: exporting to file", tarfile)

        cstruct = ContainerStructure(self.localrepo, container_id)
        if clone:
            if cstruct.clone_tofile(tarfile):
                return self.STATUS_OK
        else:
            if cstruct.export_tofile(tarfile):
                return self.STATUS_OK

        Msg().err("Error: exporting")
        return self.STATUS_ERROR

    def do_clone(self, cmdp):
        """
        clone : create a duplicate copy of an existing container
        clone <source-container-id>
        --name=<container-name>    :add an alias to the cloned container
        """
        name = cmdp.get("--name=")
        container_id = cmdp.get("P1")
        if cmdp.missing_options():  # syntax error
            return self.STATUS_ERROR
        container_id = self.localrepo.get_container_id(container_id)
        Msg().out("Info: cloning container id:", container_id, l=Msg.DBG)
        if not container_id:
            Msg().err("Error: invalid container id", container_id)
            return self.STATUS_ERROR
        clone_id = self.localfileapi.clone_container(container_id, name)
        if clone_id:
            Msg().out(clone_id)
            return self.STATUS_OK

        Msg().err("Error: cloning")
        return self.STATUS_ERROR

    def do_login(self, cmdp):
        """
        login: authenticate into docker repository e.g. dockerhub
        --username=username
        --password=password
        --registry=<url>         ex. https://registry-1.docker.io
        """
        username = cmdp.get("--username=")
        password = cmdp.get("--password=")
        registry_url = cmdp.get("--registry=")
        if cmdp.missing_options():  # syntax error
            return self.STATUS_ERROR
        self._set_repository(registry_url, None, None, None)
        if not username:
            username = GET_INPUT("username: ")
        if not password:
            password = getpass("password: ")
        if password and password == password.upper():
            Msg().out("Warning: password in uppercase",
                      "Caps Lock ?", l=Msg.WAR)

        v2_auth_token = self.dockerioapi.get_v2_login_token(username, password)
        if self.keystore.put(self.dockerioapi.registry_url,
                             v2_auth_token, "") == 0:
            return self.STATUS_OK

        Msg().err("Error: invalid credentials")
        return self.STATUS_ERROR

    def do_logout(self, cmdp):
        """
        logout: authenticate into docker repository e.g. dockerhub
        -a remove all authentication credentials
        --registry=<url>          ex. https://registry-1.docker.io
        """
        all_credentials = cmdp.get("-a")
        registry_url = cmdp.get("--registry=")
        if cmdp.missing_options():  # syntax error
            return self.STATUS_ERROR
        self._set_repository(registry_url, None, None, None)
        if all_credentials:
            exit_status = self.keystore.erase()
        else:
            exit_status = self.keystore.delete(self.dockerioapi.registry_url)

        if exit_status == self.STATUS_ERROR:
            Msg().err("Error: deleting credentials")

        return exit_status

    def do_pull(self, cmdp):
        """
        pull: download images from docker hub
        pull [options] <repo/image:tag>
        --httpproxy=socks4://user:pass@host:port        :use http proxy
        --httpproxy=socks5://user:pass@host:port        :use http proxy
        --httpproxy=socks4://host:port                  :use http proxy
        --httpproxy=socks5://host:port                  :use http proxy
        --httpproxy=socks4a://user:pass@host:port       :use http proxy
        --httpproxy=socks5h://user:pass@host:port       :use http proxy
        --httpproxy=socks4a://host:port                 :use http proxy
        --httpproxy=socks5h://host:port                 :use http proxy
        --index=https://index.docker.io/v1              :docker index
        --registry=https://registry-1.docker.io         :docker registry

        Examples:
          pull fedora:latest
          pull quay.io/something/somewhere:latest
        """
        index_url = cmdp.get("--index=")
        registry_url = cmdp.get("--registry=")
        http_proxy = cmdp.get("--httpproxy=")
        (imagerepo, tag) = self._check_imagespec(cmdp.get("P1"))
        if (not imagerepo) or cmdp.missing_options():    # syntax error
            return self.STATUS_ERROR

        self._set_repository(registry_url, index_url, imagerepo, http_proxy)
        v2_auth_token = self.keystore.get(self.dockerioapi.registry_url)
        self.dockerioapi.set_v2_login_token(v2_auth_token)
        if self.dockerioapi.get(imagerepo, tag):
            return self.STATUS_OK

        Msg().err("Error: no files downloaded")
        return self.STATUS_ERROR

    def _create(self, imagespec):
        """Auxiliary to create(), performs the creation"""
        if not self.dockerioapi.is_repo_name(imagespec):
            Msg().err("Error: must specify image:tag or repository/image:tag")
            return False
        (imagerepo, tag) = self._check_imagespec(imagespec)
        if imagerepo:
            return ContainerStructure(self.localrepo).create_fromimage(
                imagerepo, tag)
        return False

    def do_create(self, cmdp):
        """
        create: extract image layers and create a container
        create [options]  <repo/image:tag>
        --name=<container-name>    :set or change the name of the container
        """
        imagespec = cmdp.get("P1")
        name = cmdp.get("--name=")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR

        container_id = self._create(imagespec)
        if container_id:
            Msg().out(container_id)
            if name and not self.localrepo.set_container_name(container_id,
                                                              name):
                Msg().err("Error: invalid container name may already exist "
                          "or wrong format")
                return self.STATUS_ERROR
            return self.STATUS_OK
        return self.STATUS_ERROR

    def _get_run_options(self, cmdp, exec_engine=None):
        """Read command line options into variables"""
        cmdp.declare_options("-v= -e= -w= -u= -p= -i -t -a -P")
        cmd_options = {
            "netcoop": {
                "fl": ("-P", "--publish-all", "--netcoop",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "portsmap": {
                "fl": ("-p=", "--publish=",), "act": "E",
                "p2": "CMD_OPT", "p3": True
            },
            "novol": {
                "fl": ("--novol=",), "act": "R",
                "p2": "CMD_OPT", "p3": True
            },
            "vol": {
                "fl": ("-v=", "--volume=",), "act": "E",
                "p2": "CMD_OPT", "p3": True
            },
            "env": {
                "fl": ("-e=", "--env=",), "act": "E",
                "p2": "CMD_OPT", "p3": True
            },
            "envfile": {
                "fl": ("--env-file=",), "act": 'E',
                "p2": "CMD_OPT", "p3": True
            },
            "user": {
                "fl": ("-u=", "--user=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "cwd": {
                "fl": ("-w=", "--workdir=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "entryp": {
                "fl": ("--entrypoint=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "cpuset": {
                "fl": ("--cpuset-cpus=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "hostauth": {
                "fl": ("--hostauth",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "containerauth": {
                "fl": ("--containerauth",), "act": 'R',
                "p2": "CMD_OPT", "p3": False
            },
            "nosysdirs": {
                "fl": ("--nosysdirs",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "hostenv": {
                "fl": ("--hostenv",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "bindhome": {
                "fl": ("--bindhome",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "nometa": {
                "fl": ("--nometa",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "dri": {
                "fl": ("--dri",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "cmd": {
                "fl": ("P+",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "volfrom": {
                "fl": ("--volumes-from=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "dns": {
                "fl": ("--dns=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "dnssearch": {
                "fl": ("--dns-search=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "kernel": {
                "fl": ("--kernel=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "devices": {
                "fl": ("--device=",), "act": "E",
                "p2": "CMD_OPT", "p3": True
            },
            "nobanner": {
                "fl": ("--nobanner",), "act": 'R',
                "p2": "CMD_OPT", "p3": False
            }
        }
        for option, cmdp_args in list(cmd_options.items()):
            last_value = None
            for cmdp_fl in cmdp_args["fl"]:
                option_value = cmdp.get(cmdp_fl, cmdp_args["p2"],
                                        cmdp_args["p3"])
                if not exec_engine:
                    continue
                if cmdp_args["act"] == "R":   # action is replace
                    if option_value or last_value is None:
                        exec_engine.opt[option] = option_value
                elif cmdp_args["act"] == "E":   # action is extend
                    #if option == "env":
                    #    print (type(option_value))
                    #    print (option_value)
                    exec_engine.opt[option].extend(option_value)
                last_value = option_value

    def do_run(self, cmdp):
        """
        run: execute a container
        run [options] <container-id-or-name>
        run [options] <repo/image:tag>
        --rm                       :delete container upon exit
        --workdir=/home/userXX     :working directory set to /home/userXX
        --user=userXX              :run as userXX
        --user=root                :run as root
        --volume=/data:/mnt        :mount host directory /data in /mnt
        --novol=/proc              :remove /proc from list of volumes to mount
        --env="MYTAG=xxx"          :set environment variable
        --env-file=<file>          :read environment variables from file
        --hostauth                 :get user account and group from host
        --containerauth            :use container passwd and group directly
        --nosysdirs                :do not bind the host /proc /sys /run /dev
        --nometa                   :ignore container metadata
        --dri                      :bind directories relevant for dri graphics
        --hostenv                  :pass the host environment to the container
        --cpuset-cpus=<1,2,3-4>    :CPUs in which to allow execution
        --name=<container-name>    :set or change the name of the container
        --bindhome                 :bind the home directory into the container
        --kernel=<kernel-id>       :simulate this Linux kernel version
        --device=/dev/xxx          :pass device to container (R1 mode only)
        --location=<container-dir> :use container outside the repository
        --nobanner                 :don't print a startup banner
        --entrypoint               :override the container metadata entrypoint

        Only available in Rn execution modes:
        --device=/dev/xxx          :pass device to container (R1 mode only)

        Only available in Pn execution modes:
        --publish=<hport:cport>    :map container TCP/IP <cport> into <hport>
        --publish-all              :bind and connect to random ports

        run <container-id-or-name> executes an existing container, previously
        created from an image by using: create <repo/image:tag>

        run <repo/image:tag> always creates a new container from the image
        if needed the image is pulled. This is slow and may waste storage.
        """
        self._get_run_options(cmdp)
        container_or_image = cmdp.get("P1")
        Config.conf['location'] = cmdp.get("--location=")
        delete = cmdp.get("--rm")
        name = cmdp.get("--name=")
        #
        if cmdp.missing_options(): # syntax error
            return self.STATUS_ERROR

        if Config.conf['location']:
            container_id = ""
        elif not container_or_image:
            Msg().err("Error: must specify container_id or image:tag")
            return self.STATUS_ERROR
        else:
            container_id = self.localrepo.get_container_id(container_or_image)
            if not container_id:
                (imagerepo, tag) = self._check_imagespec(container_or_image)
                if (imagerepo and
                        self.localrepo.cd_imagerepo(imagerepo, tag)):
                    container_id = self._create(imagerepo + ":" + tag)
                if not container_id:
                    self.do_pull(cmdp)
                    if self.localrepo.cd_imagerepo(imagerepo, tag):
                        container_id = self._create(imagerepo + ":" + tag)
                    if not container_id:
                        Msg().err("Error: image or container not available")
                        return self.STATUS_ERROR
            if name and container_id:
                if not self.localrepo.set_container_name(container_id, name):
                    Msg().err("Error: invalid container name format")
                    return self.STATUS_ERROR

        exec_mode = ExecutionMode(self.localrepo, container_id)
        exec_engine = exec_mode.get_engine()
        if not exec_engine:
            Msg().err("Error: no execution engine for this execmode")
            return self.STATUS_ERROR

        self._get_run_options(cmdp, exec_engine)
        exit_status = exec_engine.run(container_id)
        if delete and not self.localrepo.isprotected_container(container_id):
            self.localrepo.del_container(container_id)

        return exit_status

    def do_images(self, cmdp):
        """
        images: list container images
        images [options]
        -l                         :long format
        """
        verbose = cmdp.get("-l")
        dummy = cmdp.get("--no-trunc")
        dummy = cmdp.get("--all")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR
        images_list = self.localrepo.get_imagerepos()
        Msg().out("REPOSITORY", l=Msg.INF)
        for (imagerepo, tag) in images_list:
            prot = (".", "P")[
                self.localrepo.isprotected_imagerepo(imagerepo, tag)]
            Msg().out("%s    %c" % (imagerepo + ":" + tag, prot))
            if verbose:
                imagerepo_dir = self.localrepo.cd_imagerepo(imagerepo, tag)
                Msg().out(f"  {imagerepo_dir}")
                layers_list = self.localrepo.get_layers(imagerepo, tag)
                if layers_list:
                    for (layer_name, size) in layers_list:
                        file_size = size / (1024 * 1024)
                        if not file_size and size:
                            file_size = 1
                        Msg().out("    %s (%d MB)" %
                                  (layer_name.replace(imagerepo_dir, ""),
                                   file_size))
        return self.STATUS_OK

    def do_ps(self, cmdp):
        """
        ps: list containers
        -m                         :print execution mode
        -s                         :print size in MB
        """
        print_mode = cmdp.get("-m")
        print_size = cmdp.get("-s")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR
        mod_h = size_h = ""
        mod_l = size_l = "%0s"
        if print_mode:
            mod_h = "MOD "
            mod_l = "%2.2s "
        if print_size:
            size_h = "SIZE "
            size_l = "%5.5s "
        fmt = "%-36.36s %c %c " + mod_h + size_h + "%-18s %-20.20s"
        Msg().out(fmt % ("CONTAINER ID", 'P', 'M', "NAMES", "IMAGE"))
        fmt = "%-36.36s %c %c " + mod_l + size_l + "%-18.100s %-20.100s"
        line = [''] * 7
        containers_list = self.localrepo.get_containers_list(False)
        for (line[0], line[6], line[5]) in containers_list:
            container_id = line[0]
            exec_mode = ExecutionMode(self.localrepo, container_id)
            line[3] = exec_mode.get_mode() if print_mode else ""
            line[1] = ('.', 'P')[
                self.localrepo.isprotected_container(container_id)]
            line[2] = ('R', 'W', 'N', 'D')[
                self.localrepo.iswriteable_container(container_id)]
            line[4] = self.localrepo.get_size(container_id) \
                    if print_size else ""
            Msg().out(fmt % tuple(line))
        return self.STATUS_OK

    def do_rm(self, cmdp):
        """
        rm: delete a container
        rm <container_id>
        -f                          :force removal
        """
        force = cmdp.get("-f")
        container_id_list = cmdp.get("P*")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR
        if not container_id_list:
            Msg().err("Error: must specify image:tag or repository/image:tag")
            return self.STATUS_ERROR

        exit_status = self.STATUS_OK
        for container_id in cmdp.get("P*"):
            container_id = self.localrepo.get_container_id(container_id)
            if not container_id:
                Msg().err("Error: invalid container id", container_id)
                exit_status = self.STATUS_ERROR
                continue

            if self.localrepo.isprotected_container(container_id):
                Msg().err("Error: container is protected")
                exit_status = self.STATUS_ERROR
                continue

            Msg().out("Info: deleting container:",
                      str(container_id), l=Msg.INF)
            if not self.localrepo.del_container(container_id, force):
                Msg().err("Error: deleting container")
                exit_status = self.STATUS_ERROR

        return exit_status

    def do_rmi(self, cmdp):
        """
        rmi: delete an image in the local repository
        rmi [options] <repo/image:tag>
        -f                          :force removal
        """
        force = cmdp.get("-f")
        imagespec = str(cmdp.get("P1"))
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR

        (imagerepo, tag) = self._check_imagespec(imagespec)
        if not imagerepo:
            return self.STATUS_ERROR

        if self.localrepo.isprotected_imagerepo(imagerepo, tag):
            Msg().err("Error: image repository is protected")
            return self.STATUS_ERROR

        Msg().out("Info: deleting image:", imagespec, l=Msg.INF)
        if not self.localrepo.del_imagerepo(imagerepo, tag, force):
            Msg().err("Error: deleting image")
            return self.STATUS_ERROR

        return self.STATUS_OK

    def do_protect(self, cmdp):
        """
        protect: protect a container or image against deletion
        protect <container-id or repo/image:tag>
        """
        arg = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR

        if self.localrepo.get_container_id(arg):
            if not self.localrepo.protect_container(arg):
                Msg().err("Error: protect container failed")
                return self.STATUS_ERROR
            return self.STATUS_OK

        (imagerepo, tag) = self._check_imagespec(arg)
        if imagerepo:
            if self.localrepo.protect_imagerepo(imagerepo, tag):
                return self.STATUS_OK

        Msg().err("Error: protect image failed")
        return self.STATUS_ERROR

    def do_unprotect(self, cmdp):
        """
        unprotect: remove delete protection
        unprotect <container-id or repo/image:tag>
        """
        arg = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR

        if self.localrepo.get_container_id(arg):
            if not self.localrepo.unprotect_container(arg):
                Msg().err("Error: unprotect container failed")
                return self.STATUS_ERROR
            return self.STATUS_OK

        (imagerepo, tag) = self._check_imagespec(arg)
        if imagerepo:
            if self.localrepo.unprotect_imagerepo(imagerepo, tag):
                return self.STATUS_OK

        Msg().err("Error: unprotect image failed")
        return self.STATUS_ERROR

    def do_name(self, cmdp):
        """
        name: give a name alias to a container
        name <container-id> <container-name>
        """
        container_id = cmdp.get("P1")
        name = cmdp.get("P2")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR
        if not (self.localrepo.get_container_id(container_id) and name):
            Msg().err("Error: invalid container id or name")
            return self.STATUS_ERROR
        if not self.localrepo.set_container_name(container_id, name):
            Msg().err("Error: invalid container name")
            return self.STATUS_ERROR

        return self.STATUS_OK

    def do_rename(self, cmdp):
        """
        rename: change a name alias
        name <container-name> <new-container-name>
        """
        name = cmdp.get("P1")
        new_name = cmdp.get("P2")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR
        container_id = self.localrepo.get_container_id(name)
        if not container_id:
            Msg().err("Error: container does not exist")
            return self.STATUS_ERROR
        if self.localrepo.get_container_id(new_name):
            Msg().err("Error: new name already exists")
            return self.STATUS_ERROR
        if not self.localrepo.del_container_name(name):
            Msg().err("Error: name does not exist")
            return self.STATUS_ERROR
        if not self.localrepo.set_container_name(container_id, new_name):
            Msg().err("Error: setting new name")
            self.localrepo.set_container_name(container_id, name)
            return self.STATUS_ERROR

        return self.STATUS_OK

    def do_rmname(self, cmdp):
        """
        rmname: remove a name alias from container
        rmname <container-name>
        """
        name = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR
        if not name:
            Msg().err("Error: invalid container id or name")
            return self.STATUS_ERROR
        if not self.localrepo.del_container_name(name):
            Msg().err("Error: removing container name")
            return self.STATUS_ERROR

        Msg().out(f"Info: container name: {name} removed.")
        return self.STATUS_OK

    def do_inspect(self, cmdp):
        """
        inspect: print container metadata JSON from an imagerepo or container
        inspect <container-id or repo/image:tag>
        -p                         :print container directory path on host
        """
        container_or_image = cmdp.get("P1")
        container_id = self.localrepo.get_container_id(container_or_image)
        print_dir = cmdp.get("-p")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR

        if container_id:
            (container_dir, container_json) = ContainerStructure(
                self.localrepo, container_id).get_container_attr()
        else:
            (imagerepo, tag) = self._check_imagespec(container_or_image)
            if self.localrepo.cd_imagerepo(imagerepo, tag):
                (container_json, dummy) = self.localrepo.get_image_attributes()
            else:
                Msg().err("Error: image not found", imagerepo)
                return self.STATUS_ERROR

        if print_dir:
            if container_id and container_dir:
                Msg().out(str(container_dir) + "/ROOT")
                return self.STATUS_OK
        elif container_json:
            try:
                Msg().out(json.dumps(container_json, sort_keys=True,
                                     indent=4, separators=(',', ': ')))
            except (IOError, OSError, AttributeError, ValueError, TypeError):
                Msg().out(container_json)
            return self.STATUS_OK

        Msg().err("Error: image or container not found", container_or_image)
        return self.STATUS_ERROR

    def do_verify(self, cmdp):
        """
        verify: verify an image
        verify <repo/image:tag>
        """
        (imagerepo, tag) = self._check_imagespec(cmdp.get("P1"))
        if (not imagerepo) or cmdp.missing_options():  # syntax error
            return self.STATUS_ERROR

        Msg().out(f"Info: verifying: {imagerepo}:{tag}", l=Msg.INF)
        if not self.localrepo.cd_imagerepo(imagerepo, tag):
            Msg().err("Error: selecting image and tag")
            return self.STATUS_ERROR

        if self.localrepo.verify_image():
            Msg().out("Info: image Ok", l=Msg.INF)
            return self.STATUS_OK

        Msg().err("Error: image verification failure")
        return self.STATUS_ERROR

    def do_setup(self, cmdp):
        """
        setup: change container execution settings
        setup [options] <container-id>
        --execmode=<mode>       :select execution mode from below
        --force                 :force setup change
        --purge                 :clean mountpoints and files created by udocker
        --fixperm               :attempt to fix file permissions
        --nvidia                :add NVIDIA libraries and binaries
                                 (nvidia support is EXPERIMENTAL)

        <mode> is one of the following execution modes:
        P1: proot accelerated mode using seccomp filtering (default)
        P2: proot accelerated mode disabled
        F1: fakechroot starting executables via direct loader invocation
        F2: like F1 plus protected environment and modified ld.so
        F3: fakechroot plus patching of elf headers in binaries and libs
        F4: like F3 plus support for newly created executables via
            dynamic patching of elf headers in binaries and libs
        R1: runc using rootless namespaces, requires recent kernel
            with user namespace support enabled
        R2: proot with root emulation running on top of runc to avoid
            most of the errors related to change of uid or gid
        R3: same as R2 but with proot accelerated mode disabled
        S1: singularity, requires a local installation of singularity,
            if singularity is available in the PATH udocker will use
            it to execute the container
        """
        container_id = cmdp.get("P1")
        xmode = cmdp.get("--execmode=")
        force = cmdp.get("--force")
        nvidia = cmdp.get("--nvidia")
        purge = cmdp.get("--purge")
        fixperm = cmdp.get("--fixperm")
        if cmdp.missing_options():               # syntax error
            return self.STATUS_ERROR

        container_dir = self.localrepo.cd_container(container_id)
        if not container_dir:
            Msg().err("Error: invalid container id")
            return self.STATUS_ERROR

        if xmode and self.localrepo.isprotected_container(container_id):
            Msg().err("Error: container is protected")
            return self.STATUS_ERROR

        if purge:
            FileBind(self.localrepo, container_id).restore(force)
            MountPoint(self.localrepo, container_id).restore()

        if fixperm:
            Unshare().namespace_exec(lambda: FileUtil(container_dir +
                                                      "/ROOT").rchown())
            FileUtil(container_dir + "/ROOT").rchmod()

        nvidia_mode = NvidiaMode(self.localrepo, container_id)
        if nvidia:
            nvidia_mode.set_mode(force)

        exec_mode = ExecutionMode(self.localrepo, container_id)
        if xmode:
            if exec_mode.set_mode(xmode.upper(), force):
                return self.STATUS_OK
            return self.STATUS_ERROR

        if xmode or not (xmode or force or nvidia or purge or fixperm):
            Msg().out(f"execmode: {exec_mode.get_mode()}")
            Msg().out(f"nvidiamode: {nvidia_mode.get_mode()}")

        return self.STATUS_OK

    def do_install(self, cmdp):
        """
        install: install udocker and its tools
        install [options]
        --force                    :force reinstall
        --purge                    :remove files (be careful)
        """
        if cmdp is not None:
            force = cmdp.get("--force")
            purge = cmdp.get("--purge")
            if cmdp.missing_options():  # syntax error
                return self.STATUS_ERROR
        else:
            force = False
            purge = False

        utools = UdockerTools(self.localrepo)
        if purge:
            utools.purge()

        if utools.install(force):
            return self.STATUS_OK

        return self.STATUS_ERROR

    def do_showconf(self, cmdp):
        """
        showconf: Print all configuration options
        """
        cmdp.get("showconf", "CMD")
        if cmdp.missing_options():  # syntax error
            return self.STATUS_ERROR

        Msg().out(80*"-")
        Msg().out("\t\tConfiguration options")
        for (key, value) in Config.conf.items():
            Msg().out(key, '=', value)

        Msg().out(80*"-")
        return self.STATUS_OK

    def do_version(self, cmdp):
        """
        version: Print version information
        """
        if cmdp.missing_options():  # syntax error
            return self.STATUS_ERROR

        try:
            Msg().out(f"version: {__version__}")
            Msg().out(f"tarball: {Config.conf['tarball']}")
            Msg().out(f"tarball_release: {Config.conf['tarball_release']}")
        except NameError:
            return self.STATUS_ERROR

        return self.STATUS_OK

    def do_help(self, cmdp):
        """
        Print help information
        """
        cmdp.get("help", "CMD")
        Msg().out(
            """
Syntax:
  udocker  [general_options] <command>  [command_options]  <command_args>

  udocker [-h|--help|help]        :Display this help and exits
  udocker [-V|--version|version]  :Display udocker and tarball version and exits

General options common to all commands must appear before the command:
  -D, --debug                   :Debug
  -q, --quiet                   :Less verbosity
  --insecure                    :Allow insecure non authenticated https
  --repo=<directory>            :Use repository at directory
  --allow-root                  :Allow execution by root NOT recommended
  --config=<conf_file>          :Use configuration <conf_file>

Commands:
  --help [command]              :Command specific help
  showconf                      :Print all configuration options

  search <repo/expression>      :Search dockerhub for container images
  pull <repo/image:tag>         :Pull container image from dockerhub
  create <repo/image:tag>       :Create container from a pulled image
  run <container_id|name>       :Execute created container
  run <repo/image:tag>          :Pull, create and execute container

  images -l                     :List container images
  ps -m -s                      :List created containers
  name <container_id> <name>    :Give name to container
  rmname <name>                 :Delete name from container
  rename <name> <new_name>      :Change container name
  clone <container_id>          :Duplicate container
  rm  <container-id|name>       :Delete container
  rmi <repo/image:tag>          :Delete image

  import <tar> <repo/image:tag> :Import tar file (exported by docker)
  import - <repo/image:tag>     :Import from stdin (exported by docker)
  export -o <tar> <container>   :Export container directory tree to file
  export - <container>          :Export container directory tree to stdin
  load -i <exported-image>      :Load image from file (saved by docker)
  load                          :Load image from stdin (saved by docker)
  save -o <imagefile> <repo/image:tag>  :Save image with layers to file

  inspect -p <repo/image:tag>   :Return low level information on image
  verify <repo/image:tag>       :Verify a pulled image

  protect <repo/image:tag>      :Protect repository
  unprotect <repo/image:tag>    :Unprotect repository
  protect <container>           :Protect container
  unprotect <container>         :Unprotect container

  mkrepo <top-repo-dir>         :Create another repository in location
  setup --execmode=<mode>       :Change container execution mode
  setup --nvidia                :Setup container to use nvidia GPU
  setup --purge                 :clean mountpoints and files created by udocker
  setup --fixperm               :attempt to fix file permissions

  login                         :Login into docker repository
  logout                        :Logout from docker repository

Examples:
  udocker search expression
  udocker search quay.io/expression
  udocker search --list-tags myimage
  udocker pull myimage:mytag
  udocker images
  udocker create --name=mycontainer  myimage:mytag
  udocker ps -m -s
  udocker inspect mycontainer
  udocker inspect -p mycontainer

  udocker run  mycontainer  cat /etc/redhat-release
  udocker run --hostauth --hostenv --bindhome  mycontainer
  udocker run --user=root  mycontainer  yum install firefox
  udocker run --hostauth --hostenv --bindhome mycontainer  firefox
  udocker run --entrypoint="" mycontainer  /bin/bash -i
  udocker run --entrypoint="/bin/bash" mycontainer -i

  udocker clone --name=anotherc mycontainer
  udocker rm anotherc

  udocker mkrepo /data/myrepo
  udocker --repo=/data/myrepo load -i docker-saved-repo.tar
  udocker --repo=/data/myrepo images
  udocker --repo=/data/myrepo run --user=$USER  myimage:mytag

  udocker export -o myimage.tar mycontainer
  udocker import myimage.tar mynewimage
  udocker create --name=mynewc mynewimage
  udocker export --clone -o mycontainer.tar mycontainer
  udocker import --clone mycontainer.tar

Notes:
 * by default the binaries, images and containers are placed in
      $HOME/.udocker
 * by default the following host directories are mounted in the
   container:
      /dev /proc /sys /etc/resolv.conf /etc/host.conf /etc/hostname
 * to prevent the mount of the above directories use:
      run  --nosysdirs  <container>
 * additional host directories to be mounted are specified with:
      run --volume=/data:/mnt --volume=/etc/hosts  <container>
      run --nosysdirs --volume=/dev --volume=/proc  <container>
 * udocker provides several execution modes that offer different
   approaches and technologies to execute containers, they
   can be selected using the setup command. See the setup help.
      udocker setup --execmode=F3 fedx
      udocker setup --execmode=R1 fedx
      udocker setup --execmode=S1 fedx
      udocker setup --help
 * udocker facilitates the usage of nvidia drivers within containers
      udocker setup --nvidia fedx

See: https://github.com/indigo-dc/udocker/blob/master/SUMMARY.md
            """)
        return self.STATUS_OK
