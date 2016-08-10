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
Most notably udocker requires either pycurl or the curl binary command,
to download both the binaries and/or pull containers from repositories.

2. USER INSTALLATION
====================
The official release of udocker is available from the INDIGO-DataCloud
repository at `http://repo.indigo-datacloud.eu/` where is made available
as a tarball to be deployed by the end user. Example:

```
  cd $HOME
  wget -O- http://repo.indigo-datacloud.eu/repository/indigo/1/centos7/x86_64/tgz/udocker-v1.0.0.tar.gz | tar xzvf -
```

To get the latest udocker source code from github clone the repository, or use
a web browser to access github at `https://github.com/indigo-dc/udocker`.

```
  git clone https://github.com/indigo-dc/udocker
```

A basic setup.py is also provided in the source code:

```
  python setup.py install --help
  python setup.py install --home /home/USER/bin
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

4. REMARKS
==========
Upon the first time the tool is executed it will create a udocker directory 
under $HOME/.udocker The directory will contain:

* Additional tools and modules for udocker, downloaded when udocker is invoked 
* Data from pulled container images (layers and metadata)
* Directory trees for the containers extracted from the layers

The location of the udocker directory can be changed via the `UDOCKER_DIR`
environment variable. 
