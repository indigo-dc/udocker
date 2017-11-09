# udocker INSTALLATION MANUAL

In most circumstances the end user can download and execute the tool without
system administrator intervention. udocker itself is written in Python, but 
also uses external binaries and libraries to provide a chroot like
environment where containers are executed in user space. These tools do not
require any privileges.

## 1. DEPENDENCIES

Python dependencies are described in the file requirements.txt

udocker requires either pycurl or the curl executable command,
to download both the binaries and/or pull containers from repositories.

## 2. USER INSTALLATION

### 2.1. INSTALL FROM OFFICIAL INDIGO REPOSITORIES
<!--
-->
The official release of udocker is available from the INDIGO-DataCloud
repository at `http://repo.indigo-datacloud.eu/` where is made available
as a tarball to be deployed by the end user.

The tarball installation method contains statically compiled binaries and 
is built to be used across different hosts and OS distributions.

Install of udocker v1.1.1 or higher released by INDIGO-DataCloud:

```
  curl http://repo.indigo-datacloud.eu/repository/indigo/2/centos7/x86_64/tgz/udocker-1.1.1.tar.gz > udocker-tarball.tgz
  export UDOCKER_TARBALL=$(pwd)/udocker-tarball.tgz
  tar xzvf $UDOCKER_TARBALL udocker
  ./udocker install
  mv ./udocker $HOME   # move the executable to your preferred location for binaries
```

Install of the old udocker 1.0.0 released by INDIGO-DataCloud:

```
  cd $HOME
  wget -O- http://repo.indigo-datacloud.eu/repository/indigo/1/centos7/x86_64/tgz/udocker-v1.0.0.tar.gz | tar xzvf -
  ./udocker.py version
```

When using the setup.py provided in the releases install with:

```
  mkdir /tmp/somedir
  cd /tmp/somedir
  curl http://repo.indigo-datacloud.eu/repository/indigo/1/centos7/x86_64/tgz/udocker-v1.X.X.tar.gz | tar xzvf -
  python setup.py install --home /home/USER/bin
```

### 2.2. INSTALL LATEST UDOCKER DIRECTLY FROM GITHUB

Optionally just download and execute the udocker python script from the source and the
installation will be performed automatically. The installation from source code is not
officially supported by INDIGO-DataCloud.

This method is very flexible, once you download the udocker executable from github
you can move it around between systems. Once you start it in a new system it will 
install itself. The installation requires outbound network connectivity.

From the master branch:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/master/udocker.py > udocker
  chmod u+rx ./udocker
  ./udocker version
```

From the development branch:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/devel/udocker.py > udocker
  chmod u+rx ./udocker
  ./udocker version
```

### 2.3. OBTAINING THE URL OF THE LATEST TARBALL

The udocker tarball used in the installation described in section 2.2 can be
obtained using the following method. First download udocker from the repository
then run info.py which will display the URL of the latest tarball used in the
automated installation.

```
  git clone https://github.com/indigo-dc/udocker
  cd udocker/utils
  python2 ./info.py
```

You may then download the tarball using tools such as curl or wget.


## 3. SYSTEM INSTALLATION WITH RPMs and DEBs

Beware that these packages contain dynamically linked binaries compiled for
the target OS distributions and therefore cannot be execute successfully in 
hosts running a different OS distribution. To execute the same udocker across 
systems use the tarball installation methods described above in section 2. 

RPMs for CentOS 7 are provided at http://repo.indigo-datacloud.eu

```
  rpm -i udocker-1.1.1-1.noarch.rpm \
         udocker-preng-1.1.1-1.x86_64.rpm \
         udocker-freng-1.1.1-1.x86_64.rpm
```

DEBs for Ubuntu 16 are provided at http://repo.indigo-datacloud.eu

```
  dpkg -i udocker_1.1.1-1_all.deb \
          udocker-preng_1.1.1-1_amd64.deb \
          udocker-freng_1.1.1-1_amd64.deb \
          udocker-rceng_1.1.1-1_amd64.deb
```

The rc engine (rceng) is only available for Ubuntu 14 and 16.

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
  git clone -b devel https://github.com/indigo-dc/udocker
```

## 6. BUILD

A distribution tarball can be built using the script build_tarball.sh in
the utils directory. The script fetches the code necessary to build the
binary executables such as proot and compiles them statically. The following
example builds the tarball from the master repository.

```
  git clone https://github.com/indigo-dc/udocker
  cd udocker/utils
  bash build_tarball.sh
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


