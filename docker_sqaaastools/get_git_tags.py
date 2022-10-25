#!/usr/bin/env python3

import argparse
import git


def get_input_args():
    '''Get input arguments
    '''
    parser = argparse.ArgumentParser(description=(
        'Get git release tags associated with the current commit ID.'))
    parser.add_argument('--repo-path', type=str, default='.', help='Path to the git repository')
    return parser.parse_args()


def get_tag_in_last_commit(repo):
    '''Get the tag of the last git commit
    '''
    try:
        tags = repo.git.describe('--exact-match', 'HEAD')
        tag_list = tags.split('\n')
    except git.exc.GitCommandError as e:
        tag_list = []

    return tag_list


def get_tags(repo):
    '''Get all tags
    '''
    tag_list = []
    tags = repo.tags
    if tags:
        tag_list = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
        tag_list.reverse()
        tag_list = [str(tag) for tag in tag_list]

    return tag_list


def main():
    '''main function
    '''
    args = get_input_args()
    repo = git.Repo(args.repo_path, odbt=git.db.GitDB)
    return get_tags(repo)


print(main())
