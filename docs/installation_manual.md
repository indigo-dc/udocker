# Installation and configuration manual

In most cases the end user can download and execute udocker without
system administrator intervention. udocker itself is written in Python, but
also uses external binaries and libraries to provide a chroot like
environment where containers are executed in user space. These tools do not
require any privileges and constitute the udocker tools and libraries for
engines that is downloaded and installed by udocker itself.

Redistribution, commercial use and code changes must regard all licenses
shipped with udocker. For more information see
[section 6 External tools and libraries](#6-external-tools-and-libraries).

## 1. Dependencies

The udocker dependencies are minimal and should be supported by most Linux installations.
udocker requires:

* Python 3 or alternatively Python >= 2.6
* pycurl or alternatively the curl command
* python hashlib or alternatively the openssl command
* tar
* find
* chmod
* chgrp
* ldconfig (only used by the Fn execution modes)

## 2. Installation

### 2.1. Install from a released version

Download a release tarball from <https://github.com/indigo-dc/udocker/releases>:

```bash
wget https://github.com/indigo-dc/udocker/releases/download/v1.3.2/udocker-1.3.2.tar.gz
tar zxvf udocker-1.3.2.tar.gz
export PATH=`pwd`/udocker:$PATH
```

Alternatively use `curl` instead of `wget` as follows:

```bash
curl -L https://github.com/indigo-dc/udocker/releases/download/v1.3.2/udocker-1.3.2.tar.gz \
  > udocker-1.3.2.tar.gz
tar zxvf udocker-1.3.2.tar.gz
export PATH=`pwd`/udocker:$PATH
```

udocker executes containers using external tools and libraries that
are enhanced and packaged for use with udocker. For more information see
[section 6 External tools and libraries](#6-external-tools-and-libraries).
Therefore to complete the installation invoke `udocker install` to download
and install the required tools and libraries.

```bash
udocker install
```

### 2.2. Install from the GitHub repositories

To install the latest stable code from the github `master` branch:

```bash
git clone --depth=1 https://github.com/indigo-dc/udocker.git
(cd udocker/udocker; ln -s maincmd.py udocker)  
export PATH=`pwd`/udocker/udocker:$PATH
```

Alternatively, install the latest development code from the github `devel3` branch:

```bash
git clone -b devel3 --depth=1 https://github.com/indigo-dc/udocker.git
(cd udocker/udocker; ln -s maincmd.py udocker)  
export PATH=`pwd`/udocker/udocker:$PATH
```

udocker executes containers using external tools and libraries that
are enhanced and packaged for use with udocker. For more information see
[section 6 External tools and libraries](#6-external-tools-and-libraries).
Therefore to complete the installation invoke `udocker install` to download
and install the required tools and libraries.

```bash
udocker install
```

### 2.3. Install from PyPI using pip

For installation with pip it is advisable to setup a Python3 virtual environment
before proceeding, see
[Creating a virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment).

```bash
python3 -m venv udockervenv
source udockervenv/bin/activate
pip install udocker
```

The udocker command will be `udockervenv/bin/udocker`.

udocker executes containers using external tools and libraries that
are enhanced and packaged for use with udocker. For more information see
[section 6 External tools and libraries](#6-external-tools-and-libraries).
Therefore to complete the installation invoke `udocker install` to download
and install the required tools and libraries.

```bash
udocker install
```

### 2.4. Install without outbound network access

When the installation is attempted without having outbound network connectivity,
the installation of the binary tools and libraries with `udocker install` will
fail the download step. The solution is to fetch the the tarball in advance
and then install the tools and libraries directly from the tarball file.

The tarballs containing the tools and libraries are available at <https://github.com/jorge-lip/udocker-builds>.

First, download a tarball file using:

```bash
curl -L https://github.com/jorge-lip/udocker-builds/raw/master/tarballs/udocker-englib-1.2.8.tar.gz > udocker-englib-1.2.8.tar.gz
```

Second, transfer the udocker code plus the tarball containing the tools and
libraries to the target destination host.

Finally perform the `udocker install` step using the transferred tarball file.

```bash
export UDOCKER_TARBALL=udocker-englib-1.2.8.tar.gz
udocker install
```

The environment variable `UDOCKER_TARBALL` can also point to an URL to fetch
the tarball from a specific or alternate location. To fetch from multiple
possible locations for redundancy the environment variable `UDOCKER_TARBALL`
can contain multiple URLs separated by a blank.

```bash
export UDOCKER_TARBALL="https://... https://... http://..."
udocker install
```

### 2.5. Force the re-installation of the tools and libraries

To force download and re-installation of the udocker tools and libraries.
Invoke `udocker install` with the flag `--force`:

```bash
udocker install --force
```

## 3. Configuration

The configuration of udocker has the following hierarchy:

1. The default configuration options are set in the `conf` dictionary in the `Config` class.
2. If a configuration file is present ([section 4. Configuration files](#4-configuration-files)),
   it will override 1.
3. If environment variables are set ([section 5. Environment variables](#5-environment-variables)),
   they will override 2.
4. The presence of general udocker command line options, will override 3. .

### 3.1. Directories

With the default configuration, udocker creates files and subdirectories under
`$HOME/.udocker` these are:

* `doc`: documentation and licenses.
* `bin`: executables to support the execution engines.
* `lib`: libraries, namely the fakechroot libraries to support the **F** execution mode.
* `repos`: container image repositories.
* `layers`: the layers and metadata for the container images.
* `containers`: created containers.
* `keystore.github`: authentication to access repositories (created on demand).

Both installed files, as well as the containers to be downloaded or created  
with udocker, will be installed by default under `$HOME/.udocker`.

A default configuration file is available at
[udocker.conf](https://github.com/indigo-dc/udocker/blob/master/etc/udocker.conf)
it can be copied to your udocker directory as `$HOME/.udocker/udocker.conf` and
customized.

## 4. Configuration files

The configuration files allow overriding of the udocker `Config` class
`conf` dictionary. Example of the `udocker.conf` syntax:

```ini
dockerio_registry_url = "https://myregistry.mydomain:5000"
http_insecure = True
verbose_level = 5
```

udocker loads the following configuration files if they are present:

1. `/etc/udocker.conf`
2. `$HOME/.udocker/udocker.conf`: overrides the options set in 1.
3. `$UDOCKER_DIR/udocker.conf` (if different from the above): overrides the options set in 2.
4. Configuration file set with the general CLI option `--config=`: overrides the options set in 3.

## 5. Environment variables

The following environment variables can be used to customize the installation.
The location of the udocker directories can be changed via the environment
variables:

* `UDOCKER_DIR`: root directory of udocker usually $HOME/.udocker
* `UDOCKER_BIN`: location of udocker related executables
* `UDOCKER_LIB`: location of udocker related libraries
* `UDOCKER_DOC`: location of documentation and licenses
* `UDOCKER_REPOS` images metadata and links to layers
* `UDOCKER_LAYERS`: the common location for image layers data
* `UDOCKER_CONTAINERS`: location of container directory trees (not images)
* `UDOCKER_TMP`: location of temporary directory
* `UDOCKER_KEYSTORE`: location of keystore for login/logout credentials
* `UDOCKER_TARBALL`: location of installation tarball (file of URL)
* `UDOCKER_NOSYSCONF`: do not read system wide config files in /etc

The Docker index and registry can be overridden via the environment variables.

* `UDOCKER_INDEX=https://...`
* `UDOCKER_REGISTRY=https://...`

The verbosity level of udocker can be enforced. Removing banners and most
messages can be achieved by executing with `UDOCKER_LOGLEVEL=2`.

* `UDOCKER_LOGLEVEL`: set verbosity level from 0 to 5 (MIN to MAX verbosity)

Forcing the use of a given curl executable instead of pycurl can be
specified with:

* `UDOCKER_USE_CURL_EXECUTABLE`: pathname to the location of curl executable

The fakechroot execution modes (Fn modes), the translation of symbolic links
to the actual links can be controlled by the environment variable
`UDOCKER_FAKECHROOT_EXPAND_SYMLINKS`. The default value is
`none` which will select automatically the mode to be used, `false` if mounts are
not performed or if the mount points pathname for the host and container
are equal (e.g `-v /home:/home`), `true` otherwise (e.g `-v /data:/home`).

* `UDOCKER_FAKECHROOT_EXPAND_SYMLINKS`: true, false, none

The location of some executables used by the execution modes can be enforced with
the environment variables described below together with the default behavior.
A value of `UDOCKER` will force the usage of the executables provided by the
udocker installation.

A full pathname can be used to select a specific executable (or library) from the
host or from the udocker installation.

* `UDOCKER_USE_PROOT_EXECUTABLE`: path to proot, default is proot from udocker.
* `UDOCKER_USE_RUNC_EXECUTABLE`: path to runc, default is search the host and
  if not found use runc from udocker.
* `UDOCKER_USE_SINGULARITY_EXECUTABLE`: path to singularity, default is search
  the host.
* `UDOCKER_FAKECHROOT_SO`: path to a fakechroot library, default is search
  in udocker.
* `UDOCKER_DEFAULT_EXECUTION_MODE`: default execution mode can be P1, P2, F1,
  S1, R1, R2 or R3.

## 6. External tools and libraries

### 6.1. Source code repositories

udocker uses external tools and libraries to execute the created containers.
The source code for the udocker tools and libraries is taken from several repositories.
The **F** modes need heavily modified Fakechroot libraries and also a modified Patchelf
both specifically improved to work with udocker. The Fakechroot for musl is a port
of the Fakechroot library for the musl libc performed by the udocker development team.
The **P** modes need a modified PRoot that includes fixes and enhancements to work with
udocker. The **R** modes use the original runc and crun software with small changes for
static compilation. The following table highlights the repositories used by udocker
containing the modified source code and the original repositories.


| Mode  | Engine           | Repository used by udocker                                 | Original repository
|-------|:-----------------|:-----------------------------------------------------------|:-----------------------------------------
| **P** | PRoot            | <https://github.com/jorge-lip/proot-udocker>               | <https://github.com/proot-me/proot>
| **F** | Fakechroot glibc | <https://github.com/jorge-lip/libfakechroot-glibc-udocker> | <https://github.com/dex4er/fakechroot>
| **F** | Fakechroot musl  | <https://github.com/jorge-lip/libfakechroot-musl-udocker>  | <https://github.com/dex4er/fakechroot>
| **F** | Patchelf         | <https://github.com/jorge-lip/patchelf-udocker>            | <https://github.com/NixOS/patchelf>
| **R** | runc             | THE ORIGINAL REPOSITORY IS USED                            | <https://github.com/opencontainers/runc>
| **R** | crun             | THE ORIGINAL REPOSITORY IS USED                            | <https://github.com/containers/crun>

### 6.2. Software Licenses

Redistribution, commercial use and code changes must regard all licenses shipped with udocker.
These include the [udocker license](https://github.com/indigo-dc/udocker/blob/master/LICENSE)
and the individual licenses of the external tools and libraries packaged for use with udocker.

| Mode  | Engine           | License
|-------|:-----------------|:----------------------------------------------------------------------------
| **P** | PRoot            | [GPL v2](https://github.com/jorge-lip/proot-udocker/blob/master/COPYING)
| **F** | Fakechroot glibc | [LGPL v2.1](https://github.com/jorge-lip/libfakechroot-glibc-udocker/blob/master/LICENSE)
| **F** | Fakechroot musl  | [LGPL v2.1](https://github.com/jorge-lip/libfakechroot-musl-udocker/blob/master/LICENSE)
| **F** | Patchelf         | [GPL v3](https://github.com/jorge-lip/patchelf-udocker/blob/master/COPYING)
| **R** | runc             | [Apache v2.0](https://github.com/opencontainers/runc/blob/master/LICENSE)
| **R** | crun             | [GPL v2](https://github.com/containers/crun/blob/master/COPYING)

### 6.3. Binaries

As mentioned in the previous sections the compiled binaries can be installed
with `udocker install`. Optionally they can be downloaded from the repository
containing the binary builds at: <https://github.com/jorge-lip/udocker-builds>

The executables are provided statically compiled for use across systems.
The shared libraries that support the **F** modes need to match the libc
within the container and are provided for several Linux distributions.
See `$HOME/.udocker/lib` for the supported distributions and corresponding
versions. The tools are also delivered for several architectures.

| Mode  | Supported architecture                       |
|-------|:---------------------------------------------|
| **P** | x86_64, i386, aarch64 and arm                |
| **F** | x86_64                                       |
| **R** | x86_64                                       |
| **S** | uses the binaries present in the host system |

The latest binary tarball can be produced from the source code using:

```bash
git clone -b devel3 https://github.com/indigo-dc/udocker
cd udocker/utils
./build_tarball.sh
```

## 7. Central installation

udocker can be installed and made available system wide from a central location
such as a shared read-only directory tree or file-system. The following guidelines
should be followed when installing udocker in a central shared location or in a
read only file system.

### 7.1. Install executables and libraries centrally

The executables and libraries can be installed with any of the methods described
in section 2 of this manual. The directory tree should contain the following
subdirectories: `bin`,  `containers`,  `layers`,  `lib`,  `repos`. For the
binaries and libraries the only directories required are `bin` and `lib`.

The udocker tool should be installed as shown in section 2.1:

```bash
cd /sw
wget https://github.com/indigo-dc/udocker/releases/download/1.3.2/udocker-1.3.2.tar.gz
tar zxvf udocker-1.3.2.tar.gz
```

Directing users to the central udocker installation can be done using the
environment variables described in section 5, or through the configuration files
described in section 6. The recommended approach is to set environment
variables at the user level as in the example where the assumed central location
will be under `/sw/udocker`:

```bash
export UDOCKER_BIN=/sw/udocker/bin
export UDOCKER_LIB=/sw/udocker/lib
export PATH=$PATH:$UDOCKER_BIN:/sw/udocker
```

Note that the command `udocker` will be in `/sw/udocker` with all the python
directory structure, while `/sw/udocker/bin` has all execution engines.

Make sure that the file protections are adequate namely that the files are
not modifiable by others.

### 7.2. Images and layers in central installations

The repository of pulled images can also be placed in a different location
than the user home directory `$HOME/.udocker`. Notice that if the target
location is not writable then the users will be unable to pull new images,
which may be fine if these images are managed centrally by someone else.
Make sure that the file protections are adequate to the intended purpose.

From the images in the common location the users can then create containers
whose content will be placed in the user home directory under `$HOME/.udocker`.
This can be accomplished by redirecting the directories `layers` and  `repos`
to a common location. The users will need to set the following environment
variables. Therefore assuming that the common location will be `/sw/udocker`:

```bash
export UDOCKER_REPOS=/sw/udocker/repos
export UDOCKER_LAYERS=/sw/udocker/layers
```

### 7.3. Containers in central installations

If a container is extracted to the common location, it is possible to
point udocker to execute the container from that location. Making
udocker pointing at different `containers` directory such as for example
`/sw/udocker/containers` can be accomplished with:

```bash
export UDOCKER_CONTAINERS=/sw/udocker/containers
```

Assuming that the container is to be created under `/sw/udocker/containers`
it can be extracted with:

```bash
export UDOCKER_CONTAINERS=/sw/udocker/containers
udocker --allow-root pull  centos:centos7
udocker --allow-root create  --name=myContainerId  centos:centos7
udocker --allow-root run  -v /tmp myContainerId
```

Notice the `--allow-root` should only be used when running
from the root user. However depending on the execution mode and several other
factors the limitations described in the next sections apply.

#### 7.3.1. Selection of execution mode for central installations

The selection of the execution mode requires writing in the `containers`
directory, therefore if the container is in a read-only location the
execution mode cannot be changed. If a container is to be executed in a mode
other than the default then this must be set in advance. This must be done
by someone with write access. A table summarizing the execution modes
and their implications:

|Mode| Engine      | Execution from readonly location
|----|:------------|:------------------------------------------
| P1 | PRoot       | OK
| P2 | PRoot       | OK
| F1 | Fakechroot  | OK
| F2 | Fakechroot  | OK
| F3 | Fakechroot  | OK see restrictions in section 7.3.1.2.
| F4 | Fakechroot  | NOT SUPPORTED REQUIRES WRITE ACCESS
| R1 | runc / crun | OK requires udocker version above v1.1.7
| R2 | runc / crun | OK see restrictions in section 7.3.1.3.
| R3 | runc / crun | OK see restrictions in section 7.3.1.3.
| S1 | Singularity | OK

Changing the execution mode can be accomplished with the following udocker
command where `<MODE>` is one of the supported modes in column one.

```bash
udocker --allow-root setup --execmode=<MODE> myContainerId
```

Notice the `--allow-root` should only be used when running
from the root user.

If the same container is to be provided for execution using more
than one execution mode (e.g. to be executed with P1 and F3), then
make copies of the initial container and setup each one of them with
the intended mode. The command `udocker clone` can be used to create
copies of existing containers.

##### 7.3.1.1. Mode F4 is not supported

The mode F4 is not suitable for readonly containers as it is meant to
support the dynamic creation of new executables and libraries inside of
the container, which cannot happen if the container is readonly. Use the
mode F3 instead of F4.

##### 7.3.1.2. Mode F3 restrictions

The F3 mode (and also F4) perform changes to the container executables
and libraries, in particular they change the pathnames in ELF headers
making them pointing at the container location. This means that the
pathname to the container must be always the same across all the
hosts that may share the common location. Therefore if the original
location pathname is `/sw/udocker/containers` then all hosts must
also mount it at the same exact path `/sw/udocker/containers`.

##### 7.3.1.3. Modes R2 and R3 restrictions

Central installation from readonly location using any of the R modes
requires udocker above v1.1.7.
These modes require the creation of a mount point inside the container
that is transparently created when the container is first executed,
therefore (as recommended for all other modes) the container
must be executed once by someone with write access prior to making it
available to the users. Furthermore these execution modes are nested
they use P1 or P2 inside the R engine, the Pn modes require a tmp
directory that is writable. Therefore it is recommended to mount the
host `/tmp` in the container `/tmp` like this:

```bash
udocker --allow-root run  -v /tmp myContainerId
```

Or alternatively:

```bash
export PROOT_TMP_DIR=/<path-to-host-writable-directory>
udocker --allow-root run  -v /<path-to-host-writable-directory>  myContainerId
```

Notice the `--allow-root` should only be used when running from the root user.

#### 7.3.2. Mount directories and files in central installations

Making host files and directories visible inside the container requires
creating the corresponding mount points. The creation of mount-points
requires write access to the container. Therefore if a container is in
a read-only location these files and directories must be created in
advance.

Notice that some default mount points are required and automatically
created by udocker itself, therefore the container should be executed
by the administrator to ensure that the required files and directories
are created. Furthermore if additional mount points are required to
access data or other user files from the host, such mount points
must also be created by the administrator by executing the container
with the adequate volume pathnames. The example shows how to setup
the default mount points and in addition create a new mount point
named `/data`.

```bash
udocker --allow-root run -v /home:/data  myContainerId
```

Notice the `--allow-root` should only be used when running
from the root user.

Notice that once `/data` is setup the end users can mount other
directories in `/data` at runtime, meaning that users are not
restricted to mount only the `/home` directory as the mapping
is defined at run time.

#### 7.3.3. Protection of container files and directories

For the container to be executed by other users the files and
directories within the container must be readable. When udocker
is installed in the user home directory all files belong to
the user and are therefore readable by him. If a common location
is shared by several users the file protections will likely
need to be adjusted. Consider carefully your security policies
and requirements when changing the file protections.

The following example assumes making all files readable to
anyone and making all files (and directories) that have the
executable bit to be also *executable* by anyone.

```bash
export mycdir=$(udocker --allow-root inspect -p myContainerId)
chmod -R uog+r $mycdir
find $mycdir -executable -exec chmod oug+x {} \;
```

Notice the `--allow-root` should only be used when running
from the root user.

### 7.4. Using a common directory for executables and containers

If the common directory is used both for executables and containers
then the following environment variables can be used:

```bash
export UDOCKER_DIR=/sw/udocker
export PATH=$PATH:$UDOCKER_DIR:$UDOCKER_DIR/bin
```

## 8. Uninstall

udocker does not provide an uninstall command. udocker can be uninstalled
by simply removing the created files and directories. The recommended
approach is as follows:

1. Fix permissions for all created containers
   `for id in $(udocker ps | cut -f1 -d" " | grep -v CONTAINER); do udocker setup --fixperm $id; done`
2. Remove all created containers
   `for id in $(udocker ps | cut -f1 -d" " | grep -v CONTAINER); do udocker rm -f $id; done`
3. Remove the *udocker directory tree* usually under `$HOME/.udocker`
   `cd $HOME ; rm -Rf .udocker`
4. Remove the udocker Python code

The *udocker directory tree* contains the external executables, libraries,
documentation, container images and container file system trees. By removing
it all created containers will be also removed. Changing the file permissions
might be required prior to deletion especially for the container file system
trees in the `containers` subdirectory.

## 9. Quality assurance

The udocker software quality assurance follows the Common Software 
Quality Assurance Baseline Criteria for Research Projects 
DOI: <http://hdl.handle.net/10261/160086.> available at
<https://indigo-dc.github.io/sqa-baseline/>.

udocker uses the Jenkins Pipeline Library 
<https://github.com/indigo-dc/jenkins-pipeline-library>
to implement Jenkins CI/CD pipelines for quality assurance.

### 9.1. Functional and integration tests

High level functional and integration tests used for quality assurance are available 
in <https://github.com/indigo-dc/udocker/tree/master/utils>.
These tests are also suitable to be executed by end-users to verify the installation.
After cloning the udocker repository with `git` the `bash` scripts
can be executed using:

```bash
cd utils
./udocker_test.sh
./udocker_test-run.sh
```

If the `.udocker` directory already exists these tests will not execute as they require
a clean environment. In this case proceed as follows:

1. rename the directory `$HOME/.udocker`, as in `mv $HOME/.udocker $HOME/.udocker.ORIG`
2. execute the tests
3. remove the `$HOME/.udocker` created by the tests
4. restore the original `.udocker` directory as in `mv $HOME/.udocker.ORIG $HOME/.udocker`

### 9.2. Unit and security tests
The unit tests used in the software quality assurance pipelines are available at
<https://github.com/indigo-dc/udocker/tree/master/tests/unit>.
The tests can be executed after creating a virtualenv and installing the development
requirements in [requirements-dev.txt](https://github.com/indigo-dc/udocker/blob/master/requirements-dev.txt)
These tests are meant to be executed by the automated quality assurance pipelines.

```bash
virtualenv -p python3 ud3
source ud3/bin/activate
git clone https://github.com/indigo-dc/udocker.git
cd udocker
pip install -r requirements-dev.txt
```

The unit tests coverage can be executed using:

```bash
nosetests -v --with-coverage --cover-package=udocker tests/unit
```

Other tests configured in `tox.ini`, can be executed as well, such as linting
(code style checking) and static security tests:

```bash
pylint --rcfile=pylintrc --disable=R,C udocker
bandit -r udocker -f html -o bandit.html
```

