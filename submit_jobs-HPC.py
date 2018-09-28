#! /usr/bin/python

"""
    Sumbit GROMACS 5.0.4 jobs to the new HPC
        -- Rewritten by Aingty Eung (7/18/2018)
"""
import os
import sys
import commands

# Fucntion to run a linux command
def run(command, display_output=False):
    status, output = commands.getstatusoutput(command)
    if display_output:
        print "----------------------------------------------------------------------"
        print "$" + command
        print output
        print "----------------------------------------------------------------------"

input = """ 
Usage:  submit_jobs-HPC.py  [options]

    -deffnm     or -d  name used for gro and top (required)
    -name       or -n  name of the job used by the PBS queue system (required)
    -sims       or -s  number of simulations to perform (default: 1)
    -cores      or -c  number of cores used for each simulation (default: 1, maximum: ??)
    -help       or -h  show this help message and exit
"""

# default parameters
deffnm = ""
job_name = ""
gromacs = ""
num_sims = 1
num_cores = 1

# get flags 
options = sys.argv
for i in range(len(options)):
    flag = options[i].lower()
    if flag == "-deffnm" or flag == "-d":
        deffnm = options[i+1]
    if flag == "-name" or flag == "-n":
        job_name = options[i+1]
    if flag == "-sims" or flag == "-s":
        if options[i+1].isdigit() == False:
            print "Invalid simulations number!!! ", options[i+1] ," is not a NUMBER!!"
            sys.exit()
        num_sims = int(options[i+1])
    if flag == "-cores" or flag == "-c":
        if options[i+1].isdigit() == False:
            print "Invalid cores number!!! ", options[i+1] ," is not a NUMBER!!!"
            sys.exit()
        num_cores = int(options[i+1])
    if flag == "-help" or flag == "-h":
        print input
        sys.exit()

# Check for valid input
if  deffnm == "" or num_cores > 8 or job_name == "":
	print "\n***** ERROR.  INVALID PARAMETERS. *****"
	print input
	sys.exit()

# Check that .top, .gro, and .mdp files exist
missing_file_error = False
if not os.path.exists('%s.gro' % (deffnm)):
	print "\n***** ERROR: '%s.gro' file not found. *****" % (deffnm)
	missing_file_error = True
if not os.path.exists('%s.top'% (deffnm)):
	print "\n***** ERROR: '%s.top' file not found. *****" % (deffnm)
	missing_file_error = True
if not os.path.exists('pr.mdp'):
	print "\n***** ERROR: 'pr.mdp' file not found. *****" % (deffnm)
	missing_file_error = True	
if missing_file_error:
	sys.exit()

# Crash if a working directory already exist
num_folder = 1
folder_exists_error = False
while num_folder <= num_sims:
	folder = str(num_folder)
	while len(folder) < 3:
		folder = "0" + folder
	if os.path.exists(folder):
		print "\n***** ERROR: working directory '%s' already exists. *****" % (folder)
		print "***** Please move or delete it (if not needed).      *****"
		folder_exists_error = True
	num_folder += 1
if folder_exists_error:
	sys.exit()

# make a folder for each simulation
num_folder = 1
job_folders = []
while num_folder <= num_sims:
	folder = str(num_folder)
	while len(folder) < 3:
		folder = "0" + folder
	run("mkdir %s" % (folder))
	#run("cp * %s" %(folder))
	run("cp %s.top %s" % (deffnm, folder))
	run("cp %s.gro %s" % (deffnm, folder))
	run("cp pr.mdp %s" % (folder))	
	job_folders.append(folder)
	num_folder += 1

# create and run a job script in each of the folders
script = """#!/bin/bash

### Specify the name of the job to run (the line below is not a comment even though it looks like one)
#MSUB -N %s -l walltime=99:00:00:00

### Use the current folder as the working directory
PBS_PWD="`pwd`";
cd "${PBS_O_WORKDIR}";

### Sourcing GROMACS 5.0.4 so grompp & mdrun could be used
source /research/CNSM-SorinLab/Admin/GRO/gromacs-5.0.4/bin/GMXRC;

grompp_mpi -f pr.mdp -c %s -p %s -o %s-run;
mpirun -np %s mdrun_mpi -deffnm %s-run;
""" % (job_name, deffnm, deffnm, deffnm, num_cores, deffnm)

current_folder = os.getcwd()

for folder in job_folders:
	file_name = open("%s/%s/run_sim.sh" % (current_folder,folder), "w")
	file_name.write(script)
	file_name.close()
	os.chdir(current_folder + "/" + folder)
	run("msub -j oe -l procs=%s run_sim.sh" % (num_cores),True)
	
