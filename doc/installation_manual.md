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

### 2.1. INSTALL LATEST VERSIONS DIRECTLY FROM GITHUB

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

To get a specific released version of udocker such as v1.1.4:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/v1.1.4/udocker.py > udocker
  chmod u+rx ./udocker
  ./udocker install
```

### 2.2. INSTALL FROM UDOCKERTOOLS TARBALL

This installation method uses the udockertools tarball that contains statically compiled 
binaries and is built to be used across different hosts and OS distributions. Please 
check the repositories for the latest release.

Example of installing or upgrading udocker to version v1.1.4:

```
  curl https://raw.githubusercontent.com/jorge-lip/udocker-builds/master/tarballs/udocker-1.1.4.tar.gz > udocker-1.1.4.tar.gz
  export UDOCKER_TARBALL=$(pwd)/udocker-1.1.4.tar.gz
  tar xzvf $UDOCKER_TARBALL udocker
  chmod u+rx udocker
  ./udocker install
  mv ./udocker $HOME/bin/   # move the executable to your preferred location for binaries
```

### 2.3. OBTAINING UDOCKERTOOLS TARBALL FROM OTHER LOCATIONS

The udockertools installation tarball mentioned in section 2.2 can also be obtained using 
the following method. First download the udocker python script. Second use udocker 
itself to display the udockertools tarball URLs by invoking the `version` command. The
tarball location contains several URLs pointing to different mirrors.

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/v1.1.4/udocker.py > udocker  
  chmod u+rx ./udocker
  ./udocker version
```

Pick one URL and download the udockertools tarball using curl or wget.
By using a previously downloaded tarball and the UDOCKER_TARBALL environment variable 
as explained in section 2.2, udocker can be deployed without having to downloaded it 
everytime from the official repositories. The UDOCKER_TARBALL environment variable
can also be pointed to an http or https URL of your choice.

```
  curl $(./udocker version | grep '^tarball:' | cut -d' ' -f3) > udocker-1.1.4.tar.gz
```

### 2.4. FORCE REINSTALLATION of UDOCKERTOOLS

To force download and reinstallation of the udockertools. Invoke udocker install 
with the flag `--force`:

```
  ./udocker install --force
```

## 2.5. INSTALLATION WITH PIP

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

To get a specific release version of udocker such as *v1.1.4*:

```
  pip install git+https://github.com/indigo-dc/udocker@v1.1.4
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
  tarball_release = "1.1.4"
  # Specific the installation tarball location
  tarball = "https://hostname/somepath"
  # Disable autoinstall
  autoinstall = False
  # Specify config location
  config = "/someplace/udocker.conf"
  # Specify tmp directory location
  tmpdir = "/someplace"
```

