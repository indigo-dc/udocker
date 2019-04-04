# -*- coding: utf-8 -*-
import os
import string
import getpass
import json

from udocker import __version__
from udocker.msg import Msg
from udocker.docker import DockerIoAPI
from udocker.docker import DockerLocalFileAPI
from udocker.helper.keystore import KeyStore
from udocker.container.structure import ContainerStructure
from udocker.engine.execmode import ExecutionMode
from udocker.engine.nvidia import NvidiaMode
from udocker.tools import UdockerTools


class UdockerCLI(object):
    """Implements most of the command line interface.
    These methods correspond directly to the commands that can
    be invoked via the command line interface.
    """

    def __init__(self, localrepo, conf):
        self.conf = conf
        self.localrepo = localrepo
        self.dockerioapi = DockerIoAPI(localrepo, conf)
        self.dockerlocalfileapi = DockerLocalFileAPI(localrepo, self.conf)
        if self.conf['keystore'].startswith("/"):
            self.keystore = KeyStore(self.conf, self.conf['keystore'])
        else:
            self.keystore = \
                KeyStore(self.conf, self.localrepo.homedir + "/" + self.conf['keystore'])

    def _check_imagespec(self, imagespec, def_imagespec=None):
        """Perform the image verification"""
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

    def do_mkrepo(self, cmdp):
        """
        mkrepo: create a local repository in a specified directory
        mkrepo <directory>
        """
        exit_status = 0
        topdir = cmdp.get("P1")
        if not topdir or not os.path.exists(topdir):
            self.localrepo.setup(topdir)
            if self.localrepo.create_repo():
                exit_status = 0
            else:
                Msg().err("Error: localrepo creation failure: ", topdir)
                exit_status = 1
        else:
            Msg().err("Error: localrepo directory already exists: ", topdir)
            exit_status = 1

        return exit_status

    def _search_print_v1(self, repo_list):
        """Print search results from v1 API"""
        for repo in repo_list["results"]:
            if "is_official" in repo and repo["is_official"]:
                is_official = "[OK]"
            else:
                is_official = "----"
            description = ""
            if "description" in repo and repo["description"] is not None:
                for char in repo["description"]:
                    if char in string.printable:
                        description += char
            Msg().out("%-40.40s %8.8s %s"
                      % (repo["name"], is_official, description))

    def _search_print_v2(self, repo_list):
        """Print catalog results from v2 API"""
        for reponame in repo_list["repositories"]:
            Msg().out("%-40.40s %8.8s"
                      % (reponame, "    "))

    def do_search(self, cmdp):
        """
        search: search dockerhub for container images
        search [options]  <expression>
        -a                                              :do not pause
        --index=https://index.docker.io/v1              :docker index
        --registry=https://registry-1.docker.io         :docker registry
        """
        exit_status = 0
        pause = not cmdp.get("-a")
        index_url = cmdp.get("--index=")
        registry_url = cmdp.get("--registry=")
        expression = cmdp.get("P1")
        if index_url:
            self.dockerioapi.set_index(index_url)
        if registry_url:
            self.dockerioapi.set_registry(registry_url)
        if cmdp.missing_options():         # syntax error
            exit_status = 1
            return exit_status
        Msg().out("%-40.40s %8.8s %s" %
                  ("NAME", "OFFICIAL", "DESCRIPTION"), l=Msg.INF)
        self.dockerioapi.search_init(pause)
        v2_auth_token = self.keystore.get(self.dockerioapi.registry_url)
        self.dockerioapi.set_v2_login_token(v2_auth_token)
        while True:
            repo_list = self.dockerioapi.search_get_page(expression)
            if not repo_list:
                exit_status = 0
                return exit_status
            elif "results" in repo_list:
                self._search_print_v1(repo_list)
            elif "repositories" in repo_list:
                self._search_print_v2(repo_list)
            if pause and not self.dockerioapi.search_ended:
                key_press = raw_input("[press return or q to quit]")
                if key_press in ("q", "Q", "e", "E"):
                    exit_status = 0
                    return exit_status

    def do_load(self, cmdp):
        """
        load: load a container image saved by docker with 'docker save'
        load --input=<docker-saved-container-file>
        load -i <docker-saved-container-file>
        load < <docker-saved-container-file>
        """
        exit_status = 0
        imagefile = cmdp.get("--input=")
        if not imagefile:
            imagefile = cmdp.get("-i=")
            if imagefile is False:
                imagefile = "-"
        if cmdp.missing_options():  # syntax error
            exit_status = 1
            return exit_status
        if not imagefile:
            Msg().err("Error: must specify filename of docker exported image")
            exit_status = 1
            return exit_status
        repos = self.dockerlocalfileapi.load(imagefile)
        if not repos:
            Msg().err("Error: loading failed")
            exit_status = 1
            return exit_status

        for repo_item in repos:
            Msg().out(repo_item)
        return exit_status

    def do_import(self, cmdp):
        """
        import : import image (directory tree) from tar file or stdin
        import <tar-file> <repo/image:tag>
        import - <repo/image:tag>
        --mv                       :if possible move tar-file instead of copy
        --tocontainer              :import to container, no image is created
        --clone                    :import udocker container format with metadata
        --name=<container-name>    :with --tocontainer or --clone to add an alias
        """
        exit_status = 0
        move_tarball = cmdp.get("--mv")
        to_container = cmdp.get("--tocontainer")
        name = cmdp.get("--name=")
        clone = cmdp.get("--clone")
        from_stdin = cmdp.get("-")
        if from_stdin:
            tarfile = "-"
            imagespec = cmdp.get("P1")
            move_tarball = False
        else:
            tarfile = cmdp.get("P1")
            imagespec = cmdp.get("P2")
        if not tarfile:
            Msg().err("Error: must specify tar filename")
            exit_status = 1
            return exit_status
        if cmdp.missing_options():  # syntax error
            exit_status = 1
            return exit_status
        if to_container or clone:
            if clone:
                container_id = self.dockerlocalfileapi.import_clone(
                    tarfile, name)
            else:
                (imagerepo, tag) = self._check_imagespec(imagespec,
                                                         "IMPORTED:unknown")
                container_id = self.dockerlocalfileapi.import_tocontainer(
                    tarfile, imagerepo, tag, name)
            if container_id:
                Msg().out(container_id)
                exit_status = 0
                return exit_status
        else:
            (imagerepo, tag) = self._check_imagespec(imagespec)
            if not imagerepo:
                exit_status = 1
                return exit_status
            if self.dockerlocalfileapi.import_toimage(tarfile, imagerepo, tag,
                                                      move_tarball):
                exit_status = 0
                return exit_status
        Msg().err("Error: importing")
        exit_status = 1
        return exit_status

    def do_export(self, cmdp):
        """
        export : export container (directory tree) to a tar file or stdin
        export -o <tar-file> <container-id>
        export - <container-id>
        -o                         :export to file, instead of stdout
        --clone                    :export in clone (udocker) format
        """
        exit_status = 0
        to_file = cmdp.get("-o")
        clone = cmdp.get("--clone")
        if to_file:
            tarfile = cmdp.get("P1")
            container_id = cmdp.get("P2")
        else:
            tarfile = "-"
            container_id = cmdp.get("P1")

        container_id = self.localrepo.get_container_id(container_id)
        if not container_id:
            Msg().err("Error: invalid container id", container_id)
            exit_status = 1
            return exit_status
        if not tarfile:
            Msg().err("Error: invalid output file name", tarfile)
            exit_status = 1
            return exit_status
        if clone:
            if ContainerStructure(self.localrepo, self.conf,
                                  container_id).clone_tofile(tarfile):
                exit_status = 0
                return exit_status
        else:
            if ContainerStructure(self.localrepo, self.conf,
                                  container_id).export_tofile(tarfile):
                exit_status = 0
                return exit_status
        Msg().err("Error: exporting")
        exit_status = 1
        return exit_status

    def do_clone(self, cmdp):
        """
        clone : create a duplicate copy of an existing container
        clone <source-container-id>
        --name=<container-name>    :add an alias to the cloned container
        """
        exit_status = 0
        name = cmdp.get("--name=")
        container_id = cmdp.get("P1")
        container_id = self.localrepo.get_container_id(container_id)
        if not container_id:
            Msg().err("Error: invalid container id", container_id)
            exit_status = 1
            return exit_status
        if self.dockerlocalfileapi.clone_container(container_id, name):
            Msg().out(container_id)
            exit_status = 0
            return exit_status
        Msg().err("Error: cloning")
        exit_status = 1
        return exit_status

    def do_login(self, cmdp):
        """
        login: authenticate into docker repository e.g. dockerhub
        --username=username
        --password=password
        --registry=https://registry-1.docker.io
        """
        exit_status = 0
        username = cmdp.get("--username=")
        password = cmdp.get("--password=")
        registry_url = cmdp.get("--registry=")
        if registry_url:
            self.dockerioapi.set_registry(registry_url)
        if not username:
            username = raw_input("username: ")
        if not password:
            password = getpass("password: ")
        if password and password == password.upper():
            Msg().err("Warning: password in uppercase",
                      "Caps Lock ?", l=Msg.WAR)
        v2_auth_token = \
            self.dockerioapi.get_v2_login_token(username, password)
        if self.keystore.put(self.dockerioapi.registry_url, v2_auth_token, ""):
            return exit_status
        Msg().err("Error: invalid credentials")
        exit_status = 1
        return exit_status

    def do_logout(self, cmdp):
        """
        logout: authenticate into docker repository e.g. dockerhub
        -a remove all authentication credentials
        --registry=https://registry-1.docker.io
        """
        exit_status = 0
        all_credentials = cmdp.get("-a")
        registry_url = cmdp.get("--registry=")
        if registry_url:
            self.dockerioapi.set_registry(registry_url)
        if all_credentials:
            exit_status = self.keystore.erase()
        else:
            exit_status = self.keystore.delete(self.dockerioapi.registry_url)
        if exit_status == 1:
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
        --index=https://index.docker.io/v1              :docker index
        --registry=https://registry-1.docker.io         :docker registry
        """
        exit_status = 0
        index_url = cmdp.get("--index=")
        registry_url = cmdp.get("--registry=")
        http_proxy = cmdp.get("--httpproxy=")
        (imagerepo, tag) = self._check_imagespec(cmdp.get("P1"))
        if not registry_url and self.keystore.get(imagerepo.split("/")[0]):
            registry_url = imagerepo.split("/")[0]
        if (not imagerepo) or cmdp.missing_options():    # syntax error
            exit_status = 1
            return exit_status
        else:
            if http_proxy:
                self.dockerioapi.set_proxy(http_proxy)
            if index_url:
                self.dockerioapi.set_index(index_url)
            if registry_url:
                self.dockerioapi.set_registry(registry_url)
            v2_auth_token = self.keystore.get(self.dockerioapi.registry_url)
            self.dockerioapi.set_v2_login_token(v2_auth_token)
            if self.dockerioapi.get(imagerepo, tag):
                return exit_status
            else:
                Msg().err("Error: no files downloaded")
        exit_status = 1
        return exit_status

    def do_create(self, cmdp):
        """
        create: extract image layers and create a container
        create [options]  <repo/image:tag>
        --name=xxxx                :set or change the name of the container
        """
        exit_status = 0
        imagespec = cmdp.get("P1")
        name = cmdp.get("--name=")
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status
        container_id = self._create(imagespec)
        if container_id:
            Msg().out(container_id)
            if name and not self.localrepo.set_container_name(container_id,
                                                              name):
                Msg().err("Error: invalid container name may already exist "
                          "or wrong format")
                exit_status = 1
                return exit_status
            exit_status = 0
            return exit_status
        exit_status = 1
        return exit_status

    def _create(self, imagespec):
        """Auxiliary to create(), performs the creation"""
        if not self.dockerioapi.is_repo_name(imagespec):
            Msg().err("Error: must specify image:tag or repository/image:tag")
            return False
        (imagerepo, tag) = self._check_imagespec(imagespec)
        if imagerepo:
            cont_struct = ContainerStructure(self.localrepo, self.conf)
            return cont_struct.create_fromimage(imagerepo, tag)
        return False

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
            }
        }
        for option, cmdp_args in cmd_options.iteritems():
            last_value = None
            for cmdp_fl in cmdp_args["fl"]:
                option_value = cmdp.get(cmdp_fl,
                                        cmdp_args["p2"], cmdp_args["p3"])
                if not exec_engine:
                    continue
                if cmdp_args["act"] == "R":   # action is replace
                    if option_value or last_value is None:
                        exec_engine.opt[option] = option_value
                elif cmdp_args["act"] == "E":   # action is extend
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
        --hostauth                 :bind the host /etc/passwd /etc/group ...
        --nosysdirs                :do not bind the host /proc /sys /run /dev
        --nometa                   :ignore container metadata
        --dri                      :bind directories relevant for dri graphics
        --hostenv                  :pass the host environment to the container
        --cpuset-cpus=<1,2,3-4>    :CPUs in which to allow execution
        --name=<container-name>    :set or change the name of the container
        --bindhome                 :bind the home directory into the container
        --location=<path-to-dir>   :use root tree outside the repository
        --kernel=<kernel-id>       :use this Linux kernel identifier
        --device=/dev/xxx          :pass device to container (R1 mode only)

        Only available in Pn execution modes:
        --publish=<hport:cport>    :map container TCP/IP <cport> into <hport>
        --publish-all              :bind and connect to random ports

        run <container-id-or-name> executes an existing container, previously
        created from an image by using: create <repo/image:tag>

        run <repo/image:tag> always creates a new container from the image
        if needed the image is pulled. This is slow and may waste storage.
        """
        exit_status = 0
        self._get_run_options(cmdp)
        container_or_image = cmdp.get("P1")
        self.conf['location'] = cmdp.get("--location=")
        delete = cmdp.get("--rm")
        name = cmdp.get("--name=")
        #
        if cmdp.missing_options(): # syntax error
            exit_status = 1
            return exit_status
        if self.conf['location']:
            container_id = ""
        elif not container_or_image:
            Msg().err("Error: must specify container_id or image:tag")
            exit_status = 1
            return exit_status
        else:
            container_id = self.localrepo.get_container_id(container_or_image)
            if not container_id:
                (imagerepo, tag) = self._check_imagespec(container_or_image)
                if (imagerepo and
                        self.localrepo.cd_imagerepo(imagerepo, tag)):
                    container_id = self._create(imagerepo+":"+tag)
                if not container_id:
                    self.do_pull(cmdp)
                    if self.localrepo.cd_imagerepo(imagerepo, tag):
                        container_id = self._create(imagerepo+":"+tag)
                    if not container_id:
                        Msg().err("Error: image or container not available")
                        exit_status = 1
                        return exit_status
            if name and container_id:
                if not self.localrepo.set_container_name(container_id, name):
                    Msg().err("Error: invalid container name format")
                    exit_status = 1
                    return exit_status
        exec_engine = ExecutionMode(self.conf, self.localrepo,
                                    container_id).get_engine()
        if not exec_engine:
            Msg().err("Error: no execution engine for this execmode")
            exit_status = 1
            return exit_status
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
        exit_status = 0
        verbose = cmdp.get("-l")
        dummy = cmdp.get("--no-trunc")
        dummy = cmdp.get("--all")
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status
        images_list = self.localrepo.get_imagerepos()
        Msg().out("REPOSITORY", l=Msg.INF)
        for (imagerepo, tag) in images_list:
            prot = (".", "P")[
                self.localrepo.isprotected_imagerepo(imagerepo, tag)]
            Msg().out("%-60.60s %c" % (imagerepo + ":" + tag, prot))
            if verbose:
                imagerepo_dir = self.localrepo.cd_imagerepo(imagerepo, tag)
                Msg().out("  %s" % (imagerepo_dir))
                layers_list = self.localrepo.get_layers(imagerepo, tag)
                if layers_list:
                    for (layer_name, size) in layers_list:
                        file_size = size / (1024 * 1024)
                        if not file_size and size:
                            file_size = 1
                        Msg().out("    %s (%d MB)" %
                                  (layer_name.replace(imagerepo_dir, ""),
                                   file_size))
        return exit_status

    def do_ps(self, cmdp):
        """
        ps: list containers
        """
        exit_status = 0
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status
        containers_list = self.localrepo.get_containers_list(False)
        Msg().out("%-36.36s %c %c %-18s %-s" %
                  ("CONTAINER ID", "P", "M", "NAMES", "IMAGE"), l=Msg.INF)
        for (container_id, reponame, names) in containers_list:
            prot = (".", "P")[
                self.localrepo.isprotected_container(container_id)]
            write = ("R", "W", "N", "D")[
                self.localrepo.iswriteable_container(container_id)]
            Msg().out("%-36.36s %c %c %-18s %-s" %
                      (container_id, prot, write, names, reponame))

        return exit_status

    def do_rm(self, cmdp):
        """
        rm: delete a container
        rm <container_id>
        """
        exit_status = 0
        container_id_list = cmdp.get("P*")
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status
        if not container_id_list:
            Msg().err("Error: must specify image:tag or repository/image:tag")
            exit_status = 1
            return exit_status

        for container_id in cmdp.get("P*"):
            container_id = self.localrepo.get_container_id(container_id)
            if not container_id:
                Msg().err("Error: invalid container id", container_id)
                exit_status = 1
                continue
            else:
                if self.localrepo.isprotected_container(container_id):
                    Msg().err("Error: container is protected")
                    exit_status = 1
                    continue
                Msg().out("Info: deleting container:",
                          str(container_id), l=Msg.INF)
                if not self.localrepo.del_container(container_id):
                    Msg().err("Error: deleting container")
                    exit_status = 1

        return exit_status

    def do_rmi(self, cmdp):
        """
        rmi: delete an image in the local repository
        rmi [options] <repo/image:tag>
        -f                          :force removal
        """
        exit_status = 0
        force = cmdp.get("-f")
        imagespec = str(cmdp.get("P1"))
        (imagerepo, tag) = self._check_imagespec(imagespec)
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status
        if not imagerepo:
            exit_status = 1
            return exit_status
        else:
            if self.localrepo.isprotected_imagerepo(imagerepo, tag):
                Msg().err("Error: image repository is protected")
                exit_status = 1
                return exit_status
            Msg().out("Info: deleting image:", imagespec, l=Msg.INF)
            if not self.localrepo.del_imagerepo(imagerepo, tag, force):
                Msg().err("Error: deleting image")
                exit_status = 1
                return exit_status

        return exit_status

    def do_protect(self, cmdp):
        """
        protect: protect a container or image against deletion
        protect <container-id or repo/image:tag>
        """
        exit_status = 0
        arg = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status

        if self.localrepo.get_container_id(arg):
            if not self.localrepo.protect_container(arg):
                Msg().err("Error: protect container failed")
                exit_status = 1
                return exit_status
            exit_status = 0
        else:
            (imagerepo, tag) = self._check_imagespec(arg)
            if imagerepo:
                if self.localrepo.protect_imagerepo(imagerepo, tag):
                    exit_status = 0
                    return exit_status
            Msg().err("Error: protect image failed")
            exit_status = 1

        return exit_status

    def do_unprotect(self, cmdp):
        """
        unprotect: remove delete protection
        unprotect <container-id or repo/image:tag>
        """
        exit_status = 0
        arg = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status

        if self.localrepo.get_container_id(arg):
            if not self.localrepo.unprotect_container(arg):
                Msg().err("Error: unprotect container failed")
                exit_status = 1
                return exit_status
            exit_status = 0
        else:
            (imagerepo, tag) = self._check_imagespec(arg)
            if imagerepo:
                if self.localrepo.unprotect_imagerepo(imagerepo, tag):
                    exit_status = 0
                    return exit_status
            Msg().err("Error: unprotect image failed")
            exit_status = 1

        return exit_status

    def do_name(self, cmdp):
        """
        name: give a name alias to a container
        name <container-id> <container-name>
        """
        exit_status = 0
        container_id = cmdp.get("P1")
        name = cmdp.get("P2")
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status
        if not (self.localrepo.get_container_id(container_id) and name):
            Msg().err("Error: invalid container id or name")
            exit_status = 1
            return exit_status
        if not self.localrepo.set_container_name(container_id, name):
            Msg().err("Error: invalid container name")
            exit_status = 1
            return exit_status

        return exit_status

    def do_rmname(self, cmdp):
        """
        rmname: remove name from container
        rmname <container-name>
        """
        exit_status = 0
        name = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status
        if not name:
            Msg().err("Error: invalid container id or name")
            exit_status = 1
            return exit_status
        if not self.localrepo.del_container_name(name):
            Msg().err("Error: removing container name")
            exit_status = 1
            return exit_status

        return exit_status

    def do_inspect(self, cmdp):
        """
        inspect: print container metadata JSON from an imagerepo or container
        inspect <container-id or repo/image:tag>
        -p                         :print container directory path on host
        """
        exit_status = 0
        container_dir = ""
        container_or_image = cmdp.get("P1")
        container_id = self.localrepo.get_container_id(container_or_image)
        print_dir = cmdp.get("-p")
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status

        if container_id:
            (container_dir, container_json) = ContainerStructure(
                self.localrepo, self.conf, container_id).get_container_attr()
        else:
            (imagerepo, tag) = self._check_imagespec(container_or_image)
            if self.localrepo.cd_imagerepo(imagerepo, tag):
                (container_json, dummy) = self.localrepo.get_image_attributes()
            else:
                exit_status = 1
                return exit_status

        if print_dir:
            if container_id and container_dir:
                Msg().out(str(container_dir) + "/ROOT")
                exit_status = 0
                return exit_status
        elif container_json:
            try:
                Msg().out(json.dumps(container_json, sort_keys=True,
                                     indent=4, separators=(',', ': ')))
            except (IOError, OSError, AttributeError, ValueError, TypeError):
                Msg().out(container_json)
            exit_status = 0
            return exit_status

        exit_status = 1
        return exit_status

    def do_verify(self, cmdp):
        """
        verify: verify an image
        verify <repo/image:tag>
        """
        exit_status = 0
        (imagerepo, tag) = self._check_imagespec(cmdp.get("P1"))
        if (not imagerepo) or cmdp.missing_options():  # syntax error
            exit_status = 1
            return exit_status
        else:
            Msg().out("Info: verifying: %s:%s" % (imagerepo, tag), l=Msg.INF)
            if not self.localrepo.cd_imagerepo(imagerepo, tag):
                Msg().err("Error: selecting image and tag")
                exit_status = 1
                return exit_status
            elif self.localrepo.verify_image():
                Msg().out("Info: image Ok", l=Msg.INF)
                exit_status = 0
                return exit_status
        Msg().err("Error: image verification failure")
        exit_status = 1
        return exit_status

    def do_setup(self, cmdp):
        """
        setup: change container execution settings
        setup [options] <container-id>
        --execmode=<mode>          :select execution mode from below
        --force                    :force setup change
        --nvidia                   :add NVIDIA libraries and binaries
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
        S1: singularity, requires a local installation of singularity,
            if singularity is available in the PATH udocker will use
            it to execute the container
        """
        exit_status = 0
        container_id = cmdp.get("P1")
        xmode = cmdp.get("--execmode=")
        force = cmdp.get("--force")
        nvidia = cmdp.get("--nvidia")
        if cmdp.missing_options():               # syntax error
            exit_status = 1
            return exit_status

        if not self.localrepo.cd_container(container_id):
            Msg().err("Error: invalid container id")
            exit_status = 1
            return exit_status
        elif xmode and self.localrepo.isprotected_container(container_id):
            Msg().err("Error: container is protected")
            exit_status = 1
            return exit_status

        if nvidia:
            nvidia_mode = NvidiaMode(self.conf, self.localrepo, container_id)
            nvidia_mode.set_mode(force)
        exec_mode = ExecutionMode(self.conf, self.localrepo, container_id)

        if xmode:
            return exec_mode.set_mode(xmode.upper(), force)

        Msg().out("execmode: %s" % (exec_mode.get_mode()))
        return exit_status

    def do_install(self, cmdp):
        """
        install: install udocker and its tools
        install [options]
        --force                    :force reinstall
        --purge                    :remove files (be careful)
        """
        exit_status = 0
        if cmdp is not None:
            force = cmdp.get("--force")
            purge = cmdp.get("--purge")
        else:
            force = False
            purge = False

        utools = UdockerTools(self.localrepo, self.conf)
        if purge:
            utools.purge()

        status = utools.install(force)
        if status is not None and not status:
            Msg().err("Error: installation of udockertools failed")
            exit_status = 1
            return exit_status

        Msg().err("Info: installation of udockertools successful", l=Msg.VER)
        return exit_status

    def do_listconf(self, cmdp):
        """
        listconf: Print all configuration options
        """
        exit_status = 0
        Msg().out(80*"-")
        for varopt in self.conf:
            Msg().out(varopt + ' = ', self.conf[varopt])
        Msg().out(80*"-")
        return exit_status

    def do_version(self, cmdp):
        """
        version: Print version information
        """
        exit_status = 0
        try:
            Msg().out("%s %s" % ("version:", __version__))
            Msg().out("%s %s" % ("tarball:", self.conf['tarball']))
            Msg().out("%s %s" % ("tarball_release:", self.conf['tarball_release']))
        except NameError:
            exit_status = 1
            return exit_status

        return exit_status

    def do_help(self, cmdp):
        """
        Print help information
        """
        exit_status = 0
        Msg().out(
            """
Syntax:
  udocker  [general_options] <command>  [command_options]  <command_args>

  udocker [-h|--help|help]        :Display this help and exits
  udocker [-V|--version|version]  :Display udocker version and tarball version and exits

General options common to all commands must appear before the command:
  -D, --debug                   :Debug
  -q, --quiet                   :Less verbosity
  --allow-root                  :Allow udocker to run as root
  --repo=<directory>            :Use repository at directory

  -c <conf_file>
  --config=<conf_file>          :Use configuration <conf_file>

Commands:
  help [command]                :Command specific help
  listconf                      :Print all configuration options

  search <repo/image:tag>       :Search dockerhub for container images
  pull <repo/image:tag>         :Pull container image from dockerhub
  images                        :List container images
  create <repo/image:tag>       :Create container from a pulled image
  ps                            :List created containers
  rm  <container>               :Delete container
  run <container>               :Execute container
  inspect <container>           :Low level information on container
  name <container_id> <name>    :Give name to container
  rmname <name>                 :Delete name from container

  rmi <repo/image:tag>          :Delete image
  rm <container-id>             :Delete container
  import <tar> <repo/image:tag> :Import tar file (exported by docker)
  import - <repo/image:tag>     :Import from stdin (exported by docker)
  load -i <exported-image>      :Load image from file (saved by docker)
  load                          :Load image from stdin (saved by docker)
  export -o <tar> <container>   :Export container rootfs to file
  export - <container>          :Export container rootfs to stdin
  inspect <repo/image:tag>      :Return low level information on image
  verify <repo/image:tag>       :Verify a pulled image
  clone <container>             :duplicate container

  protect <repo/image:tag>      :Protect repository
  unprotect <repo/image:tag>    :Unprotect repository
  protect <container>           :Protect container
  unprotect <container>         :Unprotect container

  mkrepo <topdir>               :Create repository in another location
  setup                         :Change container execution settings
  login                         :Login into docker repository
  logout                        :Logout from docker repository

Examples:
  udocker search fedora
  udocker pull fedora
  udocker create --name=fed  fedora
  udocker run  fed  cat /etc/redhat-release
  udocker run --hostauth --hostenv --bindhome  fed
  udocker run --user=root  fed  yum install firefox
  udocker run --hostauth --hostenv --bindhome fed   firefox
  udocker run --hostauth --hostenv --bindhome fed   /bin/bash -i
  udocker run --user=root  fed  yum install cheese
  udocker run --hostauth --hostenv --bindhome --dri fed  cheese
  udocker --repo=/home/x/.udocker  images
  udocker -D run --user=1001:5001  fedora
  udocker export -o fedora.tar fedora
  udocker import fedora.tar myfedoraimage
  udocker create --name=myfedoracontainer myfedoraimage
  udocker export -o fedora_all.tar --clone fedora
  udocker import --clone fedora_all.tar

Notes:
  * by default the binaries, images and containers are placed in
       $HOME/.udocker
  * by default the following host directories are mounted in the
    container:
       /dev /proc /sys
       /etc/resolv.conf /etc/host.conf /etc/hostname
  * to prevent the mount of the above directories use:
       run  --nosysdirs  <container>
  * additional host directories to be mounted are specified with:
       run --volume=/data:/mnt --volume=/etc/hosts  <container>
       run --nosysdirs --volume=/dev --volume=/proc  <container>

See: https://github.com/indigo-dc/udocker/blob/master/SUMMARY.md
            """)
        return exit_status
