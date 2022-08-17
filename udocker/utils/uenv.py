# -*- coding: utf-8 -*-
"""Object classes to store Nix environment"""

import os
import sys
import string

from udocker import is_genstr

def get_pair(envstr):
    """Split env=var into key and val"""
    if not (is_genstr(envstr) and envstr):
        return ("", "")
    if '=' in envstr:
        try:
            (key, val) = envstr.split('=', 1)
        except (ValueError, NameError, AttributeError):
            return ("", "")
        key = key.strip()
        val = val.strip()
        #for quote in ("'", '"'):
        #    if quote == val[0]:
        #        val = val.strip(quote)
        #        break
    else:
        key = envstr.strip()
        val = os.getenv(envstr, "")
    if not key or ' ' in key or key[0] in string.digits:
        return ("", "")
    return (key, val)


class UenvIterator(object):
    """Uenv Iterator class"""

    def __init__(self, uenv):
        """Init Uenv iterator"""
        self._uenv = uenv
        if sys.version_info[0] >= 3:
            self._keys = list(uenv.env.keys())
        else:
            self._keys = uenv.env.keys()
        self._index = 0

    def __next__(self):
        """Python 3 next (key, value) of environment"""
        if self._index < len(self._keys):
            key = self._keys[self._index]
            value = self._uenv.env[key]
            self._index += 1
            return (key, value)
        raise StopIteration

    next = __next__ # Python 2


class Uenv(object):
    """Class to store environment variables"""

    def __init__(self, thisenv=None):
        """Init Uenv instance"""
        self.env = {}
        if thisenv and not self.add(thisenv):
            raise ValueError('invalid environment')

    def __iter__(self):
        """Returns the Uenv iterator"""
        return UenvIterator(self)

    def __len__(self):
        """Returns the number of stored env variables"""
        return len(self.env)

    def append(self, envstr):
        """Add string with key=val to Uenv"""
        (key, val) = get_pair(envstr)
        if key:
            self.env[key] = val
        return self

    def appendif(self, envstr):
        """Add string with key=val to Uenv if key non-existent"""
        (key, val) = get_pair(envstr)
        if key and key not in self.env:
            self.env[key] = val
        return self

    def extend(self, envlist):
        """Extend Uenv stored environment with list or dict of key=val"""
        if isinstance(envlist, (list)):
            for envstr in envlist:
                self.append(envstr)
        elif isinstance(envlist, (dict)):
            for key in envlist.keys():
                self.env[key] = envlist[key]
        return self

    def extendif(self, envlist):
        """Extend Uenv environment with list of key=val if key non-existant"""
        if isinstance(envlist, (list)):
            for envstr in envlist:
                self.appendif(envstr)
        elif isinstance(envlist, (dict)):
            for key in envlist.keys():
                if key not in self.env:
                    self.env[key] = envlist[key]
        return self

    def add(self, thisenv):
        """Extend Uenv environment with str or list with key=val"""
        if isinstance(thisenv, (str)):
            self.append(thisenv)
        elif isinstance(thisenv, (list)):
            self.extend(thisenv)
        return self

    def getenv(self, key):
        """Get variable by name"""
        try:
            return self.env[key]
        except KeyError:
            return ""

    def setenv(self, key, val):
        """Set variable name"""
        return self.append(f'{key}={val}')

    def unsetenv(self, key):
        """Delete variable by name"""
        try:
            del self.env[key]
            return True
        except KeyError:
            return False

    def list(self):
        """Get list with environment variables"""
        env_list = []
        for (key, val) in self.env.items():
            env_list.append(f'{key}={val}')
        return env_list

    def dict(self):
        """Get dict with environment"""
        return self.env

    def keys(self):
        """Get list of environment variable names"""
        return self.env.keys()
