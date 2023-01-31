#!/usr/bin/env python
"""
udocker unit tests: Unique
"""
import pytest
from udocker.helper.unique import Unique, LOG


def test_01_uuid_01():
    """Test01_01 Unique.uuid()."""
    uniq = Unique()
    rand = uniq.uuid("zxcvbnm")
    assert len(rand) == 36

def test_01_uuid_02():
    """Test01_02 Unique.uuid()."""
    uniq = Unique()
    rand = uniq.uuid(789)
    assert len(rand) == 36

def test_02_imagename():
    """Test02 Unique.imagename()."""
    uniq = Unique()
    rand = uniq.imagename()
    assert len(rand) == 16

def test_03_imagetag():
    """Test03 Unique.imagetag()."""
    uniq = Unique()
    rand = uniq.imagetag()
    assert len(rand) == 10

def test_04_layer_v1():
    """Test04 Unique.layer_v1()."""
    uniq = Unique()
    rand = uniq.layer_v1()
    assert len(rand) == 64

def test_05_filename_01():
    """Test05_01 Unique.filename()."""
    uniq = Unique()
    rand = uniq.filename("zxcvbnmasdf")
    assert rand.endswith("zxcvbnmasdf") == True
    assert rand.startswith("udocker") == True
    assert len(rand.strip()) > 56

def test_05_filename_02():
    """Test05_02 Unique.filename()."""
    uniq = Unique()
    rand = uniq.filename(12345)
    assert rand.endswith("12345") == True
    assert rand.startswith("udocker") == True
    assert len(rand.strip()) > 50
