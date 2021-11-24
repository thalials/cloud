import boto3
from dotenv import dotenv_values
import sys
import time

config = dotenv_values()

# AWS CREDENTIALS 
AWS_ACCESS_KEY_ID = config["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = config["AWS_SECRET_ACCESS_KEY"]
AWS_REGION_NAME_NV = config["AWS_REGION_NAME_NV"] 
AWS_REGION_NAME_OHIO = config["AWS_REGION_NAME_OHIO"]  

# VARIABLES 
ORM = 'ORM'
POSTGRES = 'POSTGRES'
LoadBalancerName = 'LOADBALANCER'
LaunchConfigurationNames = 'LAUNCH_CONFIG'
AutoScalingGroupName = 'AUTOSCALLING_ORM'

imageId_nv = 'ami-0279c3b3186e54acd'
imageId_ohio = 'ami-020db2c14939a8efb'

default_ohio = 'default_ohio'
default_nv = 'default_nv'

# CONFIGURING AWS
ohio_s = boto3.session.Session(region_name=AWS_REGION_NAME_OHIO, 
                               aws_access_key_id=AWS_ACCESS_KEY_ID, 
                               aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
nv_s = boto3.session.Session(region_name=AWS_REGION_NAME_NV, 
                             aws_access_key_id=AWS_ACCESS_KEY_ID, 
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

ohio_resource = ohio_s.resource("ec2")
nv_resource = nv_s.resource("ec2")

ohio_client = ohio_s.client("ec2")
nv_client = nv_s.client("ec2")

def read_file(filename):
    file = open(filename, mode='r', encoding='utf-8')
    content = file.read()
    file.close()
    return content