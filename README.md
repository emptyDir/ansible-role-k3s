# Ansible Role: k3s

An Ansible role that installs [k3s](https://k3s.io/) on Linux. 

This role is designed to more or less implement the [install.sh](https://github.com/rancher/k3s/blob/master/install.sh) script from the k3s source code repository in Ansible.

## Requirements

No additional packages are required for this role.

## Role Variables

See [defaults/main.yml](defaults/main.yml) for a detailed overview of the available variables for this role. Here is a sample of some variables and their defaults:

```yaml
    k3s_version: 0.5.0
    k3s_role: server    # Can be server or agent

    ## This is the name to use for the service (either k3s or k3s-agent)
    k3s_system_name: 'k3s{% if k3s_role == "agent" %}-agent{% endif %}'
    k3s_bin_dir: /usr/local/bin
    k3s_etc_dir: /etc/rancher/k3s
    k3s_lib_dir: /var/lib/rancher/k3s
    k3s_logrotate_dir: /etc/logrotate.d
    k3s_killall_script: k3s-killall.sh
    k3s_uninstall_script: "{{ k3s_role }}-uninstall.sh"
    k3s_server_log: "/var/log/{{ k3s_system_name }}.log"
```

At a minimum it's important to specify the `k3s_role` when using this role in your playbooks. This will determine whether to install a k3s master server or as an agent in an existing cluster. Valid values for this variable are `server` and `agent`, with the role defaulting to `server`.

If running k3s as an `agent` the following options need to be set:

```yaml
k3s_token: <token_value>
k3s_url: https://your-k3s-server.example.com:6443
```

The `k3s_url` should be the url to the k3s server whose cluster you want to join the agent to, and the token can be found on the k3s server in `/var/lib/rancher/k3s/server/node-token`.

The `k3s_version` variable will determine which [k3s release](https://github.com/rancher/k3s/releases) is installed. The role will automatically determine whether to use the amd64 or arm binaries based on the value of the `ansible_architecture` fact. This role defaults to and has been tested with `0.5.0`, though as of this writing `0.6.1` is the latest release.

This role only supports systems with `systemd` or `openrc` as their `ansible_service_mgr`. This is a limitation of the original script that I based this role on, but there's no reason it can't be expanded to support other init systems. In [tasks/main.yml](tasks/main.yml) there is a task that checks the `ansible_service_mgr` against the `k3s_supported_init_types`. This check will fail the playbook before attempting to set up a `k3s` service. If this role is expanded to support other init systems this list should be expanded or the check should be removed.

There are a number of configurable parameters that apply to different use cases for this role. Some
configure command-line options passed to k3s at runtime. Some cli options apply only to k3s servers, and some are only required for k3s agents. You should review the [k3s documenation](https://github.com/rancher/k3s/blob/master/README.md) in order to determine which settings you need for your specific use case(s).

### systemd-specific options

The following variables are only used for `systemd`-based systems. Most have sensible defaults, but can be overridded if necessary.

```yaml
k3s_systemd_dir: /etc/systemd/system
k3s_systemd_service_name: "{{ k3s_system_name }}.service"
k3s_systemd_service: "{{ k3s_systemd_dir }}/{{ k3s_systemd_service_name }}"
k3s_systemd_env: "{{ k3s_systemd_dir }}/{{ k3s_systemd_service_name }}.env"
k3s_systemd_use_logfile: false
```

Systemd services by default log to the system's `journald`, but if you want to configure k3s to log to a specific file on systemd systems you can set `k3s_systemd_use_logfile` to `true`. This will use the `--log` option at runtime to tell k3s to log to the file specified by `k3s_server_log`.

### K3s Runtime Arguments

Most runtime arguments are set by the CLI options passed to k3s by the relevant service manager startup command. Some options can be used with both the server and the agent. Some are server or agent specific. This should be specified in the variable name. All variables for this role start with `k3s_`, with `k3s_server_` and `k3s_agent_` prepending variables specific for either a server or agent. Because servers can also run an agent you can specify `k3s_agent_` variables for hosts running the `server` role as long as `k3s_server_disable_agent` is `false`.

Some variables when set to `false` will leave out the CLI option, but will pass the appopriate flag or option if a value is set. For example, `k3s_token` is `false`, but if a token value is set it will be passed to k3s as `--token <value>` at runtime.

Variable names are designed to match the corresponsing cli argument. Arguments which have a corresponding environment variable will use a similar name to the environment variable (e.g. `k3s_url`), and will be set in the environment file sourced by the k3s service, though I found in testing that some of them don't always work reliably when set that way so they are specified as command-line arguments.

Any variable which has a default specified in the k3s `--help` output defaults to that given value.

Output from the `--help` flag was used as a reference to determine the configuration and naming of the variables for this role and can be referred to for more information:

```bash
$ k3s server --help
NAME:
  k3s server - Run management server

USAGE:
  k3s server [OPTIONS]

OPTIONS:
  --bind-address value                k3s bind address (default: localhost)
  --https-listen-port value           HTTPS listen port (default: 6443)
  --http-listen-port value            HTTP listen port (for /healthz, HTTPS redirect, and port for TLS terminating LB) (default: 0)
  --data-dir value, -d value          Folder to hold state default /var/lib/rancher/k3s or ${HOME}/.rancher/k3s if not root
  --disable-agent                     Do not run a local agent and register a local kubelet
  --log value, -l value               Log to file
  --cluster-cidr value                Network CIDR to use for pod IPs (default: "10.42.0.0/16")
  --cluster-secret value              Shared secret used to bootstrap a cluster [$K3S_CLUSTER_SECRET]
  --service-cidr value                Network CIDR to use for services IPs (default: "10.43.0.0/16")
  --cluster-dns value                 Cluster IP for coredns service. Should be in your service-cidr range
  --cluster-domain value              Cluster Domain (default: "cluster.local")
  --no-deploy value                   Do not deploy packaged components (valid items: coredns, servicelb, traefik)
  --write-kubeconfig value, -o value  Write kubeconfig for admin client to this file [$K3S_KUBECONFIG_OUTPUT]
  --write-kubeconfig-mode value       Write kubeconfig with this mode [$K3S_KUBECONFIG_MODE]
  --tls-san value                     Add additional hostname or IP as a Subject Alternative Name in the TLS cert
  --kube-apiserver-arg value          Customized flag for kube-apiserver process
  --kube-scheduler-arg value          Customized flag for kube-scheduler process
  --kube-controller-arg value         Customized flag for kube-controller-manager process
  --rootless                          (experimental) Run rootless
  --node-ip value, -i value           (agent) IP address to advertise for node
  --node-name value                   (agent) Node name [$K3S_NODE_NAME]
  --docker                            (agent) Use docker instead of containerd
  --no-flannel                        (agent) Disable embedded flannel
  --flannel-iface value               (agent) Override default flannel interface
  --container-runtime-endpoint value  (agent) Disable embedded containerd and use alternative CRI implementation
  --pause-image value                 (agent) Customized pause image for containerd sandbox
  --resolv-conf value                 (agent) Kubelet resolv.conf file [$K3S_RESOLV_CONF]
  --kubelet-arg value                 (agent) Customized flag for kubelet process
  --kube-proxy-arg value              (agent) Customized flag for kube-proxy process
```

```bash
$ k3s agent --help
NAME:
  k3s agent - Run node agent

USAGE:
  k3s agent [OPTIONS]

OPTIONS:
  --token value, -t value             Token to use for authentication [$K3S_TOKEN]
  --token-file value                  Token file to use for authentication [$K3S_TOKEN_FILE]
  --server value, -s value            Server to connect to [$K3S_URL]
  --data-dir value, -d value          Folder to hold state (default: "/var/lib/rancher/k3s")
  --cluster-secret value              Shared secret used to bootstrap a cluster [$K3S_CLUSTER_SECRET]
  --rootless                          (experimental) Run rootless
  --docker                            (agent) Use docker instead of containerd
  --no-flannel                        (agent) Disable embedded flannel
  --flannel-iface value               (agent) Override default flannel interface
  --node-name value                   (agent) Node name [$K3S_NODE_NAME]
  --node-ip value, -i value           (agent) IP address to advertise for node
  --container-runtime-endpoint value  (agent) Disable embedded containerd and use alternative CRI implementation
  --pause-image value                 (agent) Customized pause image for containerd sandbox
  --resolv-conf value                 (agent) Kubelet resolv.conf file [$K3S_RESOLV_CONF]
  --kubelet-arg value                 (agent) Customized flag for kubelet process
  --kube-proxy-arg value              (agent) Customized flag for kube-proxy process
```

You can also refer to [defaults/main.yml](defaults/main.yml) for more details.

## Dependencies

This role has no external dependencies.

## Example Playbook

Server playbook:

```yaml
---
- name: Install k3s as a server
  hosts: k3s_servers
  become: true
  roles:
    - { role: emptyDir.k3s, k3s_role: server }
```

Agent playbook:

```yaml
---
- name: Install k3s as an agent
  hosts: k3s_agents
  become: true
  vars:
    k3s_url: https://k3s-server.example.com:6443
    k3s_token: <token> # This is for example purposes. This var should probably be kept in a vault.
  roles:
    - { role: emptyDir.k3s, k3s_role: agent }
```

## Testing

This role includes a few test scenarios using [molecule](https://molecule.readthedocs.io/en/stable/) with the [ec2 driver](https://molecule.readthedocs.io/en/stable/configuration.html#ec2). Docker would be preferrable, but most containers don't include all of the features necessary for k3s so it was ultimately simpler to just use a full Linux VM.

It's necessary to set an ec2 region when using molecule, and in this case all of the AMI ids and subnets are from `us-east-1`. You may need to edit the platforms in `molecule.yaml` for each test suite with the subnet/ami ids necessary for your particular region/account. Some more detail can be found in [this article](https://blog.codecentric.de/en/2019/01/ansible-molecule-travisci-aws/).

There are currently three scenarios that cover a few different aspects of the role:

**[aws-ec2-funtoo13](molecule/aws-ec2-funtoo13)**

Uses t2.micro instances with the [Funtoo Linux 1.3 AMI](https://aws.amazon.com/marketplace/pp/B07KT3VN7Q). Funtoo is used because an OS which uses openrc was needed, but the Alpine AMI doesn't include some of the kernel features necessary for k3s to work.

**[aws-ec2-ubuntu1804](molecule/aws-ec2-ubuntu1804)**

Tests the systemd portion of the role with Ubuntu 18.04 LTS on t3.nano instances.

**[aws-ec2-ubuntu1804-arm64](molecule/aws-ec2-ubuntu1804-arm64)**

Same as the standard Ubuntu scenario, but using `a1.medium` instances to verify that the arm binary is detected properly.

### Setup

- Set up your [AWS credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).
- Install the necessary libraries:

```bash
pip install -r test_requirements.txt
```

- Set `EC2_REGION` in your environment to the region you want to use:

```bash
export EC2_REGION=us-east-1
```

Running the full test sequence for your chosen scenario. There is no default scenario, so it's necessary to specify your scenario explicitly with the `-s` option. `molecule test` will run the full suite:

```bash
molecule test -s aws-ec2-ubuntu1804
```

See the [molecule documentation](https://molecule.readthedocs.io/en/stable/getting-started.html) for more detail on using molecule tests scenarios.

## License

[MIT](LICENSE)

## Author Information

This role was created in June of 2019 by [Adam Duston](https://github.com/emptyDir).
