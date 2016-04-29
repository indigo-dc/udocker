# udocker
A basic user tool to execute simple containers in batch or interactive 
systems without root privileges. Enables basic idownload and execution 
of docker containers in systems without docker and where the user does 
not have root privileges, such as batch systems and interactive clusters
managed by other entities.

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
  load  <exported-image>      :Load container image saved by docker
  inspect <repo/image:tag>    :Return low level information on image
  verify <repo/image:tag>     :Verify a pulled image

  protect <repo/image:tag>    :Protect repository
  unprotect <repo/image:tag>  :Unprotect repository
  protect <container_id>      :Protect container
  unprotect <container_id>    :Unprotect container

  mkrepo <topdir>             :Create repository in another location

  help                        :This help
  help <command>              :Help about specific command
  help options                :Help about all command options

Options common to all commands must appear before the command:
  -D                          :Debug
  --repo=<directory>          :Use repository at directory
```

## Examples
Some examples of usage:

Search on dockerhub
```
udocker search fedora
```

Pull from docker hub and list local images
```
udocker pull fedora
udocker images
```

Create the container from the image and run it
```
udocker create --name=myfed  fedora
udocker run  myfed  cat /etc/redhat-release
```

Run mounting some directories
```
udocker run -v /home:/home -v /var:/var  myfed  /bin/bash
```

Install software
```
udocker run  myfed  yum install firefox
```

Run as some user
```
udocker --user 1000:1001 run  myfed  /bin/id
```

## Aknowlegments

PRoot http://proot.me
