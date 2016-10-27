#! /usr/bin/env python
# Copyright (C) 2014 Bitergia

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
from ConfigParser import SafeConfigParser

def read_main_conf(conf_file, panel):
    parser = SafeConfigParser()
    fd = open(conf_file, 'r')
    parser.readfp(fd)
    fd.close()
    options = {}
    if parser.has_section(panel):
        if parser.getboolean(panel,'status'):
            opti = parser.options(panel)
            for o in opti:
                if (o != 'status'):
                    options[o] = parser.get(panel,o)
    return options

    """sec = parser.sections()
    for s in sec:
        options[s] = {}
        opti = parser.options(s)
        for o in opti:
            # first, some special cases
            if o == 'debug':
                options[s][o] = parser.getboolean(s,o)
            elif o in ('trackers', 'projects', 'pre_scripts', 'post_scripts'):
                data_sources = parser.get(s,o).split(',')
                options[s][o] = [ds.replace('\n', '') for ds in data_sources]
            else:
                options[s][o] = parser.get(s,o)

    return options"""

def get_arguments():
    parser = argparse.ArgumentParser(description='Apply conf parameters to templates')
    parser.add_argument('--template', dest='template_file', help='Template file name')
    parser.add_argument('--content', dest='content_file', help='Content file name')
    parser.add_argument('--conf', dest='conf_file', help='Conf file name')
    parser.add_argument('--panel', dest='panel', help='Panel name')

    args = parser.parse_args()
    #print args.accumulate(args.integers)
    return args

def include_values(conf, body_template):
    for k in conf.keys():
        upper_key = k.upper()
        replace_pattern = 'REPLACE_' + upper_key
        body_template = body_template.replace(replace_pattern,conf[k])
    return body_template

def include_webstats(html_body):
    """
    Replace string "REPLACE_WEBSTATS" in html_body with JS code from file
    webstats.tmpl if present. If not, it just include and empty string
    """
    text = "REPLACE_WEBSTATS"
    try:
        fd = open("webstats.tmpl","r")
        jscode = fd.read()
        fd.close()
    except:
        jscode = ""
    html_body = html_body.replace(text, jscode)
    return html_body

#python .. --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scm-repos
if __name__ == "__main__":

    arg = get_arguments()

    conf = read_main_conf(arg.conf_file, arg.panel)

    fd = open(arg.content_file, "r")
    body = fd.read()
    fd.close()
    body = include_values(conf, body)

    fd = open(arg.template_file, "r")
    template = fd.read()
    fd.close()

    template = include_webstats(template)
    text = "REPLACE_HERE"
    template = template.replace(text, body)

    print template
