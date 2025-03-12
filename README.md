# Azure VM Deployment with Python

This project demonstrates how to use Python and the Azure SDK to programmatically create a Virtual Machine (VM) in Microsoft Azure. The script sets up a resource group, virtual network, subnet, network security group, public IP, network interface, and an Ubuntu VM with SSH key-based authentication.

## Prerequisites

- **Python 3.10+**: Ensure Python is installed on your system.
- **Azure Subscription**: You need an active Azure subscription.
- **Azure Service Principal**: Required for authentication (see Setup).
- **SSH Key Pair**: Generate an SSH key pair if you don’t have one (`ssh-keygen -t rsa -b 4096`).

## Setup

### 1. Install Dependencies
Install the required Python packages:
```bash
pip install azure-identity azure-mgmt-compute azure-mgmt-network azure-mgmt-resource python-dotenv
```

### 2. Create a Service Principal
Create a service principal with Contributor role on your subscription:
```bash
az ad sp create-for-rbac --name "PythonScriptSP" --role Contributor --scopes /subscriptions/<your-subscription-id> --sdk-auth
```
Save the `clientId`, `clientSecret`, and `tenantId` from the output.

### 3. Configure Secrets
Create a `.env` file in the project directory with your Azure credentials:
```bash
echo "AZURE_SUBSCRIPTION_ID=your-subscription-id" > .env
echo "AZURE_CLIENT_ID=your-client-id" >> .env
echo "AZURE_CLIENT_SECRET=your-client-secret" >> .env
echo "AZURE_TENANT_ID=your-tenant-id" >> .env
```
- Replace placeholders with values from your service principal and subscription.

### 4. Update SSH Key (Optional)
The script uses SSH key-based authentication. Replace the `"key_data"` value in `main.py` under `create_virtual_machine` with your own SSH public key:
```python
"key_data": "ssh-rsa AAAAB3NzaC1yc2E... your-email@example.com"
```
- Find your public key in `~/.ssh/id_rsa.pub` or generate a new one with `ssh-keygen`.

### 5. Directory Structure
After setup, your directory should look like this:
```
python_and_azure/
├── main.py         # Main script
├── .env            # Secret file (not tracked by git)
├── .gitignore      # Ignore .env
└── README.md       # This file
```

### 6. Git Ignore
Add `.env` to `.gitignore` to keep secrets safe:
```bash
echo ".env" > .gitignore
```

## Running the Script

1. **Execute the Script**:
   Run the Python script (no `az login` required):
   ```bash
   python3 main.py
   ```
   The script will:
   - Create a resource group (`YonatanResourceGroup`).
   - Set up networking components (VNet, subnet, NSG, public IP, NIC).
   - Deploy an Ubuntu 18.04 VM (`YonatanVm`) with SSH access.

2. **Connect to the VM**:
   After successful execution, the script outputs the VM’s public IP:
   ```
   VM YonatanVm created successfully!
   Connect using: ssh azureuser@<public-ip-address>
   ```
   Use your private key to connect:
   ```bash
   ssh -i ~/.ssh/id_rsa azureuser@<public-ip-address>
   ```

## Configuration

- **Resource Names**: Modify variables in `main.py` (e.g., `resource_group_name`, `vm_name`) to customize names.
- **Location**: Change `location = "eastus"` to another Azure region if needed (e.g., `westus`).
- **VM Size**: Update `"vm_size": "Standard_B1s"` to a different size (e.g., `Standard_D2s_v3`).

## Troubleshooting

- **Authentication Errors**: Verify `.env` contains correct `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_TENANT_ID`.
- **SSH Issues**: Ensure `"key_data"` matches your private key and the path is `/home/azureuser/.ssh/authorized_keys`.
- **Permission Issues**: Confirm the service principal has `Contributor` role on the subscription.

## Idempotency

The `main.py` script is designed to be idempotent, meaning:

- Running the script multiple times will produce the same result
- If resources already exist, the script will:
  - Skip creation of existing resources
  - Update resources if configurations differ
  - Continue execution without errors
- This makes the script safe to run multiple times and reliable for automation

Examples of idempotent behavior:
- If the resource group exists, it won't attempt to create a new one
- If the VM exists with the same configuration, no changes will be made
- If networking components exist, they will be reused

## Cleanup

To avoid incurring costs, delete the resource group after use:
```bash
az group delete --name YonatanResourceGroup --yes --no-wait
```

