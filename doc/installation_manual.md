# udocker INSTALLATION MANUAL

In most circumstances the end user can download and execute the tool without
system administrator intervention. udocker itself is written in Python, but 
also uses external binaries and libraries to provide a chroot like
environment where containers are executed in user space. These tools do not
require any privileges.

## 1. DEPENDENCIES

Python dependencies are described in the file [requirements.txt](../requirements.txt).

Other host libraries and tools required:
 * udocker requires either pycurl or the curl executable command, to download both the udocker tools and/or pull containers from repositories.
 * tar is needed during `udocker install` to unpackage binaries and libraries.
 * tar is used to unpack the container image layers.
 * openssl or python hashlib are required to calculate hashes. 
 * ldconfig is used in Fn execution modes to obtain the host sharable libraries.

## 2. USER INSTALLATION

### 2.1. INSTALL LATEST VERSIONS DIRECTLY FROM GITHUB

Just download and execute the udocker python script and the remainder of the
installation including downloading and installation of additional tools will 
be performed automatically.

Once you download the udocker executable from github you can move it around 
between systems. Once you start it in a new system it will install the
required tools. The installation requires outbound network connectivity.

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

### 2.2. INSTALL FROM REPOSITORIES

udocker is also available as a tarball in certain repositories such as:
 * `https://download.ncg.ingrid.pt/webdav/udocker/`
 * `http://repo.indigo-datacloud.eu/` 

This installation method uses the udocker tarball that contains statically compiled 
binaries and is built to be used across different hosts and OS distributions. Please 
check the repositories for the latest release.

Example of installing or upgrading udocker to version v1.1.3:

```
  curl https://download.ncg.ingrid.pt/webdav/udocker/udocker-1.1.3.tar.gz > udocker-tarball.tgz
  export UDOCKER_TARBALL=$(pwd)/udocker-tarball.tgz
  tar xzvf $UDOCKER_TARBALL udocker
  ./udocker install
  mv ./udocker $HOME/bin/   # move the executable to your preferred location for binaries
```

### 2.3. OBTAINING THE URL OF THE TARBALL

The udocker installation tarball mentioned in section 2.2 can also be obtained using 
the following method. First download the udocker python script. Second use udocker 
itself to display the installation tarball URL by invoking the `version` command. The
tarball location may contain several URLs pointing to mirrors.

```
  ./udocker version
```

Then, pick one URL and download the tarball using tools such as curl or wget.
By using a previously downloaded tarball and the UDOCKER_TARBALL environment variable 
as explained in section 2.2, udocker can be deployed without having to downloaded it 
everytime from the official repositories. The UDOCKER_TARBALL environment variable
can also be pointed to an http or https URL of your choice.

### 2.4. FORCE REINSTALLATION

To force download and reinstallation of the udocker tools. Invoke udocker install 
with the flag `--force`:

```
  ./udocker install --force
```

## 3. SYSTEM INSTALLATION WITH RPMs and DEBs

Beware that these packages contain dynamically linked binaries compiled for
the target OS distributions and therefore cannot be executed successfully in 
hosts running a different OS distribution. To execute the same udocker across 
systems use the tarball installation methods described above in section 2. 

RPMs are provided at http://repo.indigo-datacloud.eu

```
  rpm -i udocker-1.X.X-1.noarch.rpm \
         udocker-preng-1.X.X-1.x86_64.rpm \
         udocker-freng-1.X.X-1.x86_64.rpm
```

DEBs are provided at http://repo.indigo-datacloud.eu

```
  dpkg -i udocker_1.X.X-1_all.deb \
          udocker-preng_1.X.X-1_amd64.deb \
          udocker-freng_1.X.X-1_amd64.deb \
          udocker-rceng_1.X.X-1_amd64.deb
```
Check the INDIGO-DataCloud repository for the latest versions and supported distributions.
Replace `X` in the examples with the latest version.
Notice that the rc engine (udocker-rceng) package is only available for Ubuntu 16 and 18.

## 4. SYSTEM INSTALLATION WITH ANSIBLE AND PYTHON

For system administrators wishing to provide udocker an ansible playbook is provided in
the file ansible_install.yaml:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/master/ansible_install.yaml > ansible_install.yaml

  ansible-playbook ansible_install.yaml
```

## 5. INSTALLATION WITH PIP

Optionally installation can be performed directly with pip:

```
  pip install git+https://github.com/indigo-dc/udocker
```

## 6. SOURCE CODE

To get the source code from github:

```
  git clone https://github.com/indigo-dc/udocker
```

## 7. BUILD

A distribution tarball can be built using the script `build_tarball.sh` in
the utils directory. The script fetches the code necessary to build the
binary executables such as proot and compiles them statically. The following
example builds the tarball from the master repository.

```
  git clone https://github.com/indigo-dc/udocker
  cd udocker/utils
  ./build_tarball.sh
```
 
## 8. DIRECTORIES

The binary executables and containers are usually kept in the user home directory
under `$HOME/.udocker` this directory will contain:

 * Additional tools and modules for udocker such as proot, etc.
 * Data from pulled container images (layers and metadata).
 * Directory trees for the containers extracted from the layers.

## 9. ENVIRONMENT

The location of the udocker directories can be changed via environment variables.

 * UDOCKER_DIR : root directory of udocker usually $HOME/.udocker
 * UDOCKER_BIN : location of udocker related executables
 * UDOCKER_LIB : location of udocker related libraries
 * UDOCKER_CONTAINERS : location of container directory trees (not images)
 * UDOCKER_KEYSTORE : location of keystore for repository login/logout
 * UDOCKER_TMP : location of temporary directory
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

## 10. CONFIGURATION

udocker loads the following configuration files:

 * /etc/udocker.conf
 * $UDOCKER_DIR/udocker.conf
 * $HOME/.udocker/udocker.conf (if different from the above)

The configuration files allow modification of the udocker `class Config` attributes.
Examples of the udocker.conf syntax:

```
  # Select the default registry
  dockerio_registry_url = "https://myregistry.mydomain:5000"
  # Allow transfers that fail SSL authentication
  http_insecure = True
  # Increase verbosity
  verbose_level = 5
  # Require this version the `tarball` attribute must point to the correct tarball
  tarball_release = "1.1.3"
  # Specific the installation tarball location
  tarball = "https://hostname/somepath"
  # Disable autoinstall
  autoinstall = False
  # Specify config location
  config = "/someplace/udocker.conf"
  # Specify tmp directory location
  tmpdir = "/someplace"
```

