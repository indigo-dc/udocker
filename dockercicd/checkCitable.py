from github import Github
from github import GithubException
from urllib.parse import urlparse
import gitlab
import sys


def is_file_in_github_repo(repo, file):
    '''Find file in github repository
    repo: repository url
    file: filename
    '''
    ghub = Github()
    g_repo = ghub.get_repo(repo)
    try:
        g_repo.get_contents(file)
        print(f"File {file} found in GitHub repository {g_repo.name}")
        return True
    except GithubException:
        print(f"File {file} not found in GitHub repository {g_repo.name}")
        return False

def is_file_in_gitlab_repo(server, repo, file):
    '''Find file in gitlab repository
    server: gitlab server
    repo: repository url
    file: filename
    '''
    glab = gitlab.Gitlab(server)
    try:
        project = glab.projects.get(repo)
        items = project.repository_tree()
        for item in items:
            if(item['name'] == file):
                print(f"File {file} found in GitLab repository {repo}")
                return True
    except gitlab.exceptions.GitlabGetError:
        print("Repository not found or no permission to access it.")
        return False

    print(f"File {file} not found in GitLab repository {repo}")
    return False

def is_file_in_repo(urlrepo, file):
    '''Find file in git repository
    url: repository url
    file: filename
    '''
    urlp = urlparse(urlrepo)
    repo = urlp.path[1:]
    retvalue = False
    if urlp.hostname == 'github.com':
        retvalue = is_file_in_github_repo(repo, file)
    else:
        server = urlp.scheme + "://" + urlp.netloc
        retvalue =  is_file_in_gitlab_repo(server, repo, file)

    return retvalue

if __name__ == "__main__":
    url = sys.argv[1]
    print("Repository URL " , url)
    assert (is_file_in_repo(url, "CITATION.json") or
            is_file_in_repo(url, "CITING.md") or
            is_file_in_repo(url, "codemeta.json"))
