# Changelog

## udocker (1.3.2)

* fix missing f (format) for string
* fix bugs with dict .items()
* solving several pylint issues
* remove use2to3, fix issue #358

## udocker (1.3.1)

* Add --entrypoint to run --help
* Set docker hub registry registry-1.docker.io
* Fix repository name in search --list-tags
* Improve tests: udocker_test.sh and udocker_test-run.sh
* Documentation revision and improvements
* Add licenses and licenses notice to documentation
* Add test instructions
* Issues with --allow-root in Python 3.8
* Add security policy SECURITY.md
* Remove old Python 2 tests
* Fix configuration hierarchy, configuration files
* Update documentation: README, user and install manuals
* Fix sqa and config

## udocker (1.3.0)

* Prepare to move the stable code for Python 3 and Python 2 >= 2.6 to master
* Installation procedure changed since 1.1.x series see the `installation_manual`
* Improve user and installation documentation
* Extract documentation upon installation
* Add codemeta.json, metadata for the software
* Add support for `faccessat2()` in Pn and Fn execution modes
* Fix support for `newfstatat()` in Pn execution modes
* Add Fn libraries for Fedora 34 and Ubuntu 21.04
* Remove broken links in FileUtil.remove()
* update minimum udocker tools tarball to 1.2.8
* Cmd and entrypoint metadata and arguments processing changed to mimic docker
* Improve removal of files and links in install and filebind restore
* Add follow location option to GetURL()
* Implement use of `--entrypoint=<cmd>` to force execution of command
  * closes: #306
* Implement use of `--entrypoint=""` to bypass entrypoint in metadata
  * closes: #306

## udocker (1.2.9)

* method Unshare.unshare os.strerror() takes one argument,
  * closes: #254
* Add unit test for #254
* Method chown udocker.utils.fileutil FileUtil
  * closes: #276
* Several fixes of unit tests and pylint
* Fix confusion between exit code 0 and inferred False
* Dereference on `safe_prefixes`
* untar exclude dev
* Fix rmi for referenced layers
* Set default for `PROOT_TMP_DIR`
* sysdir mountpoint not found and set tmpdir
* Update installation instructions
* Improve `oskernel_isgreater()`
* Improve `osinfo()`
* Fix repository login/logout
* Improve keystore logic
* Fix pull /v2

## udocker (1.2.8b2)

* Fix Rn modes to enable containers execution from readonly dirs
* Documentation centralized installation and readonly setups
* Fix handling of dockerhub repository names in /v2
* Improve documentation and algn with 1.1.8b2
* Add credits
* Fix delete of paths with symlinks
  * closes: #267, #265
* Fix issues with login credentials
  * closes: #310
* Fix pull images from docker hub in Termux
  * closes: #307 
* Fix issues on running udocker in googlecolab
  * closes: #286
* Fix execution with Pn modes in alternate /tmp
  * closes: #284
* Add conditional delay-directory-restore to untar layers
* Add exclude of whiteouts on layer untar
* Add --nobanner to udocker run

## udocker (1.2.7)

* Major restructuring of the code
* Major restructuring of the unit tests
* Porting to Python 3, still supports python 2.7
* all fixes up to previous 1.1.7 version have been applied
* added scripts tests udocker: `utils/udocker_test.sh utils/udocker_test-run.sh`

## udocker (1.1.7)

* Fix P1 when Linux 4.8.0 SECCOMP is backported, affects newer CentOS 7 
  * closes: #282
* Check for file ownership on remove wrongly follows symlinks 
  * closes: #266, #267
* udocker unexpectedly uses P1 exec mode instead of P2
  * closes: #274
* Allow passing of `PROOT_TMP_DIR` environment variable
  * closes: #284

## udocker (1.1.6)

* Complete fix for of ELF paths in modes Fn for $ORIGIN:$ORIGIN
  * closes: #255

## udocker (1.1.5)

* Preliminary fix for of ELF paths in modes Fn for $ORIGIN:$ORIGIN
* Add Fn libraries for Ubuntu20, Fedora32, Fedora33
* Add Fn libraries for Alpine 3.12, 3.13

## udocker (1.1.4-1)

* Fix run --location
* Fix udocker integrated help
* Fix naming of containers
* Improve parsing of image names
* Documentation improvements
* `os._exit` from Unshare.unshare()
* Disable `FAKECHROOT_DISALLOW_ENV_CHANGES` in F4 mode

## udocker (1.1.4)

* Use hub.docker.com as default registry
* Search using v1 and v2 APIs
* Implement API /v2/search/repositories
* Adjust search results to screen size
* List container size with ps -s
* List container execution modes with ps -m
* Added support for nameat() and statx() in Pn and Fn modes
* Added Fn libraries for Ubuntu18, Ubuntu19, Fedora29, Fedora30, Fedora31, CentOS8
* Added Fn libraries for Alpine 3.8, 3.9, 3.10, 3.11
* Added support for sha512 hashes
* Added support for opaque whiteouts
* Added search --list-tags to available tags for a given repository
* Add CLI support for image names in format host/repository:tag
* Support for fake root in Sn execution modes via --user=root
* Improve verify of loaded/pulled images
* Improve handling of mountpoints
* Added --containerauth to enable direct use of the container passwd and group
* Added support for file mount bindings in singularity
* Added `UDOCKER_USE_PROOT_EXECUTABLE` env var to select proot location
* Added `UDOCKER_USE_RUNC_EXECUTABLE` env var to select runc location
* Added `UDOCKER_USE_SINGULARITY_EXECUTABLE` env var to select singularity
* Added `UDOCKER_DEFAULT_EXECUTION_MODE` env var to select default execution mode
* Added R2 and R3 execution modes for PRoot overlay execution in runc
* Added setup --purge for cleanup of mountpoints and files 
* Added setup --fixperms to fix container file permissions
* Added run --env-file= to load file with environment variables
* Improve file and directory binding support for Singularity and runc
* Add command rename for renaming of containers
* Create processes without shell context
* Safer parsing of config files and removal of directories
* Improve installation
* Improved fix of SECCOMP accelerated mode for P1 mode
* Added loading and handling of container images in OCI format
* Fixes for udocker in ARM aarch64
* Fix processing of --dri in Sn mode
  * closes: #241
* Improve handling of container and host authentication
  * partially addresses: #239
* Fixes to address authentication and redirects in pull
  * closes: #225, #230
* Added minimal support to load OCI images
  * closes: #111
* Added Pn support for newer distributions
  * closes: #192
* Improve the installation of udockertools
  * closes: #220, #228
* Read environment variables from file with --env-file=
  * closes: #212
* Prepare for pypy
  * closes: #211
* Fixes for verification of container images
  * closes: #209
* Fix command line processing for "-" in argument
  * closes: #202
* Fix file protections on extraction making files u+r
  * closes: #202, #206
* Fix comparison of kernel versions having non-integers
  * closes: #183
* Support for both manifest V2 schema 1 and schema 2
  * closes: #218, #225
* Further improved pathname translation in Fn modes
  * closes: #160
* Implement save images in docker format
  * closes: #74
* useradd and groupadd not working in containers
  * closes: #141
* fix return code when exporting to stdin
  * closes: #202

## udocker (1.1.3)

* Support for nvidia drivers on ubuntu
  * closes: #162
* Installation improvements
  * closes: #166
* Fix issue on Fn mode symlink convertion
  * partially addresses: #160

## udocker (1.1.2)

* Improve parsing of quotes in the command line
  * closes: #98
* Fix version command to exit with 0
  * closes: #107
* Add kill-on-exit to proot on Pn modes
* Improve download of udocker utils
* Handle authentication headers when pulling 
  * closes: #110
* Handle of redirects when pulling
* Fix registries table
* Support search quay.io
* Fix auth header when no standard Docker registry is used
* Add registry detection on image name
* Add --version option
* Force python2 as interpreter
  * closes: #131
* Fix handling of volumes in metadata
* Handle empty metadata
* Fix http proxy functionality
  * closes: #115
* Ignore --no-trunc and --all in the images command
  * closes: #108
* Implement verification of layers in manifest
* Add --nvidia to support GPUs and related drivers
* Send download messages to stderr
* Enable override of curl executable
* Fix building on CentOS 6
  * closes: #157
* Mitigation for upstream limitation in runC without tty
  * closes: #132
* Fix detection of executable with symlinks in container
  * closes: #118
* Updated runC to v1.0.0-rc5
* Experimental support for Alpine in Fn modes
* Improve pathname translation in Fn modes for mounted dirs
  * partially addresses: #160

## udocker (1.1.1)

* New execution engine using singularity
* Updated documentation with OpenMPI information and examples
* Additional unit tests
* Redirect messages to stderr
* Improved parsing of quotes in the command line
  * closes: #87
* Allow override of the HOME environment variable
* Allow override of libfakechroot.so at the container level
* Automatic selection of libfakechroot.so from container info
* Improve automatic install
* Enable resetting prefix paths in Fn modes in remote hosts
* Do not set `AF_UNIX_PATH` in Fn modes when the host /tmp is a volume
* Export containers in both docker and udocker format
* Import containers docker and udocker format
* Load, import and export to/from stdin/stdout
* Clone existing containers
* Support for TCP/IP port remap in execution modes Pn
* Fix run with basenames failing
  * closes: #89
* Allow run as root flag
  * closes: #91

## udocker (1.1.0)

* Support image names prefixed by registry similarly to docker 
* Add execution engine selection logic
* Add fr execution engine based on shared library interception
* Add rc execution engine based on rootless namespaces
* Improve proot tmp files cleanup on non ext filesystems
* Improve search returning empty on Docker repositories
* Improve runC execution portability 
* Add environment variable `UDOCKER_KEYSTORE`
  * closes: #75
* Prevent creation of .udocker when `UDOCKER_KEYSTORE` is used
  * closes: #75

## udocker (1.0.4)

* Documentation fixes

## udocker (1.0.3)

* Support for import Docker containers in newer metadata structure
* Improve the command line parsing
* Improve temporary file handling and removal
* Support for additional execution engines to be provided in the future
* Improved parsing of entrypoint and cmd metadata
  * closes: #53
* Increase name alias length
  * closes: #52
* Add support for change dir into volume directories
  * closes: #51
* Fix deletion of files upon container import
  * closes: #50
* Fix exporting of host environment variables to the containers
  * closes: #48
* Change misleading behavior of import tarball from move to copy
  * closes: #44
* Fix validation of volumes specification
  * closes: #43

## udocker (1.0.2)

* Improve download on repositories that fail authentication on /v2
* Improve run verification of binaries with recursive symbolic links
* Improve accelerated seccomp on kernels >= 4.8.0
  * closes: #40

## udocker (1.0.1)

* Minor bugfixes
* Executable name changed from udocker.py to udocker
* Added support for login into docker repositories
* Added support for private repositories
* Added support for listing of v2 repositories catalog
* Added checksum verification for sha256 layers
* Improved download handling for v1 and v2 repositories
* Improved installation tarball structure
* Insecure flag fixed
* Address seccomp change introduced on kernels >= 4.8.0
* Utilities for packaging
* Improved verbose levels, messaging and output
  * closes: #24, #23
* Fully implement support for registry selection --registry parameter
  * closes: #29
* Provide support for private repositories e.g. gitlab registries
  * closes: #30
* Provide --insecure command line parameter for SSL requests
  * closes: #31

## udocker (1.0.0)

* Initial version
