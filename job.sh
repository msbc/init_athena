#! /bin/bash
#SBATCH --job-name="{name:}"
#SBATCH --export=ALL
#SBATCH --mail-user=mcoleman@ias.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes={node_num:d}
#SBATCH --ntasks-per-node={node_size:d}
#SBATCH -t {walltime:}

RST=$(ls -rt *.rst ls 2> /dev/null | tail -n 1)
if [ -z "$RST" ]; then
  RST="NONE"
fi

if [ -f $RST ]; then
  echo "Restart:" $RST
  srun -n  {core_num:d} athena -r $RST -t {stop_time:}
else
  srun -n  {core_num:d} athena -i athinput.bl -t {stop_time:}
fi
