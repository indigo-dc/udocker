udocker reference card
======================
udocker is user oriented tool to enable pulling and execution of docker
containers were docker is unavailable or cannot be used safely. 

## Configuration files

* /etc/udocker.conf
* $UDOCKER_DIR/udocker.conf
* $HOME/.udocker/udocker.conf
* $HOME/.udocker/containers/<container-id>/container.conf

All attributes of the udocker::Config class can be modified via the
configuration files. Example:

```
# do not verify digital certificates
http_insecure = True
# set default verbose level
verbose_level = 5
```

## Environment variables

 * UDOCKER_DIR : root directory of udocker usually $HOME/.udocker
 * UDOCKER_BIN : location of udocker related executables
 * UDOCKER_LIB : location of udocker related libraries
 * UDOCKER_CONTAINERS : location of container directory trees (not images)
 * UDOCKER_TMP : location of temporary directory
 * UDOCKER_KEYSTORE : location of keystore for repository login/logout
 * UDOCKER_TARBALL : location of installation tarball (file of URL)
 * UDOCKER_LOGLEVEL : logging level
 * UDOCKER_REGISTRY : override default registry default is Docker Hub.
 * UDOCKER_INDEX : override default index default is Docker Hub.
 * UDOCKER_DEFAULT_EXECUTION_MODE : change default execution mode
 * UDOCKER_USE_CURL_EXECUTABLE : pathname for curl executable
 * UDOCKER_USE_PROOT_EXECUTABLE : change pathname for proot executable
 * UDOCKER_USE_RUNC_EXECUTABLE : change pathname for runc executable
 * UDOCKER_USE_SINGULARITY_EXECUTABLE : change pathname for singularity executable
 * UDOCKER_FAKECHROOT_SO : change pathname for fakechroot sharable library
 * UDOCKER_FAKECHROOT_EXPAND_SYMLINKS : translate symbolic links in Fn modes
 * UDOCKER_NOSYSCONF : prevent loading of udocker system wide configuration

## Verbosity

The verbosity level of udocker can be enforced. Removing banners and most
messages can be achieved by executing with UDOCKER_LOGLEVEL=2

 * UDOCKER_LOGLEVEL : set verbosity level from 0 to 5 (MIN to MAX verbosity)

Optionally invoke udocker with `--quiet` or `-q` to decrease verbosity.

```
 udocker --quiet run <container>
```

## Security

udocker does not require any type of privileges nor the deployment of 
services by system administrators. It can be downloaded and executed 
entirely by the end user. udocker runs under the identity of the user
invoking it.

Most udocker execution modes do not provide process isolation features
such as docker. Due to the lack of isolation udocker must not be run 
by privileged users.

## Troubleshooting

Invoke udocker with `-D` for debugging.

```
 udocker -D run <container>
```

## Documentation

* https://github.com/indigo-dc/udocker/blob/master/SUMMARY.md 

