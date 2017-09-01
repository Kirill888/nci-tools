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


@click.command(name='nbconnect')
@click.argument('ssh_host', default='raijin.nci.org.au')
@click.option('--user', help='SSH user name, if not given will be read from ~/.ssh/config')
@click.option('--local-port', type=int, default=0, help='Local port to use for ssh forwarding')
@click.option('--runtime-dir', help='Jupyter runtime dir on a remote `jupyter --runtime-dir`')
@click.option('--ask', is_flag=True, help='Ask for ssh password')
def main(ssh_host, user=None, local_port=0, runtime_dir=None, ask=False):
    from ._ssh import open_ssh, launch_tunnel
    import sys

    if runtime_dir is None:
        runtime_dir = '.local/share/jupyter/runtime/'

    ssh, sftp = (None, None)

    try:
        ssh, ssh_cfg = open_ssh(ssh_host, user, ask_password=ask)
        sftp = ssh.open_sftp()
        cfgs = nbserver_all_configs(sftp, runtime_dir)
    except:
        warn('Failed to connect to "{}{}"'.format(user+'@' if user else '', ssh_host))
        return 1
    finally:
        if sftp is not None:
            sftp.close()
        if ssh is not None:
            ssh.close()

    if len(cfgs) == 0:
        warn('# no configs')
        return 1

    nb_cfg = cfgs[0]

    if len(cfgs) > 1:
        warn('# **WARNING**: found more than one config')

    tunnel = launch_tunnel(ssh_cfg, nb_cfg, local_port)

    url = mk_url(nb_cfg, tunnel.local_bind_port)
    warn(url)
    click.launch(url)

    click.echo('''Tunnel is running, press
q - quit
o - open notebook url again
r - restart tunnel
''')

    def relaunch():
        url = mk_url(nb_cfg, tunnel.local_bind_port)
        warn(url)
        click.launch(url)

    while True:
        k = click.getchar()

        if type(k) is bytes:
            k = k.decode('utf-8')

        if k == 'q':
            click.echo('Quiting')
            tunnel.stop()
            sys.exit(0)
        elif k == 'o':
            relaunch()
        elif k == 'r':
            click.echo('Restarting tunnel')
            try:
                tunnel.restart()
                click.echo(' OK')
                relaunch()
            except:
                click.echo('Failed')
        else:
            pass

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
