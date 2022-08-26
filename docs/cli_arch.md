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

* `install`      perform default installation
  * (DEFAULT no options or args) download and install udocker to udocker directory, sets $PATH, and all modules to .udocker
  * With config file or setting environment variables will install to custom directories
  * `--from=<url>|<dir>`     URL or local directory with modules
  * `--prefix=<directory>`   installation directory
  * `<module>`               positional args 1 or more

* `showmod`      show installed modules, versions, URLS for download

* `availmod`     show available modules in the catalog
  * (DEFAULT no options or args) downloads metadata.json if it doesn't exist already in `topdir`
  * `--force`                Force download of metadata.json

* `downloadmod`  download tarball modules, so it can be installed offline
  * (DEFAULT no options or args) download udocker and all modules to udocker_install directory
  * With config file or setting environment variables will download to custom directory
  * `--from=<url>|<dir>`     URL or local directory with modules
  * `--prefix=<directory>`   destination download directory
  * `<module>`               positional args 1 or more

* `upgrademod    upgrade module
  * (DEFAULT no options or args) upgrade all modules to udocker_install directory
  * `--from=<url>|<dir>`     URL or local directory with modules
  * `<module>`               positional args 1 or more

* `verifymod`    verify/checksum tarballs
  * `--prefix=<directory>`   destination download directory

* `deletemod`    delete module
  * (DEFAULT no options or args) delete all modules
  * `--prefix=<directory>`   destination download directory
  * `<module>`               positional args 1 or more

* `deletemeta`   delete cached metadata
  * `--prefix=<directory>`   destination download directory
