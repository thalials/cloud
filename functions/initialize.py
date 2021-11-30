# import boto3
from functions.constants import *
from functions.destroy import *

def initialize(region, resource, client, session, name_instance):
    ec2 = boto3.client('ec2', region_name=region, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    try:
        # destroy instance
        destroy_instance(resource, client, name_instance)

        # destroy images
        images = ec2.describe_images(Owners=['self'])
        for image in images['Images']:
            ImageId = image["ImageId"]
            print(ImageId)

            response = client.deregister_image(ImageId=ImageId)
        
        # destroy load balancer
        destroy_load_balancer(session, region, LoadBalancerName)

        # destroy autoscalling
        destroy_autoscalling(session, region, AutoScalingGroupName)

        # destroy target group 
        load_balancer_client = boto3.client('elbv2', region_name=AWS_REGION_NAME_NV)
        destroy_target_groups(LB_TARGET_GROUP_NAME, load_balancer_client)

        # destroy launch config
        destroy_launch_configuration(session, region, LaunchConfigurationNames)

        print("---- {} sucess in initialization! ----\n".format(name_instance))


    except Exception as e:
        print('Failed to initialize ', e)
