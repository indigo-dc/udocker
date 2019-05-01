#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: UdockerCLI
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

sys.path.append('.')

from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.cli import UdockerCLI

if sys.version_info[0] >= 3:
    BUILTIN = "builtins"
else:
    BUILTIN = "__builtin__"

BOPEN = BUILTIN + '.open'


class UdockerCLITestCase(TestCase):
    """Test UdockerTestCase() command line interface."""

    def setUp(self):
        self.conf = Config().getconf()
        self.conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        self.conf['cmd'] = "/bin/bash"
        self.conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                                ["taskset", "-c", "%s", ])
        self.conf['valid_host_env'] = "HOME"
        self.conf['username'] = "user"
        self.conf['userhome'] = "/"
        self.conf['oskernel'] = "4.8.13"
        self.conf['location'] = ""
        self.conf['keystore'] = "KEYSTORE"
        self.local = LocalRepository(self.conf)

    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    def test_01_init(self, mock_dioapi, mock_dlocapi, mock_ks):
        """Test UdockerCLI() constructor."""

        # Test self.conf['keystore'] starts with /
        self.conf['keystore'] = "/xxx"
        udoc = UdockerCLI(self.local, self.conf)
        self.assertTrue(mock_dioapi.called)
        self.assertTrue(mock_dlocapi.called)
        self.assertTrue(mock_ks.called_with(self.conf['keystore']))
        mock_ks.reset_mock()

        # Test self.conf['keystore'] does not starts with /
        self.conf['keystore'] = "xx"
        udoc = UdockerCLI(self.local, self.conf)
        self.assertTrue(mock_ks.called_with(self.conf['keystore']))

    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_02__check_imagespec(self, mock_msg, mock_dioapi,
                                 mock_dlocapi, mock_ks):
        """Test UdockerCLI()._check_imagespec()."""

        mock_msg.level = 0
        mock_dioapi.is_repo_name = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc._check_imagespec("")
        self.assertEqual(status, (None, None))

        mock_dioapi.is_repo_name = False
        status = udoc._check_imagespec("AAA")
        self.assertEqual(status, ("AAA", "latest"))

        mock_dioapi.is_repo_name = False
        status = udoc._check_imagespec("AAA:45")
        self.assertEqual(status, ("AAA", "45"))


if __name__ == '__main__':
    main()
