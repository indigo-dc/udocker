udocker USER MANUAL
===================
A basic user tool to execute simple docker containers in user space 
without requiring root privileges. Enables basic download and execution 
of docker containers by non-privileged users in Linux systems were docker 
is not available. It can be used to access and execute the content of 
docker containers in Linux batch systems and interactive clusters that 
are managed by other entities such as grid infrastructures or externaly 
managed batch or interactive systems.

udocker does not require any type of privileges nor the
deployment of services by system administrators. It can be downloaded
and executed entirely by the end user. 

udocker is a wrapper around several tools to mimic a subset of the
docker capabilities including pulling images and running then with
minimal functionality.

1. INTRODUCTION
===============
1.1. How does it work
---------------------
udocker is a simple tool written in Python, it has a minimal set
of dependencies so that can be executed in a wide range of Linux
systems. udocker does not make use of docker nor requires its 
installation.

udocker "executes" the containers by simply providing a chroot like 
environment to the extracted container. The current implementation 
uses PRoot to mimic chroot without requiring privileges.

1.2. Limitations
----------------
Since root privileges are not involved any operation that really 
requires privileges is not possible. The following are
examples of operations that are not possible:

* accessing host protected devices and files
* listening on TCP/IP privileged ports (range below 1024)
* mount file-systems
* the su command will not work
* change the system time
* changing routing tables, firewall rules, or network interfaces

Other limitations:

* The current implementation is limited to the pulling of docker images and its execution. 
* The actual containers should be built using docker and dockerfiles. 
* udocker does not provide all the docker features, and is not intended as a docker replacement.
* Due to the way PRoot implements the chroot environment debugging and system call tracing inside of udocker will not work.
* udocker is mainly oriented at providing a run-time environment for containers execution in user space.

1.3. Security
-------------
Because of the limitations described in section 1.2 udocker does not offer 
isolation features such as the ones offered by docker. If the containers
content is not trusted then they should not be executed with udocker as
they will run inside the user environment. 

The containers data will be unpacked and stored in the user home directory or 
other location of choice. Therefore the containers data will be subjected to
the same filesystem protections as other files owned by the user. If the
containers have sensitive information the files and directories should be
adequately protected by the user.

udocker does not require privileges and runs under the identity of the user 
invoking it.

Users can download the udocker tarball, install in the home directory and 
execute it from their own accounts without requiring system administration 
intervention. 

udocker provides a chroot like environment for container execution. This is
currently implemented by PRoot via the kernel ptrace system call.

udocker via PRoot offers the emulation of the root user. This emulation
mimics a real root user (e.g getuid will return 0). This is just an emulation
no root privileges are involved. This feature enables tools that do not 
require privileges but that check the user id to work properly. This enables
for instance software installation with rpm and yum inside the container.

Due to the lack of isolation features udocker must not be run by privileged 
users.

Similarly to docker, the login credentials for private repositories are stored 
in a file and can be easily stolen. Logout can be used to delete the credentials. 
If the host system is not trustable the private repositoty login feature should 
not be used as it may expose the credentials.

1.4. Basic flow
---------------
The basic flow with udocker is:

1. The user downloads udocker to its home directory and executes it
2. Upon the first execution udocker will download additional tools 
3. Container images can be fetched from dockerhub with `pull`
4. Containers can be created from the images with `create`
5. Containers can then be executed with `run`

Additionally:

* Containers saved with `docker save` can be loaded with `udocker load -i`
* Tarballs created with `docker export` can be imported with `udocker import`


2. INSTALLATION
===============
udocker can be placed in the user home directory and thus does not require
system installation. For further information see the installation manual.


3. COMMANDS
===========
3.1. Syntax
-----------
The udocker syntax is very similar to docker. Since version 1.0.1 the udocker
preferred command name changed from udocker.py to udocker. A symbolic link
between udocker and udocker.py is provided when installing with the distribution
tarball.

```
  udocker [GLOBAL-PARAMETERS] COMMAND [COMMAND-OPTIONS] [COMMAND-ARGUMENTS]
```

Quick examples:

```
  udocker --help
  udocker run --help

  udocker pull busybox
  udocker --insecure pull busybox
  udocker create --name=verybusy busybox
  udocker run -v /tmp/mydir verybusy
  udocker run verybusy /bin/ls -l /etc

  udocker pull --registry=https://registry.access.redhat.com  rhel7
  udocker create --name=rh7 rhel7
  udocker run rh7
```

3.2. Obtaining help
-------------------
General help about available commands can be obtained with:
```
  udocker --help
```

Command specific help can be obtained with:
```  
  udocker COMMAND --help
```

3.3. search
-----------
```
  udocker search [OPTIONS] REPO/IMAGE:TAG
```
Search dockerhub for container images. The command displays containers one
page at a time and pauses for user input.

Options:

* `-a` display pages continously without pause.

Examples:
```
  udocker search busybox
  udocker search -a busybox
  udocker search iscampos/openqcd
```

3.4. pull
---------
```
  udocker pull [OPTIONS] REPO/IMAGE:TAG
```
Pull a container image from a docker repository by defaulkt uses dockerhub. 
The associated layers and metadata are downloaded from dockerhub. Requires 
python pycurl or the presence of the curl command.

Options:

* `--index=url` specify an index other than index.docker.io
* `--registry=url` specify a registry other than registry-1.docker.io
* `--httpproxy=proxy` specify a socks proxy for downloading

Examples:
```
  udocker pull busybox
  udocker pull fedora:latest
  udocker pull indigodatacloudapps/disvis
  udocker pull --registry=https://registry.access.redhat.com  rhel7
  udocker pull --httpproxy=socks4://host:port busybox
  udocker pull --httpproxy=socks5://host:port busybox
  udocker pull --httpproxy=socks4://user:pass@host:port busybox
  udocker pull --httpproxy=socks5://user:pass@host:port busybox
```

3.5. images
-----------
```
  udocker images [OPTIONS]
```
List images available in the local repository, these are images pulled
form dockerhub, and/or load or imported from files.

Options:

* `-l` long format, display more information about the images and related layers

Examples:
```
  udocker images
  udocker images -l
```

3.6. create
-----------
```
  udocker create [OPTIONS] REPO/IMAGE:TAG
```
Extract a container from an image available in the local repository.
Requires that the image has been previously pulled from dockerhub,
and/or load or imported into the local repository from a file.
use `udocker images` to see the images available to create.
If sucessful the comand prints the id of the extracted container.
An easier to remember name can also be given with `--name`.

Options:

* `--name=NAME` give a name to the extracted container 

Examples:
```
  udocker create --name=mycontainer indigodatacloud/disvis:latest
```

3.7. ps
-------
```
  udocker ps
```
List extracted containers. These are not processes but containers
extracted and available to the executed with `udocker run`.
The command displays:

* container id
* protection mode (e.g. whether can be removed with `udocker rm`)
* whether the container tree is writable (is in a R/W location)
* the easier to remeber name(s)
* the name of the container image from which it was extracted

Examples:
```
  udocker ps
```

3.8. rmi
--------
```
  udocker rmi [OPTIONS] REPO/IMAGE:TAG
```
Delete a local container image previously pulled/loaded/imported. 
Existing images in the local repository can be listed with `udocker images`.
If short of disk space deleting the image after creating the container can be
an option.

Options:

* `-f` force continuation of delete even if errors occur during the delete.

Examples:
```
  udocker rmi -f indigodatacloud/ambertools\_app:latest
```

3.9. rm
-------
```
  udocker rm CONTAINER-ID
```
Delete a previously created container. Removes the entire directory tree
extracted from the container image and associated metadata. The data in the
container tree WILL BE LOST. The container id or name can be used.

Examples:
```
  udocker rm 7b2d4456-9ee7-3138-ad01-63d1342d8545
  udocker rm mycontainer
```

3.10. inspect
-------------
```
  udocker inspect REPO/IMAGE:TAG
  udocker inspect [OPTIONS] CONTAINER-ID
```
Prints container metadata. Applies both to container images or to 
previously extracted containers, accepts both an image or container id
as input.

Options:

* `-p` with a container-id prints the pathname to the root of the container directory tree

Examples:
```
  udocker inspect ubuntu:latest
  udocker inspect d2578feb-acfc-37e0-8561-47335f85e46d
  udocker inspect -p d2578feb-acfc-37e0-8561-47335f85e46d
```

3.11. name
----------
```
  udocker name CONTAINER-ID NAME
```
Give an easier to remeber name to an extracted container.
This is an alternative to the use of `create --name=`

Examples:
```
  udocker name d2578feb-acfc-37e0-8561-47335f85e46d BLUE
```

3.12. rmname
------------
```
  udocker rmname NAME
```
Remove a name previously given to an extracted container with 
`udocker --name=` or with `udocker name`. Does not remove the container.

Examples:
```
  udocker rmname BLUE
```

3.13. verify
------------
```
  udocker verify REPO/IMAGE:TAG
```
Performs sanity checks to verify a image available in the local repository.

Examples:
```
  udocker verify indigodatacloud/powerfit:latest
```

3.14. import
------------
```
  udocker import [OPTIONS] TARBALL REPO/IMAGE:TAG
```
Imports into the local repository a tarball containing a directory tree of
a container. Can be used to import containers previously exported by docker
with `docker export`.

Options:

* `--mv` move the container file instead to copy to save space.

Examples:
```
  udocker import container.tar myrepo:latest
  udocker import --mv container.tar myrepo:latest
```

3.15. load
----------
```
  udocker load -i IMAGE-FILE
```
Loads into the local repository a tarball containing a docker image with
its layers and metadata. This is equivallent to pulling an image from
dockerhub but instead loading from a locally available file. It can be
used to load a docker image saved with `docker save`. A typical saved
image is a tarball containing additional tar files corresponding to the
layers and metadata.

Examples:
```
  udocker load -i docker-image.tar
```

3.16. protect
-------------
```
  udocker protect REPO/IMAGE:TAG
  udocker protect CONTAINER-ID
```
Marks an image or container against deletion by udocker.
Prevents `udocker rmi` and `udocker rm` from removing
images or containers.

Examples:
```
  udocker protect indigodatacloud/ambertools\_app:latest
  udocker protect 3d528987-a51e-331a-94a0-d278bacf79d9
```

3.17. unprotect
---------------
```
  udocker unprotect REPO/IMAGE:TAG
  udocker unprotect CONTAINER-ID
```
Removes a mark agains deletion placed by `udocker protect`.

Examples:
```
  udocker unprotect indigodatacloud/ambertools\_app:latest
  udocker unprotect 3d528987-a51e-331a-94a0-d278bacf79d9
```

3.18. mkrepo
------------
```
  udocker mkrepo DIRECTORY
```
Creates a udocker local repository in specify directory other than
the default one ($HOME/.udocker). Can be used to place the containers
in another filesystem. The created repository can then be accessed
with `udocker --repo=DIRECTORY COMMAND`.

Examples:
```
  udocker mkrepo /tmp/myrepo
  udocker --repo=/tmp/myrepo pull docker.io/fedora/memcached
  udocker --repo=/tmp/myrepo images
```

3.19. run
---------
```
  udocker run [OPTIONS] CONTAINER-ID|CONTAINER-NAME
  udocker run [OPTIONS] REPO/IMAGE:TAG
```
Executes a container. The execution is performed using an external
tool currently only PRoot is supported. The container can be specified
using the container id or its associated name. Additionaly it is
possible to invoke run with an image name, in this case the image is
extracted and run is invoked over the newly extracted container. 
Using this later approach will create multiple container directory
trees possibly occuping considerable disk space.

Options:

* `--rm` delete the container after execution
* `--workdir=PATH` specifies a working directory within the container
* `--user=NAME` username or uid:gid inside the container
* `--volume=DIR:DIR` map an host file or directory to appear inside the container
* `--novol=DIR` excludes a host file or directory from being mapped
* `--env="VAR=VAL"` set environment variables
* `--hostauth` make the host /etc/passwd and /etc/group appear inside the container
* `--nosysdirs` prevent udocker from mapping /proc /sys /run and /dev inside the container
* `--nometa` ignore the container metadata settings
* `--hostenv` pass the user host environment to the container
* `--name=NAME` set or change the name of the container useful if running from an image
* `--bindhome` attempt to make the user home directory appear inside the container
* `--kernel=KERNELID` use a specific kernel id to emulate useful when the host kernel is too old
* `--location=DIR` execute a container in a certain directory

Examples:
```
  # Pull fedora from dockerhub
  udocker pull fedora

  # create the container named myfed from the image named fedora
  udocker create --name=myfed  fedora

  # execute a cat inside of the container
  udocker run  myfed  cat /etc/redhat-release


  # In this example the host /tmp is mapped to the container /tmp
  udocker run --volume=/tmp  myfed  /bin/bash

  # Same as above bun run something in /tmp
  udocker run  -v=/tmp  myfed  /bin/bash -c 'cd /tmp; ./myscript.sh'

  # Run binding a host directory inside the container to make it available
  # The host $HOME is mapped to /home/user inside the container
  # The shortest -v form is used instead of --volume=
  # The option -w same as --workdir is used to change dir to /home/user
  udocker run -v=$HOME:/home/user -w=/home/user myfed  /bin/bash

  # Install software inside the container
  udocker run  --user=root myfed  yum install -y firefox pulseaudio gnash-plugin

  # Run as certain uid:gid inside the container
  udocker run --user=1000:1001  myfed  /bin/id

  # Run firefox
  udocker run --bindhome --hostauth --hostenv \
     -v /sys -v /proc -v /var/run -v /dev --user=green --dri myfed  firefox
  
  # Run in a script
  udocker run ubuntu  /bin/bash <<EOF
cd /etc
ls -l
cat lsb-release
EOF

```


3.20. Debug
-----------
Further debugging information can be obtaining by running with `-D`.

Examples:
```
  udocker -D pull busybox:latest
  udocker -D run busybox:latest
```

3.21. Login
-----------
```
  udocker login [--username=USERNAME] [--password=PASSWORD] [--registry=REGISTRY]
```
Login into a docker registry using v2 API. Only basic authentication
using username and password is supported. The username and password
can be prompted or specified in the command line. The username is the
username in the repository, not the associated email address.

Options:

* `--username=USERNAME` provide the username in the command line
* `--password=PASSWORD` provide the password in the command line
* `--registry=REGISTRY` credentials are for this registry

Examples:
```
  udocker login --username=xxxx --password=yyyy

  udocker login --registry="https://hostname:5000"
  username: xxxx
  password: ****
```

3.22. Logout
------------
```
  udocker logout [-a]
```
Delete the login credentials (username and password) stored by
previous logins. Without arguments deletes the credentials for 
the current registry. To delete all registry credentials use -a.

Options:

* `-a` delete all credentials from previous logins
* `--registry=REGISTRY` delete credentials for this registry

Examples:
```
  udocker logout
  udocker logout --registry="https://hostname:5000"
  udocker logout -a
```


Aknowlegments
=============

* PRoot http://proot.me
* INDIGO DataCloud https://www.indigo-datacloud.eu
