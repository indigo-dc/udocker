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
import logging
import click
__version__ = '2.0.0-dev2'


logger = logging.getLogger('udocker')


@click.group(context_settings={
    'help_option_names': ('-h', '--help')}
)
@click.version_option(__version__, '-v', '--version')
def main():
    pass


@click.option('--force', help='force reinstall')
@click.option('--purge', help='remove files (be careful)')
@main.command()
def install(force, purge):
    """Install udocker and its tools
    """
    click.echo('Install files')


@click.argument('directory', nargs=1, type=click.Path(writable=True))
@main.command()
def mkrepo(directory):
    """Create a local repository in a specified directory
    """
    click.echo('Local repository: %s' % directory)


if __name__ == "__main__":
    sys.exit(main())


