udocker INSTALLATION MANUAL
===========================
In most circumstances the end user can download and execute the tool without
system administrator intervention. udocker itself is written in Python, but 
also uses external statically compiled binaries to provide a chroot like
environment where containers are executed. These tools do not require any
privileges.

1. DEPENDENCIES
===============
Python dependencies are described in the file requirements.txt

udocker requires either pycurl or the curl executable command,
to download both the binaries and/or pull containers from repositories.

2. USER INSTALLATION
====================
The official release of udocker is available from the INDIGO-DataCloud
repository at `http://repo.indigo-datacloud.eu/` where is made available
as a tarball to be deployed by the end user. Allways check for the latest
official version released by INDIGO-DataCloud.

For udocker v1.0.1 or higher released by INDIGO-DataCloud:

```
  curl http://repo.indigo-datacloud.eu/repository/indigo/1/centos7/x86_64/tgz/udocker-v1.0.1.tar.gz > udocker-tarball.tgz
  export UDOCKER_TARBALL=$(pwd)/udocker-tarball.tgz
  tar xzvf $UDOCKER_TARBALL udocker
  ./udocker help   
```

For the previous udocker 1.0.0 released by INDIGO-DataCloud:

```
  cd $HOME
  wget -O- http://repo.indigo-datacloud.eu/repository/indigo/1/centos7/x86_64/tgz/udocker-v1.0.0.tar.gz | tar xzvf -
```

If using the setup.py provided in the releases install with:

```
  mkdir /tmp/somedir
  cd /tmp/somedir
  curl http://repo.indigo-datacloud.eu/repository/indigo/1/centos7/x86_64/tgz/udocker-v1.X.X.tar.gz | tar xzvf -
  python setup.py install --help
  python setup.py install --home /home/USER/bin
```


Optionally just download and execute the udocker python script from the source and the installation
will be performed automatically. The installation from source code is not officially supported by 
INDIGO-DataCloud.

For the master branch:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/master/udocker > udocker
  chmod u+rx ./udocker
  ./udocker
```

For the development branch:

```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/devel/udocker > udocker
  chmod u+rx ./udocker
  ./udocker
```


3. SYSTEM INSTALLATION
======================
For system administrators wishing to provider udocker and its dependencies. 
An ansible playbook is provided in the file ansible_install.yaml:

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

4. SOURCE CODE
==============
To get the latest udocker script from the github development branch without
cloning the entire repository.
```
  curl https://raw.githubusercontent.com/indigo-dc/udocker/devel/udocker.py
```

To get the udocker source code repository from the github master branch, clone the 
repository, or use a web browser to access github at `https://github.com/indigo-dc/udocker`.

```
  git clone https://github.com/indigo-dc/udocker
```

To get the udocker source code repository from the development branch.

```
  git clone -b devel https://github.com/indigo-dc/udocker
```


5. BUILD
========
A distribution tarball can be built using the script build_tarball.sh in
the utils directory. The script fetches the code necessary to build the
binary executables such as proot and compiles them statically. The following
example builds the tarball from the master repository.

```
  git clone https://github.com/indigo-dc/udocker
  cd udocker/utils
  sh build_tarball.sh
```
 
6. DIRECTORIES
==============
The binary executables and containers are usually kept in the user home directory
under $HOME/.udocker this directory will contain:

* Additional tools and modules for udocker such as proot.
* Data from pulled container images (layers and metadata).
* Directory trees for the containers extracted from the layers.

The location of the udocker directory can be changed via environment variables.

* UDOCKER_DIR : change the root directory of udocker usually $HOME/.udocker
* UDOCKER_BIN : change the location of udocker related executables
* UDOCKER_LIB : change the location of udocker related libraries
* UDOCKER_CONTAINERS : change the location of container directory trees (not images)

