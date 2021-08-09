
---
title: 'udocker: a user oriented tool for unprivileged Linux containers'
tags:
  - Python
  - Linux containers
  - Distributed computing
  - Advanced computing
authors:
  - name: Jorge Gomes^[corresponding author]
    orcid: 0000-0002-9142-2596
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Mario David
    orcid: 0000-0003-1802-5356
    affiliation: "1, 2"
  - name: João Martins
    orcid: 0000-0003-4308-266X
    affiliation: "1, 2"
  - name: João Pina
    orcid: 0000-0001-8959-5044
    affiliation: "1, 2" 
  - name: Samuel Bernardo
    orcid: 0000-0002-6175-4012
    affiliation: "1, 2"
  - name: Isabel Campos
    orcid: 0000-0002-9350-0383
    affiliation: 3
  - name: Pablo Orviz
    orcid: 0000-0002-2473-6405
    affiliation: 3
  - name: Alvaro López-García
    orcid: 0000-0002-0013-4602
    affiliation: 3
    
affiliations:
 - name: LIP, Laboratório de Instrumentação e Física Experimental de Partículas, Lisboa, Portugal
   index: 1
 - name: INCD, Infraestrutura Nacional de Computação Distribuída, Lisboa, Portugal
   index: 2
 - name: IFCA, Consejo Superior de Investigaciones Científicas-CSIC, Santander, Spain
   index: 3
date: 12 May 2021
bibliography: paper.bib
---

# Summary

Containers are increasingly used to package, distribute and run scientific software. 
udocker is a tool to enable execution of Linux containers in advanced computing
environments. Distinctively from other tools, udocker is meant for easy deployment
and provides multiple execution engines to cope with different host environments. 
udocker can execute containers with or without using Linux namespaces. udocker is 
being used by a wide range of projects and research communities to facilitate the 
execution of Linux containers across heterogeneous computing environments.

# Statement of need

Researchers have at their disposal a wide range of computing resources ranging
from laptops to high performance computing clusters and cloud services. Enabling 
execution of scientific codes across such resources often requires significant 
effort to adapt to the underlying system configurations. This can be particularly
difficult for codes with complex software dependencies and can become a continuous 
effort due to system changes and software updates. Furthermore ensuring the 
reproducibility across heterogeneous computing resources can be challenging when 
the software needs to be adapted to the specificity of each resource. In this 
context Linux containers have gained interest as means to enable encapsulation of 
research software for easier execution across these environments.

udocker is designed to address the requirement of executing scientific 
applications easily across a wide range of computing systems and digital 
infrastructures where the user may not have administration privileges, and
where tools and functionalities to support Linux containers may not be
available. 
In addition, udocker also simplifies the researcher interaction with the tools 
required to execute containers by providing an integrated solution to execute 
Linux containers leveraging different approaches suitable for unprivileged
users. Finally by executing containers without privileges udocker decreases the 
risks of privilege escalation. The udocker development started in 2016 and 
the original udocker paper [@GOMES2018] documented the initial versions up
to 1.1.1.

# Concept

udocker provides a self contained solution with minimal dependencies to enable
execution across systems without need of source code compilation. udocker itself 
was initially implemented in Python 2 and later ported to Python 3.

udocker implements pulling, importing and loading of *docker* or OCI containers to 
a local repository in the user home directory. The layers composing a container 
image can then be sequentially extracted to create a flattened directory tree.
Furthermore udocker also provides the logic to interface with the several 
execution engines that enable the execution of code extracted from the container 
images, thus hiding as much as possible the execution engines specificity.
The execution engines are based on existing open source software that in several
cases has been significantly improved, integrated and packaged to be used with 
udocker. The following engines are currently provided:

* **F** engine: uses the Linux shared library PRELOAD mechanism to intercept
  shared library calls and translate pathnames to provide an unprivileged chroot 
  like functionality. It is implemented by an extensively enhanced *Fakechroot*
  shared library with versions for the *glibc* [@FAKECHROOT-GLIBC-UDOCKER] 
  and *musl* [@FAKECHROOT-MUSL-UDOCKER] *C* standard libraries. 
  This approach requires the modification of pathnames in the ELF headers of 
  shared libraries and executables. These changes are performed by udocker using 
  a modified *Patchelf* [@PATCHELF-UDOCKER]. This is the 
  execution engine that generally provides the highest performance. 
* **P** engine: uses the Linux PTRACE mechanism to implement a chroot like 
  environment by intercepting system calls and translating pathnames. It is 
  implemented by a modified *PRoot* [@PROOT-UDOCKER]. This 
  engine provides the highest interoperability across Linux distributions both 
  older and newer, and constitutes the default execution engine for udocker. 
* **R** engine: uses either *runc* [@RUNC] or *crun* [@CRUN] to execute the 
  containers without privileges using Linux user namespaces. Both tools are 
  provided with udocker for wider interoperability.
* **S** engine: uses *Singularity* [@KURTZER2017] to execute the containers using 
  user namespaces or other *Singularity* supported execution method depending
  on the system configuration. 
  
All required commands are statically compiled for execution across a
wide range of systems. The shared libraries for the **F** modes are also 
compiled and provided for major Linux distributions. The **F** modes 
require the compilation of the libraries against each *libc* and therefore
requires creation of different libraries for each release of a given 
distribution.

Support for the ARM architecture is 
provided for the **P** mode and is ongoing for the other modes. The binaries 
for the **S** engine are not provided with udocker, as this mode is provided 
to take advantage of local installations of *Singularity* where available.

Once the udocker Python code is transferred to the target host it can be 
used by an unprivileged user to download the additional executables and 
binaries into the user home directory. The user can then use udocker to 
pull images, create container directories from the images and execute them. 
Each extracted container can be easily setup for execution using any of the 
execution engines. udocker provides a command line interface with a syntax 
similar to docker.

Compared with other container tools that can enable unprivileged 
execution such as *podman*, *docker*, or *Singularity* among others, udocker 
is unique in offering multiple execution engines for unprivileged execution,
two of these engines are based on pathname translation not requiring kernel 
features such as Linux user namespaces thus enabling execution across a 
wider range of systems and services where user namespaces are unavailable. 
The Linux user namespaces approach also has limitations and may create 
problems when accessing host files via bind mount due to the usage of 
subordinate uid and gid identifiers. These limitations 
extend to system calls that may return uid and gid or when credentials 
are passed across sockets. In addition user namespaces still expose 
code in the kernel to normal users that was previously only really 
accessible to root creating opportunities for new vulnerabilities to
arise. If isolation between the container and the running host is 
important then namespaces provide the highest level of isolation at the 
expense of the described risks and limitations. For the users that wish 
to rely on Linux namespaces udocker also offers support for this approach 
through *runc* and *crun* or through *Singularity* if locally installed. 
The tools that can execute containers using `chroot` or `pivot_root` and 
use privileges such as *Shifter*, *Sarus* [@BENEDICIC2019] or the original 
mode of *Singularity* have the limitation of requiring installation and 
configuration by a system administrator and of having a higher risk of 
privilege escalation as privileges are used in some operations. 
Since these tools run with privileges they can use approaches such as 
using *squashfs* to improve file access. On de other hand udocker is 
focused on deployment and execution entirely by the end-user and thus 
cannot provide features that require privileges. 


# Developments since 1.1.1

Since 1.1.1, udocker moved from a proof of concept tool suitable for production. 
The focus has been put on sustainability and interoperability. The code structure 
was redesigned moving from the Python 2 monolithic code to a new Python 3 modular 
implementation. New features and improvements were added to support a wider range 
of Linux distributions and environments. To this end the execution engines now 
support *crun* for namespace based execution with cgroups v2 and a port of *Fakechroot*
to support *MUSL* libc. The existing execution engines were also enhanced to address 
the shortcomings present in the proof of concept and improve interoperability for 
execution across a wider range of distributions, kernels and better supporting the 
functionalities required for containers execution. Support for multiple architectures 
was added and binaries for ARM and x86 are now provided for *PRoot* based execution, 
further binaries can be easily added as needed. Support for accelerated computing 
was implemented by introducing the capability to setup containers to use NVIDIA GPUs 
according to the host environment and across the several execution engines. The 
handling of container images was improved both at the level of interaction with 
container registries and handling of formats. The interaction with registries is 
now more interoperable and robust and support for the OCI image specification v1 
was introduced. Furthermore the search capabilities support docker registry v1 and 
v2 specifications and listing of tags. The command line interface and configuration 
was improved with new commands, flags and better parsing of both the command line 
and config files. Finally the installation of the tools and libraries was decoupled 
from udocker itself, both can now be released separately. The shared installation 
of udocker in distributed filesystems was addressed with changes introduced to 
handle the cases where udocker is executed from readonly filesystems. Finally, udocker 
is now also available from PyPI.

# Research with udocker

Examples of usage can be found in several domains including:
physics [@BAGNASCHI2018] [@BAGNASCHI2019] [@BEZYAZEEKOV2019] [@BEZYAZEEKOV2021],
life sciences [@KORHONEN2019] [@ZIEMANN2019] [@MERELLI2019] [@KERN2020] [@CHILLARON2017] [@KORHONEN2019], 
coastal modeling [@OLIVEIRA2019] [@OLIVEIRA2020], 
chemistry [@NALINI2020] [@DBLP2020],
structural biology [@TRAYNOR2020], 
fusion [@LAHIFF2020],
earth sciences [@KERZENMACHER2021] [@AGUILAR2017],
machine learning [@GRUPP2019] [@DEEP2020] [@CAVALLARO2019],
and computer science in general [@CABALLER2021] [@RISCO2021] [@SUFI2020] [@ALDINUCCI2017] [@OWSIAK2017].


udocker was used in the European projects EOSC-hub [@EOSCHUB] where it 
was further improved and DEEP-hybrid-DataCloud [@DEEP2020] where it was ported 
to Python 3, enhanced to support nvidia GPUs and used to execute deep 
learning frameworks. Since 2021 is used in the EOSC-Synergy [@KERZENMACHER2021], 
EGI-ACE [@EGIACE] and BIG-HPC [@PAULO2020] projects. Although is a tool meant for
end-users, it is also supported by several scientific and academic computer 
centers and research infrastructures worldwide such as:

 * EGI advanced computing infrastructure in Europe [@EGI]
 * IBERGRID Iberian distributed computing infrastructure [@IBERGRID]
 * INCD Portuguese Distributed Computing Infrastructure [@INCD]
 * CESGA Super computing Center of Galicia [@CESGA]
 * HPC center of the Telaviv University  [@TELAVIV]
 * Trinity College HPC center in Dublin [@TCD]
 * University of Utah HPC center [@UTAH] 
 * University of Coruña Pluton Cluster [@CORUNA]

udocker was been integrated in several research oriented frameworks such as: 

 * SCAR - Serverless Container-aware Architectures [@PEREZ2018] to enable execution of containers in Amazon Lambda exploiting function as a service (FaaS);
 * common-workflow-language [@CWL2016], [@KORHONEN2019] to enable containers in scientific workflows;
 * bioconda [@GRUNING2018] for the conda package manager specialized in bioinformatics software;
 * openmole  workflow engine [@REUILLON2013] for exploration of simulation models using high throughput computing;
 * and is also referenced in the SLUM Containers Guide [@SLURM].

# Acknowledgments

udocker has been developed in the framework of the H2020 projects INDIGO-DataCloud (RIA 653549), EOSC-hub (RIA 777536) and DEEP-Hybrid-DataCloud (RIA 777435). The proofs of concept have been performed at INCD-Infraestrutura Nacional de Computação Distribuída (funded by FCT, P2020, Lisboa2020, COMPETE and FEDER under the project number 22153-01/SAICT/2016), FinisTerrae II machine provided by CESGA (funded by Xunta de Galicia and MINECO) and Altamira machine (funded by the University of Cantabria and MINECO).

# References



