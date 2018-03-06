import click
import sys
from collections import namedtuple
from random import randint

Ctx = namedtuple('Ctx', ['ctl', 'ssh', 'ssh_cfg'])


@click.group()
@click.pass_context
@click.option('--host', default='vdi.nci.org.au', help='Customize vdi login node')
@click.option('--user', help='SSH user name, if not given will be read from ~/.ssh/config')
@click.option('--no-ask', is_flag=True, help='Do not ask for passwords')
def cli(ctx, host, user, no_ask):
    """ Control and query info about VDI sessions
    """
    from ._ssh import open_ssh
    from .vdi import vdi_ctl

    try:
        ssh, ssh_cfg = open_ssh(host, user, no_ask=no_ask)
    except:
        click.echo('Failed to connect to "{}{}"'.format(user+'@' if user else '', host))
        ctx.exit()

    ctl = vdi_ctl(ssh)

    ctx.obj = Ctx(ssh=ssh, ssh_cfg=ssh_cfg, ctl=ctl)


@cli.command('launch')
@click.pass_obj
@click.option('--force', is_flag=True, help='Launch new session even if one is already running')
def launch(ctx, force):
    """ Launch session if not running
    """
    ctl = ctx.ctl
    jobs = ctl('list-avail', '--partition', 'main', flatten=False)

    if len(jobs) != 0 and not force:
        click.echo('Job already running', err=True)
        sys.exit(1)

    job = ctl('launch', '--partition', 'main')
    click.echo(job.get('id'))

    return 0


@cli.command('terminate')
@click.pass_obj
def terminate(ctx):
    """ Shutdown session (all sessions actually)
    """
    ctl = ctx.ctl
    jobs = ctl('list-avail', '--partition', 'main', flatten=False)

    for job in jobs:
        jobid = job['id']
        click.echo('Terminating {}'.format(jobid))
        ctl('terminate', '--jobid', jobid)


@cli.command('host')
@click.pass_obj
def hostname(ctx):
    """ Print hostname for every active session
    """
    ctl = ctx.ctl

    jobs = ctl('list-avail', '--partition', 'main', flatten=False)

    if len(jobs) == 0:
        click.echo('No jobs running', err=True)
        sys.exit(1)

    for job in jobs:
        host = ctl('get-host', '--jobid', job['id']).get('host')
        click.echo(host)

    return 0


@cli.command('get-passwd')
@click.pass_obj
def get_passwd(ctx):
    """ Print VNC password
    """
    ctl = ctx.ctl

    password = ctl('get-passwd').get('passwd')

    if password is None:
        click.echo('Failed to query VNC password', err=True)
        sys.exit(1)

    click.echo(password)
    return 0


def collect_vnc_info(ctl, job_id, ssh_cfg):
    from ._ssh import mk_ssh
    from .vdi import vdi_ctl

    cfg = dict(**ssh_cfg)
    host = ctl('get-host', '--jobid', job_id).get('host')
    passwd = ctl('get-passwd').get('passwd')
    cfg['hostname'] = host

    try:
        client_ctl = vdi_ctl(mk_ssh(cfg))
    except:
        click.echo('Failed to connect to {}'.format(host), err=True)
        sys.exit(2)

    display = client_ctl('get-display-nbr').get('display')
    if display is None:
        click.echo('Failed to query display {}'.format(host), err=True)
        sys.exit(3)

    try:
        display = int(display[1:])  # Parse `:2`
    except ValueError:
        click.echo('Failed to parse display number: "{}"'.format(display))
        sys.exit(3)

    return dict(host=host,
                display=display,
                port=display+5900,
                passwd=passwd)


def get_vnc_tunnel_cmd(ctx, job_id, local_port):
    v_map = {True: 'yes', False: 'no'}

    opts = dict(
        PasswordAuthentication=False,
        ChallengeResponseAuthentication=False,
        KbdInteractiveAuthentication=False,
        PubkeyAuthentication=True,
        StrictHostKeyChecking=True,
    )

    args = ['-T'] + ['-o{}={}'.format(k, v_map.get(v, v))
                     for k, v in opts.items()]

    cmd = '/opt/vdi/bin/session-ctl --configver=20173552330 tunnel'.split(' ')

    user = ctx.ssh_cfg.get('user')

    if user is not None:
        args.extend(['-l', user])

    info = collect_vnc_info(ctx.ctl, job_id, ctx.ssh_cfg)
    fwd_args = ['-L',
                '{local_port}:127.0.0.1:{remote_port} {host}'.format(
                    local_port=local_port,
                    remote_port=info['port'],
                    host=info['host'])]

    return ['ssh'] + args + fwd_args + cmd


@cli.command('display-nbr')
@click.option('--as-port', is_flag=True, help='Print it as a port number of the VNC server')
@click.pass_obj
def display_nbr(ctx, as_port=False):
    """ Print display number for active session (s)
    """
    ctl = ctx.ctl

    jobs = ctl('list-avail', '--partition', 'main', flatten=False)

    if len(jobs) == 0:
        click.echo('No jobs running', err=True)
        sys.exit(1)

    for job in jobs:
        info = collect_vnc_info(ctl, job['id'], ctx.ssh_cfg)

        if as_port:
            click.echo('%d' % info['port'])
        else:
            click.echo(':%d' % info['display'])


@cli.command('vnc-tunnel-cmd')
@click.option('--local-port', type=int, default=0, help='Local port to use for ssh forwarding')
@click.pass_obj
def vnc_tunnel_cmd(ctx, local_port=0):
    """ Print port forwarding command
    """
    ctl = ctx.ctl

    jobs = ctl('list-avail', '--partition', 'main', flatten=False)

    if len(jobs) == 0:
        click.echo('No jobs running', err=True)
        sys.exit(1)

    local_port = local_port or randint(10000, 65000)

    for job in jobs:
        cmd = get_vnc_tunnel_cmd(ctx, job['id'], local_port)
        click.echo(' '.join(cmd))


@cli.command('nbconnect')
@click.option('--local-port', type=int, default=0, help='Local port to use for ssh forwarding')
@click.option('--runtime-dir', help='Jupyter runtime dir on a remote `jupyter --runtime-dir`')
@click.pass_obj
def nbconnect(ctx, local_port=0, runtime_dir=None):
    """ Connect to notebook on VDI
    """
    from ._ssh import mk_ssh
    from .nbconnect import run_nb_tunnel

    ctl = ctx.ctl
    ssh_cfg = ctx.ssh_cfg

    jobs = ctl('list-avail', '--partition', 'main', flatten=False)

    if len(jobs) == 0:
        click.echo('No jobs running', err=True)
        sys.exit(1)

    for job in jobs:
        host = ctl('get-host', '--jobid', job['id']).get('host')
        ssh_cfg['hostname'] = host
        try:
            ssh = mk_ssh(ssh_cfg)
        except:
            click.echo('Failed to connect to {}'.format(host))
            sys.exit(2)

        sys.exit(run_nb_tunnel(ssh, ssh_cfg, runtime_dir=runtime_dir, local_port=local_port))


def _cli():
    cli(obj={})


if __name__ == '__main__':
    _cli()
