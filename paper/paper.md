
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
difficult for codes with complex software dependencies and can become a continous 
effort due to system changes and software updates. Furthermore ensuring the 
reproducibility across heterogeneous computing resources can be challenging when 
the software needs to be adapted to the specificities of each resource. In this 
context Linux containers have gained interest as means to enable encapsulation of 
research software for easier execution across these environments.

udocker is designed to address the requirement of executing scientific 
applications easily across a wide range of computing systems and digital 
infrastructures where the user may not have administration privileges, and
where run times and functionalities to support Linux containers may not be
available. 
In addition, udocker also simplifies the researcher interaction with the tools 
required to execute containers by providing an integrated solution to execute 
Linux containers leveraging different approaches suitable for unprivileged
users. Finally by executing containers without privileges udocker decreases the 
risks of privilege escalation. The udocker development started in 2016 and 
the original udocker paper [@GOMES2018] documented versions 1.1.0 and 1.1.1.
Since then several new features have been released.

# Concept
udocker provides a self contained solution with minimal dependencies to enable
execution across systems without need of compilation. udocker itself was 
initialy implemented in Python 2 and later ported to Python 3.

udocker implements pulling, importing and loading of docker or OCI containers to 
a local repository in the user home directory. The layers composing a container 
image can then be sequentialy extracted to create a flatened directory tree.
Furthermore udocker also provides the logic to interface with the several 
execution engines that enable the execution of code extracted from the container 
images, thus hiding as much as possible the execution engines specificities.
The execution engines are based on existing software that in most cases has been
further developed, integrated and packaged to be used with udocker. The following
engines are currently provided:

* **F** engine: uses the Linux shared library PRELOAD mechanism to intercept
  shared library calls and translate pathnames to provide an unprivileged chroot 
  like functionality. It is implemented by an extensively enhanced Fakechroot 
  shared library with versions for the `glibc` [@FAKECHROOT-GLIBC-UDOCKER] 
  and `musl` [@FAKECHROOT-MUSL-UDOCKER] C standard libraries. 
  This approach requires the modification of pathnames in the ELF headers of 
  shared libraries and executables. These changes are performed by udocker using 
  a modified `Patchelf` [@PATCHELF-UDOCKER]. This is the 
  execution engine that generally provides the highest performance. 
* **P** engine: uses the Linux PTRACE mechanism to implement a chroot like 
  environment by intercepting system calls and translating pathnames. It is 
  implemented by a modified PRoot [@PROOT-UDOCKER]. This 
  engine provides the highest interoperability across Linux distributions both 
  older and newer, and constitutes the default execution engine for udocker. 
* **R** engine: uses either `runc` [@RUNC] or `crun` [@CRUN] to execute the 
  containers without privileges using Linux user namespaces. Both tools are 
  provided with udocker for wider interoperability.
* **S** engine: uses Singularity [@KURTZER2017] to execute the containers using 
  user namespaces or other Singularity execution method when available. 
  
All required executables are statically compiled for execution across a
wide range of systems. The shared libraries for the **F** modes are also provided
for major Linux distributions. Support for the ARM architecture is provided 
for the **P** mode and is ongoing for the other modes. The binaries for the 
**S** engine are not provided with udocker, as this mode is provided to take 
advantage of local installations of Singularity where available.

Once the udocker Python code is transferred to the target host it can be 
used by an unprivileged user to download the additional executables and 
binaries into the user home directory. The user can then use udocker to 
pull images, create container directories from the images and execute them. 
Each extracted container can be easily setup for execution using any of the 
execution engines. udocker provides a command line interface with a syntax 
similar to docker.

# Research with udocker
udocker was initially developed in the context of the INDIGO-DataCloud
 [@INDIGO2018] project between 2015 and 2017 to support the execution of 
scientific applications in Linux batch and interactive systems where 
container run times can be unavailable, and as a common tool to easily 
execute containers across the ecosystem of computing resources available 
to the researchers. Examples of usage can be found in several domains 
including:
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
was further improved and DEEP-hybrid-datacloud [@DEEP2020] where it was ported 
to Python 3, enhanced to support nvidia GPUs and used to execute deep 
learning frameworks. Since 2021 is used in the EOSC-Synergy [@KERZENMACHER2021], 
EGI-ACE [@EGIACE] and BIG-HPC [@PAULO2020] projects. Althrough is a tool meant for
end-users, it is also supported by several scientific and academic computer 
centers and research infrastructures worldwide such as:

 * EGI advanced computing infrastructure in Europe [@EGI]
 * IBERGRID Iberian distributed computing infrastructure [@IBERGRID]
 * INCD Portuguese Distributed Computing Infrastructure [@INCD]
 * CESGA Supercomputing Center of Galicia [@CESGA]
 * HPC center of the Telaviv University  [@TELAVIV]
 * Trinity College HPC center in Dublin [@TCD]
 * University of Utah HPC center [@UTAH] 
 * University of Coruña Pluton Cluster [@CORUNA]

udocker was been integrated in several research oriented frameworks such as: 

 * SCAR - Serverless Container-aware ARchitectures [@PEREZ2018] to enable execution of containers in Amazon Lambda exploiting function as a service (FaaS);
 * common-workflow-language [@CWL2016], [@KORHONEN2019] to enable containers in scientific workflows;
 * bioconda [@GRUNING2018] for the conda package manager specialized in bioinformatics software;
 * openmole  workflow engine [@REUILLON2013] for exploration of simulation models using high throughput computing.


# Acknowledgements

udocker has been developed in the framework of the H2020 projects INDIGO-Datacloud (RIA 653549), EOSC-hub (RIA 777536) and DEEP-Hybrid-DataCloud (RIA 777435). The proofs of concept have been performed at INCD-Infraestrutura Nacional de Computação Distribuída (funded by FCT, P2020, Lisboa2020, COMPETE and FEDER under the project number 22153-01/SAICT/2016), FinisTerrae II machine provided by CESGA (funded by Xunta de Galicia and MINECO) and Altamira machine (funded by the University of Cantabria and MINECO).

# References



