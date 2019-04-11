#! /bin/bash
#$ -V
#$ -cwd
#$ -N {name:}
#$ -l h_rt={walltime:}
#$ -m abe
#$ -M mcoleman@ias.edu
#$ -pe orte {core_num:d}

# tells the scheduler to put all output files into the directory where
# we spawned from

module load hdf5/gcc-4.4.7/openmpi-1.10.7/1.10.1
module load fftw/gcc-4.4.7/openmpi-1.10.7/3.3.7
module load openmpi/1.10.7_gcc-4.4.7

RST=$(ls -rt *.rst ls 2> /dev/null | tail -n 1)
if [ -z "$RST" ]; then
  RST="NONE"
fi

if [ -f $RST ]; then
  echo "Restart:" $RST
  mpirun -np {core_num:} ./athena -r $RST -t {stop_time:}
else
  mpirun -np {core_num:} ./athena -i athinput.bl -t {stop_time:}
fi

