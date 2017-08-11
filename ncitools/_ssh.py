import paramiko
from pathlib import Path

__all__ = ['open_ssh', 'launch_tunnel']


def get_ssh_config(name):
    cfg = paramiko.SSHConfig()

    try:
        with open(str(Path.home()/".ssh"/"config"), 'rt') as f:
            cfg.parse(f)
            return cfg.lookup(name)
    except FileNotFoundError:
        return {'hostname': name}


def mk_ssh(cfg):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_server = cfg['hostname']
    ssh_user = cfg.get('user')

    ssh.connect(ssh_server,
                username=ssh_user)

    return ssh


def open_ssh(host, user=None):
    cfg = get_ssh_config(host)

    if user is not None:
        cfg['user'] = user

    return mk_ssh(cfg), cfg


def launch_tunnel(ssh_cfg, nb_cfg, lport):
    from sshtunnel import SSHTunnelForwarder

    ssh_user = ssh_cfg.get('user')
    ssh_server = ssh_cfg.get('hostname')

    tunnel = SSHTunnelForwarder(ssh_server,
                                ssh_username=ssh_user,
                                local_bind_address=('localhost', lport),
                                remote_bind_address=(nb_cfg.get('hostname'),
                                                     nb_cfg.get('port')))
    tunnel.start()
    return tunnel
