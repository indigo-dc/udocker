#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: Config
"""
import os
from configparser import ConfigParser

import pytest
from udocker.config import Config


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.config.LOG')


@pytest.mark.parametrize("config_contents, ignore_keys, expected_output", [
    ({"key1": "value1", "key2": "value2"}, None, {'key1': 'value1', 'key2': 'value2'}),
    ({"key1": "value1", "key2": "value2"}, ['key1'], {'key2': 'value2'})
])
def test_01__conf_file_read(mocker, config_contents, ignore_keys, expected_output):
    """Test01 Config._conf_file_read()"""
    mocker.patch.object(Config, 'conf', {})
    mock_config_parser_instance = mocker.Mock(spec=ConfigParser)
    mock_config_parser_instance.items.return_value = config_contents.items()

    mocker.patch('udocker.config.ConfigParser', return_value=mock_config_parser_instance)
    mocker.patch('udocker.config.LOG.info')

    Config()._conf_file_read("dummy_path", ignore_keys)
    assert Config.conf == expected_output


@pytest.mark.parametrize("paths_exist, user_cfile, ignore_keys, expected_calls", [
    ([False, False, False, False], "user.conf", None, []),
    ([False, False, False, True], "user.conf", None, [("user.conf", None)]),
    ([True, False, False, True], "user.conf", None, [("/etc/udocker.conf", None), ("user.conf", None)]),
    ([True, True, True, True], "user.conf", ["key1"], [("/etc/udocker.conf", ["key1"]),
                                                       ('/home/user/udocker.conf', ["key1"]),
                                                       ('/home/user/.udocker/udocker.conf', ["key1"]),
                                                       ("user.conf", ["key1"])])
])
def test_02_file_override(mocker, config, paths_exist, user_cfile, ignore_keys, expected_calls):
    """Test02 Config._file_override()"""
    mocker.patch.object(Config, 'conf',
                        {'config': "udocker.conf", 'homedir': "/home/user", 'topdir': "/home/user/.udocker"})
    mocker.patch.object(os.path, 'exists', side_effect=paths_exist)
    mock_conf_file_read = mocker.patch("udocker.config.Config._conf_file_read")
    config._file_override(user_cfile, ignore_keys)

    assert mock_conf_file_read.call_args_list == [mocker.call(*args) for args in expected_calls]


def test_03_getconf(config):
    """Test03 Config.getconf() default conf."""
    config.getconf()
    assert config.conf["keystore"] == "keystore"


def test_04_getconf(mocker):
    """Test04 Config.getconf() conf file."""
    conf_file = "[DEFAULT]\nkeystore = ks_conf\n"
    mock_pexist = mocker.patch("udocker.config.os.path.exists", side_effect=[False, False, True])
    mock_file = mocker.mock_open(read_data=conf_file)
    mocker.patch("builtins.open", mock_file)
    config = Config()
    config.getconf(conf_file)
    assert config.conf["keystore"] == "ks_conf"
    mock_pexist.assert_called()
    mock_file.assert_called()


def test_05_getconf(monkeypatch, config):
    """Test05 Config.getconf() env var."""
    monkeypatch.setenv("UDOCKER_KEYSTORE", "ks_env")
    config.getconf()
    assert config.conf["keystore"] == "ks_env"
