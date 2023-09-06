#!/usr/bin/env python
"""
udocker unit tests: LocalFileAPI
"""
import pytest
from udocker.localfile import LocalFileAPI


@pytest.fixture
def lrepo(mocker):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    return mock_lrepo


@pytest.fixture
def lfileapi(mocker, lrepo):
    mock_commonfapi = mocker.patch('udocker.commonlocalfile.CommonLocalFileApi')
    return LocalFileAPI(lrepo)


def test_01_load(mocker, lfileapi):
    """Test01 LocalFileAPI().load. image path does not exist."""
    mock_exists = mocker.patch('udocker.localfile.os.path.exists', return_value=False)
    mock_futilmktmp = mocker.patch('udocker.localfile.FileUtil.mktmp')
    status = lfileapi.load('imgfile')
    assert not status
    mock_exists.assert_called()
    mock_futilmktmp.assert_not_called()


def test_02_load(mocker, lfileapi):
    """Test02 LocalFileAPI().load. image path exist. os.mkdir raises OSError"""
    mock_exists = mocker.patch('udocker.localfile.os.path.exists', return_value=True)
    mock_futilmktmp = mocker.patch('udocker.localfile.FileUtil.mktmp', return_value='/tmp/imgdir')
    mock_mkdir = mocker.patch('udocker.localfile.os.makedirs', side_effect=OSError)
    mock_untar = mocker.patch.object(LocalFileAPI, '_untar_saved_container', return_value=False)
    status = lfileapi.load('imgfile')
    assert not status
    mock_exists.assert_called()
    mock_futilmktmp.assert_called()
    mock_mkdir.assert_called()
    mock_untar.assert_not_called()


def test_03_load(mocker, lfileapi):
    """Test03 LocalFileAPI().load. image path exist. os.mkdir OK, untar False"""
    mock_exists = mocker.patch('udocker.localfile.os.path.exists', return_value=True)
    mock_futilmktmp = mocker.patch('udocker.localfile.FileUtil.mktmp', return_value='/tmp/imgdir')
    mock_mkdir = mocker.patch('udocker.localfile.os.makedirs')
    mock_untar = mocker.patch.object(LocalFileAPI, '_untar_saved_container', return_value = False)
    mock_remove = mocker.patch('udocker.localfile.FileUtil.remove')
    mock_imgtype = mocker.patch.object(LocalFileAPI, '_get_imagedir_type')
    status = lfileapi.load('imgfile')
    assert not status
    mock_exists.assert_called()
    mock_futilmktmp.assert_called()
    mock_mkdir.assert_called()
    mock_untar.assert_called()
    mock_remove.assert_called()
    mock_imgtype.assert_not_called()


def test_04_load(mocker, lfileapi):
    """Test04 LocalFileAPI().load. image path exist. os.mkdir OK, untar True, imagetype Docker"""
    mock_exists = mocker.patch('udocker.localfile.os.path.exists', return_value=True)
    mock_futilmktmp = mocker.patch('udocker.localfile.FileUtil.mktmp', return_value='/tmp/imgdir')
    mock_mkdir = mocker.patch('udocker.localfile.os.makedirs')
    mock_untar = mocker.patch.object(LocalFileAPI, '_untar_saved_container', return_value = True)
    mock_remove = mocker.patch('udocker.localfile.FileUtil.remove')
    mock_imgtype = mocker.patch.object(LocalFileAPI, '_get_imagedir_type', return_value = "Docker")
    mock_dockerload = mocker.patch('udocker.localfile.DockerLocalFileAPI.load',
                                   return_value = ['docker-repo1', 'docker-repo2'])
    mock_ociload = mocker.patch('udocker.localfile.OciLocalFileAPI.load')
    status = lfileapi.load('imgfile')
    assert status == ['docker-repo1', 'docker-repo2']
    mock_exists.assert_called()
    mock_futilmktmp.assert_called()
    mock_mkdir.assert_called()
    mock_untar.assert_called()
    mock_remove.assert_called()
    mock_imgtype.assert_called()
    mock_dockerload.assert_called()
    mock_ociload.assert_not_called()


def test_05_load(mocker, lfileapi):
    """Test05 LocalFileAPI().load. image path exist. os.mkdir OK, untar True, imagetype OCI"""
    mock_exists = mocker.patch('udocker.localfile.os.path.exists', return_value=True)
    mock_futilmktmp = mocker.patch('udocker.localfile.FileUtil.mktmp', return_value='/tmp/imgdir')
    mock_mkdir = mocker.patch('udocker.localfile.os.makedirs')
    mock_untar = mocker.patch.object(LocalFileAPI, '_untar_saved_container', return_value=True)
    mock_remove = mocker.patch('udocker.localfile.FileUtil.remove')
    mock_imgtype = mocker.patch.object(LocalFileAPI, '_get_imagedir_type', return_value="OCI")
    mock_dockerload = mocker.patch('udocker.localfile.DockerLocalFileAPI.load')
    mock_ociload = mocker.patch('udocker.localfile.OciLocalFileAPI.load',
                                return_value=['OCI-repo1', 'OCI-repo2'])
    status = lfileapi.load('imgfile')
    assert status == ['OCI-repo1', 'OCI-repo2']
    mock_exists.assert_called()
    mock_futilmktmp.assert_called()
    mock_mkdir.assert_called()
    mock_untar.assert_called()
    mock_remove.assert_called()
    mock_imgtype.assert_called()
    mock_dockerload.assert_not_called()
    mock_ociload.assert_called()


def test_06_load(mocker, lfileapi):
    """Test06 LocalFileAPI().load. image path exist. os.mkdir OK, untar True, imagetype empty"""
    mock_exists = mocker.patch('udocker.localfile.os.path.exists', return_value=True)
    mock_futilmktmp = mocker.patch('udocker.localfile.FileUtil.mktmp', return_value='/tmp/imgdir')
    mock_mkdir = mocker.patch('udocker.localfile.os.makedirs')
    mock_untar = mocker.patch.object(LocalFileAPI, '_untar_saved_container', return_value=True)
    mock_remove = mocker.patch('udocker.localfile.FileUtil.remove')
    mock_imgtype = mocker.patch.object(LocalFileAPI, '_get_imagedir_type', return_value="")
    mock_dockerload = mocker.patch('udocker.localfile.DockerLocalFileAPI.load')
    mock_ociload = mocker.patch('udocker.localfile.OciLocalFileAPI.load')
    status = lfileapi.load('imgfile')
    assert status == []
    mock_exists.assert_called()
    mock_futilmktmp.assert_called()
    mock_mkdir.assert_called()
    mock_untar.assert_called()
    mock_remove.assert_called()
    mock_imgtype.assert_called()
    mock_dockerload.assert_not_called()
    mock_ociload.assert_not_called()


def test_07_save(mocker, lfileapi):
    """Test07 LocalFileAPI().save."""
    mock_dockersave = mocker.patch('udocker.localfile.DockerLocalFileAPI.save', return_value=True)
    status = lfileapi.save(['tag1', 'tag2'], 'imgfile')
    assert status
    mock_dockersave.assert_called()
