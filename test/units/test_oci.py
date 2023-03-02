#!/usr/bin/env python
"""
udocker unit tests: OciLocalFileAPI
"""
import pytest
from udocker.oci import OciLocalFileAPI


@pytest.fixture
def lrepo(mocker):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    return mock_lrepo


@pytest.fixture
def ociapi(mocker, lrepo):
    mock_commonfapi = mocker.patch('udocker.commonlocalfile.CommonLocalFileApi')
    return OciLocalFileAPI(lrepo)


@pytest.fixture
def load_json(mocker):
    mock_ljson = mocker.patch('udocker.container.localrepo.LocalRepository.load_json')
    return mock_ljson


def test_01__load_structure(mocker, ociapi, load_json):
    """Test01 OciLocalFileAPI()._load_structure. Structure empty"""
    tmpdir = '/ROOT'
    load_json.side_effect = [[], []]
    mock_oslist = mocker.patch('os.listdir')
    status = ociapi._load_structure(tmpdir)
    assert status == {}
    assert load_json.call_count == 2
    mock_oslist.assert_not_called()


def test_02__load_structure(mocker, ociapi, load_json):
    """Test02 OciLocalFileAPI()._load_structure. Structure not empty"""
    tmpdir = '/ROOT'
    load_json.side_effect = ['oci_lay1', 'idx1']
    out_res = {'repolayers': {'f1:f2': {'layer_a': 'f1',
                                        'layer_f': '/ROOT/blobs/f1/f2',
                                        'layer_h': 'f2'}},
               'manifest': {},
               'oci-layout': 'oci_lay1',
               'index': 'idx1'}

    mock_oslist = mocker.patch('os.listdir', side_effect=[['f1'], ['f2']])
    mock_isdir = mocker.patch('udocker.oci.FileUtil.isdir', return_value=True)
    status = ociapi._load_structure(tmpdir)
    assert status == out_res
    assert load_json.call_count == 2
    assert mock_oslist.call_count == 2
    mock_isdir.assert_called()


def test_03__get_from_manifest(ociapi):
    """Test03 OciLocalFileAPI()._get_from_manifest. Struct empty"""
    imgtag = ''
    struct = dict()
    status = ociapi._get_from_manifest(struct, imgtag)
    assert status == ("", list())


def test_04__get_from_manifest(ociapi):
    """Test04 OciLocalFileAPI()._get_from_manifest. Struct non-empty"""
    imgtag = '123'
    struct = {'manifest': {'123': {'json': {'layers': [{'digest': 'd1'},
                                                       {'digest': 'd2'}],
                                            'config': {'digest': 'dgt'}}}}}
    lay_out = ['d2', 'd1']
    conf_out = 'dgt'
    status = ociapi._get_from_manifest(struct, imgtag)
    assert status == (conf_out, lay_out)


## TODO: the structure and manifest need to be understood what is the schema in particular
##         structure["manifest"][imagetag]["json"] = \
##            self.localrepo.load_json(structure["repolayers"][manifest["digest"]]["layer_f"])
##        structure["manifest"][imagetag]["json_f"] = \
##            structure["repolayers"][manifest["digest"]]["layer_f"]

# def test_05__load_manifest(mocker, ociapi, load_json):
#     """Test05 OciLocalFileAPI()._load_manifest."""
#     manifest = {'annotations': {'org.opencontainers.image.ref.name': '/ctn:123'},
#                 'digest': {'layer_a': 'f1',
#                            'layer_f': 'tmpimg/blobs/f1/f2',
#                            'layer_h': 'f2'}}

#     ljson = {'layers': [{'digest': 'd1'},
#                         {'digest': 'd2'}],
#              'config': {'digest': 'dgt'}}
#     load_json.return_value = ljson

#     struct = {'manifest': {'123': {'json': ljson}},
#               'repolayers': manifest}

#     mock_loadimg = mocker.patch('udocker.commonlocalfile.CommonLocalFileApi._load_image',
#                                 return_value=['123'])
#     status = ociapi._load_manifest(struct, manifest)
#     assert status == ['123']


# def test_06__load_manifest(mocker, ociapi, load_json):
#     """Test06 OciLocalFileAPI()._load_manifest. with Unique"""


def test_07__load_repositories(mocker, ociapi):
    """Test05 OciLocalFileAPI()._load_repositories."""
    manifest = [{'mediaType': 'application/vnd.oci.image.manifest.v1+json'}]
    struct = {'index': {'manifests': manifest}}
    mock_loadmanif = mocker.patch.object(OciLocalFileAPI, '_load_manifest',
                                         return_value=['123'])
    status = ociapi._load_repositories(struct)
    assert status == [['123']]
    mock_loadmanif.assert_called()


def test_08__load_image_step2(mocker, ociapi):
    """Test08 OciLocalFileAPI()._load_image_step2. move layer to v1 repo false"""
    imgtag = '123'
    imgrepo = '/somerepo'
    struct = {'repolayers':
              {'layer1': {'layer_a': 'f1',
                          'layer_f': '/somedir/cfg1.json',
                          'layer_h': 'f2'},
               'layer2': {'layer_a': 'g1',
                          'layer_f': '/somedir/cfg2.json',
                          'layer_h': 'g2'}},
              'manifest': {},
              'oci-layout': 'oci_lay1',
              'index': 'idx1'}
    out_manif = ('layer1', ['layer1', 'layer2'])
    mock_getmanif = mocker.patch.object(OciLocalFileAPI, '_get_from_manifest',
                                        return_value=out_manif)
    mock_mvv1 = mocker.patch.object(OciLocalFileAPI, '_move_layer_to_v1repo',
                                    side_effect=[True, False, False])
    mock_logerr = mocker.patch('udocker.LOG.error')
    status = ociapi._load_image_step2(struct, imgrepo, imgtag)
    assert status == []
    mock_getmanif.assert_called()
    assert mock_mvv1.call_count == 2
    mock_logerr.assert_called()


def test_09__load_image_step2(mocker, ociapi):
    """Test09 OciLocalFileAPI()._load_image_step2. move layer to v1 repo true"""
    imgtag = '123'
    imgrepo = '/somerepo'
    struct = {'repolayers':
              {'layer1': {'layer_a': 'f1',
                          'layer_f': '/somedir/cfg1.json',
                          'layer_h': 'f2'},
               'layer2': {'layer_a': 'g1',
                          'layer_f': '/somedir/cfg2.json',
                          'layer_h': 'g2'}},
              'manifest': {},
              'oci-layout': 'oci_lay1',
              'index': 'idx1'}
    out_manif = ('layer1', ['layer1', 'layer2'])
    mock_getmanif = mocker.patch.object(OciLocalFileAPI, '_get_from_manifest',
                                        return_value=out_manif)
    mock_mvv1 = mocker.patch.object(OciLocalFileAPI, '_move_layer_to_v1repo',
                                    side_effect=[True, True, True])
    mock_logerr = mocker.patch('udocker.LOG.error')
    mock_sjson = mocker.patch('udocker.container.localrepo.LocalRepository.save_json')
    status = ociapi._load_image_step2(struct, imgrepo, imgtag)
    assert status == ['/somerepo:123']
    mock_getmanif.assert_called()
    assert mock_mvv1.call_count == 3
    mock_logerr.assert_not_called()
    mock_sjson.assert_called()


def test_10_load(mocker, ociapi):
    """Test10 OciLocalFileAPI().load. Structure empty list"""
    tmpdir = '/ROOT'
    imgrepo = 'somerepo'
    mock_loadstruct = mocker.patch.object(OciLocalFileAPI, '_load_structure', return_value={})
    mock_loadrepo = mocker.patch.object(OciLocalFileAPI, '_load_repositories')
    status = ociapi.load(tmpdir, imgrepo)
    assert status == []
    mock_loadstruct.assert_called()
    mock_loadrepo.assert_not_called()


def test_11_load(mocker, ociapi):
    """Test11 OciLocalFileAPI().load. Structure non empty list"""
    tmpdir = '/ROOT'
    imgrepo = 'somerepo'
    struct = {'repolayers':
              {'f1:f2': {'layer_a': 'f1',
                         'layer_f': 'tmpimg/blobs/f1/f2',
                         'layer_h': 'f2'}},
              'manifest': {},
              'oci-layout': 'oci_lay1',
              'index': 'idx1'}
    mock_loadstruct = mocker.patch.object(OciLocalFileAPI, '_load_structure', return_value=struct)
    mock_loadrepo = mocker.patch.object(OciLocalFileAPI, '_load_repositories',
                                        return_value=['r1', 'r2'])
    status = ociapi.load(tmpdir, imgrepo)
    assert status == ['r1', 'r2']
    mock_loadstruct.assert_called()
    mock_loadrepo.assert_called()
