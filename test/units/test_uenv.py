#!/usr/bin/env python
"""
udocker unit tests: Uenv
"""
import pytest
from udocker.utils.uenv import Uenv, get_pair, UenvIterator

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

@pytest.mark.parametrize("env_data, expected_keys", [
    (["key1=value1", "key2=value2"], ["key1", "key2"]),
    ([], []),
])
def test_02_uenv_iterator(env_data, expected_keys):
    """Test02 UenvIterator class."""
    uenv = Uenv(env_data)
    iterator = UenvIterator(uenv)

    iterated_keys = []
    try:
        while True:
            key, _ = next(iterator)
            iterated_keys.append(key)
    except StopIteration:
        pass

    assert iterated_keys == expected_keys

    assert iterator._uenv == uenv
    assert iterator._keys == expected_keys
    assert iterator._index == len(expected_keys)


@pytest.mark.parametrize("init_input, add, expected_output", [
    (None, True, {}),
    (['LANG=en_US', 'HOME=/h/u1'], True, {}),
    (['LANG=en_US', 'HOME=/h/u1'], False, {'HOME': '/h/u1', 'LANG': 'en_US'}),
])
def test_03__init(mocker, init_input, add, expected_output):
    """Test03 Uenv().__init__() """
    mocker.patch('udocker.utils.uenv.Uenv.add', return_value=add)
    if not add:
        with pytest.raises(ValueError):
            Uenv(init_input)
    else:
        uenv = Uenv(init_input)
        assert uenv.env == expected_output

@pytest.mark.parametrize("env_data, expected_items", [
    (["key1=value1", "key2=value2"], [("key1", "value1"), ("key2", "value2")]),
    ([], []),
])
def test_04_uenv_iter(env_data, expected_items):
    """Test04 Uenv.__iter__() """
    uenv = Uenv(env_data)
    iterated_items = []
    for key, value in uenv:
        iterated_items.append((key, value))
    assert iterated_items == expected_items

@pytest.mark.parametrize("env_list, expected_length", [
    (["key1=value1", "key2=value2"], 2),
    (["key1=value1"], 1),
    ([], 0),
])
def test_05_uenv_len(env_list, expected_length):
    """Test05 Uenv.__len__() """
    uenv = Uenv(env_list)
    assert len(uenv) == expected_length

@pytest.mark.parametrize("envt,envstr,expected", data_ap)
def test_06_append(envt, envstr, expected):
    """Test06 Uenv().append"""
    uenv = Uenv(envt).append(envstr)
    assert uenv.env == expected


data_apif = [(['LANG=en_US'], 'HOME=/h/u1', {'HOME': '/h/u1', 'LANG': 'en_US'}),
             (['HOME=/h/u1', 'LANG=en_US'], 'HOME=/h/u2', {'HOME': '/h/u1', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envt,envstr,expected", data_apif)
def test_07_appendif(envt, envstr, expected):
    """Test07 Uenv().appendif"""
    uenv = Uenv(envt).appendif(envstr)
    assert uenv.env == expected


data_ext = [(['LANG=en_US'], ['HOME=/h/u1'], {'HOME': '/h/u1', 'LANG': 'en_US'}),
            (['LANG=en_US'], {'HOME': '/h/u1'}, {'HOME': '/h/u1', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envt,envl,expected", data_ext)
def test_08_extend(envt, envl, expected):
    """Test08 Uenv().extend"""
    uenv = Uenv(envt).extend(envl)
    assert uenv.env == expected


data_extif = [(['LANG=en_US'], ['HOME=/h/u1'], {'HOME': '/h/u1', 'LANG': 'en_US'}),
              (['HOME=/h/u1', 'LANG=en_US'], {'HOME': '/h/u2'}, {'HOME': '/h/u1', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envt,envstr,expected", data_extif)
def test_09_extendif(envt, envstr, expected):
    """Test09 Uenv().extendif"""
    uenv = Uenv(envt).extendif(envstr)
    assert uenv.env == expected


data_add = [(['LANG=en_US'], ['HOME=/h/u1'], {'HOME': '/h/u1', 'LANG': 'en_US'}),
            (['LANG=en_US'], 'HOME=/h/u1', {'HOME': '/h/u1', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envt,envl,expected", data_add)
def test_10_add(envt, envl, expected):
    """Test10 Uenv().add"""
    uenv = Uenv(envt).add(envl)
    assert uenv.env == expected


data_get = [(['HOME=/h/u1'], 'HOME', '/h/u1'),
            (['HOME=/h/u1'], 'dummy', '')]


@pytest.mark.parametrize("envl,keystr,expected", data_get)
def test_11_getenv(envl, keystr, expected):
    """Test11 Uenv().getenv"""
    result = Uenv(envl).getenv(keystr)
    assert result == expected


data_set = [(['LANG=en_US'], 'HOME', '/h/u1', {'HOME': '/h/u1', 'LANG': 'en_US'})]


@pytest.mark.parametrize("envl,key,value,expected", data_set)
def test_12_setenv(envl, key, value, expected):
    """Test12 Uenv().setenv"""
    uenv = Uenv(envl).setenv(key, value)
    assert uenv.env == expected


data_unset = [(['LANG=en_US', 'HOME=/h/u1'], 'HOME', True),
              (['LANG=en_US', 'HOME=/h/u1'], 'dummy', False)]


@pytest.mark.parametrize("envl,key,expected", data_unset)
def test_13_unsetenv(envl, key, expected):
    """Test13 Uenv().unsetenv"""
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
