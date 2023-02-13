#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: Config
"""
import pytest
from io import StringIO
from udocker.config import Config


@pytest.fixture
def config():
    return Config()


def test_01_getconf(config):
    """Test01 Config.getconf() default conf."""
    config.getconf()
    assert config.conf["keystore"] == "keystore"


# def test_01_getconf_02(mocker):
#     """Test01_02 Config.getconf() conf file."""
#     conf_file = StringIO("[DEFAULT]\nkeystore = ks_conf\n")
#     mocker.patch("os.path.exists", side_effect=[False, False, True])
#     config = Config()
#     config.getconf(conf_file)
#     assert config.conf["keystore"] == "ks_conf"


def test_03_getconf(monkeypatch, config):
    """Test03 Config.getconf() env var."""
    monkeypatch.setenv("UDOCKER_KEYSTORE", "ks_env")
    config.getconf()
    assert config.conf["keystore"] == "ks_env"
