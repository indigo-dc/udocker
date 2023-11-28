#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: UdockerCLI
"""
import json
import os

import pytest

from udocker import MSG, LOG
from udocker.cli import UdockerCLI
from udocker.cmdparser import CmdParser
from udocker.config import Config
from udocker.helper.hostinfo import HostInfo
from udocker.helper.unshare import Unshare


@pytest.fixture
def lrepo(mocker):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    return mock_lrepo


@pytest.fixture
def cmdparse(mocker):
    mock_cmdp = mocker.patch('udocker.cmdparser.CmdParser')
    return mock_cmdp


@pytest.fixture
def config(mocker):
    mock_conf = mocker.patch('udocker.cli.Config')
    return mock_conf


@pytest.fixture
def dioapi(mocker):
    mock_dioapi = mocker.patch('udocker.cli.DockerIoAPI')
    return mock_dioapi


@pytest.fixture
def lfapi(mocker):
    mock_lfapi = mocker.patch('udocker.cli.LocalFileAPI')
    return mock_lfapi


@pytest.fixture
def ks(mocker):
    mock_ks = mocker.patch('udocker.cli.KeyStore')
    return mock_ks


@pytest.fixture
def ucli(mocker, lrepo, dioapi, lfapi, ks, config):
    config.conf['keystore'] = "/xxx"
    return UdockerCLI(lrepo)


@pytest.fixture
def ucli2(mocker, lrepo, dioapi, lfapi, ks, config):
    config.conf['keystore'] = "/xxx"
    return UdockerCLI(lrepo)


@pytest.fixture
def udockertools(mocker):
    return mocker.patch('udocker.cli.UdockerTools')


def test_01_init(mocker, lrepo):
    """Test01 UdockerCLI() constructor."""
    mock_dioapi = mocker.patch('udocker.cli.DockerIoAPI')
    mock_lfapi = mocker.patch('udocker.cli.LocalFileAPI')
    mock_ks = mocker.patch('udocker.cli.KeyStore')
    mock_conf = mocker.patch('udocker.cli.Config')
    mock_conf.conf['keystore'] = "/xxx"
    UdockerCLI(lrepo)
    mock_dioapi.assert_called()
    mock_lfapi.assert_called()
    mock_ks.assert_called()


data_cdrepo = ((None, True, 0, False),
               (False, False, 1, False),
               (True, False, 1, True))


@pytest.mark.parametrize('risdir,ropt,cisdir,expected', data_cdrepo)
def test_02__cdrepo(mocker, ucli, cmdparse, risdir, ropt, cisdir, expected):
    """Test02 UdockerCLI()._cdrepo()."""
    mock_isdir = mocker.patch('udocker.cli.FileUtil.isdir', return_value=risdir)
    cmdparse.get.return_value = '/.udocker'
    cmdparse.missing_options.return_value = ropt
    resout = ucli._cdrepo(cmdparse)
    assert resout == expected
    assert mock_isdir.call_count == cisdir


#    assert lrepo.setup.call_count == clrepo


data_imgspec = ((False, '', None, (None, None)),
                (True, '', 'AAA', ('AAA', 'latest')),
                (True, 'AAA:45', None, ('AAA', '45')))


@pytest.mark.parametrize('rdioapi,inprmt1,inprmt2,expected', data_imgspec)
def test_03__check_imagespec(mocker, ucli, dioapi, rdioapi, inprmt1, inprmt2, expected):
    """Test03 UdockerCLI()._check_imagespec()."""
    dioapi.is_repo_name.return_value = rdioapi
    resout = ucli._check_imagespec(inprmt1, inprmt2)
    assert resout == expected


data_imgrepo = ((False, '', None, None),
                (True, '', 'AAA', 'AAA'),
                (True, 'AAA:45', None, 'AAA:45'))


@pytest.mark.parametrize('rdioapi,inprmt1,inprmt2,expected', data_imgrepo)
def test_04__check_imagerepo(mocker, ucli, dioapi, rdioapi, inprmt1, inprmt2, expected):
    """Test04 UdockerCLI()._check_imagespec()."""
    dioapi.is_repo_name.return_value = rdioapi
    resout = ucli._check_imagerepo(inprmt1, inprmt2)
    assert resout == expected


data_setrepo = (('registry.io', 'dockerhub.io', 'dockerhub.io/myimg:1.2', 'http://proxy', True),
                ('', '', 'https://dockerhub.io/myimg:1.2', 'http://proxy', True),
                ('', '', 'dockerhub', 'http://proxy', False))


@pytest.mark.parametrize('regist,idxurl,imgrepo,http_proxy,expected', data_setrepo)
def test_05__set_repository(mocker, ucli, dioapi, regist, idxurl, imgrepo, http_proxy, expected):
    """Test05 UdockerCLI()._set_repository()."""
    dioapi.set_proxy.return_value = None
    dioapi.set_registry.side_effect = [None, None, None, None]
    dioapi.set_index.side_effect = [None, None, None, None]
    resout = ucli._set_repository(regist, idxurl, imgrepo, http_proxy)
    assert resout == expected
    dioapi.return_value.set_proxy.assert_called()
    # dioapi.return_value.set_registry.assert_called()
    # dioapi.return_value.set_index.assert_called()


data_setimg = (('', ('', '', '', '')),
               ('dockerhub.io/myimg:1.2', ('', 'dockerhub.io', 'myimg', '1.2')),
               ('https://dockerhub.io/myimg:1.2', ('https:', 'dockerhub.io', 'myimg', '1.2')),
               ('https://dockerhub/myimg:1.2', ('https:', '', 'dockerhub/myimg', '1.2')))


@pytest.mark.parametrize('imgrepo,expected', data_setimg)
def test_06__split_imagespec(mocker, ucli, imgrepo, expected):
    """Test06 UdockerCLI()._split_imagespec()."""
    resout = ucli._split_imagespec(imgrepo)
    assert resout == expected


def test_07_do_mkrepo(mocker, ucli, cmdparse):
    """Test07 UdockerCLI().do_mkrepo()."""
    cmdparse.get.return_value = '/.udocker'
    cmdparse.missing_options.return_value = True
    mock_exists = mocker.patch('udocker.cli.os.path.exists')
    resout = ucli.do_mkrepo(cmdparse)
    assert resout == ucli.STATUS_ERROR
    mock_exists.assert_not_called()


def test_08_do_mkrepo(mocker, ucli, cmdparse, lrepo):
    """Test08 UdockerCLI().do_mkrepo()."""
    cmdparse.get.return_value = '/.udocker'
    cmdparse.missing_options.return_value = False
    mock_exists = mocker.patch('udocker.cli.os.path.exists', return_value=False)
    lrepo.setup.return_value = None
    lrepo.create_repo.return_value = False
    resout = ucli.do_mkrepo(cmdparse)
    assert resout == ucli.STATUS_ERROR
    mock_exists.assert_called()
    lrepo.setup.assert_called()
    lrepo.create_repo.assert_called()


def test_09_do_mkrepo(mocker, ucli, cmdparse, lrepo):
    """Test09 UdockerCLI().do_mkrepo()."""
    cmdparse.get.return_value = '/.udocker'
    cmdparse.missing_options.return_value = False
    mock_exists = mocker.patch('udocker.cli.os.path.exists', return_value=True)
    lrepo.setup.return_value = None
    lrepo.create_repo.return_value = False
    resout = ucli.do_mkrepo(cmdparse)
    assert resout == ucli.STATUS_ERROR
    mock_exists.assert_called()
    lrepo.setup.assert_not_called()
    lrepo.create_repo.assert_not_called()


def test_10_do_mkrepo(mocker, ucli, cmdparse, lrepo):
    """Test10 UdockerCLI().do_mkrepo()."""
    cmdparse.get.return_value = '/.udocker'
    cmdparse.missing_options.return_value = False
    mock_exists = mocker.patch('udocker.cli.os.path.exists', return_value=False)
    lrepo.setup.return_value = None
    lrepo.create_repo.return_value = True
    resout = ucli.do_mkrepo(cmdparse)
    assert resout == ucli.STATUS_OK
    mock_exists.assert_called()
    lrepo.setup.assert_called()
    lrepo.create_repo.assert_called()


def test_11__search_print_lines(mocker, ucli):
    """Test11 UdockerCLI()._search_print_lines()."""
    fmt = "%-55.80s %8.8s %-70.70s %5.5s"
    repo_list = {
        'results': [
            {'name': 'repo1', 'is_official': True, 'description': 'First repo', 'star_count': 10},
            {'name': 'repo2', 'is_official': False, 'description': 'Second repo\n', 'star_count': 5}
        ]
    }
    lines = 2
    mock_msg = mocker.patch.object(MSG, 'info')
    ucli._search_print_lines(repo_list, lines, fmt)
    expected_calls = [
        mocker.call("repo1                                                       [OK] First repo                       "
                    "                                         10"),
        mocker.call("repo2                                                       ---- Second repo                      "
                    "                                          5")
    ]
    mock_msg.assert_has_calls(expected_calls)


@pytest.mark.parametrize("pause, no_trunc, search_ended, expected_status", [
    (False, False, False, 0),
    (True, False, False, 0),
    (False, True, False, 0)
])
def test_12__search_repositories(mocker, ucli, pause, no_trunc, search_ended, expected_status):
    """Test12 UdockerCLI()._search_repositories()."""
    expression = "ipyrad"
    mock_termsz = mocker.patch.object(HostInfo, 'termsize', return_value=(3, ""))
    mock_doiasearch = mocker.patch.object(ucli.dockerioapi, 'search_get_page')
    mocker.patch.object(ucli.dockerioapi, 'search_ended', search_ended)

    repo_list = {
        "count": 1, "next": "", "previous": "",
        "results": [
            {
                "repo_name": "lipcomputing/ipyrad",
                "short_description": "Docker to run ipyrad",
                "star_count": 0,
                "pull_count": 188,
                "repo_owner": "",
                "is_automated": True,
                "is_official": False
            }
        ]
    }

    if pause:
        mocker.patch('udocker.cli.GET_INPUT', side_effect=['q'])
        mock_doiasearch.side_effect = [repo_list, repo_list, []]
    else:
        mock_doiasearch.side_effect = [repo_list, []]

    status = ucli._search_repositories(expression, pause, no_trunc)
    assert status == expected_status
    mock_doiasearch.assert_called()
    mock_doiasearch.assert_called_with(expression, 1)
    mock_termsz.assert_called()


@pytest.mark.parametrize("tags, expected_status, raises_exception", [
    (["latest", "v1.0", "v2.0"], 0, None),
    ([], 0, None),
    (None, 1, KeyError),
    (None, 1, TypeError),
    (None, 1, ValueError),
])
def test_13__list_tags(mocker, ucli, tags, expected_status, raises_exception):
    """Test10 UdockerCLI()._list_tags()."""
    expression = "t1"
    mock_get_tags = mocker.patch.object(ucli.dockerioapi, 'get_tags', side_effect=raises_exception, return_value=tags)
    mock_msg = mocker.patch('udocker.cli.MSG.info')

    status = ucli._list_tags(expression)

    assert status == expected_status
    if not raises_exception:
        assert mock_get_tags.call_count == 1
        assert mock_msg.call_count == len(tags)
        for tag in tags:
            mock_msg.assert_any_call(tag)
    else:
        mock_get_tags.assert_called_once_with(expression)
        mock_msg.assert_not_called()


@pytest.mark.parametrize("argv, mock_values, expected_status", [
    (["udocker", "-h"], (None, None, None, None, None, None, None), 1),
    (["udocker", "search", "--list-tags", "ipyrad"],
     (None, ("d1", "d2", "ipyrad", "d3"), None, "v2token1", None, ["t1", "t2"], None), ["t1", "t2"]),
    (["udocker", "search", "ipyrad"], (None, ("d1", "d2", "ipyrad", "d3"), None, "v2token1", None, None, 0), 0),
])
def test_14_do_search(mocker, ucli, cmdparse, argv, mock_values, expected_status):
    """Test14 UdockerCLI().do_search()."""
    cmdp = CmdParser()
    cmdp.parse(argv)
    mock_setrepo, mock_split, mock_doiasearch, mock_ksget, mock_doiasetv2, mock_listtags, mock_searchrepo = mock_values
    mocker.patch.object(ucli, '_set_repository', return_value=mock_setrepo)
    mocker.patch.object(ucli, '_split_imagespec', return_value=mock_split)
    mocker.patch.object(ucli.dockerioapi, 'search_get_page', return_value=mock_doiasearch)
    mocker.patch.object(ucli.keystore, 'get', return_value=mock_ksget)
    mocker.patch.object(ucli.dockerioapi.v2api, 'set_login_token', return_value=mock_doiasetv2)

    mocker.patch.object(ucli, '_list_tags', return_value=mock_listtags)
    mocker.patch.object(ucli, '_search_repositories', return_value=mock_searchrepo)

    status = ucli.do_search(cmdp)
    assert status == expected_status


@pytest.mark.parametrize("cmdp_options, check_imagerepo, load, missing_options, expected_status, error_msg", [
    ({}, None, None, True, 1, None),  # missing command-line parameters
    ({'-': 'stdin', 'P1': "-", '-i': 'ipyrad'}, True, ['docker-repo1'], False, 0, None),
    ({'--input=': "ipyrad", 'P1': "invalidrepo"}, False, None, False, 1, None),
    ({'--input=': "ipyrad", 'P1': "ipyimg"}, True, None, False, 1, "load failed"),  # load failure
    ({'--input=': "ipyrad", 'P1': "ipyimg"}, True, ['docker-repo1', 'docker-repo2'], False, 0, None),  # successful load
    ({'--input=': "-", 'P1': "ipyimg"}, True, ['docker-repo1'], False, 0, None),  # read from stdin
    # ({'--input=': None, 'P1': "-"}, True, None, False, 1, "must specify filename of docker exported image"), # FIXME: this scenario is impossible to work, i can't figure a scenario were LOG.error("must specify filename of docker exported image") is called, also not sure reaching the end with imagerepofile as '-' makes sense
])
def test_15_do_load(mocker, ucli, cmdparse, cmdp_options, check_imagerepo, load, missing_options, expected_status,
                    error_msg):
    """ Test15 UdockerCLI().do_load(). """
    cmdparse.get.side_effect = lambda x: cmdp_options.get(x, None)
    cmdparse.missing_options.return_value = missing_options

    mocker.patch.object(ucli, '_check_imagerepo', return_value=check_imagerepo)
    mocker.patch.object(ucli.localfileapi, 'load', return_value=load)
    error_log_mock = mocker.patch.object(LOG, 'error')
    info_log_mock = mocker.patch.object(LOG, 'info')

    status = ucli.do_load(cmdparse)

    assert status == expected_status
    if error_msg:
        error_log_mock.assert_called_with(error_msg)
    if load:
        for repo in load:
            info_log_mock.assert_any_call(repo)


@pytest.mark.parametrize("cmdp_opts, missing_opts, file_exists, save, check_img, exp_status, err_msg, imgspec_list", [
    ({}, True, None, None, (None, None), 1, None, None),
    ({'-o=': "ipyrad.tar", 'P*': ["repo:latest"]}, False, False, True, ("ipyimg", "latest"), 0, None, ["repo:latest"]),
    ({'-o=': "ipyrad.tar", 'P*': ["ipyimg:latest"]}, False, True, True, ("ipyimg", "latest"), 1,
     "output file already exists: %s", ["ipyimg:latest"]),
    ({'--output=': None, '-': True, 'P*': ["-", "ipyimg:latest"]}, False, False, True, ("ipyimg", "latest"), 0, None,
     ['ipyimg:latest']),
    ({'-o=': "ipyimg.tar", 'P*': ["ipyimg:latest"]}, False, False, False, ("ipyimg", "latest"), 1, None,
     ['ipyimg:latest']),
    ({'-o=': "image.tar", 'P*': ["invalid/repo"]}, False, False, True, (None, None), 1, None,
     ["invalid/repo"]),
    # ({'--output=': None, 'P*': ["repo:tag"]}, False, False, True, ("repo", "tag"), 1, "must specify filename of image file for output", ["repo:tag"]),
])
def test_16_do_save(mocker, ucli, cmdparse, cmdp_opts, missing_opts, file_exists, save, check_img, exp_status, err_msg,
                    imgspec_list):
    """ Test16 UdockerCLI().do_save(). """
    cmdparse.get.side_effect = lambda x: cmdp_opts.get(x, None)
    cmdparse.missing_options.return_value = missing_opts

    mocker.patch.object(ucli, '_check_imagespec', return_value=check_img)
    mocker.patch.object(os.path, 'exists', return_value=file_exists)
    mocker.patch.object(ucli.localfileapi, 'save', return_value=save)
    error_log_mock = mocker.patch.object(LOG, 'error')

    if cmdparse.get('-'):
        if imgspec_list and imgspec_list[0] == '-':
            imgspec_list.pop(0)

    status = ucli.do_save(cmdparse)

    assert status == exp_status
    if err_msg:
        error_log_mock.assert_called_with(err_msg, 'ipyrad.tar')
    assert cmdparse.get("P*") == imgspec_list


@pytest.mark.parametrize("cmd_opts, missing_opts, check_imagespec_return, import_result, expected_status, error_msg", [
    ({}, True, None, None, 1, None),  # missing options
    ({'P1': 'ipyrad.tar', 'P2': 'invalid_spec'}, False, (None, None), None, 1, None),  # invalid image spec
    ({'P1': 'ipyrad.tar', 'P2': 'repo/ipyrad:latest'}, False, ("ipyrad", "latest"), False, 1, "importing"),
    # import failed
    ({'P1': 'ipyrad.tar', 'P2': 'repo/ipyrad:latest'}, False, ("ipyrad", "latest"), True, 0, None),  # import success
    ({'--tocontainer': True, 'P1': 'ipyrad.tar', 'P2': 'repo/ipyrad:latest'}, False, ("ipyrad", "latest"), False, 1,
     "importing"),  # import to container failed
    ({'--tocontainer': True, 'P1': 'ipyrad.tar', 'P2': 'repo/ipyrad:latest'}, False, ("ipyrad", "latest"),
     "container_id", 0, None),  # import to container success
    (
            {'--clone': True, 'P1': 'ipyrad.tar', 'P2': 'ipyrad/ipyrad:latest'}, False, ("ipyrad", "latest"),
            "container_id", 0,
            None),  # import clone success
    ({'--clone': True, 'P1': 'ipyrad.tar', 'P2': 'repo/ipyrad:latest'}, False, None, False, 1, "importing"),
    # import clone failed
    # ({'P1': '', 'P2': 'repo/ipyrad:latest'}, True, None, None, 1, "must specify tar filename"),
])
def test_17_do_import(mocker, cmdparse, ucli, cmd_opts, missing_opts, check_imagespec_return, import_result,
                      expected_status,
                      error_msg):
    """ Test17 UdockerCLI().do_import(). """
    cmdparse.get.side_effect = lambda x: cmd_opts.get(x, None)
    cmdparse.missing_options.return_value = missing_opts

    mocker.patch.object(ucli, '_check_imagespec', return_value=check_imagespec_return)
    mocker.patch.object(ucli.localfileapi, 'import_toimage', return_value=import_result)
    mocker.patch.object(ucli.localfileapi, 'import_tocontainer', return_value=import_result)
    mocker.patch.object(ucli.localfileapi, 'import_clone', return_value=import_result)
    log_mock = mocker.patch.object(LOG, 'info')
    error_log_mock = mocker.patch.object(LOG, 'error')

    status = ucli.do_import(cmdparse)

    assert status == expected_status
    if error_msg:
        error_log_mock.assert_called_with(error_msg)
    elif status == UdockerCLI.STATUS_OK and (cmd_opts.get('--tocontainer') or cmd_opts.get('--clone')):
        log_mock.assert_called_with("container ID: %s", import_result)


@pytest.mark.parametrize("cmdp_opts, missing_opts, container_id, export_result, expected_status, err_msg", [
    ({'-o': True, 'P1': "ipyrad.tar", 'P2': "ipyrad:latest", '--clone': False}, False, "cont123", True, 0, None),
    ({'-o': True, 'P1': "ipyrad.tar", 'P2': "invalid", '--clone': False}, False, "", True, 1,
     "invalid container id: %s"),
    ({'-o': True, 'P1': "ipyrad.tar", 'P2': ""}, True, "cont123", True, 1, None),
    ({'-o': True, 'P1': "ipyrad.tar", 'P2': "invalid"}, False, "", True, 1, "invalid container id: %s"),
    ({'-o': True, 'P1': "ipyrad.tar", 'P2': "ipyrad:latest"}, False, "cont123", False, 1, "exporting"),
    ({'-o': True, 'P1': "ipyrad.tar", 'P2': "ipyrad:latest", '--clone': True}, False, "cont123", True, 0, None),
])
def test_18_do_export(mocker, ucli, cmdparse, cmdp_opts, missing_opts, container_id, export_result, expected_status,
                      err_msg):
    """ Test18 UdockerCLI().do_export(). """
    cmdparse.get.side_effect = lambda x: cmdp_opts.get(x, None)
    cmdparse.missing_options.return_value = missing_opts

    mocker.patch.object(ucli.localrepo, 'get_container_id', return_value=container_id)
    log_error = mocker.patch.object(LOG, 'error')
    log_mock = mocker.patch.object(LOG, 'info')

    cstruct_mock = mocker.Mock()
    mocker.patch('udocker.cli.ContainerStructure', return_value=cstruct_mock)

    cstruct_mock.clone_tofile.return_value = export_result
    cstruct_mock.export_tofile.return_value = export_result

    status = ucli.do_export(cmdparse)

    assert status == expected_status
    if err_msg and not err_msg == 'exporting':
        log_error.assert_called_with(err_msg, '' if not container_id else container_id)  # FIXME: tmp fix
    elif err_msg and not missing_opts:
        log_mock.assert_called_with("exporting to file: %s", cmdp_opts['P1'])
    elif err_msg:
        log_error.assert_called_with(err_msg)

    # cstruct_class_mock.assert_called_with(ucli.localrepo, container_id) # FIXME: this need changes in the code
    if not missing_opts:
        if cmdp_opts.get('--clone') and expected_status == UdockerCLI.STATUS_OK:
            cstruct_mock.clone_tofile.assert_called_with(cmdp_opts['P1'])
        elif expected_status == UdockerCLI.STATUS_OK:
            cstruct_mock.export_tofile.assert_called_with(cmdp_opts['P1'])


@pytest.mark.parametrize("cmdp_options, missing_opts, get_container_id, clone, expected_status, err_msg", [
    ({}, True, None, None, 1, None),
    ({'P1': 'invalid_id'}, False, "", None, 1, "invalid container id: %s"),
    ({'--name=': 'new_name', 'P1': 'cont123'}, False, 'cont123', None, 1, "container name already exists"),
    ({'P1': 'valid_id'}, False, 'valid_id', None, 1, "cloning"),
    ({'P1': 'valid_id'}, False, 'valid_id', 'clone_id', 0, None),
    ({'--name=': 'new_name', 'P1': 'valid_id'}, False, "", 'clone_id', 1, "invalid container id: %s"),
])
def test_19_do_clone(mocker, ucli, cmdparse, cmdp_options, missing_opts, get_container_id, clone, expected_status,
                     err_msg):
    """ Test19 UdockerCLI().do_clone(). """
    cmdparse.get.side_effect = lambda x: cmdp_options.get(x, None)
    cmdparse.missing_options.return_value = missing_opts

    mocker.patch.object(ucli.localrepo, 'get_container_id', return_value=get_container_id)
    mocker.patch.object(ucli.localfileapi, 'clone_container', return_value=clone)
    log_mock = mocker.patch.object(LOG, 'info')
    error_log_mock = mocker.patch.object(LOG, 'error')

    status = ucli.do_clone(cmdparse)

    assert status == expected_status
    if err_msg and not get_container_id:
        error_log_mock.assert_called_with(err_msg, mocker.ANY)
    elif err_msg and cmdparse.get('--name=') and get_container_id:
        error_log_mock.assert_called_with(err_msg)
    elif status == UdockerCLI.STATUS_OK:
        log_mock.assert_called_with("clone ID: %s", clone)


@pytest.mark.parametrize("cmdp_opts, missing_opts, input, getpass, token, keystore, exp_status, err_msg", [
    ({}, True, None, None, None, None, 1, None),
    ({'--username=': 'u1', '--password=': 'xx', "--registry=": 'https://registry-1.docker.io'}, False, None, None,
     "zx1", 0, 0, None),
    ({'--username=': 'u1', '--password=': 'XX'}, False, None, None, "zx1", 0, 0, None),
    ({'--username=': 'u1', '--password=': 'xx'}, False, None, None, "zx1", 1, 1, "invalid credentials"),
    ({}, False, "u1", "xx", "zx1", 0, 0, None),
])
def test_20_do_login(mocker, ucli, cmdparse, cmdp_opts, missing_opts, input, getpass, token, keystore, exp_status,
                     err_msg):
    """ Test20 UdockerCLI().do_login(). """
    cmdparse.get.side_effect = lambda x: cmdp_opts.get(x, None)
    cmdparse.missing_options.return_value = missing_opts

    mocker.patch.object(ucli, '_set_repository', return_value=cmdp_opts.get("--registry="))
    mocker.patch.object(ucli.dockerioapi.v2api, 'get_login_token', return_value=token)
    mocker.patch.object(ucli.keystore, 'put', return_value=keystore)
    mocker.patch('udocker.cli.GET_INPUT', return_value=input)
    mocker.patch('udocker.cli.getpass', return_value=getpass)
    mock_log_error = mocker.patch.object(LOG, 'error')
    mock_log_warning = mocker.patch.object(LOG, 'warning')

    status = ucli.do_login(cmdparse)

    assert status == exp_status
    assert cmdparse.get.call_count == 3

    password = cmdp_opts.get("--password=")
    if password and password == password.upper():
        mock_log_warning.assert_called_with("password in uppercase. Caps Lock ?")

    if not missing_opts and cmdp_opts.get("--registry="):
        assert ucli._set_repository.return_value == "https://registry-1.docker.io"
    else:
        assert ucli._set_repository.return_value == None

    if err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize("cmdp_opts, missing_opts, all_credentials, erase_status, delete_status, exp_status, err_msg", [
    ({}, True, None, None, None, 1, None),  # Missing options
    ({'--registry=': 'https://registry-1.docker.io'}, False, False, None, 0, 0, None),
    # Successful logout from specified registry
    ({'-a': True}, False, True, 0, None, 0, None),  # Successful logout from all credentials
    ({'--registry=': 'https://registry-1.docker.io'}, False, False, None, 1, 1, "deleting credentials"),
    # Delete error on specific registry
    ({'-a': True}, False, True, 1, None, 1, "deleting credentials"),  # Erase error on all credentials
])
def test_21_do_logout(mocker, ucli, cmdparse, cmdp_opts, missing_opts, all_credentials, erase_status, delete_status,
                      exp_status, err_msg):
    """ Test21 UdockerCLI().do_logout(). """
    cmdparse.get.side_effect = lambda x: cmdp_opts.get(x, None)
    cmdparse.missing_options.return_value = missing_opts

    mocker.patch.object(ucli, '_set_repository', return_value=None)
    mocker.patch.object(ucli.keystore, 'erase', return_value=erase_status)
    mocker.patch.object(ucli.keystore, 'delete', return_value=delete_status)
    mock_log_error = mocker.patch.object(LOG, 'error')

    status = ucli.do_logout(cmdparse)

    assert status == exp_status
    if all_credentials:
        ucli.keystore.erase.assert_called()
    elif missing_opts:
        ucli.keystore.erase.assert_not_called()
    else:
        ucli.keystore.delete.assert_called_with(ucli.dockerioapi.registry_url)

    if err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize("cmdp_opts, image_spec, missing_opts, pull_success, exp_status, err_msg", [
    ({}, (None, None), True, None, 1, None),  # Missing options
    ({'--registry=': 'https://registry-1.docker.io', 'P1': 'ipyrad:latest'}, ('ipyrad', 'latest'), False, True, 0,
     None),  # Successful pull
    ({'--registry=': 'https://registry-1.docker.io', 'P1': 'ipyrad:latest'}, ('ipyrad', 'latest'), False, False, 1,
     "no files downloaded"),  # Pull failure
    ({'--httpproxy=': 'socks5://host:port', 'P1': 'ipyrad:latest'}, ('ipyrad', 'latest'), False, True, 0, None),
])
def test_22_do_pull(mocker, ucli, cmdparse, cmdp_opts, image_spec, missing_opts, pull_success, exp_status, err_msg):
    """ Test22 UdockerCLI().do_pull(). """
    cmdparse.get.side_effect = lambda x: cmdp_opts.get(x, None)
    cmdparse.missing_options.return_value = missing_opts

    mocker.patch.object(ucli, '_check_imagespec', return_value=image_spec)
    mocker.patch.object(ucli, '_set_repository', return_value=None)
    mocker.patch.object(ucli.dockerioapi, 'get', return_value=pull_success)
    mock_log_error = mocker.patch.object(LOG, 'error')

    status = ucli.do_pull(cmdparse)

    assert status == exp_status
    if not pull_success and not missing_opts:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize("imagespec, is_repo_name, check_imagespec, create_fromimage, expected", [
    ("valid/repo:tag", True, ("valid/repo", "tag"), True, True),
    ("invalid/repo", False, (None, None), False, False),
    ("no_tag", True, (None, None), False, False),
])
def test_23__create(mocker, ucli, imagespec, is_repo_name, check_imagespec, create_fromimage, expected):
    """ Test23 UdockerCLI()._create method in UdockerCLI. """
    mocker.patch.object(ucli.dockerioapi, 'is_repo_name', return_value=is_repo_name)
    mocker.patch.object(ucli, '_check_imagespec', return_value=check_imagespec)
    mock_container_struct = mocker.patch('udocker.cli.ContainerStructure')
    mock_container_struct.return_value.create_fromimage.return_value = create_fromimage
    mocker.patch.object(ucli.localrepo, 'get_image_attributes', return_value=("valid", "layer_id"))
    mock_log_error = mocker.patch.object(LOG, 'error')

    result = ucli._create(imagespec)

    assert result == expected
    if not is_repo_name:
        mock_log_error.assert_called_with("must specify image:tag or repository/image:tag")


@pytest.mark.parametrize("cmdp_opts, missing_opts, name_exists, force, create_result, exp_status, err_msg", [
    ({'P1': 'valid/repo:tag', '--name=': 'container1'}, False, False, False, '12345', 0, None),  # Successful creation
    (
            {'P1': 'valid/repo:tag', '--name=': 'existing_name'}, False, True, False, None, 1,
            "container name already exists"),
    # Name conflict without force
    ({'P1': 'valid/repo:tag', '--name=': 'existing_name', '--force': True}, False, True, True, '12345', 0, None),
    # Name conflict with force
    ({'P1': 'valid/repo:tag'}, False, False, False, None, 1, None),  # Creation failure
    ({}, True, False, False, None, 1, None),  # Missing options
])
def test_24_do_create(mocker, ucli, cmdparse, cmdp_opts, missing_opts, name_exists, force, create_result, exp_status,
                      err_msg):
    """ Test24 UdockerCLI().do_create(). """
    cmdparse.get.side_effect = lambda x: cmdp_opts.get(x, None)
    cmdparse.missing_options.return_value = missing_opts
    mocker.patch.object(ucli.localrepo, 'get_container_id', return_value=name_exists)
    mocker.patch.object(ucli, '_create', return_value=create_result)
    mock_log_error = mocker.patch.object(LOG, 'error')
    mock_log_info = mocker.patch.object(LOG, 'info')
    mock_msg_info = mocker.patch.object(MSG, 'info')

    status = ucli.do_create(cmdparse)

    assert status == exp_status
    if err_msg:
        mock_log_error.assert_called_with(err_msg)
    if create_result:
        mock_log_info.assert_called_with("container ID: %s", create_result)
        mock_msg_info.assert_called_with("ContainerID=%s", create_result)


@pytest.mark.parametrize("exec, cmdp_input, expected_output", [
    (False, {}, {"vol": [], "env": [], "cwd": None}),
    (True, {"-v": ["/path/to/volume"], "-e": ["VAR=value"], "-w": "/workdir"},
     {"vol": ["/path/to/volume"], "env": ["VAR=value"], "cwd": "/workdir"}),
    (True, {"--volume": ["/path/to/volume"], "--env": ["VAR=value"], "--workdir": "/workdir"},
     {"vol": ["/path/to/volume"], "env": ["VAR=value"], "cwd": "/workdir"}),
])
def test_25_get_run_options(mocker, ucli, cmdparse, exec, cmdp_input, expected_output):
    """ Test25 UdockerCLI()._get_run_options(). """
    extendable_opts_extend = ['-p', '--publish', '-v', '--volume', '-e', '--env', '--env-file', '--device']
    extendable_opts_replace = ['--workdir']

    def get_side_effect(arg, *args):
        arg_normalized = arg.rstrip('=')
        if arg_normalized in cmdp_input:
            return cmdp_input[arg_normalized]
        else:
            if arg_normalized in extendable_opts_extend:
                return []
            elif arg_normalized in extendable_opts_replace:
                return None
            return None

    cmdparse.get.side_effect = get_side_effect

    mock_exec = mocker.Mock()
    mock_exec.opt = {
        'portsmap': [],
        'vol': [],
        'env': [],
        'devices': [],
        'envfile': [],
        'cwd': None,
    }

    ucli._get_run_options(cmdparse, mock_exec if exec else None)
    for key, value in expected_output.items():
        assert mock_exec.opt[key] == value


@pytest.mark.parametrize("params", [
    {"cmdp_opts": {'P1': 'image:tag', '--pull': 'never'}, "config": {'location': '/.udocker'}, "missing_opts": False,
     "location_set": None, "image": 'image:tag', "pull_opt": 'never', "container": False, "expected_status": 1,
     "exec_engine": True, "err_msg": "image or container not available"},

    {"cmdp_opts": {'P1': None, '--pull': 'never'}, "config": {'location': '/.udocker'}, "missing_opts": False,
     "location_set": None, "image": 'image:tag', "pull_opt": 'never', "container": False, "expected_status": 1,
     "exec_engine": True, "err_msg": "must specify container_id or image:tag"},

    {"cmdp_opts": {'P1': 'container2', '--rm': False}, "config": None, "missing_opts": False, "location_set": None,
     "image": 'container2', "pull_opt": None, "container": True, "expected_status": 0, "exec_engine": True,
     "err_msg": None},

    {"cmdp_opts": {'P1': 'existing_container'}, "config": None, "missing_opts": False, "location_set": None,
     "image": 'existing_container', "pull_opt": None, "container": True, "expected_status": 0, "exec_engine": True,
     "err_msg": None},

    {"cmdp_opts": {'P1': 'new_image:tag', '--pull': 'always'}, "config": None, "missing_opts": False,
     "location_set": None, "image": 'new_image:tag', "pull_opt": 'always', "container": True, "expected_status": 0,
     "exec_engine": True, "err_msg": None},

    {"cmdp_opts": {'P1': 'new_image:tag', '--pull': 'always'}, "config": None, "missing_opts": False,
     "location_set": None, "image": 'new_image:tag', "pull_opt": 'always', "container": True, "expected_status": 1,
     "exec_engine": False, "err_msg": "no execution engine for this execmode"},

    {"cmdp_opts": {'P1': 'existing_image:tag', '--pull': 'always'}, "config": None, "missing_opts": False,
     "location_set": None, "image": 'existing_image:tag', "pull_opt": 'always', "container": True, "expected_status": 0,
     "exec_engine": True, "err_msg": None},

    {"cmdp_opts": {}, "config": None, "missing_opts": True, "location_set": None, "image": None, "pull_opt": None,
     "container": False, "expected_status": 1, "exec_engine": True, "err_msg": None},

    {"cmdp_opts": {'P1': 'container1', '--rm': True}, "config": None, "missing_opts": False, "location_set": None,
     "image": 'container1', "pull_opt": None, "container": True, "expected_status": 0, "exec_engine": True,
     "err_msg": None},

    {"cmdp_opts": {'P1': 'container1', '--name=': 'invalid name', '--pull=': 'never'},
     "config": {'location': '/.udocker'}, "missing_opts": False, "location_set": None, "image": 'container1',
     "pull_opt": None, "container": True, "expected_status": 1, "exec_engine": True,
     "err_msg": "invalid container name format"},

    {"cmdp_opts": {'P1': 'container2', '--rm': True}, "config": None, "missing_opts": False, "location_set": None,
     "image": 'container2', "pull_opt": None, "container": True, "expected_status": 0, "exec_engine": True,
     "err_msg": None},
])
def test_26_do_run(mocker, ucli, cmdparse, config, params):
    """ Test26 UdockerCLI().do_run(). """
    cmdparse.get.side_effect = lambda x: params['cmdp_opts'].get(x)
    cmdparse.missing_options.return_value = params['missing_opts']

    config.conf = params['config'] if params['config'] else {}
    mocker.patch.object(ucli.localrepo, 'get_container_id', return_value=params['container'])
    mocker.patch.object(ucli.localrepo, 'set_container_name', return_value=False)
    mocker.patch.object(ucli.localrepo, 'isprotected_container', return_value=False)
    mocker.patch.object(ucli, '_create', return_value=params['container'])
    mocker.patch.object(ucli, '_get_run_options')
    mocker.patch.object(ucli, 'do_pull')
    mocker.patch.object(ucli.localrepo, 'del_container')
    mock_log_error = mocker.patch.object(LOG, 'error')

    mock_exec_mode = mocker.patch('udocker.cli.ExecutionMode')
    if params['exec_engine']:
        mock_engine = mocker.Mock()
        mock_exec_mode.return_value.get_engine.return_value = mock_engine
        mock_engine.run.return_value = params['expected_status']
    else:
        mock_exec_mode.return_value.get_engine.return_value = None

    status = ucli.do_run(cmdparse)

    assert status == params['expected_status']
    if params['err_msg']:
        mock_log_error.assert_called_with(params['err_msg'])


@pytest.mark.parametrize("missing_opts, cmdp_opts, images_list, layers_list, expected_status", [
    (True, {}, [], [], 1),
    (False, {}, [], [], 0),
    (False, {}, [('repo1', 'tag1'), ('repo2', 'tag2')], [], 0),
    (False, {'-l': True}, [('repo1', 'tag1')], [('layer1', 2048)], 0),
    # (False, {'-l': True}, [('repo1', 'tag1')], [('layer1', 512)], 0), # FIXME: need to be casted to int file_size
])
def test_27_do_images(mocker, ucli, cmdparse, missing_opts, cmdp_opts, images_list, layers_list, expected_status):
    """ Test27 UdockerCLI().do_images(). """
    cmdparse.get.side_effect = lambda x: cmdp_opts.get(x)
    cmdparse.missing_options.return_value = missing_opts
    mocker.patch.object(ucli.localrepo, 'get_imagerepos', return_value=images_list)
    mocker.patch.object(ucli.localrepo, 'isprotected_imagerepo', return_value=False)
    mocker.patch.object(ucli.localrepo, 'cd_imagerepo', return_value="image_dir")
    mocker.patch.object(ucli.localrepo, 'get_layers', return_value=layers_list)

    status = ucli.do_images(cmdparse)

    assert status == expected_status


@pytest.mark.parametrize("missing_opts, cmdp_opts, containers_list, exec_mode, expected_status", [
    (True, {}, [], '', 1),
    (False, {}, [], '', 0),
    (False, {}, [('container1', 'repo:tag1', '123456')], 'R1', 0),
    (False, {'-m': True}, [('container1', 'repo:tag1', '123456')], 'R1', 0),
    (False, {'-s': True}, [('container1', 'repo:tag1', '123456')], 'R1', 0),
    (False, {'-m': True, '-s': True}, [('container1', 'repo:tag1', '123456')], 'R1', 0),
])
def test_28_do_ps(mocker, ucli, cmdparse, missing_opts, cmdp_opts, containers_list, exec_mode, expected_status):
    """ Test28 UdockerCLI().do_ps(). """
    cmdparse.get.side_effect = lambda x: cmdp_opts.get(x)
    cmdparse.missing_options.return_value = missing_opts
    mocker.patch.object(ucli.localrepo, 'get_containers_list', return_value=containers_list)
    mock_exec_mode = mocker.patch('udocker.engine.execmode.ExecutionMode')
    mock_exec_mode.return_value.get_mode.return_value = exec_mode
    mocker.patch.object(ucli.localrepo, 'isprotected_container', return_value=True)
    mocker.patch.object(ucli.localrepo, 'iswriteable_container', return_value=True)
    mocker.patch.object(ucli.localrepo, 'get_size', return_value='100MB')

    status = ucli.do_ps(cmdparse)

    assert status == expected_status


@pytest.mark.parametrize(
    "missing_opts, cmdp_opts, container_ids, is_protected, delete_success, expected_status, err_msg", [
        (False, {'-f': True, 'P*': ['container1']}, ['container1'], False, True, 0, None),
        (False, {'-f': True, 'P*': ['container1']}, ['container1'], False, False, 1, "deleting container"),
        (False, {'P*': ['container1', 'container2']}, ['container1', 'container2'], False, True, 0, None),
        (False, {'P*': ['invalid_id']}, [None], False, False, 1, "invalid container id: %s"),
        (False, {'P*': ['protected_container']}, ['protected_container'], True, False, 1, "container is protected"),
        (False, {'P*': []}, None, True, False, 1, "must specify image:tag or repository/image:tag"),
        (True, {}, ['protected_container'], False, False, 1, None),
    ])
def test_29_do_rm(mocker, ucli, cmdparse, missing_opts, cmdp_opts, container_ids, is_protected, delete_success,
                  expected_status, err_msg):
    """ Test29 UdockerCLI().do_rm(). """
    cmdparse.get.side_effect = lambda x: cmdp_opts.get(x)
    cmdparse.missing_options.return_value = missing_opts
    mocker.patch.object(ucli.localrepo, 'get_container_id',
                        side_effect=lambda x: container_ids.pop(0) if container_ids else None)
    mocker.patch.object(ucli.localrepo, 'isprotected_container', return_value=is_protected)
    mocker.patch.object(ucli.localrepo, 'del_container', return_value=delete_success)
    mock_log_error = mocker.patch.object(LOG, 'error')
    status = ucli.do_rm(cmdparse)
    assert status == expected_status
    if err_msg and "%s" in err_msg:
        mock_log_error.assert_called_with(err_msg, mocker.ANY)
    elif err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize(
    "missing_opts, src_spec, targ_spec, ck_imagespec, cd_imagerepo, src_protected, tag_success, exp_status, err_msg", [
        (True, "repo1:tag1", "repo2:tag2", ("repo2", "tag2"), [False, False], False, False, 1, None),
        (False, "repo1:tag1", "repo2:tag2", ("repo2", "tag2"), [False, True], False, True, 0, None),
        (False, "repo1:tag1", "invalid/tag", (None, None), [False, True], False, True, 1, "target name is invalid"),
        (False, "repo1:tag1", "repo2:tag2", ("repo2", "tag2"), [True, True], False, True, 1, "target already exists"),
        (False, "repo1:tag1", "repo2:tag2", ("repo2", "tag2"), [False, False], False, True, 1, "source does not exist"),
        (False, "repo1:tag1", "repo2:tag2", ("repo2", "tag2"), [False, True], True, True, 1,
         "source repository is protected"),
        (False, "repo1:tag1", "repo2:tag2", ("repo2", "tag2"), [False, True], False, False, 1,
         "creation of new image tag failed"),
    ])
def test_30_do_tag(mocker, ucli, cmdparse, missing_opts, src_spec, targ_spec, ck_imagespec, cd_imagerepo, src_protected,
                   tag_success, exp_status, err_msg):
    """ Test30 UdockerCLI().do_tag(). """
    cmdparse.get.side_effect = lambda x: {'P1': src_spec, 'P2': targ_spec}.get(x)
    cmdparse.missing_options.return_value = missing_opts
    mocker.patch.object(ucli.localrepo, 'cd_imagerepo', side_effect=cd_imagerepo)
    mocker.patch.object(ucli.localrepo, 'isprotected_imagerepo', return_value=src_protected)
    mocker.patch.object(ucli.localrepo, 'tag', return_value=tag_success)
    mocker.patch.object(ucli, '_check_imagespec', return_value=ck_imagespec)
    mock_log_error = mocker.patch.object(LOG, 'error')

    status = ucli.do_tag(cmdparse)

    assert status == exp_status
    if err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize(
    "missing_opts, force, imagespec, imagerepo_exists, is_protected, delete_success, expected_status, err_msg", [
        (True, False, "repo:tag", True, False, True, 1, None),
        (False, False, "repo:tag", True, False, True, 0, None),
        (False, True, "repo:tag", True, False, True, 0, None),
        (False, False, "repo:tag", True, True, True, 1, "image repository is protected"),
        (False, False, "invalid/tag", False, False, False, 1, None),
        (False, False, "repo:tag", True, False, False, 1, "deleting image"),
    ])
def test_31_do_rmi(mocker, ucli, cmdparse, missing_opts, force, imagespec, imagerepo_exists, is_protected,
                   delete_success, expected_status, err_msg):
    """ Test31 UdockerCLI().do_rmi(). """
    cmdparse.get.side_effect = lambda x: {'-f': force, 'P1': imagespec}.get(x)
    cmdparse.missing_options.return_value = missing_opts
    mocker.patch.object(ucli, '_check_imagespec',
                        return_value=tuple(imagespec.split(':')) if imagerepo_exists else (None, None))
    mocker.patch.object(ucli.localrepo, 'isprotected_imagerepo', return_value=is_protected)
    mocker.patch.object(ucli.localrepo, 'del_imagerepo', return_value=delete_success)
    mock_log_error = mocker.patch.object(LOG, 'error')

    status = ucli.do_rmi(cmdparse)

    assert status == expected_status
    if err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize(
    "arg, container_id, protect_container, imagerepo, tag, protect_imagerepo, expected_status, err_msg", [
        ("", "", True, None, None, None, 1, None),
        ("container1", "container1", True, None, None, None, 0, None),
        ("ipyrad:latest", None, None, "ipyrad", "latest", True, 0, None),
        ("invalid_container", None, None, None, None, None, 1, "protect image failed"),
        ("container1", "container1", False, None, None, None, 1, "protect container failed"),
        ("ipyrad:latest", None, None, "ipyrad", "latest", False, 1, "protect image failed"),
    ])
def test_32_do_protect(mocker, ucli, cmdparse, arg, container_id, protect_container, imagerepo, tag, protect_imagerepo,
                       expected_status, err_msg):
    """ Test32 UdockerCLI().do_protect(). """
    cmdparse.get.side_effect = lambda x: {'P1': arg}.get(x)
    cmdparse.missing_options.return_value = True if not arg else False
    mocker.patch.object(ucli.localrepo, 'get_container_id', return_value=container_id)
    mocker.patch.object(ucli.localrepo, 'protect_container', return_value=protect_container)
    mocker.patch.object(ucli.localrepo, 'protect_imagerepo', return_value=protect_imagerepo)
    mocker.patch.object(ucli, '_check_imagespec', return_value=(imagerepo, tag))
    mock_log_error = mocker.patch.object(LOG, 'error')

    status = ucli.do_protect(cmdparse)

    assert status == expected_status
    if err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize(
    "arg, container_id, unprotect_container, imagerepo, tag, unprotect_imagerepo, expected_status, err_msg", [
        ("", "", False, None, None, None, 1, None),
        ("container1", "container1", True, None, None, None, 0, None),
        ("repo:tag", None, None, "repo", "tag", True, 0, None),
        ("invalid_container", None, None, None, None, None, 1, "unprotect image failed"),
        ("container1", "container1", False, None, None, None, 1, "unprotect container failed"),
        ("repo:tag", None, None, "repo", "tag", False, 1, "unprotect image failed"),
    ])
def test_33_do_unprotect(mocker, ucli, cmdparse, arg, container_id, unprotect_container, imagerepo, tag,
                         unprotect_imagerepo, expected_status, err_msg):
    """ Test33 UdockerCLI().do_unprotect(). """
    cmdparse.get.side_effect = lambda x: {'P1': arg}.get(x)
    cmdparse.missing_options.return_value = True if not arg else False
    mocker.patch.object(ucli.localrepo, 'get_container_id', return_value=container_id)
    mocker.patch.object(ucli.localrepo, 'unprotect_container', return_value=unprotect_container)
    mocker.patch.object(ucli.localrepo, 'unprotect_imagerepo', return_value=unprotect_imagerepo)
    mocker.patch.object(ucli, '_check_imagespec', return_value=(imagerepo, tag))
    mock_log_error = mocker.patch.object(LOG, 'error')

    status = ucli.do_unprotect(cmdparse)

    assert status == expected_status
    if err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize("container_id, name, container_exists, set_name_success, expected_status, err_msg", [
    ("", "", False, False, 1, None),
    ("container1", "new_name", True, True, 0, None),
    ("invalid_container", "new_name", False, True, 1, "invalid container id or name"),
    ("container1", "", True, True, 1, "invalid container id or name"),
    ("container1", "new_name", True, False, 1, "invalid container name"),
])
def test_34_do_name(mocker, ucli, cmdparse, container_id, name, container_exists, set_name_success, expected_status,
                    err_msg):
    """ Test34 UdockerCLI().do_name(). """
    cmdparse.get.side_effect = lambda x: {'P1': container_id, 'P2': name}.get(x)
    cmdparse.missing_options.return_value = True if not container_id else False
    mocker.patch.object(ucli.localrepo, 'get_container_id', return_value=container_id if container_exists else None)
    mocker.patch.object(ucli.localrepo, 'set_container_name', return_value=set_name_success)
    mock_log_error = mocker.patch.object(LOG, 'error')

    status = ucli.do_name(cmdparse)

    assert status == expected_status
    if err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize("missing_opts, old_name, new_name, container, del_name, set_name, expected_status, err_msg", [
    (True, "", "", [False, False], False, False, 1, None),
    (False, "old_name", "new_name", [True, False], True, True, 0, None),
    (False, "nonexistent", "new_name", [False, False], True, True, 1, "container does not exist"),
    (False, "old_name", "existing_name", [True, True], True, True, 1, "new name already exists"),
    (False, "old_name", "new_name", [True, False], False, True, 1, "name does not exist"),
    (False, "old_name", "new_name", [True, False], True, False, 1, "setting new name"),
])
def test_35_do_rename(mocker, ucli, cmdparse, missing_opts, old_name, new_name, container, del_name, set_name,
                      expected_status, err_msg):
    """ Test35 UdockerCLI().do_rename(). """
    cmdparse.get.side_effect = lambda x: {'P1': old_name, 'P2': new_name}.get(x)
    cmdparse.missing_options.return_value = missing_opts
    mocker.patch.object(ucli.localrepo, 'get_container_id', side_effect=container)
    mocker.patch.object(ucli.localrepo, 'del_container_name', return_value=del_name)
    mocker.patch.object(ucli.localrepo, 'set_container_name', return_value=set_name)
    mock_log_error = mocker.patch.object(LOG, 'error')

    status = ucli.do_rename(cmdparse)

    assert status == expected_status
    if err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize("missing_opts, name, del_name, expected_status, err_msg", [
    (True, "", False, 1, None),
    (False, "container_name", True, 0, None),
    (False, "", False, 1, "invalid container id or name"),
    (False, "nonexistent_name", False, 1, "removing container name"),
])
def test_36_do_rmname(mocker, ucli, cmdparse, missing_opts, name, del_name, expected_status, err_msg):
    """ Test36 UdockerCLI().do_rmname(). """
    cmdparse.get.return_value = name
    cmdparse.missing_options.return_value = missing_opts
    mocker.patch.object(ucli.localrepo, 'del_container_name', return_value=del_name)
    mock_log_error = mocker.patch.object(LOG, 'error')

    status = ucli.do_rmname(cmdparse)

    assert status == expected_status
    if err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize(
    "subcommand, imagerepo_tag, http_proxy, manifest, manifest_json, expected_status, err_msg", [
        ("inspect", ("repo", "tag"), None, True, {"example": "manifest"}, 0, None),
        ("inspect", (None, None), None, True, {}, 1, None),
        ("inspect", ("repo", "tag"), "socks5://host:port", True, {"example": "manifest"}, 0, None),
        ("inspect", ("repo", "tag"), None, False, None, 1, None),
    ])
def test_37_do_manifest(mocker, ucli, cmdparse, subcommand, imagerepo_tag, http_proxy, manifest, manifest_json,
                        expected_status, err_msg):
    """ Test37 UdockerCLI().do_manifest(). """
    cmdparse.get.side_effect = lambda x: {"P1": subcommand, "P2": f"{imagerepo_tag[0]}:{imagerepo_tag[1]}",
                                          "--httpproxy=": http_proxy}.get(x, False)
    cmdparse.missing_options.return_value = False
    mocker.patch.object(ucli, '_check_imagespec', return_value=imagerepo_tag)
    mocker.patch.object(ucli, '_set_repository')
    mocker.patch.object(ucli.dockerioapi, 'get_manifest',
                        return_value=(None, manifest_json) if manifest else (None, None))
    mocker.patch.object(ucli.keystore, 'get')
    mocker.patch.object(ucli.dockerioapi.v2api, 'set_login_token')

    json_dumps = json.dumps(manifest_json, sort_keys=True, indent=4, separators=(',', ': '))

    mocker.patch.object(json, 'dumps',
                        side_effect=OSError if not manifest else lambda x, *args, **kwargs: json_dumps)

    mock_msg_info = mocker.patch.object(MSG, 'info')
    status = ucli.do_manifest(cmdparse)

    assert status == expected_status
    if manifest_json and manifest:
        mock_msg_info.assert_called_with(json.dumps(manifest_json, sort_keys=True, indent=4, separators=(',', ': ')))
    if err_msg:
        mock_msg_info.assert_called_with(err_msg)


@pytest.mark.parametrize(
    "cont_or_image, container_id, print_dir, container_dir, container_json, image, json_dumps, expected_status", [
        ("", "", False, None, None, False, None, 1),
        ("imagerepo:latest", "", False, None, True, False, None, 1),
        ("imagerepo:latest", "", False, None, True, True, None, 0),
        ("imagerepo:latest", "", False, None, True, True, OSError, 0),
        ("imagerepo:latest", "", False, None, None, True, None, 1),
        ("123", "123", True, "/ROOT/cont", True, True, None, 0),
    ])
def test_38_do_inspect(mocker, ucli, cmdparse, cont_or_image, container_id, print_dir, container_dir,
                       container_json, image, json_dumps, expected_status):
    """ Test38 UdockerCLI().do_inspect(). """

    cont_insp = {
        "architecture": "amd64",
        "config": {
            "AttachStderr": False,
            "AttachStdin": False,
            "AttachStdout": False,
            "Cmd": [
                "/bin/bash"
            ],
            "Domainname": "",
            "Entrypoint": None,
            "Env": [
                "PATH=/usr/local/sbin"
            ],
            "Hostname": "",
            "Image": "sha256:05725a",
            "Labels": {
                "org.opencontainers.image.vendor": "CentOS"
            },
            "WorkingDir": ""
        },
        "container": "c171c",
        "container_config": {
            "ArgsEscaped": True,
            "Cmd": ["/bin/sh", "-c"],
            "Domainname": "",
            "Env": [
                "PATH=/usr/local/sbin"
            ],
            "Hostname": "c171c5a1528a",
            "Image": "sha256:05725a",
            "Labels": {
                "org.label-schema.license": "GPLv2",
                "org.label-schema.name": "CentOS Base Image",
                "org.opencontainers.image.vendor": "CentOS"
            },
            "WorkingDir": ""
        },
        "created": "2020-05-05T21",
        "docker_version": "18.09.7",
        "id": "e72c1",
        "os": "linux",
        "parent": "61dc7"
    }

    cmdparse.get.side_effect = lambda x: {'P1': cont_or_image, '-p': print_dir}.get(x)
    cmdparse.missing_options.return_value = not cont_or_image
    mocker.patch.object(ucli.localrepo, 'get_container_id', return_value=container_id)

    ck_image = cont_or_image.split(':')[0], cont_or_image.split(':')[1] if ':' in cont_or_image else (None, None)
    mocker.patch.object(ucli, '_check_imagespec', return_value=ck_image)

    mocker.patch.object(ucli.localrepo, 'cd_imagerepo', return_value=cont_insp if image else None)
    mocker.patch.object(ucli.localrepo, 'get_image_attributes', return_value=(container_json, None))
    container_struct_mock = mocker.patch('udocker.cli.ContainerStructure')
    container_struct_mock.return_value.get_container_attr.return_value = (container_dir, container_json)
    mocker.patch.object(json, 'dumps', side_effect=json_dumps)
    mock_msg_info = mocker.patch.object(MSG, 'info')

    status = ucli.do_inspect(cmdparse)

    assert status == expected_status
    if expected_status == 0:
        if print_dir and container_dir:
            mock_msg_info.assert_called_with(f"{container_dir}/ROOT")
        elif container_json and not json_dumps:
            mock_msg_info.assert_called_with(
                json.dumps(container_json, sort_keys=True, indent=4, separators=(',', ': ')))


@pytest.mark.parametrize("imagespec, imagerepo_exists, verify_success, expected_status, err_msg", [
    ("repo:tag", True, True, 0, None),
    ("invalid/image:tag", False, True, 1, "selecting image and tag"),
    ("repo:tag", True, False, 1, "image verification failure"),
])
def test_39_do_verify(mocker, ucli, cmdparse, imagespec, imagerepo_exists, verify_success, expected_status, err_msg):
    """ Test39 UdockerCLI().do_verify(). """
    cmdparse.get.return_value = imagespec
    cmdparse.missing_options.return_value = not imagespec
    ck_image = tuple(imagespec.split(':')) if imagespec else (None, None)
    mocker.patch.object(ucli, '_check_imagespec', return_value=ck_image)
    mocker.patch.object(ucli.localrepo, 'cd_imagerepo', return_value=imagerepo_exists)
    mocker.patch.object(ucli.localrepo, 'verify_image', return_value=verify_success)
    mock_log_error = mocker.patch.object(LOG, 'error')

    status = ucli.do_verify(cmdparse)

    assert status == expected_status
    if err_msg:
        mock_log_error.assert_called_with(err_msg)


@pytest.mark.parametrize("params_setup", [
    # "container_id, xmode, force, nvidia, purge, fixperm, container, protected, exec_mode_set, expected_status, msgs",
    {"container_id": "", "xmode": "", "force": False, "nvidia": False, "purge": False, "fixperm": False,
     "container": False, "protected": False, "exec_mode_set": False, "expected_status": 1,
     "msgs": {'error': None, 'info': None}},
    {"container_id": "123", "xmode": "P1", "force": False, "nvidia": False, "purge": False, "fixperm": False,
     "container": True, "protected": False, "exec_mode_set": True, "expected_status": 0,
     "msgs": {'error': None, 'info': None}},
    {"container_id": "123", "xmode": "P1", "force": False, "nvidia": False, "purge": False, "fixperm": False,
     "container": True, "protected": False, "exec_mode_set": False, "expected_status": 1,
     "msgs": {'error': None, 'info': None}},
    {"container_id": "123", "xmode": None, "force": False, "nvidia": False, "purge": True, "fixperm": False,
     "container": True, "protected": False, "exec_mode_set": True, "expected_status": 0,
     "msgs": {'error': None, 'info': None}},
    {"container_id": "123", "xmode": None, "force": False, "nvidia": False, "purge": False, "fixperm": True,
     "container": True, "protected": False, "exec_mode_set": True, "expected_status": 0,
     "msgs": {'error': None, 'info': "fixed permissions in container: %s"}},
    {"container_id": "123", "xmode": None, "force": False, "nvidia": True, "purge": False, "fixperm": False,
     "container": True, "protected": False, "exec_mode_set": True, "expected_status": 0,
     "msgs": {'error': None, 'info': "nvidia mode set"}},
    {"container_id": "123", "xmode": "P1", "force": False, "nvidia": False, "purge": False, "fixperm": False,
     "container": True, "protected": True, "exec_mode_set": False, "expected_status": 1,
     "msgs": {'error': "container is protected", 'info': None}},
    {"container_id": "invalid", "xmode": None, "force": False, "nvidia": False, "purge": False, "fixperm": False,
     "container": False, "protected": False, "exec_mode_set": False, "expected_status": 1,
     "msgs": {'error': "invalid container id", 'info': None}},
])
def test_40_do_setup(mocker, ucli, cmdparse, params_setup):
    """ Test40 UdockerCLI().do_setup(). """
    cmdparse.get.side_effect = lambda x: {'P1': params_setup['container_id'], '--execmode=': params_setup['xmode'],
                                          '--force': params_setup['force'],
                                          '--nvidia': params_setup['nvidia'],
                                          '--purge': params_setup['purge'], '--fixperm': params_setup['fixperm']}.get(x)
    cmdparse.missing_options.return_value = not params_setup['container_id']
    mocker.patch.object(ucli.localrepo, 'cd_container',
                        return_value=params_setup['container_id'] if params_setup['container'] else None)
    mocker.patch.object(ucli.localrepo, 'isprotected_container', return_value=params_setup['protected'])

    exec_mode_mock = mocker.patch('udocker.cli.ExecutionMode')
    exec_mode_mock.return_value.set_mode.return_value = params_setup['exec_mode_set']

    mocker.patch.object(Unshare, 'namespace_exec')
    mock_log_error = mocker.patch.object(LOG, 'error')
    mock_log_info = mocker.patch.object(LOG, 'info')

    status = ucli.do_setup(cmdparse)

    assert status == params_setup['expected_status']
    if params_setup['msgs']['error']:
        mock_log_error.assert_called_with(params_setup['msgs']['error'])

    if params_setup['msgs']['info']:
        mock_log_info.assert_called_with(params_setup['msgs']['info'], mocker.ANY) \
            if "%s" in params_setup['msgs']['info'] else mock_log_info.assert_called_with(params_setup['msgs']['info'])


@pytest.mark.parametrize("missing_options, expected_status, conf_items, expected_output", [
    (False, 0, {'option1': 'value1', 'option2': 'value2'}, True),
    (True, 1, {}, False),
])
def test_41_do_showconf(mocker, ucli, cmdparse, config, missing_options, expected_status, conf_items, expected_output):
    """ Test41 UdockerCLI().do_showconf(). """
    cmdparse.missing_options.return_value = missing_options
    config.conf = conf_items
    mock_msg_info = mocker.patch.object(MSG, 'info')
    status = ucli.do_showconf(cmdparse)
    assert status == expected_status
    if expected_output:
        expected_calls = [mocker.call(80 * "_"), mocker.call("\t\tConfiguration options")]
        expected_calls += [mocker.call(f'{k} = {v}') for k, v in sorted(conf_items.items())]
        expected_calls.append(mocker.call(80 * "_"))
        mock_msg_info.assert_has_calls(expected_calls, any_order=True)


@pytest.mark.parametrize("missing_options, module_ids, force, prefix, from_loc, install_success, expected_status", [
    (True, [], False, None, None, False, 1),
    (False, [1, 2], False, None, None, True, 0),
    (False, [], True, "/custom/dir", "http://example.com", True, 0),
    (False, [3], False, None, None, False, 1),
])
def test_42_do_install(mocker, ucli, cmdparse, missing_options, udockertools, module_ids, force, prefix, from_loc,
                       install_success, expected_status):
    """ Test42 UdockerCLI().do_install(). """
    cmdparse.get.side_effect = lambda x: {'P*': module_ids, '--force': force, '--prefix=': prefix,
                                          '--from=': from_loc}.get(x)
    cmdparse.missing_options.return_value = missing_options
    mocker.patch.object(ucli.localrepo, 'installdir', '/default/install/dir')
    mocker.patch.object(ucli.localrepo, 'tardir', '/default/tar/dir')
    udockertools.return_value.install_modules.return_value = install_success

    status = ucli.do_install(cmdparse)
    assert status == expected_status


@pytest.mark.parametrize("missing_options, module_ids, get_modules, prefix, rm_success, expected_status", [
    (True, [], [], None, False, 1),
    (False, [1, 2], [], None, True, 0),
    (False, [], [2, 3], "/custom/dir", True, 0),
    (False, [3], [], None, False, 1),
])
def test_43_do_rmmod(mocker, ucli, cmdparse, udockertools, missing_options, module_ids, get_modules, prefix, rm_success,
                     expected_status):
    """ Test43 UdockerCLI().do_rmmod(). """
    cmdparse.get.side_effect = lambda x: {'P*': module_ids, '--prefix=': prefix}.get(x)
    cmdparse.missing_options.return_value = missing_options
    mocker.patch.object(ucli.localrepo, 'installdir', '/default/install/dir')
    udockertools.return_value.rm_module.return_value = rm_success
    mock_module_metadata = [{'uid': uid} for uid in get_modules]
    udockertools.return_value.get_modules.return_value = mock_module_metadata

    status = ucli.do_rmmod(cmdparse)
    assert status == expected_status


@pytest.mark.parametrize("missing_opts, force, long, metadata_success, expected_status", [
    (True, False, False, False, 1),
    (False, False, False, True, 0),
    (False, True, False, True, 0),
    (False, False, True, True, 0),
    (False, False, False, False, 0),
])
def test_44_do_availmod(ucli, udockertools, cmdparse, missing_opts, force, long, metadata_success, expected_status):
    """ Test44 UdockerCLI().do_availmod(). """
    cmdparse.get.side_effect = lambda x: {'--force': force, '-l': long}.get(x)
    cmdparse.missing_options.return_value = missing_opts
    udockertools.return_value.get_metadata.return_value = {"example": "metadata"} if metadata_success else None

    status = ucli.do_availmod(cmdparse)
    assert status == expected_status


@pytest.mark.parametrize("missing_options, file_exists, remove_success, expected_status, err_msg", [
    (True, False, False, 1, None),
    (False, True, True, 0, None),
    (False, False, True, 0, None),
    (False, True, False, 1, "could not remove: %s - %s."),
])
def test_45_do_rmmeta(mocker, ucli, cmdparse, config, missing_options, file_exists, remove_success, expected_status,
                      err_msg):
    """ Test45 UdockerCLI().do_rmmeta(). """
    cmdparse.missing_options.return_value = missing_options
    config.conf = {'installdir': '/default/install/dir', 'metadata_json': 'metadata.json'}
    mocker.patch.object(Config, 'conf', {'installdir': '/default/install/dir', 'metadata_json': 'metadata.json'})
    mocker.patch('os.path.exists', return_value=file_exists)
    if remove_success:
        mocker.patch('os.remove')
    else:
        mocker.patch('os.remove', side_effect=OSError)
    mock_log_error = mocker.patch.object(LOG, 'error')
    mock_log_info = mocker.patch.object(LOG, 'info')

    status = ucli.do_rmmeta(cmdparse)

    assert status == expected_status
    if file_exists and remove_success:
        mock_log_info.assert_called()
    elif file_exists and not remove_success:
        mock_log_error.assert_called_with(err_msg, mocker.ANY, mocker.ANY)


@pytest.mark.parametrize("module_ids, force, prefix, from_loc, download, expected_status", [
    ([1, 2], False, None, None, True, 0),
    ([], True, "/custom/dir", "http://example.com", True, 0),
    ([3], False, None, None, False, 1),
])
def test_46_do_downloadtar(mocker, ucli, cmdparse, udockertools, module_ids, force, prefix, from_loc, download,
                           expected_status):
    """ Test46 UdockerCLI().do_downloadtar(). """
    cmdparse.get.side_effect = lambda x: {'P*': module_ids, '--force': force, '--prefix=': prefix,
                                          '--from=': from_loc}.get(x)
    mocker.patch.object(ucli.localrepo, 'tardir', '/default/tar/dir')
    udockertools.return_value.download_tarballs.return_value = download
    status = ucli.do_downloadtar(cmdparse)

    assert status == expected_status


@pytest.mark.parametrize("module_ids, prefix, delete_success, expected_status", [
    ([1, 2], None, True, 0),
    ([], "/custom/dir", True, 0),
    ([3], None, False, 1),
])
def test_47_do_rmtar(mocker, ucli, cmdparse, udockertools, module_ids, prefix, delete_success, expected_status):
    """ Test47 UdockerCLI().do_rmtar(). """
    cmdparse.get.side_effect = lambda x: {'P*': module_ids, '--prefix=': prefix}.get(x)
    mocker.patch.object(ucli.localrepo, 'tardir', '/default/tar/dir')
    udockertools.return_value.delete_tarballs.return_value = delete_success

    status = ucli.do_rmtar(cmdparse)
    assert status == expected_status


@pytest.mark.parametrize("missing_options, long_format, prefix, metadata_content, expected_status", [
    (False, False, None, [{"module1": "info1"}, {"module2": "info2"}], 0),
    (False, True, "/custom/dir", [{"module1": "detailed_info1"}], 0),
    (True, False, None, [], 1),
])
def test_48_do_showmod(mocker, ucli, cmdparse, missing_options, udockertools, long_format, prefix, metadata_content,
                       expected_status):
    """ Test48 UdockerCLI().do_showmod(). """
    cmdparse.get.side_effect = lambda x: {'-l': long_format, '--prefix=': prefix}.get(x)
    cmdparse.missing_options.return_value = missing_options
    mocker.patch.object(ucli.localrepo, 'installdir', '/default/install/dir')
    udockertools.return_value.get_modules.return_value = metadata_content

    status = ucli.do_showmod(cmdparse)
    assert status == expected_status


@pytest.mark.parametrize("chk_dir, force, tarball_files, is_file, verify_sha256_result, expected_status", [
    (None, False, ['mod1.tar', 'mod2.tar'], [True, True], True, 0),
    (None, False, ['mod1.tar', 'mod2.tar'], [True, True], False, 1),
    (None, False, [], [], True, 0),
    ("/custom/dir", False, ['mod1.tar'], [True], True, 0),
    (None, True, ['mod1.tar'], [True], True, 0),
])
def test_49_do_verifytar(mocker, ucli, cmdparse, udockertools, chk_dir, force, tarball_files, is_file,
                         verify_sha256_result, expected_status):
    cmdparse.get.side_effect = lambda opt: {"--prefix=": chk_dir, "--force": force}.get(opt)
    mocker.patch.object(ucli.localrepo, 'tardir', '/default/tar/dir')
    mocker.patch.object(os.path, 'isfile', side_effect=is_file)

    metadata = [{'tarball': file} for file in tarball_files]
    udockertools.return_value.get_metadata.return_value = metadata
    udockertools.return_value.verify_sha.return_value = verify_sha256_result

    status = ucli.do_verifytar(cmdparse)

    assert status == expected_status


@pytest.mark.parametrize("missing_options, raises_exception,  expected_status", [
    (False, False, 0),
    # (False, True, 1), # TODO: this scenario needs the exception to be changed to KeyError
    (True, False, 1),
])
def test_50_do_version(mocker, ucli, config, cmdparse, missing_options, raises_exception, expected_status):
    """ Test50 UdockerCLI().do_version(). """
    cmdparse.missing_options.return_value = missing_options
    mocker.patch('udocker.cli.__version__', '1.1.1')
    config.conf = {} if raises_exception else {'tarball_release': '1.2.3'}
    mocker.patch.object(MSG, 'info')

    status = ucli.do_version(cmdparse)

    assert status == expected_status


def test_51_do_help(mocker, ucli, cmdparse):
    """ Test51 UdockerCLI().do_help(). """
    mock_msg_info = mocker.patch.object(MSG, 'info')
    status = ucli.do_help(cmdparse)
    assert status == 0
    mock_msg_info.assert_called()
