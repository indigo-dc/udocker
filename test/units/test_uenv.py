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
def test_09_getenv(envl, keystr, expected):
    """Test09 Uenv().getenv"""
    result = Uenv(envl).getenv(keystr)
    assert result == expected


# def test_10_setenv(self):
#     """Test10 Uenv().setenv"""
#     envt = 'HOME=/home/user'
#     result = {'HOME': '/home/user',
#                 'LANG': 'en_US.UTF-8'}
#     uenv = Uenv(envt)
#     uenv.setenv('LANG', 'en_US.UTF-8')
#     self.assertEqual(uenv.env, result)

# def test_11_unsetenv(self):
#     """Test11 Uenv().unsetenv"""
#     envt = 'HOME=/home/user'
#     result = {'HOME': '/home/user'}
#     uenv = Uenv(envt)
#     uenv.setenv('LANG', 'en_US.UTF-8')

#     uenv.unsetenv('LANG')
#     self.assertEqual(uenv.env, result)

# def test_12_list(self):
#     """Test12 Uenv().list"""
#     envt = 'HOME=/home/user'
#     result = ['LANG=en_US.UTF-8', envt]
#     uenv = Uenv(envt)
#     uenv.setenv('LANG', 'en_US.UTF-8')
#     self.assertEqual(uenv.list().sort(), result.sort())

# def test_13_dict(self):
#     """Test13 Uenv().dict"""
#     envt = 'HOME=/home/user'
#     result = {'HOME': '/home/user',
#                 'LANG': 'en_US.UTF-8'}
#     uenv = Uenv(envt)
#     uenv.setenv('LANG', 'en_US.UTF-8')
#     self.assertEqual(uenv.dict(), result)

# def test_14_keys(self):
#     """Test14 Uenv().keys"""
#     envt = 'HOME=/home/user'
#     result = {'HOME': None, 'LANG': None}
#     uenv = Uenv(envt)
#     uenv.setenv('LANG', 'en_US.UTF-8')
#     self.assertEqual(uenv.keys(), result.keys())
