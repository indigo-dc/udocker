
<!---
[![Build Status](https://jenkins.indigo-datacloud.eu/buildStatus/icon?job=Pipeline-as-code/udocker/master)](https://jenkins.indigo-datacloud.eu/job/Pipeline-as-code/job/udocker/job/master/)
-->
[![Build Status](https://jenkins.indigo-datacloud.eu/buildStatus/icon?job=Pipeline-as-code/udocker/master)](https://jenkins.indigo-datacloud.eu/job/Pipeline-as-code/job/udocker/job/master/)

[![logo](https://raw.githubusercontent.com/indigo-dc/udocker/master/doc/logo-small.png)]()

udocker is a basic user tool to execute simple docker containers in user
space without requiring root privileges. Enables download and execution
of docker containers by non-privileged users in Linux systems where
docker is not available. It can be used to pull and execute docker
containers in Linux batch systems and interactive clusters that are
managed by other entities such as grid infrastructures or externally
managed batch or interactive systems.

udocker does not require any type of privileges nor the deployment of
services by system administrators. It can be downloaded and executed
entirely by the end user.

udocker is a wrapper around several tools to mimic a subset of the
docker capabilities including pulling images and running containers
with minimal functionality.

## How does it work
udocker is a simple tool written in Python, it has a minimal set
of dependencies so that can be executed in a wide range of Linux
systems.

udocker does not make use of docker nor requires its presence.

udocker "executes" the containers by simply providing a chroot like
environment over the extracted container. The current implementation
supports different methods to mimic chroot thus enabling execution of
containers under a chroot like environment without requiring privileges.
udocker transparently supports several methods to execute the containers
using tools and libraries such as:

* PRoot
* Fakechroot
* runC
* Singularity

## Advantages
* Provides a docker like command line interface
* Supports a subset of docker commands:
  search, pull, import, export, load, save, create and run
* Understands docker container metadata
* Allows loading of docker and OCI containers
* Can be deployed by the end-user
* Does not require privileges for installation
* Does not require privileges for execution
* Does not require compilation, just transfer the Python script and run
* Encapsulates several tools and execution methods
* Includes the required tools already statically compiled to work across systems
* Tested with GPGPU and MPI applications
* Runs both on new and older Linux distributions including:
  CentOS 6, CentOS 7, CentOS 8, Ubuntu 14, Ubuntu 16, Ubuntu 18, Fedora, etc

## Installation and Users manuals
See the **[Installation manual](doc/installation_manual.md)**
and the **[Users manual](doc/user_manual.md)**.

## Syntax
```
        Commands:
          search <repo/expression>      :Search dockerhub for container images
          pull <repo/image:tag>         :Pull container image from dockerhub
          create <repo/image:tag>       :Create container from a pulled image
          run <container>               :Execute container

          images -l                     :List container images
          ps -m -s                      :List created containers
          name <container_id> <name>    :Give name to container
          rmname <name>                 :Delete name from container
          rename <name> <new_name>      :Change container name 
          clone <container_id>          :Duplicate container
          rm <container-id>             :Delete container
          rmi <repo/image:tag>          :Delete image

          import <tar> <repo/image:tag> :Import tar file (exported by docker)
          import - <repo/image:tag>     :Import from stdin (exported by docker)
          export -o <tar> <container>   :Export container directory tree
          export - <container>          :Export container directory tree
          load -i <imagefile>           :Load image from file (saved by docker)
          load                          :Load image from stdin (saved by docker)
          save -o <imagefile> <repo/image:tag>  :Save image with layers to file

          inspect -p <repo/image:tag>   :Return low level information on image
          verify <repo/image:tag>       :Verify a pulled or loaded image

          protect <repo/image:tag>      :Protect repository
          unprotect <repo/image:tag>    :Unprotect repository
          protect <container>           :Protect container
          unprotect <container>         :Unprotect container

          mkrepo <top-repo-dir>         :Create another repository in location
          setup                         :Change container execution settings
          login                         :Login into docker repository
          logout                        :Logout from docker repository

          help                          :This help
          run --help                    :Command specific help
          version                       :Shows udocker version

        Options common to all commands must appear before the command:
          -D                            :Debug
          --quiet                       :Less verbosity
          --repo=<directory>            :Use repository at directory
          --insecure                    :Allow insecure non authenticated https
          --allow-root                  :Allow execution by root NOT recommended
```

## Examples
Some examples of usage:

Search container images in dockerhub.
```
udocker search  fedora
udocker search  ubuntu
udocker search  indigodatacloud
```

Pull from dockerhub and list the pulled images.
```
udocker pull   fedora:29
udocker pull   busybox
udocker pull   iscampos/openqcd
udocker images
```

Pull from a registry other than dockerhub.
```
udocker search  quay.io/bio
udocker search  --list-tags  quay.io/biocontainers/scikit-bio
udocker pull    quay.io/biocontainers/scikit-bio:0.2.3--np112py35_0
udocker images
```

Create a container from a pulled image and run it.
```
udocker create --name=myfed  fedora:29
udocker run  myfed  cat /etc/redhat-release
```

The three steps of pulling, creating and running can be achieved in
a single command, however this will create a new container in each
invocation consuming additional space and time. Therefore is better
to pull and create separately and use the identifier returned by
create or use an alias to execute the container as demonstrated above.

```
udocker run  fedora:29  cat /etc/redhat-release
```

Execute mounting the host /home/u457 into the container directory /home/cuser.
Notice that you can "mount" any host directory inside the container.
Depending on the execution mode the "mount" is implemented differently and
may have restrictions.
```
udocker run -v /home/u457:/home/cuser -w /home/user myfed  /bin/bash
udocker run -v /var -v /proc -v /sys -v /tmp  myfed  /bin/bash
```

Put a script in your host /tmp and execute it in the container.
```
udocker run  -v /tmp  myfed  /bin/bash -c 'cd /tmp; ./myscript.sh'
```

Execute mounting the host /var, /proc, /sys and /tmp in the same container
directories. Notice that the content of these container directories will
be obfuscated.
```
udocker run -v /var -v /proc -v /sys -v /tmp  myfed  /bin/bash
```

Install software inside the container.
```
udocker run  --user=root myfed  yum install -y firefox pulseaudio gnash-plugin
```

Run as some user. The usernames should exist in the container.
```
udocker run --user 1000:1001  myfed  /bin/id
udocker run --user root   myfed  /bin/id
udocker run --user jorge  myfed  /bin/id
```

Running Firefox.
```
udocker run --bindhome --hostauth --hostenv \
   -v /sys -v /proc -v /var/run -v /dev --user=jorge --dri myfed  firefox
```

Change execution engine mode from PRoot to Fakechroot and run.
```
udocker setup  --execmode=F3  myfed

udocker run --bindhome --hostauth --hostenv \
   -v /sys -v /proc -v /var/run -v /dev --user=jorge --dri myfed  firefox
```

Change execution engine mode to accelerated PRoot.
```
udocker setup  --execmode=P1  myfed
```

Change execution engine to runC.
```
udocker setup  --execmode=R1  myfed
```

Change execution engine to Singularity. Requires the availability of
Singularity in the host system.
```
./udocker setup  --execmode=S1  myfed
```

Install software running as root emulation in Singularity:
```
udocker setup  --execmode=S1  myfed
udocker run  --user=root myfed  yum install -y firefox pulseaudio gnash-plugin
```


## Limitations
Since root privileges are not involved any operation that really
requires such privileges will not be possible. The following  are
examples of operations that are not possible:

* accessing host protected devices and files
* listening on TCP/IP privileged ports (range below 1024)
* mount file-systems
* the su command will not work
* change the system time
* changing routing tables, firewall rules, or network interfaces

If the containers require such capabilities then docker should be used
instead.

The current implementation is limited to the pulling of docker images
and its execution. The actual containers should be built using docker
and dockerfiles.

udocker does not provide all the docker features, and is not intended
as a docker replacement.

Debugging inside of udocker with the PRoot engine will not work due to
the way PRoot implements the chroot environment

udocker is mainly oriented at providing a run-time environment for
containers execution in user space. udocker is particularly suited to 
run user applications encapsulated in docker containers.

## Security
Because of the limitations described in the previous section udocker does
not offer robust isolation features such as the ones offered by docker. 
If the containers content is not trusted then these containers should not 
be executed with udocker as they will run inside the user environment.

The containers data will be unpacked and stored in the user home directory or
other location of choice. Therefore the containers data will be subjected to
the same filesystem protections as other files owned by the user. If the
containers have sensitive information the files and directories should be
adequately protected by the user.

udocker does not require privileges and runs under the identity of the user
invoking it.

Users can downloaded udocker and execute it without requiring system
administrators intervention.

udocker via PRoot offers the emulation of the root user. This emulation
mimics a real root user (e.g getuid will return 0). This is just an emulation
no root privileges are involved. This feature makes possible the execution
of some tools that do not require actual privileges but which refuse to
work if the username or id are not root or 0. This enables for instance
software installation using rpm, yum or dnf inside the container.

udocker must not be run by privileged users.

udocker also provides execution with runc and Singularity, these modes make
use of rootless namespaces and enable a normal user to execute as root with
certain limitations.

## Other limitations
When using execution modes such as F2, F3 and F4 the created
containers cannot be moved across hosts. In this case convert back to a Pn
mode before transfer.
This is not needed if the hosts are part of an homogeneous cluster where
the mount points and directory structure is the same. This limitation
applies to the absolute realpath to the container directory.


The default accelerated mode of PRoot (mode P1) may exhibit failures in Linux 
kernels above 4.0 due to kernel changes and upstream issues, in this case use
mode P2 or any of the other execution modes.

```
./udocker setup  --execmode=P2  my-container-id
```

The Fn modes require shared libraries compiled against the libc within
the containers. udocker provides these libraries for several distributions
and versions, they are installed under:

```
$HOME/.udocker/lib/libfakechroot-*
```
 
The runC mode requires a recent kernel with user namespaces enabled.

The singularity mode requires the availability of Singularity in the host
system.

## Documentation
The full documentation is available at:

* master: https://github.com/indigo-dc/udocker/blob/master/SUMMARY.md
* devel: https://github.com/indigo-dc/udocker/blob/devel/SUMMARY.md

## Contributing

See: [Contributing](CONTRIBUTING.md)

## Citing
When citing udocker please use the following:

* Jorge Gomes, Emanuele Bagnaschi, Isabel Campos, Mario David, Luís Alves, João Martins, João Pina, Alvaro López-García, Pablo Orviz, Enabling rootless Linux Containers in multi-user environments: The udocker tool, Computer Physics Communications, Available online 6 June 2018, ISSN 0010-4655, https://doi.org/10.1016/j.cpc.2018.05.021

## Acknowledgements

* Docker https://www.docker.com/
* PRoot https://proot-me.github.io/
* Fakechroot https://github.com/dex4er/fakechroot/wiki
* runC https://runc.io/
* Singularity https://www.sylabs.io/
* Open Container Initiative https://www.opencontainers.org/
* INDIGO DataCloud https://www.indigo-datacloud.eu
* EOSC-hub https://eosc-hub.eu
* DEEP-Hybrid-DataCloud https://deep-hybrid-datacloud.eu
* LIP https://www.lip.pt
* INCD https://www.incd.pt
