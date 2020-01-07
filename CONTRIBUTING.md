Introduction
============
Thanks for considering contributing to udocker.
Contributions to udocker are welcome. 
You can contribute by improving the documentation, submit bug reports,
provide feature requests, or writing code for udocker its installation
and testing.

Ground Rules
============
We aim at having portability, udocker is meant to be executed both
on older distributions (such as CentOS 6) and newer, so beware of
which python features you use and whether they are supported in
older distributions.

udocker is meant to be very easily moved between hosts, and submitted 
to batch systems, that's why we have everything in a single Python script.

Repositories
============
For udocker: https://github.com/indigo-dc/udocker
For PRoot: https://github.com/jorge-lip/proot-udocker
For libfakechroot-glibc: https://github.com/jorge-lip/libfakechroot-glibc-udocker
For libfakechroot-musl: https://github.com/jorge-lip/libfakechroot-musl-udocker
For patchelf: https://github.com/jorge-lip/patchelf-udocker

How to report a bug
===================
If you find a security vulnerability, do NOT open an issue.
Email udocker@lip.pt instead.

Other issues and or feature enhancements can be communicated on GitHub 
https://github.com/indigo-dc/udocker/issues

Code contributions
==================

* Perform pull requests against the devel branch for the current python 2 based version.
* Perform pull requests against the devel3 branch for the future python 3 based version.
* Please check you Python code with pylint.
* For new features please also provide unit tests.
