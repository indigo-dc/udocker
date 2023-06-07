# -*- coding: utf-8 -*-
"""Common architecture info and methods for hostinfo and osinfo"""

class ArchInfo(object):
    """Common object for architecture information"""

    # { 'docker':['docker_arch'], 'qemu':['qemu_arch'],
    #   'UDOCKER':['udocker_arch'], 'uname':['uname string]',
    #   'file':['file string'], 'readelf':['readelf string']
    # }

    _arch_list = [
        {'docker':['amd64'], 'qemu':['x86_64'], 'UDOCKER':['x86_64'],
         'uname':['x86_64'], 'file':['x86_64'], 'readelf':['X86_64']},
        {'docker':['386'], 'qemu':['i386'], 'UDOCKER':['x86'],
         'uname':['i386'], 'file':['Intel 80386'], 'readelf':['Intel 80386']},
        {'docker':['arm64'], 'qemu':['aarch64'], 'UDOCKER':['arm64'],
         'uname':['aarch64'], 'file':['aarch64'], 'readelf':['AArch64']},
        {'docker':['arm'], 'qemu':['arm'], 'UDOCKER':['arm'],
         'uname':['arm'], 'file':[' ARM'], 'readelf':[' ARM']},
        {'docker':['ppc64le'], 'qemu':['ppc64le'], 'UDOCKER':['ppc64le'],
         'uname':['ppc64le'], 'file':['64-bit PowerPC', 'LSB executable'],
         'readelf':['PowerPC64', 'little endian']},
        {'docker':['ppc64'], 'qemu':['ppc64'], 'UDOCKER':['ppc64'],
         'uname':['ppc64'], 'file':['PowerPC', '64-bit'],
         'readelf':['PowerPC', 'ELF64']},
        {'docker':['ppc'], 'qemu':['ppc'], 'UDOCKER':['ppc'],
         'uname':['ppc'], 'file':['PowerPC', '32-bit'],
         'readelf':['PowerPC', 'ELF32']},
        {'docker':['mipsle'], 'qemu':['mipsel'], 'UDOCKER':['mipsle'],
         'uname':['mips'], 'file':['mips', '32-bit', 'LSB executable'],
         'readelf':['mips', 'ELF32', 'little endian']},
        {'docker':['mips'], 'qemu':['mips'], 'UDOCKER':['mips'],
         'uname':['mips'], 'file':['mips', '32-bit', 'MSB'],
         'readelf':['mips', 'ELF32', 'big endian']},
        {'docker':['mips64le'], 'qemu':['mips64el'], 'UDOCKER':['mips64le'],
         'uname':['mips64'], 'file':['mips', '64-bit', 'LSB executable'],
         'readelf':['mips', 'ELF64', 'little endian']},
        {'docker':['mips64'], 'qemu':['mips64'], 'UDOCKER':['mips64'],
         'uname':['mips64'], 'file':['mips', '64-bit', 'MSB'],
         'readelf':['mips', 'ELF64', 'big endian']},
        {'docker':['riscv64'], 'qemu':['riscv64'], 'UDOCKER':['riscv64'],
         'uname':['riscv64'], 'file':['riscv', '64-bit'],
         'readelf':['riscv', 'ELF64']},
        {'docker':['s390x'], 'qemu':['s390x'], 'UDOCKER':['s390x'],
         'uname':['s390x'], 'file':['IBM S/390', '64-bit', 'MSB'],
         'readelf':['IBM S/390', 'ELF64', 'big endian']}
    ]

    # binaries from which to get architecture information using
    # host tools such as "readelf -h" and "file"

    _binaries_list = ["/lib64/ld-linux-x86-64.so",
                      "/lib64/ld-linux-x86-64.so.2",
                      "/lib64/ld-linux-x86-64.so.3",
                      "/bin/bash", "/bin/sh", "/bin/zsh",
                      "/bin/csh", "/bin/tcsh", "/bin/ash",
                      "/bin/ls", "/bin/busybox",
                      "/system/bin/sh", "/system/bin/ls",
                      "/lib/ld-linux.so",
                      "/lib/ld-linux.so.2",
                     ]

    def get_binaries_list(self):
        """Return list of binary files"""
        return self._binaries_list

    def get_arch(self, source_type, arch_info, target_type="UDOCKER"):
        """
        Return (docker_arch, qemu_arch, udocker_arch) by source type
        source can be "uname", "file" or "readelf"
        arch_info is data previously produced by uname, file or readelf
        target_type can be docker, qemu, UDOCKER or ALL
        """
        try:
            for arch_dict in self._arch_list:
                for arch_expression in arch_dict[source_type]:
                    if not arch_expression in arch_info:
                        break
                if target_type == "ALL":
                    return (arch_dict['docker'], arch_dict['qemu'],
                            arch_dict['UDOCKER'])
                return (arch_dict[target_type], [], [])
        except (KeyError, ValueError, TypeError, AttributeError):
            pass
        return ([], [], [])

    def translate_arch(self, source_arch, source_type, target_type):
        """
        For a source architecture return the matching target architecture
        Example: translate_arch("ppc64le" "docker", "udocker")
        """
        try:
            for arch_dict in self._arch_list:
                for arch_expression in arch_dict[source_type]:
                    if arch_expression == source_arch:
                        return arch_dict[target_type]
        except (KeyError, ValueError, TypeError, AttributeError):
            pass
        return []
