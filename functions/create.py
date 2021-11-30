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

        time.sleep(90)
        print('Instance {} created'.format(name_instance))
        return instance 
    except Exception as e:
        print('Error', e)
        print("Não deu certo criar a {}".format(name_instance))

def instances():
    # create instance in ohio 
    print("---------- OHIO ----------")
    userData = read_file("setup.sh")
    ohio = create_instance(ohio_resource, imageId_ohio, default_ohio, userData, POSTGRES)
    
    ohio[0].wait_until_running()
    print("Instancia em ohio criada!\n")

    # pega o ip publico de ohio 
    instances = ohio_client.describe_instances(Filters=[{'Name':'instance-state-name', 'Values':['running']}])
    ip_public_ohio = instances['Reservations'][0]['Instances'][0]['PublicIpAddress']
    print("ip: \n", ip_public_ohio)
    print("----------------------------\n")

    print("---------- NORTH VIRGINIA ----------")
    # create instance in north virginia
    orm = read_file("setup_orm.sh").format(ip_public_ohio)

    nv = create_instance(nv_resource, imageId_nv, default_nv, orm, ORM)

    nv[0].wait_until_running()
    print("Instancia em North Virginia criada!\n")
    print("--------------------------------------\n")

    return ohio, nv

def create_ami(client, instance, name):
    waiter = client.get_waiter('image_available')
    image = client.create_image(InstanceId=instance[0].id,
                                NoReboot=True,
                                Name=name)

    waiter.wait(ImageIds=[image["ImageId"]])

    print("---------------AMI criada--------------\n")
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
        # print('Security Group Created {0} in vpc {1}.'.format(security_group_id, VpcId))
        
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
        print('Fail to create security group ', e)

def create_security_group(ec2, name_security_group):          
    security = config_security_group(ec2, name_security_group)
    print("Security group created - {}".format(name_security_group))
    return security

def describe_subnets_for_aws(ec2):
    current_subnets = ec2.describe_subnets()['Subnets']
    subnet_ids = []
    for subnet in current_subnets:
        subnet_ids.append(subnet['SubnetId'])
    return subnet_ids

def create_load_balancer(ec2, lb_client, load_balancer_name, security_group, waiter): 
    try:
        # print('Creating loadbalancer {0}'.format(load_balancer_name))
        subnets = describe_subnets_for_aws(ec2)

        load_balancer = lb_client.create_load_balancer(
            SecurityGroups=[security_group],
            Tags=[{"Key": "Name", "Value": load_balancer_name}],
            Name=load_balancer_name,
            Subnets=subnets,
            IpAddressType='ipv4',
            Type='application',
            Scheme='internet-facing'
        )

        amazon_resource_name = load_balancer['LoadBalancers'][0]['LoadBalancerArn']
        waiter.wait(LoadBalancerArns=[amazon_resource_name])
        time.sleep(10)

        print("LOADBALANCER=", load_balancer)
        print("arn = ", amazon_resource_name)

        print('Loadbalancer {0} created!'.format(load_balancer_name))
        return load_balancer, amazon_resource_name

    except Exception as e:
        print('Fail to create loadbalancer ', e)

def create_listener(protocol, port, default_actions_type, target_group_arn,  load_balancer_arn, ec2):
    try:
        ec2.create_listener(
            LoadBalancerArn=load_balancer_arn,
            Protocol=protocol,
            Port=port,
            DefaultActions=[{'Type': default_actions_type, 'TargetGroupArn': target_group_arn}]
        )
        print('Listener created!')
    except Exception as e:
        print("Fail to create listener", e)

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

def create_auto_scalling(client, region, AutoScalingGroupName, LaunchConfigurationName, TargetGroupARNs):
    # client = boto3.client('autoscaling', region_name=region)

    try:
        client.create_auto_scaling_group(
            AutoScalingGroupName=AutoScalingGroupName,
            LaunchConfigurationName=LaunchConfigurationName,
            MinSize=1,
            MaxSize=3,
            AvailabilityZones=['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1e', 'us-east-1f'],
            # LoadBalancerNames=[LoadBalancerName],
            TargetGroupARNs=[TargetGroupARNs],
            # CapacityRebalance=True
        )
        print("SUCESS: autoscalling created!")

    except Exception as e:
        print('Fail to create autoscalling ', e)    

def create_target_group(target_group_name, protocol, health_check_enabled, health_check_protocol, health_check_port, health_check_path, port, target_type, ec2_region, ec2_lb):
    try:
        vpc_id = ec2_region.describe_vpcs()["Vpcs"][0]["VpcId"]

        target_group = ec2_lb.create_target_group(Name=target_group_name,
                                                Protocol=protocol,
                                                Port=port,
                                                HealthCheckEnabled=health_check_enabled,
                                                HealthCheckProtocol=health_check_protocol,
                                                HealthCheckPort=health_check_port,
                                                HealthCheckPath=health_check_path,
                                                Matcher={'HttpCode': '200,302,301,404,403'},
                                                TargetType=target_type,
                                                VpcId=vpc_id )

        print('Created Target group {0}'.format(target_group_name))

        return target_group["TargetGroups"][0]["TargetGroupArn"]

    except Exception as e:
        print("Fail to create target group ", e)