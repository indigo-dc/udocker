# -*- coding: utf-8 -*-
"""Manipulate volume bindings host_path:container_path"""


class Uvolume(object):
    """Manipulate volumes"""

    def __init__(self, volume=""):
        self.volume = volume

    def cleanpath(self, path):
        """Remove duplicate and trailing slashes"""
        clean_path = ""
        p_char = ''
        for char in str(path):
            if not clean_path:
                clean_path = char
            else:
                if not (char == p_char and char == '/'):
                    clean_path += char
            p_char = char

        if clean_path == "/":
            return clean_path

        return clean_path.rstrip('/')

    def split(self):
        """Split volume string host_path:container_path into list"""
        try:
            (host_dir, cont_dir) = self.volume.split(":", 1)
            if not cont_dir:
                cont_dir = host_dir
        except ValueError:
            host_dir = self.volume
            cont_dir = self.volume
        return (self.cleanpath(host_dir), self.cleanpath(cont_dir))
