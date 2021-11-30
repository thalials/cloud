from functions.constants import *
from functions.create import *
from functions.destroy import *
from functions.initialize import *

def main():
    # deleta tudo o que já existia 
    initialize(AWS_REGION_NAME_NV, nv_resource, nv_client, nv_s, ORM)
    initialize(AWS_REGION_NAME_OHIO, ohio_resource, ohio_client, ohio_s, POSTGRES)

    # COLOCAR SLEEP DEPOIS DE apagar o load balancer 

    # create security group 
    sg_id_ohio = create_security_group(ohio_client, default_ohio) # ohio
    sg_id_nv = create_security_group(nv_client, default_nv) # north virginia
    print("\n")

    # create instances OHIO and NORTH VIRGINIA 
    ohio_instance, nv_instance = instances()

    time.sleep(90) # tempo pra instalar as dependencias 
    print("Provavelmente, o setup já foi instalado em cada instância. Criando AMI......\n")
    
    # create AMI for ORM instance
    AMI = create_ami(nv_client, nv_instance, 'image_ORM')

    # destroy instance NORTH VIRGINIA
    destroy_instance(nv_resource, nv_client, ORM)

    # create target group
    north_virginia_client = boto3.client('ec2', region_name=AWS_REGION_NAME_NV)
    load_balancer_client = boto3.client('elbv2', region_name=AWS_REGION_NAME_NV)
    load_balancer_waiter_available = load_balancer_client.get_waiter('load_balancer_available')

    target_group = create_target_group(LB_TARGET_GROUP_NAME,LB_PROTOCOL,
                                                LB_HEALTH_CHECK_ENABLED,
                                                LB_HEALTH_CHECK_PROTOCOL,
                                                LB_HEALTH_CHECK_PORT,
                                                LB_HEALTH_CHECK_PATH,
                                                LB_PORT,
                                                LB_TARGET_TYPE,
                                                north_virginia_client,
                                                load_balancer_client)

    # create loadbalancer
    response_lb, amazon_resource_name = create_load_balancer(north_virginia_client, load_balancer_client, LoadBalancerName, sg_id_nv, load_balancer_waiter_available)
    DNSName = response_lb['LoadBalancers'][0]['DNSName'] 
    with open("DNSName.txt", "w") as file:
        file.write(DNSName)

    # create listener 
    create_listener(LT_PROTOCOL, LT_PORT, LT_DEFAULT_ACTIONS_TYPE, target_group, amazon_resource_name, load_balancer_client)
    
    # create launch configuration with AMI
    create_launch_configuration(nv_s, AWS_REGION_NAME_NV, LaunchConfigurationNames, sg_id_nv, AMI)
   
    # create autoscalling 
    client_autoscaling = boto3.client('autoscaling', region_name=AWS_REGION_NAME_NV)
    create_auto_scalling(client_autoscaling, AWS_REGION_NAME_NV, AutoScalingGroupName, LaunchConfigurationNames, target_group)
    
if __name__ == "__main__":
    main()
