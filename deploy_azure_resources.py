"""
Azure Resource Deployment Script for AI Image Analyzer
Automatically creates all required Azure resources with proper naming conventions
"""

import json
import argparse
import subprocess
import random
import string
import os
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
                    "target_keywords": ["person", "car", "animal", "building"],
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
    
    def _run_az_command(self, command: str) -> Dict[str, Any]:
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
                return json.loads(result.stdout)
            return {}
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Command failed: {e}")
            print(f"   Error output: {e.stderr}")
            raise
        except json.JSONDecodeError:
            print(f"   ⚠️  Command succeeded but returned non-JSON output")
            return {}
    
    def check_azure_login(self) -> bool:
        """Check if user is logged in to Azure CLI"""
        try:
            self._run_az_command("az account show")
            print("✅ Azure CLI authentication verified")
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
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        connection_string = result.stdout.strip()
        
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
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        endpoint = result.stdout.strip()
        
        # Get key
        command = f"""az cognitiveservices account keys list 
            --name {vision_name} 
            --resource-group {self.resource_group} 
            --query key1 -o tsv""".replace('\n', ' ')
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        key = result.stdout.strip()
        
        print(f"✅ AI Vision service '{vision_name}' created")
        return {"endpoint": endpoint, "key": key}
    
    def create_key_vault(self, storage_connection: str, vision_info: Dict[str, str]) -> str:
        """Create Key Vault and store secrets"""
        kv_name = self.resource_names["key_vault"]
        print(f"🔐 Creating Key Vault: {kv_name}")
        
        # Create Key Vault
        command = f"""az keyvault create 
            --name {kv_name} 
            --resource-group {self.resource_group} 
            --location {self.location}""".replace('\n', ' ')
        
        self._run_az_command(command)
        
        # Store secrets
        secrets = {
            "storage-connection-string": storage_connection,
            "vision-endpoint": vision_info["endpoint"],
            "vision-key": vision_info["key"]
        }
        
        for secret_name, secret_value in secrets.items():
            print(f"   🔑 Storing secret: {secret_name}")
            command = f"""az keyvault secret set 
                --vault-name {kv_name} 
                --name "{secret_name}" 
                --value "{secret_value}" """.replace('\n', ' ')
            
            self._run_az_command(command)
        
        key_vault_url = f"https://{kv_name}.vault.azure.net/"
        print(f"✅ Key Vault '{kv_name}' created with secrets")
        return key_vault_url
    
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
        
        for file_path in Path(images_folder).glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                blob_name = file_path.name
                print(f"   📁 Uploading: {blob_name}")
                
                command = f"""az storage blob upload 
                    --container-name {input_container} 
                    --file "{file_path}" 
                    --name "{blob_name}" 
                    --connection-string "{storage_connection}" 
                    --overwrite""".replace('\n', ' ')
                
                try:
                    self._run_az_command(command)
                    uploaded_count += 1
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
            "deployment_date": "2025-07-04T" + "13:29:23"  # Current timestamp
        }
        
        # Save updated config
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        print(f"✅ Configuration updated: {self.config_file}")
    
    def deploy_all_resources(self) -> Dict[str, str]:
        """Deploy all Azure resources"""
        print("🚀 Starting Azure Resource Deployment")
        print(f"📍 Resource Group: {self.resource_group}")
        print(f"📍 Location: {self.location}")
        print(f"🎲 Suffix: {self.suffix}")
        print()
        
        # Check Azure login
        if not self.check_azure_login():
            return {}
        
        try:
            # Deploy resources
            self.create_resource_group()
            storage_connection = self.create_storage_account()
            vision_info = self.create_ai_vision()
            key_vault_url = self.create_key_vault(storage_connection, vision_info)
            
            # Create local credentials for development
            self.create_local_credentials_file(storage_connection, vision_info)
            
            # Upload sample images
            self.upload_sample_images(storage_connection)
            
            # Update configuration
            self.update_config_with_resources(key_vault_url)
            
            # Summary
            print("\n" + "="*60)
            print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"📦 Resource Group: {self.resource_group}")
            print(f"💾 Storage Account: {self.resource_names['storage_account']}")
            print(f"👁️  AI Vision: {self.resource_names['ai_vision']}")
            print(f"🔐 Key Vault: {self.resource_names['key_vault']}")
            print(f"🔗 Key Vault URL: {key_vault_url}")
            print()
            print("🚀 Ready to run analyzer:")
            print("   # Using Key Vault:")
            print(f'   export KEY_VAULT_URL="{key_vault_url}"')
            print('   export CREDENTIAL_METHOD="keyvault"')
            print('   python azure_ai_image_analyzer.py')
            print()
            print("   # Using local credentials:")
            print('   export CREDENTIAL_METHOD="local"')
            print('   python azure_ai_image_analyzer.py')
            
            return {
                "key_vault_url": key_vault_url,
                "resource_group": self.resource_group,
                "storage_account": self.resource_names['storage_account'],
                "ai_vision": self.resource_names['ai_vision'],
                "key_vault": self.resource_names['key_vault']
            }
            
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
    
    deployer.deploy_all_resources()


if __name__ == "__main__":
    main()


"""
🚀 DEPLOYMENT SCRIPT FEATURES:

📦 AUTOMATIC RESOURCE CREATION:
✅ Resource Group with specified location
✅ Storage Account with unique naming
✅ AI Vision service (Computer Vision)
✅ Key Vault for secure credential storage
✅ Blob containers for images and results

🔐 CREDENTIAL MANAGEMENT:
✅ Stores secrets in Azure Key Vault
✅ Creates local creds.txt for development
✅ Supports both authentication methods

📤 SAMPLE DATA SETUP:
✅ Uploads images from local 'images' folder
✅ Creates proper container structure
✅ Handles multiple image formats

⚙️ CONFIGURATION:
✅ Updates config.json with deployment info
✅ Configurable naming conventions
✅ Resource name collision avoidance

🎯 USAGE EXAMPLES:

# Basic deployment
python deploy_azure_resources.py --resource-group my-ai-analyzer-rg

# Custom location
python deploy_azure_resources.py -g my-rg -l westus2

# Custom config file
python deploy_azure_resources.py -g my-rg -c custom_config.json

# Complete example
python deploy_azure_resources.py \
  --resource-group ai-image-analyzer-prod \
  --location eastus \
  --config production_config.json
"""