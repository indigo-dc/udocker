# -*- coding: utf-8 -*-
"""Management and tools for the keystore"""

import os
import json

from udocker.utils.fileutil import FileUtil
from udocker.helper.hostinfo import HostInfo


class KeyStore(object):
    """Basic storage for authentication tokens to be used
    with dockerhub and private repositories
    """

    def __init__(self, keystore_file):
        """Initialize keystone"""
        self.keystore_file = keystore_file
        self.credential = {}

    def _verify_keystore(self):
        """Verify the keystore file and directory"""
        keystore_uid = FileUtil(self.keystore_file).uid()
        if keystore_uid not in (-1, HostInfo.uid):
            raise IOError(f"not owner of keystore: {self.keystore_file}")
        keystore_dir = os.path.dirname(self.keystore_file)
        if FileUtil(keystore_dir).uid() != HostInfo.uid:
            raise IOError(f"keystore dir not found or not owner: {keystore_dir}")
        if (keystore_uid != -1 and (os.stat(self.keystore_file).st_mode & 0o077)):
            raise IOError(f"keystore is accessible to group or others: {self.keystore_file}")

    def _read_all(self):
        """Read all credentials from file"""
        try:
            with open(self.keystore_file, "r", encoding='utf-8') as filep:
                return json.load(filep)
        except (IOError, OSError, ValueError):
            return {}

    def _shred(self):
        """Shred file content"""
        exit_status = 0
        self._verify_keystore()
        try:
            size = FileUtil(self.keystore_file).size()
            with open(self.keystore_file, "rb+") as filep:
                filep.write(b" " * size)
        except (IOError, OSError):
            exit_status = 1
            return exit_status
        return exit_status

    def _write_all(self, auths):
        """Write all credentials to file"""
        exit_status = 0
        self._verify_keystore()
        oldmask = None
        try:
            oldmask = os.umask(0o77)
            with open(self.keystore_file, "w", encoding='utf-8') as filep:
                json.dump(auths, filep)
            os.umask(oldmask)
        except (IOError, OSError):
            if oldmask is not None:
                os.umask(oldmask)
            exit_status = 1
            return exit_status
        return exit_status

    def get(self, url):
        """Get credential from keystore for given url"""
        auths = self._read_all()
        try:
            self.credential = auths[url]
            return self.credential["auth"]
        except KeyError:
            pass
        return ""

    def put(self, url, credential, email):
        """Put credential in keystore for given url"""
        if not credential:
            return 1
        auths = self._read_all()
        auths[url] = {"auth": credential, "email": email, }
        self._shred()
        return self._write_all(auths)

    def delete(self, url):
        """Delete credential from keystore for given url"""
        self._verify_keystore()
        auths = self._read_all()
        try:
            del auths[url]
        except KeyError:
            return 1
        self._shred()
        return self._write_all(auths)

    def erase(self):
        """Delete all credentials from keystore"""
        self._verify_keystore()
        try:
            self._shred()
            os.unlink(self.keystore_file)
        except (IOError, OSError):
            return 1
        return 0
