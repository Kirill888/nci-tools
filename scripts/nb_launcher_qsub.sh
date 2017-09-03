#!/bin/bash

#PBS -N notebook
#PBS -l ncpus=1
#PBS -l mem=2G
#PBS -l walltime=8:00:00

#PBS -l wd
#PBS -o logs/stdout.txt
#PBS -e logs/stderr.txt

nb_dir="${HOME}/notebooks"

module use '/g/data/v10/public/modules/modulefiles'
module load agdc-py3-prod

#pick random port number
port=$(shuf -n 1 -i 8300-8400)

exec jupyter-notebook --no-browser --notebook-dir "${nb_dir}" --ip "${HOSTNAME}" --port "${port}"
