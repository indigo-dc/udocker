#!/usr/bin/env python

import argparse
import git

def get_input_args():
    '''Get input arguments
    '''
    parser = argparse.ArgumentParser(description=(
        'Get git release tags associated with the current commit ID.'
    ))
    parser.add_argument(
        '--repo-path',
        type=str,
        default='.',
        help='Path to the git repository'
    )

    return parser.parse_args()

def main():
    '''main function
    '''
    args = get_input_args()
    repo = git.Repo(args.repo_path)
    try:
        tags = repo.git.describe('--exact-match', 'HEAD')
        tag_list = tags.split('\n')
    except git.exc.GitCommandError as exc:
        tag_list = []

    return tag_list

if __name__ == "__main__":
    print(main())
