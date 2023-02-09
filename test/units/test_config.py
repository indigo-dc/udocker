#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: Config
"""
from io import StringIO
from udocker.config import Config

def test_01_getconf():
    """Test01 Config.getconf() default conf."""
    config = Config()
    config.getconf()
    assert config.conf["keystore"] == "keystore"

# def test_01_getconf_02(mocker):
#     """Test01_02 Config.getconf() conf file."""
#     conf_file = StringIO("[DEFAULT]\nkeystore = ks_conf\n")
#     mocker.patch("os.path.exists", side_effect=[False, False, True])
#     config = Config()
#     config.getconf(conf_file)
#     assert config.conf["keystore"] == "ks_conf"

def test_03_getconf(monkeypatch):
    """Test03 Config.getconf() env var."""
    monkeypatch.setenv("UDOCKER_KEYSTORE", "ks_env")
    config = Config()
    config.getconf()
    assert config.conf["keystore"] == "ks_env"
