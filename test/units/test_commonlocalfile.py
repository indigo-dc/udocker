#!/usr/bin/env python
"""
udocker unit tests: CommonLocalFileApi
"""
import pytest
from udocker.commonlocalfile import CommonLocalFileApi


@pytest.fixture
def lrepo(mocker):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    return mock_lrepo


@pytest.fixture
def clfapi(mocker, lrepo):
    return CommonLocalFileApi(lrepo)


def test_02__move_layer_to_v1repo(mocker, clfapi):
    """Test02 CommonLocalFileApi()._move_layer_to_v1repo(). filepath and layerid empty"""
    layer_id = ""
    filepath = ""
    mock_layersdir = mocker.patch('udocker.container.localrepo.LocalRepository.layersdir')
    status = clfapi._move_layer_to_v1repo(filepath, layer_id)
    assert not status
    mock_layersdir.assert_not_called()


data_in = (("/home/.udocker/12345.json", "12345"),
           ("/home/.udocker/12345.layer.tar", "12345"),
           ("/home/.udocker/12345", "some:12345"))

@pytest.mark.parametrize("fpath,lid", data_in)
def test_03__move_layer_to_v1repo(mocker, clfapi, lrepo, fpath, lid):
    """Test03 CommonLocalFileApi()._move_layer_to_v1repo(). filepath not empty"""
    layer_id = lid
    filepath = fpath
    mock_rename = mocker.patch('os.rename')
    mock_copy = mocker.patch('udocker.commonlocalfile.FileUtil.copyto')
    lrepo.return_value.layersdir = "/home/.udocker"
    lrepo.return_value.add_image_layer.return_value = True

    status = clfapi._move_layer_to_v1repo(filepath, layer_id)
    assert status
    mock_rename.assert_called()
    lrepo.add_image_layer.assert_called()
    mock_copy.assert_not_called()


def test_04__move_layer_to_v1repo(mocker, clfapi, lrepo):
    """Test04 CommonLocalFileApi()._move_layer_to_v1repo(). raises OSError"""
    layer_id = "12345"
    filepath = "/home/.udocker/12345.layer.tar"
    mock_rename = mocker.patch('os.rename', side_effect=OSError("fail"))
    mock_copy = mocker.patch('udocker.commonlocalfile.FileUtil.copyto', return_value=False)
    lrepo.return_value.layersdir = "/home/.udocker"
    lrepo.return_value.add_image_layer.return_value = True

    status = clfapi._move_layer_to_v1repo(filepath, layer_id)
    assert not status
    mock_rename.assert_called()
    lrepo.add_image_layer.assert_not_called()
    mock_copy.assert_called()


def test_05__load_image(clfapi, lrepo):
    """Test05 CommonLocalFileApi()._load_image().cd_imagerepo True"""
    structure = "12345"
    imagerepo = "/home/.udocker/images"
    tag = "v1"
    lrepo.cd_imagerepo.return_value = True

    status = clfapi._load_image(structure, imagerepo, tag)
    assert status == []
    lrepo.cd_imagerepo.assert_called()
    lrepo.setup_imagerepo.assert_not_called()


def test_06__load_image(clfapi, lrepo):
    """Test06 CommonLocalFileApi()._load_image().cd_imagerepo False"""
    structure = "12345"
    imagerepo = "/home/.udocker/images"
    tag = "v1"
    lrepo.cd_imagerepo.return_value = False
    lrepo.setup_imagerepo.return_value = True
    lrepo.setup_tag.return_value = False

    status = clfapi._load_image(structure, imagerepo, tag)
    assert status == []
    lrepo.cd_imagerepo.assert_called()
    lrepo.setup_imagerepo.assert_called()
    lrepo.setup_tag.assert_called()
    lrepo.set_version.assert_not_called()


def test_07__load_image(clfapi, lrepo):
    """Test07 CommonLocalFileApi()._set version False"""
    structure = "12345"
    imagerepo = "/home/.udocker/images"
    tag = "v1"
    lrepo.cd_imagerepo.return_value = False
    lrepo.setup_imagerepo.return_value = True
    lrepo.setup_tag.return_value = True
    lrepo.set_version.return_value = False

    status = clfapi._load_image(structure, imagerepo, tag)
    assert status == []
    lrepo.cd_imagerepo.assert_called()
    lrepo.setup_imagerepo.assert_called()
    lrepo.setup_tag.assert_called()
    lrepo.set_version.assert_called()


def test_08__load_image(mocker, clfapi, lrepo):
    """Test08 CommonLocalFileApi()._set version True"""
    structure = "12345"
    imagerepo = "/home/.udocker/images"
    tag = "v1"
    lrepo.cd_imagerepo.return_value = False
    lrepo.setup_imagerepo.return_value = True
    lrepo.setup_tag.return_value = True
    lrepo.set_version.return_value = True
    mock_imgstep2 = mocker.patch.object(CommonLocalFileApi, '_load_image_step2', return_value=True)

    status = clfapi._load_image(structure, imagerepo, tag)
    assert status
    lrepo.cd_imagerepo.assert_called()
    lrepo.setup_imagerepo.assert_called()
    lrepo.setup_tag.assert_called()
    lrepo.set_version.assert_called()
    mock_imgstep2.assert_called()


def test_09__untar_saved_container(mocker, clfapi):
    """Test09 CommonLocalFileApi()._untar_saved_container()."""
    tarfile = "file.tar"
    destdir = "/home/.udocker/images"
    mock_ucall = mocker.patch('udocker.commonlocalfile.Uprocess.call', return_value=True)

    status = clfapi._untar_saved_container(tarfile, destdir)
    assert not status
    mock_ucall.assert_called()


def test_10_create_container_meta(mocker, clfapi):
    """Test10 CommonLocalFileApi().create_container_meta()."""
    layer_id = "12345"
    comment = "created by my udocker"
    mock_arch = mocker.patch('udocker.commonlocalfile.HostInfo.arch', return_value="x86_64")
    mock_version = mocker.patch('udocker.commonlocalfile.HostInfo.osversion', return_value="8")
    mock_size = mocker.patch('udocker.commonlocalfile.FileUtil.size', return_value=-1)

    status = clfapi.create_container_meta(layer_id, comment)
    assert status["id"] == layer_id
    assert status["comment"] == comment
    assert status["size"] == 0
    mock_arch.assert_called()
    mock_version.assert_called()
    mock_size.assert_called()


def test_11_import_toimage(mocker, clfapi, lrepo):
    """Test11 CommonLocalFileApi().import_toimage(). path exists False"""
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    mock_logerr = mocker.patch('udocker.LOG.error')
    lrepo.setup_imagerepo.return_value = True

    status = clfapi.import_toimage("img.tar", "/images", "v1")
    assert not status
    mock_exists.assert_called()
    mock_logerr.assert_called()
    lrepo.setup_imagerepo.assert_not_called()


def test_12_import_toimage(mocker, clfapi, lrepo):
    """Test12 CommonLocalFileApi().import_toimage(). path exists True"""
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    mock_logerr = mocker.patch('udocker.LOG.error')
    mock_loginf = mocker.patch('udocker.LOG.info')
    lrepo.setup_imagerepo.return_value = True
    lrepo.cd_imagerepo.return_value = '/tag'
    lrepo.setup_tag.return_value = ''

    status = clfapi.import_toimage("img.tar", "/images", "v1")
    assert not status
    mock_exists.assert_called()
    mock_logerr.assert_not_called()
    lrepo.setup_imagerepo.assert_called()
    lrepo.cd_imagerepo.assert_called()
    mock_loginf.assert_called()
    lrepo.setup_tag.assert_not_called()


def test_13_import_toimage(mocker, clfapi, lrepo):
    """Test13 CommonLocalFileApi().import_toimage(). path exists True tag not exist"""
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    mock_logerr = mocker.patch('udocker.LOG.error')
    mock_loginf = mocker.patch('udocker.LOG.info')
    lrepo.setup_imagerepo.return_value = True
    lrepo.cd_imagerepo.return_value = ''
    lrepo.setup_tag.return_value = ''
    lrepo.set_version.return_value = False

    status = clfapi.import_toimage("img.tar", "/images", "v1")
    assert not status
    mock_exists.assert_called()
    mock_logerr.assert_called()
    lrepo.setup_imagerepo.assert_called()
    lrepo.cd_imagerepo.assert_called()
    mock_loginf.assert_not_called()
    lrepo.setup_tag.assert_called()
    lrepo.set_version.assert_not_called()


def test_14_import_toimage(mocker, clfapi, lrepo):
    """Test14 CommonLocalFileApi().import_toimage(). tag exist set version False"""
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    mock_logerr = mocker.patch('udocker.LOG.error')
    mock_loginf = mocker.patch('udocker.LOG.info')
    mock_layerv1 = mocker.patch('udocker.commonlocalfile.Unique.layer_v1')
    lrepo.setup_imagerepo.return_value = True
    lrepo.cd_imagerepo.return_value = ''
    lrepo.setup_tag.return_value = 'tag'
    lrepo.set_version.return_value = False

    status = clfapi.import_toimage("img.tar", "/images", "v1")
    assert not status
    mock_exists.assert_called()
    mock_logerr.assert_called()
    lrepo.setup_imagerepo.assert_called()
    lrepo.cd_imagerepo.assert_called()
    mock_loginf.assert_not_called()
    lrepo.setup_tag.assert_called()
    lrepo.set_version.assert_called()
    mock_layerv1.assert_not_called()


def test_15_import_toimage(mocker, clfapi, lrepo):
    """Test15 CommonLocalFileApi().import_toimage(). set version True copyto False"""
    mock_exists = mocker.patch('os.path.exists', side_effect=[True, False])
    mock_logerr = mocker.patch('udocker.LOG.error')
    mock_loginf = mocker.patch('udocker.LOG.info')
    mock_layerv1 = mocker.patch('udocker.commonlocalfile.Unique.layer_v1', return_value='123')
    mock_rename = mocker.patch('os.rename', return_value=True)
    mock_copy = mocker.patch('udocker.commonlocalfile.FileUtil.copyto', return_value=False)
    lrepo.setup_imagerepo.return_value = True
    lrepo.cd_imagerepo.return_value = ''
    lrepo.setup_tag.return_value = 'tag'
    lrepo.set_version.return_value = True
    lrepo.layersdir.return_value = '/layers'

    status = clfapi.import_toimage("img.tar", "/images", "v1")
    assert not status
    assert mock_exists.call_count == 2
    mock_logerr.assert_called()
    lrepo.setup_imagerepo.assert_called()
    lrepo.cd_imagerepo.assert_called()
    mock_loginf.assert_not_called()
    lrepo.setup_tag.assert_called()
    lrepo.set_version.assert_called()
    mock_layerv1.assert_called()
    mock_rename.assert_called()
    mock_copy.assert_called()


def test_16_import_toimage(mocker, clfapi, lrepo):
    """Test16 CommonLocalFileApi().import_toimage(). return layerid"""
    mock_exists = mocker.patch('os.path.exists', side_effect=[True, True])
    mock_logerr = mocker.patch('udocker.LOG.error')
    mock_loginf = mocker.patch('udocker.LOG.info')
    mock_layerv1 = mocker.patch('udocker.commonlocalfile.Unique.layer_v1', return_value='123')
    mock_rename = mocker.patch('os.rename', return_value=True)
    mock_copy = mocker.patch('udocker.commonlocalfile.FileUtil.copyto', return_value=False)
    mock_contmeta = mocker.patch.object(CommonLocalFileApi, 'create_container_meta')
    lrepo.setup_imagerepo.return_value = True
    lrepo.cd_imagerepo.return_value = ''
    lrepo.setup_tag.return_value = 'tag'
    lrepo.set_version.return_value = True
    lrepo.layersdir.return_value = '/layers'
    lrepo.add_image_layer.side_effect = [True, True]
    lrepo.save_json.side_effect = [True, True]

    status = clfapi.import_toimage("img.tar", "/images", "v1")
    assert status == '123'
    assert mock_exists.call_count == 2
    assert lrepo.add_image_layer.call_count == 2
    assert lrepo.save_json.call_count == 2
    mock_logerr.assert_not_called()
    lrepo.setup_imagerepo.assert_called()
    lrepo.cd_imagerepo.assert_called()
    mock_loginf.assert_called()
    lrepo.setup_tag.assert_called()
    lrepo.set_version.assert_called()
    mock_layerv1.assert_called()
    mock_rename.assert_called()
    mock_copy.assert_not_called()
    mock_contmeta.assert_called()


def test_17_import_tocontainer(mocker, clfapi):
    """Test17 CommonLocalFileApi().import_tocontainer(). path exists False"""
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    mock_logerr = mocker.patch('udocker.LOG.error')

    status = clfapi.import_tocontainer('', '', '', '')
    assert not status
    mock_exists.assert_called()
    mock_logerr.assert_called()


def test_18_import_tocontainer(mocker, clfapi, lrepo):
    """Test18 CommonLocalFileApi().import_tocontainer(). path exists cont exists"""
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    mock_logerr = mocker.patch('udocker.LOG.error')
    mock_loginf = mocker.patch('udocker.LOG.info')
    lrepo.get_container_id.return_value = True

    status = clfapi.import_tocontainer('img.tar', '/images', 'v1', 'mycont')
    assert not status
    lrepo.get_container_id.assert_called()
    mock_exists.assert_called()
    mock_logerr.assert_not_called()
    mock_loginf.assert_called()


def test_19_import_tocontainer(mocker, clfapi, lrepo):
    """Test19 CommonLocalFileApi().import_tocontainer(). path exists cont does not exist"""
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    mock_logerr = mocker.patch('udocker.LOG.error')
    mock_loginf = mocker.patch('udocker.LOG.info')
    lrepo.get_container_id.return_value = False
    mock_layerv1 = mocker.patch('udocker.commonlocalfile.Unique.layer_v1', return_value='123')
    mock_contmeta = mocker.patch.object(CommonLocalFileApi, 'create_container_meta')
    mock_cstruct = mocker.patch('udocker.commonlocalfile.ContainerStructure')
    mock_cstruct.return_value.create_fromlayer.return_value = '543'
    lrepo.set_container_name.return_value = True

    status = clfapi.import_tocontainer('img.tar', '/images', 'v1', 'mycont')
    assert status == '543'
    lrepo.get_container_id.assert_called()
    mock_exists.assert_called()
    mock_logerr.assert_not_called()
    mock_loginf.assert_not_called()
    mock_layerv1.assert_called()
    mock_contmeta.assert_called()
    mock_cstruct.return_value.create_fromlayer.assert_called()
    lrepo.set_container_name.assert_called()


def test_20_import_clone(mocker, clfapi, lrepo):
    """Test20 CommonLocalFileApi().import_clone(). path not exist"""
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    mock_logerr = mocker.patch('udocker.LOG.error')
    lrepo.get_container_id.return_value = False

    status = clfapi.import_clone('', '')
    assert not status
    mock_exists.assert_called()
    mock_logerr.assert_called()
    lrepo.get_container_id.assert_not_called()


def test_21_import_clone(mocker, clfapi, lrepo):
    """Test21 CommonLocalFileApi().import_clone(). path exists"""
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    mock_logerr = mocker.patch('udocker.LOG.error')
    lrepo.get_container_id.return_value = True
    mock_loginf = mocker.patch('udocker.LOG.info')
    mock_cstruct = mocker.patch('udocker.commonlocalfile.ContainerStructure.clone_fromfile')

    status = clfapi.import_clone('img.tar', 'mycont')
    assert not status
    mock_exists.assert_called()
    mock_logerr.assert_not_called()
    lrepo.get_container_id.assert_called()
    mock_loginf.assert_called()
    mock_cstruct.assert_not_called()


def test_22_import_clone(mocker, clfapi, lrepo):
    """Test22 CommonLocalFileApi().import_clone(). path exists cont does not exist"""
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    mock_logerr = mocker.patch('udocker.LOG.error')
    lrepo.get_container_id.return_value = False
    mock_loginf = mocker.patch('udocker.LOG.info')
    mock_cstruct = mocker.patch('udocker.commonlocalfile.ContainerStructure.clone_fromfile',
                                return_value='543')
    lrepo.set_container_name.return_value = True

    status = clfapi.import_clone('img.tar', 'mycont')
    assert status == '543'
    mock_exists.assert_called()
    mock_logerr.assert_not_called()
    lrepo.get_container_id.assert_called()
    mock_loginf.assert_not_called()
    mock_cstruct.assert_called()
    lrepo.set_container_name.assert_called()


def test_22_clone_container(mocker, clfapi, lrepo):
    """Test22 CommonLocalFileApi().clone_container(). container name exists"""
    lrepo.get_container_id.return_value = True
    mock_loginf = mocker.patch('udocker.LOG.info')

    status = clfapi.clone_container("1234", "mycont")
    assert not status
    lrepo.get_container_id.assert_called()
    mock_loginf.assert_called()


def test_23_clone_container(mocker, clfapi, lrepo):
    """Test23 CommonLocalFileApi().clone_container(). container does not exists"""
    lrepo.get_container_id.return_value = False
    mock_loginf = mocker.patch('udocker.LOG.info')
    mock_clone = mocker.patch('udocker.commonlocalfile.ContainerStructure.clone',
                              return_value="345")
    lrepo.set_container_name.return_value = True
    mock_exmode = mocker.patch('udocker.commonlocalfile.ExecutionMode')
    mock_exmode.return_value.get_mode.return_value = 'F2'
    mock_exmode.return_value.set_mode.return_value = None

    status = clfapi.clone_container("1234", "mycont")
    assert status == "345"
    lrepo.get_container_id.assert_called()
    mock_loginf.assert_not_called()
    mock_clone.assert_called()
    lrepo.set_container_name.assert_called()
    mock_exmode.assert_called()
    mock_exmode.return_value.get_mode.assert_called()
    mock_exmode.return_value.set_mode.assert_called()


data_in = (([False, False], ""),
           ([True, False], "OCI"),
           ([False, True], "Docker"))


@pytest.mark.parametrize("pexists,expected", data_in)
def test_11__get_imagedir_type(mocker, clfapi, pexists, expected):
    """Test11 CommonLocalFileApi()._get_imagedir_type()."""
    mock_exists = mocker.patch('os.path.exists', side_effect=pexists)

    status = clfapi._get_imagedir_type('images/myimg')
    assert status == expected
    mock_exists.assert_called()
