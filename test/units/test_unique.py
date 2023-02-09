#!/usr/bin/env python
"""
udocker unit tests: Unique
"""
from udocker.helper.unique import Unique


def test_01_uuid():
    """Test01 Unique.uuid()."""
    uniq = Unique()
    rand = uniq.uuid("zxcvbnm")
    assert len(rand) == 36


def test_02_uuid():
    """Test02 Unique.uuid()."""
    uniq = Unique()
    rand = uniq.uuid(789)
    assert len(rand) == 36


def test_03_imagename():
    """Test03 Unique.imagename()."""
    uniq = Unique()
    rand = uniq.imagename()
    assert len(rand) == 16


def test_04_imagetag():
    """Test04 Unique.imagetag()."""
    uniq = Unique()
    rand = uniq.imagetag()
    assert len(rand) == 10


def test_05_layer_v1():
    """Test05 Unique.layer_v1()."""
    uniq = Unique()
    rand = uniq.layer_v1()
    assert len(rand) == 64


def test_06_filename():
    """Test06 Unique.filename()."""
    uniq = Unique()
    rand = uniq.filename("zxcvbnmasdf")
    assert rand.endswith("zxcvbnmasdf") == True
    assert rand.startswith("udocker") == True
    assert len(rand.strip()) > 56


def test_07_filename():
    """Test07 Unique.filename()."""
    uniq = Unique()
    rand = uniq.filename(12345)
    assert rand.endswith("12345") == True
    assert rand.startswith("udocker") == True
    assert len(rand.strip()) > 50
