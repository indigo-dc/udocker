udocker
=======
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
* Due to the way PRoot implements the chroot environment debugging inside of udocker will not work.
* udocker is mainly oriented at providing a run-time environment for containers execution in user space.
* The current version does not support dockerhub private repositories.

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

Users can download udocker and execute it from their own accounts without
requiring system administration intervention. 

udocker via PRoot offers the emulation of the root user. This emulation
mimics a real root user (e.g getuid will return 0). This is just an emulation
no root privileges are involved. This feature enables tools that do not 
require privileges but that check the user id to work properly. This enables
for instance software installation with rpm and yum inside the container.

Due to the lack of isolation features udocker must not be run by privileged users.

1.4. Basic flow
---------------
The basic flow with udocker is:

1. The user downloads udocker to its home directory and executes it
2. Upon the first execution udocker will download additional tools 
3. Container images can be fetched from dockerhub with `pull`
4. Containers can be created from the images with `create`
5. Containers can then be executed with `run`

Additionally:

* Containers saved with `docker save` can be loaded with `udocker.py load`
* Tarballs created with `docker export` can be imported with `udocker.py import`

2. INSTALLATION
===============
Installation is not required. The end user can download and execute the tool. 
To get udocker use a git client to clone the repository, or use a web browser 
to access udocker in github at https://github.com/indigo-dc/udocker and download.

```
  git clone https://github.com/indigo-dc/udocker
```

A basic setup.py is also provided but not mandatory:

```
  python setup.py install --help
  python setup.py install --home /home/user/tools
```

Upon the first time the tool is executed it will create a udocker directory 
under $HOME/.udocker The directory will contain:

* Additional tools and modules for udocker, downloaded when udocker is invoked 
* Data from pulled container images (layers and metadata)
* Directory trees for the containers extracted from the layers

The location of the udocker directory can be changed via the `UDOCKER_DIR`
environment variable.

3. COMMANDS
===========
3.1. Syntax
-----------
The udocker syntax is very similar to docker:

```
  udocker.py [GLOBAL-PARAMETERS] COMMAND [COMMAND-OPTIONS] [COMMAND-ARGUMENTS]
```

Quick examples:

```
  udocker.py --help

  udocker.py pull busybox
  udocker.py create --name=verybusy busybox
  udocker.py run -v /tmp/mydir verybusy
```

3.2. Obtaining help
-------------------
General help about available commands can be obtained with:
```
  udocker.py --help
```

Command specific help can be obtained with:
```  
  udocker.py COMMAND --help
```

3.3. search
-----------
```
  udocker.py search [OPTIONS] REPO/IMAGE:TAG
```
Search dockerhub for container images. The command displays containers one
page at a time and pauses for user input.

Options:

* `-a` display pages continously without pause.

Examples:
```
  udocker.py search busybox
  udocker.py search -a busybox
  udocker.py search indigodatacloud/docker-opencl
```

3.4. pull
---------
```
  udocker.py pull [OPTIONS] REPO/IMAGE:TAG
```
Pull a container image from dockerhub. The associated layers and metadata
is downloaded from dockerhub. Requires pycurl or the curl command.

Options:

* `--index=url` specify an index other than index.docker.io
* `--registry=url` specify a default registry other than registry-1.docker.io
* `--httpproxy=proxy` specify a socks proxy for downloading

Examples:
```
  udocker.py pull busybox
  udocker.py pull fedora:latest
  udocker.py indigodatacloud/disvis
  udocker.py pull --httpproxy=socks4://host:port busybox
  udocker.py pull --httpproxy=socks5://host:port busybox
  udocker.py pull --httpproxy=socks4://user:pass@host:port busybox
  udocker.py pull --httpproxy=socks5://user:pass@host:port busybox
```

3.5. images
-----------
```
  udocker.py images [OPTIONS]
```
List images available in the local repository, these are images pulled
form dockerhub, and/or load or imported from files.

Options:

* `-l` long format, display more information about the images and related layers

Examples:
```
  udocker.py images
  udocker.py images -l
```

3.6. create
-----------
```
  udocker.py create [OPTIONS] REPO/IMAGE:TAG
```
Extract a container from an image available in the local repository.
Requires that the image has been previously pulled from dockerhub,
and/or load or imported into the local repository from a file.
use `udocker.py images` to see the images available to create.
If sucessful the comand prints the id of the extracted container.
An easier to remember name can also be given with `--name`.

Options:

* `--name=NAME` give a name to the extracted container 

Examples:
```
  udocker.py create --name=mycontainer indigodatacloud/disvis:latest
```

3.7. ps
-------
```
  udocker.py ps
```
List extracted containers. These are not processes but containers
extracted and available to the executed with `udocker.py run`.
The command displays:

* container id
* protection mode (e.g. if can be removed with `udocker.py rm`)
* whether the container tree is writable (is in a R/W location)
* the easier to remeber name(s)
* the name of the container image from which it was extracted

Examples:
```
  udocker.py ps
```

3.8. rmi
--------
```
  udocker.py rmi [OPTIONS] REPO/IMAGE:TAG
```
Delete a local container image previously pulled/loaded/imported. 
Existing images in the local repository can be listed with `udocker.py images`.
If short of disk space deleting the image after creating the container can be
an option.

Options:

* `-f` force continuation of delete even if errors occur during the delete.

Examples:
```
  udocker.py rmi -f indigodatacloud/ambertools\_app:latest
```

3.9. rm
-------
```
  udocker.py rm CONTAINER-ID
```
Delete a previously created container. Removes the entire directory tree
extracted from the container image and associated metadata. The data in the
container tree WILL BE LOST. The container id or name can be used.

Examples:
```
  udocker.py rm 7b2d4456-9ee7-3138-ad01-63d1342d8545
  udocker.py rm mycontainer
```

3.10. inspect
-------------
```
  udocker.py inspect REPO/IMAGE:TAG
  udocker.py inspect [OPTIONS] CONTAINER-ID
```
Prints container metadata. Applies both to container images or to 
previously extracted containers, accepts both an image or container id
as input.

Options:

* `-p` with a container-id prints the pathname to the root of the container directory tree

Examples:
```
  udocker.py inspect ubuntu:latest
  udocker.py inspect d2578feb-acfc-37e0-8561-47335f85e46d
  udocker.py inspect -p d2578feb-acfc-37e0-8561-47335f85e46d
```

3.11. name
----------
```
  udocker.py name CONTAINER-ID NAME
```
Give an easier to remeber name to an extracted container.
This is an alternative to the use of `create --name=`

Examples:
```
  udocker.py name d2578feb-acfc-37e0-8561-47335f85e46d BLUE
```

3.12. rmname
------------
```
  udocker.py rmname NAME
```
Remove a name previously given to an extracted container with 
`udocker.py --name=` or with `udocker.py name`. Does not remove the container.

Examples:
```
  udocker.py rmname BLUE
```

3.13. verify
------------
```
  udocker.py verify REPO/IMAGE:TAG
```
Performs sanity checks to verify a image available in the local repository.

Examples:
```
  udocker.py verify indigodatacloud/powerfit:latest
```

3.14. import
------------
```
  udocker.py import TARBALL REPO/IMAGE:TAG
```
Imports into the local repository a tarball containing a directory tree of
a container. Can be used to import containers previously exported by docker
with `docker export`.

Examples:
```
  udocker.py import container.tar myrepo:latest
```

3.15. load
----------
```
  udocker.py load -i IMAGE-FILE
```
Loads into the local repository a tarball containing a docker image with
its layers and metadata. This is equivallent to pulling an image from
dockerhub but instead loading from a locally available file. It can be
used to load a docker image saved with `docker save`. A typical saved
image is a tarball containing additional tar files corresponding to the
layers and metadata.

Examples:
```
  udocker.py load -i docker-image.tar
```

3.16. protect
-------------
```
  udocker.py protect REPO/IMAGE:TAG
  udocker.py protect CONTAINER-ID
```
Marks an image or container against deletion by udocker.
Prevents `udocker.py rmi` and `udocker.py rm` from removing
images or containers.

Examples:
```
  udocker.py protect indigodatacloud/ambertools\_app:latest
  udocker.py protect 3d528987-a51e-331a-94a0-d278bacf79d9
```

3.17. unprotect
---------------
```
  udocker.py unprotect REPO/IMAGE:TAG
  udocker.py unprotect CONTAINER-ID
```
Removes a mark agains deletion placed by `udocker.py protect`.

Examples:
```
  udocker.py unprotect indigodatacloud/ambertools\_app:latest
  udocker.py unprotect 3d528987-a51e-331a-94a0-d278bacf79d9
```

3.18. mkrepo
------------
```
  udocker.py mkrepo DIRECTORY
```
Creates a udocker local repository in specify directory other than
the default one ($HOME/.udocker). Can be used to place the containers
in another filesystem. The created repository can then be accessed
with `udocker.py --repo=DIRECTORY COMMAND`.

Examples:
```
  udocker.py mkrepo /tmp/myrepo
  udocker.py --repo=/tmp/myrepo pull docker.io/fedora/memcached
```

3.19. run
---------
```
  udocker.py run [OPTIONS] CONTAINER-ID|CONTAINER-NAME
  udocker.py run [OPTIONS] REPO/IMAGE:TAG
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
  udocker.py pull fedora

  # create the container named myfed from the image named fedora
  udocker.py create --name=myfed  fedora

  # execute a cat inside of the container
  udocker.py run  myfed  cat /etc/redhat-release


  # In this example the host /tmp is mapped to the container /tmp
  udocker.py run --volume=/tmp  myfed  /bin/bash

  # Same as above bun run something in /tmp
  udocker.py run  -v /tmp  myfed  /bin/bash -c 'cd /tmp; ./myscript.sh'

  # Run binding a host directory inside the container to make it available
  # The host $HOME is mapped to /home/user inside the container
  # The shortest -v form is used instead of --volume=
  # The option -w same as --workdir is used to change dir to /home/user
  udocker.py run -v $HOME:/home/user -w /home/user myfed  /bin/bash

  # Install software inside the container
  udocker.py run  --user=root myfed  yum install -y firefox pulseaudio gnash-plugin

  # Run as certain uid:gid inside the container
  udocker.py run --user=1000:1001  myfed  /bin/id

  # Run firefox
  udocker.py run --bindhome --hostauth --hostenv \
     -v /sys -v /proc -v /var/run -v /dev --user=green --dri myfed  firefox
  
```


3.20. Debug
-----------
Further debugging information can be obtaining by running with `-D`.

Examples:
```
  udocker.py -D pull busybox:latest
  udocker.py -D run busybox:latest
```


Aknowlegments
=============

* PRoot http://proot.me
* INDIGO DataCloud https://www.indigo-datacloud.eu
