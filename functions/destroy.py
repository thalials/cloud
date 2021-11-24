from functions.constants import *

def destroy_instance(resource, client, name_instance):
    print("Destroying instance ", name_instance)

    try:
        instaces = resource.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': [name_instance]}])
        instaces_id = []

        for instance in instaces:
            instaces_id.append(instance.id)

        if len(instaces_id) > 0:
            terminate_waiter = client.get_waiter('instance_terminated')
            instaces.terminate()
            terminate_waiter.wait(InstanceIds=instaces_id)
            print("Instance {} destroyed".format(name_instance))   

    except Exception as e:
        print('Error', e)
        print("It was not possible to destroy the instance ", name_instance)

def destroy_launch_configuration(session, region, LaunchConfigurationNames):
    client_autoscaling = session.client('autoscaling', region_name=region)

    try:
        if len(client_autoscaling.describe_launch_configurations(LaunchConfigurationNames=[LaunchConfigurationNames])['LaunchConfigurations']):
            response = client_autoscaling.delete_launch_configuration(LaunchConfigurationName=LaunchConfigurationNames)
            print("Launch configuration destroyed!\n")
    except Exception as e:
        print('failed to destroy launch config ', e)

def destroy_load_balancer(session, region, LoadBalancerName):
    client_load_balancer = session.client('elb', region_name=region)

    try:
        client_load_balancer.delete_load_balancer(LoadBalancerName=LoadBalancerName)
        print("load balancer destroyed!\n")
    except Exception as e:
        print('Fail to destroy load balancer ', e)

def destroy_autoscalling(session, region, AutoScalingGroupName):
    client_autoscaling = session.client('autoscaling', region_name=region)

    try:
        res = client_autoscaling.describe_auto_scaling_groups()
        for group in res['AutoScalingGroups']:
            if group['AutoScalingGroupName'] == AutoScalingGroupName:
                client_autoscaling.delete_auto_scaling_group(
                    AutoScalingGroupName=AutoScalingGroupName,
                    ForceDelete=True
                )

        done = False
        while not done:
            if len(client_autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=['AUTOSCALLING_ORM'])['AutoScalingGroups']) == 0:
                done = True
            time.sleep(5)
        print("Autoscaling deletado com sucesso\n")
    except Exception as e:
        print('Fail to destroy load balancer ', e)