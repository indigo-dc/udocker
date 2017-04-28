udocker
=======
A basic user tool to execute simple docker containers in user space
without requiring root privileges. Enables basic download and execution
of docker containers by non-privileged users in Linux systems were docker
is not available. It can be used to access and execute the content of
docker containers in Linux batch systems and interactive clusters that
are managed by other entities such as grid infrastructures or externaly
managed batch or interactive systems.

The Indigo udocker does not require any type of privileges nor the
deployment of services by system administrators. It can be downloaded
and executed entirely by the end user.

udocker is a wrapper around several tools to mimic a subset of the
docker capabilities including pulling images and running then with
minimal functionality.

## Development version
A development version with support for multiple execution methods
is available in the udocker-fr branch on github. The development 
version supports the following execution engines.

* PRoot (default)
* Fakechroot
* runC

See: https://github.com/indigo-dc/udocker/tree/udocker-fr

## How does it work
udocker is a simple tool written in Python, it has a minimal set
of dependencies so that can be executed in a wide range of Linux
systems.

udocker does not make use of docker nor requires its installation.

udocker "executes" the containers by simply providing a chroot like
environment over the extracted container. The current implementation
uses PRoot to mimic chroot without requiring privileges.

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

Due to the way PRoot implements the chroot environment debugging inside
of udocker will not work.

udocker is mainly oriented at providing a run-time environment for
containers execution in user space.

## Security
Because of the limitations described in the previous section udocker does not offer
isolation features such as the ones offered by docker. If the containers
content is not trusted then these containers should not be executed with udocker as
they will run inside the user environment.

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
no root privileges are involved. This feature enables some tools that do not
require privileges but which check the user id. This enables for instance 
software installation using rpm, yum or dnf inside the container.

Due to the lack of isolation udocker must not be run by privileged users.

## Installation
The installation tarball available from the INDIGO-DataCloud repositories
at https://repo.indigo-datacloud.eu please check for the latest version.

See the [Installation manual](doc/installation_manual.md)

## Syntax
```
Commands:
  search <repo/image:tag>     :Search dockerhub for container images
  pull <repo/image:tag>       :Pull container image from dockerhub
  images                      :List container images
  create <repo/image:tag>     :Create container from a pulled image
  ps                          :List created containers
  rm  <container_id>          :Delete container
  run <container_id>          :Execute container
  inspect <container_id>      :Low level information on container
  name <container_id> <name>  :Give name to container
  rmname <name>               :Delete name from container

  rmi <repo/image:tag>        :Delete image
  rm <container-id>           :Delete container
  import <container-id>       :Import tar file (exported by docker)
  load -i <exported-image>    :Load container image saved by docker
  inspect <repo/image:tag>    :Return low level information on image
  verify <repo/image:tag>     :Verify a pulled image

  protect <repo/image:tag>    :Protect repository
  unprotect <repo/image:tag>  :Unprotect repository
  protect <container_id>      :Protect container
  unprotect <container_id>    :Unprotect container

  mkrepo <topdir>             :Create repository in another location

  help                        :This help
  run --help                  :Command specific help

Options common to all commands must appear before the command:
  -D                          :Debug
  --repo=<directory>          :Use repository at directory
```

## Examples
Some examples of usage:

Search on dockerhub
```
udocker search  fedora
udocker search  ubuntu
udocker search  indigodatacloud
```

Pull from docker hub and list the pulled images.
```
udocker pull  fedora
udocker pull  busybox
udocker pull  iscampos/openqcd
udocker images
```

Pull from a registry other than dockerhub.
```
udocker pull --registry=https://registry.access.redhat.com  rhel7
udocker create --name=rh7 rhel7
udocker run rh7
```

Create the container from a pulled image and run it.
```
udocker create --name=myfed  fedora
udocker run  myfed  cat /etc/redhat-release
```

Run mounting the host /home/u457 into the container directory /home/cuser. 
Notice that you can "mount" any host directory inside the container, this 
is not a real mount but the directories will be visible inside the container.
```
udocker run -v /home/u457:/home/cuser -w /home/user myfed  /bin/bash
udocker run -v /var -v /proc -v /sys -v /tmp  myfed  /bin/bash
```

Put a script in your host /tmp and execute it in the container.
```
udocker run  -v /tmp  myfed  /bin/bash -c 'cd /tmp; ./myscript.sh'
```

Run mounting the host /var, /proc, /sys and /tmp in the same container
directories. Notice that the content of these container directories will
be obfuscated.
```
udocker run -v /var -v /proc -v /sys -v /tmp  myfed  /bin/bash
```

Install software inside the container
```
udocker run  --user=root myfed  yum install -y firefox pulseaudio gnash-plugin
```

Run as some user. The usernames should exist in the container 
```
udocker run --user 1000:1001  myfed  /bin/id
udocker run --user root   myfed  /bin/id
udocker run --user jorge  myfed  /bin/id
```

Firefox with audio and video
```
./udocker run --bindhome --hostauth --hostenv \
   -v /sys -v /proc -v /var/run -v /dev --user=jorge --dri myfed  firefox
```

## Other limitations
The accelerated mode of PRoot may exhibit failures in Linux kernels above 4.0 
with some applications due to upstream issues, in this case use run with 
--noseccomp.

```
udocker run --noseccomp mycontainer
```

## Documentation
Documentation is available at gitbook.

https://indigo-dc.gitbooks.io/udocker/content/

## Aknowlegments

* PRoot http://proot.me
* INDIGO DataCloud https://www.indigo-datacloud.eu
