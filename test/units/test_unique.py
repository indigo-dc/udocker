#!/usr/bin/env python
"""
udocker unit tests: Unique
"""
import pytest
from udocker.helper.unique import Unique


data_uuid = [("zxcvbnm", 36),
             (789, 36)]


@pytest.mark.parametrize("argv,expected", data_uuid)
def test_01_uuid(argv, expected):
    """Test01 Unique.uuid()."""
    rand = Unique().uuid(argv)
    assert len(rand) == expected


def test_02_imagename():
    """Test02 Unique.imagename()."""
    rand = Unique().imagename()
    assert len(rand) == 16


def test_03_imagetag():
    """Test03 Unique.imagetag()."""
    rand = Unique().imagetag()
    assert len(rand) == 10


def test_04_layer_v1():
    """Test04 Unique.layer_v1()."""
    rand = Unique().layer_v1()
    assert len(rand) == 64


data_fname = [("zxcvbnmasdf", "zxcvbnmasdf", "udocker", 56),
              (12345, "12345", "udocker", 50)]


@pytest.mark.parametrize("p1,p2,p3,expected", data_fname)
def test_05_filename(p1, p2, p3, expected):
    """Test05 Unique.filename()."""
    rand = Unique().filename(p1)
    assert rand.endswith(p2)
    assert rand.startswith(p3)
    assert len(rand.strip()) > expected
