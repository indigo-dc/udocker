# -*- coding: utf-8 -*-
"""Messages, output, errors, MSG levels"""
import sys


class Msg(object):
    """Write messages to stdout and stderr. Allows to filter the
    messages to be displayed through a verbose level, also allows
    to control if child process that produce output through a
    file descriptor should be redirected to /dev/null
    """

    NIL = -1
    ERR = 0
    MSG = 1
    WAR = 2
    INF = 3
    VER = 4
    DBG = 5
    DEF = INF
    level = DEF
    previous = DEF
    nullfp = None
    chlderr = sys.stderr
    chldout = sys.stdout
    chldnul = sys.stderr

    def __init__(self, new_level=None):
        """
        Initialize Msg level and /dev/null file pointers to be
        used in subprocess calls to obfuscate output and errors
        """
        if new_level is not None:
            Msg.level = new_level
        try:
            if Msg.nullfp is None:
                Msg.nullfp = open('/dev/null', 'w', encoding='utf-8')
        except (IOError, OSError):
            Msg.chlderr = sys.stderr
            Msg.chldout = sys.stdout
            Msg.chldnul = sys.stderr
        else:
            Msg.chlderr = Msg.nullfp
            Msg.chldout = Msg.nullfp
            Msg.chldnul = Msg.nullfp

    def setlevel(self, new_level=None):
        """Define debug level"""
        if new_level is None:
            new_level = Msg.previous
        else:
            Msg.previous = Msg.level
        Msg.level = new_level
        if Msg.level >= Msg.DBG:
            Msg.chlderr = sys.stderr
            Msg.chldout = sys.stdout
        else:
            Msg.chlderr = Msg.nullfp
            Msg.chldout = Msg.nullfp
        return Msg.previous

    def out(self, *args, **kwargs):
        """Write text to stdout respecting verbose level"""
        level = kwargs.get("l", Msg.MSG)
        if level <= Msg.level:
            sys.stdout.write(' '.join([str(x) for x in args]) + '\n')

    def err(self, *args, **kwargs):
        """Write text to stderr respecting verbose level"""
        level = kwargs.get("l", Msg.ERR)
        if level <= Msg.level:
            sys.stderr.write(' '.join([str(x) for x in args]) + '\n')
