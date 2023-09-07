#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: Config
"""
import pytest
from udocker.config import Config


@pytest.fixture
def config():
    return Config()


def test_01_getconf(config):
    """Test01 Config.getconf() default conf."""
    config.getconf()
    assert config.conf["keystore"] == "keystore"


def test_02_getconf(mocker):
    """Test01_02 Config.getconf() conf file."""
    conf_file = "[DEFAULT]\nkeystore = ks_conf\n"
    mock_pexist = mocker.patch("udocker.config.os.path.exists", side_effect=[False, False, True])
    mock_file = mocker.mock_open(read_data=conf_file)
    mocker.patch("builtins.open", mock_file)
    config = Config()
    config.getconf(conf_file)
    assert config.conf["keystore"] == "ks_conf"
    mock_pexist.assert_called()
    mock_file.assert_called()


def test_03_getconf(monkeypatch, config):
    """Test03 Config.getconf() env var."""
    monkeypatch.setenv("UDOCKER_KEYSTORE", "ks_env")
    config.getconf()
    assert config.conf["keystore"] == "ks_env"
