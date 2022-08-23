# -*- coding: utf-8 -*-
"""
========
udocker
========
Wrapper to execute basic docker containers without using docker.
This tool is a last resort for the execution of docker containers
where docker is unavailable. It only provides a limited set of
functionalities.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import sys
__author__ = "udocker@lip.pt"
__copyright__ = "Copyright 2016 - 2022, LIP"
__credits__ = ["PRoot http://proot.me",
               "runC https://runc.io",
               "crun https://github.com/containers/crun",
               "Fakechroot https://github.com/dex4er/fakechroot",
               "Singularity http://singularity.lbl.gov"
              ]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "1.3.3"
__date__ = "2022"

def is_genstr(objstr):
    """test if objstr is string or unicode both in py2 nd py3
    unicode type has been removed in py3
    :param objstr: object to test if string or unicode
    :return (bool) is_gstr if it is string or unicode or not
    """
    is_gstr = False
    if sys.version_info[0] >= 3:
        is_gstr = isinstance(objstr, str)
    else:
        is_gstr = isinstance(objstr, (str, unicode))
    return is_gstr
