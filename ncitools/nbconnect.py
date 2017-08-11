import click


def warn(*args, **kwargs):
    from sys import stderr
    print(*args, file=stderr, **kwargs)


def load_nbserver_configs(sftp, jupyter_runtime='.local/share/jupyter/runtime/'):
    import json

    if not jupyter_runtime.endswith('/'):
        jupyter_runtime += '/'

    def parse(fname):
        with sftp.open(fname) as f:
            cfg = json.loads(f.read().decode('utf-8'))
            cfg['mtime'] = f.stat().st_mtime
            return cfg

    for f in sftp.listdir(jupyter_runtime):
        if f.startswith('nbserver-') and f.endswith('.json'):
            yield parse(jupyter_runtime + f)


def nbserver_all_configs(sftp):
    cfgs = list(load_nbserver_configs(sftp))
    cfgs.sort(key=lambda c: c.get('mtime', 0), reverse=True)
    return cfgs


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
    from ._ssh import open_ssh, launch_tunnel

    ssh, ssh_cfg = open_ssh(ssh_host, user)

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
