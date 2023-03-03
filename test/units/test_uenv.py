#!/usr/bin/env python
"""
udocker unit tests: Uenv
"""
import pytest
from udocker.utils.uenv import Uenv, get_pair


data_env = [('ENV1=VAL1', ('ENV1', 'VAL1')),
            (1, ('', '')),
            ('ENV1', ('ENV1', '')),
            ('ENV1 VAL1', ('', ''))]


@pytest.mark.parametrize("envstr,expected", data_env)
def test_01_get_pair(envstr, expected):
    """Test01 get_pair"""
    (key, val) = get_pair(envstr)
    assert (key, val) == expected


data_ap = [(['LANG=en_US'], 'HOME=/h/u1', {'HOME': '/h/u1', 'LANG': 'en_US'}),
           (['HOME=/h/u1', 'LANG=en_US'], 'HOME=/h/u2', {'HOME': '/h/u2', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envt,envstr,expected", data_ap)
def test_02_append(envt, envstr, expected):
    """Test02 Uenv().append"""
    uenv = Uenv(envt).append(envstr)
    assert uenv.env == expected


data_apif = [(['LANG=en_US'], 'HOME=/h/u1', {'HOME': '/h/u1', 'LANG': 'en_US'}),
             (['HOME=/h/u1', 'LANG=en_US'], 'HOME=/h/u2', {'HOME': '/h/u1', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envt,envstr,expected", data_apif)
def test_03_appendif(envt, envstr, expected):
    """Test03 Uenv().appendif"""
    uenv = Uenv(envt).appendif(envstr)
    assert uenv.env == expected


data_ext = [(['LANG=en_US'], ['HOME=/h/u1'], {'HOME': '/h/u1', 'LANG': 'en_US'}),
            (['LANG=en_US'], {'HOME': '/h/u1'}, {'HOME': '/h/u1', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envt,envl,expected", data_ext)
def test_04_extend(envt, envl, expected):
    """Test04 Uenv().extend"""
    uenv = Uenv(envt).extend(envl)
    assert uenv.env == expected


data_extif = [(['LANG=en_US'], ['HOME=/h/u1'], {'HOME': '/h/u1', 'LANG': 'en_US'}),
              (['HOME=/h/u1', 'LANG=en_US'], {'HOME': '/h/u2'}, {'HOME': '/h/u1', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envt,envstr,expected", data_extif)
def test_05_extendif(envt, envstr, expected):
    """Test05 Uenv().extendif"""
    uenv = Uenv(envt).extendif(envstr)
    assert uenv.env == expected


data_add = [(['LANG=en_US'], ['HOME=/h/u1'], {'HOME': '/h/u1', 'LANG': 'en_US'}),
            (['LANG=en_US'], 'HOME=/h/u1', {'HOME': '/h/u1', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envt,envl,expected", data_add)
def test_06_add(envt, envl, expected):
    """Test06 Uenv().add"""
    uenv = Uenv(envt).add(envl)
    assert uenv.env == expected


data_get = [(['HOME=/h/u1'], 'HOME', '/h/u1'),
            (['HOME=/h/u1'], 'dummy', '')]


@pytest.mark.parametrize("envl,keystr,expected", data_get)
def test_07_getenv(envl, keystr, expected):
    """Test07 Uenv().getenv"""
    result = Uenv(envl).getenv(keystr)
    assert result == expected


data_set = [(['LANG=en_US'], 'HOME', '/h/u1', {'HOME': '/h/u1', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envl,key,value,expected", data_set)
def test_08_setenv(envl, key, value, expected):
    """Test08 Uenv().setenv"""
    uenv = Uenv(envl).setenv(key, value)
    assert uenv.env == expected


data_unset = [(['LANG=en_US', 'HOME=/h/u1'], 'HOME', True),
              (['LANG=en_US', 'HOME=/h/u1'], 'dummy', False)]


@pytest.mark.parametrize("envl,key,expected", data_unset)
def test_09_unsetenv(envl, key, expected):
    """Test09 Uenv().unsetenv"""
    out = Uenv(envl).unsetenv(key)
    assert out == expected


def test_10_list():
    """Test10 Uenv().list"""
    envl = ['LANG=en_US', 'HOME=/h/u1']
    result = ['LANG=en_US', 'HOME=/h/u1']

    out = Uenv(envl).list()
    assert out == result


def test_11_dict():
    """Test11 Uenv().dict"""
    envl = ['LANG=en_US', 'HOME=/h/u1']
    result = {'HOME': '/h/u1', 'LANG': 'en_US'}

    out = Uenv(envl).dict()
    assert out == result


def test_12_keys():
    """Test12 Uenv().keys"""
    envl = ['LANG=en_US', 'HOME=/h/u1']
    result = {'HOME': None, 'LANG': None}

    out = Uenv(envl).keys()
    assert out == result.keys()
