from functions.constants import *
from functions.create import *
from functions.destroy import *
from functions.initialize import *

def main():
    # initialize(region, resource, client, session, name_instance):
    initialize(AWS_REGION_NAME_NV, nv_resource, nv_client, nv_s, ORM)
    initialize(AWS_REGION_NAME_OHIO, ohio_resource, ohio_client, ohio_s, POSTGRES)

    # create security group 
    sg_id_ohio = create_security_group(ohio_client, default_ohio) # ohio
    sg_id_nv = create_security_group(nv_client, default_nv) # north virginia

    # create instances OHIO and NORTH VIRGINIA 
    ohio_instance, nv_instance = instances()

    # create AMI for ORM instance
    AMI = create_ami(nv_client, nv_instance, 'image_ORM')

    # destroy instance NORTH VIRGINIA
    destroy_instance(nv_resource, nv_client, ORM)

    create_launch_configuration(nv_s, AWS_REGION_NAME_NV, LaunchConfigurationNames, sg_id_nv, AMI)

    # create loadbalancer
    DNSName = create_load_balancer(nv_s, AWS_REGION_NAME_NV, LoadBalancerName, sg_id_nv)
    with open("DNSName.txt", "w") as file:
        file.write(DNSName)
    
    # create autoscalling with AMI
    create_auto_scalling(nv_s, AWS_REGION_NAME_NV, AutoScalingGroupName, LaunchConfigurationNames)
    
if __name__ == "__main__":
    main()
