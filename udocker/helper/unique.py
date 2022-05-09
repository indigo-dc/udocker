# -*- coding: utf-8 -*-
"""Unique IDentifiers"""

import os
import time
import string

try:
    import random
except ImportError:
    pass

try:
    import uuid
except ImportError:
    pass


class Unique(object):
    """Produce unique identifiers for container names, temporary
    file names and other purposes. If module uuid does not exist
    it tries to use as last option the random generator.
    """
    def __init__(self):
        self.string_set = "abcdef"
        self.def_name = "udocker"

    def _rnd(self, size):
        """Generate a random string"""
        return "".join(
            random.sample(self.string_set * 64 + string.digits * 64, size))

    def uuid(self, name):
        """Get an ID"""
        if not name:
            name = self.def_name
        try:
            return str(uuid.uuid3(uuid.uuid4(), str(name) + str(time.time())))
        except (NameError, AttributeError):
            return f"{self._rnd(8)}-{self._rnd(4)}-{self._rnd(4)}-{self._rnd(4)}-{self._rnd(12)}"

    def imagename(self):
        """Get a container image name"""
        return self._rnd(16)

    def imagetag(self):
        """Get a container image tag"""
        return self._rnd(10)

    def layer_v1(self):
        """Get a random container layer name"""
        return self._rnd(64)

    def filename(self, filename):
        """Get a filename"""
        prefix = self.def_name + '-' + str(os.getpid()) + '-'
        try:
            return (prefix +
                    str(uuid.uuid3(uuid.uuid4(), str(time.time()))) +
                    '-' + str(filename))
        except (NameError, AttributeError):
            return prefix + self.uuid(filename) + '-' + str(filename)
