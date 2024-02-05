# ___________________________________________________

[![PyPI version](https://badge.fury.io/py/udocker.svg)](https://badge.fury.io/py/udocker)
[![Build Status](https://jenkins.eosc-synergy.eu/buildStatus/icon?job=indigo-dc%2Fudocker%2Fmaster)](https://jenkins.eosc-synergy.eu/job/indigo-dc/job/udocker/job/master/)

[![SQAaaS badge](https://github.com/EOSC-synergy/SQAaaS/raw/master/badges/badges_150x116/badge_software_gold.png)](https://api.eu.badgr.io/public/assertions/70dSTwYKQpmEv7dFy6TF3w "SQAaaS gold badge achieved")

---
![logo](docs/logo-small.png)

udocker is a basic user tool to execute simple docker containers in user space without requiring
root privileges. Enables download and execution of docker containers by non-privileged users in
Linux systems where docker is not available. It can be used to pull and execute docker containers in
Linux batch systems and interactive clusters that are managed by other entities such as grid
infrastructures or externally managed batch or interactive systems.

udocker does not require any type of privileges nor the deployment of services by system
administrators. It can be downloaded and executed entirely by the end user. The limited root
functionality provided by some of the udocker execution modes is either simulated or provided via
user namespaces.

udocker is a wrapper around several tools and libraries to mimic a subset of the docker capabilities
including pulling images and running containers with minimal functionality.

## Documentation

The full documentation is available at:

* [udocker documentation](https://indigo-dc.github.io/udocker/)
* [Installation manual](https://indigo-dc.github.io/udocker/installation_manual.html)
* [User manual](https://indigo-dc.github.io/udocker/user_manual.html)
* [CLI architecture](https://indigo-dc.github.io/udocker/cli_arch.html)
* [Reference card](https://indigo-dc.github.io/udocker/reference_card.html)

## How does it work

udocker is written in Python, it has a minimal set of dependencies so that can be executed in a wide
range of Linux systems. udocker does not make use of docker nor requires its presence.

udocker "executes" the containers by simply providing a chroot like environment over the extracted
container. The current implementation supports different methods to mimic chroot thus enabling
execution of containers under a chroot like environment without requiring privileges. udocker
transparently supports several methods to execute the containers based on external tools and
libraries such as:

* PRoot
* Fakechroot
* runc
* crun
* Singularity

With the exception of Singularity the tools and libraries to support execution are downloaded and
deployed by udocker during the installation process. This installation is performed in the user home
directory and does not require privileges. The udocker related files such as libraries, executables,
documentation, licenses, container images and extracted directory trees are placed by default under
`$HOME/.udocker`.

## Advantages

* Can be deployed by the end-user
* Does not require privileges for installation
* Does not require privileges for execution
* Does not require compilation, just transfer the Python code
* Encapsulates several tools and execution methods
* Includes the required tools already statically compiled to work across systems
* Provides a docker like command line interface
* Supports a subset of docker commands:
   * search, pull, import, export, load, save, login, logout, create and run
* Understands docker container metadata
* Allows loading of docker and OCI containers
* Supports NVIDIA GPGPU applications
* Can execute in systems and environments where Linux namespaces support is unavailable
* Runs both on new and older Linux distributions including: CentOS 7, CentOS 8, Ubuntu 18.04,
  Ubuntu 20.04, Ubuntu 22.04, Alpine, Fedora, etc

## Support Python 3

Since v1.5.0 (or the development v1.4.x), udocker supports Python >= 3.6. The original udocker
v1.1.x for Python 2 is no longer maintained but is still available
[here](https://github.com/indigo-dc/udocker/tree/v1.1.8).

## Syntax

```txt
        Commands:
          search <repo/expression>      :Search dockerhub for container images
          pull <repo/image:tag>         :Pull container image from dockerhub
          create <repo/image:tag>       :Create container from a pulled image
          run <container>               :Execute container
          run <repo/image:tag>          :Pull, create and execute container

          images -l                     :List container images
          ps -m -s                      :List created containers
          name <container_id> <name>    :Give name to container
          rmname <name>                 :Delete name from container
          rename <name> <new_name>      :Change container name
          clone <container_id>          :Duplicate container
          rm <container-id>             :Delete container
          rmi <repo/image:tag>          :Delete image
          tag <repo/image:tag> <repo2/image2:tag2> :Tag image

          import <tar> <repo/image:tag> :Import tar file (exported by docker)
          import - <repo/image:tag>     :Import from stdin (exported by docker)
          export -o <tar> <container>   :Export container directory tree
          export - <container>          :Export container directory tree
          load -i <imagefile>           :Load image from file (saved by docker)
          load                          :Load image from stdin (saved by docker)
          save -o <imagefile> <repo/image:tag>  :Save image with layers to file

          inspect <repo/image:tag>      :Return low level information on image
          inspect -p <container>        :Return path to container location
          verify <repo/image:tag>       :Verify a pulled or loaded image
          manifest inspect <repo/image:tag> :Print manifest metadata

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

Search container images in dockerhub and listing tags.

```bash
udocker search  fedora
udocker search  ubuntu
udocker search  debian

udocker search --list-tags ubuntu
```

Pull from dockerhub and list the pulled images.

```bash
udocker pull   fedora:39
udocker pull   busybox
udocker pull   iscampos/openqcd
udocker images
```

Pull from a registry other than dockerhub.

```bash
udocker search  quay.io/bio
udocker search  --list-tags  quay.io/biocontainers/scikit-bio
udocker pull    quay.io/biocontainers/scikit-bio:0.2.3--np112py35_0
udocker images
```

Pull a different architecture such as arm64 instead of amd64.

```bash
udocker manifest inspect centos/centos8
udocker pull --platform=linux/arm64 centos/centos8
udocker tag centos/centos8  mycentos/centos8:arm64
```

Create a container from a pulled image, assign a name to the created container and run it. A created
container can be run multiple times until it is explicitly removed. Files modified or added to the container
remain available across executions until the container is removed.

```bash
udocker create --name=myfed  fedora:29
udocker run  myfed  cat /etc/redhat-release
```

The three steps of pulling, creating and running can be also achieved in a single command, however
this will be much slower for multiple invocations of the same container, as a new container will be
created for each invocation. This approach will also consume more storage space. The following
example creates a new container for each invocation.

```bash
udocker run  fedora:29  cat /etc/redhat-release
```

Execute mounting the host /home/u457 into the container directory /home/cuser. Notice that you can
"mount" any host directory inside the container. Depending on the execution mode the "mount" is
implemented differently and may have restrictions.

```bash
udocker run -v /home/u457:/home/cuser -w /home/user myfed  /bin/bash
udocker run -v /var -v /proc -v /sys -v /tmp  myfed  /bin/bash
```

Place a script in your host /tmp and execute it in the container. Notice that the behavior of
`--entrypoint` changed from the previous versions for better compatibility with docker.

```bash
udocker run  -v /tmp  --entrypoint="" myfed  /bin/bash -c 'cd /tmp; ./myscript.sh'

udocker run  -v /tmp  --entrypoint=/bin/bash  myfed  -c 'cd /tmp; ./myscript.sh'
```

Execute mounting the host /var, /proc, /sys and /tmp in the same container directories. Notice that
the content of these container directories will be obfuscated by the host files.

```bash
udocker run -v /var -v /proc -v /sys -v /tmp  myfed  /bin/bash
```

Install software inside the container.

```bash
udocker run  --user=root myfed  yum install -y firefox pulseaudio gnash-plugin
```

Run as some user. The usernames should exist in the container.

```bash
udocker run --user 1000:1001  myfed  /bin/id
udocker run --user root   myfed  /bin/id
udocker run --user jorge  myfed  /bin/id
```

Running Firefox.

```bash
udocker run --bindhome --hostauth --hostenv \
   -v /sys -v /proc -v /var/run -v /dev --user=jorge --dri myfed  firefox
```

Change execution engine mode from PRoot to Fakechroot and run.

```bash
udocker setup  --execmode=F3  myfed

udocker run --bindhome --hostauth --hostenv \
   -v /sys -v /proc -v /var/run -v /dev --user=jorge --dri myfed  firefox
```

Change execution engine mode to accelerated PRoot.

```bash
udocker setup  --execmode=P1  myfed
```

Change execution engine to runc.

```bash
udocker setup  --execmode=R1  myfed
```

Change execution engine to Singularity. Requires the availability of Singularity in the host system.

```bash
./udocker setup  --execmode=S1  myfed
```

Install software running as root emulation in Singularity:

```bash
udocker setup  --execmode=S1  myfed
udocker run  --user=root myfed  yum install -y firefox pulseaudio gnash-plugin
```

Change execution to enable nvidia ready applications. Requires that
the nvidia drivers are installed in the host system.

```bash
udocker setup  --nvidia  mytensorflow
```


## Security

By default udocker via PRoot offers the emulation of the root user. This emulation mimics a real
root user (e.g getuid will return 0). This is just an emulation no root privileges are involved.
This feature makes possible the execution of some tools that do not require actual privileges but
which refuse to work if the username or id are not root or 0. This enables for instance software
installation using rpm, yum or dnf inside the container.

udocker does not offer robust isolation features such as the ones offered by docker. Therefore if
the containers content is not trusted then these containers should not be executed with udocker as
they will run inside the user environment. For this reason udocker should not be run by privileged
users.

Container images and filesystems will be unpacked and stored in the user home directory under
`$HOME/.udocker` or other location of choice. Therefore the containers data will be subjected to the
same filesystem protections as other files owned by the user. If the containers have sensitive
information the files and directories should be adequately protected by the user.

udocker does not require privileges and runs under the identity of the user invoking it. Users can
downloaded udocker and execute it without requiring system administrators intervention.

udocker also provides execution with runc, crun and Singularity, these modes make use of rootless
namespaces and enable a normal user to execute as root with the limitations that apply to user
namespaces and to these tools.

When executed by normal unprivileged users, udocker limits privilege escalation issues since it does
not use or require system privileges.

## General Limitations

Since root privileges are not involved any operation that really requires such privileges will not
be possible. The following are examples of operations that are not possible:

* accessing host protected devices and files
* listening on TCP/IP privileged ports (range below 1024)
* mount file-systems
* the su command will not work
* change the system time
* changing routing tables, firewall rules, or network interfaces

If the containers require such privilege capabilities then docker should be used instead.

udocker is not meant to create containers. Creation of containers is better performed using docker
and dockerfiles.

udocker does not provide all the docker features, and is not intended as a docker replacement.

udocker is mainly oriented at providing a run-time environment for containers execution in user
space. udocker is particularly suited to run user applications encapsulated in docker containers.

Debugging or using strace with the PRoot engine will not work as both the debuggers and PRoot use the
same tracing mechanism.  

## Execution mode specific limitations

udocker offers multiple execution modes leveraging several external tools such as PRoot (P mode),
Fakechroot (F mode), runC (R mode), crun (R mode) and Singularity (S mode).

When using execution Fakechroot modes such as F2, F3 and F4 the created containers cannot be moved
across hosts. In this case convert back to a Pn mode before transfer. This is not needed if the
hosts are part of an homogeneous cluster where the mount points and directory structure is the same.
This limitation applies whenever the absolute real path to the container directory changes.

The default accelerated mode of PRoot (mode P1) may exhibit problems in Linux kernels above 4.0 due
to kernel changes and upstream issues, in this case use mode P2 or any of the other execution modes.

```bash
./udocker setup  --execmode=P2  my-container-id
```

The Fakechroot modes (Fn modes) require shared libraries compiled against the libc shipped with the
container. udocker provides these libraries for several Linux distributions, these shared libraries
are installed by udocker under:

```bash
$HOME/.udocker/lib/libfakechroot-*
```

The runc and crun modes (R modes) require a kernel with user namespaces enabled. The singularity
mode (S mode) requires the availability of Singularity in the host system. Singularity is not
shipped with udocker.

## Metadata generation

The `codemeta.json` metadata file was initially generated with `codemetapy`
package:

```bash
codemetapy udocker --with-orcid --affiliation "LIP Lisbon" \
  --buildInstructions "https://https://github.com/indigo-dc/udocker/blob/master/docs/installation_manual.md#3-source-code-and-build" \
  --citation "https://doi.org/10.1016/j.cpc.2018.05.021" \
  --codeRepository "https://github.com/indigo-dc/udocker" \
  --contIntegration "https://jenkins.eosc-synergy.eu/job/indigo-dc/job/udocker/job/master/" --contributor "Mario David" \
  --copyrightHolder "LIP"  --copyrightYear "2016" --creator "Jorge Gomes" \
  --dateCreated "2021-05-26" --maintainer "Jorge Gomes" \
  --readme "https://github.com/indigo-dc/udocker/blob/master/README.md" \
  --referencePublication "https://doi.org/10.1016/j.cpc.2018.05.021" \
  --releaseNotes "https://github.com/indigo-dc/udocker/blob/master/changelog" \
  -O codemeta.json
```

Further updates may be needed to add the correct values in the metadata file.

## Contributing

See: [Contributing](CONTRIBUTING.md)

## Citing

See: [Citing](CITING.md)

When citing udocker please use the following:

* Jorge Gomes, Emanuele Bagnaschi, Isabel Campos, Mario David,
  Luís Alves, João Martins, João Pina, Alvaro López-García, Pablo Orviz,
  Enabling rootless Linux Containers in multi-user environments: The udocker
  tool, Computer Physics Communications, Available online 6 June 2018,
  ISSN 0010-4655, <https://doi.org/10.1016/j.cpc.2018.05.021>

## Licensing

Redistribution, commercial use and code changes must regard all licenses shipped with udocker. These
include the [udocker license](LICENSE) and the individual licenses of the external tools and
libraries packaged for use with udocker. For further information see the
[software licenses section](https://indigo-dc.github.io/udocker/installation_manual.html#62-software-licenses)
of the installation manual.

## Acknowledgements

* Docker <https://www.docker.com/>
* PRoot <https://proot-me.github.io/>
* Fakechroot <https://github.com/dex4er/fakechroot/wiki>
* Patchelf <https://github.com/NixOS/patchelf>
* runC <https://runc.io/>
* crun <https://github.com/containers/crun>
* Singularity <https://www.sylabs.io/>
* Open Container Initiative <https://www.opencontainers.org/>
* INDIGO DataCloud <https://www.indigo-datacloud.eu>
* DEEP-Hybrid-DataCloud <https://deep-hybrid-datacloud.eu>
* EOSC-hub <https://eosc-hub.eu>
* EGI-ACE <https://www.egi.eu/projects/egi-ace/>
* EOSC-Synergy <https://www.eosc-synergy.eu/>
* DT-Geo <https://dtgeo.eu/>
* LIP [https://www.lip.pt](https://www.lip.pt/?section=home&page=homepage&lang=en)
* INCD [https://www.incd.pt](https://www.incd.pt/?lang=en)

This work was performed in the framework of the H2020 project INDIGO-Datacloud
(RIA 653549) and further developed with co-funding by the projects EOSC-hub
(Horizon 2020) under Grant number 777536, DEEP-Hybrid-DataCloud
(Horizon 2020) under Grant number 777435, DT-Geo (Horizon Europe) under Grant
number 101058129. Software Quality Assurance is performed with the support of
by the project EOSC-Synergy (Horizon 2020).
The authors wish to acknowleadge the support of INCD-Infraestrutura Nacional de
Computação Distribuída (funded by FCT, P2020, Lisboa2020, COMPETE and FEDER
under the project number 22153-01/SAICT/2016).
