#! /usr/bin/python

# Sumbit GROMACS 5.0.4 jobs to the new HPC
# 	-- Rewritten by Aingty Eung (7/18/2018)
    
import os
import sys
import commands
import re

# Function to run a linux command
def run(command, display_output=False):
    status, output = commands.getstatusoutput(command)
    if display_output:
        print("----------------------------------------------------------------------")
        print("$" + command)
        print(output)
        print("----------------------------------------------------------------------")

# Function used to get qstat status of HPC
def getProcessor():
    status, output = commands.getstatusoutput("qstat -f |grep exec_host")
    return output

# Grabbing Available Cores Information and Setting Constraint on Cores Usage Section
listArray = getProcessor()
listArray = listArray.replace("+","\n")
listArray = listArray.split("\n")

# Declare to cores available for all Sorinlab Nodes
coresAvailable = {
	"n017":48,
	"n018":48
}
for i in listArray:
	# Add more "if" statements if we get a new node 
	if "n017" in i:
		tempSplit = i.split("/")
		if "-" in tempSplit[1]:
			tempSplit = tempSplit[1].split("-")
			tempSplit = [int(j) for j in tempSplit]
			coresAvailable["n017"] = coresAvailable["n017"] - (tempSplit[1] - tempSplit[0] + 1)
		else:
			coresAvailable["n017"] = coresAvailable["n017"] - 1
	if "n018" in i:
		tempSplit = i.split("/")
		if "-" in tempSplit[1]:
			tempSplit = tempSplit[1].split("-")
			tempSplit = [int(j) for j in tempSplit]
			coresAvailable["n018"] = coresAvailable["n018"] - (tempSplit[1] - tempSplit[0] + 1)
		else:
			coresAvailable["n018"] = coresAvailable["n018"] - 1
maximumCore = 0
for key in coresAvailable:
	maximumCore = maximumCore + coresAvailable[key] 
input = """ 
Usage:  submit_jobs-HPC.py  [options]

    -deffnm     or -d  name used for mdp, gro, top, and ndx (required)
    -name       or -n  name of the job used by the PBS queue system (required)
    -sim        or -s  number of simulations to perform (default: 1, maximum: *must not exceed cores)
			* IE: 2 simulations with 5 cores means 2 simulations with 5 cores each, totaling 10 cores
    -core       or -c  number of cores used for each simulation (default: 1, maximum: %s)
			* Maximum core(s) calculated to 1 simulation
    -nondx      or -x  exclude ndx file
    -help       or -h  show this help message and exit
	
Current Cores Usage:
	Node 17: %s core(s) available
	Node 18: %s core(s) available
""" % (maximumCore,coresAvailable["n017"],coresAvailable["n018"])
# End of Constraint Section

# default parameters
deffnm = ""
job_name = ""
gromacs = ""
num_sims = 1
num_cores = 1
take_ndx = True

# get flags 
options = sys.argv
for i in range(len(options)):
	flag = options[i].lower()
	if flag == "-deffnm" or flag == "-d":
		deffnm = options[i+1]
	if flag == "-name" or flag == "-n":
		job_name = options[i+1]
	if flag == "-sim" or flag == "-s":
		if options[i+1].isdigit() == False:
			print("Invalid simulations number!!! ", options[i+1] ," is not a NUMBER!!")
			sys.exit()
		num_sims = int(options[i+1])
	if flag == "-core" or flag == "-c":
		if options[i+1].isdigit() == False:
			print("Invalid cores number!!! ", options[i+1] ," is not a NUMBER!!!")
			sys.exit()
		num_cores = int(options[i+1])
	if flag == "-nondx" or flag == "-x":
		take_ndx = False
	if flag == "-help" or flag == "-h":
		print(input)
		sys.exit()

# Check for valid input
if  deffnm == "" or num_cores > maximumCore or job_name == "" or num_sims * num_cores > maximumCore or num_cores <= 0 or num_sims <= 0:
	print("\n***** ERROR.  INVALID PARAMETERS. *****")
	if deffnm == "":
		print("\nName of mdp, gro, top, and ndx is missing!!")
	if num_cores <= 0:
		print("\nYou've have selected an invalid number of core(s)")
	if num_cores > maximumCore:
		if maximumCore == 0:
			print("\nNo more cores available!!!")
		else:
			print("\nNumber of cores exceed maximum cores!!")
	if job_name == "":
		print("\nPBS queue name is missing!!")
	if num_sims <= 0:
		print("\nYou've have selected an invalid number of simulation(s)")
	if num_sims * num_cores > maximumCore:
		print("\nNumber of simulations times number of cores exceed maximum cores!!")
	print(input)
	sys.exit()

# Check that .top, .gro, and .mdp files exist
missing_file_error = False
if not os.path.exists('%s.gro' % (deffnm)):
	print("\n***** ERROR: '%s.gro' file not found. *****" % (deffnm))
	missing_file_error = True
if not os.path.exists('%s.top' % (deffnm)):
	print("\n***** ERROR: '%s.top' file not found. *****" % (deffnm))
	missing_file_error = True
if not os.path.exists('%s.mdp' % (deffnm)):
	print("\n***** ERROR: '%s.mdp' file not found. *****" % (deffnm))
	missing_file_error = True
if take_ndx == True and not os.path.exists('%s.ndx' % (deffnm)):
	print("\n***** ERROR: '%s.ndx' file not found. *****" % (deffnm))
	missing_file_error = True
if missing_file_error:
	sys.exit()

# Check if a working directory already exist then prompt user for deletion
num_folder = 1
while num_folder <= num_sims:
	folder = str(num_folder)
	while len(folder) < 3:
		folder = "0" + folder
	if os.path.exists(folder):
		print("\n***** ERROR: simulation directory already exists. *****")
		answer = raw_input("Would you like me to delete all existing folders for you? (Y/y for yes)\n\tAnswer: ")
		if(answer == "y" or answer == "Y"):
			print("\nOkay removing all existing folders (Running: rm -rf 0*)")
			run("rm -rf 0*")
		else:
			print("\nPlease deal with the existing folders before running this script again.")
			sys.exit()
	num_folder += 1

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
	if take_ndx == True:
		run("cp %s.ndx %s" % (deffnm, folder))	
	job_folders.append(folder)
	num_folder += 1

# create and run a job script in each of the folders based on ndx
script = ''
if take_ndx == True:	
	script = """#!/bin/bash

	### Specify the name of the job to run (the line below is not a comment even though it looks like one)
	#MSUB -N %s -l walltime=99:00:00:00

	### Use the current folder as the working directory
	PBS_PWD="`pwd`";
	cd "${PBS_O_WORKDIR}";

	### Sourcing GROMACS 5.0.4 so grompp & mdrun could be used
	source /research/CNSM-SorinLab/Admin/GRO/gromacs-5.0.4/bin/GMXRC;

	grompp_mpi -f %s -c %s -p %s -o %s-run -n %s;
	mdrun_mpi -ntomp 32 -ntmpi 1 -deffnm %s-run;
	""" % (job_name, deffnm, deffnm, deffnm, deffnm, deffnm, deffnm)
else:
	script = """#!/bin/bash

	### Specify the name of the job to run (the line below is not a comment even though it looks like one)
	#MSUB -N %s -l walltime=99:00:00:00

	### Use the current folder as the working directory
	PBS_PWD="`pwd`";
	cd "${PBS_O_WORKDIR}";

	### Sourcing GROMACS 5.0.4 so grompp & mdrun could be used
	source /research/CNSM-SorinLab/Admin/GRO/gromacs-5.0.4/bin/GMXRC;

	grompp_mpi -f %s.mdp -c %s -p %s -o %s-run;
	mdrun_mpi -ntomp 32 -ntmpi 1 -deffnm %s-run;
	""" % (job_name, deffnm, deffnm, deffnm, deffnm, deffnm)

current_folder = os.getcwd()

for folder in job_folders:
	file_name = open("%s/%s/run_sim.sh" % (current_folder,folder), "w")
	file_name.write(script)
	file_name.close()
	os.chdir(current_folder + "/" + folder)
	run("msub -l procs=%s run_sim.sh" % (num_cores),True)
	
