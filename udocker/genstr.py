# -*- coding: utf-8 -*-
"""Handling str instance checking"""
import sys


def is_genstr(objstr):
    """test if objstr is string or unicode both in py2 and py3
    unicode type has been removed in py3
    :param objstr (string): object to test if string or unicode
    :return (bool) is_gstr if it is string or unicode or not
    """
    is_gstr = False
    if sys.version_info[0] >= 3:
        is_gstr = isinstance(objstr, str)
    else:
        is_gstr = isinstance(objstr, (str, unicode))

    return is_gstr
