#!/usr/bin/env python
"""
udocker unit tests: ExecutionMode
"""
import random

import mock
import pytest

from udocker.engine.execmode import ExecutionMode
from udocker.engine.fakechroot import FakechrootEngine
from udocker.engine.proot import PRootEngine
from udocker.engine.runc import RuncEngine
from udocker.engine.singularity import SingularityEngine

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


@pytest.fixture
def mock_elfp(mocker):
    mocker_elfp = mocker.patch('udocker.engine.execmode.ElfPatcher')
    return mocker_elfp


@pytest.fixture
def mock_fileutil(mocker):
    mock_fileutil = mocker.patch('udocker.engine.execmode.FileUtil')
    return mock_fileutil


@pytest.fixture
def mock_filebind(mocker):
    mocker_fbind = mocker.patch('udocker.engine.execmode.FileBind')
    return mocker_fbind


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
def test_02_get_mode(exec_mode, mock_fileutil, expected):
    """Test02 ExecutionMode().get_mode."""
    # forced mode
    exec_mode.force_mode = "P2"
    assert exec_mode.get_mode() == "P2"

    # selected mode
    exec_mode.force_mode = None
    mock_fileutil.return_value.getdata.return_value.strip.return_value = expected
    assert exec_mode.get_mode() == expected

    # default mode
    mock_fileutil.return_value.getdata.return_value.strip.return_value = None
    assert exec_mode.get_mode() == "P1"


@pytest.mark.parametrize('mode,prev_mode,msg,force,expected', [
    ("P1", "P1", [], True, True), ("P1", "P1", [], False, True),
    ("P1", "P2", [], True, True), ("P1", "P2", [], False, True),
    ("P1", "F3", [], True, True), ("P1", "F3", [mock.call("container setup failed")], False, False),
    ("P1", "R3", [], True, True), ("P1", "R3", [], False, True),
    ("R3", "S1", [], True, True), ("R3", "S1", [], False, True),
    ("F2", "F3", [], True, True), ("F2", "F3", [mock.call('container setup failed')], False, False),
    ("F2", "P1", [], True, True), ("F2", "P1", [], False, True),
    ("F3", "P1", [], True, True), ("F3", "P1", [], False, True),
    ("F3", "F4", [], True, True), ("F3", "F4", [], False, True),
    ("NOMODE", "F4", [mock.call('invalid execmode: %s', 'NOMODE')], True, False),
    ("NOMODE", "F4", [mock.call('invalid execmode: %s', 'NOMODE')], False, False),
])
def test_03_set_mode(mocker, exec_mode, logger, mock_elfp, mock_fileutil, mode, prev_mode, msg, force, expected):
    """Test03 ExecutionMode().set_mode."""
    mock_elfp.return_value.restore_ld.return_value = False
    mock_elfp.return_value.restore_binaries.return_value = False

    logger.reset_mock()
    mocker.patch.object(exec_mode, 'get_mode', return_value=prev_mode)
    mocker.patch.object(mock_fileutil, 'links_conv')

    status = exec_mode.set_mode(xmode=mode, force=force)
    assert status is expected
    assert logger.error.called == (not expected)
    assert logger.error.call_args_list == msg


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
