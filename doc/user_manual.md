# udocker USER MANUAL

A basic user tool to execute simple Docker containers in user space 
without requiring root privileges. udocker enables basic download and execution 
of Docker containers by non-privileged users in Linux systems where Docker 
is not available. It can be used to access and execute the content of 
docker containers in Linux batch systems and interactive clusters that 
are managed by other entities such as grid infrastructures, HPC clusters
or other externally managed batch or interactive systems.

udocker does not require any type of privileges nor the deployment of 
services by system administrators. It can be downloaded and executed 
entirely by the end user. 

udocker is a wrapper around several tools and technologies to mimic a 
subset of the Docker capabilities including pulling images and running 
then with minimal functionality. It is mainly meant to execute user 
applications packaged in Docker containers. 

We recommend the use of Docker whenever possible, but when it is 
unavailable udocker can be the right tool to run your applications.

## 1. INTRODUCTION

### 1.1. How does it work
udocker is a simple tool written in Python, it has a minimal set of 
dependencies so that can be executed in a wide range of Linux systems. 
udocker does not make use of Docker nor requires its installation.

udocker "executes" the containers by simply providing a chroot like 
environment to the extracted container. udocker is meant to integrate
several technologies and approaches hence providing an integrated environment
that offers several execution options. This version provides execution engines
based on PRoot, Fakechroot, runC and Singularity to facilitate the execution
of Docker containers without privileges.

The basic usage flow starts by downloading the image from an image repository
in the usual way; create the container out of that image (flatenning the image
on the filesystem), and finally run the container with the name we gave it in
the creation process:

  * `udocker pull` busybox
  * `udocker create` --name=verybusy busybox
  * `udocker run` verybusy

This sequence allows the created container to be executed many times. If simultaneous
executions are envisage just make sure that input/output files are not overwritten by
giving them different names during execution as the container will be shared among
executions.

Containers can also be pulled, created and executed in a single step. However in this
case a new container is created for every run invocation thus occupying more storage
space. To pull, create and execute in a single step invoke run with an image name
instead of container name:

 * `udocker run` busybox

### 1.2. Limitations
Since root privileges are not involved, any operation that really requires privileges
is not possible. The following are examples of operations that are not possible:

* accessing host protected devices and files;
* listening on TCP/IP privileged ports (range below 1024);
* mount file-systems;
* the su command will not work;
* change the system time;
* changing routing tables, firewall rules, or network interfaces.

Other limitations:

* the current implementation is limited to the pulling of Docker images and its execution;
* the actual containers should be built using Docker and dockerfiles;
* udocker does not provide all the Docker features, and is not intended as a Docker replacement;
* debugging and tracing in the PRoot engine will not work;
* the Fakechroot engine does not support execution of statically linked executables;
* udocker is mainly oriented at providing a run-time environment for containers execution in user space.

### 1.3. Security
Because of the limitations described in section 1.2 udocker does not offer 
isolation features such as the ones offered by Docker. If the containers
content is not trusted then they should not be executed within udocker as
they will run inside the user environment. 

Due to the lack of isolation features udocker must not be run by privileged 
users.

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
currently implemented by:

* PRoot engine via the kernel ptrace system call;
* Fakechroot engine via shared library preload;
* runC engine using rootless namespaces;
* Singularity if available in the host system.

udocker via PRoot offers the emulation of the root user. This emulation
mimics a real root user (e.g getuid will return 0). This is just an emulation
no root privileges are involved. This feature enables tools that do not 
require privileges but that check the user id to work properly. This enables
for instance software installation with rpm and yum inside the container.

Similarly to Docker, the login credentials for private repositories are stored 
in a file and can be easily accessed. Logout can be used to delete the credentials. 
If the host system is not trustable the login feature should not be used as it may
expose the login credentials.

### 1.4. Basic flow
The basic flow with udocker is:

1. The user downloads udocker to its home directory and executes it
2. Upon the first execution udocker will download additional tools 
3. Container images can be fetched from Docker Hub with `pull`
4. Containers can be created from the images with `create`
5. Containers can then be executed with `run`

Additionally:

* Containers saved with `docker save` can be loaded with `udocker load -i`
* Tarballs created with `docker export` can be imported with `udocker import`


## 2. INSTALLATION

udocker can be placed in the user home directory and thus does not require
system installation. For further information see the installation manual.


## 3. COMMANDS

### 3.1. Syntax
The udocker syntax is very similar to Docker. Since version 1.0.1 the udocker
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

### 3.2. Obtaining help
General help about available commands can be obtained with:
```
  udocker --help
```

Command specific help can be obtained with:
```  
  udocker COMMAND --help
```

### 3.3. install
```
  udocker install [OPTIONS]
```
Install of udocker tools. Pulls the tools and installs them in the user
home directory under `$HOME/.udocker` or in a location defined by the
environment variable `UDOCKER_DIR`. The pulling may attempt several 
mirrors.

Options:

* `--force` force installation, useful to reinstall.
* `--purge` remove files from older installations. 

Examples:
```
  udocker install
  udocker install --force --purge
```

### 3.4. search
```
  udocker search [-a] STRING
  udocker search --list-tags REPO/IMAGE
```
Search Docker Hub for container images. The command displays containers one
page at a time and pauses for user input. Not all registries have search
capabilities.

Options:

* `-a` display pages continuously without pause.
* `--list-tags` list the tags for a given repository

Examples:
```
  udocker search busybox
  udocker search -a busybox
  udocker search iscampos/openqcd
  udocker search --list-tags centos
```

### 3.5. pull
```
  udocker pull [OPTIONS] REPO/IMAGE:TAG
```
Pull a container image from a docker repository by default uses dockerhub. 
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
  udocker pull quay.io/something/somewhere
  udocker pull --httpproxy=socks4://host:port busybox
  udocker pull --httpproxy=socks5://host:port busybox
  udocker pull --httpproxy=socks4://user:pass@host:port busybox
  udocker pull --httpproxy=socks5://user:pass@host:port busybox
```

### 3.6. images
```
  udocker images [OPTIONS]
```
List images available in the local repository, these are images pulled
form Docker Hub, and/or load or imported from files.

Options:

* `-l` long format, display more information about the images and related layers

Examples:
```
  udocker images
  udocker images -l
```

### 3.7. create
```
  udocker create [OPTIONS] REPO/IMAGE:TAG
```
Extract a container from an image available in the local repository.
Requires that the image has been previously pulled from Docker Hub,
and/or load or imported into the local repository from a file.
use `udocker images` to see the images available to create.
If successful the command prints the id of the extracted container.
An easier to remember name can also be given with `--name`.

Options:

* `--name=NAME` give a name to the extracted container 

Examples:
```
  udocker create --name=mycontainer indigodatacloud/disvis:latest
```

### 3.8. ps
```
  udocker ps [options]
```
List extracted containers. These are not processes but containers
extracted and available to the executed with `udocker run`.
The command displays:

* container id
* protection mode (e.g. whether can be removed with `udocker rm`)
* whether the container tree is writable (is in a R/W location)
* the easier to remember name(s)
* the name of the container image from which it was extracted
* with option -m adds the execution mode
* with option -s adds the container current size in MB

Options:

* `-m` show the current execution mode of each container
* `-s` show current disk usage (container size in MB), can be very slow

Examples:
```
  udocker ps
```

### 3.9. rmi
```
  udocker rmi [OPTIONS] REPO/IMAGE:TAG
```
Delete a local container image previously pulled/loaded/imported. 
Existing images in the local repository can be listed with `udocker images`.
If short of disk space deleting the image after creating the container can be
an option.

Options:

* `-f` force removal independently from errors

Examples:
```
  udocker rmi -f indigodatacloud/ambertools\_app:latest
```

### 3.10. rm
```
  udocker rm [options] CONTAINER-ID
```
Delete a previously created container. Removes the entire directory tree
extracted from the container image and associated metadata. The data in the
container tree WILL BE LOST. The container id or name can be used.

Options:

* `-f` force removal by changing file permissions

Examples:
```
  udocker rm 7b2d4456-9ee7-3138-ad01-63d1342d8545
  udocker rm mycontainer
```

### 3.11. inspect
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

### 3.12. name
```
  udocker name CONTAINER-ID NAME
```
Give an easier to remember name to an extracted container.
This is an alternative to the use of `create --name=`

Examples:
```
  udocker name d2578feb-acfc-37e0-8561-47335f85e46d BLUE
```

### 3.13. rmname
```
  udocker rmname NAME
```
Remove a name previously given to an extracted container with 
`udocker --name=` or with `udocker name`. Does not remove the container.

Examples:
```
  udocker rmname BLUE
```

### 3.14. rename
```
  udocker rename NAME NEWNAME
```
Change a container name previously given to an extracted container with 
`udocker --name=` or with `udocker name`. Does not change the container id.

Examples:
```
  udocker rename BLUE GREEN
```

### 3.15. verify
```
  udocker verify REPO/IMAGE:TAG
```
Performs sanity checks to verify a image available in the local repository.

Examples:
```
  udocker verify indigodatacloud/powerfit:latest
```

### 3.16. import
```
  udocker import [OPTIONS] TARBALL|- REPO/IMAGE:TAG
```

Import a tarball from file or stdin. The tarball can be imported into a new
image or container. Without options can be used to import a container exported 
by Docker (with `docker export`) creating a new image in the local repository. 
When using `--tocontainer`  allows importing directly into containers without 
creating images in the local repository.
Use `--tocontainer` alone to import a container exported by docker 
(with `docker export`) into a new container without creating an image. 
Use `--clone` to import a udocker container 
(e.g. exported with `udocker export --clone`) into a new container also 
without creating an image and allowing to preserve the container metadata
and udocker execution modes. The option `--name=` adds a name alias to the
created container, is used in conjunction with `--tocontainer` or `--clone`.

Options:

* `--mv` move the container tarball instead of copy to save space.
* `--tocontainer` import directly into a container.
* `--clone` import udocker container format with both metadata and container
* `--name=ALIAS` with `--tocontainer` or `--clone` to give an alias to the container

Examples:
```
  udocker import docker_container.tar myrepo:latest
  udocker import - myrepo:latest < docker_container.tar
  udocker import --mv docker_container.tar myrepo:latest
  udocker import --tocontainer --name=BLUE docker_container.tar 
  udocker import --clone --name=RED udocker_container.tar 
```

### 3.17. load
```
  udocker load -i IMAGE-FILE
  udocker load -i IMAGE-FILE NAME
  udocker load -
```
Loads into the local repository a tarball containing a Docker image with
its layers and metadata. This is equivalent to pulling an image from
Docker Hub but instead loading from a locally available file. It can be
used to load a Docker image saved with `docker save`. A typical saved
image is a tarball containing additional tar files corresponding to the
layers and metadata. From version 1.1.4 onwards, udocker can also load 
images in OCI format.
The optional NAME argument can be used to change the name of the loaded 
image. This argument is particularly relevant to provide adequate names
to OCI loaded images as these frequently only provide tag names. If an 
OCI image does not provide a name and the argument NAME is also not 
provided in the command line, then udocker will generate a random name.

Examples:
```
  udocker load -i docker-image.tar
  udocker load - < docker-image.tar
  udocker load -i oci-image.tar test-image
```

### 3.18. protect
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

### 3.19. unprotect
```
  udocker unprotect REPO/IMAGE:TAG
  udocker unprotect CONTAINER-ID
```
Removes a mark against deletion placed by `udocker protect`.

Examples:
```
  udocker unprotect indigodatacloud/ambertools\_app:latest
  udocker unprotect 3d528987-a51e-331a-94a0-d278bacf79d9
```

### 3.20. mkrepo
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

### 3.21. run
```
  udocker run [OPTIONS] CONTAINER-ID|CONTAINER-NAME
  udocker run [OPTIONS] REPO/IMAGE:TAG
```
Executes a container. The execution several execution engines are
provided. The container can be specified using the container id or its
associated name. Additionally it is possible to invoke run with an image
name, in this case the image is extracted and run is invoked over the
newly extracted container. Using this later approach will create multiple
container directory trees possibly occupying considerable disk space, 
therefore the recommended approach is to first extract a container using
"udocker create" and only then execute with "udocker run". The same
extracted container can then be executed as many times as required without
duplication.

udocker provides several execution modes to support the actual execution
within a container. Execution modes can be changed using the command
`udocker setup --execmode=<mode> <container-id>` for more information
on available modes and their characteristics see section 3.25.

Options:

* `--rm` delete the container after execution
* `--workdir=PATH` specifies a working directory within the container
* `--user=NAME` username or uid:gid inside the container
* `--volume=DIR:DIR` map an host file or directory to appear inside the container
* `--novol=DIR` excludes a host file or directory from being mapped
* `--env="VAR=VAL"` set environment variables
* `--env-file=FILE` load environment variables from file
* `--hostauth` obtain user account from the host and add it to the container passwd and group
* `--containerauth` use the container passwd and group directly without binding files
* `--nosysdirs` prevent udocker from mapping /proc /sys /run and /dev inside the container
* `--nometa` ignore the container metadata settings
* `--hostenv` pass the user host environment to the container
* `--cpuset-cpus=<1,2-3>` CPUs in which to allow execution
* `--name=NAME` set or change the name of the container useful if running from an image
* `--bindhome` attempt to make the user home directory appear inside the container
* `--kernel=KERNELID` use a specific kernel id to emulate useful when the host kernel is too old
* `--location=DIR` execute a container in a given directory

Options valid only in Pn execution modes:

* `--publish=HOST_PORT:CONT_PORT` map a container port to another host port
* `--publish-all` map all container ports to random different ones

Options valid only in Rn execution modes:

* `--device=/dev/xxx` pass device to container

Examples:
```
  # Pull fedora from Docker Hub
  udocker pull fedora:29

  # create the container named myfed from the image named fedora
  udocker create --name=myfed  fedora:29

  # execute a cat inside of the container
  udocker run  myfed  cat /etc/redhat-release

  # The above three operations could have done with a single command
  # However each time udocker is invoked this way a new container
  # directory tree is created consuming additional space and time
  udocker run fedora:29 cat /etc/redhat-release

  # In this example the host /tmp is mapped to the container /tmp
  udocker run --volume=/tmp  myfed  /bin/bash

  # Same as above but running something in /tmp
  udocker run  -v=/tmp  myfed  /bin/bash -c "cd /tmp; ./myscript.sh"

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
cat motd
cat lsb-release
EOF


  # Search and pull from another repository than dockerhub
  # First search for the expression `myrepo` in quay.io 
  # Second list the tags for a given image in quay.io
  # Third finally pull a given image:tag from quay.io
  udocker search quay.io/myrepo
  udocker search --list-tags quay.io/myrepository/myimage
  udocker pull quay.io/myrepository/myimage:v2.3.1

  # Run container in a given directory tree using the DEFAULT EXECUTION MODE 
  # Below ROOT is the complete directory structure of the container operating system
  # This enables udocker to execute directory trees created by other tools
  # Much of the udocker functionality is not usable when using --location
  ./udocker run --location=/tmp/u/containers/07b3226e-6513-3f85-884f-e3cfdd2fbc0e/ROOT
```


### 3.22. Debug and Verbosity
Further debugging information can be obtaining by running with `-D`.

Examples:
```
  udocker -D pull busybox:latest
  udocker -D run busybox:latest
```

The options '-q' or '--quiet' can be specified before each command 
to reduce verbosity. The verbosity level can also be specified by 
assigning a value between 0 and 5 to the environment variable 
UDOCKER_LOGLEVEL.

Examples:
```
  udocker -q run busybox:latest /bin/ls
  UDOCKER_LOGLEVEL=2 udocker run busybox:latest /bin/ls
```


### 3.23. login
```
  udocker login [--username=USERNAME] [--password=PASSWORD] [--registry=REGISTRY]
```
Login into a Docker registry using v2 API. Only basic authentication
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

### 3.24. logout
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

### 3.25. clone
```
  udocker clone [--name=NAME] CONTAINER-ID|CONTAINER-NAME
```
Duplicate an existing container creating a complete replica. The replica receives a different CONTAINER-ID. An alias can be assigned to the newly created container by using `--name=NAME`.

Options:

* `--name=NAME` assign a name alias to the newly created container

Examples:
```
  udocker clone f24771be-f0bb-3046-80f0-db301e099517
  udocker clone --name=RED  f24771be-f0bb-3046-80f0-db301e099517
  udocker clone --name=RED  BLUE
```

### 3.26. save
```
  udocker save -o IMAGE-FILE REPO/IMAGE:TAG
  udocker save -o - REPO/IMAGE:TAG
```
Saves an image including all its layers and metadata to a tarball.
The input is an image not a container, to produce a tarball of a 
container use export. The saved images can be read by udocker or Docker
using the command load.

Examples:
```
  udocker save -o docker-image.tar centos:centos7
  udocker save -o - > docker-image.tar ubuntu:16.04 ubuntu:18.04 ubuntu:19.04
```

### 3.27. setup
```
  udocker setup [--execmode=XY] [--force] [--nvidia] [--purge] CONTAINER-ID|CONTAINER-NAME
```
With `--execmode` chooses an execution mode to define how a given container 
will be executed, namelly enables selection of an execution engine and 
its related execution modes. Without options, setup will print the current 
execution mode for the given container. 
The option `--nvidia` enables access to GPGPUs by adding the necessary host 
libraries to the container.
The option `--force` can be used both with `--execmode` and with `--nvidia` to 
force the setup of the container to the specified mode.
The option `--purge` removes mountpoints, auxiliary files and directories 
created by udockr inside the container directory tree to support its execution.
It should only be invoked when there is no execution taking place as it may
affect processes running in the container tree.

Options:

* `--execmode=XY` choose an execution mode
* `--nvidia`  enable access to GPGPUs
* `--force` force the selection of the execution mode, can be used to
  force the change of an execution mode when it fails namely if it is
  transferred to a remote host while in one of the Fn modes. Can be
  used with --nvidia.
* `--purge` remove mountpoints, auxiliary files and directories created
  by udocker to support the container execution.

|Mode| Engine      | Description                               | Changes container
|----|:------------|:------------------------------------------|:------------------
| P1 | PRoot       | accelerated mode using seccomp            | No
| P2 | PRoot       | seccomp accelerated mode disabled         | No
| F1 | Fakechroot  | exec with direct loader invocation        | symbolic links
| F2 | Fakechroot  | F1 plus modified loader                   | F1 + ld.so
| F3 | Fakechroot  | fix ELF headers in binaries               | F2 + ELF headers
| F4 | Fakechroot  | F3 plus enables new executables and libs  | same as F3
| R1 | runC        | rootless user mode namespaces             | resolv, passwd
| R2 | runC        | R1 plus P1 for software installation      | resolv, passwd, proot
| R3 | runC        | R1 plus P2 for software installation      | resolv, passwd, proot
| S1 | Singularity | uses singularity if available in the host | passwd

The default execution mode is P1 using PRoot and starting in root
emulation mode.

The mode P2 also uses PRoot and although has lower performance than P1 
can be more reliable. The mode P1 uses PRoot with 
SECCOMP syscall filtering which provides higher performance in most 
operating systems. PRoot provides the most universal execution mode
in udocker but may also exhibit lower performance on older kernels 
such as in CentOS 6 systems.
The Pn modes also offer root emulation to facilitate software installation
and to execute applications that expect to run under root.

The Fakechroot (Fn), runC (Rn) and Singularity (Sn) engines are EXPERIMENTAL.
They provide higher performance in most cases, but are less universal thus
supporting less Linux distributions. 

The udocker Fakechroot engine has four modes that offer increasing
compatibility levels. F1 is the least intrusive mode and only changes 
absolute symbolic links so that they point to locations inside the 
container.  F2 adds changes to the loader to prevent loading of host 
shareable libraries. F3 adds changes to all binaries (ELF headers of 
executables and libraries) to remove absolute references pointing to 
the host shareable libraries. These changes are performed once during 
the setup, executables added after setup will not have their ELF headers 
fixed and will fail to run. Notice that setup can be rerun with the 
--force option to fix these binaries. F4 performs the ELF header
changes dynamically (on-the-fly) thus enabling compilation and linking 
within the container and new executables to be transferred to the 
container and executed. Executables and libraries in host volumes are
not changed and hence cannot be executed from a container in F2, F3 and
F4 execution modes.
runC with rootless user namespaces requires a recent Linux kernel and
is known to work on Ubuntu and Fedora hosts. 

Mode Rn requires kernels with support for rootless containers, thus
it will not work on some distributions (e.g. CentOS 6 and CentOS 7).
The rootless execution modes have inherent limitations related to the
manipulation of uids and gids that may cause certain operations to fail
such as software installations. To overcome this limitation of the R1 
execution mode, udocker provides the R2 and R3 execution modes that 
combine runc with the proot uid/gid emulation. In these modes the 
execution chain is 

`runc -> proot -> executable`

When using the Rn modes, udocker will search for a runc executable in the
host system, only if it does not find one it will default to use the runc
provided with the udockertools. This behavior can be change through
environment variables and configuration settings.
Fakechroot requires libraries compiled for each guest operating system,
udocker provides these libraries for several distributions including
Ubuntu 14, Ubuntu 16, Ubuntu 18, CentOS 6 and CentOS 7 and some others. 
Other guests may or may not work with these same libraries. 

Notice that changes performed in Fn and Rn modes will prevent the
containers from running in hosts where the directory path to the container
is different. In this case convert back to P1 or P2, transfer to the target 
host, and then convert again from Pn to the desired Fn mode.
 
Singularity must be available in the host system for execution mode S1.
Newer versions of Singularity may run without requiring privileges but
need a recent kernel in the host system with support for rootless user 
mode namespaces similar to runC in mode R1.
Singularity cannot be compiled statically due to dependencies on
dynamic libraries and therefore is not provided with udocker.
In CentOS 6 and CentOS 7 Singularity must be installed with privileges
by a system administrator as it requires suid or capabilities.
The S1 mode also offers root emulation to facilitate software installation
and to execute applications that expected to run under root.
 
Examples:

```
  udocker create --name=mycontainer  fedora:25

  udocker setup --execmode=F3  mycontainer
  udocker setup  mycontainer                 # prints the execution mode

  udocker run  mycontainer /bin/ls

  udocker setup  --execmode=F4  mycontainer
  udocker run  mycontainer /bin/ls

  udocker setup  --execmode=P1  mycontainer
  udocker run  mycontainer  /bin/ls

  udocker setup  --execmode=R1  mycontainer
  udocker run  mycontainer  /bin/ls

  udocker setup  --execmode=S1  mycontainer
  udocker run  mycontainer  /bin/ls
```

The default execution mode of udocker can also be changed. This has however
several limitations, therefore the recommended method to change the execution
mode is via the `udocker setup` command. The default execution mode can be 
changed through the configuration files by changing the attribute 
**default_execution_mode** or through the environment variable 
**UDOCKER_DEFAULT_EXECUTION_MODE**. Only the following modes can be used as
default modes:
**P1**, **P2**, **F1**, **S1**, and **R1**. Changing the default execution
mode can be useful in case the default does not work as expected.

Example:

```
  UDOCKER_DEFAULT_EXECUTION_MODE=P2 ./udocker run mycontainer /bin/ls
```

## 4. RUNNING MPI JOBS

In this section we will use the Lattice QCD simulation software openQCD to
demonstrate how to run Open MPI applications with udocker 
(http://luscher.web.cern.ch/luscher/openQCD). Lattice QCD simulations are
performed on high-performance parallel computers with hundreds and thousands
of processing units. All the software environment that is needed for openQCD
is a compliant C compiler and a local MPI installation such as Open MPI. 

In what follows we describe the steps to execute openQCD using udocker in a
HPC system with a batch system (e.g. SLURM). An analogous procedure can be
followed for other MPI applications.

A container image of openQCD can be downloaded from the Docker Hub repository.
From this image a container can be extracted to the filesystem (using udocker
create) as described below.


```
./udocker pull iscampos/openqcd
./udocker create --name=openqcd iscampos/openqcd
fbeb130b-9f14-3a9d-9962-089b4acf3ea8
```

Next the created container is executed (notice that the variable LD_LIBRARY_PATH is explicitly set):


```
./udocker run -e LD_LIBRARY_PATH=/usr/lib openqcd /bin/bash
```

In this approach the host mpiexec will submit the N MPI process instances, as
containers, in such a way that the containers are able to communicate via the
low latency interconnect (Infiniband in the case at hand).

For this approach to work, the code in the container needs to be compiled with
the same version of MPI that is available in the HPC system. This is necessary 
because the Open MPI versions of mpiexec and orted available in the host system
need to match with the compiled program. In this example the Open MPI version 
is v2.0.1. Therefore we need to download this version and compile it inside the
container.

Note: first the example Open MPI installation that comes along with the openqcd
container are removed with: 

```
yum remove openmpi
```

We download Open MPI v.2.0.1 from https://www.open-mpi.org/software/ompi/v2.0 and compile it. 

Openib and libibverbs need to be install to compile Open MPI over Infiniband. For that,
install the epel repository on the container. This step is not required if running using 
TCP/IP is enough.

To install the Infiniband drivers one needs to install the epel repository.

```
yum install -y epel-release
```

The list of packages to be installed is:

```
openib
libibverbs, libibverbs-utils, libibverbs-devel
librdmacm, librdmacm-utils, ibacm
libnes
libibumad
libfabric, libfabric-devel
opensm-libs
swig
ibutils-libs, ibutils
opensm
libibmad
infiniband-diags
```

The driver needs to be installed as well, in our examples the Mellanox driver.

```
yum install mlx4*x86_64
```

The installation of both, i686 and x86_64 versions might be conflictive, and lead to an 
error ("libibverbs: Warning: no userspace device-specific driver found for 
/sys/class/infiniband_verbs/uverbs0) if for example the i686 is used. The best approach 
is to install only the version for the architecture of the machine in this case x86_64.

The Open MPI source is compiled and installed in the container under /usr for convenience:

```
cd /usr
tar xvf openmpi-2.0.1.tgz 
cd /usr/openmpi-2.0.1
./configure --with-verbs --prefix=/usr
make
make install
```


OpenQCD can then be compiled inside the udocker container in the usual way. 
The MPI job submission to the HPC cluster succeeds by including this line in 
the batch script:

```
/opt/cesga/openmpi/2.0.1/gcc/6.3.0/bin/mpiexec -np 128 \
$LUSTRE/udocker-master/udocker run -e LD_LIBRARY_PATH=/usr/lib  \
--hostenv --hostauth --user=cscdiica -v /tmp \
--workdir=/op/projects/openQCD-1.6/main openqcd \
/opt/projects/openQCD-1.6/main/ym1 -i ym1.in -noloc 
```
(where $LUSTRE points to the appropriate user filesystem directory in the HPC system)

Notice that depending on the application and host operating system a variable 
performance degradation may occur when using the default execution mode (Pn). In 
this situation other execution modes (such as Fn) may provide significantly higher
performance. The command `udocker setup --execmode=<mode> <container-id>` can be used to change
between execution modes (see section 3.25).


## 5. ACCESSING GP/GPUs

The host (either the physical machine or VM) where the container will run has to have
the NVIDIA driver installed. Moreover, the NVIDIA driver version has to be known apriori,
since the docker image has to have the exact same version as the host

The command `udocker setup --nvidia <container-id>` can be used to prepare the 
container with the drivers necessary to run with nvidia GPGPUs. This will copy
the required files from the host into the container. 

Another different approach is to have docker images already prepared with the driver
files but they must match what is being used in the target host. For instance base
docker images with several version of the NVIDIA driver can be found in dockerhub:

* https://hub.docker.com/r/lipcomputing/nvidia-ubuntu16.04/
* https://hub.docker.com/r/lipcomputing/nvidia-centos7/

In the tags tab one can check which versions are available. Dockerfiles and Ansible
roles used to build these images are in the github repository: 
https://github.com/LIP-Computing/ansible-role-nvidia 

Examples of using those NVIDIA base images with a given application are the "disvis" and 
"powerfit" images whose Dockerfiles and Ansible roles can be found in:

* https://github.com/indigo-dc/ansible-role-disvis-powerfit

In order to build your docker image with a given CUDA or OpenCL application, the 
aforementioned images can be used. When the docker image with your application has 
been built you can run udocker with that image as described in the previous sections.

## 6. ACCESSING AND TRANSFERRING UDOCKER CONTAINERS

In udocker, images and containers are stored in the filesystem
usually in the user home directory under $HOME/.udocker. If this location is in
a shared filesystem such as in a computing farm or cluster then the content will 
be seen by all the hosts mounting the filesystem and can be used transparently by
udocker across these hosts. If the home directory is not shared but some other
location is, then you may point the UDOCKER_DIR environment variable to such a 
location and use it to store the udocker installation, including udockertools,
images and containers.

### 6.1. Directory structure

The directory structure of .udocker (or UDOCKER_DIR) is a as follows:

* `bin/` udocker executables
* `lib/` udocker libraries
* `repos/` images pulled or imported by udocker
* `layers` image layers so that they can be shared by several images saving space
* `containers/` containers extracted from images or imported

For a given container its directory pathname in the filesystem can be obtained
as follows:

```
$ udocker inspect -p ubuntu17
/home/user01/.udocker/containers/feb0041d-e1b6-3eee-89d8-2d0617feb13a/ROOT
```

The pathname in the example is the root of the container filesystem tree.
Below **ROOT** you will find all the files that comprise the container. Upon 
execution udocker performs a chroot like operation into this directory. 
You can modify, add, remove files below this location and upon execution 
these changes will be seen inside the container. 
This can be used to place or retrieve files to/from the container. 
By accessing this directory from the host you may also perform copies of the 
container directory tree e.g. for backup or other purposes.

All containers are stored under the directory "**containers**". Each container is
under a separate directory whose name corresponds to its alphanumeric id. 
This directory contains control files and the "**ROOT**" directory for the container 
filesystem. 

### 6.2. Transfer containers with import/export or load/save

Across isolated hosts the correct way to transfer containers is to pull them from
a repository such as Docker Hub. However this may implies slow downloads from remote
locations and also the need to create the container again from the pulled image.

udocker provides limited support for loading images and importing containers.
Containers exported to a file by Docker with `docker export` can be imported by
udocker using:

* `udocker import CONTAINER-FILE  NEWIMAGE:NEWTAG` import the 
   container file into a new image (not into a new container).
* `udocker import --tocontainer CONTAINER-FILE` import the
   container file directly into a new container (without creating an image).
   This is udocker specific.
* `udocker import --tocontainer --clone CONTAINER-FILE` import the
   container file directly into a new container (without creating an image).
   This assumes the container was initially exported by udocker with 
   `udocker export --clone` and thus contains not only the ROOT tree of
   the container but also all metadata, and control files of udocker.
   This is udocker specific.

Images saved by Docker using `docker save` can be imported by udocker using
`udocker load`. Images in OCI format can also be loaded by udocker using
`udocker load`, the format will be automatically detected.

udocker can also save images in a Docker compliant format using `udocker save`.

### 6.3. Manual transfer

The example below shows a container named MyContainer being manually transferred 
to another host and executed. Make sure the udocker executable is in your PATH on 
both the local and remote hosts.

```
$ MYC_ROOT=$(udocker inspect -p MyContainer)
$ MYC_PATH=$(dirname $MYC_ROOT)
$ MYC_ID=$(basename $MYC_PATH)
$ MYC_DIR=$(dirname $MYC_PATH)
$ cd $MYC_DIR; tar cvf - $MYC_ID | ssh user@ahost "udocker install ; cd ~/.udocker/containers; tar xf -"
$ ssh user@ahost "udocker name $MYC_ID MyContainer; udocker run MyContainer"
```

## 7. RUNNING AS ROOT INSIDE CONTAINERS

The behavior and capabilities of running as root inside the containers
depends on the execution mode. In the Pn and Rn modes udocker will run
as root. In other modes execution as root is achieved by invoking
run with the `--user=root` option:

```
udocker run --user=root <container-id>` 
```

### 7.1. Running as root in Pn modes

In the default modes Pn, running as root is emulated, meaning that no
root privileges or root capabilities are involved. The root execution is
emulated by intercepting system calls and returning id 0 thus emulating
a root environment.

### 7.2. Running as root in Fn modes

In the Fn modes running as root is not supported. 

### 7.3. Running as root in Rn modes

In the Rn (runc) modes execution defaults to run as root, this is however 
achieved in a very different manner through *user namespaces*, as implemented
in runc. These modes only work in recent Linux distributions that support
*user namespaces*. In these execution modes the user is truly root inside 
the container, but with several limitations, namely on what regards 
access to other UIDs and GUIs. Although the user can be root inside the
container, it will be a normal user outside, thus protecting the host system
if a container process breaks out.
The use of *user namespaces* may require the setup of the system configuration
files */etc/subuid* and */etc/subgid* which require system administrator
intervention to be configured. They assign a range of UIDs and GIDs for each
user to be used within the *user namespaces*. To overcome some of the root
limitations when running inside *user namespaces*, udocker offers an
overlay execution of proot inside runc through the execution modes R2 and R3.
In these modes proot is used to overcome some of the UID and GID issues
while still enabling the benefits of isolation and root execution 
inside de *user namespaces*. 

### 7.4. Running as root in Sn modes

In the Sn (singularity) execution modes default to the normal unprivileged 
user. Running as root can be achieved with `udocker run --user=root <container-id>`.
Execution within singularity requires *namespaces* and can operate in two 
different manners. In older distributions and kernels singularity must be installed
by the system administrator with privileges. In more recent distributions and
kernels singularity can operate similarly to runc and take advantage of the 
*user namespaces*. In this later case UID/GID entries might also be required in
*/etc/subuid* and */etc/subgid*.
Singularity is to package in the udokertools but, udocker can exploit existing 
singularity installations to execute the udocker containers. 

### 7.5. Summary of running as root 

The following table provides a summary of running as root within udocker:

|Mode| Engine      | Running as root
|----|:------------|:--------------------------------------------------------------
| P1 | PRoot       | Defaults to run as root. Run as root via emulation.
| P2 | PRoot       | Same as P1
| F1 | Fakechroot  | Running as root not supported.
| F2 | Fakechroot  | Running as root not supported.
| F3 | Fakechroot  | Running as root not supported.
| F4 | Fakechroot  | Running as root not supported.
| R1 | runC        | Defaults to run as root. Run as root via *user namespaces*
| R2 | runC        | Same as R1 plus overlay execution with proot in mode P1.
| R3 | runC        | Same as R1 plus overlay execution with proot in mode P2.
| S1 | Singularity | Use --user=root. Run as root via *user namespaces*

### 7.6. Running as root for software installation

Most applications and services can be run without running as root.
However running as root within udocker can be useful to install software packages.
Depending on the execution mode, running as root may imply additional
overheads and/or security considerations.

If the software installation will need to create/change users and groups then
udocker needs to run with direct access to the container passwd and group files
as follows:

```
udocker run --user=root --containerauth <CONTAINER-ID>
```

For **software installation** the recommended execution modes are **P2**, **S1**
and **R3**. The emulation is not perfect and issues can still arise.  Namelly 
when using APT it can be required to install using:

```
apt-get -o APT::Sandbox::User=root update
apt-get -o APT::Sandbox::User=root install <package>
```

Upon APT errors such as `cannot get security labeling handle: No such file or directory` 
try to run ias above in P2 mode but start udocker as:

```
udocker.py run --user=root --nosysdirs -v /etc/resolv.conf -v /dev --containerauth <CONTAINER-ID>
```

## 8. NESTED EXECUTION

udocker as not been designed for nested executions, meaning execution
of containers within containers. However there are sucessful examples of using
udocker in such scenarios such as [SCAR](https://github.com/grycap/scar).

For running inside docker and similiar: udocker offers the **Fn** mode which
enables execution within docker or other Linux namespaces based applications.

For running within udocker itself the following guidelines apply:

* Fn within Pn: Possible
* Pn within Rn: Possible only in R1
* Pn within Sn: Possible
* Fn within Rn: Possible
* Fn within Sn: Possible
* Pn within Pn: Not possible or possible with huge overheads
* Fn within Fn: Not possible
* Pn within Fn: Not possible

## 9. PERFORMANCE

The experienced performance in the different execution modes will depend
greatly on the application being executed. In general the following
considerations may hold:

 * P1 is faster than P2, unless in older kernels without *SECCOMP 
   filtering* where both modes will have the same performance.
 * In heavily multithreaded or I/O intensive applications the P2 
   mode may exhibit a large performance penalty. This can also
   apply to P1 in older kernels without **SECCOMP filtering**
 * Fn modes are generally faster than Pn modes and do not have 
   multithreading or I/O limitations.
 * Singularity and runC should provide similar performances.

## 10. ISSUES

To avoid corruption backups for safeguard or transfer should only be performed 
when the container is not being executed (not locally nor in any other host if 
the filesystem is shared).

Containers should only be copied when they are in the execution
modes Pn or Rn. The modes Fn perform changes to the containers that will make
them fail if they are execute in a different host if the absolute pathname to 
the container location is different. In this later case convert back to P1 
(using:  udocker setup --execmode=P1) before performing the backup.

When experiencing issues in the default execution mode (P1) you may try
to setup the container to execute using mode P2 or one of the Fn or 
Rn modes. See section 3.23 for information on changing execution modes.

Some execution modes require the creation of auxiliary files, directories and mountpoints. These can be purged from a given container using "setup --purge", however this operation must be performed when the container is not being executed. 

## Acknowledgements

* Docker https://www.docker.com/
* PRoot http://proot.me
* Fakechroot https://github.com/dex4er/fakechroot/wiki
* runC https://runc.io/
* Singularity http://singularity.lbl.gov
* INDIGO DataCloud https://www.indigo-datacloud.eu
* EOSC-hub https://eosc-hub.eu
* DEEP-Hybrid-DataCloud https://deep-hybrid-datacloud.eu
* Open MPI https://www.open-mpi.org
* openQCD http://luscher.web.cern.ch/luscher/openQCD

