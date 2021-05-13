# udocker organization of classes

Repository path udocker/udocker

Based in version 1.1.3 released in the DEEP-Hybrid-dataCloud project.

## Base directory

dir = .

* udocker.py - class Main(object):
* cmdparser.py - class CmdParser(object):
* cli.py -     class UdockerCLI(object):
  * This is the command line implementation
* config.py -  class Config(object):
* tools.py -   class UdockerTools(object):
* msg.py - class Msg(object):
* docker.py:
  * class DockerIoAPI(object):
  * class DockerLocalFileAPI(object):



## Directory utils

dir = utils/

* uprocess.py - class Uprocess(object):
* filebind.py - class FileBind(object):
* fileutil.py - class FileUtil(object):
* chkcsum.py -  class ChkSUM(object):

* curl.py:
  * class CurlHeader(object):
  * class GetURL(object):
  * class GetURLpyCurl(GetURL):
  * class GetURLexeCurl(GetURL):

## Directory helper

dir = helper

* guestinfo.py -  class GuestInfo(object):
* keystore.py -   class KeyStore(object):
* unique.py -     class Unique(object):
* elfpatcher.py - class ElfPatcher(object):
* nixauth.py -    class NixAuthentication(object):

## Directory engine

dir = engine/

* base.py -        class ExecutionEngineCommon(object):
* proot.py -       class PRootEngine(ExecutionEngineCommon):
* runc.py -        class RuncEngine(ExecutionEngineCommon):
* singularity.py - class SingularityEngine(ExecutionEngineCommon):
* fakechroot.py -  class FakechrootEngine(ExecutionEngineCommon):
* nvidia.py -      class NvidiaMode(object):
* execmode.py -    class ExecutionMode(object):

## Directory container

dir = container

* structure.py - class ContainerStructure(object):
* localrepo.py - class LocalRepository(object):
