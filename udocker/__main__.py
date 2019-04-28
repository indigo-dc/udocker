#!/usr/bin/env python

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
import os
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + '/../')
from udocker.umain import UMain


# def main():
#     """main execution function"""
#     run_main = UMain(sys.argv)
#     sys.exit(run_main.start())


if __name__ == "__main__":
    UMain(sys.argv).start()
