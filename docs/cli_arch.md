# Command Line Interface definition

New commands for the CLI of udocker

Usage:

```bash
udocker |GENERAL_OPTIONS| COMMAND |SPEC_OPTIONS and ARGS|
```

**General Options**:

```bash
-h, --help                    help, usage
-V, --version                 show version
-v N, --verbose=N             verbosity level 0 (quiet) - 5 (debug)
-q, --quiet                   quiet (verbosity level 0)
-c conffile, --conf=conffile  use configuration file
```

**Commands, specific options and positional arguments**:

* `install`: Perform default modules installation: proot for host arch and kernel, fakechroot and
  its dependency patchelf:
  * (DEFAULT no options or args) download and install default modules to udocker directory
  * With config file or setting environment variables will install to custom directories
  * `--force`                Force installation of modules
  * `--upgrade`              Upgrade installed of modules
  * `--from=<url>|<dir>`     URL or local directory with modules tarball
  * `--prefix=<directory>`   modules installation directory
  * `<module>`               positional args 1 or more

* `rmmod`: Remove one or more installed modules
  * (DEFAULT no options or args) delete all modules
  * `--prefix=<directory>`   destination install directory
  * `<module>`               positional args one or more

* `availmod`: Show available modules in the catalog - metadata.json:
  * (DEFAULT no options or args) downloads metadata.json if it doesn't exist already in `topdir`
  * `--force`                Force download of metadata.json

* `rmmeta`: Remove cached metadata.json

* `downloadtar`: Download tarballs with modules and verifies sha256sum, so it can be installed
  offline
  * (DEFAULT no options or args) download tarballs proot for host arch and kernel, fakechroot and
  its dependency patchelf.
  * With config file or setting environment variables will download to custom directory
  * `--force`                Force the download
  * `--from=<url>|<dir>`     URL or local directory with modules, default is given in metadata.json.
  * `--prefix=<directory>`   destination download directory, default is `topdir/tar`
  * `<module>`               positional args one or more

* `rmtar`: Remove one or more tarballs
  * (DEFAULT no options or args) remove all tarballs
  * `--prefix=<directory>`   destination download directory
  * `<module>`               positional args one or more, module name corresponding to the tarball

* `showmod`: Show installed modules and all information from metadata.json.

* `verifytar`: Verify/checksum downloaded tarballs, sha256
  * `--force`                Force the download
  * `--prefix=<directory>`   Destination download directory, no trailing /
