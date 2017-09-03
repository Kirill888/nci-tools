# NCI tools

Collection of command line tools for interacting with [NCI](http://nci.org.au) compute nodes.

## nbconnect

Connect to a jupyter notebook server over ssh tunnel. Not NCI specific.

1. Connects to a remote server
2. Finds out what port notebook server is running on
3. Establishes ssh tunnel
4. Launches browser with appropriate token for authenticated access


## vdi

Lighter version of [Strudel](https://cvl.massive.org.au/launcher_files/stable/)
for connecting to vdi nodes, probably very much NCI specific. Still incomplete.

Currently supports:

- Launching/terminating sessions on VDI
- Finding out hostname of a current job
- Connecting to jupyter notebook on vdi

TODO:

- vnc tunnel setup

## Installing

Using pip

```
git clone https://github.com/Kirill888/nci-tools.git
cd nci-tools
pip install .
```

If using `conda` make sure to activate your environment of choice.

## SSH Authentication

It is recommended to use ssh key-based authentication in conjunction with
*ssh-agent* for managing encrypted keys. However if you don't have this set up,
you can still connect using password based authentication, just supply `--ask`
command line option, you will be asked to enter password (this works for both
password based authentication and for password protected ssh keys if you don't
use ssh agent).

On Windows [Putty Authentication Agent](https://winscp.net/eng/docs/ui_pageant)
is consulted for public keys.

You can supply user name on a command line, but it's probably best to put it
into your ssh configuration file `$HOME/.ssh/config` like so

```
Host raijin.nci.org.au
User your-nci-user-name

Host vdi.nci.org.au
User your-nci-user-name
```

## Launch notebook on PBS

There is an example launch script for a jupyter notebook in scripts
folder [scripts/nb_launcher_qsub.sh](scripts/nb_launcher_qsub.sh). You probably
want to tweak `#PBS -l mem=` parameter depending on what you are doing. Submit
the job with `qsub` on raijin wait for it to start, then connect from your PC
with `nbconnect raijin.nci.org.au`.


## Autostart notebook server on VDI

Let's configure vdi nodes to start jupyter notebook on startup. There is a
script in `scripts` folder [setup_auto_start.sh](scripts/setup_auto_start.sh).
After running the script above on VDI node you should be able to restart vdi job
and connect to a running notebook server.

```bash
vdi terminate
vdi launch
sleep 5
vdi nbconnect
```

Note that when connecting to notebook on VDI you should use `vdi nbconnect`
instead of just `nbconnect`, this is because there is an extra step of figuring
out what host your VDI job is running on that `vdi nbconnect` does for you.
