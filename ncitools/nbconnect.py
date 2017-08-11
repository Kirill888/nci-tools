import click
import paramiko
from pathlib import Path
import json


def warn(*args, **kwargs):
    from sys import stderr
    print(*args, file=stderr, **kwargs)


def load_nbserver_configs(sftp):

    def parse(fname):
        with sftp.open(fname) as f:
            cfg = json.loads(f.read().decode('utf-8'))
            cfg['mtime'] = f.stat().st_mtime
            return cfg

    p = '.local/share/jupyter/runtime/'
    for f in sftp.listdir(p):
        if f.startswith('nbserver-') and f.endswith('.json'):
            yield parse(p + f)


def nbserver_all_configs(sftp):
    cfgs = list(load_nbserver_configs(sftp))
    cfgs.sort(key=lambda c: c.get('mtime', 0), reverse=True)
    return cfgs


def get_ssh_config(name):
    cfg = paramiko.SSHConfig()

    try:
        with open(str(Path.home()/".ssh/config")) as f:
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


def mk_url(nb_cfg, lport):
    return 'http://localhost:{lport}{base_url}?token={token}'.format(lport=lport, **nb_cfg)


def launch_url(url):
    import sys
    import os
    import subprocess

    if sys.platform == 'win32':
        os.startfile(url)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', url])
    else:
        try:
            subprocess.Popen(['xdg-open', url])
        except OSError:
            print('See: ' + url)


@click.command(name='nbconnect')
@click.argument('ssh_host', default='raijin.nci.org.au')
@click.option('--user', help='SSH user name, if not given will be read from ~/.ssh/config')
@click.option('--local-port', type=int, default=5566, help='Local port to use for ssh forwarding')
def main(ssh_host, user=None, local_port=5566):
    ssh_cfg = get_ssh_config(ssh_host)

    if user is not None:
        ssh_cfg['user'] = user

    ssh = mk_ssh(ssh_cfg)
    cfgs = nbserver_all_configs(ssh.open_sftp())

    if len(cfgs) == 0:
        warn('# no configs')
        return 1

    nb_cfg = cfgs[0]
    url = mk_url(nb_cfg, local_port)

    if len(cfgs) > 1:
        warn('# **WARNING**: found more than one config')

    tunnel = launch_tunnel(ssh_cfg, nb_cfg, local_port)

    warn(url)
    launch_url(url)

    while tunnel.is_active:
        k = input('Tunnel is running, press q then <Enter> to quit\n > ')
        if k == 'q':
            tunnel.stop()

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
