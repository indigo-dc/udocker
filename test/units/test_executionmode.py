#!/usr/bin/env python
"""
udocker unit tests: ExecutionMode
"""
import pytest
import random
import mock
from udocker.engine.execmode import ExecutionMode
from udocker.engine.proot import PRootEngine
from udocker.engine.runc import RuncEngine
from udocker.engine.fakechroot import FakechrootEngine
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
def localrepo_cd_container(mocker):
    cd_container = mocker.patch('udocker.container.localrepo.LocalRepository.cd_container')
    cd_container.return_value = TMP_FOLDER
    return cd_container


@pytest.fixture
def execution_mode(localrepo, container_id, localrepo_cd_container):
    localrepo_cd_container.return_value = TMP_FOLDER
    mocker_execution_mode = ExecutionMode(localrepo, container_id)
    return mocker_execution_mode


@pytest.fixture
def mock_elfp(mocker):
    mocker_elfp = mocker.patch('udocker.engine.execmode.ElfPatcher')
    return mocker_elfp


@pytest.fixture
def mock_fbind_setup(mocker):
    mocker_fbindsetup = mocker.patch('udocker.utils.filebind.FileBind.setup')
    return mocker_fbindsetup


@pytest.fixture
def mock_getdata(mocker):
    mocker_getdata = mocker.patch('udocker.utils.fileutil.FileUtil.getdata')
    return mocker_getdata


@pytest.fixture
def mock_getmode(mocker):
    mocker_getmode = mocker.patch('udocker.engine.execmode.ExecutionMode.get_mode')
    return mocker_getmode


@pytest.fixture
def mock_logger(mocker):
    mocker_logger = mocker.patch('udocker.engine.execmode.LOG')
    return mocker_logger


@pytest.fixture
def mock_futil_linksconv(mocker):
    mocker_links_conv = mocker.patch('udocker.utils.fileutil.FileUtil.links_conv')
    return mocker_links_conv


@pytest.fixture
def mock_filebind(mocker):
    mocker_fbind = mocker.patch('udocker.engine.execmode.FileBind')
    return mocker_fbind


def test_01_init(execution_mode, localrepo, container_id):
    """Test01 ExecutionMode() constructor."""
    localrepo.cd_container.return_value = "/tmp"

    assert execution_mode.localrepo == localrepo
    assert execution_mode.container_id == container_id
    assert execution_mode.container_dir == TMP_FOLDER
    assert execution_mode.container_root == TMP_FOLDER + "/ROOT"
    assert execution_mode.container_execmode == TMP_FOLDER + "/execmode"
    assert execution_mode.container_orig_root == TMP_FOLDER + "/root.path"
    assert execution_mode.exec_engine is None
    assert execution_mode.force_mode is None
    assert execution_mode.valid_modes == ("P1", "P2", "F1", "F2", "F3", "F4", "R1", "R2", "R3", "S1")


@pytest.mark.parametrize('expected', ["P1", "P2", "F1", "F2", "F3", "F4", "R1", "R2", "R3", "S1"])
def test_02_get_mode(execution_mode, mock_getdata, expected):
    """Test02 ExecutionMode().get_mode."""
    execution_mode.force_mode = "P2"
    status = execution_mode.get_mode()
    assert status == "P2"

    execution_mode.force_mode = None
    mock_getdata.return_value.strip.return_value = expected
    status = execution_mode.get_mode()
    assert status == expected

    mock_getdata.return_value.strip.return_value = None
    status = execution_mode.get_mode()
    assert status == "P1"


set_mode_data = (
    ("P1", "P1", [], True, True), ("P1", "P1", [], False, True),
    ("P1", "P2", [], True, True), ("P1", "P2", [], False, True),
    ("P1", "F3", [], True, True), ("P1", "F3", [mock.call("container setup failed")], False, False),
    ("P1", "R3", [], True, True), ("P1", "R3", [], False, True),
    ("R3", "S1", [], True, True), ("R3", "S1", [], False, True),
    ("F2", "F3", [], True, True), ("F2", "F3", [mock.call('container setup failed')], False, False),
    ("F2", "P1", [], True, True), ("F2", "P1", [], False, True),
    ("F3", "P1", [], True, True), ("F3", "P1", [], False, True),
    ("F3", "F4", [], True, True), ("F3", "F4", [], False, True),
    ("F3", "F4", [], True, True), ("F3", "F4", [], False, True),
    ("NOMODE", "F4", [mock.call('invalid execmode: %s', 'NOMODE')], True, False),
    ("NOMODE", "F4", [mock.call('invalid execmode: %s', 'NOMODE')], False, False),
)


@pytest.mark.parametrize('mode,prev_mode,msg,force,expected', set_mode_data)
def test_03_set_mode(execution_mode, mock_getmode, mock_elfp, mock_fbind_setup, mock_getdata, mock_filebind,
                     mock_futil_linksconv, mock_logger, mode, prev_mode, msg, force, expected):
    """Test03 ExecutionMode().set_mode."""
    #status = futil.putdata(os.path.realpath(self.container_root), "w")  FIXME: check this
    mock_elfp.return_value.restore_ld.return_value = False
    mock_elfp.return_value.restore_binaries.return_value = False

    mock_logger.reset_mock()
    mock_getmode.return_value = prev_mode
    status = execution_mode.set_mode(xmode=mode, force=force)
    assert status is expected
    assert mock_logger.error.called == (not expected)
    assert mock_logger.error.call_args_list == msg


get_engine_data = (
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
)


@pytest.mark.parametrize('mode,expected', get_engine_data)
def test_04_get_engine(execution_mode, mock_getmode, mode, expected):
    """Test04 ExecutionMode().get_engine."""
    mock_getmode.return_value = mode
    exec_engine = execution_mode.get_engine()
    assert isinstance(exec_engine, expected)
