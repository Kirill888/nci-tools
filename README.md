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

TODO:

- vnc tunnel setup
- notebook launching
- notebook tunnel setup

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
