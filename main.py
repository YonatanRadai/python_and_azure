from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve secrets from .env
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")
tenant_id = os.getenv("AZURE_TENANT_ID")

# Authenticate using service principal credentials
credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

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
    try:
        # Check if resource group exists
        resource_client.resource_groups.get(resource_group_name)
        print(f"Resource group '{resource_group_name}' already exists, skipping creation.")
    except ResourceNotFoundError:
        # Create if it doesn't exist
        print(f"Creating resource group '{resource_group_name}'...")
        resource_client.resource_groups.create_or_update(
            resource_group_name,
            {"location": location}
        )

def create_network_security_group():
    try:
        # Check if NSG exists
        nsg = network_client.network_security_groups.get(resource_group_name, nsg_name)
        print(f"Network security group '{nsg_name}' already exists, skipping creation.")
        return nsg.id
    except ResourceNotFoundError:
        # Create if it doesn't exist
        print(f"Creating network security group '{nsg_name}'...")
        nsg_params = {"location": location}
        nsg_result = network_client.network_security_groups.begin_create_or_update(
            resource_group_name, nsg_name, nsg_params
        ).result()

        # Add SSH rule (only if NSG is newly created)
        try:
            network_client.security_rules.get(resource_group_name, nsg_name, "AllowSSH")
            print("SSH rule already exists, skipping creation.")
        except ResourceNotFoundError:
            print("Adding SSH rule to NSG...")
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
    try:
        # Check if VNet exists
        vnet = network_client.virtual_networks.get(resource_group_name, vnet_name)
        print(f"Virtual network '{vnet_name}' already exists.")
    except ResourceNotFoundError:
        # Create if it doesn't exist
        print(f"Creating virtual network '{vnet_name}'...")
        vnet_params = {
            "location": location,
            "address_space": {"address_prefixes": ["10.0.0.0/16"]}
        }
        vnet = network_client.virtual_networks.begin_create_or_update(
            resource_group_name, vnet_name, vnet_params
        ).result()

    # Check if subnet exists
    try:
        subnet = network_client.subnets.get(resource_group_name, vnet_name, subnet_name)
        print(f"Subnet '{subnet_name}' already exists, skipping creation.")
        return subnet.id
    except ResourceNotFoundError:
        # Create subnet if it doesn't exist
        print(f"Creating subnet '{subnet_name}'...")
        subnet_params = {
            "address_prefix": "10.0.0.0/24",
            "network_security_group": {"id": nsg_id}
        }
        subnet_result = network_client.subnets.begin_create_or_update(
            resource_group_name, vnet_name, subnet_name, subnet_params
        ).result()
        return subnet_result.id

def create_public_ip():
    try:
        # Check if public IP exists
        public_ip = network_client.public_ip_addresses.get(resource_group_name, public_ip_name)
        print(f"Public IP '{public_ip_name}' already exists, skipping creation.")
        return public_ip.id
    except ResourceNotFoundError:
        # Create if it doesn't exist
        print(f"Creating public IP '{public_ip_name}'...")
        public_ip_params = {
            "location": location,
            "public_ip_allocation_method": "Dynamic"
        }
        public_ip_result = network_client.public_ip_addresses.begin_create_or_update(
            resource_group_name, public_ip_name, public_ip_params
        ).result()
        return public_ip_result.id

def create_network_interface(subnet_id, public_ip_id):
    try:
        # Check if NIC exists
        nic = network_client.network_interfaces.get(resource_group_name, nic_name)
        print(f"Network interface '{nic_name}' already exists, skipping creation.")
        return nic.id
    except ResourceNotFoundError:
        # Create if it doesn't exist
        print(f"Creating network interface '{nic_name}'...")
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
    try:
        # Check if VM exists
        vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
        print(f"Virtual machine '{vm_name}' already exists, skipping creation.")
        return vm
    except ResourceNotFoundError:
        # Create if it doesn't exist
        print(f"Creating virtual machine '{vm_name}'...")
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
    print("Starting deployment...")
    create_resource_group()
    
    nsg_id = create_network_security_group()
    subnet_id = create_virtual_network(nsg_id)
    public_ip_id = create_public_ip()
    nic_id = create_network_interface(subnet_id, public_ip_id)
    vm = create_virtual_machine(nic_id)
    
    # Get the public IP after creation (even if VM already exists)
    public_ip = network_client.public_ip_addresses.get(resource_group_name, public_ip_name)
    print(f"VM {vm.name} deployment complete!")
    print(f"Connect using: ssh azureuser@{public_ip.ip_address}")

if __name__ == "__main__":
    main()