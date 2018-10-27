class ContainerStructure(object):
    """Docker container structure.
    Creation of a container filesystem from a repository image.
    Creation of a container filesystem from a layer tar file.
    Access to container metadata.
    """

    def __init__(self, localrepo, container_id=None):
        self.localrepo = localrepo
        self.container_id = container_id
        self.tag = ""
        self.imagerepo = ""

    def get_container_attr(self):
        """Get container directory and JSON metadata by id or name"""
        if Config.location:
            container_dir = ""
            container_json = []
        else:
            container_dir = self.localrepo.cd_container(self.container_id)
            if not container_dir:
                Msg().err("Error: container id or name not found")
                return(False, False)
            container_json = self.localrepo.load_json(
                container_dir + "/container.json")
            if not container_json:
                Msg().err("Error: invalid container json metadata")
                return(False, False)
        return(container_dir, container_json)

    def _chk_container_root(self, container_id=None):
        """Check container ROOT sanity"""
        if container_id:
            container_dir = self.localrepo.cd_container(container_id)
        else:
            container_dir = self.localrepo.cd_container(self.container_id)
        if not container_dir:
            return 0
        container_root = container_dir + "/ROOT"
        check_list = ["/lib", "/bin", "/etc", "/tmp", "/var", "/usr", "/sys",
                      "/dev", "/data", "/home", "/system", "/root", "/proc", ]
        found = 0
        for f_path in check_list:
            if os.path.exists(container_root + f_path):
                found += 1
        return found

    def create_fromimage(self, imagerepo, tag):
        """Create a container from an image in the repository.
        Since images are stored as layers in tar files, this
        step consists in extracting those layers into a ROOT
        directory in the appropriate sequence.
        first argument: imagerepo
        second argument: image tag in that repo
        """
        self.imagerepo = imagerepo
        self.tag = tag
        image_dir = self.localrepo.cd_imagerepo(self.imagerepo, self.tag)
        if not image_dir:
            Msg().err("Error: create container: imagerepo is invalid")
            return False
        (container_json, layer_files) = self.localrepo.get_image_attributes()
        if not container_json:
            Msg().err("Error: create container: getting layers or json")
            return False
        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))
        container_dir = self.localrepo.setup_container(
            self.imagerepo, self.tag, self.container_id)
        if not container_dir:
            Msg().err("Error: create container: setting up container")
            return False
        self.localrepo.save_json(
            container_dir + "/container.json", container_json)
        status = self._untar_layers(layer_files, container_dir + "/ROOT")
        if not status:
            Msg().err("Error: creating container:", self.container_id)
        elif not self._chk_container_root():
            Msg().err("Warning: check container content:", self.container_id,
                      l=Msg.WAR)
        return self.container_id

    def create_fromlayer(self, imagerepo, tag, layer_file, container_json):
        """Create a container from a layer file exported by Docker.
        """
        self.imagerepo = imagerepo
        self.tag = tag
        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))
        if not container_json:
            Msg().err("Error: create container: getting json")
            return False
        container_dir = self.localrepo.setup_container(
            self.imagerepo, self.tag, self.container_id)
        if not container_dir:
            Msg().err("Error: create container: setting up")
            return False
        self.localrepo.save_json(
            container_dir + "/container.json", container_json)
        status = self._untar_layers([layer_file, ], container_dir + "/ROOT")
        if not status:
            Msg().err("Error: creating container:", self.container_id)
        elif not self._chk_container_root():
            Msg().err("Warning: check container content:", self.container_id,
                      l=Msg.WAR)
        return self.container_id

    def clone_fromfile(self, clone_file):
        """Create a cloned container from a file containing a cloned container
        exported by udocker.
        """
        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))
        container_dir = self.localrepo.setup_container(
            "CLONING", "inprogress", self.container_id)
        if not container_dir:
            Msg().err("Error: create container: setting up")
            return False
        status = self._untar_layers([clone_file, ], container_dir)
        if not status:
            Msg().err("Error: creating container clone:", self.container_id)
        elif not self._chk_container_root():
            Msg().err("Warning: check container content:", self.container_id,
                      l=Msg.WAR)
        return self.container_id

    def _apply_whiteouts(self, tarf, destdir):
        """The layered filesystem od docker uses whiteout files
        to identify files or directories to be removed.
        The format is .wh.<filename>
        """
        cmd = r"tar tf %s '*\/\.wh\.*'" % (tarf)
        proc = subprocess.Popen(cmd, shell=True, stderr=Msg.chlderr,
                                stdout=subprocess.PIPE, close_fds=True)
        while True:
            wh_filename = proc.stdout.readline().strip()
            if wh_filename:
                wh_basename = os.path.basename(wh_filename)
                if wh_basename.startswith(".wh."):
                    rm_filename = destdir + "/" \
                        + os.path.dirname(wh_filename) + "/" \
                        + wh_basename.replace(".wh.", "", 1)
                    FileUtil(rm_filename).remove()
            else:
                try:
                    proc.stdout.close()
                    proc.terminate()
                except(NameError, AttributeError):
                    pass
                break
        return True

    def _untar_layers(self, tarfiles, destdir):
        """Untar all container layers. Each layer is extracted
        and permissions are changed to avoid file permission
        issues when extracting the next layer.
        """
        status = True
        gid = str(os.getgid())
        for tarf in tarfiles:
            if tarf != "-":
                self._apply_whiteouts(tarf, destdir)
            cmd = "umask 022 ; tar -C %s -x " % destdir
            if Msg.level >= Msg.VER:
                cmd += " -v "
            cmd += r" --one-file-system --no-same-owner "
            cmd += r"--no-same-permissions --overwrite -f " + tarf
            cmd += r"; find " + destdir
            cmd += r" \( -type d ! -perm -u=x -exec /bin/chmod u+x {} \; \) , "
            cmd += r" \( ! -perm -u=w -exec /bin/chmod u+w {} \; \) , "
            cmd += r" \( ! -gid " + gid + r" -exec /bin/chgrp " + gid
            cmd += r" {} \; \) , "
            cmd += r" \( -name '.wh.*' -exec "
            cmd += r" /bin/rm -f --preserve-root {} \; \)"
            status = subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                                     close_fds=True)
            if status:
                Msg().err("Error: while extracting image layer")
        return not status

    def _tar(self, tarfile, sourcedir):
        """Create a tar file for a given sourcedir
        """
        cmd = "tar -C %s -c " % sourcedir
        if Msg.level >= Msg.VER:
            cmd += " -v "
        cmd += r" --one-file-system "
        #cmd += r" --xform 's:^\./::' "
        cmd += r" -S --xattrs -f " + tarfile + " . "
        status = subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                                 close_fds=True)
        if status:
            Msg().err("Error: creating tar file:", tarfile)
        return not status

    def _copy(self, sourcedir, destdir):
        """Copy directories
        """
        cmd = "tar -C %s -c " % sourcedir
        if Msg.level >= Msg.VER:
            cmd += " -v "
        cmd += r" --one-file-system -S --xattrs -f - . "
        cmd += r"|tar -C %s -x " % destdir
        cmd += r" -f - "
        status = subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                                 close_fds=True)
        if status:
            Msg().err("Error: copying:", sourcedir, " to ", destdir)
        return not status

    def get_container_meta(self, param, default, container_json):
        """Get the container metadata from the container"""
        if "config" in container_json:
            confidx = "config"
        elif "container_config" in container_json:
            confidx = "container_config"
        if container_json[confidx]  and param in container_json[confidx]:
            if container_json[confidx][param] is None:
                pass
            elif (isinstance(container_json[confidx][param], str) and (
                    isinstance(default, (list, tuple)))):
                return container_json[confidx][param].strip().split()
            elif (isinstance(default, str) and (
                    isinstance(container_json[confidx][param], (list, tuple)))):
                return " ".join(container_json[confidx][param])
            elif (isinstance(default, str) and (
                    isinstance(container_json[confidx][param], dict))):
                return self._dict_to_str(container_json[confidx][param])
            elif (isinstance(default, list) and (
                    isinstance(container_json[confidx][param], dict))):
                return self._dict_to_list(container_json[confidx][param])
            else:
                return container_json[confidx][param]
        return default

    def _dict_to_str(self, in_dict):
        """Convert dict to str"""
        out_str = ""
        for (key, val) in in_dict.iteritems():
            out_str += "%s:%s " % (str(key), str(val))
        return out_str

    def _dict_to_list(self, in_dict):
        """Convert dict to list"""
        out_list = []
        for (key, val) in in_dict.iteritems():
            out_list.append("%s:%s" % (str(key), str(val)))
        return out_list

    def export_tofile(self, clone_file):
        """Export a container creating a tar file of the rootfs
        """
        container_dir = self.localrepo.cd_container(self.container_id)
        if not container_dir:
            Msg().err("Error: container not found:", self.container_id)
            return False
        status = self._tar(clone_file, container_dir + "/ROOT")
        if not status:
            Msg().err("Error: exporting container file system:", self.container_id)
        return self.container_id

    def clone_tofile(self, clone_file):
        """Create a cloned container tar file containing both the rootfs
        and all udocker control files. This is udocker specific.
        """
        container_dir = self.localrepo.cd_container(self.container_id)
        if not container_dir:
            Msg().err("Error: container not found:", self.container_id)
            return False
        status = self._tar(clone_file, container_dir)
        if not status:
            Msg().err("Error: exporting container as clone:", self.container_id)
        return self.container_id

    def clone(self):
        """Clone a container by creating a complete copy
        """
        source_container_dir = self.localrepo.cd_container(self.container_id)
        if not source_container_dir:
            Msg().err("Error: source container not found:", self.container_id)
            return False
        dest_container_id = Unique().uuid(os.path.basename(self.imagerepo))
        dest_container_dir = self.localrepo.setup_container(
            "CLONING", "inprogress", dest_container_id)
        if not dest_container_dir:
            Msg().err("Error: create destination container: setting up")
            return False
        status = self._copy(source_container_dir, dest_container_dir)
        if not status:
            Msg().err("Error: creating container:", dest_container_id)
        elif not self._chk_container_root(dest_container_id):
            Msg().err("Warning: check container content:", dest_container_id,
                      l=Msg.WAR)
        return dest_container_id
