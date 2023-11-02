#!/usr/bin/env python
"""
udocker unit tests: ExecutionMode
"""
import os
import random

import pytest

from udocker.engine.execmode import ExecutionMode
from udocker.engine.fakechroot import FakechrootEngine
from udocker.engine.proot import PRootEngine
from udocker.engine.runc import RuncEngine
from udocker.engine.singularity import SingularityEngine
from udocker.helper.elfpatcher import ElfPatcher
from udocker.utils.fileutil import FileUtil

TMP_FOLDER = "/tmp"


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker):
    mocker_localrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mocker_localrepo._container_id = container_id
    return mocker_localrepo


@pytest.fixture
def exec_mode(mocker, localrepo, container_id):
    mocker.patch('udocker.container.localrepo.LocalRepository.cd_container', return_value=TMP_FOLDER)
    mocker_execution_mode = ExecutionMode(localrepo, container_id)
    return mocker_execution_mode


@pytest.fixture
def logger(mocker):
    mocker_logger = mocker.patch('udocker.engine.execmode.LOG')
    return mocker_logger


def test_01_init(exec_mode, localrepo, container_id):
    """Test01 ExecutionMode() constructor."""
    localrepo.cd_container.return_value = "/tmp"

    assert exec_mode.localrepo == localrepo
    assert exec_mode.container_id == container_id
    assert exec_mode.container_dir == TMP_FOLDER
    assert exec_mode.container_root == TMP_FOLDER + "/ROOT"
    assert exec_mode.container_execmode == TMP_FOLDER + "/execmode"
    assert exec_mode.container_orig_root == TMP_FOLDER + "/root.path"
    assert exec_mode.exec_engine is None
    assert exec_mode.force_mode is None
    assert exec_mode.valid_modes == ("P1", "P2", "F1", "F2", "F3", "F4", "R1", "R2", "R3", "S1")


@pytest.mark.parametrize('expected', ["P1", "P2", "F1", "F2", "F3", "F4", "R1", "R2", "R3", "S1"])
def test_02_get_mode(mocker, exec_mode, expected):
    """Test02 ExecutionMode().get_mode."""
    # forced mode
    exec_mode.force_mode = "P2"
    assert exec_mode.get_mode() == "P2"

    # selected mode
    exec_mode.force_mode = None
    mocker_fileutil = mocker.patch.object(FileUtil, 'getdata', return_value=mocker.Mock())
    mocker_fileutil.return_value.strip.return_value = expected
    assert exec_mode.get_mode() == expected

    # default mode
    mocker_fileutil.return_value.strip.return_value = None
    assert exec_mode.get_mode() == "P1"


@pytest.mark.parametrize('mode, prev_mode, mock_return_values, force, expected, error_msg', [
    # Successful mode transitions
    ("P1", "F3", {'restore_ld': True, 'restore_binaries': True}, False, True, None),
    ("F2", "P1", {'restore_ld': True, 'restore_binaries': True}, False, False, "container setup failed"),
    ("R3", "S1", {'restore_ld': True, 'restore_binaries': True}, False, True, None),

    # force flag impact on failed restore
    ("F2", "F3", {'restore_ld': False, 'restore_binaries': False}, True, True, None),
    ("F3", "P1", {'restore_ld': False, 'restore_binaries': False}, True, True, None),

    # invalid modes
    ("NOMODE", "F4", {'restore_ld': True, 'restore_binaries': True}, False, False, "invalid execmode: %s"),

    # mode transition with no operation needed
    ("P1", "P1", {'restore_ld': True, 'restore_binaries': True}, False, True, None),

    # transitions resulting in failure due to failed restoration
    ("P1", "F3", {'restore_ld': False, 'restore_binaries': False}, False, False, "container setup failed"),
    ("F2", "F3", {'restore_ld': False, 'restore_binaries': False}, False, False, "container setup failed"),

    # failure in dependencies like FileUtil
    ("F2", "P1", {'restore_ld': True, 'restore_binaries': True, 'links_conv': False}, False, False,
     "container setup failed"),

    # success filebind.restore()
    ("P1", "R1", {'restore_ld': True, 'restore_binaries': True}, False, True, None),
    ("F4", "F3", {'restore_ld': True, 'restore_binaries': True}, False, True, None),
    ("F3", "F4", {'restore_ld': True, 'restore_binaries': True}, False, True, None),

])
def test_03_set_mode(mocker, exec_mode, logger, mode, prev_mode, mock_return_values, force, expected, error_msg):
    """Test03 ExecutionMode().set_mode."""
    mocker.patch.object(ElfPatcher, 'restore_ld', return_value=mock_return_values['restore_ld'])
    mocker.patch.object(ElfPatcher, 'restore_binaries', return_value=mock_return_values['restore_binaries'])
    mocker.patch.object(ElfPatcher, 'get_ld_libdirs')
    mocker.patch.object(FileUtil, 'links_conv', return_value=mock_return_values.get('links_conv', True))

    mocker.patch.object(exec_mode, 'get_mode', return_value=prev_mode)
    mocker.patch.object(os.path, 'exists', return_value=True)
    mocker.patch.object(os.path, 'isdir', return_value=True)

    status = exec_mode.set_mode(xmode=mode, force=force)
    assert status == expected

    if error_msg:
        logger.error.assert_called_with(error_msg, mode) if '%s' in error_msg else logger.error.assert_called_with(
            error_msg)
    else:
        logger.error.assert_not_called()


@pytest.mark.parametrize('mode,expected', [
    ("P1", PRootEngine),
    ("P2", PRootEngine),
    ("F1", FakechrootEngine),
    ("F2", FakechrootEngine),
    ("F3", FakechrootEngine),
    ("F4", FakechrootEngine),
    ("R1", RuncEngine),
    ("R2", RuncEngine),
    ("R3", RuncEngine),
    ("S1", SingularityEngine),
])
def test_04_get_engine(mocker, exec_mode, mode, expected):
    """Test04 ExecutionMode().get_engine."""
    mocker.patch.object(exec_mode, 'get_mode', return_value=mode)
    exec_engine = exec_mode.get_engine()
    assert isinstance(exec_engine, expected)
    assert exec_mode.exec_engine == exec_engine
