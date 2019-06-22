import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_service_enabled(host):
    ansible_vars = host.ansible.get_variables()
    role = ansible_vars['k3s_role']
    service_name = 'k3s'
    if role == 'agent':
        service_name += '-agent'

    service = host.service(service_name)

    assert service.is_enabled


def test_service_files(host):
    ansible_vars = host.ansible.get_variables()
    role = ansible_vars['k3s_role']
    service_name = 'k3s'
    if role == 'agent':
        service_name += '-agent'
    service_mgr = host.ansible('setup')['ansible_facts']['ansible_service_mgr']
    if service_mgr == 'systemd':
        env_file = host.file('/etc/systemd/system/' + service_name + '.service.env')
        assert env_file.exists
        assert env_file.is_file
        assert oct(env_file.mode) == '0o600'
        unit_file = host.file('/etc/systemd/system/' + service_name + '.service')
        assert unit_file.exists
        assert unit_file.is_file
        assert oct(unit_file.mode) == '0o644'
    if service_mgr == 'openrc':
        etc_dir = host.file('/etc/rancher/k3s')
        assert etc_dir.exists
        assert etc_dir.is_directory
        assert oct(etc_dir.mode) == '0o755'
        env_file = host.file('/etc/rancher/k3s/' + service_name + '.env')
        assert env_file.exists
        assert env_file.is_file
        assert oct(env_file.mode) == '0o600'
        logrotate_conf = host.file('/etc/logrotate.d/' + service_name)
        assert logrotate_conf.exists
        assert logrotate_conf.is_file
        assert oct(logrotate_conf.mode) == '0o644'
