# -*- coding: utf-8 -*-
"""Checksumming for files"""

import re

from udocker.utils.uprocess import Uprocess

try:
    import hashlib
except ImportError:
    pass

class ChkSUM(object):
    """Checksumming for files"""

    def __init__(self):
        self._algorithms = {}
        try:
            dummy = hashlib.sha256()
            self._algorithms["sha256"] = self._hashlib_sha256
        except NameError:
            self._algorithms["sha256"] = self._openssl_sha256
        try:
            dummy = hashlib.sha512()
            self._algorithms["sha512"] = self._hashlib_sha512
        except NameError:
            self._algorithms["sha512"] = self._openssl_sha512

    def _hashlib(self, algorithm, filename):
        """hash calculation using hashlib"""
        try:
            with open(filename, "rb") as filep:
                for chunk in iter(lambda: filep.read(4096), b""):
                    algorithm.update(chunk)
            return algorithm.hexdigest()
        except (IOError, OSError):
            return ""

    def _hashlib_sha256(self, filename):
        """sha256 calculation using hashlib"""
        return self._hashlib(hashlib.sha256(), filename)

    def _hashlib_sha512(self, filename):
        """sha512 calculation using hashlib"""
        return self._hashlib(hashlib.sha512(), filename)

    def _openssl(self, algorithm, filename):
        """hash calculation using openssl"""
        cmd = ["openssl", "dgst", "-hex", "-r", algorithm, filename]
        output = Uprocess().get_output(cmd)
        if output is None:
            return ""
        match = re.match("^(\\S+) ", output)
        if match:
            return match.group(1)
        return ""

    def _openssl_sha256(self, filename):
        """sha256 calculation using openssl"""
        return self._openssl("-sha256", filename)

    def _openssl_sha512(self, filename):
        """sha512 calculation using openssl"""
        return self._openssl("-sha512", filename)

    def sha256(self, filename):
        """Call the actual implementation selected in __init__"""
        return self._algorithms["sha256"](filename)

    def sha512(self, filename):
        """Call the actual implementation selected in __init__"""
        return self._algorithms["sha512"](filename)

    def hash(self, filename, algorithm):
        """Compute hash algorithm for file"""
        if algorithm in self._algorithms:
            return self._algorithms[algorithm](filename)
        return ""
