#!/usr/bin/env python

import argparse
import json
from pathlib import Path


# Types of files to look for
FILE_TYPES = [
    'all',
    'README',
    'CODE_OF_CONDUCT',
    'CONTRIBUTING'
]
# Follows GitHub supported markup languages
# -- https://github.com/github/markup/blob/master/README.md#markups
AVAILABLE_EXTENSIONS = [
    '',     # allow no-extension
    '.markdown', '.mdown', '.mkdn', '.md',
    '.textile',
    '.rdoc',
    '.org',
    '.creole',
    '.mediawiki', '.wiki',
    '.rst',
    '.asciidoc', '.adoc', '.asc',
    '.pod'
]
# Ordered list of possible file locations
LOCATIONS = [
    '.',
    'docs',
    '.github'
]


def get_input_args():
    '''Get input arguments
    '''
    parser = argparse.ArgumentParser(description=(
        'Find common collaboration-enabling files in a code repository.'
    ))
    parser.add_argument(
        '--file_type',
        choices=FILE_TYPES,
        type=str,
        help='Type of file to look for in the code repository'
    )
    parser.add_argument(
        '--path',
        metavar='PATH',
        type=str,
        help='Path to look for in the code repository'
    )
    parser.add_argument(
        '--extension',
        metavar='EXTENSION',
        type=str,
        action='append',
        help=(
            'Filter by extension (default: %s)' % AVAILABLE_EXTENSIONS
        )
    )

    return parser.parse_args()


def get_st_size(file_name):
    '''Get file size
    '''
    return Path(file_name).stat().st_size


def find_file(file_type, extensions, check_single_path=None):
    '''Find a file
    '''
    locations = LOCATIONS
    if check_single_path:
        locations = [check_single_path]
    for extension in extensions:
        file_name = ''.join([file_type, extension])
        for location in locations:
            path_obj = Path(location).joinpath(file_name)
            if path_obj.exists():
                return path_obj.as_posix()


def main():
    '''main function
    '''
    args = get_input_args()
    FILE_TYPES.remove('all')
    if not args.file_type or args.file_type in ['all']:
        args.file_type = FILE_TYPES
    else:
        args.file_type = [args.file_type]

    if not args.extension:
        args.extension = AVAILABLE_EXTENSIONS

    out = {}
    for file_type in args.file_type:
        file_found_list = []
        file_found = find_file(
            file_type=file_type,
            extensions=args.extension,
            check_single_path=args.path
        )
        file_data = {}
        if file_found:
            file_data = {
                'file_name': file_found,
                'size': get_st_size(file_found)
            }
            file_found_list.append(file_data)

        out[file_type] = file_found_list

    return json.dumps(out)


print(main())
