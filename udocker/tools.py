class UdockerTools(object):
    """Download and setup of the udocker supporting tools
    Includes: proot and alternative python modules, these
    are downloaded to facilitate the installation by the
    end-user.
    """

    def __init__(self, localrepo):
        self.localrepo = localrepo        # LocalRepository object
        self._autoinstall = Config.autoinstall  # True / False
        self._tarball = Config.tarball  # URL or file
        self._installinfo = Config.installinfo  # URL or file
        self._install_json = dict()
        self.curl = GetURL()

    def _version_isequal(self, filename):
        """Is version inside file equal to this udocker version"""
        version = FileUtil(filename).getdata().strip()
        return version and version == __version__

    def is_available(self):
        """Are the tools already installed"""
        return self._version_isequal(self.localrepo.libdir + "/VERSION")

    def _download(self, url):
        """Download a file """
        download_file = FileUtil("udockertools").mktmp()
        if Msg.level <= Msg.DEF:
            Msg().setlevel(Msg.NIL)
        (hdr, dummy) = self.curl.get(url, ofile=download_file)
        if Msg.level == Msg.NIL:
            Msg().setlevel()
        try:
            if "200" in hdr.data["X-ND-HTTPSTATUS"]:
                return download_file
        except (KeyError, TypeError, AttributeError):
            pass
        FileUtil(download_file).remove()
        return ""

    def _get_file(self, locations):
        """Get file from list of possible locations file or internet"""
        for url in locations:
            Msg().err("Info: getting file:", url, l=Msg.VER)
            filename = ""
            if "://" in url:
                filename = self._download(url)
            elif os.path.exists(url):
                filename = os.path.realpath(url)
            if filename and os.path.isfile(filename):
                return (filename, url)
        return ("", "")

    def _verify_version(self, tarball_file):
        """verify the tarball version"""
        if not (tarball_file and os.path.isfile(tarball_file)):
            return False
        tmpdir = FileUtil("VERSION").mktmpdir()
        if not tmpdir:
            return False
        cmd = "cd " + tmpdir + " ; "
        cmd += "tar --strip-components=2 -x"
        if Msg.level >= Msg.VER:
            cmd += "v"
        cmd += "zf " + tarball_file + " udocker_dir/lib/VERSION ; "
        status = subprocess.call(cmd, shell=True, close_fds=True)
        if status:
            return False
        status = self._version_isequal(tmpdir + "/VERSION")
        FileUtil(tmpdir).remove()
        return status

    def purge(self):
        """Remove existing files in bin and lib"""
        for f_name in os.listdir(self.localrepo.bindir):
            FileUtil(self.localrepo.bindir + "/" + f_name).register_prefix()
            FileUtil(self.localrepo.bindir + "/" + f_name).remove()
        for f_name in os.listdir(self.localrepo.libdir):
            FileUtil(self.localrepo.libdir + "/" + f_name).register_prefix()
            FileUtil(self.localrepo.libdir + "/" + f_name).remove()

    def _install(self, tarball_file):
        """Install the tarball"""
        if not (tarball_file and os.path.isfile(tarball_file)):
            return False
        cmd = "cd " + self.localrepo.bindir + " ; "
        cmd += "tar --strip-components=2 -x"
        if Msg.level >= Msg.VER:
            cmd += "v"
        cmd += "zf " + tarball_file + " udocker_dir/bin ; "
        cmd += "/bin/chmod u+rx *"
        status = subprocess.call(cmd, shell=True, close_fds=True)
        if status:
            return False
        cmd = "cd " + self.localrepo.libdir + " ; "
        cmd += "tar --strip-components=2 -x"
        if Msg.level >= Msg.VER:
            cmd += "v"
        cmd += "zf " + tarball_file + " udocker_dir/lib ; "
        cmd += "/bin/chmod u+rx *"
        status = subprocess.call(cmd, shell=True, close_fds=True)
        if status:
            return False
        return True

    def _instructions(self):
        """
        Udocker installation instructions are available at:

          https://indigo-dc.gitbooks.io/udocker/content/

        Udocker requires additional tools to run. These are available
        in the tarball that comprises udocker. The tarballs are available
        at the INDIGO-DataCloud repository under tarballs at:

          http://repo.indigo-datacloud.eu/

        Udocker can be installed with these instructions:

        1) set UDOCKER_TARBALL to a remote URL or local filename e.g.

          $ export UDOCKER_TARBALL=http://host/path
          or
          $ export UDOCKER_TARBALL=/tmp/filename

        2) run udocker and installation will proceed

          ./udocker version

        The correct tarball version for this udocker executable is:
        """
        Msg().out(self._instructions.__doc__, __version__, l=Msg.ERR)

    def _get_mirrors(self, mirrors):
        """Get shuffled list of tarball mirrors"""
        if isinstance(mirrors, str):
            mirrors = mirrors.split(" ")
        try:
            random.shuffle(mirrors)
        except NameError:
            pass
        return mirrors

    def get_installinfo(self):
        """Get json containing installation info"""
        (infofile, url) = self._get_file(self._get_mirrors(self._installinfo))
        try:
            with open(infofile, "r") as filep:
                self._install_json = json.load(filep)
            for msg in self._install_json["messages"]:
                Msg().err("Info:", msg)
        except (KeyError, AttributeError, ValueError,
                OSError, IOError) as error:
            Msg().err("Warning: in install information:",
                      error, url, l=Msg.VER)
        return self._install_json

    def install(self, force=False):
        """Get the udocker tarball and install the binaries"""
        if self.is_available() and not force:
            return True
        elif not self._autoinstall and not force:
            Msg().err("Warning: no engine available and autoinstall disabled",
                      l=Msg.WAR)
            return None
        elif not self._tarball:
            Msg().err("Error: UDOCKER_TARBALL not defined")
        else:
            Msg().err("Info: installing", __version__, l=Msg.INF)
            (tarfile, url) = self._get_file(self._get_mirrors(self._tarball))
            if tarfile:
                Msg().err("Info: installing from:", url, l=Msg.VER)
                status = False
                if not self._verify_version(tarfile):
                    Msg().err("Error: wrong tarball version:", url)
                else:
                    status = self._install(tarfile)
                if "://" in url:
                    FileUtil(tarfile).remove()
                    if status:
                        self.get_installinfo()
                if status:
                    return True
            Msg().err("Error: installing tarball:", self._tarball)
        self._instructions()
        return False
