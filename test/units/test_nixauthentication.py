#!/usr/bin/env python
"""
udocker unit tests: NixAuthentication
"""
import pwd
import grp
from udocker.helper.nixauth import NixAuthentication


def test_01_user_in_subuid(mocker):
    """Test01 NixAuthentication().user_in_subuid."""
    sub_file = ("user1:100000:65536\n"
                "user2:165536:65536")
    uinfo = ("user2", "1000", "1000", "usr", "/home/user", "/bin/bash")
    mock_file = mocker.mock_open(read_data=sub_file)
    mocker.patch("builtins.open", mock_file)
    mock_userfile = mocker.patch.object(NixAuthentication, '_get_user_from_file',
                                        return_value=uinfo)
    mock_userhost = mocker.patch.object(NixAuthentication, '_get_user_from_host')
    auth = NixAuthentication(passwd_file='/etc/passwd', group_file='/etc/group',
                             subuid_file=sub_file)
    out = auth.user_in_subuid('user2')
    assert out == [("165536", "65536")]
    mock_file.assert_called()
    mock_userfile.assert_called()
    mock_userhost.assert_not_called()


def test_02_user_in_subuid(mocker):
    """Test02 NixAuthentication().user_in_subuid."""
    sub_file = ("user1:100000:65536\n"
                "user2:165536:65536")
    uinfo = ("user2", "1000", "1000", "usr", "/home/user", "/bin/bash")
    mock_file = mocker.mock_open(read_data=sub_file)
    mocker.patch("builtins.open", mock_file)
    mock_userfile = mocker.patch.object(NixAuthentication, '_get_user_from_file')
    mock_userhost = mocker.patch.object(NixAuthentication, '_get_user_from_host',
                                        return_value=uinfo)
    auth = NixAuthentication(subuid_file=sub_file)
    out = auth.user_in_subuid('user2')
    assert out == [("165536", "65536")]
    mock_file.assert_called()
    mock_userfile.assert_not_called()
    mock_userhost.assert_called()


def test_03_user_in_subuid(mocker):
    """Test03 NixAuthentication().user_in_subuid."""
    sub_file = ("user1:100000:65536\n"
                "user2:165536:65536")
    uinfo = ("user2", "1000", "1000", "usr", "/home/user", "/bin/bash")
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    mock_userfile = mocker.patch.object(NixAuthentication, '_get_user_from_file')
    mock_userhost = mocker.patch.object(NixAuthentication, '_get_user_from_host',
                                        return_value=uinfo)
    auth = NixAuthentication(subuid_file=sub_file)
    out = auth.user_in_subuid('user2')
    assert out == []
    mock_userfile.assert_not_called()
    mock_userhost.assert_called()


def test_04_user_in_subgid(mocker):
    """Test04 NixAuthentication().user_in_subgid."""
    mock_subid = mocker.patch.object(NixAuthentication, '_user_in_subid',
                                     return_value=[("165536", "65536")])
    auth = NixAuthentication()
    out = auth.user_in_subgid('user2')
    assert out == [("165536", "65536")]
    mock_subid.assert_called()


def test_09_add_user(mocker):
    """Test09 NixAuthentication().add_user()."""
    uinfo = "root:pw:0:0:gecos:/home:/bin/bash\n"
    mock_get = mocker.patch('udocker.helper.nixauth.FileUtil.getdata', return_value=uinfo)
    mock_put = mocker.patch('udocker.helper.nixauth.FileUtil.putdata')
    auth = NixAuthentication()
    out = auth.add_user("root", "pw", 0, 0, "gecos", "/home", "/bin/bash")
    assert out
    mock_get.assert_called()
    mock_put.assert_not_called()


def test_10_add_user(mocker):
    """Test10 NixAuthentication().add_user()."""
    uget = "user:upw:1000:1000:gecos:/home/user:/bin/bash\n"
    uput = "root:pw:0:0:gecos:/home:/bin/bash\n"
    mock_get = mocker.patch('udocker.helper.nixauth.FileUtil.getdata', return_value=uget)
    mock_put = mocker.patch('udocker.helper.nixauth.FileUtil.putdata', return_value=uput)
    auth = NixAuthentication()
    out = auth.add_user("root", "pw", 0, 0, "gecos", "/home", "/bin/bash")
    assert out == uput
    mock_get.assert_called()
    mock_put.assert_called()


def test_11_add_group(mocker):
    """Test11 NixAuthentication().add_group()."""
    uinfo = "group1:x:1001:user1,user2,\n"
    mock_get = mocker.patch('udocker.helper.nixauth.FileUtil.getdata', return_value=uinfo)
    mock_put = mocker.patch('udocker.helper.nixauth.FileUtil.putdata')
    auth = NixAuthentication()
    out = auth.add_group("group1", 1001, users=["user1", "user2"])
    assert out
    mock_get.assert_called()
    mock_put.assert_not_called()


def test_12_add_group(mocker):
    """Test12 NixAuthentication().add_group()."""
    uget = "group1:x:1001:user1,user2,\n"
    uput = "group2:x:1002:user3,user4,\n"
    mock_get = mocker.patch('udocker.helper.nixauth.FileUtil.getdata', return_value=uget)
    mock_put = mocker.patch('udocker.helper.nixauth.FileUtil.putdata', return_value=uput)
    auth = NixAuthentication()
    out = auth.add_group("group2", 1002, users=["user3", "user4"])
    assert out == uput
    mock_get.assert_called()
    mock_put.assert_called()


def test_13_get_user(mocker):
    """Test13 NixAuthentication().get_user(). From host uid exist"""
    usr = pwd.struct_passwd(["root", "*", "0", "0", "root usr", "/root", "/bin/bash"])
    usr_tuple = (usr.pw_name, str(usr.pw_uid), str(usr.pw_gid),
                 usr.pw_gecos, usr.pw_dir, usr.pw_shell)
    mock_getpwuid = mocker.patch('udocker.helper.nixauth.pwd.getpwuid', return_value=usr)
    mock_getpwnam = mocker.patch('udocker.helper.nixauth.pwd.getpwnam')
    auth = NixAuthentication()
    out = auth.get_user(0)
    assert out == usr_tuple
    mock_getpwuid.assert_called()
    mock_getpwnam.assert_not_called()


def test_14_get_user(mocker):
    """Test14 NixAuthentication().get_user(). From host uid not exist"""
    usr = pwd.struct_passwd(["root", "*", "0", "0", "root usr", "/root", "/bin/bash"])
    usr_tuple = ("", "", "", "", "", "")
    mock_getpwuid = mocker.patch('udocker.helper.nixauth.pwd.getpwuid', side_effect=OSError)
    mock_getpwnam = mocker.patch('udocker.helper.nixauth.pwd.getpwnam')
    auth = NixAuthentication()
    out = auth.get_user(1001)
    assert out == usr_tuple
    mock_getpwuid.assert_called()
    mock_getpwnam.assert_not_called()


def test_15_get_user(mocker):
    """Test15 NixAuthentication().get_user(). From host name exit"""
    usr = pwd.struct_passwd(["root", "*", "0", "0", "root usr", "/root", "/bin/bash"])
    usr_tuple = (usr.pw_name, str(usr.pw_uid), str(usr.pw_gid),
                 usr.pw_gecos, usr.pw_dir, usr.pw_shell)
    mock_getpwuid = mocker.patch('udocker.helper.nixauth.pwd.getpwuid')
    mock_getpwnam = mocker.patch('udocker.helper.nixauth.pwd.getpwnam', return_value=usr)
    auth = NixAuthentication()
    out = auth.get_user('root')
    assert out == usr_tuple
    mock_getpwuid.assert_not_called()
    mock_getpwnam.assert_called()


def test_16_get_user(mocker):
    """Test16 NixAuthentication().get_user(). From host name not exist"""
    usr = pwd.struct_passwd(["root", "*", "0", "0", "root usr", "/root", "/bin/bash"])
    usr_tuple = ("", "", "", "", "", "")
    mock_getpwuid = mocker.patch('udocker.helper.nixauth.pwd.getpwuid')
    mock_getpwnam = mocker.patch('udocker.helper.nixauth.pwd.getpwnam', side_effect=OSError)
    auth = NixAuthentication()
    out = auth.get_user('user')
    assert out == usr_tuple
    mock_getpwuid.assert_not_called()
    mock_getpwnam.assert_called()


def test_17_get_user(mocker):
    """Test17 NixAuthentication().get_user(). From file uid exist"""
    pwd_file = 'root:x:0:0:root user:/root:/bin/bash\n'
    usr_tuple = ('root', '0', '0', 'root user', '/root', '/bin/bash')
    mock_file = mocker.mock_open(read_data=pwd_file)
    mocker.patch("builtins.open", mock_file)
    auth = NixAuthentication(passwd_file=pwd_file)
    out = auth.get_user(0)
    assert out == usr_tuple
    mock_file.assert_called()


def test_18_get_user(mocker):
    """Test18 NixAuthentication().get_user(). From file uid not exist"""
    pwd_file = 'root:x:0:0:root user:/root:/bin/bash\n'
    usr_tuple = ("", "", "", "", "", "")
    mock_file = mocker.mock_open(read_data=pwd_file)
    mocker.patch("builtins.open", mock_file)
    auth = NixAuthentication(passwd_file=pwd_file)
    out = auth.get_user(1001)
    assert out == usr_tuple
    mock_file.assert_called()


def test_19_get_user(mocker):
    """Test19 NixAuthentication().get_user(). From file name exist"""
    pwd_file = 'root:x:0:0:root user:/root:/bin/bash\n'
    usr_tuple = ('root', '0', '0', 'root user', '/root', '/bin/bash')
    mock_file = mocker.mock_open(read_data=pwd_file)
    mocker.patch("builtins.open", mock_file)
    auth = NixAuthentication(passwd_file=pwd_file)
    out = auth.get_user('root')
    assert out == usr_tuple
    mock_file.assert_called()


def test_20_get_user(mocker):
    """Test20 NixAuthentication().get_user(). From file name not exist"""
    pwd_file = 'root:x:0:0:root user:/root:/bin/bash\n'
    usr_tuple = ("", "", "", "", "", "")
    mock_file = mocker.mock_open(read_data=pwd_file)
    mocker.patch("builtins.open", mock_file)
    auth = NixAuthentication(passwd_file=pwd_file)
    out = auth.get_user('user')
    assert out == usr_tuple
    mock_file.assert_called()


def test_21_get_user(mocker):
    """Test21 NixAuthentication().get_user(). From file oserror"""
    pwd_file = 'root:x:0:0:root user:/root:/bin/bash\n'
    usr_tuple = ("", "", "", "", "", "")
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    auth = NixAuthentication(passwd_file=pwd_file)
    out = auth.get_user('')
    assert out == usr_tuple
    mock_file.assert_not_called()


def test_22_get_group(mocker):
    """Test22 NixAuthentication().get_group(). From host gid exist"""
    grp_struct = grp.struct_group(["root", "*", "0", str(['root', 'admin'])])
    grp_tuple = (grp_struct.gr_name, str(grp_struct.gr_gid), grp_struct.gr_mem)
    mock_getgrgid = mocker.patch('udocker.helper.nixauth.grp.getgrgid', return_value=grp_struct)
    mock_getgrnam = mocker.patch('udocker.helper.nixauth.grp.getgrnam')
    auth = NixAuthentication()
    out = auth.get_group(0)
    assert out == grp_tuple
    mock_getgrgid.assert_called()
    mock_getgrnam.assert_not_called()


def test_23_get_group(mocker):
    """Test23 NixAuthentication().get_group(). From host gid not exist"""
    grp_struct = grp.struct_group(["root", "*", "0", str(['root', 'admin'])])
    grp_tuple = ("", "", "")
    mock_getgrgid = mocker.patch('udocker.helper.nixauth.grp.getgrgid', side_effect=OSError)
    mock_getgrnam = mocker.patch('udocker.helper.nixauth.grp.getgrnam')
    auth = NixAuthentication()
    out = auth.get_group(1000)
    assert out == grp_tuple
    mock_getgrgid.assert_called()
    mock_getgrnam.assert_not_called()


def test_24_get_group(mocker):
    """Test24 NixAuthentication().get_group(). From host groupname exist"""
    grp_struct = grp.struct_group(["root", "*", "0", str(['root', 'admin'])])
    grp_tuple = (grp_struct.gr_name, str(grp_struct.gr_gid), grp_struct.gr_mem)
    mock_getgrgid = mocker.patch('udocker.helper.nixauth.grp.getgrgid')
    mock_getgrnam = mocker.patch('udocker.helper.nixauth.grp.getgrnam', return_value=grp_struct)
    auth = NixAuthentication()
    out = auth.get_group('root')
    assert out == grp_tuple
    mock_getgrgid.assert_not_called()
    mock_getgrnam.assert_called()


def test_25_get_group(mocker):
    """Test25 NixAuthentication().get_group(). From host groupname not exist"""
    grp_struct = grp.struct_group(["root", "*", "0", str(['root', 'admin'])])
    grp_tuple = ("", "", "")
    mock_getgrgid = mocker.patch('udocker.helper.nixauth.grp.getgrgid')
    mock_getgrnam = mocker.patch('udocker.helper.nixauth.grp.getgrnam', side_effect=OSError)
    auth = NixAuthentication()
    out = auth.get_group('user')
    assert out == grp_tuple
    mock_getgrgid.assert_not_called()
    mock_getgrnam.assert_called()


def test_26_get_group(mocker):
    """Test26 NixAuthentication().get_group(). From file gid exist"""
    grp_file = 'root:x:0:root,admin\n'
    grp_tuple = ('root', '0', 'root,admin')
    mock_file = mocker.mock_open(read_data=grp_file)
    mocker.patch("builtins.open", mock_file)
    auth = NixAuthentication(group_file=grp_file)
    out = auth.get_group(0)
    assert out == grp_tuple
    mock_file.assert_called()


def test_27_get_group(mocker):
    """Test27 NixAuthentication().get_group(). From file gid not exist"""
    grp_file = 'root:x:0:root,admin\n'
    grp_tuple = ('', '', '')
    mock_file = mocker.mock_open(read_data=grp_file)
    mocker.patch("builtins.open", mock_file)
    auth = NixAuthentication(group_file=grp_file)
    out = auth.get_group(1000)
    assert out == grp_tuple
    mock_file.assert_called()


def test_28_get_group(mocker):
    """Test28 NixAuthentication().get_group(). From file groupname exist"""
    grp_file = 'root:x:0:root,admin\n'
    grp_tuple = ('root', '0', 'root,admin')
    mock_file = mocker.mock_open(read_data=grp_file)
    mocker.patch("builtins.open", mock_file)
    auth = NixAuthentication(group_file=grp_file)
    out = auth.get_group('root')
    assert out == grp_tuple
    mock_file.assert_called()


def test_29_get_group(mocker):
    """Test29 NixAuthentication().get_group(). From file groupname not exist"""
    grp_file = 'root:x:0:root,admin\n'
    grp_tuple = ('', '', '')
    mock_file = mocker.mock_open(read_data=grp_file)
    mocker.patch("builtins.open", mock_file)
    auth = NixAuthentication(group_file=grp_file)
    out = auth.get_group('group')
    assert out == grp_tuple
    mock_file.assert_called()


def test_30_get_group(mocker):
    """Test30 NixAuthentication().get_group(). From groupfile oserror"""
    grp_file = 'root:x:0:root,admin\n'
    grp_tuple = ('', '', '')
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    auth = NixAuthentication(group_file=grp_file)
    out = auth.get_group('')
    assert out == grp_tuple
    mock_file.assert_not_called()


def test_31_get_home(mocker):
    """Test31 NixAuthentication().get_home()."""
    uinfo = ('root', '0', '0', 'root', '/root', '/bin/bash')
    mock_user = mocker.patch.object(NixAuthentication, 'get_user', return_value=uinfo)
    auth = NixAuthentication()
    out = auth.get_home()
    assert out == '/root'
    mock_user.assert_called()


def test_32_get_home(mocker):
    """Test32 NixAuthentication().get_home()."""
    uinfo = ('', '', '', '', '', '')
    mock_user = mocker.patch.object(NixAuthentication, 'get_user', return_value=uinfo)
    auth = NixAuthentication()
    out = auth.get_home()
    assert out == ''
    mock_user.assert_called()
