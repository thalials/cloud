from functions.constants import *

def create_instance(resource, imageId, SecurityGroups, userData, name_instance): 
    try:
        # lauching new instances
        instance = resource.create_instances(ImageId=imageId,
                            MinCount=1,
                            MaxCount=1,
                            InstanceType='t2.micro',
                            KeyName='ssh',
                            SecurityGroups=[SecurityGroups],
                            UserData=userData,
                            TagSpecifications=[
                                {
                                    'ResourceType': 'instance',
                                    'Tags': [
                                        {
                                            'Key': 'Name',
                                            'Value': name_instance
                                        },
                                    ]
                                }]
                    )
        print('Instance {} created'.format(name_instance))
        return instance 
    except Exception as e:
        print('Error', e)
        print("Não deu certo criar a {}".format(name_instance))
   
def create_ami(client, instance, name):
    waiter = client.get_waiter('image_available')
    image = client.create_image(InstanceId=instance[0].id,
                                NoReboot=True,
                                Name=name)

    waiter.wait(ImageIds=[image["ImageId"]])
    print("SUCESSO: AMI criada!")
    return image['ImageId']

def config_security_group(ec2, groupName):
    response = ec2.describe_security_groups()
    for group in response['SecurityGroups']:
        # delete if already exists
        if group['GroupName'] == groupName:
            ec2.delete_security_group(GroupName=groupName)
        
    res = ec2.describe_vpcs()
    VpcId = res.get('Vpcs', [{}])[0].get('VpcId', '')

    try:
        res = ec2.create_security_group(GroupName=groupName,
                                            Description='description',
                                            VpcId=VpcId)
        security_group_id = res['GroupId']
        print('Security Group Created {0} in vpc {1}.'.format(security_group_id, VpcId))
        
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[{'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                        {'IpProtocol': 'tcp',
                        'FromPort': 5432,
                        'ToPort': 5432,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                        {'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                        {'IpProtocol': 'tcp',
                        'FromPort': 8080,
                        'ToPort': 8080,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]
        )

        return security_group_id

    except Exception as e:
        print('Error', e)

def create_security_group(ec2, name_security_group):          
    security = config_security_group(ec2, name_security_group)
    return security

def instances():
    # create instance in ohio 
    userData = read_file("setup.sh")
    ohio = create_instance(ohio_resource, imageId_ohio, default_ohio, userData, POSTGRES)
    
    ohio[0].wait_until_running()
    print("Instancia em ohio criada!")

    # pega o ip publico de ohio 
    instances = ohio_client.describe_instances(Filters=[{'Name':'instance-state-name', 'Values':['running']}])
    ip_public_ohio = instances['Reservations'][0]['Instances'][0]['PublicIpAddress']
    print("ip: ", ip_public_ohio)

    # create instance in north virginia
    orm = read_file("setup_orm.sh").format(ip_public_ohio)

    nv = create_instance(nv_resource, imageId_nv, default_nv, orm, ORM)

    nv[0].wait_until_running()
    print("Instancia em North Virginia criada!")

    return ohio, nv

def create_load_balancer(session, region, LoadBalancerName, SecurityGroups):
    client = session.client('elb', region_name=region)

    try: 
        response = client.create_load_balancer(
                    LoadBalancerName=LoadBalancerName,
                    Listeners=[
                        {
                            'Protocol': 'http',
                            'LoadBalancerPort': 80,
                            'InstancePort': 8080,
                        },
                    ],
                    AvailabilityZones=['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d'],
                    SecurityGroups=[SecurityGroups],
                    Tags=[
                        {
                            'Key': 'Name',
                            'Value': LoadBalancerName
                        },
                    ])
        print("loadbalancer created!")
        DNSName = response['DNSName']
        return DNSName

    except Exception as e:
        print('Fail to create loadbalancer ', e)

def create_launch_configuration(session, region, name, SecurityGroups, AMI):
    client = session.client('autoscaling', region_name=region)
    try:
        client.create_launch_configuration(
            LaunchConfigurationName=name,
            ImageId=AMI,
            KeyName='ssh',
            SecurityGroups=[SecurityGroups],
            InstanceType='t2.micro'
        )
        print("SUCESS: launch configuration created!")
    except Exception as e:
        print('Fail to create launch configuration ', e)

def create_auto_scalling(session, region, AutoScalingGroupName, LaunchConfigurationName):
    client = session.client('autoscaling', region_name=region)

    try:
        client.create_auto_scaling_group(
            AutoScalingGroupName=AutoScalingGroupName,
            LaunchConfigurationName=LaunchConfigurationName,
            MinSize=2,
            MaxSize=5,
            DesiredCapacity=2,
            AvailabilityZones=['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d'],
            LoadBalancerNames=[LoadBalancerName],
            CapacityRebalance=True
        )
        print("SUCESS: autoscalling created!")

    except Exception as e:
        print('Fail to create autoscalling ', e)    