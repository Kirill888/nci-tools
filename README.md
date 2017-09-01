# NCI tools

Collection of command line tools for interacting with NCI compute nodes (http://nci.org.au)

## nbconnect

Connect to a jupyter notebook server over ssh tunnel. Not NCI specific.

1. Connects to a remote server
2. Finds out what port notebook server is running on
3. Establishes ssh tunnel
4. Launches browser with appropriate token for authenticated access


## vdi

Lighter version of Strudel (https://cvl.massive.org.au/launcher_files/stable/)
for connecting to vdi nodes, probably very much NCI specific. Still incomplete.

Currently supports:

- Launching/terminating sessions on VDI
- Finding out hostname of a current job
- Connecting to jupyter notebook on vdi

TODO:

- vnc tunnel setup
- notebook launching

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
password based authentication and for encrypted ssh keys if you don't use ssh
agent).

On windows [Putty Authentication Agent](https://winscp.net/eng/docs/ui_pageant)
is consulted for public keys.

You can supply user name on a command line, but it's probably best to put into
your ssh configuration file `$HOME/.ssh/config` like so

```
Host raijin.nci.org.au
User your-nci-user-name

Host vdi.nci.org.au
User your-nci-user-name
```

## Launch notebook

Example launch script for a jupyter notebook.

```bash
#!/bin/bash

#PBS -N notebook
#PBS -l ncpus=1
#PBS -l mem=2G
#PBS -l walltime=8:00:00 

#PBS -l wd
#PBS -o logs/stdout.txt
#PBS -e logs/stderr.txt

module use '/g/data/v10/public/modules/modulefiles'
module load agdc-py3-prod

#pick random port number
port=$(shuf -n 1 -i 8300-8400)

exec jupyter-notebook --no-browser --ip "${HOSTNAME}" --port "${port}"
```

Probably want to tweak `#PBS -l mem=` parameter depending on what you doing.
