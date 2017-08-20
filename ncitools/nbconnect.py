import click


def warn(*args, **kwargs):
    from sys import stderr
    print(*args, file=stderr, **kwargs)


def load_nbserver_configs(sftp, jupyter_runtime='.local/share/jupyter/runtime/'):
    import json

    if not jupyter_runtime.endswith('/'):
        jupyter_runtime += '/'

    def parse(fname):
        try:
            with sftp.open(fname) as f:
                cfg = json.loads(f.read().decode('utf-8'))
                cfg['mtime'] = f.stat().st_mtime
                return cfg
        except IOError:
            return None

    try:
        runtime_files = sftp.listdir(jupyter_runtime)
    except IOError:
        warn('No such folder: ' + jupyter_runtime)
        runtime_files = []

    for f in runtime_files:
        if f.startswith('nbserver-') and f.endswith('.json'):
            doc = parse(jupyter_runtime + f)
            if doc is None:
                warn('Failed to read ' + f)
            else:
                yield doc


def nbserver_all_configs(sftp, jupyter_runtime):
    cfgs = list(load_nbserver_configs(sftp, jupyter_runtime))
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
@click.option('--local-port', type=int, default=0, help='Local port to use for ssh forwarding')
@click.option('--runtime-dir', help='Jupyter runtime dir on a remote `jupyter --runtime-dir`')
def main(ssh_host, user=None, local_port=0, runtime_dir=None):
    from ._ssh import open_ssh, launch_tunnel

    ssh, ssh_cfg = open_ssh(ssh_host, user)

    if runtime_dir is None:
        runtime_dir = '.local/share/jupyter/runtime/'

    cfgs = nbserver_all_configs(ssh.open_sftp(), runtime_dir)

    if len(cfgs) == 0:
        warn('# no configs')
        return 1

    nb_cfg = cfgs[0]

    if len(cfgs) > 1:
        warn('# **WARNING**: found more than one config')

    tunnel = launch_tunnel(ssh_cfg, nb_cfg, local_port)

    url = mk_url(nb_cfg, tunnel.local_bind_port)
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
