import os
import pytest
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_bin(host):
    cmd = host.run('/usr/local/bin/k3s --version')
    assert cmd.rc == 0
    assert cmd.stdout == "k3s version v0.5.0 (8c0116dd)"


@pytest.mark.parametrize('path, mode', [
    ('/usr/local/bin/k3s', '0o755'),
    ('/usr/local/bin/k3s-killall.sh', '0o755')
])
def test_files(host, path, mode):
    f = host.file(path)

    assert f.exists
    assert f.is_file
    assert f.user == 'root'
    assert f.group == 'root'
    assert oct(f.mode) == mode


@pytest.mark.parametrize('path, target', [
    ('/usr/local/bin/kubectl', '/usr/local/bin/k3s'),
    ('/usr/local/bin/crictl', '/usr/local/bin/k3s'),
])
def test_symlinks(host, path, target):
    f = host.file(path)

    assert f.exists
    assert f.is_symlink
    assert f.linked_to == target
    assert f.user == 'root'
    assert f.group == 'root'


def test_uninstall_script(host):
    ansible_vars = host.ansible.get_variables()
    role = ansible_vars['k3s_role']
    script_path = '/usr/local/bin/{role}-uninstall.sh'.format(role=role)
    f = host.file(script_path)

    assert f.exists
    assert f.is_file
    assert f.user == 'root'
    assert f.group == 'root'
    assert oct(f.mode) == '0o755'
