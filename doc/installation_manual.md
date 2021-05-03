# udocker INSTALLATION MANUAL

In most cases the end user itself can download and execute udocker without the
system administrator's intervention. udocker is written in Python, but 
also uses external binaries and sharable libraries to provide a chroot like
environment where containers are executed in user space. These tools do not
require any privileges.

## 1. DEPENDENCIES

Python dependencies are described in the file [requirements.txt](../requirements.txt).

Other host libraries and tools required:
 * udocker requires either pycurl or the curl executable command, to download both the 
   udockertools and pull containers from repositories.
 * tar is needed during `udocker install` to unpackage binaries and libraries.
 * find is used for some operations that perform filesystem transversal.
 * tar is used to unpack the container image layers.
 * openssl or python hashlib are required to calculate hashes. 
 * ldconfig is used in Fn execution modes to obtain the host sharable libraries.

## 2. USER INSTALLATION

### 2.1. PYTHON2: INSTALL DIRECTLY FROM GITHUB

Just download and execute the udocker python script and the remainder of the
installation including downloading and installing the udockertools will 
be performed automatically.

Once you download the udocker executable from github you can move it around 
between systems. Once you start it in a new system it will install the
required udockertools. The installation requires outbound network connectivity.

From the master branch for *production*:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/master/udocker.py > udocker
  chmod u+rx ./udocker
  ./udocker install
```

From the *development* branch for the latest additions and fixes:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/devel/udocker.py > udocker
  chmod u+rx ./udocker
  ./udocker install
```

To get a specific released version of udocker such as the old v1.1.4:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/v1.1.4/udocker.py > udocker
  chmod u+rx ./udocker
  ./udocker install
```

### 2.2. PYTHON3: INSTALL PRE-RELEASE

This pre-release is based on udocker 1.1.7, with additional bug fixes and compatibility to run in python3. Follow this steps to install and run udocker:

    wget https://github.com/indigo-dc/udocker/releases/download/devel3_1.2.7/udocker-1.2.7.tar.gz
    tar zxvf udocker-1.2.7.tar.gz
    export PATH=`pwd`/udocker:$PATH

Test with:

    udocker --help
    udocker install

### 2.3. INSTALL FROM UDOCKERTOOLS TARBALL

This installation method uses the udockertools tarball that contains statically compiled 
binaries and is built to be used across different hosts and OS distributions. Please 
check the repositories for the latest release.

Example of installing or upgrading udocker to version v1.1.7:

```
  curl https://raw.githubusercontent.com/jorge-lip/udocker-builds/master/tarballs/udocker-1.1.7.tar.gz > udocker-1.1.7.tar.gz
  export UDOCKER_TARBALL=$(pwd)/udocker-1.1.7.tar.gz
  tar xzvf $UDOCKER_TARBALL udocker
  chmod u+rx udocker
  ./udocker install
  mv ./udocker $HOME/bin/   # move the executable to your preferred location for binaries
```

### 2.4. OBTAINING UDOCKERTOOLS TARBALL FROM OTHER LOCATIONS

The udockertools installation tarball mentioned in section 2.3 can also be obtained using 
the following method. First download the udocker python script. Second use udocker 
itself to display the udockertools tarball URLs by invoking the `version` command. The
tarball location contains several URLs pointing to different mirrors.

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/v1.1.7/udocker.py > udocker  
  chmod u+rx ./udocker
  ./udocker version
```

Pick one URL and download the udockertools tarball using curl or wget.
By using a previously downloaded tarball and the UDOCKER_TARBALL environment variable 
as explained in section 2.3, udocker can be deployed without having to downloaded it 
everytime from the official repositories. The UDOCKER_TARBALL environment variable
can also be pointed to an http or https URL of your choice.

```
  curl $(./udocker version | grep '^tarball:' | cut -d' ' -f2- ) > udocker-1.1.7.tar.gz
```

### 2.5. FORCE REINSTALLATION of UDOCKERTOOLS

To force download and reinstallation of the udockertools. Invoke udocker install 
with the flag `--force`:

```
  ./udocker install --force
```

### 2.6. INSTALLATION WITH PIP

For installation with pip it is advisable to setup a Python2 virtual environment
before proceeding, see instructions [HERE](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
The actual installation of udocker can be performed directly from github with pip.

From the master branch for *production*:

```
  pip install git+https://github.com/indigo-dc/udocker
```
 
From the *development* branch for the latest additions and fixes:

```
  pip install git+https://github.com/indigo-dc/udocker@devel
```

To get a specific release version of udocker such as *v1.1.7*:

```
  pip install git+https://github.com/indigo-dc/udocker@v1.1.7
```

## 3. SOURCE CODE AND BUILD

A udockertools distribution tarball can be built using the script `build_tarball.sh`
in the utils directory. The script fetches the code necessary to build the
binary executables such as proot and compiles them statically. The following
example builds the tarball from the master repository.

```
  git clone https://github.com/indigo-dc/udocker
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
under `$HOME/.udocker` this directory will contain:

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
 * UDOCKER_CONTAINERS : top directory for storing containers (not images)
 * UDOCKER_KEYSTORE : location of keystore for login/logout credentials
 * UDOCKER_TMP : location of temporary directory
 * UDOCKER_TARBALL : location of installation tarball (file of URL)
 * UDOCKER_NOSYSCONF: do not read udocker system wide config files in /etc

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
host or from the udocker instalaltion.

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

The configuration files allow modification of the udocker `class Config` attributes.
Examples of the udocker.conf syntax:

```
  # Allow transfers that fail SSL authentication
  http_insecure = True
  # Increase verbosity
  verbose_level = 5
  # Require this version the `tarball` attribute must point to the correct tarball
  tarball_release = "1.1.7"
  # Specific the installation tarball location
  tarball = "https://hostname/somepath"
  # Disable autoinstall
  autoinstall = False
  # Specify config location
  config = "/someplace/udocker.conf"
  # Specify tmp directory location
  tmpdir = "/someplace"
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
Make sure that the file protections are adequate to your purpose.

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
| R1 | runC / crun | OK requires a udocker version above 1.1.7
| R2 | runC / crun | OK see restrictions in section 7.3.1.3. 
| R3 | runC / crun | OK see restrictions in section 7.3.1.3.
| S1 | Singularity | OK

Changing the execution mode can be accomplished with the following udocker
command where <MODE> is one of the supported modes in column one.

```
 udocker --allow-root setup --execmode=<MODE>   myContainerId
```

Notice the `--allow-root` should only be used when running
from the root user.

If you need to provide the same container with two different execution
modes then you need to create two containers and configure each one
with a different mode.

##### 7.3.1.1. Mode F4 is not supported
The mode F4 is not suitable for readonly containers as it is meant to
support the dynamic creation of new executables and libraries inside of
the container, which cannot happen if the container is readonly. Is
mode F3 instead.

##### 7.3.1.2. Mode F3 restrictions
The F3 mode (and also F4) perform changes to the container executables 
and libraries, in particular they change the pathnames in ELF headers
making them pointing at the container location. This means that the
pathname to the container must be always the same across all the
hosts that may share the common location. Therefore in the location
prefix is `/sw/udocker/containers` then the directory cannot be mounted 
elsewhere under a different prefix.

##### 7.3.1.3. Modes R2 and R3 restrictions
Central installation from readonly location using any of the R modes 
requires udocker above 1.1.7 available from the devel branch.
These modes require the creation of a mountpoint inside the container
that is transparently created when the container is first executed,
therefore (as also recommended in all the other modes) the container
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
directories within the container must be readable. When 
installed in the user home directory all files belong to
the user and are therefore readable. If a common location
is shared by several users the file protections will likelly
need to be adjusted. Consider carefully your security 
requirements when changing the file protections.

The following example assumes making all files readable to
anyone and making all files (and directories) that have the
executable bit to be also executable by anyone.

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
 
