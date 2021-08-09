#!/usr/bin/env python
"""
udocker unit tests: ChkSUM
"""

from unittest import TestCase, main
from unittest.mock import patch, Mock, mock_open
from io import BytesIO as strio
from udocker.utils.chksum import ChkSUM

BUILTINS = "builtins"


class ChkSUMTestCase(TestCase):
    """Test ChkSUM()."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('udocker.utils.chksum.hashlib.sha512')
    @patch('udocker.utils.chksum.hashlib.sha256')
    @patch.object(ChkSUM, '_openssl_sha512', autospec=True)
    @patch.object(ChkSUM, '_hashlib_sha512', autospec=True)
    @patch.object(ChkSUM, '_openssl_sha256', autospec=True)
    @patch.object(ChkSUM, '_hashlib_sha256', autospec=True)
    def test_01__init(self, mock_hash256, mock_ossl256,
                      mock_hash512, mock_ossl512,
                      mock_lib256, mock_lib512):
        """Test01 ChkSUM() constructor."""
        mock_hash256.return_value = '123456'
        mock_hash512.return_value = '1234567891011'
        mock_lib256.return_value = True
        mock_lib512.return_value = True
        chksum = ChkSUM()
        self.assertTrue(mock_lib256.called)
        self.assertTrue(mock_lib512.called)
        # self.assertTrue(mock_hash256.called)
        # self.assertTrue(mock_hash512.called)

        # with self.assertRaises(NameError):
        #     ChkSUM()
        #     self.assertTrue(mock_ossl256.called)


    # def test_02__hashlib(self):
    #     """Test02 ChkSUM()._hashlib."""

    # def test_03__hashlib_sha256(self):
    #     """Test03 ChkSUM()._hashlib_sha256."""

    # def test_04__hashlib_sha512(self):
    #     """Test04 ChkSUM()._hashlib_sha512."""

    # def test_05__openssl(self):
    #     """Test05 ChkSUM()._openssl."""

    # def test_06__openssl_sha256(self):
    #     """Test06 ChkSUM()._openssl_sha256."""

    # def test_07__openssl_sha512(self):
    #     """Test07 ChkSUM()._openssl_sha512."""

    # def test_08_sha256(self):
    #     """Test08 ChkSUM().sha256."""

    # def test_09_sha512(self):
    #     """Test09 ChkSUM().sha512."""

    # def test_10_hash(self):
    #     """Test10 ChkSUM().hash."""
    #     sha256sum = (
    #       "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    #     cksum = ChkSUM()
    #     file_data = strio('qwerty')
    #     with patch(BUILTINS + '.open', mock_open()) as mopen:
    #         mopen.return_value.__iter__ = (
    #             lambda self: iter(file_data.readline, ''))
    #         status = cksum.hash("filename", "sha256")
    #         self.assertEqual(status, sha256sum)

    #     sha512sum = ("cf83e1357eefb8bdf1542850d66d8007d620e4050b"
    #                  "5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff831"
    #                  "8d2877eec2f63b931bd47417a81a538327af927da3e")
    #     cksum = ChkSUM()
    #     file_data = strio('qwerty')
    #     with patch(BUILTINS + '.open', mock_open()) as mopen:
    #         mopen.return_value.__iter__ = (
    #             lambda self: iter(file_data.readline, ''))
    #         status = cksum.hash("filename", "sha512")
    #         self.assertEqual(status, sha512sum)


if __name__ == '__main__':
    main()
