#! /usr/bin/python

""" 
    sumbit job several times to the PBS queue
"""
import os
import sys
import commands

def run(command, display_output=False):
    """ function to run a linux command """
    status, output = commands.getstatusoutput(command)
    if display_output:
        print "----------------------------------------------------------------------"
        print "$" + command
        print output
        print "----------------------------------------------------------------------"
        

input = """ 
Usage:  submit_jobs.py  [options]

    -deffnm     or -d  name used for gro, top, mdp, and output files (required)
    -name       or -n  name of the job used by the PBS queue system (required)
    -gromacs    or -g  314 or 33 (required)
    -sims       or -s  number of simulations to perform (default: 1)
    -cores      or -c  number of cores used for each simulation (default: 1, maximum: 8)
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
i = 0
while i < len(options): 
    flag = options[i].lower()
    if flag == "-deffnm" or flag == "-d":  deffnm = options[i+1]
    if flag == "-name" or flag == "-n":    job_name = options[i+1]
    if flag == "-gromacs" or flag == "-g": gromacs = options[i+1]
    if flag == "-sims" or flag == "-s":    num_sims = int(options[i+1])
    if flag == "-cores" or flag == "-c":   num_cores = int(options[i+1])
    if flag == "-help" or flag == "-h":
    	print input
    	sys.exit()
    i += 1

# Check for valid input
if  deffnm == "" or num_cores > 8 or job_name == "" or (gromacs != "314" and gromacs != "33"):
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
if not os.path.exists('%s.mdp'% (deffnm)):
	print "\n***** ERROR: '%s.mdp' file not found. *****" % (deffnm)
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
	run("cp %s.top %s" % (deffnm, folder))
	run("cp %s.gro %s" % (deffnm, folder))
	run("cp %s.mdp %s" % (deffnm, folder))	
	job_folders.append(folder)
	num_folder += 1

# create and run a job script in each of the folders
script = """#!/bin/bash

### Specify the name of the job to run (the line below is not a comment even though it looks like one)
#PBS -N %s

### Use the current folder as the working directory
PBS_PWD="`pwd`";
cd "${PBS_O_WORKDIR}";

### Use the the mpi version of gromacs-3.1.4
source ~/GRO/gromacs-3.1.4_mpi/x86_64-unknown-linux-gnu/bin/GMXRC;

grompp_mpi -np %s -f %s -c %s -p %s -o %s;
mpirun -np %s mdrun_mpi -np %s -deffnm %s;
""" % (job_name, num_cores, deffnm, deffnm, deffnm, deffnm, num_cores, num_cores, deffnm)

if gromacs == "33":
    script = script.replace('source ~/GRO/gromacs-3.1.4_mpi/x86_64-unknown-linux-gnu/bin/GMXRC;',
                            'source ~/GRO/gromacs-3.3_mpi/bin/GMXRC;')
    script = script.replace('gromacs-3.1.4', 'gromacs-3.3')


current_folder = os.getcwd()

for folder in job_folders:
	file_name = open("%s/%s/run_sim.sh" % (current_folder,folder), "w")
	file_name.write(script)
	file_name.close()
	os.chdir(current_folder + "/" + folder)
	run("qsub -l nodes=1:ppn=%s run_sim.sh" % (num_cores),True)
	





	

		
		
