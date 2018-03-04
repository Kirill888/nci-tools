import click
import sys
from collections import namedtuple

Ctx = namedtuple('Ctx', ['ctl', 'ssh', 'ssh_cfg'])


@click.group()
@click.pass_context
@click.option('--host', default='vdi.nci.org.au', help='Customize vdi login node')
@click.option('--user', help='SSH user name, if not given will be read from ~/.ssh/config')
@click.option('--no-ask', is_flag=True, help='Do not ask for passwords')
def cli(ctx, host, user, no_ask):
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
    ctl = ctx.ctl
    jobs = ctl('list-avail', '--partition', 'main', flatten=False)

    if len(jobs) != 0 and not force:
        click.echo('Job already running', err=True)
        return 1

    job = ctl('launch', '--partition', 'main')
    click.echo(job.get('id'))

    return 0


@cli.command('terminate')
@click.pass_obj
def terminate(ctx):
    ctl = ctx.ctl
    jobs = ctl('list-avail', '--partition', 'main', flatten=False)

    for job in jobs:
        jobid = job['id']
        click.echo('Terminating {}'.format(jobid))
        ctl('terminate', '--jobid', jobid)


@cli.command('host')
@click.pass_obj
def hostname(ctx):
    ctl = ctx.ctl

    jobs = ctl('list-avail', '--partition', 'main', flatten=False)

    if len(jobs) == 0:
        click.echo('No jobs running', err=True)
        return 1

    for job in jobs:
        host = ctl('get-host', '--jobid', job['id']).get('host')
        click.echo(host)

    return 0


@cli.command('nbconnect')
@click.option('--local-port', type=int, default=0, help='Local port to use for ssh forwarding')
@click.option('--runtime-dir', help='Jupyter runtime dir on a remote `jupyter --runtime-dir`')
@click.pass_obj
def nbconnect(ctx, local_port=0, runtime_dir=None):
    from ._ssh import mk_ssh
    from .nbconnect import run_nb_tunnel

    ctl = ctx.ctl
    ssh_cfg = ctx.ssh_cfg

    jobs = ctl('list-avail', '--partition', 'main', flatten=False)

    if len(jobs) == 0:
        click.echo('No jobs running', err=True)
        return 1

    for job in jobs:
        host = ctl('get-host', '--jobid', job['id']).get('host')
        ssh_cfg['hostname'] = host
        try:
            ssh = mk_ssh(ssh_cfg)
        except:
            click.echo('Failed to connect to {}'.format(host))
            sys.exit(1)

        sys.exit(run_nb_tunnel(ssh, ssh_cfg, runtime_dir=runtime_dir, local_port=local_port))


def _cli():
    cli(obj={})


if __name__ == '__main__':
    _cli()
