#!/usr/bin/env python
"""
udocker unit tests: Uprocess
"""
import logging
from udocker.utils.uprocess import Uprocess, LOG
from udocker.config import Config


def test_01_get_stderr(mocker):
    """Test01 Uprocess().get_stderr() info level."""
    mock_subproc = mocker.patch('udocker.utils.uprocess.subprocess')
    mock_subproc.DEVNULL = -3
    Config().getconf()
    Config.conf['verbose_level'] = logging.INFO
    status = Uprocess().get_stderr()
    assert status == -3


# def test_02_get_stderr(mocker):
#     """Test01 Uprocess().get_stderr() debug level."""
#     mock_subproc = mocker.patch('udocker.utils.uprocess.subprocess')
#     mock_sysstderr = mocker.patch('sys.stderr', return_value=1)
#     mock_subproc.DEVNULL = -3
#     Config().getconf()
#     Config.conf['verbose_level'] = logging.DEBUG
#     status = Uprocess().get_stderr()
#     assert status == 1
#     mock_sysstderr.assert_called()


def test_03_find_inpath(mocker):
    """Test03 Uprocess().find_inpath() empty fname and path."""
    fname = ''
    path = ''
    mock_base = mocker.patch('os.path.basename')
    mock_debug = mocker.patch('udocker.LOG.debug')
    status = Uprocess().find_inpath(fname, path)
    assert status == ''
    mock_base.assert_not_called()
    mock_debug.assert_not_called()


def test_04_find_inpath(mocker):
    """Test04 Uprocess().find_inpath() fname and path not empty."""
    fname = 'ls'
    path = 'PATH=/usr/bin'
    full_path = '/usr/bin/ls'
    mock_base = mocker.patch('os.path.basename', return_value=fname)
    mock_debug = mocker.patch('udocker.LOG.debug')
    mock_lexists = mocker.patch('os.path.lexists', return_value=True)
    status = Uprocess().find_inpath(fname, path)
    assert status == full_path
    mock_base.assert_called()
    mock_debug.assert_called()
    mock_lexists.assert_called()


def test_05_find_inpath(mocker):
    """Test05 Uprocess().find_inpath() fname and path is multiple."""
    fname = 'ls'
    path = 'PATH=/usr/bin:/bin'
    full_path = '/bin/ls'
    mock_base = mocker.patch('os.path.basename', return_value=fname)
    mock_debug = mocker.patch('udocker.LOG.debug')
    mock_lexists = mocker.patch('os.path.lexists', side_effect=[False, True])
    status = Uprocess().find_inpath(fname, path)
    assert status == full_path
    mock_base.assert_called()
    mock_debug.assert_called()
    mock_lexists.assert_called()


def test_06_check_output(mocker):
    """Test06 Uprocess().check_output() raise OSError."""
    mock_subp_chkout = mocker.patch('subprocess.check_output', side_effect=OSError("fail"))
    status = Uprocess().check_output()
    assert status == ""
    mock_subp_chkout.assert_called()


def test_07_check_output(mocker):
    """Test06 Uprocess().check_output()."""
    chkout = b"some_check"
    mock_subp_chkout = mocker.patch('subprocess.check_output', return_value=chkout)
    status = Uprocess().check_output()
    assert status == "some_check"
    mock_subp_chkout.assert_called()


def test_08_get_output(mocker):
    """Test08 Uprocess().get_output()."""
    mock_getenv = mocker.patch('os.getenv', return_value='/usr/bin')
    mock_findinpath = mocker.patch.object(Uprocess, 'find_inpath', return_value='/usr/bin/ls')
    mock_chkout = mocker.patch.object(Uprocess, 'check_output', return_value='OUTPUT')

    status = Uprocess().check_output('/usr/bin/ls')
    assert status == "OUTPUT"
    mock_getenv.assert_not_called()
    mock_findinpath.assert_not_called()
    mock_chkout.assert_called()




    # @patch.object(Uprocess, 'find_inpath')
    # @patch('udocker.utils.uprocess.subprocess.call')
    # def test_05_call(self, mock_subcall, mock_find):
    #     """Test05 Uprocess().call()."""
    #     mock_find.return_value = '/bin/ls'
    #     mock_subcall.return_value = 0
    #     uproc = Uprocess()
    #     status = uproc.call('/bin/ls')
    #     self.assertEqual(status, 0)

    # # @patch.object(Uprocess, 'find_inpath')
    # # @patch('udocker.utils.uprocess.subprocess.Popen')
    # # def test_06_pipe(self, mock_popen, mock_find):
    # #     """Test06 Uprocess().pipe()."""
    # #     mock_find.side_effect = ["/bin/ls", "/usr/bin/grep"]
