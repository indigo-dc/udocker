#!/usr/bin/env python
"""
udocker unit tests: Uenv
"""

from unittest import TestCase, main
from udocker.utils.uenv import Uenv


class UenvTestCase(TestCase):
    """Test Uenv()."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test01 Uenv() constructor"""
        envt = 'HOME=/home/user'
        result = {'HOME': '/home/user'}
        self.assertEqual(Uenv(envt).env, result)

    # def test_02__iter__(self):
    #     """Test02 Uenv().__iter__"""

    def test_03__len__(self):
        """Test03 Uenv().__len__"""
        envt = 'HOME=/home/user'
        uenv = Uenv(envt)
        uenv.env = {'HOME': '/home/user', 'LANG': 'en_US.UTF-8'}
        self.assertEqual(uenv.__len__(), 2)

    def test_04_append(self):
        """Test04 Uenv().append"""
        envt = 'HOME=/home/user'
        env_app = 'LANG=en_US.UTF-8'
        result = {'HOME': '/home/user', 'LANG': 'en_US.UTF-8'}
        uenv = Uenv(envt)
        uenv.append(env_app)
        self.assertEqual(uenv.env, result)

    def test_05_appendif(self):
        """Test05 Uenv().appendif"""
        envt = 'HOME=/home/user'
        env_app = 'LANG=en_US.UTF-8'
        result = {'HOME': '/home/user', 'LANG': 'en_US.UTF-8'}
        uenv = Uenv(envt)
        uenv.appendif(env_app)
        self.assertEqual(uenv.env, result)

        envt = 'HOME=/home/user'
        env_app = envt
        result = {'HOME': '/home/user'}
        uenv = Uenv(envt)
        uenv.appendif(env_app)
        self.assertEqual(uenv.env, result)

    def test_06_extend(self):
        """Test06 Uenv().extend"""
        envt = 'HOME=/home/user'
        envlist = ['LANG=en_US.UTF-8', 'USER=myuser']
        result = {'HOME': '/home/user',
                  'LANG': 'en_US.UTF-8',
                  'USER': 'myuser'}
        uenv = Uenv(envt)
        uenv.extend(envlist)
        self.assertEqual(uenv.env, result)

        envdict = {'LANG': 'en_US.UTF-8', 'USER': 'myuser'}
        uenv = Uenv(envt)
        uenv.extend(envdict)
        self.assertEqual(uenv.env, result)

    def test_07_extendif(self):
        """Test07 Uenv().extendif"""
        envt = 'HOME=/home/user'
        envlist = ['LANG=en_US.UTF-8', 'USER=myuser']
        result = {'HOME': '/home/user',
                  'LANG': 'en_US.UTF-8',
                  'USER': 'myuser'}
        uenv = Uenv(envt)
        uenv.extendif(envlist)
        self.assertEqual(uenv.env, result)

        envdict = {'LANG': 'en_US.UTF-8', 'USER': 'myuser'}
        uenv = Uenv(envt)
        uenv.extendif(envdict)
        self.assertEqual(uenv.env, result)

        envt = 'HOME=/home/user'
        envlist = ['LANG=en_US.UTF-8', 'HOME=/home/user']
        result = {'HOME': '/home/user',
                  'LANG': 'en_US.UTF-8'}
        uenv = Uenv(envt)
        uenv.extendif(envlist)
        self.assertEqual(uenv.env, result)

    def test_08_add(self):
        """Test08 Uenv().add"""
        envt = 'HOME=/home/user'
        envlist = ['LANG=en_US.UTF-8']
        result = {'HOME': '/home/user',
                  'LANG': 'en_US.UTF-8'}
        uenv = Uenv(envt)
        uenv.add(envlist)
        self.assertEqual(uenv.env, result)

        envt = 'HOME=/home/user'
        envstr = 'LANG=en_US.UTF-8'
        result = {'HOME': '/home/user',
                  'LANG': 'en_US.UTF-8'}
        uenv = Uenv(envt)
        uenv.add(envstr)
        self.assertEqual(uenv.env, result)

    def test_09_getenv(self):
        """Test09 Uenv().getenv"""
        envt = 'HOME=/home/user'
        uenv = Uenv(envt)
        uenv.getenv('HOME')
        self.assertEqual(uenv.env, {'HOME': '/home/user'})

    def test_10_setenv(self):
        """Test10 Uenv().setenv"""
        envt = 'HOME=/home/user'
        result = {'HOME': '/home/user',
                  'LANG': 'en_US.UTF-8'}
        uenv = Uenv(envt)
        uenv.setenv('LANG', 'en_US.UTF-8')
        self.assertEqual(uenv.env, result)

    def test_11_unsetenv(self):
        """Test11 Uenv().unsetenv"""
        envt = 'HOME=/home/user'
        result = {'HOME': '/home/user'}
        uenv = Uenv(envt)
        uenv.setenv('LANG', 'en_US.UTF-8')

        uenv.unsetenv('LANG')
        self.assertEqual(uenv.env, result)

    def test_12_list(self):
        """Test12 Uenv().list"""
        envt = 'HOME=/home/user'
        result = ['LANG=en_US.UTF-8', envt]
        uenv = Uenv(envt)
        uenv.setenv('LANG', 'en_US.UTF-8')
        self.assertEqual(uenv.list().sort(), result.sort())

    def test_13_dict(self):
        """Test13 Uenv().dict"""
        envt = 'HOME=/home/user'
        result = {'HOME': '/home/user',
                  'LANG': 'en_US.UTF-8'}
        uenv = Uenv(envt)
        uenv.setenv('LANG', 'en_US.UTF-8')
        self.assertEqual(uenv.dict(), result)

    def test_14_keys(self):
        """Test14 Uenv().keys"""
        envt = 'HOME=/home/user'
        result = {'HOME': None, 'LANG': None}
        uenv = Uenv(envt)
        uenv.setenv('LANG', 'en_US.UTF-8')
        self.assertEqual(uenv.keys(), result.keys())


if __name__ == '__main__':
    main()
