#!/usr/bin/env python
"""
udocker unit tests: ArchInfo
"""
import pytest
from udocker.helper.archinfo import ArchInfo


@pytest.fixture
def archinfo_instance():
    return ArchInfo()


def test_01_get_binaries_list():
    """Test01 ArchInfo.get_binaries_list"""
    binlist = ["/lib64/ld-linux-x86-64.so",
               "/lib64/ld-linux-x86-64.so.1",
               "/lib64/ld-linux-x86-64.so.2",
               "/lib64/ld-linux-x86-64.so.3",
               "/lib64/ld-linux-aarch64.so",
               "/lib64/ld-linux-aarch64.so.1",
               "/lib64/ld-linux-aarch64.so.2",
               "/lib64/ld-linux-aarch64.so.3",
               "/lib64/ld64.so", "/lib64/ld64.so.1",
               "/lib64/ld64.so.2", "/lib64/ld64.so.3",
               "/usr/sbin/ldconfig", "/sbin/ldconfig",
               "/bin/bash", "/bin/sh", "/bin/zsh",
               "/bin/csh", "/bin/tcsh", "/bin/ash",
               "/bin/dash", "/bin/ls", "/bin/busybox",
               "/system/bin/sh", "/system/bin/ls",
               "/lib/ld-linux.so", "/lib/ld-linux.so.1",
               "/lib/ld-linux.so.2", "/lib/ld-linux.so.3",
               "/usr/bin/coreutils", "/bin/coreutils", ]
    output = ArchInfo().get_binaries_list()
    for item in binlist:
        assert item in output


data_arch = (
             ('uname', 'x86_64', 'ALL', (['amd64'], ['x86_64'], ['x86_64'])),
             ('file', 'x86-64', 'ALL', (['amd64'], ['x86_64'], ['x86_64'])),
             ('readelf', 'X86_64', 'ALL', (['x86_64'], ['x86_64'], ['x86_64'])),
             ('uname', 'ppc64', 'ALL', (['ppc64'], ['ppc64'], ['ppc64'])),
             ('uname', 'ppc64le', 'UDOCKER', (['ppc64le'], [], [])),
             ('readelf', 'AArch64', 'qemu', (['aarch64'], [], [])),
             ('readelf', 'dumm', 'qemu', ([], [], [])),
             ('invalid_source', 'x86_64', 'ALL', ([], [], [])),
             )

@pytest.mark.parametrize("source_type,arch_info,target_type,expected", data_arch)
def test_02_get_arch(source_type, arch_info, target_type, expected):
    """Test02 ArchInfo.get_arch"""
    output = ArchInfo().get_arch(source_type, arch_info, target_type)
    assert output == expected


# data_trsl = (('amd64', 'docker', 'udocker', 'x86_64'),
#              )

@pytest.mark.parametrize("source_arch, source_type, target_type, expected_result", [
    ("x86_64", "docker", "udocker", ["amd64"]),
    ("unknown_arch", "docker", "udocker", []),
    ("x86_64", "unknown_type", "udocker", []),
    ("x86_64", "docker", "unknown_type", []),
])
# @pytest.mark.parametrize("source_arch,source_type,target_type,expected", data_trsl)
def test_03_translate_arch(archinfo_instance, source_arch, source_type, target_type, expected_result):
    """Test03 ArchInfo.translate_arch"""
    archinfo_instance._arch_list = [
        {"docker": ["x86_64"], "udocker": ["amd64"]},
        {"docker": ["ppc64le"], "udocker": ["powerpc64le"]}
    ]
    result = archinfo_instance.translate_arch(source_arch, source_type, target_type)
    assert result == expected_result
