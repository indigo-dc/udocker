# Reference card

udocker is user oriented tool to enable pulling and execution of docker
containers were docker is unavailable or cannot be used safely.

## 1. Configuration

The configuration of udocker has the following hierarchy:

1. The default configuration options are set in the `conf` dictionary in the `Config` class.
2. If a configuration file is present, it will override 1.
3. If environment variables are set they will override 2.
4. The presence of general udocker command line options, will override 3. .

## 2. Configuration files

The configuration files allow overriding of the udocker `Config` class
`conf` dictionary. Example of the `udocker.conf` syntax:

```ini
dockerio_registry_url = "https://myregistry.mydomain:5000"
http_insecure = True
verbose_level = 5
```

udocker loads the following configuration files if they are present:

1. `/etc/udocker.conf`
2. `$HOME/.udocker/udocker.conf`: overrides the options set in 1.
3. `$UDOCKER_DIR/udocker.conf` (if different from the above): overrides the options set in 2.
4. Configuration file set with the general CLI option `--config=`: overrides the options set in 3.

## 3. Environment variables

* `UDOCKER_DIR`: root directory of udocker usually $HOME/.udocker
* `UDOCKER_BIN`: location of udocker related executables
* `UDOCKER_LIB`: location of udocker related libraries
* `UDOCKER_DOC`: location of documentation and licenses
* `UDOCKER_CONTAINERS`: location of container directory trees (not images)
* `UDOCKER_TMP`: location of temporary directory
* `UDOCKER_KEYSTORE`: location of keystore for repository login/logout
* `UDOCKER_TARBALL`: location of installation tarball (file of URL)
* `UDOCKER_LOGLEVEL`: logging level
* `UDOCKER_REGISTRY`: override default registry default is Docker Hub.
* `UDOCKER_INDEX`: override default index default is Docker Hub.
* `UDOCKER_DEFAULT_EXECUTION_MODE`: change default execution mode
* `UDOCKER_USE_CURL_EXECUTABLE`: pathname for curl executable
* `UDOCKER_USE_PROOT_EXECUTABLE`: change pathname for proot executable
* `UDOCKER_USE_RUNC_EXECUTABLE`: change pathname for runc executable
* `UDOCKER_USE_SINGULARITY_EXECUTABLE`: change pathname for singularity executable
* `UDOCKER_FAKECHROOT_SO`: change pathname for fakechroot sharable library
* `UDOCKER_FAKECHROOT_EXPAND_SYMLINKS`: translate symbolic links in Fn modes
* `UDOCKER_NOSYSCONF`: prevent loading of udocker system wide configuration

## 4. Verbosity

The verbosity level of udocker can be enforced. Removing banners and most
messages can be achieved by executing with `UDOCKER_LOGLEVEL=2`:

* `UDOCKER_LOGLEVEL` : set verbosity level from 0 to 5 (MIN to MAX verbosity)

Optionally invoke udocker with `--quiet` or `-q` to decrease verbosity.

```bash
udocker --quiet run <container>
```

## 5. Security

udocker does not require any type of privileges nor the deployment of
services by system administrators. It can be downloaded and executed
entirely by the end user. udocker runs under the identity of the user
invoking it.

Most udocker execution modes do not provide process isolation features
such as docker. Due to the lack of isolation udocker must not be run
by privileged users.

## 6. Troubleshooting

Invoke udocker with `-D` for debugging.

```bash
udocker -D run <container>
```

## 7. Documentation

For Python 3:

* <https://indigo-dc.github.io/udocker/>
