# udocker INSTALLATION MANUAL

In most circumstances the end user can download and execute the tool without
system administrator intervention. udocker itself is written in Python, but 
also uses external binaries and libraries to provide a chroot like
environment where containers are executed in user space. These tools do not
require any privileges.

## 1. DEPENDENCIES

Python dependencies are described in the file requirements.txt.

udocker requires either pycurl or the curl executable command,
to download both the binaries and/or pull containers from repositories.

tar is needed when using `udocker install` to unpackage binaries and libraries.

## 2. USER INSTALLATION

### 2.1. INSTALL FROM A RELEASED VERSION

---
Download a release tarball from https://github.com/indigo-dc/udocker/releases: 

```
  wget https://github.com/indigo-dc/udocker/releases/download/devel3_1.2.7/udocker-1.2.7.tar.gz

  tar zxvf udocker-1.2.7.tar.gz

  export PATH=`pwd`/udocker:$PATH
```

alternatively use `curl` instead of `wget` as follows:

```
  curl -L https://github.com/indigo-dc/udocker/releases/download/devel3_1.2.7/udocker-1.2.7.tar.gz > udocker-1.2.7.tar.gz

  tar zxvf udocker-1.2.7.tar.gz

  export PATH=`pwd`/udocker:$PATH
```

Complete the installation by invoking udocker install to download and install udockertools:

```
  udocker install
```

A default configuration file can be found in directory `udocker/etc/udocker.conf`,
you can copy it to your home directory `$HOME` or to `$UDOCKER` 

---

This installation method contains statically compiled binaries and is built 
to be used across different hosts and OS distributions.

### 2.2. INSTALL FROM THE DEVELOPMENT BRANCH

To install from the github development branch `devel3`:

```
  git clone -b devel3 --depth=1 https://github.com/indigo-dc/udocker.git
  
  export PATH=`pwd`/udocker:$PATH
```

As before complete the installation by invoking udocker install to download and install udockertools:

```
  udocker install
```


### 2.3. OBTAINING THE URL OF THE TARBALL

The udocker installation tarball mentioned in section 2.2 can be obtained using the 
following method. First download udocker. Second use udocker itself to display the
installation tarball URL by invoking the `version` command. The tarball location may 
contain several URLs pointing to mirrors.

```
  udocker version
```

Then, pick one URL and download the tarball using tools such as curl or wget.
By using a previously downloaded tarball and the UDOCKER_TARBALL environment variable 
as explained in section 2.2, udocker can be deployed without having to downloaded it 
everytime from the official repositories. The UDOCKER_TARBALL environment variable
can also be pointed to an http or https URL.

### 2.4. FORCE REINSTALLATION OF udockertools

To force download and reinstallation of udockertools. Invoke udocker install 
with the flag `--force`:

```
  udocker install --force
```

## 3. SOURCE CODE AND BUILD

A udockertools distribution tarball can be built using the script `build_tarball.sh`
in the utils directory. The script fetches the code necessary to build the
binary executables such as proot and compiles them statically. The following
example builds the tarball from the master repository.

```
  git clone -b devel3 https://github.com/indigo-dc/udocker
  cd udocker/utils
  ./build_tarball.sh
```

You can also get a tarball for a given release of the source code from github and compile it.
The released source code is available at:

```
  https://github.com/indigo-dc/udocker/releases
```
 
## 4. DIRECTORIES

The binary executables and containers are usually kept in the user home directory
under $HOME/.udocker this directory will contain:

 * Additional tools and modules for udocker such as proot, etc.
 * Data from pulled container images (layers and metadata).
 * Directory trees for the containers extracted from the layers.


## 5. ENVIRONMENT

The location of the udocker directories can be changed via environment variables.

 * UDOCKER_DIR : root directory of udocker usually $HOME/.udocker
 * UDOCKER_BIN : location of udocker related executables
 * UDOCKER_LIB : location of udocker related libraries
 * UDOCKER_REPOS: images metadata and links to layers
 * UDOCKER_LAYERS: the common location for image layers data
 * UDOCKER_CONTAINERS : location of container directory trees (not images)
 * UDOCKER_TMP : location of temporary directory
 * UDOCKER_KEYSTORE : location of keystore for login/logout credentials
 * UDOCKER_TARBALL : location of installation tarball (file of URL)
 * UDOCKER_NOSYSCONF: do not read system wide config files in /etc

The Docker index and registry and be overrided via environment variables.

 * UDOCKER_INDEX : https://...
 * UDOCKER_REGISTRY : https://...

The verbosity level of udocker can be enforced. Removing banners and most messages
can be achieved by executing with UDOCKER_LOGLEVEL=2

 * UDOCKER_LOGLEVEL : set verbosity level from 0 to 5 (MIN to MAX verbosity)

Forcing the use of a given curl executable instead of pycurl can be specified with:

 * UDOCKER_USE_CURL_EXECUTABLE : pathname to the location of curl executable

In Fn modes the translation of symbolic links to the actual links can be controlled
the env variable accepts the values: true, false, none

 * UDOCKER_FAKECHROOT_EXPAND_SYMLINKS : default is none

The location of some executables used in the execution modes can be enforced with
the environment variables described below together with the default behavior.
A value of "UDOCKER" will force the usage of the executables provided by the
udocker installation.
A full pathname can be used to select a specific executable (or library) from the
host or from the udocker installation.

 * UDOCKER_USE_PROOT_EXECUTABLE : path to proot, default is proot from udocker
 * UDOCKER_USE_RUNC_EXECUTABLE : path to runc, default is search the host and if not found use runc from udocker
 * UDOCKER_USE_SINGULARITY_EXECUTABLE : path to singularity, default is search the host
 * UDOCKER_FAKECHROOT_SO : path to a fakechroot library, default is search in udocker
 * UDOCKER_DEFAULT_EXECUTION_MODE : default execution mode can be P1, P2, F1, S1, R1, R2 or R3


## 6. CONFIGURATION

udocker loads the following configuration files:

 * /etc/udocker.conf
 * $UDOCKER_DIR/udocker.conf
 * $HOME/.udocker/udocker.conf (if different from the above)

The configuration files allow modification of the udocker Config class attributes.
Example of the udocker.conf syntax:

```
  dockerio_registry_url = "https://myregistry.mydomain:5000"
  http_insecure = True
  verbose_level = 5
```

## 7. CENTRAL INSTALLATION

udocker can be installed and made available system wide from a central location
such as a shared read-only directory tree or file-system.

### 7.1. EXECUTABLES AND LIBRARIES

The executables and libraries can be installed with any of the methods described
in section 2 of this manual. The directory tree should contain the following
subdirectories: `bin`,  `containers`,  `layers`,  `lib`,  `repos`. For the
binaries and libraries the only directories required are `bin` and `lib`.
The actual udocker command can be placed in the `bin` directory.

Directing users to the central udocker installation can be done using the
environment variables described in section 5, or through the configuration files
described in section 6. The recommended approach is to set environment
variables at the user level as in the example where the assumed central location
will be under `/sw/udocker`:

```
 export UDOCKER_BIN=/sw/udocker/bin
 export UDOCKER_LIB=/sw/udocker/lib
 export PATH=$PATH:/sw/udocker/bin
```

Make sure that the file protections are adequate namelly that the files are
not modifiable by others.

### 7.2. IMAGES AND LAYERS IN A COMMON LOCATION

The repository of pulled images can also be placed in a different location
than the user home directory `$HOME/.udocker`. Notice that if the target
location is not writable then the users will be unable to pull new images,
which may be fine if these images are managed centrally by someone else.
Make sure that the file protections are adequate to the intended purpose.

From the images in the common location the users can then create containers
whose content will be placed in the user home directory under `$HOME/.udocker`.
This can be accomplished by redirecting the directories `layers` and  `lib`
to a common location. The users will need to set the following environment
variables. Therefore assuming that the common location will be `/sw/udocker`:

```
 export UDOCKER_REPOS=/sw/udocker/repos
 export UDOCKER_LAYERS=/sw/udocker/layers
```

### 7.3. CONTAINERS IN THE COMMON LOCATION

If a container is extracted to  the common location, it is possible to
point udocker to execute the container from that location. Making
udocker pointing at different `containers` directory such as for example
`/sw/udocker/containers` can be performed with:

```
 export UDOCKER_CONTAINERS=/sw/udocker/containers
```

Assuming that the container is to be created under `/sw/udocker/containers`
it can be extracted with:

```
 export UDOCKER_CONTAINERS=/sw/udocker/containers
 udocker --allow-root pull  centos:centos7
 udocker --allow-root create  --name=myContainerId  centos:centos7
 udocker --allow-root run  -v /tmp myContainerId
```

Notice the `--allow-root` should only be used when running
from the root user.

However depending on the execution mode and several other factors the
limitations described in the next sections apply.

#### 7.3.1. SELECTION OF EXECUTION MODE

The selection of the execution mode requires writing in the `containers`
directory, therefore if the container is in a read-only location the
execution mode cannot be changed. If a container is to be executed in a mode
other than the default then this must be set in advance. This must be done
by a someone with write access. A table summarizing the execution modes
and their implications:

|Mode| Engine      | Execution from readonly location
|----|:------------|:------------------------------------------
| P1 | PRoot       | OK
| P2 | PRoot       | OK
| F1 | Fakechroot  | OK
| F2 | Fakechroot  | OK
| F3 | Fakechroot  | OK see restrictions in section 7.3.1.2.
| F4 | Fakechroot  | NOT SUPPORTED
| R1 | runC / crun | OK requires a udocker version above v1.1.7
| R2 | runC / crun | OK see restrictions in section 7.3.1.3.
| R3 | runC / crun | OK see restrictions in section 7.3.1.3.
| S1 | Singularity | OK

Changing the execution mode can be accomplished with the following udocker
command where `<MODE>` is one of the supported modes in column one.

```
 udocker --allow-root setup --execmode=<MODE>   myContainerId
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
requires udocker above v1.1.7 available from the udocker `devel` branch.
These modes require the creation of a mountpoint inside the container
that is transparently created when the container is first executed,
therefore (as recommended for all other modes) the container
must be executed once by someone with write access prior to making it
available to the users. Furthermore these execution modes are nested
they use P1 or P2 inside the R engine, the Pn modes require a tmp
directory that is writable. Therefore it is recommended to mount the
host /tmp in the container /tmp like this:

```
 udocker --allow-root run  -v /tmp myContainerId
```

or alternatively:

```
 export PROOT_TMP_DIR=/<path-to-host-writable-directory>
 udocker --allow-root run  -v /<path-to-host-writable-directory>  myContainerId
```

Notice the `--allow-root` should only be used when running
from the root user.


#### 7.3.2. MOUNT OF DIRECTORIES AND FILES

Making host files and directories visible inside the container requires
creating the corresponding mount points. The creation of mount-points
requires write access to the container. Therefore if a container is in
a read-only location these files and directories must be created in
advance.

Notice that some default mount points are required and automatically
created by udocker itself, therefore the container should be executed
by the administrator to ensure that the required files and directories
are created. Furthermore if additional mountpoints are required to
access data or other user files from the host, such mountpoints
must be also created by the administrator by executing the container
with the adequate volume pathnames. The example shows how to setup
the default mountpoints and in addition create a new mountpoint
named `/data`.

```
 udocker --allow-root run -v /home:/data  myContainerId
```

Notice the `--allow-root` should only be used when running
from the root user.

Notice that once `/data` is setup the end users can mount other
directories in `/data` at runtime, meaning that users are not
restricted to mount only the `/home` directory as the mapping
is defined at run time.

#### 7.3.3. PROTECTION OF CONTAINER FILES AND DIRECTORIES

For the container to be executed by other users the files and
directories within the container must be readable. When udocker
is installed in the user home directory all files belong to
the user and are therefore readable by him. If a common location
is shared by several users the file protections will likelly
need to be adjusted. Consider carefully your security policies
and requirements when changing the file protections.

The following example assumes making all files readable to
anyone and making all files (and directories) that have the
executable bit to be also *executable* by anyone.

```
 mycdir=$(udocker --allow-root inspect -p myContainerId)
 chmod -R uog+r $mycdir
 find $mycdir -executable -exec chmod oug+x {} \;
```

Notice the `--allow-root` should only be used when running
from the root user.


### 7.4. USING A COMMON DIRECTORY FOR BOTH EXECUTABLES AND CONTAINERS

If the common directory is used both for executables and containers
then the following environment variables can be used:

```
 export UDOCKER_DIR=/sw/udocker
 export PATH=$PATH:/sw/udocker/bin
```

