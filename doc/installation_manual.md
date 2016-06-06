udocker INSTALLATION MANUAL
===========================
In most circumstances the end user can download and execute the tool without
system administrator intervention. udocker itself is written in Python, but 
also uses external statically compiled binaries to provide a chroot like
environment where containers are executed. These tools do not require any
privileges.

udocker is available from github at: `https://github.com/indigo-dc/udocker`

1. DEPENDENCIES
===============
Python dependencies are described in the file requirements.txt
Most notably udocker requires either pycurl or the curl binary command,
to download both the binaries and/or pull containers from repositories.

2. USER INSTALLATION
====================
To get udocker use a git client to clone the repository, or use a web browser 
to access udocker in github at https://github.com/indigo-dc/udocker and download.

```
  git clone https://github.com/indigo-dc/udocker
```

A basic setup.py is also provided but not mandatory:

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
