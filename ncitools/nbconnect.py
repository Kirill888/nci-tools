import sys
import click


def warn(*args, **kwargs):
    from sys import stderr
    print(*args, file=stderr, **kwargs)


def check_connection(url, direct=False):
    from urllib.request import build_opener, ProxyHandler

    # Force direct connection ignoring proxy settings if requested
    oo = build_opener(ProxyHandler({})) if direct else build_opener()

    try:
        with oo.open(url) as f:
            return len(f.read()) > 0
    except IOError:
        return False


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
                doc['_file'] = jupyter_runtime + f
                yield doc


def nbserver_all_configs(sftp, jupyter_runtime):
    cfgs = list(load_nbserver_configs(sftp, jupyter_runtime))
    cfgs.sort(key=lambda c: c.get('mtime', 0), reverse=True)
    return cfgs


def mk_url(nb_cfg, lport):
    return 'http://localhost:{lport}{base_url}?token={token}'.format(lport=lport, **nb_cfg)


def run_nb_tunnel(ssh, ssh_cfg, local_port=0, runtime_dir=None, auto_clean=False):
    from ._ssh import launch_tunnel

    sftp = None
    cfgs = []

    def cleanup_ssh():
        if sftp is not None:
            sftp.close()
        ssh.close()

    if runtime_dir is None:
        runtime_dir = '.local/share/jupyter/runtime/'

    try:
        sftp = ssh.open_sftp()
        cfgs = nbserver_all_configs(sftp, runtime_dir)
    except:
        cleanup_ssh()
        return 1

    if len(cfgs) == 0:
        warn('No active notebooks were found!')
        return 2

    tunnel = None
    for nb_cfg in cfgs:
        tunnel = launch_tunnel(ssh_cfg, nb_cfg, local_port)
        url = mk_url(nb_cfg, tunnel.local_bind_port)
        if check_connection(url, direct=True):
            break

        nb_file_path = nb_cfg.get('_file')
        warn('Notebook {} is probably no more'.format(nb_cfg.get('url')))
        tunnel.stop()
        tunnel = None

        if auto_clean or click.confirm('Cleanup remote config file: {}'.format(nb_file_path), default=True):
            try:
                sftp.remove(nb_file_path)
            except IOError as e:
                if not auto_clean:
                    warn('Failed: ' + repr(e))

    cleanup_ssh()  # close sftp

    if tunnel is None:
        warn('No active notebooks were found!')
        return 3

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
            click.echo('Quitting')
            break
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

    tunnel.stop()
    return 0


@click.command(name='nbconnect')
@click.argument('ssh_host', default='raijin.nci.org.au')
@click.option('--user', help='SSH user name, if not given will be read from ~/.ssh/config')
@click.option('--local-port', type=int, default=0, help='Local port to use for ssh forwarding')
@click.option('--runtime-dir', help='Jupyter runtime dir on a remote `jupyter --runtime-dir`')
@click.option('--no-ask', is_flag=True, help='Do not ask for passwords')
def main(ssh_host, user=None, local_port=0, runtime_dir=None, no_ask=False):
    from ._ssh import open_ssh

    try:
        ssh, ssh_cfg = open_ssh(ssh_host, user, no_ask=no_ask)
    except:
        warn('Failed to connect to "{}{}"'.format(user+'@' if user else '', ssh_host))
        sys.exit(1)

    sys.exit(run_nb_tunnel(ssh, ssh_cfg, runtime_dir=runtime_dir, local_port=local_port))


if __name__ == '__main__':
    sys.exit(main())
