from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
import os

# Set your Azure subscription ID
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

# Authenticate using default credentials
credential = DefaultAzureCredential()

# Initialize management clients
resource_client = ResourceManagementClient(credential, subscription_id)
network_client = NetworkManagementClient(credential, subscription_id)
compute_client = ComputeManagementClient(credential, subscription_id)

# Configuration
resource_group_name = "YonatanResourceGroup"
location = "eastus"
vm_name = "YonatanVm"
vnet_name = "YonatanVnet"
subnet_name = "YonatanSubnet"
nic_name = "YonatanNic"
public_ip_name = "YonatanPublicIP"
nsg_name = "YonatanNSG"

def create_resource_group():
    resource_client.resource_groups.create_or_update(
        resource_group_name,
        {"location": location}
    )

def create_network_security_group():
    nsg_params = {"location": location}
    nsg_result = network_client.network_security_groups.begin_create_or_update(
        resource_group_name, nsg_name, nsg_params
    ).result()

    # Add SSH rule
    security_rule_params = {
        "protocol": "Tcp",
        "source_port_range": "*",
        "destination_port_range": "22",
        "source_address_prefix": "*",  # Warning: This allows SSH from any IP
        "destination_address_prefix": "*",
        "access": "Allow",
        "priority": 100,
        "direction": "Inbound"
    }
    network_client.security_rules.begin_create_or_update(
        resource_group_name, nsg_name, "AllowSSH", security_rule_params
    ).result()
    
    return nsg_result.id

def create_virtual_network(nsg_id):
    vnet_params = {
        "location": location,
        "address_space": {"address_prefixes": ["10.0.0.0/16"]}
    }
    vnet_result = network_client.virtual_networks.begin_create_or_update(
        resource_group_name, vnet_name, vnet_params
    ).result()

    subnet_params = {
        "address_prefix": "10.0.0.0/24",
        "network_security_group": {"id": nsg_id}
    }
    subnet_result = network_client.subnets.begin_create_or_update(
        resource_group_name, vnet_name, subnet_name, subnet_params
    ).result()

    return subnet_result.id

def create_public_ip():
    public_ip_params = {
        "location": location,
        "public_ip_allocation_method": "Dynamic"
    }
    public_ip_result = network_client.public_ip_addresses.begin_create_or_update(
        resource_group_name, public_ip_name, public_ip_params
    ).result()
    return public_ip_result.id

def create_network_interface(subnet_id, public_ip_id):
    nic_params = {
        "location": location,
        "ip_configurations": [{
            "name": "myIpConfig",
            "subnet": {"id": subnet_id},
            "public_ip_address": {"id": public_ip_id}
        }]
    }
    nic_result = network_client.network_interfaces.begin_create_or_update(
        resource_group_name, nic_name, nic_params
    ).result()
    return nic_result.id

def create_virtual_machine(nic_id):
    vm_params = {
        "location": location,
        "hardware_profile": {"vm_size": "Standard_B1s"},
        "storage_profile": {
            "image_reference": {
                "publisher": "Canonical",
                "offer": "UbuntuServer",
                "sku": "18.04-LTS",
                "version": "latest"
            },
            "os_disk": {
                "create_option": "FromImage",
                "managed_disk": {"storage_account_type": "Standard_LRS"}
            }
        },
        "os_profile": {
            "computer_name": vm_name,
            "admin_username": "azureuser",
            # For password-based SSH:
            "admin_password": "ComplexP@ssw0rd123!",
            # For SSH key-based authentication (uncomment and add your public key):
            "linux_configuration": {
                "disable_password_authentication": True,
                "ssh": {
                    "public_keys": [{
                        "path": "/home/azureuser/.ssh/authorized_keys",
                        "key_data": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDIAfx6n+tGOHhJa1iVwGzdkqlpSDGJQy/vDKUfW0V+lyrUq4VGo9a7uHHYgWdUwqUGJjrU1p8JAEGeGNT3J5fOIIryPoGHaqiAgSrQn93HqCOSx/S7oiSThMCvIVqDDQqP4UnKQ+raeDqKmfMtrOiy8PZkI5y3WdUXuuYPTKpyODiVCYSQq9kEw2K8bymxCJrJbAZQZBaesj9ypBwDuaXKGne7pAcheCvMbncIqksUV2JiYxLf05DOwZKyRxEWSkqi2T/1HSyPfV5mgcqptHZUpqenrmWqUEwgIT1/Bku520Q3TDqEofHQ+sMhZA0nPdZkVyabDKuTlAf1zQNekNtN radai2510@gmail.com"
                    }]
                }
            }
        },
        "network_profile": {
            "network_interfaces": [{"id": nic_id}]
        }
    }
    
    vm_result = compute_client.virtual_machines.begin_create_or_update(
        resource_group_name, vm_name, vm_params
    ).result()
    return vm_result

def main():
    print("Creating resource group...")
    create_resource_group()
    
    print("Creating network security group...")
    nsg_id = create_network_security_group()
    
    print("Creating virtual network and subnet...")
    subnet_id = create_virtual_network(nsg_id)
    
    print("Creating public IP...")
    public_ip_id = create_public_ip()
    
    print("Creating network interface...")
    nic_id = create_network_interface(subnet_id, public_ip_id)
    
    print("Creating virtual machine...")
    vm = create_virtual_machine(nic_id)
    
    # Get the public IP after creation
    public_ip = network_client.public_ip_addresses.get(resource_group_name, public_ip_name)
    print(f"VM {vm.name} created successfully!")
    print(f"Connect using: ssh azureuser@{public_ip.ip_address}")

if __name__ == "__main__":
    main()