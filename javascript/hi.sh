#!/bin/sh

## DO NOT EDIT ANY LINE BELOW ##
## THIS IS THE STANDARD TEMPLATE FOR SUBMITTING A JOB IN DGX BOX ##
## The line above is used by computer to process it as
## bash script.

## This file serves as the template of the bash script which
## should be used to run the codes required for experiments 
## associated with the ISL Lab.


## The following are some necessary commands associated with 
## the SLURM.
#SBATCH --job-name=SELAB ## Job name
#SBATCH --ntasks=3 ## Run on a single CPU
##SBATCH --gres=gpu:a100_1g.15gb:1 ## example request for GPU
#SBATCH --time=05:00:00 ## Time limit hrs:min:sec
#SBATCH --partition=mediumq ## ( partition name )
#SBATCH --qos=mediumq ## ( QUEUE name )
#SBATCH --mem=50000M

## The output of the scuessfully executed code will be saved
## in the file mentioned below. %u -> user, %x -> jon-name, 
## %N -> the compute node (dgx1), %j-> job ID.
#SBATCH --output=/scratch/%u/%x-%N-%j.out ##Output file

## The errors associated will be saved in the file below
#SBATCH --error=/scratch/%u/%x-%N-%j.err ## Error file

## the following command ensures successful loading of modules
. /etc/profile.d/modules.sh
module load anaconda/2023.03-1

## DO NOT EDIT ANY LINE ABOVE ###

## Uncomment the following to import torch
eval "$(conda shell.bash hook)"
conda activate /home1/cs21b052/.conda/envs/temp
#conda activate pytorch_gpu 
## put all your required python code in demo.py
## call your python script here
## command to execute this script:

python3 /scratch/cs21b052/SEProject/python2/BugLearn.py --pattern IncorrectAssignment --token_emb /scratch/cs21b052/SEProject/token_to_vector*.json --type_emb /scratch/cs21b052/SEProject/type_to_vector.json --node_emb /scratch/cs21b052/SEProject/node_type_to_vector.json --training_data /scratch/cs21b052/SEProject/assignments_train/*.json

## sbatch job_submit.sh
conda deactivate
## note down the jobid for the submitted job
## check your job status using the below command
## sacct -u <username> 
## once your job status is shown as completed
## then cd to the directory /scratch/<username>/ 
## the file isl-dgx1-<jobid>.out -- contains the output of your program
## the file isl-dgx1-<jobid>.err -- contains the errors encountered
