# Contributing

## Introduction

Thanks for considering contributing to udocker.
Contributions to udocker are welcome.
You can contribute by improving the documentation, submit bug reports,
provide feature requests, or writing code for udocker its installation
and testing.

## Ground Rules

We aim at having portability, udocker is meant to be executed both
on older distributions (such as CentOS 6) and newer, so beware of
which python features you use and whether they are supported in
older distributions.

The current Python 2 version of udocker is meant to be very easily moved
between hosts, and submitted to batch systems, that's why we have everything
in a single Python script.

Development work on a Python 3 version is ongoing in branch devel3
This version supports Python 2 and Python 3 and is modular.

## Repositories

* For udocker: <https://github.com/indigo-dc/udocker>
* For PRoot: <https://github.com/jorge-lip/proot-udocker>
* For libfakechroot-glibc: <https://github.com/jorge-lip/libfakechroot-glibc-udocker>
* For libfakechroot-musl: <https://github.com/jorge-lip/libfakechroot-musl-udocker>
* For patchelf: <https://github.com/jorge-lip/patchelf-udocker>

## How to report a bug

If you find a security vulnerability, do NOT open an issue.
Email udocker@lip.pt instead.

Other issues and or feature enhancements can be communicated on GitHub
<https://github.com/indigo-dc/udocker/issues>

## Code contributions

* Perform pull requests against the devel3 branch for the python 3 based version: <https://github.com/indigo-dc/udocker/tree/devel3>
* Perform pull requests against the devel branch for maintenance of the old python 2 based version <https://github.com/indigo-dc/udocker/tree/devel>
* Please check you Python code with pylint.
* For new features please also provide unit tests.
