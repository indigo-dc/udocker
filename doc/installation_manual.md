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

### 2.1. INSTALL LATEST VERSIONS DIRECTLY FROM GITHUB

Just download and execute the udocker and the installation will be performed
automatically.

This installation method contains statically compiled binaries and is built 
to be used across different hosts and OS distributions.

Once you download the udocker executable from github you can move it around 
between systems. Once you start it in a new system it will install the
required tools. The installation requires outbound network connectivity.

From the master branch:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/master/udocker.py > udocker
  chmod u+rx ./udocker
  ./udocker install
```

From the development branch:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/devel/udocker.py > udocker
  chmod u+rx ./udocker
  ./udocker install
```

### 2.2. INSTALL FROM INDIGO-DATACLOUD REPOSITORIES
<!--
-->
The official release of udocker is available from the INDIGO-DataCloud
repository at `http://repo.indigo-datacloud.eu/` where is made available
as a tarball to be deployed by the end user.

This installation method contains statically compiled binaries and is built
to be used across different hosts and OS distributions. Please check the
repositories for the latest release.

Install or upgrade of udocker v1.1.0 or higher released by INDIGO-DataCloud:

```
  curl http://repo.indigo-datacloud.eu/repository/indigo/2/centos7/x86_64/tgz/udocker-1.1.0.tar.gz > udocker-tarball.tgz
  export UDOCKER_TARBALL=$(pwd)/udocker-tarball.tgz
  tar xzvf $UDOCKER_TARBALL udocker
  ./udocker install
  mv ./udocker $HOME/bin/   # move the executable to your preferred location for binaries
```

When using the setup.py provided in the release after downloading use:

```
  python setup.py install --home $HOME/bin/
```

### 2.3. Install from pypi tarball

After download of tarball from PYPI, you can uncompress, and set the
udocker executable in your PATH:

```
  ls udocker-2.0.5.tar.gz
  tar zxvf udocker-2.0.5.tar.gz
  export PATH=`pwd`/udocker-2.0.5/udocker:$PATH
```

### 2.4. OBTAINING THE URL OF THE TARBALL

The udocker installation tarball mentioned in section 2.2 can be obtained using the 
following method. First download udocker. Second use udocker itself to display the
installation tarball URL by invoking the `version` command. The tarball location may 
contain several URLs pointing to mirrors.

```
  ./udocker version
```

Then, pick one URL and download the tarball using tools such as curl or wget.
By using a previously downloaded tarball and the UDOCKER_TARBALL environment variable 
as explained in section 2.2, udocker can be deployed without having to downloaded it 
everytime from the official repositories. The UDOCKER_TARBALL environment variable
can also be pointed to an http or https URL.

### 2.5. FORCE REINSTALLATION

To force download and reinstallation of the udocker tools. Invoke udocker install 
with the flag `--force`:

```
  ./udocker install --force
```

## 3. SYSTEM INSTALLATION WITH RPMs and DEBs

Beware that these packages contain dynamically linked binaries compiled for
the target OS distributions and therefore cannot be execute successfully in 
hosts running a different OS distribution. To execute the same udocker across 
systems use the tarball installation methods described above in section 2. 

RPMs are provided at http://repo.indigo-datacloud.eu

```
  rpm -i udocker-1.1.X-1.noarch.rpm \
         udocker-preng-1.1.X-1.x86_64.rpm \
         udocker-freng-1.1.X-1.x86_64.rpm
```

DEBs are provided at http://repo.indigo-datacloud.eu

```
  dpkg -i udocker_1.1.X-1_all.deb \
          udocker-preng_1.1.X-1_amd64.deb \
          udocker-freng_1.1.X-1_amd64.deb \
          udocker-rceng_1.1.X-1_amd64.deb
```
Check the INDIGO-DataCloud repository for the latest versions and supported distributions.
Replace `X` in the examples with the latest version.
Notice that the rc engine (udocker-rceng) package is only available for Ubuntu 14 and 16.

## 4. SYSTEM INSTALLATION WITH ANSIBLE AND PYTHON

For system administrators wishing to provider udocker and its dependencies, 
an ansible playbook is provided in the file ansible_install.yaml:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/master/ansible_install.yaml > ansible_install.yaml

  ansible-playbook ansible_install.yaml
```

Under debian based systems ansible can be installed with:

```
  apt install ansible
```

Under RH based systems ansible can be installed with:

```
  yum install epel-release 
  yum install ansible
```

Optionally installation can be performed directly with pip:

```
  pip install git+https://github.com/indigo-dc/udocker
```

## 5. SOURCE CODE
To get the master branch:

```
  git clone https://github.com/indigo-dc/udocker
```

To get the latest udocker script from the github devel branch without
cloning the entire repository. This downloads udocker.py only.
```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/devel/udocker.py
```

To get the udocker source code repository from the github master branch, clone the 
repository, or use a web browser to access github at `https://github.com/indigo-dc/udocker`.

```
  git clone https://github.com/indigo-dc/udocker
```

To get the udocker source code repository from the devel branch.

```
  git clone https://github.com/indigo-dc/udocker
  cd udocker
  checkout devel
```

## 6. BUILD

A distribution tarball can be built using the script build_tarball.sh in
the utils directory. The script fetches the code necessary to build the
binary executables such as proot and compiles them statically. The following
example builds the tarball from the master repository.

```
  git clone https://github.com/indigo-dc/udocker
  cd udocker/utils
  ./build_tarball.sh
```
 
## 7. DIRECTORIES

The binary executables and containers are usually kept in the user home directory
under $HOME/.udocker this directory will contain:

 * Additional tools and modules for udocker such as proot.
 * Data from pulled container images (layers and metadata).
 * Directory trees for the containers extracted from the layers.


## 8. ENVIRONMENT

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

## 9. CONFIGURATION

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

