import click
from collections import namedtuple

Ctx = namedtuple('Ctx', ['ctl', 'ssh', 'ssh_cfg'])


@click.group()
@click.pass_context
@click.option('--host', default='vdi.nci.org.au')
@click.option('--user', help='SSH user name, if not given will be read from ~/.ssh/config')
def cli(ctx, host, user):
    from ._ssh import open_ssh
    from .vdi import vdi_ctl

    ssh, ssh_cfg = open_ssh(host, user)

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


def _cli():
    cli(obj={})


if __name__ == '__main__':
    _cli()
