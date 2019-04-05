# -*- coding: utf-8 -*-
import os
import subprocess
import json

from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil

try:
    import cStringIO
except ImportError:
    from io import BytesIO as cStringIO
try:
    import pycurl
except ImportError:
    pass


class CurlHeader(object):
    """An http header parser to be used with PyCurl
    Allows to retrieve the header fields and the status.
    Allows to obtain just the header by stopping the
    download (returning -1) e.g to get the content length
    this is useful if the RESTful interface or web server
    does not implement HEAD.
    """

    def __init__(self):
        self.sizeonly = False
        self.data = dict()
        self.data["X-ND-HTTPSTATUS"] = ""
        self.data["X-ND-CURLSTATUS"] = ""

    def write(self, buff):
        """Write is called by Curl()"""
        pair = buff.split(":", 1)
        if len(pair) == 2:
            key = pair[0].strip().lower()
            if key:
                self.data[key] = pair[1].strip()
        elif pair[0].startswith("HTTP/"):
            self.data["X-ND-HTTPSTATUS"] = buff.strip()
        elif (self.sizeonly and
              pair[0].strip() == "" and
              "location" not in self.data):
            return -1
        return None

    def setvalue_from_file(self, in_filename):
        """Load header content from file instead of from Curl()
        Alternative to write() to be used with the curl executable
        version.
        """
        try:
            infile = open(in_filename)
        except (IOError, OSError):
            return False
        for line in infile:
            self.write(line)
        infile.close()
        return True

    def getvalue(self):
        """Return the curl data buffer"""
        return str(self.data)

    def __str__(self):
        """Return a string representation"""
        return str(self.data)


class GetURL(object):
    """File downloader using PyCurl or a curl cli executable"""

    def __init__(self, conf):
        """Load configuration common to the implementations"""
        self.conf = conf
        self.timeout = self.conf['timeout']
        self.ctimeout = self.conf['ctimeout']
        self.download_timeout = self.conf['download_timeout']
        self.agent = self.conf['http_agent']
        self.http_proxy = self.conf['http_proxy']
        self.cache_support = False
        self.insecure = self.conf['http_insecure']
        self._curl_executable = self.conf['use_curl_executable']
        self._select_implementation()

    # pylint: disable=locally-disabled
    def _select_implementation(self):
        """Select which implementation to use"""
        if GetURLpyCurl(self.conf).is_available() and not self._curl_executable:
            self._geturl = GetURLpyCurl(self.conf)
            self.cache_support = True
        elif GetURLexeCurl(self.conf).is_available():
            self._geturl = GetURLexeCurl(self.conf)
        else:
            Msg().err("Error: need curl or pycurl to perform downloads")
            raise NameError('need curl or pycurl')

    def get_content_length(self, hdr):
        """Get content length from the http header"""
        try:
            return int(hdr.data["content-length"])
        except (ValueError, TypeError):
            return -1

    def set_insecure(self, bool_value=True):
        """Use insecure downloads no SSL verification"""
        self.insecure = bool_value
        self._geturl.insecure = bool_value

    def set_proxy(self, http_proxy):
        """Specify a socks http proxy"""
        self.http_proxy = http_proxy
        self._geturl.http_proxy = http_proxy

    def get(self, *args, **kwargs):
        """Get URL using selected implementation
        Example:
            get(url, ctimeout=5, timeout=5, header=[]):
        """
        if len(args) != 1:
            raise TypeError('wrong number of arguments')
        return self._geturl.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        """POST using selected implementation"""
        if len(args) != 2:
            raise TypeError('wrong number of arguments')
        kwargs["post"] = args[1]
        return self._geturl.get(args[0], **kwargs)

    def _get_status_code(self, status_line):
        """
        get http status code from http status line.
        Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF
        """
        parts = status_line.split(" ")
        try:
            return int(parts[1])
        except ValueError:
            return 400


class GetURLpyCurl(GetURL):
    """Downloader implementation using PyCurl"""

    def __init__(self, conf):
        self.conf = conf
        GetURL.__init__(self, self.conf)
        self._url = None

    def is_available(self):
        """Can we use this approach for download"""
        try:
            dummy = pycurl.Curl()
        except (NameError, AttributeError):
            return False
        return True

    def _select_implementation(self):
        """Override the parent class method"""
        pass

    def _set_defaults(self, pyc, hdr):
        """Set options for pycurl"""
        if self.insecure:
            pyc.setopt(pyc.SSL_VERIFYPEER, 0)
            pyc.setopt(pyc.SSL_VERIFYHOST, 0)
        pyc.setopt(pyc.FOLLOWLOCATION, False)
        pyc.setopt(pyc.FAILONERROR, False)
        pyc.setopt(pyc.NOPROGRESS, True)
        pyc.setopt(pyc.HEADERFUNCTION, hdr.write)
        pyc.setopt(pyc.USERAGENT, self.agent)
        pyc.setopt(pyc.CONNECTTIMEOUT, self.ctimeout)
        pyc.setopt(pyc.TIMEOUT, self.timeout)
        pyc.setopt(pyc.PROXY, self.http_proxy)
        if Msg.level >= Msg.DBG:
            pyc.setopt(pyc.VERBOSE, True)
        else:
            pyc.setopt(pyc.VERBOSE, False)
        self._url = ""

    def _mkpycurl(self, pyc, hdr, buf, *args, **kwargs):
        """Prepare curl command line according to invocation options"""
        self._url = str(args[0])
        pyc.setopt(pycurl.URL, self._url)
        if "post" in kwargs:
            pyc.setopt(pyc.POST, 1)
            pyc.setopt(pyc.HTTPHEADER, ['Content-Type: application/json'])
            pyc.setopt(pyc.POSTFIELDS, json.dumps(kwargs["post"]))
        if "sizeonly" in kwargs:
            hdr.sizeonly = True
        if "proxy" in kwargs and kwargs["proxy"]:
            pyc.setopt(pyc.PROXY, pyc.USERAGENT, kwargs["proxy"])
        if "ctimeout" in kwargs:
            pyc.setopt(pyc.CONNECTTIMEOUT, kwargs["ctimeout"])
        if "header" in kwargs:  # avoid known pycurl bug
            clean_header_list = []
            for header_item in kwargs["header"]:
                if str(header_item).startswith("Authorization: Bearer"):
                    if "Signature=" in self._url:
                        continue
                    if "redirect" in kwargs:
                        continue
                clean_header_list.append(str(header_item))
            pyc.setopt(pyc.HTTPHEADER, clean_header_list)
        if "v" in kwargs:
            pyc.setopt(pyc.VERBOSE, kwargs["v"])
        if "nobody" in kwargs:
            pyc.setopt(pyc.NOBODY, kwargs["nobody"])  # header only no content
        if "timeout" in kwargs:
            pyc.setopt(pyc.TIMEOUT, kwargs["timeout"])
        if "ofile" in kwargs:
            output_file = kwargs["ofile"]
            pyc.setopt(pyc.TIMEOUT, self.download_timeout)
            openflags = "wb"
            if "resume" in kwargs and kwargs["resume"]:
                pyc.setopt(pyc.RESUME_FROM, FileUtil(output_file).size())
                openflags = "ab"
            try:
                filep = open(output_file, openflags)
            except(IOError, OSError):
                Msg().err("Error: opening download file: %s" % output_file)
                raise
            pyc.setopt(pyc.WRITEDATA, filep)
        else:
            filep = None
            output_file = ""
            pyc.setopt(pyc.WRITEFUNCTION, buf.write)
        hdr.data["X-ND-CURLSTATUS"] = 0
        return(output_file, filep)

    def get(self, *args, **kwargs):
        """http get implementation using the PyCurl"""
        cont_redirs = 0
        max_redirs = 10
        status_code = 302
        hdr = ""
        while status_code >= 300 and status_code <= 308 and cont_redirs < max_redirs:
            cont_redirs += 1
            hdr = CurlHeader()
            buf = cStringIO.StringIO()
            pyc = pycurl.Curl()
            self._set_defaults(pyc, hdr)
            try:
                (output_file, filep) = self._mkpycurl(pyc, hdr, buf, *args, **kwargs)
                Msg().err("curl url: ", self._url, l=Msg.DBG)
                Msg().err("curl arg: ", kwargs, l=Msg.DBG)
                pyc.perform()     # call pyculr
            except(IOError, OSError):
                return(None, None)
            except pycurl.error as error:
                errno, errstr = error
                hdr.data["X-ND-CURLSTATUS"] = errno
                if not hdr.data["X-ND-HTTPSTATUS"]:
                    hdr.data["X-ND-HTTPSTATUS"] = errstr
            status_code = self._get_status_code(hdr.data["X-ND-HTTPSTATUS"])
            if status_code >= 300 and status_code <= 308:
                args = (hdr.data['location'],)
                kwargs["redirect"] = True

        if "header" in kwargs:
            hdr.data["X-ND-HEADERS"] = kwargs["header"]
        if "ofile" in kwargs:
            filep.close()
            if status_code == 401:  # needs authentication
                pass
            elif status_code == 206 and "resume" in kwargs:
                pass
            elif status_code == 416 and "resume" in kwargs:
                kwargs["resume"] = False
                (hdr, buf) = self.get(self._url, **kwargs)
            elif status_code != 200:
                Msg().err("Error: in download: " + str(
                    hdr.data["X-ND-HTTPSTATUS"]))
                FileUtil(output_file).remove()
        return(hdr, buf)


class GetURLexeCurl(GetURL):
    """Downloader implementation using curl cli executable"""

    def __init__(self, conf):
        GetURL.__init__(self, conf)
        self._opts = None
        self._files = None

    def is_available(self):
        """Can we use this approach for download"""
        return bool(FileUtil("curl").find_exec())

    def _select_implementation(self):
        """Override the parent class method"""
        pass

    def _set_defaults(self):
        """Set defaults for curl command line options"""
        self._opts = {
            "insecure": "",
            "header": "",
            "verbose": "",
            "nobody": "",
            "proxy": "",
            "resume": "",
            "ctimeout": "--connect-timeout " + str(self.ctimeout),
            "timeout": "-m " + str(self.timeout),
            "other": "-s -q -S"
        }
        if self.insecure:
            self._opts["insecure"] = "-k"
        if Msg().level > Msg.DBG:
            self._opts["verbose"] = "-v"
        self._files = {
            "url":  "",
            "error_file": FileUtil("execurl_err").mktmp(),
            "output_file": FileUtil("execurl_out").mktmp(),
            "header_file": FileUtil("execurl_hdr").mktmp()
        }

    def _mkcurlcmd(self, *args, **kwargs):
        """Prepare curl command line according to invocation options"""
        self._files["url"] = str(args[0])
        if "post" in kwargs:
            self._opts["post"] = "-X POST -H Content-Type: application/json' "
            self._opts["post"] += "-d '%s'" % (json.dumps(kwargs["post"]))
        if "ctimeout" in kwargs:
            self._opts["ctimeout"] = "--connect-timeout %s" \
                % (str(kwargs["ctimeout"]))
        if "timeout" in kwargs:
            self._opts["timeout"] = "-m %s" % (str(kwargs["timeout"]))
        if "proxy" in kwargs and kwargs["proxy"]:
            self._opts["proxy"] = "--proxy '%s'" % (str(kwargs["proxy"]))
        elif self.http_proxy:
            self._opts["proxy"] = "--proxy '%s'" % (self.http_proxy)
        if "header" in kwargs:
            for header_item in kwargs["header"]:
                if str(header_item).startswith("Authorization: Bearer"):
                    if "Signature=" in self._files["url"]:
                        continue
                    if "redirect" in kwargs:
                        continue
                    self._opts["header"] += "-H '%s'" % (str(header_item))
        if "v" in kwargs and kwargs["v"]:
            self._opts["verbose"] = "-v"
        if "nobody" in kwargs and kwargs["nobody"]:
            self._opts["nobody"] = "--head"
        if "ofile" in kwargs:
            FileUtil(self._files["output_file"]).remove()
            self._files["output_file"] = kwargs["ofile"] + ".tmp"
            self._opts["timeout"] = "-m %s" % (str(self.download_timeout))
            if "resume" in kwargs and kwargs["resume"]:
                self._opts["resume"] = "-C -"
        curl_executable = "curl"
        if self._curl_executable and isinstance(self._curl_executable, str):
            curl_executable = self._curl_executable
        return(curl_executable + " " + " ".join(self._opts.values()) +
               " -D %s -o %s --stderr %s '%s'" %
               (self._files["header_file"], self._files["output_file"],
                self._files["error_file"], self._files["url"]))

    def get(self, *args, **kwargs):
        """http get implementation using the curl cli executable"""
        cont_redirs = 0
        max_redirs = 10
        status_code = 302
        while status_code >= 300 and status_code <= 308 and cont_redirs < max_redirs:
            cont_redirs += 1
            hdr = CurlHeader()
            buf = cStringIO.StringIO()
            self._set_defaults()
            cmd = self._mkcurlcmd(*args, **kwargs)
            status = subprocess.call(cmd, shell=True, close_fds=True) # call curl
            hdr.setvalue_from_file(self._files["header_file"])
            hdr.data["X-ND-CURLSTATUS"] = status
            if status:
                Msg().err("Error: in download: %s"
                          % str(FileUtil(self._files["error_file"]).getdata()))
                FileUtil(self._files["output_file"]).remove()
                return(hdr, buf)
            status_code = self._get_status_code(hdr.data["X-ND-HTTPSTATUS"])
            if status_code >= 300 and status_code <= 308:
                args = (hdr.data['location'],)
                kwargs["redirect"] = True

        if "header" in kwargs:
            hdr.data["X-ND-HEADERS"] = kwargs["header"]
        if "ofile" in kwargs:
            if " 401" in hdr.data["X-ND-HTTPSTATUS"]:  # needs authentication
                pass
            elif " 206" in hdr.data["X-ND-HTTPSTATUS"] and "resume" in kwargs:
                os.rename(self._files["output_file"], kwargs["ofile"])
            elif " 416" in hdr.data["X-ND-HTTPSTATUS"]:
                if "resume" in kwargs:
                    kwargs["resume"] = False
                (hdr, buf) = self.get(self._files["url"], **kwargs)
            elif " 200" not in hdr.data["X-ND-HTTPSTATUS"]:
                Msg().err("Error: in download: ", str(
                    hdr.data["X-ND-HTTPSTATUS"]), ": ", str(status))
                FileUtil(self._files["output_file"]).remove()
            else:  # OK downloaded
                os.rename(self._files["output_file"], kwargs["ofile"])
        else:
            try:
                buf = cStringIO.StringIO(open(self._files["output_file"],
                                              "r").read())
            except(IOError, OSError):
                Msg().err("Error: reading curl output file to buffer")
            FileUtil(self._files["output_file"]).remove()
        FileUtil(self._files["error_file"]).remove()
        FileUtil(self._files["header_file"]).remove()
        return(hdr, buf)
