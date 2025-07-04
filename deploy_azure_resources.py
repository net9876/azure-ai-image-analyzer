"""
Azure Resource Deployment Script for AI Image Analyzer
Automatically creates all required Azure resources with proper RBAC permissions
"""

import json
import argparse
import subprocess
import random
import string
import os
import time
from pathlib import Path
from typing import Dict, Any

class AzureResourceDeployer:
    def __init__(self, resource_group: str, location: str, config_file: str = "config.json"):
        self.resource_group = resource_group
        self.location = location
        self.config_file = config_file
        self.suffix = self._generate_suffix()
        
        # Load configuration
        self.config = self._load_config()
        
        # Generate resource names
        self.resource_names = self._generate_resource_names()
        
        # Get current user info for RBAC
        self.current_user_id = None
        
    def _generate_suffix(self) -> str:
        """Generate random suffix for unique resource names"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Return default config if file doesn't exist
            return {
                "analysis_settings": {
                    "target_keywords": ["cat", "dog", "animal", "pet"],
                    "confidence_threshold": 0.5,
                    "max_tags": 10,
                    "features": ["caption", "tags", "objects"]
                },
                "containers": {
                    "input_container": "input-images",
                    "results_container": "analysis-results"
                },
                "naming_convention": {
                    "storage_prefix": "aianalyzer",
                    "vision_prefix": "ai-vision",
                    "keyvault_prefix": "ai-kv"
                }
            }
    
    def _generate_resource_names(self) -> Dict[str, str]:
        """Generate all resource names based on configuration"""
        naming = self.config["naming_convention"]
        
        return {
            "storage_account": f"{naming['storage_prefix']}{self.suffix}",
            "ai_vision": f"{naming['vision_prefix']}-{self.suffix}",
            "key_vault": f"{naming['keyvault_prefix']}-{self.suffix}"
        }
    
    def _run_az_command(self, command: str, ignore_errors: bool = False) -> Dict[str, Any]:
        """Run Azure CLI command and return JSON result"""
        try:
            print(f"   Running: {command}")
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            if result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"output": result.stdout.strip()}
            return {}
            
        except subprocess.CalledProcessError as e:
            if ignore_errors:
                print(f"   ⚠️  Command failed (ignoring): {e}")
                return {}
            print(f"   ❌ Command failed: {e}")
            print(f"   Error output: {e.stderr}")
            raise
    
    def _run_az_command_text(self, command: str) -> str:
        """Run Azure CLI command and return text result"""
        try:
            print(f"   Running: {command}")
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Command failed: {e}")
            print(f"   Error output: {e.stderr}")
            raise
    
    def check_azure_login(self) -> bool:
        """Check if user is logged in to Azure CLI and get user info"""
        try:
            account_info = self._run_az_command("az account show")
            print("✅ Azure CLI authentication verified")
            
            # Get current user ID for RBAC assignments
            user_info = self._run_az_command("az ad signed-in-user show")
            self.current_user_id = user_info.get("id") or user_info.get("objectId")
            
            if self.current_user_id:
                print(f"✅ Current user ID: {self.current_user_id}")
            else:
                print("⚠️  Could not get user ID - will try alternative method")
            
            return True
        except:
            print("❌ Not logged in to Azure CLI")
            print("Please run: az login")
            return False
    
    def create_resource_group(self):
        """Create resource group"""
        print(f"📦 Creating resource group: {self.resource_group}")
        
        command = f"az group create --name {self.resource_group} --location {self.location}"
        self._run_az_command(command)
        print(f"✅ Resource group '{self.resource_group}' created in {self.location}")
    
    def create_storage_account(self) -> str:
        """Create storage account and containers"""
        storage_name = self.resource_names["storage_account"]
        print(f"💾 Creating storage account: {storage_name}")
        
        # Create storage account
        command = f"""az storage account create 
            --name {storage_name} 
            --resource-group {self.resource_group} 
            --location {self.location} 
            --sku Standard_LRS 
            --kind StorageV2""".replace('\n', ' ')
        
        self._run_az_command(command)
        
        # Get connection string
        command = f"""az storage account show-connection-string 
            --name {storage_name} 
            --resource-group {self.resource_group} 
            --query connectionString -o tsv""".replace('\n', ' ')
        
        connection_string = self._run_az_command_text(command)
        
        # Create containers
        containers = [
            self.config["containers"]["input_container"],
            self.config["containers"]["results_container"]
        ]
        
        for container in containers:
            print(f"   📁 Creating container: {container}")
            command = f"""az storage container create 
                --name {container} 
                --connection-string "{connection_string}" """.replace('\n', ' ')
            
            self._run_az_command(command)
        
        print(f"✅ Storage account '{storage_name}' created with containers")
        return connection_string
    
    def create_ai_vision(self) -> Dict[str, str]:
        """Create AI Vision service"""
        vision_name = self.resource_names["ai_vision"]
        print(f"👁️  Creating AI Vision service: {vision_name}")
        
        # Create AI Vision service
        command = f"""az cognitiveservices account create 
            --name {vision_name} 
            --resource-group {self.resource_group} 
            --kind ComputerVision 
            --sku S1 
            --location {self.location}""".replace('\n', ' ')
        
        self._run_az_command(command)
        
        # Get endpoint
        command = f"""az cognitiveservices account show 
            --name {vision_name} 
            --resource-group {self.resource_group} 
            --query properties.endpoint -o tsv""".replace('\n', ' ')
        
        endpoint = self._run_az_command_text(command)
        
        # Get key
        command = f"""az cognitiveservices account keys list 
            --name {vision_name} 
            --resource-group {self.resource_group} 
            --query key1 -o tsv""".replace('\n', ' ')
        
        key = self._run_az_command_text(command)
        
        print(f"✅ AI Vision service '{vision_name}' created")
        return {"endpoint": endpoint, "key": key}
    
    def create_key_vault_with_permissions(self, storage_connection: str, vision_info: Dict[str, str]) -> str:
        """Create Key Vault with proper permissions and store secrets"""
        kv_name = self.resource_names["key_vault"]
        print(f"🔐 Creating Key Vault: {kv_name}")
        
        # Create Key Vault with RBAC enabled
        command = f"""az keyvault create 
            --name {kv_name} 
            --resource-group {self.resource_group} 
            --location {self.location}
            --enable-rbac-authorization true""".replace('\n', ' ')
        
        self._run_az_command(command)
        print(f"✅ Key Vault '{kv_name}' created with RBAC enabled")
        
        # Wait for propagation
        print("⏳ Waiting for Key Vault to be ready...")
        time.sleep(10)
        
        # Get Key Vault resource ID
        kv_resource_id = f"/subscriptions/{self._get_subscription_id()}/resourceGroups/{self.resource_group}/providers/Microsoft.KeyVault/vaults/{kv_name}"
        
        # Assign Key Vault Administrator role to current user
        print("🔑 Assigning Key Vault Administrator permissions...")
        
        if self.current_user_id:
            # Method 1: Use user ID
            command = f"""az role assignment create 
                --assignee {self.current_user_id} 
                --role "Key Vault Administrator" 
                --scope "{kv_resource_id}" """.replace('\n', ' ')
        else:
            # Method 2: Use signed-in user
            command = f"""az role assignment create 
                --assignee-object-id $(az ad signed-in-user show --query id -o tsv) 
                --role "Key Vault Administrator" 
                --scope "{kv_resource_id}" """.replace('\n', ' ')
        
        try:
            self._run_az_command(command)
            print("✅ Key Vault Administrator permissions assigned")
        except Exception as e:
            print(f"⚠️  Warning: Could not assign permissions automatically: {e}")
            print("   Trying alternative permission method...")
            
            # Alternative: Use access policy instead of RBAC
            self._setup_keyvault_access_policy(kv_name)
        
        # Wait for permissions to propagate
        print("⏳ Waiting for permissions to propagate...")
        time.sleep(15)
        
        # Store secrets with retry logic
        secrets = {
            "storage-connection-string": storage_connection,
            "vision-endpoint": vision_info["endpoint"],
            "vision-key": vision_info["key"]
        }
        
        for secret_name, secret_value in secrets.items():
            self._store_secret_with_retry(kv_name, secret_name, secret_value)
        
        key_vault_url = f"https://{kv_name}.vault.azure.net/"
        print(f"✅ Key Vault '{kv_name}' created with secrets")
        return key_vault_url
    
    def _get_subscription_id(self) -> str:
        """Get current subscription ID"""
        command = "az account show --query id -o tsv"
        return self._run_az_command_text(command)
    
    def _setup_keyvault_access_policy(self, kv_name: str):
        """Setup Key Vault access policy as fallback"""
        print("   🔑 Setting up Key Vault access policy as fallback...")
        
        # Get current user principal name
        try:
            upn_command = "az ad signed-in-user show --query userPrincipalName -o tsv"
            upn = self._run_az_command_text(upn_command)
            
            command = f"""az keyvault set-policy 
                --name {kv_name} 
                --upn {upn} 
                --secret-permissions get list set delete""".replace('\n', ' ')
            
            self._run_az_command(command)
            print("   ✅ Access policy configured")
        except Exception as e:
            print(f"   ⚠️  Could not set access policy: {e}")
    
    def _store_secret_with_retry(self, kv_name: str, secret_name: str, secret_value: str, max_retries: int = 3):
        """Store secret in Key Vault with retry logic"""
        print(f"   🔑 Storing secret: {secret_name}")
        
        for attempt in range(max_retries):
            try:
                command = f"""az keyvault secret set 
                    --vault-name {kv_name} 
                    --name "{secret_name}" 
                    --value "{secret_value}" """.replace('\n', ' ')
                
                self._run_az_command(command)
                print(f"   ✅ Secret '{secret_name}' stored successfully")
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"   ⚠️  Attempt {attempt + 1} failed, retrying in 10 seconds...")
                    time.sleep(10)
                else:
                    print(f"   ❌ Failed to store secret '{secret_name}' after {max_retries} attempts: {e}")
                    raise
    
    def create_local_credentials_file(self, storage_connection: str, vision_info: Dict[str, str]):
        """Create local credentials file for development"""
        print("📝 Creating local credentials file: creds.txt")
        
        creds_content = f"""# Azure AI Image Analyzer Credentials
# Generated automatically by deployment script
# DO NOT COMMIT THIS FILE TO VERSION CONTROL

storage_connection_string={storage_connection}
vision_endpoint={vision_info["endpoint"]}
vision_key={vision_info["key"]}

# Usage:
# export CREDENTIAL_METHOD="local"
# python azure_ai_image_analyzer.py
"""
        
        with open("creds.txt", "w") as f:
            f.write(creds_content)
        
        print("✅ Local credentials file created")
        print("⚠️  Remember: creds.txt is gitignored for security")
    
    def upload_sample_images(self, storage_connection: str):
        """Upload sample images if they exist"""
        images_folder = "images"
        if not os.path.exists(images_folder):
            print(f"⚠️  Sample images folder '{images_folder}' not found. Skipping upload.")
            return
        
        print(f"📤 Uploading sample images from '{images_folder}' folder")
        
        input_container = self.config["containers"]["input_container"]
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif')
        uploaded_count = 0
        
        # Get list of image files
        image_files = [f for f in Path(images_folder).glob('*') 
                      if f.is_file() and f.suffix.lower() in image_extensions]
        
        print(f"   Found {len(image_files)} image files to upload")
        
        # Upload in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(image_files), batch_size):
            batch = image_files[i:i + batch_size]
            print(f"   📦 Uploading batch {i//batch_size + 1}/{(len(image_files) + batch_size - 1)//batch_size}")
            
            for file_path in batch:
                blob_name = file_path.name
                
                command = f"""az storage blob upload 
                    --container-name {input_container} 
                    --file "{file_path}" 
                    --name "{blob_name}" 
                    --connection-string "{storage_connection}" 
                    --overwrite""".replace('\n', ' ')
                
                try:
                    self._run_az_command(command)
                    uploaded_count += 1
                    if uploaded_count % 10 == 0:
                        print(f"      ✅ Uploaded {uploaded_count} images...")
                except Exception as e:
                    print(f"   ⚠️  Failed to upload {blob_name}: {e}")
        
        print(f"✅ Uploaded {uploaded_count} sample images")
    
    def update_config_with_resources(self, key_vault_url: str):
        """Update configuration file with deployed resource information"""
        print("📋 Updating configuration file with resource information")
        
        # Add deployment information to config
        self.config["deployment_info"] = {
            "resource_group": self.resource_group,
            "location": self.location,
            "key_vault_url": key_vault_url,
            "resource_names": self.resource_names,
            "deployment_date": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        # Save updated config
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        print(f"✅ Configuration updated: {self.config_file}")
    
    def deploy_all_resources(self) -> Dict[str, str]:
        """Deploy all Azure resources with proper error handling"""
        print("🚀 Starting Azure Resource Deployment")
        print(f"📍 Resource Group: {self.resource_group}")
        print(f"📍 Location: {self.location}")
        print(f"🎲 Suffix: {self.suffix}")
        print()
        
        # Check Azure login
        if not self.check_azure_login():
            return {}
        
        try:
            # Deploy resources step by step
            self.create_resource_group()
            storage_connection = self.create_storage_account()
            vision_info = self.create_ai_vision()
            
            # Try to create Key Vault with proper permissions
            try:
                key_vault_url = self.create_key_vault_with_permissions(storage_connection, vision_info)
            except Exception as e:
                print(f"⚠️  Key Vault creation failed: {e}")
                print("📝 Falling back to local credentials only...")
                key_vault_url = None
            
            # Create local credentials for development
            self.create_local_credentials_file(storage_connection, vision_info)
            
            # Upload sample images
            self.upload_sample_images(storage_connection)
            
            # Update configuration
            if key_vault_url:
                self.update_config_with_resources(key_vault_url)
            
            # Summary
            print("\n" + "="*60)
            print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"📦 Resource Group: {self.resource_group}")
            print(f"💾 Storage Account: {self.resource_names['storage_account']}")
            print(f"👁️  AI Vision: {self.resource_names['ai_vision']}")
            
            if key_vault_url:
                print(f"🔐 Key Vault: {self.resource_names['key_vault']}")
                print(f"🔗 Key Vault URL: {key_vault_url}")
                print()
            print("🐳 Ready to run with Docker:")
            print("   docker build -t azure-ai-image-analyzer .")
            print("   docker run --env-file .env azure-ai-image-analyzer")
            print("🚀 Ready to run analyzer with local credentials:")
            print('   export CREDENTIAL_METHOD="local"')
            print('   python azure_ai_image_analyzer.py')
            
            result = {
                "resource_group": self.resource_group,
                "storage_account": self.resource_names['storage_account'],
                "ai_vision": self.resource_names['ai_vision'],
                "key_vault": self.resource_names['key_vault']
            }
            
            if key_vault_url:
                result["key_vault_url"] = key_vault_url
            
            return result
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {e}")
            print("🧹 You may want to clean up partially created resources:")
            print(f"   az group delete --name {self.resource_group} --yes --no-wait")
            return {}


def main():
    parser = argparse.ArgumentParser(description="Deploy Azure resources for AI Image Analyzer")
    parser.add_argument("--resource-group", "-g", required=True, help="Azure resource group name")
    parser.add_argument("--location", "-l", default="eastus", help="Azure region (default: eastus)")
    parser.add_argument("--config", "-c", default="config.json", help="Configuration file (default: config.json)")
    
    args = parser.parse_args()
    
    deployer = AzureResourceDeployer(
        resource_group=args.resource_group,
        location=args.location,
        config_file=args.config
    )
    
    result = deployer.deploy_all_resources()
    
    if result:
        print(f"\n✅ Deployment successful! Resources created:")
        for key, value in result.items():
            print(f"   {key}: {value}")
    else:
        print("\n❌ Deployment failed. Check the error messages above.")


if __name__ == "__main__":
    main()


"""
🚀 ENHANCED DEPLOYMENT SCRIPT FEATURES:

🔐 RBAC PERMISSION HANDLING:
✅ Automatically gets current user ID
✅ Assigns Key Vault Administrator role
✅ Fallback to access policies if RBAC fails
✅ Retry logic for permission propagation
✅ Graceful fallback to local credentials

⏳ TIMING & RELIABILITY:
✅ Proper wait times for resource propagation
✅ Retry logic for secret storage
✅ Batch upload for large image sets
✅ Error handling with graceful degradation

📦 COMPREHENSIVE SETUP:
✅ Creates all Azure resources
✅ Handles both RBAC and legacy Key Vault permissions
✅ Uploads sample images in batches
✅ Creates both Key Vault and local credentials
✅ Updates configuration with deployment info

🎯 USAGE EXAMPLES:

# Basic deployment
python deploy_azure_resources.py --resource-group my-ai-analyzer-rg

# Custom location and config
python deploy_azure_resources.py -g my-rg -l westus2 -c custom_config.json

# The script will:
# 1. Create all Azure resources
# 2. Set up proper permissions automatically
# 3. Store secrets in Key Vault (with fallback)
# 4. Upload all sample images
# 5. Create local creds.txt for development
# 6. Provide ready-to-use commands
"""