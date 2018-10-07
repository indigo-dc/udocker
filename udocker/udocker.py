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
import click


@click.command()
def main(args=None):

    click.echo("Replace this message by putting your code into "
               "udocker.udocker.main")
    click.echo("See click documentation at http://click.pocoo.org/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
  

