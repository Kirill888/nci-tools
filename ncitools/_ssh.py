import paramiko
from pathlib import Path
import click

__all__ = ['open_ssh', 'launch_tunnel']


def get_ssh_config(name):
    cfg = paramiko.SSHConfig()

    try:
        with open(str(Path.home()/".ssh"/"config"), 'rt') as f:
            cfg.parse(f)
            return cfg.lookup(name)
    except FileNotFoundError:
        return {'hostname': name}


def load_key(filename, password=None):
    for ktype in (paramiko.DSSKey, paramiko.ECDSAKey, paramiko.Ed25519Key, paramiko.RSAKey):
        try:
            return ktype.from_private_key_file(filename, password)
        except paramiko.ssh_exception.PasswordRequiredException as e:
            raise e
        except paramiko.ssh_exception.SSHException as e:
            pass

    return None


def is_key_encrypted(filename):
    for ktype in (paramiko.RSAKey, paramiko.DSSKey, paramiko.ECDSAKey, paramiko.Ed25519Key,):
        try:
            if ktype.from_private_key_file(filename) is not None:
                return False
        except paramiko.ssh_exception.PasswordRequiredException as e:
            return True
        except paramiko.ssh_exception.SSHException as e:
            pass

    return False


def get_keyfile(cfg):
    ids = cfg.get('identityfile')
    if ids is None:
        return None
    elif len(ids) == 1:
        return ids[0]
    elif len(ids) > 1:
        # TODO: log warning?
        return ids[0]


def mk_ssh(cfg, ask_pass=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    params = {}

    def add_params(**kwargs):
        nonlocal params
        for k, v in kwargs.items():
            if v is not None:
                params[k] = v

    key_filename = get_keyfile(cfg)
    add_params(username=cfg.get('user'))
    add_params(port=cfg.get('port'))
    add_params(password=cfg.get('password'))
    add_params(passphrase=cfg.get('passphrase'))
    add_params(key_filename=key_filename)

    last_exception = None

    def try_connect():
        nonlocal last_exception

        try:
            ssh.connect(cfg['hostname'], **params)
        except (paramiko.ssh_exception.PasswordRequiredException,
                paramiko.ssh_exception.AuthenticationException) as e:
            last_exception = e
            return False
        return True

    if try_connect():
        return ssh

    if ask_pass is None:
        raise last_exception

    if key_filename is None:
        # fall to password auth
        for i in range(3):
            params['password'] = ask_pass('Password for %s: ' % cfg['hostname'])
            if try_connect():
                cfg['password'] = params['password']
                return ssh

    elif is_key_encrypted(key_filename):
        # Get password for encrypted key file
        for i in range(3):
            passphrase = ask_pass('Unlock key %s: ' % key_filename)
            pkey = load_key(key_filename, passphrase)
            if pkey:
                params.pop('key_filename')
                add_params(pkey=pkey)

                if try_connect():
                    cfg['pkey'] = pkey
                    cfg['passphrase'] = passphrase

                    return ssh
        raise paramiko.ssh_exception.PasswordRequiredException('Failed to decrypt key')

    if last_exception is not None:
        raise last_exception

    return ssh


def open_ssh(host, user=None, no_ask=True):
    cfg = get_ssh_config(host)

    if user is not None:
        cfg['user'] = user

    def ask_password(msg):
        return click.prompt(msg,
                            hide_input=True,
                            prompt_suffix='',
                            show_default=False)

    ssh = mk_ssh(cfg, None if no_ask else ask_password)

    return ssh, cfg


def launch_tunnel(ssh_cfg, nb_cfg, lport=0):
    from sshtunnel import SSHTunnelForwarder

    ssh_user = ssh_cfg.get('user')
    ssh_server = ssh_cfg.get('hostname')
    ssh_port = ssh_cfg.get('port')
    ssh_password = ssh_cfg.get('password')
    ssh_pkey = ssh_cfg.get('pkey')

    if ssh_pkey is None:
        ssh_pkey = get_keyfile(ssh_cfg)

    tunnel = SSHTunnelForwarder(ssh_server,
                                ssh_username=ssh_user,
                                ssh_password=ssh_password,
                                ssh_port=ssh_port,
                                ssh_pkey=ssh_pkey,
                                local_bind_address=('localhost', lport),
                                remote_bind_address=(nb_cfg.get('hostname'),
                                                     nb_cfg.get('port')))
    tunnel.start()
    return tunnel
