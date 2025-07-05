"""
Azure Container App Deployment Script for AI Image Analyzer
Deploys the analyzer as a containerized application with Azure Container Registry and Container Apps
This script assumes you already have Azure resources created by deploy_azure_resources.py
"""

import json
import argparse
import subprocess
import os
import time
from typing import Dict, Any

class ContainerDeployer:
    def __init__(self, resource_group: str, location: str = "eastus", config_file: str = "config.json"):
        self.resource_group = resource_group
        self.location = location
        self.config_file = config_file
        
        # Load existing configuration (from previous deployment)
        self.config = self._load_config()
        
        # Generate container-specific resource names
        self.deployment_info = self.config.get("deployment_info", {})
        self.suffix = self._extract_suffix_from_deployment()
        
        self.container_resources = {
            "registry_name": f"aianalyzerregistry{self.suffix}",
            "container_env_name": f"ai-analyzer-env-{self.suffix}",
            "container_app_name": f"ai-analyzer-app-{self.suffix}",
            "log_analytics_name": f"ai-analyzer-logs-{self.suffix}"
        }

    def _load_config(self) -> Dict[str, Any]:
        """Load existing configuration file"""
        if not os.path.exists(self.config_file):
            print(f"❌ Configuration file '{self.config_file}' not found!")
            print("Please run deploy_azure_resources.py first to create Azure resources.")
            exit(1)
        
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        if "deployment_info" not in config:
            print("❌ No deployment info found in config.json!")
            print("Please run deploy_azure_resources.py first to create Azure resources.")
            exit(1)
            
        return config

    def _extract_suffix_from_deployment(self) -> str:
        """Extract the suffix from existing deployment"""
        resource_names = self.deployment_info.get("resource_names", {})
        storage_account = resource_names.get("storage_account", "")
        
        # Extract suffix from storage account name (e.g., aianalyzer0ca92c -> 0ca92c)
        if storage_account.startswith("aianalyzer"):
            return storage_account[len("aianalyzer"):]
        else:
            # Fallback: generate new suffix
            import random
            import string
            return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    def _run_az_command(self, command: str, capture_output: bool = True) -> str:
        """Run Azure CLI command and return output"""
        try:
            print(f"   Running: {command}")
            if capture_output:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    check=True, 
                    capture_output=True, 
                    text=True
                )
                return result.stdout.strip()
            else:
                subprocess.run(command, shell=True, check=True)
                return ""
                
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Command failed: {e}")
            if capture_output and e.stderr:
                print(f"   Error output: {e.stderr}")
            raise

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check Azure CLI
        try:
            self._run_az_command("az version")
        except:
            print("❌ Azure CLI not found!")
            return False
        
        # Check Docker
        try:
            subprocess.run("docker --version", shell=True, check=True, capture_output=True)
        except:
            print("❌ Docker not found!")
            print("Please install Docker: https://docs.docker.com/get-docker/")
            return False
        
        # Check if logged in to Azure
        try:
            self._run_az_command("az account show")
        except:
            print("❌ Not logged in to Azure!")
            print("Please run: az login")
            return False
        
        # Check if Azure resources exist
        try:
            storage_account = self.deployment_info["resource_names"]["storage_account"]
            self._run_az_command(f"az storage account show --name {storage_account} --resource-group {self.resource_group}")
        except:
            print("❌ Azure resources not found!")
            print("Please run deploy_azure_resources.py first.")
            return False
        
        print("✅ All prerequisites met")
        return True

    def create_container_registry(self) -> str:
        """Create Azure Container Registry"""
        registry_name = self.container_resources["registry_name"]
        print(f"📦 Creating Azure Container Registry: {registry_name}")
        
        # Create ACR
        command = f"""az acr create 
            --resource-group {self.resource_group} 
            --name {registry_name} 
            --sku Basic 
            --location {self.location}
            --admin-enabled true""".replace('\n', ' ')
        
        self._run_az_command(command)
        
        # Get login server
        login_server = self._run_az_command(f"az acr show --name {registry_name} --resource-group {self.resource_group} --query loginServer -o tsv")
        
        print(f"✅ Container Registry created: {login_server}")
        return login_server

    def build_and_push_image(self, registry_login_server: str) -> str:
        """Build Docker image and push to ACR"""
        image_name = "azure-ai-image-analyzer"
        image_tag = "latest"
        full_image_name = f"{registry_login_server}/{image_name}:{image_tag}"
        
        print(f"🐳 Building Docker image: {full_image_name}")
        
        # Login to ACR
        registry_name = self.container_resources["registry_name"]
        self._run_az_command(f"az acr login --name {registry_name}")
        
        # Build image
        print("   🔨 Building Docker image...")
        self._run_az_command(f"docker build -t {full_image_name} .", capture_output=False)
        
        # Push image
        print("   📤 Pushing image to registry...")
        self._run_az_command(f"docker push {full_image_name}", capture_output=False)
        
        print(f"✅ Image pushed: {full_image_name}")
        return full_image_name

    def create_log_analytics_workspace(self) -> str:
        """Create Log Analytics workspace for Container Apps"""
        workspace_name = self.container_resources["log_analytics_name"]
        print(f"📊 Creating Log Analytics workspace: {workspace_name}")
        
        # Create workspace
        command = f"""az monitor log-analytics workspace create 
            --resource-group {self.resource_group} 
            --workspace-name {workspace_name} 
            --location {self.location}""".replace('\n', ' ')
        
        self._run_az_command(command)
        
        # Get workspace ID and key
        workspace_id = self._run_az_command(f"""az monitor log-analytics workspace show 
            --resource-group {self.resource_group} 
            --workspace-name {workspace_name} 
            --query customerId -o tsv""".replace('\n', ' '))
        
        workspace_key = self._run_az_command(f"""az monitor log-analytics workspace get-shared-keys 
            --resource-group {self.resource_group} 
            --workspace-name {workspace_name} 
            --query primarySharedKey -o tsv""".replace('\n', ' '))
        
        print(f"✅ Log Analytics workspace created")
        return workspace_id, workspace_key

    def create_container_environment(self, workspace_id: str, workspace_key: str) -> str:
        """Create Container Apps environment"""
        env_name = self.container_resources["container_env_name"]
        print(f"🌐 Creating Container Apps environment: {env_name}")
        
        # Create environment
        command = f"""az containerapp env create 
            --name {env_name} 
            --resource-group {self.resource_group} 
            --location {self.location}
            --logs-workspace-id {workspace_id}
            --logs-workspace-key {workspace_key}""".replace('\n', ' ')
        
        self._run_az_command(command)
        
        print(f"✅ Container Apps environment created: {env_name}")
        return env_name

    def create_container_app(self, image_name: str, environment_name: str) -> str:
        """Create Container App with the analyzer"""
        app_name = self.container_resources["container_app_name"]
        registry_name = self.container_resources["registry_name"]
        key_vault_url = self.deployment_info.get("key_vault_url", "")
        
        print(f"🚀 Creating Container App: {app_name}")
        
        # Get ACR credentials
        acr_username = self._run_az_command(f"az acr credential show --name {registry_name} --query username -o tsv")
        acr_password = self._run_az_command(f"az acr credential show --name {registry_name} --query passwords[0].value -o tsv")
        
        # Create container app
        command = f"""az containerapp create 
            --name {app_name} 
            --resource-group {self.resource_group} 
            --environment {environment_name} 
            --image {image_name}
            --registry-server {image_name.split('/')[0]}
            --registry-username {acr_username}
            --registry-password {acr_password}
            --env-vars CREDENTIAL_METHOD=keyvault KEY_VAULT_URL='{key_vault_url}'
            --cpu 1.0 
            --memory 2.0Gi
            --min-replicas 0
            --max-replicas 3
            --ingress external 
            --target-port 8000""".replace('\n', ' ')
        
        self._run_az_command(command)
        
        # Get app URL
        app_url = self._run_az_command(f"""az containerapp show 
            --name {app_name} 
            --resource-group {self.resource_group} 
            --query properties.configuration.ingress.fqdn -o tsv""".replace('\n', ' '))
        
        print(f"✅ Container App created: https://{app_url}")
        return f"https://{app_url}"

    def assign_managed_identity(self, app_name: str):
        """Assign managed identity and Key Vault permissions"""
        print("🔐 Setting up managed identity and permissions...")
        
        # Enable managed identity
        identity_result = self._run_az_command(f"""az containerapp identity assign 
            --name {app_name} 
            --resource-group {self.resource_group} 
            --system-assigned""".replace('\n', ' '))
        
        # Extract principal ID
        import json
        identity_info = json.loads(identity_result)
        principal_id = identity_info["principalId"]
        
        # Assign Key Vault permissions
        key_vault_name = self.deployment_info["resource_names"]["key_vault"]
        kv_resource_id = f"/subscriptions/{self._get_subscription_id()}/resourceGroups/{self.resource_group}/providers/Microsoft.KeyVault/vaults/{key_vault_name}"
        
        self._run_az_command(f"""az role assignment create 
            --assignee {principal_id} 
            --role "Key Vault Secrets User" 
            --scope {kv_resource_id}""".replace('\n', ' '))
        
        print("✅ Managed identity and permissions configured")

    def _get_subscription_id(self) -> str:
        """Get current subscription ID"""
        return self._run_az_command("az account show --query id -o tsv")

    def update_config_with_container_info(self, app_url: str):
        """Update configuration with container deployment info"""
        print("📋 Updating configuration with container deployment info...")
        
        if "container_deployment" not in self.config:
            self.config["container_deployment"] = {}
        
        self.config["container_deployment"] = {
            "registry_name": self.container_resources["registry_name"],
            "container_app_name": self.container_resources["container_app_name"],
            "container_env_name": self.container_resources["container_env_name"],
            "app_url": app_url,
            "deployment_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "resource_group": self.resource_group,
            "location": self.location
        }
        
        # Save updated config
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        print(f"✅ Configuration updated: {self.config_file}")

    def deploy_container_app(self) -> Dict[str, str]:
        """Deploy the complete container application"""
        print("🚀 Starting Container App Deployment")
        print(f"📍 Resource Group: {self.resource_group}")
        print(f"📍 Location: {self.location}")
        print(f"🎲 Suffix: {self.suffix}")
        print()
        
        if not self.check_prerequisites():
            return {}
        
        try:
            # Step 1: Create Container Registry
            registry_login_server = self.create_container_registry()
            
            # Step 2: Build and push Docker image
            image_name = self.build_and_push_image(registry_login_server)
            
            # Step 3: Create Log Analytics workspace
            workspace_id, workspace_key = self.create_log_analytics_workspace()
            
            # Step 4: Create Container Apps environment
            environment_name = self.create_container_environment(workspace_id, workspace_key)
            
            # Step 5: Create Container App
            app_url = self.create_container_app(image_name, environment_name)
            
            # Step 6: Setup managed identity and permissions
            self.assign_managed_identity(self.container_resources["container_app_name"])
            
            # Step 7: Update configuration
            self.update_config_with_container_info(app_url)
            
            # Summary
            print("\n" + "="*60)
            print("🎉 CONTAINER DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"📦 Container Registry: {self.container_resources['registry_name']}")
            print(f"🐳 Container Image: {image_name}")
            print(f"🌐 Container Environment: {self.container_resources['container_env_name']}")
            print(f"🚀 Container App: {self.container_resources['container_app_name']}")
            print(f"🔗 App URL: {app_url}")
            print()
            print("📊 Monitoring:")
            print(f"   Log Analytics: {self.container_resources['log_analytics_name']}")
            print(f"   Container Logs: az containerapp logs show --name {self.container_resources['container_app_name']} --resource-group {self.resource_group}")
            print()
            print("🔧 Management:")
            print(f"   Scale app: az containerapp update --name {self.container_resources['container_app_name']} --resource-group {self.resource_group} --min-replicas 1 --max-replicas 5")
            print(f"   Update image: az containerapp update --name {self.container_resources['container_app_name']} --resource-group {self.resource_group} --image {image_name}")
            
            return {
                "registry_name": self.container_resources["registry_name"],
                "container_app_name": self.container_resources["container_app_name"],
                "app_url": app_url,
                "image_name": image_name
            }
            
        except Exception as e:
            print(f"\n❌ Container deployment failed: {e}")
            print("🧹 You may want to clean up partially created resources")
            return {}


def main():
    parser = argparse.ArgumentParser(description="Deploy AI Image Analyzer as Container App")
    parser.add_argument("--resource-group", "-g", required=True, help="Azure resource group name (same as used for deploy_azure_resources.py)")
    parser.add_argument("--location", "-l", default="eastus", help="Azure region (default: eastus)")
    parser.add_argument("--config", "-c", default="config.json", help="Configuration file (default: config.json)")
    
    args = parser.parse_args()
    
    print("🐳 Azure AI Image Analyzer - Container Deployment")
    print("This script will create:")
    print("  • Azure Container Registry")
    print("  • Build and push Docker image") 
    print("  • Create Container Apps environment")
    print("  • Deploy as scalable Container App")
    print("  • Configure managed identity and permissions")
    print()
    
    deployer = ContainerDeployer(
        resource_group=args.resource_group,
        location=args.location,
        config_file=args.config
    )
    
    result = deployer.deploy_container_app()
    
    if result:
        print(f"\n✅ Container deployment successful!")
        print(f"🔗 Your app is running at: {result['app_url']}")
        print("🚀 The analyzer will process images automatically when triggered!")
    else:
        print("\n❌ Container deployment failed. Check the error messages above.")


if __name__ == "__main__":
    main()


"""
🐳 CONTAINER DEPLOYMENT SCRIPT FEATURES:

📦 CONTAINER REGISTRY:
✅ Creates Azure Container Registry with admin access
✅ Builds Docker image locally
✅ Pushes to private registry with authentication

🚀 CONTAINER APPS:
✅ Creates Log Analytics workspace for monitoring
✅ Sets up Container Apps environment
✅ Deploys scalable container app (0-3 replicas)
✅ Configures ingress and external access

🔐 SECURITY & IDENTITY:
✅ Enables managed identity for container app
✅ Assigns Key Vault permissions automatically
✅ Uses existing Key Vault from previous deployment
✅ Secure credential management without secrets in container

📊 MONITORING & MANAGEMENT:
✅ Log Analytics integration for monitoring
✅ Container logs accessible via Azure CLI
✅ Scaling and update commands provided
✅ Configuration tracking in config.json

🎯 USAGE:

# Prerequisites: Run deploy_azure_resources.py first
python deploy_azure_resources.py --resource-group my-rg

# Then deploy as container app
python deploy_container_app.py --resource-group my-rg

# Result: Scalable, production-ready container app with monitoring
"""