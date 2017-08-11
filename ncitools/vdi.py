

def vdi_ctl(ssh, configver='20151620513'):

    cmd = ('/opt/vdi/bin/session-ctl',
           '--configver={}'.format(configver))

    def split_x(txt, delim):
        return [s for s in txt.split(delim) if len(s)]

    def parse_line(l):
        return dict(tuple(s.split('=')) for s in split_x(l, '#~#'))

    def session_ctl(*args, raw=False, flatten=True):
        cmdline = ' '.join(cmd + args)
        (_, stdout, stderr) = ssh.exec_command(cmdline)
        txt = stdout.read().decode('utf-8')

        if raw:
            return txt

        ll = [parse_line(l) for l in split_x(txt, '\n')]

        if not flatten:
            return ll

        if len(ll) == 0:
            return None
        elif len(ll) == 1:
            return ll[0]
        return ll

    return session_ctl
