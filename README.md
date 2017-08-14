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

