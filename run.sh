#! /bin/bash
#PBS -q {queue:}
#PBS -l walltime={walltime:}
#PBS -lselect={node_num:d}:ncpus={node_size:d}:mpiprocs={node_size:d}:model={node_type:}
#PBS -N {name:}
#PBS -m abe
#PBS -M mcoleman@ias.edu

# tells the scheduler to put all output files into the directory where
# we spawned from
cd $PBS_O_WORKDIR

module load comp-intel/2018.0.128
module load mpi-sgi/mpt
module load hdf5/1.8.18_mpt


RST=$(ls -rt *.rst ls 2> /dev/null | tail -n 1)
if [ -z "$RST" ]; then
  RST="NONE"
fi

if [ -f $RST ]; then
  echo "Restart:" $RST
  mpiexec -np {core_num:d} ./athena -r $RST -t {stop_time:} > output
else
  mpiexec -np {core_num:d} ./athena -i athinput.bl -t {stop_time:} > output
fi
