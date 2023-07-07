# -*- coding: utf-8 -*-
"""Checksumming for files"""
import hashlib
from udocker import LOG


class ChkSUM:
    """Checksumming for files"""

    def __init__(self):
        self._algorithms = {"sha256": self.sha256, "sha512": self.sha512}

    def _hashlib(self, algorithm, filename):
        """hash calculation using hashlib"""
        try:
            with open(filename, "rb") as filep:
                for chunk in iter(lambda: filep.read(4096), b""):
                    algorithm.update(chunk)

            return algorithm.hexdigest()
        except OSError:
            return ""

    def sha256(self, filename):
        """Call the actual implementation selected in __init__"""
        LOG.info("sha256 calculation using hashlib: %s", filename)
        return self._hashlib(hashlib.sha256(), filename)

    def sha512(self, filename):
        """Call the actual implementation selected in __init__"""
        LOG.info("sha512 calculation using hashlib: %s", filename)
        return self._hashlib(hashlib.sha512(), filename)

    def hash(self, filename, algorithm):
        """Compute hash algorithm for file"""
        if algorithm in self._algorithms:
            return self._algorithms[algorithm](filename)

        return ""
