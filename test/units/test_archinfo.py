#!/usr/bin/env python
"""
udocker unit tests: ArchInfo
"""
import pytest
from udocker.helper.archinfo import ArchInfo


def test_01_get_binaries_list():
    '''Test01 ArchInfo.get_binaries_list'''
    binlist = ["/lib64/ld-linux-x86-64.so",
               "/lib64/ld-linux-x86-64.so.2",
               "/lib64/ld-linux-x86-64.so.3",
               "/bin/bash", "/bin/sh", "/bin/zsh",
               "/bin/csh", "/bin/tcsh", "/bin/ash",
               "/bin/ls", "/bin/busybox",
               "/system/bin/sh", "/system/bin/ls",
               "/lib/ld-linux.so",
               "/lib/ld-linux.so.2",
               ]
    output = ArchInfo().get_binaries_list()
    assert output == binlist


data_arch = (('uname', 'x86_64', 'ALL', (['amd64'], ['x86_64'], ['x86_64'])),
             ('file', 'x86-64', 'ALL', (['amd64'], ['x86_64'], ['x86_64'])),
             ('readelf', 'X86_64', 'ALL', (['amd64'], ['x86_64'], ['x86_64'])),
             ('uname', 'ppc64', 'ALL', (['ppc64'], ['ppc64'], ['ppc64'])),
             ('uname', 'ppc64le', 'UDOCKER', (['ppc64le'], [], [])),
             ('readelf', 'AArch64', 'qemu', (['aarch64'], [], [])),
             ('readelf', 'dumm', 'qemu', ([], [], [])),
             )


@pytest.mark.parametrize("source_type,arch_info,target_type,expected", data_arch)
def test_02_get_arch(source_type, arch_info, target_type, expected):
    '''Test02 ArchInfo.get_arch'''
    output = ArchInfo().get_arch(source_type, arch_info, target_type)
    assert output == expected


# data_trsl = (('amd64', 'docker', 'udocker', 'x86_64'),
#              )


# @pytest.mark.parametrize("source_arch,source_type,target_type,expected", data_trsl)
# def test_03_translate_arch(source_arch, source_type, target_type, expected):
#     '''Test03 ArchInfo.translate_arch'''
#     output = ArchInfo().translate_arch(source_arch, source_type, target_type)
#     assert output == expected
