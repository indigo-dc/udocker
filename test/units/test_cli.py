#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: UdockerCLI
"""
import os

import pytest

from udocker import MSG, LOG
from udocker.cli import UdockerCLI
from udocker.cmdparser import CmdParser
from udocker.helper.hostinfo import HostInfo


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
    mock_msg.assert_has_calls(expected_calls, any_order=True)


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
def test_14_do_search(mocker, ucli, argv, mock_values, expected_status):
    """Test14 UdockerCLI().do_search()."""
    cmdp = CmdParser()
    cmdp.parse(argv)
    mock_setrepo, mock_split, mock_doiasearch, mock_ksget, mock_doiasetv2, mock_listtags, mock_searchrepo = mock_values
    mocker.patch.object(ucli, '_set_repository', return_value=mock_setrepo)
    mocker.patch.object(ucli, '_split_imagespec', return_value=mock_split)
    mocker.patch.object(ucli.dockerioapi, 'search_get_page', return_value=mock_doiasearch)
    mocker.patch.object(ucli.keystore, 'get', return_value=mock_ksget)
    mocker.patch.object(ucli.dockerioapi.v2api, 'set_login_token', return_value=mock_doiasetv2)

    if argv[1] == "search" and "--list-tags" in argv:
        mocker.patch.object(ucli, '_list_tags', return_value=mock_listtags)
    elif argv[1] == "search":
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
def test_15_do_load(mocker, ucli, cmdp_options, check_imagerepo, load, missing_options,
                    expected_status,
                    error_msg):
    """ Test15 UdockerCLI().do_load(). """
    cmdp = mocker.Mock()
    cmdp.get.side_effect = lambda x: cmdp_options.get(x, None)
    cmdp.missing_options.return_value = missing_options

    mocker.patch.object(ucli, '_check_imagerepo', return_value=check_imagerepo)
    mocker.patch.object(ucli.localfileapi, 'load', return_value=load)
    error_log_mock = mocker.patch.object(LOG, 'error')
    info_log_mock = mocker.patch.object(LOG, 'info')

    status = ucli.do_load(cmdp)

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
def test_16_do_save(mocker, ucli, cmdp_opts, missing_opts, file_exists, save, check_img, exp_status, err_msg,
                    imgspec_list):
    """ Test16 UdockerCLI().do_save(). """
    cmdp = mocker.Mock()
    cmdp.get.side_effect = lambda x: cmdp_opts.get(x, None)
    cmdp.missing_options.return_value = missing_opts

    mocker.patch.object(ucli, '_check_imagespec', return_value=check_img)
    mocker.patch.object(os.path, 'exists', return_value=file_exists)
    mocker.patch.object(ucli.localfileapi, 'save', return_value=save)
    error_log_mock = mocker.patch.object(LOG, 'error')

    if cmdp.get('-'):
        if imgspec_list and imgspec_list[0] == '-':
            imgspec_list.pop(0)

    status = ucli.do_save(cmdp)

    assert status == exp_status
    if err_msg:
        error_log_mock.assert_called_with(err_msg, 'ipyrad.tar')
    assert cmdp.get("P*") == imgspec_list


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
def test_17_do_import(mocker, ucli, cmd_opts, missing_opts, check_imagespec_return, import_result, expected_status,
                      error_msg):
    """ Test17 UdockerCLI().do_import(). """
    cmdp = mocker.Mock()
    cmdp.get.side_effect = lambda x: cmd_opts.get(x, None)
    cmdp.missing_options.return_value = missing_opts

    mocker.patch.object(ucli, '_check_imagespec', return_value=check_imagespec_return)
    mocker.patch.object(ucli.localfileapi, 'import_toimage', return_value=import_result)
    mocker.patch.object(ucli.localfileapi, 'import_tocontainer', return_value=import_result)
    mocker.patch.object(ucli.localfileapi, 'import_clone', return_value=import_result)
    log_mock = mocker.patch.object(LOG, 'info')
    error_log_mock = mocker.patch.object(LOG, 'error')

    status = ucli.do_import(cmdp)

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
def test_18_do_export(mocker, ucli, cmdp_opts, missing_opts, container_id, export_result, expected_status,
                      err_msg):
    """ Test18 UdockerCLI().do_export(). """
    cmdp = mocker.Mock()
    cmdp.get.side_effect = lambda x: cmdp_opts.get(x, None)
    cmdp.missing_options.return_value = missing_opts

    mocker.patch.object(ucli.localrepo, 'get_container_id', return_value=container_id)
    log_error = mocker.patch.object(LOG, 'error')
    log_mock = mocker.patch.object(LOG, 'info')

    cstruct_mock = mocker.Mock()
    cstruct_class_mock = mocker.patch('udocker.cli.ContainerStructure', return_value=cstruct_mock)

    cstruct_mock.clone_tofile.return_value = export_result
    cstruct_mock.export_tofile.return_value = export_result

    status = ucli.do_export(cmdp)

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
def test_19_do_clone(mocker, ucli, cmdp_options, missing_opts, get_container_id, clone, expected_status, err_msg):
    cmdp = mocker.Mock()
    cmdp.get.side_effect = lambda x: cmdp_options.get(x, None)
    cmdp.missing_options.return_value = missing_opts

    mocker.patch.object(ucli.localrepo, 'get_container_id', return_value=get_container_id)
    mocker.patch.object(ucli.localfileapi, 'clone_container', return_value=clone)
    log_mock = mocker.patch.object(LOG, 'info')
    error_log_mock = mocker.patch.object(LOG, 'error')

    status = ucli.do_clone(cmdp)

    assert status == expected_status
    if err_msg and not get_container_id:
        error_log_mock.assert_called_with(err_msg, mocker.ANY)
    elif err_msg and cmdp.get('--name=') and get_container_id:
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
def test_20_do_login(mocker, ucli, cmdp_opts, missing_opts, input, getpass, token, keystore, exp_status,
                     err_msg):
    """ Test20 UdockerCLI().do_login(). """
    cmdp = mocker.Mock()
    cmdp.get.side_effect = lambda x: cmdp_opts.get(x, None)
    cmdp.missing_options.return_value = missing_opts

    mocker.patch.object(ucli, '_set_repository', return_value=cmdp_opts.get("--registry="))
    mocker.patch.object(ucli.dockerioapi.v2api, 'get_login_token', return_value=token)
    mocker.patch.object(ucli.keystore, 'put', return_value=keystore)
    mocker.patch('udocker.cli.GET_INPUT', return_value=input)
    mocker.patch('udocker.cli.getpass', return_value=getpass)
    mock_log_error = mocker.patch.object(LOG, 'error')
    mock_log_warning = mocker.patch.object(LOG, 'warning')

    status = ucli.do_login(cmdp)

    assert status == exp_status
    assert cmdp.get.call_count == 3

    if not missing_opts and cmdp_opts.get("--registry="):
        assert ucli._set_repository.return_value == "https://registry-1.docker.io"
    else:
        assert ucli._set_repository.return_value == None

    if err_msg:
        mock_log_error.assert_called_with(err_msg)

# @patch('udocker.cli.KeyStore.put')
# @patch('udocker.cli.DockerIoAPI.get_v2_login_token')
# @patch.object(UdockerCLI, '_set_repository')
# def test_17_do_login(self, mock_setrepo, mock_dioalog, mock_ksput):
#     """Test17 UdockerCLI().do_login()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_login(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "login", "--username", "u1", "--password", "xx"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_setrepo.return_value = True
#     mock_dioalog.return_value = "zx1"
#     mock_ksput.return_value = 1
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_login(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(mock_setrepo.called)
#     self.assertTrue(mock_dioalog.called)
#     self.assertTrue(mock_ksput.called)

#     argv = ["udocker", "login", "--username", "u1", "--password", "xx"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_setrepo.return_value = None
#     mock_dioalog.return_value = "zx1"
#     mock_ksput.return_value = 0
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_login(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(mock_setrepo.called)
#     self.assertTrue(mock_dioalog.called)
#     self.assertTrue(mock_ksput.called)

# @patch('udocker.cli.KeyStore')
# @patch.object(UdockerCLI, '_set_repository')
# def test_18_do_logout(self, mock_setrepo, mock_ks):
#     """Test18 UdockerCLI().do_logout()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_logout(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "logout", "-a"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_setrepo.return_value = None
#     mock_ks.return_value.erase.return_value = 0
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_logout(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(mock_setrepo.called)
#     self.assertTrue(mock_ks.return_value.erase.called)

#     argv = ["udocker", "logout"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_setrepo.return_value = None
#     mock_ks.return_value.delete.return_value = 1
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_logout(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(mock_setrepo.called)
#     self.assertTrue(mock_ks.return_value.delete.called)

# @patch.object(UdockerCLI, '_set_repository')
# @patch.object(UdockerCLI, '_check_imagespec')
# @patch('udocker.cli.DockerIoAPI')
# @patch('udocker.cli.KeyStore.get')
# def test_19_do_pull(self, mock_ksget, mock_dioa, mock_chkimg, mock_setrepo):
#     """Test19 UdockerCLI().do_pull()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_pull(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "pull", "ipyrad:latest"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     mock_setrepo.return_value = None
#     mock_ksget.return_value = "zx1"
#     mock_dioa.return_value.set_v2_login_token.return_value = None
#     mock_dioa.return_value.get.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_pull(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(mock_chkimg.called)
#     self.assertTrue(mock_setrepo.called)
#     self.assertTrue(mock_ksget.called)
#     self.assertTrue(mock_dioa.return_value.set_v2_login_token.called)
#     self.assertTrue(mock_dioa.return_value.get.called)

#     argv = ["udocker", "pull", "ipyrad:latest"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     mock_setrepo.return_value = None
#     mock_ksget.return_value = "zx1"
#     mock_dioa.return_value.set_v2_login_token.return_value = None
#     mock_dioa.return_value.get.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_pull(cmdp)
#     self.assertEqual(status, 0)

# @patch.object(UdockerCLI, '_check_imagespec')
# @patch('udocker.cli.ContainerStructure')
# @patch('udocker.cli.DockerIoAPI')
# def test_20__create(self, mock_dioapi, mock_cstruct, mock_chkimg):
#     """Test20 UdockerCLI()._create()."""
#     mock_dioapi.return_value.is_repo_name.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc._create("IMAGE:TAG")
#     self.assertFalse(status)

#     mock_dioapi.return_value.is_repo_name.return_value = True
#     mock_chkimg.return_value = ("", "TAG")
#     mock_cstruct.return_value.create.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc._create("IMAGE:TAG")
#     self.assertFalse(status)

#     mock_dioapi.return_value.is_repo_name.return_value = True
#     mock_chkimg.return_value = ("IMAGE", "TAG")
#     mock_cstruct.return_value.create.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc._create("IMAGE:TAG")
#     self.assertTrue(status)

# @patch.object(UdockerCLI, '_create')
# def test_21_do_create(self, mock_create):
#     """Test21 UdockerCLI().do_create()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_create(cmdp)
#     self.assertEqual(status, 1)
#     self.assertFalse(mock_create.called)

#     argv = ["udocker", "create", "ipyrad:latest"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_create.return_value = ""
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_create(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(mock_create.called)

#     argv = ["udocker", "create", "ipyrad:latest"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_create.return_value = "12345"
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_create(cmdp)
#     self.assertEqual(status, 0)
#     self.assertFalse(self.local.set_container_name.called)

#     argv = ["udocker", "create", "--name=mycont", "ipyrad:latest"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_create.return_value = "12345"
#     self.local.set_container_name.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_create(cmdp)
#     self.assertEqual(status, 1)
#     self.assertFalse(self.local.set_container_name.called)

# # def test_22__get_run_options(self):
# #    """Test22 UdockerCLI()._get_run_options()"""

# @patch('udocker.cli.ExecutionMode')
# @patch.object(UdockerCLI, 'do_pull')
# @patch.object(UdockerCLI, '_create')
# @patch.object(UdockerCLI, '_check_imagespec')
# def test_23_do_run(self, mock_chkimg, mock_create, mock_pull, mock_exec):
#     """Test23 UdockerCLI().do_run()."""
#     mock_pull.return_value = None
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_run(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "run"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_pull.return_value = None
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_run(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "run", "--location=/tmp/udocker", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_pull.return_value = None
#     mock_exec.return_value.get_engine.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_run(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(mock_exec.return_value.get_engine.called)

#     mock_pull.return_value = None
#     exeng_patch = patch("udocker.engine.proot.PRootEngine")
#     proot = exeng_patch.start()
#     mock_proot = Mock()
#     proot.return_value = mock_proot

#     argv = ["udocker", "run", "--location=/tmp/udocker", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_pull.return_value = None
#     mock_exec.return_value.get_engine.return_value = proot
#     proot.run.return_value = 0
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_run(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(proot.run.called)
#     self.assertFalse(self.local.isprotected_container.called)

#     argv = ["udocker", "run", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = ""
#     mock_pull.return_value = None
#     mock_exec.return_value.get_engine.return_value = proot
#     proot.run.return_value = 0
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     self.local.cd_imagerepo.return_value = True
#     mock_create.return_value = "12345"
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_run(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(self.local.get_container_id.called)
#     self.assertTrue(mock_chkimg.called)
#     self.assertTrue(self.local.cd_imagerepo.called)
#     self.assertTrue(mock_create.called)

#     exeng_patch.stop()

# def test_24_do_images(self):
#     """Test24 UdockerCLI().do_images()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_images(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "images", "-l"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_imagerepos.return_value = [("img1", "tag1")]
#     self.local.isprotected_imagerepo.return_value = False
#     self.local.cd_imagerepo.return_value = "/img1"
#     self.local.get_layers.return_value = [("l1", 1024)]
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_images(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(self.local.get_imagerepos.called)
#     self.assertTrue(self.local.isprotected_imagerepo.called)
#     self.assertTrue(self.local.cd_imagerepo.called)
#     self.assertTrue(self.local.get_layers.called)

# @patch('udocker.cli.ExecutionMode')
# def test_25_do_ps(self, mock_exec):
#     """Test25 UdockerCLI().do_ps()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_ps(cmdp)
#     self.assertEqual(status, 1)

#     exeng_patch = patch("udocker.engine.proot.PRootEngine")
#     proot = exeng_patch.start()
#     mock_proot = Mock()
#     proot.return_value = mock_proot
#     cdir = "/home/u1/.udocker/containers"
#     argv = ["udocker", "ps", "-m", "-s"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_containers_list.return_value = [[cdir, "/", "a"]]
#     mock_exec.return_value.get_engine.return_value = proot
#     self.local.isprotected_container.return_value = False
#     self.local.iswriteable_container.return_value = True
#     self.local.get_size.return_value = 1024
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_ps(cmdp)
#     self.assertEqual(status, 0)
#     exeng_patch.stop()

# def test_26_do_rm(self):
#     """Test26 UdockerCLI().do_rm()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rm(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "rm"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rm(cmdp)
#     self.assertEqual(status, 1)
#     self.assertFalse(self.local.get_container_id.called)

#     argv = ["udocker", "rm", "mycont"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = None
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rm(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.get_container_id.called)
#     self.assertFalse(self.local.isprotected_container.called)

#     argv = ["udocker", "rm", "mycont"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = "12345"
#     self.local.isprotected_container.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rm(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.isprotected_container.called)
#     self.assertFalse(self.local.del_container.called)

#     argv = ["udocker", "rm", "mycont"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = "12345"
#     self.local.isprotected_container.return_value = False
#     self.local.del_container.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rm(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.del_container.called)

#     argv = ["udocker", "rm", "mycont"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = "12345"
#     self.local.isprotected_container.return_value = False
#     self.local.del_container.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rm(cmdp)
#     self.assertEqual(status, 0)

# @patch.object(UdockerCLI, '_check_imagespec')
# def test_27_do_rmi(self, mock_chkimg):
#     """Test27 UdockerCLI().do_rmi()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rmi(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "rmi"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_chkimg.return_value = ("", "latest")
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rmi(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(mock_chkimg.called)
#     self.assertFalse(self.local.isprotected_imagerepo.called)

#     argv = ["udocker", "rmi", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     self.local.isprotected_imagerepo.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rmi(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.isprotected_imagerepo.called)
#     self.assertFalse(self.local.del_imagerepo.called)

#     argv = ["udocker", "rmi", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     self.local.isprotected_imagerepo.return_value = False
#     self.local.del_imagerepo.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rmi(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.del_imagerepo.called)

#     argv = ["udocker", "rmi", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     self.local.isprotected_imagerepo.return_value = False
#     self.local.del_imagerepo.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rmi(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(self.local.del_imagerepo.called)

# @patch.object(UdockerCLI, '_check_imagespec')
# def test_28_do_protect(self, mock_chkimg):
#     """Test28 UdockerCLI().do_protect()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_protect(cmdp)
#     self.assertEqual(status, 1)
#     self.assertFalse(self.local.get_container_id.called)

#     argv = ["udocker", "protect"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = False
#     mock_chkimg.return_value = ("", "latest")
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_protect(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.get_container_id.called)
#     self.assertTrue(mock_chkimg.called)
#     self.assertFalse(self.local.protect_container.called)
#     self.assertFalse(self.local.protect_imagerepo.called)

#     argv = ["udocker", "protect", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = False
#     mock_chkimg.return_value = ("", "latest")
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_protect(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "protect", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = False
#     self.local.protect_imagerepo.return_value = True
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_protect(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(self.local.protect_imagerepo.called)

#     argv = ["udocker", "protect", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = True
#     self.local.protect_container.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_protect(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(self.local.get_container_id.called)
#     self.assertTrue(self.local.protect_container.called)

#     argv = ["udocker", "protect", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = True
#     self.local.protect_container.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_protect(cmdp)
#     self.assertEqual(status, 1)

# @patch.object(UdockerCLI, '_check_imagespec')
# def test_29_do_unprotect(self, mock_chkimg):
#     """Test29 UdockerCLI().do_unprotect()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_unprotect(cmdp)
#     self.assertEqual(status, 1)
#     self.assertFalse(self.local.get_container_id.called)

#     argv = ["udocker", "protect"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = False
#     mock_chkimg.return_value = ("", "latest")
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_unprotect(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.get_container_id.called)
#     self.assertTrue(mock_chkimg.called)
#     self.assertFalse(self.local.unprotect_container.called)
#     self.assertFalse(self.local.unprotect_imagerepo.called)

#     argv = ["udocker", "protect", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = False
#     mock_chkimg.return_value = ("", "latest")
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_unprotect(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "protect", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = False
#     self.local.unprotect_imagerepo.return_value = True
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_unprotect(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(self.local.unprotect_imagerepo.called)

#     argv = ["udocker", "protect", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = True
#     self.local.unprotect_container.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_unprotect(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(self.local.get_container_id.called)
#     self.assertTrue(self.local.unprotect_container.called)

#     argv = ["udocker", "protect", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = True
#     self.local.unprotect_container.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_unprotect(cmdp)
#     self.assertEqual(status, 1)

# def test_30_do_name(self):
#     """Test30 UdockerCLI().do_name()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_name(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "name"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_name(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.get_container_id.called)
#     self.assertFalse(self.local.set_container_name.called)

#     argv = ["udocker", "name", "12345", "mycont"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = True
#     self.local.set_container_name.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_name(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.set_container_name.called)

#     argv = ["udocker", "name", "12345", "mycont"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = True
#     self.local.set_container_name.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_name(cmdp)
#     self.assertEqual(status, 0)

# def test_31_do_rename(self):
#     """Test31 UdockerCLI().do_rename()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rename(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "rename", "contname", "newname"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.side_effect = ["", ""]
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rename(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.get_container_id.call_count, 1)

#     argv = ["udocker", "rename", "contname", "newname"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.side_effect = ["123", "543"]
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rename(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.get_container_id.call_count, 2)

#     argv = ["udocker", "rename", "contname", "newname"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.side_effect = ["123", ""]
#     self.local.del_container_name.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rename(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.del_container_name.called)
#     self.assertFalse(self.local.set_container_name.called)

#     argv = ["udocker", "rename", "contname", "newname"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.side_effect = ["123", ""]
#     self.local.del_container_name.return_value = True
#     self.local.set_container_name.side_effect = [False, True]
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rename(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.set_container_name.call_count, 2)

#     argv = ["udocker", "rename", "contname", "newname"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.side_effect = ["123", ""]
#     self.local.del_container_name.return_value = True
#     self.local.set_container_name.side_effect = [True, True]
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rename(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(self.local.set_container_name.call_count, 1)

# def test_32_do_rmname(self):
#     """Test32 UdockerCLI().do_rmname()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rmname(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "rmname"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rmname(cmdp)
#     self.assertEqual(status, 1)
#     self.assertFalse(self.local.del_container_name.called)

#     argv = ["udocker", "rmname", "contname"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.del_container_name.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rmname(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.del_container_name.called)

#     argv = ["udocker", "rmname", "contname"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.del_container_name.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_rmname(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(self.local.del_container_name.called)

# @patch.object(UdockerCLI, '_check_imagespec')
# @patch('udocker.cli.json.dumps')
# @patch('udocker.cli.ContainerStructure.get_container_attr')
# def test_33_do_inspect(self, mock_csattr, mock_jdump, mock_chkimg):
#     """Test33 UdockerCLI().do_inspect()."""
#     cont_insp = {
#         "architecture": "amd64",
#         "config": {
#             "AttachStderr": False,
#             "AttachStdin": False,
#             "AttachStdout": False,
#             "Cmd": [
#                 "/bin/bash"
#             ],
#             "Domainname": "",
#             "Entrypoint": None,
#             "Env": [
#                 "PATH=/usr/local/sbin"
#             ],
#             "Hostname": "",
#             "Image": "sha256:05725a",
#             "Labels": {
#                 "org.opencontainers.image.vendor": "CentOS"
#             },
#             "WorkingDir": ""
#         },
#         "container": "c171c",
#         "container_config": {
#             "ArgsEscaped": True,
#             "Cmd": ["/bin/sh", "-c"],
#             "Domainname": "",
#             "Env": [
#                 "PATH=/usr/local/sbin"
#             ],
#             "Hostname": "c171c5a1528a",
#             "Image": "sha256:05725a",
#             "Labels": {
#                 "org.label-schema.license": "GPLv2",
#                 "org.label-schema.name": "CentOS Base Image",
#                 "org.opencontainers.image.vendor": "CentOS"
#             },
#             "WorkingDir": ""
#         },
#         "created": "2020-05-05T21",
#         "docker_version": "18.09.7",
#         "id": "e72c1",
#         "os": "linux",
#         "parent": "61dc7"
#     }

#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = ""
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_inspect(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "inspect"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = ""
#     mock_chkimg.return_value = ("", "latest")
#     self.local.cd_imagerepo.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_inspect(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "inspect"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = ""
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     self.local.cd_imagerepo.return_value = True
#     self.local.get_image_attributes.return_value = (cont_insp, "")
#     mock_jdump.return_value = cont_insp
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_inspect(cmdp)
#     self.assertEqual(status, 0)

#     argv = ["udocker", "inspect", "-p", "123"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.get_container_id.return_value = "123"
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     self.local.cd_imagerepo.return_value = True
#     self.local.get_image_attributes.return_value = (cont_insp, "")
#     mock_csattr.return_value = ("/ROOT/cont", cont_insp)
#     mock_jdump.return_value = cont_insp
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_inspect(cmdp)
#     self.assertEqual(status, 0)

# @patch.object(UdockerCLI, '_check_imagespec')
# def test_34_do_verify(self, mock_chkimg):
#     """Test34 UdockerCLI().do_verify()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_verify(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "verify", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     self.local.cd_imagerepo.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_verify(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "verify", "ipyrad"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_chkimg.return_value = ("ipyrad", "latest")
#     self.local.cd_imagerepo.return_value = True
#     self.local.verify_image.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_verify(cmdp)
#     self.assertEqual(status, 0)

# @patch('udocker.cli.ExecutionMode')
# @patch('udocker.cli.NvidiaMode')
# @patch('udocker.cli.FileUtil.rchmod')
# @patch('udocker.cli.Unshare.namespace_exec')
# @patch('udocker.cli.MountPoint')
# @patch('udocker.cli.FileBind')
# def test_35_do_setup(self, mock_fb, mock_mp, mock_unshr, mock_furchmod, mock_nv, mock_execm):
#     """Test35 UdockerCLI().do_setup()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_setup(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "setup"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.cd_container.return_value = ""
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_setup(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.cd_container.called)

#     argv = ["udocker", "setup", "--execmode=P2", "mycont"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.cd_container.return_value = "/ROOT/cont1"
#     self.local.isprotected_container.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_setup(cmdp)
#     self.assertEqual(status, 1)
#     self.assertTrue(self.local.isprotected_container.called)

#     argv = ["udocker", "setup", "--execmode=P2", "--purge", "--fixperm", "--nvidia", "mycont"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.cd_container.return_value = "/ROOT/cont1"
#     self.local.isprotected_container.return_value = False
#     mock_fb.return_value.restore.return_value = None
#     mock_mp.return_value.restore.return_value = None
#     mock_unshr.return_value = None
#     mock_furchmod.return_value = None
#     mock_nv.return_value.set_mode.return_value = None
#     mock_execm.return_value.set_mode.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_setup(cmdp)
#     self.assertEqual(status, 0)
#     self.assertTrue(mock_fb.return_value.restore.called)
#     self.assertTrue(mock_mp.return_value.restore.called)
#     self.assertTrue(mock_unshr.called)
#     self.assertTrue(mock_furchmod.called)
#     self.assertTrue(mock_nv.return_value.set_mode.called)
#     self.assertTrue(mock_execm.return_value.set_mode.called)

#     argv = ["udocker", "setup", "--execmode=P2", "--purge", "--fixperm", "--nvidia", "mycont"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.cd_container.return_value = "/ROOT/cont1"
#     self.local.isprotected_container.return_value = False
#     mock_fb.return_value.restore.return_value = None
#     mock_mp.return_value.restore.return_value = None
#     mock_unshr.return_value = None
#     mock_furchmod.return_value = None
#     mock_nv.return_value.set_mode.return_value = None
#     mock_execm.return_value.set_mode.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_setup(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "setup", "mycont"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     self.local.cd_container.return_value = "/ROOT/cont1"
#     self.local.isprotected_container.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_setup(cmdp)
#     self.assertEqual(status, 0)

# @patch('udocker.cli.UdockerTools')
# def test_36_do_install(self, mock_utools):
#     """Test36 UdockerCLI().do_install()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_install(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "install", "--force", "--purge"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_utools.return_value.purge.return_value = None
#     mock_utools.return_value.install.return_value = False
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_install(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "install", "--force", "--purge"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     mock_utools.return_value.purge.return_value = None
#     mock_utools.return_value.install.return_value = True
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_install(cmdp)
#     self.assertEqual(status, 0)

# def test_37_do_showconf(self):
#     """Test37 UdockerCLI().do_showconf()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_showconf(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "showconf"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_showconf(cmdp)
#     self.assertEqual(status, 0)

# def test_38_do_version(self):
#     """Test38 UdockerCLI().do_version()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_version(cmdp)
#     self.assertEqual(status, 1)

#     argv = ["udocker", "version"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_version(cmdp)
#     self.assertEqual(status, 0)

# def test_39_do_help(self):
#     """Test39 UdockerCLI().do_help()."""
#     argv = ["udocker", "-h"]
#     cmdp = CmdParser()
#     cmdp.parse(argv)
#     udoc = UdockerCLI(self.local)
#     status = udoc.do_help(cmdp)
#     self.assertEqual(status, 0)
