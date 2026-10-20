#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
udocker unit tests: DockerfileParser and ContainerBuilder
"""

import os
import io
import shutil
import tarfile
import tempfile
from unittest import TestCase, main
from unittest.mock import Mock, patch
import collections

from udocker.container.dockerfile import DockerfileParser, ContainerBuilder

collections.Callable = collections.abc.Callable


class DockerfileParserTestCase(TestCase):
    """Test DockerfileParser()."""

    def _parse(self, content):
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "Dockerfile")
        with open(path, "w") as filep:
            filep.write(content)
        try:
            return DockerfileParser().parse(path)
        finally:
            shutil.rmtree(tmpdir)

    def test_01_basic(self):
        """Test01 basic FROM/RUN parsing."""
        result = self._parse("FROM ubuntu:20.04\nRUN echo hi\n")
        self.assertEqual(result,
                         [("FROM", "ubuntu:20.04"), ("RUN", "echo hi")])

    def test_02_comments_and_blank_lines(self):
        """Test02 comments and blank lines are ignored."""
        content = ("# top comment\n\nFROM ubuntu\n"
                   "  # indented comment\nCMD [\"ls\"]\n")
        result = self._parse(content)
        self.assertEqual(result, [("FROM", "ubuntu"), ("CMD", '["ls"]')])

    def test_03_continuation(self):
        """Test03 backslash line continuation is joined into one line,
        as a single shell statement (the backslash+newline is deleted,
        not replaced by a newline)."""
        result = self._parse("RUN echo a && \\\n    echo b\n")
        self.assertEqual(result, [("RUN", "echo a &&     echo b")])

    def test_06_multi_package_continuation(self):
        """Test06 a multi-line package list stays a single RUN command."""
        content = ("RUN apk add --no-cache \\\n"
                   "    build-base \\\n"
                   "    cmake \\\n"
                   "    git\n")
        result = self._parse(content)
        self.assertEqual(
            result,
            [("RUN", "apk add --no-cache     build-base     cmake     git")])

    def test_04_lowercase_instruction(self):
        """Test04 instruction keywords are case-insensitive."""
        result = self._parse("from ubuntu\n")
        self.assertEqual(result, [("FROM", "ubuntu")])

    def test_05_no_argument(self):
        """Test05 instruction without argument."""
        result = self._parse("FROM ubuntu\nEXPOSE\n")
        self.assertEqual(result, [("FROM", "ubuntu"), ("EXPOSE", "")])

    def test_07_comment_inside_continuation(self):
        """Test07 a '#' comment inside a RUN continuation is dropped,
        the surrounding lines still form a single shell command."""
        content = ("RUN apk add --no-cache \\\n"
                   "    # core libs\n"
                   "    libusb \\\n"
                   "    eudev-libs\n")
        result = self._parse(content)
        self.assertEqual(
            result,
            [("RUN", "apk add --no-cache     libusb     eudev-libs")])

    def test_08_split_stages(self):
        """Test08 split_stages() groups instructions by FROM and
        captures the optional AS <name>."""
        instructions = [
            ("FROM", "alpine:3.20 AS builder"),
            ("RUN", "echo build"),
            ("FROM", "alpine:3.20"),
            ("COPY", "--from=builder /bin/x /bin/x"),
        ]
        stages = DockerfileParser.split_stages(instructions)
        self.assertEqual(len(stages), 2)
        self.assertEqual(stages[0]["image"], "alpine:3.20")
        self.assertEqual(stages[0]["name"], "builder")
        self.assertEqual(stages[0]["instructions"], [("RUN", "echo build")])
        self.assertIsNone(stages[1]["name"])
        self.assertEqual(stages[1]["instructions"],
                         [("COPY", "--from=builder /bin/x /bin/x")])

    def test_09_split_stages_requires_from_first(self):
        """Test09 an instruction before any FROM is rejected."""
        with self.assertRaises(ValueError):
            DockerfileParser.split_stages([("RUN", "echo hi")])


class ContainerBuilderTestCase(TestCase):
    """Test ContainerBuilder()."""

    def setUp(self):
        self.mock_lrepo = Mock()
        self.mock_lrepo.cd_container.return_value = "/containers/CID"
        self.mock_lrepo.load_json.return_value = {
            "config": {"Env": ["PATH=/usr/bin"]}
        }
        self.mock_lrepo.layersdir = "/layers"

    def _builder(self):
        return ContainerBuilder(self.mock_lrepo, "CID", "/context")

    def test_01_init(self):
        """Test01 constructor loads existing container metadata."""
        builder = self._builder()
        self.assertEqual(builder.container_root, "/containers/CID/ROOT")
        self.assertEqual(builder.envs.env, {"PATH": "/usr/bin"})

    def test_02_set_build_args(self):
        """Test02 set_build_args() registers --build-arg overrides."""
        builder = self._builder()
        builder.set_build_args(["FOO=bar", "BAZ=qux"])
        self.assertEqual(builder.build_args, {"FOO": "bar", "BAZ": "qux"})

    def test_03_do_arg_with_override(self):
        """Test03 ARG value overridden by --build-arg."""
        builder = self._builder()
        builder.set_build_args(["FOO=override"])
        self.assertTrue(builder._do_arg("FOO=default"))
        self.assertEqual(builder.args["FOO"], "override")

    def test_04_do_arg_default(self):
        """Test04 ARG uses its default when not overridden."""
        builder = self._builder()
        self.assertTrue(builder._do_arg("FOO=default"))
        self.assertEqual(builder.args["FOO"], "default")
        self.assertFalse(builder._do_arg(""))

    def test_05_expand(self):
        """Test05 ${VAR} and $VAR substitution."""
        builder = self._builder()
        builder._do_arg("NAME=world")
        result = builder._expand("hello ${NAME} and $NAME")
        self.assertEqual(result, "hello world and world")

    def test_06_expand_undefined(self):
        """Test06 undefined variables are left untouched."""
        builder = self._builder()
        result = builder._expand("value=${UNSET}")
        self.assertEqual(result, "value=${UNSET}")

    def test_07_do_env_multi(self):
        """Test07 ENV with multiple KEY=VALUE pairs."""
        builder = self._builder()
        self.assertTrue(builder._do_env("A=1 B=2"))
        envs = builder.envs.env
        self.assertEqual(envs["A"], "1")
        self.assertEqual(envs["B"], "2")
        self.assertIn("A=1", builder.config["Env"])

    def test_08_do_env_legacy(self):
        """Test08 legacy ENV KEY VALUE form."""
        builder = self._builder()
        self.assertTrue(builder._do_env("A value with spaces"))
        self.assertEqual(builder.envs.env["A"], "value with spaces")

    def test_09_do_env_invalid(self):
        """Test09 empty ENV instruction is rejected."""
        builder = self._builder()
        self.assertFalse(builder._do_env(""))

    @patch('udocker.container.dockerfile.os.makedirs')
    def test_10_do_workdir_absolute(self, mock_mkdirs):
        """Test10 WORKDIR with an absolute path."""
        builder = self._builder()
        self.assertTrue(builder._do_workdir("/app"))
        self.assertEqual(builder.config["WorkingDir"], "/app")

    @patch('udocker.container.dockerfile.os.makedirs')
    def test_11_do_workdir_relative(self, mock_mkdirs):
        """Test11 WORKDIR with a relative path is joined to the previous one."""
        builder = self._builder()
        builder.config["WorkingDir"] = "/app"
        self.assertTrue(builder._do_workdir("sub"))
        self.assertEqual(builder.config["WorkingDir"], "/app/sub")

    def test_12_do_user(self):
        """Test12 USER instruction."""
        builder = self._builder()
        self.assertTrue(builder._do_user("someuser"))
        self.assertEqual(builder.config["User"], "someuser")
        self.assertFalse(builder._do_user(""))

    def test_13_do_label(self):
        """Test13 LABEL instruction with quoted values."""
        builder = self._builder()
        self.assertTrue(builder._do_label('a=1 b="two words"'))
        self.assertEqual(builder.config["Labels"],
                         {"a": "1", "b": "two words"})

    def test_14_do_expose(self):
        """Test14 EXPOSE defaults to tcp when no protocol given."""
        builder = self._builder()
        self.assertTrue(builder._do_expose("80 443/udp"))
        self.assertEqual(builder.config["ExposedPorts"],
                         {"80/tcp": {}, "443/udp": {}})

    @patch('udocker.container.dockerfile.os.makedirs')
    def test_15_do_volume(self, mock_mkdirs):
        """Test15 VOLUME instruction."""
        builder = self._builder()
        self.assertTrue(builder._do_volume("/data"))
        self.assertIn("/data", builder.config["Volumes"])

    def test_16_do_cmd_shell(self):
        """Test16 CMD shell form is wrapped with /bin/sh -c."""
        builder = self._builder()
        self.assertTrue(builder._do_cmd("echo hi"))
        self.assertEqual(builder.config["Cmd"], ["/bin/sh", "-c", "echo hi"])

    def test_17_do_cmd_exec(self):
        """Test17 CMD exec (JSON array) form."""
        builder = self._builder()
        self.assertTrue(builder._do_cmd('["/bin/ls", "-l"]'))
        self.assertEqual(builder.config["Cmd"], ["/bin/ls", "-l"])

    def test_18_do_entrypoint(self):
        """Test18 ENTRYPOINT exec form."""
        builder = self._builder()
        self.assertTrue(builder._do_entrypoint('["/entry.sh"]'))
        self.assertEqual(builder.config["Entrypoint"], ["/entry.sh"])

    def test_19_do_copy_from_stage(self):
        """Test19 COPY --from=<stage> resolves against stage_roots and
        copies real files, exercised against real temp directories since
        the underlying copy goes through an actual tar pipe."""
        tmpdir = tempfile.mkdtemp()
        try:
            stage_root = os.path.join(tmpdir, "stage_root")
            os.makedirs(os.path.join(stage_root, "usr", "local", "bin"))
            with open(os.path.join(stage_root, "usr", "local", "bin",
                                   "tool"), "w") as filep:
                filep.write("binary")
            container_dir = os.path.join(tmpdir, "container")
            os.makedirs(container_dir + "/ROOT")
            self.mock_lrepo.cd_container.return_value = container_dir
            builder = self._builder()
            builder.set_stage_roots({"builder": stage_root})
            status = builder._do_copy(
                "--from=builder /usr/local/bin/ /usr/local/bin/")
            self.assertTrue(status)
            self.assertTrue(os.path.isfile(
                container_dir + "/ROOT/usr/local/bin/tool"))
        finally:
            shutil.rmtree(tmpdir)

    def test_20_do_copy_from_unknown_stage(self):
        """Test20 COPY --from an undeclared stage fails."""
        builder = self._builder()
        status = builder._do_copy("--from=missing /src /dest")
        self.assertFalse(status)

    def test_21_run_instructions_unknown_warns(self):
        """Test20 unsupported instructions are skipped with a warning."""
        builder = self._builder()
        status = builder.run_instructions([("MAINTAINER", "me")])
        self.assertTrue(status)

    @patch('udocker.container.dockerfile.ExecutionMode')
    def test_22_do_run_success(self, mock_execmode):
        """Test22 RUN executes the command via the execution engine."""
        builder = self._builder()
        mock_engine = Mock()
        mock_engine.opt = {}
        mock_engine.run.return_value = 0
        mock_execmode.return_value.get_engine.return_value = mock_engine
        self.assertTrue(builder._do_run("echo hi"))
        self.assertEqual(mock_engine.opt["cmd"], ["/bin/sh", "-c", "echo hi"])

    @patch('udocker.container.dockerfile.ExecutionMode')
    def test_23_do_run_failure(self, mock_execmode):
        """Test23 a non-zero exit status fails the build."""
        builder = self._builder()
        mock_engine = Mock()
        mock_engine.opt = {}
        mock_engine.run.return_value = 1
        mock_execmode.return_value.get_engine.return_value = mock_engine
        self.assertFalse(builder._do_run("false"))

    @patch('udocker.container.dockerfile.ExecutionMode')
    def test_24_do_run_no_engine(self, mock_execmode):
        """Test24 no execution engine available."""
        builder = self._builder()
        mock_execmode.return_value.get_engine.return_value = None
        self.assertFalse(builder._do_run("echo hi"))

    @patch('udocker.container.dockerfile.FileUtil')
    @patch('udocker.container.dockerfile.ChkSUM')
    @patch('udocker.container.dockerfile.Unique')
    def test_25_commit(self, mock_unique, mock_chksum, mock_fileutil):
        """Test25 commit() tars the rootfs and registers a new image layer."""
        builder = self._builder()
        mock_unique.return_value.layer_v1.return_value = "LAYERID"
        mock_fileutil.return_value.tar.return_value = True
        mock_fileutil.return_value.size.return_value = 100
        mock_chksum.return_value.hash.return_value = "abc123"
        self.mock_lrepo.setup_tag.return_value = True
        self.mock_lrepo.set_version.return_value = True
        self.mock_lrepo.save_json.return_value = True
        status = builder.commit("myrepo/myimage", "latest")
        self.assertTrue(status)
        self.mock_lrepo.setup_imagerepo.assert_called_with("myrepo/myimage")
        self.mock_lrepo.add_image_layer.assert_any_call(
            "/layers/LAYERID.layer")

    @patch('udocker.container.dockerfile.FileUtil')
    def test_26_commit_tar_failure(self, mock_fileutil):
        """Test26 commit() fails if the rootfs cannot be tarred."""
        builder = self._builder()
        self.mock_lrepo.setup_tag.return_value = True
        self.mock_lrepo.set_version.return_value = True
        mock_fileutil.return_value.tar.return_value = False
        status = builder.commit("myrepo/myimage", "latest")
        self.assertFalse(status)

    def test_27_do_copy_source_outside_context(self):
        """Test27 COPY refuses sources resolving outside the context."""
        tmpdir = tempfile.mkdtemp()
        try:
            context = os.path.join(tmpdir, "ctx")
            container = os.path.join(tmpdir, "container")
            os.makedirs(context)
            os.makedirs(container + "/ROOT")
            with open(os.path.join(tmpdir, "outside.txt"), "w") as filep:
                filep.write("secret")
            self.mock_lrepo.cd_container.return_value = container
            builder = ContainerBuilder(self.mock_lrepo, "CID", context)
            status = builder._do_copy("../outside.txt /leaked.txt")
            self.assertFalse(status)
            self.assertFalse(os.path.exists(container + "/ROOT/leaked.txt"))
        finally:
            shutil.rmtree(tmpdir)

    def test_28_do_copy_destination_outside_root(self):
        """Test28 COPY refuses destinations outside the container ROOT."""
        tmpdir = tempfile.mkdtemp()
        try:
            context = os.path.join(tmpdir, "ctx")
            container = os.path.join(tmpdir, "container")
            os.makedirs(context)
            os.makedirs(container + "/ROOT")
            with open(os.path.join(context, "f.txt"), "w") as filep:
                filep.write("x")
            self.mock_lrepo.cd_container.return_value = container
            builder = ContainerBuilder(self.mock_lrepo, "CID", context)
            target = os.path.join(tmpdir, "escaped.txt")
            dest = "/" + "../" * 10 + target.lstrip("/")
            status = builder._do_copy("f.txt " + dest)
            self.assertFalse(status)
            self.assertFalse(os.path.exists(target))
        finally:
            shutil.rmtree(tmpdir)

    def test_29_extract_tar_refuses_escaping_member(self):
        """Test29 ADD refuses tar members escaping the destination."""
        tmpdir = tempfile.mkdtemp()
        try:
            root = os.path.join(tmpdir, "ROOT")
            os.makedirs(root)
            target = os.path.join(tmpdir, "tarslip.txt")
            tarpath = os.path.join(tmpdir, "evil.tar")
            with tarfile.open(tarpath, "w") as tfile:
                data = b"pwn"
                info = tarfile.TarInfo("/".join([".."] * 10) + target)
                info.size = len(data)
                tfile.addfile(info, io.BytesIO(data))
            builder = self._builder()
            self.assertFalse(builder._extract_tar(tarpath, root))
            self.assertFalse(os.path.exists(target))
        finally:
            shutil.rmtree(tmpdir)

    def test_30_safe_member_symlink_escape(self):
        """Test30 tar members cannot escape through an extracted symlink."""
        root = tempfile.mkdtemp()
        try:
            link = tarfile.TarInfo("evil")
            link.type = tarfile.SYMTYPE
            link.linkname = "/etc"
            self.assertTrue(ContainerBuilder._safe_member(root, link))
            os.symlink("/etc", os.path.join(root, "evil"))
            through = tarfile.TarInfo("evil/passwd")
            self.assertFalse(ContainerBuilder._safe_member(root, through))
        finally:
            shutil.rmtree(root)

    def test_31_chmod_spec(self):
        """Test31 --chmod accepts octal and symbolic notation."""
        self.assertEqual(ContainerBuilder._chmod_spec("755", 0o644, False),
                         0o755)
        self.assertEqual(ContainerBuilder._chmod_spec("+x", 0o644, False),
                         0o755)
        self.assertEqual(ContainerBuilder._chmod_spec("u=rwX,go=rX", 0o644,
                                                      False), 0o644)
        self.assertEqual(ContainerBuilder._chmod_spec("u=rwX,go=rX", 0o644,
                                                      True), 0o755)
        self.assertEqual(ContainerBuilder._chmod_spec("g=u", 0o600, False),
                         0o660)
        self.assertIsNone(ContainerBuilder._chmod_spec("abc", 0o644, False))

    def test_32_do_copy_chmod(self):
        """Test32 COPY --chmod applies the mode to copied files."""
        tmpdir = tempfile.mkdtemp()
        try:
            context = os.path.join(tmpdir, "ctx")
            container = os.path.join(tmpdir, "container")
            os.makedirs(context)
            os.makedirs(container + "/ROOT")
            with open(os.path.join(context, "f.txt"), "w") as filep:
                filep.write("x")
            os.chmod(os.path.join(context, "f.txt"), 0o600)
            self.mock_lrepo.cd_container.return_value = container
            builder = ContainerBuilder(self.mock_lrepo, "CID", context)
            self.assertTrue(builder._do_copy("--chmod=755 f.txt /f.txt"))
            target = container + "/ROOT/f.txt"
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o755)
            self.assertFalse(builder._do_copy("--chmod=abc f.txt /g.txt"))
        finally:
            shutil.rmtree(tmpdir)

    def test_33_do_copy_chown(self):
        """Test33 COPY --chown accepts numeric ids, unknown names fail."""
        tmpdir = tempfile.mkdtemp()
        try:
            context = os.path.join(tmpdir, "ctx")
            container = os.path.join(tmpdir, "container")
            os.makedirs(context)
            os.makedirs(container + "/ROOT")
            with open(os.path.join(context, "f.txt"), "w") as filep:
                filep.write("x")
            self.mock_lrepo.cd_container.return_value = container
            builder = ContainerBuilder(self.mock_lrepo, "CID", context)
            self.assertTrue(builder._do_copy(
                "--chown=1000:1000 f.txt /f.txt"))
            self.assertFalse(builder._do_copy(
                "--chown=nosuchuser f.txt /g.txt"))
        finally:
            shutil.rmtree(tmpdir)

    def test_34_do_shell(self):
        """Test34 SHELL sets the shell used by shell form commands."""
        builder = self._builder()
        self.assertTrue(builder._do_shell('["/bin/bash", "-c"]'))
        self.assertEqual(builder.shell, ["/bin/bash", "-c"])
        builder._do_cmd("echo hi")
        self.assertEqual(builder.config["Cmd"],
                         ["/bin/bash", "-c", "echo hi"])
        self.assertFalse(builder._do_shell("bash"))
        self.assertFalse(builder._do_shell("[]"))

    def test_35_do_expose(self):
        """Test35 EXPOSE validates ports."""
        builder = self._builder()
        self.assertTrue(builder._do_expose("8080 53/udp"))
        self.assertEqual(builder.config["ExposedPorts"],
                         {"8080/tcp": {}, "53/udp": {}})
        self.assertFalse(builder._do_expose("abc"))
        self.assertFalse(builder._do_expose("70000"))

    def test_36_do_add_unpack_false(self):
        """Test36 ADD --unpack=false copies the archive as a file."""
        tmpdir = tempfile.mkdtemp()
        try:
            context = os.path.join(tmpdir, "ctx")
            container = os.path.join(tmpdir, "container")
            os.makedirs(context)
            os.makedirs(container + "/ROOT")
            with tarfile.open(os.path.join(context, "a.tar"), "w") as tfile:
                data = b"content"
                info = tarfile.TarInfo("inner.txt")
                info.size = len(data)
                tfile.addfile(info, io.BytesIO(data))
            self.mock_lrepo.cd_container.return_value = container
            builder = ContainerBuilder(self.mock_lrepo, "CID", context)
            self.assertTrue(builder._do_add("--unpack=false a.tar /a.tar"))
            self.assertTrue(os.path.isfile(container + "/ROOT/a.tar"))
            self.assertFalse(os.path.exists(container + "/ROOT/inner.txt"))
        finally:
            shutil.rmtree(tmpdir)

    def test_37_extract_tar_xattrs(self):
        """Test37 ADD restores pax extended attributes."""
        if not hasattr(os, "setxattr"):
            return
        tmpdir = tempfile.mkdtemp()
        try:
            root = os.path.join(tmpdir, "ROOT")
            os.makedirs(root)
            probe = os.path.join(tmpdir, "probe")
            with open(probe, "w"):
                pass
            try:
                os.setxattr(probe, "user.test", b"1")
            except (IOError, OSError):
                return
            tarpath = os.path.join(tmpdir, "x.tar")
            with tarfile.open(tarpath, "w",
                              format=tarfile.PAX_FORMAT) as tfile:
                data = b"x"
                info = tarfile.TarInfo("x.txt")
                info.size = len(data)
                info.pax_headers = {"SCHILY.xattr.user.test": "1"}
                tfile.addfile(info, io.BytesIO(data))
            builder = self._builder()
            self.assertTrue(builder._extract_tar(tarpath, root))
            self.assertEqual(os.getxattr(os.path.join(root, "x.txt"),
                                         "user.test"), b"1")
        finally:
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    main()
