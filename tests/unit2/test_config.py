#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: Config
"""
import pytest
from udocker.config import Config, LOG

def test_01_getconf_01():
    """Test01_01 Config.getconf() default conf."""
    config = Config()
    config.getconf()
    assert config.conf["keystore"] == "keystore"

# def test_01_getconf_02(mocker):
#     """Test01_02 Config.getconf() conf file."""
#     conf_data = ("[DEFAULT]"
#                  "\n"
#                  "keystore = ks_conf")

#     mocked_file_data = mocker.mock_open(read_data=conf_data)
#     mocker.patch("builtins.open", mocked_file_data)
#     mocker.patch("os.path.exists", side_effect = [False, False, True])
#     config = Config()
#     config.getconf(mocked_file_data)
#     assert config.conf["keystore"] == "ks_conf"

def test_01_getconf_03(monkeypatch):
    """Test01_03 Config.getconf() env var."""
    monkeypatch.setenv("UDOCKER_KEYSTORE", "ks_env")
    config = Config()
    config.getconf()
    assert config.conf["keystore"] == "ks_env"
