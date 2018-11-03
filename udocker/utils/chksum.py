# -*- coding: utf-8 -*-
import hashlib
import re


class ChkSUM(object):
    """Checksumming for files"""

    def __init__(self):
        try:
            dummy = hashlib.sha256()
            self._sha256_call = self._hashlib_sha256
        except NameError:
            self._sha256_call = self._openssl_sha256

    def _hashlib_sha256(self, filename):
        """sha256 calculation using hashlib"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filename, "rb") as filep:
                for chunk in iter(lambda: filep.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (IOError, OSError):
            return ""

    def _openssl_sha256(self, filename):
        """sha256 calculation using openssl"""
        cmd = "openssl dgst -hex -r -sha256 %s" % (filename)
        output = Uprocess().get_output(cmd)
        if output is None:
            return ""
        match = re.match("^(\\S+) ", output)
        if match:
            return match.group(1)
        return ""

    def sha256(self, filename):
        """
        Call the actual sha256 implementation selected in __init__
        """
        return self._sha256_call(filename)
