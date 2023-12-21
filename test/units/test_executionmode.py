#!/usr/bin/env python
"""
udocker unit tests: ExecutionMode
"""
import os
import random

import pytest

from udocker.config import Config
from udocker.engine.execmode import ExecutionMode
from udocker.engine.fakechroot import FakechrootEngine
from udocker.engine.proot import PRootEngine
from udocker.engine.runc import RuncEngine
from udocker.engine.singularity import SingularityEngine
from udocker.helper.elfpatcher import ElfPatcher
from udocker.helper.hostinfo import HostInfo
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


@pytest.mark.parametrize("arch, xmode, expected", [
    ("x86_64", "P1", "P1"),
    ("unknown", None, "R2"),
])
def test_03_get_mode(mocker, exec_mode, arch, xmode, expected):
    """Test03 ExecutionMode().get_mode."""
    mocker_fileutil = mocker.patch.object(FileUtil, 'getdata', return_value=mocker.Mock())
    mocker_fileutil.return_value.strip.return_value = xmode
    mocker.patch.object(Config, 'conf', {'override_default_execution_mode': None,
                                         'default_execution_modes': {"x86_64": "P1", "DEFAULT": "R2"},
                                         'tmpdir': TMP_FOLDER})
    mocker.patch.object(HostInfo, 'arch', return_value=arch)

    if xmode is not None:
        mocker.patch.dict(Config.conf['default_execution_modes'], {arch: xmode})
    elif arch is not None and arch != "unknown":
        mocker.patch.dict(Config.conf['default_execution_modes'], {}, clear=True)
    assert exec_mode.get_mode() == expected


@pytest.mark.parametrize('mode, prev_mode, mock_return_values, force, expected, error_msg', [
    ("P1", "F3", {'restore_ld': True, 'restore_binaries': True}, False, True, None),
    ("F2", "P1", {'restore_ld': True, 'restore_binaries': True}, False, False, "container setup failed"),
    ("R3", "S1", {'restore_ld': True, 'restore_binaries': True}, False, True, None),
    ("F2", "F3", {'restore_ld': False, 'restore_binaries': False}, True, True, None),
    ("F3", "P1", {'restore_ld': False, 'restore_binaries': False}, True, True, None),
    ("NOMODE", "F4", {'restore_ld': True, 'restore_binaries': True}, False, False, "invalid execmode: %s"),
    ("P1", "P1", {'restore_ld': True, 'restore_binaries': True}, False, True, None),
    ("P1", "F3", {'restore_ld': False, 'restore_binaries': False}, False, False, "container setup failed"),
    ("F2", "F3", {'restore_ld': False, 'restore_binaries': False}, False, False, "container setup failed"),
    ("F2", "P1", {'restore_ld': True, 'restore_binaries': True, 'links_conv': False}, False, False,
     "container setup failed"),
    ("P1", "R1", {'restore_ld': True, 'restore_binaries': True}, False, True, None),
    ("F4", "F3", {'restore_ld': True, 'restore_binaries': True}, False, True, None),
    ("F3", "F4", {'restore_ld': True, 'restore_binaries': True}, False, True, None),

])
def test_04_set_mode(mocker, exec_mode, logger, mode, prev_mode, mock_return_values, force, expected, error_msg):
    """Test04 ExecutionMode().set_mode."""
    mocker.patch.object(ElfPatcher, 'restore_ld', return_value=mock_return_values['restore_ld'])
    mocker.patch.object(ElfPatcher, 'restore_binaries', return_value=mock_return_values['restore_binaries'])
    mocker.patch.object(ElfPatcher, 'get_ld_libdirs')
    mocker.patch.object(FileUtil, 'links_conv', return_value=mock_return_values.get('links_conv', True))

    mocker.patch.object(exec_mode, 'get_mode', return_value=prev_mode)
    mocker.patch.object(os.path, 'exists', return_value=True)

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
def test_05_get_engine(mocker, exec_mode, mode, expected):
    """Test05 ExecutionMode().get_engine."""
    mocker.patch.object(exec_mode, 'get_mode', return_value=mode)
    exec_engine = exec_mode.get_engine()
    assert isinstance(exec_engine, expected)
    assert exec_mode.exec_engine == exec_engine
