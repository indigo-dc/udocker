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


# def test_03__get_from_manifest(self):
#     """Test03 OciLocalFileAPI()._get_from_manifest."""
#     imgtag = '123'
#     struct = {'manifest': {'123': {'json': {'layers': [{'digest': 'd1'},
#                                                         {'digest': 'd2'}],
#                                             'config': {'digest': 'dgt'}}}}}
#     lay_out = ['d2', 'd1']
#     conf_out = 'dgt'
#     status = OciLocalFileAPI(self.local)._get_from_manifest(struct, imgtag)
#     self.assertEqual(status, (conf_out, lay_out))

#     imgtag = ''
#     struct = dict()
#     ocilocal = OciLocalFileAPI(self.local)
#     self.assertEqual(ocilocal._get_from_manifest(struct, imgtag), ("", list()))

# # @patch('udocker.oci.Unique.imagename')
# # @patch('udocker.oci.Unique.imagetag')
# # @patch('udocker.container.localrepo.LocalRepository.load_json',autospec=True)
# # def test_04__load_manifest(self, mock_ljson, mock_uniqtag, mock_uniqname):
# #     """Test04 OciLocalFileAPI()._load_manifest."""
# #     manifest = {'annotations': {'org.opencontainers.image.ref.name': '123'},
# #                 'digest': {'layer_a': 'f1',
# #                            'layer_f': 'tmpimg/blobs/f1/f2',
# #                            'layer_h': 'f2'}}
# #     mock_uniqtag.return_value = '123'
# #     mock_uniqname.return_value = 'imgname'
# #     mock_ljson.return_value = {'layers': [{'digest': 'd1'},
# #                                           {'digest': 'd2'}],
# #                                'config': {'digest': 'dgt'}}
# #     struct = {'manifest': {'123': {'json': mock_ljson}},
# #               'repolayers': manifest}
# #     status = OciLocalFileAPI(self.local)._load_manifest(struct, manifest)
# #     self.assertEqual(status, (struct, "imgname", ['123']))

# # def test_05__load_repositories(self):
# #     """Test05 OciLocalFileAPI()._load_repositories."""

# # def test_06__load_image_step2(self):
# #     """Test07 OciLocalFileAPI()._load_image_step2."""

