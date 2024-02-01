#!/usr/bin/env python
"""
udocker unit tests: Unique
"""
import string

import pytest
from udocker.helper.unique import Unique

@pytest.fixture
def unique():
    return Unique()

def test_01_init():
    """Test01 Unique.__init__()."""
    unique = Unique()
    assert unique.string_set == "abcdef"
    assert unique.def_name == "udocker"

@pytest.mark.parametrize("size", [8, 16, 32])
def test_02__rnd(unique, size):
    """Test02 Unique._rnd()."""
    rnd_str = unique._rnd(size)
    assert len(rnd_str) == size
    assert all(c in string.hexdigits for c in rnd_str)


data_uuid = [("zxcvbnm", 36, False),
             (789, 36, False),
             ("test", 36, True),
             (None, 36, False)]

@pytest.mark.parametrize("argv,expected,raise_exception", data_uuid)
def test_03_uuid(mocker, unique, argv, expected, raise_exception):
    """Test03 Unique.uuid()."""
    if raise_exception:
        with mocker.patch('uuid.uuid3', side_effect=NameError), \
             mocker.patch('uuid.uuid4', side_effect=NameError):
            rand = unique.uuid(argv)
    else:
        rand = unique.uuid(argv)
    assert len(rand) == expected


def test_04_imagename(unique):
    """Test04 Unique.imagename()."""
    rand = unique.imagename()
    assert len(rand) == 16


def test_05_imagetag(unique):
    """Test05 Unique.imagetag()."""
    rand = unique.imagetag()
    assert len(rand) == 10


def test_06_layer_v1(unique):
    """Test06 Unique.layer_v1()."""
    rand = unique.layer_v1()
    assert len(rand) == 64


data_fname = [("zxcvbnmasdf", "zxcvbnmasdf", "udocker", 56, False),
              (12345, "12345", "udocker", 50, False),
              ("testfile", "testfile", "udocker", 50, True)]


@pytest.mark.parametrize("p1,p2,p3,expected,raise_exception", data_fname)
def test_07_filename(mocker, unique, p1, p2, p3, expected, raise_exception):
    """Test07 Unique.filename()."""
    if raise_exception:
        with mocker.patch('uuid.uuid3', side_effect=NameError), mocker.patch('uuid.uuid4', side_effect=NameError):
            rand = unique.filename(p1)
    else:
        rand = unique.filename(p1)

    assert rand.endswith(p2)
    assert rand.startswith(p3)
    assert len(rand.strip()) > expected
