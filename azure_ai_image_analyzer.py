"""
Azure AI Image Analyzer - Generalized Image Analysis with Flexible Configuration
Supports both Azure Key Vault and local credential file authentication
"""

import json
import requests
import os
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, AzureCliCredential, ChainedTokenCredential

class AzureAIImageAnalyzer:
    def __init__(self, credential_method: str = "keyvault", key_vault_url: str = None, config_file: str = "config.json"):
        """
        Initialize the analyzer with flexible credential management
        
        Args:
            credential_method: "keyvault" or "local"
            key_vault_url: Azure Key Vault URL (required if using keyvault method)
            config_file: Path to configuration file
        """
        self.credential_method = credential_method
        self.key_vault_url = key_vault_url
        self.results = []
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Initialize credentials based on method
        if credential_method == "keyvault":
            self._init_keyvault_credentials()
        elif credential_method == "local":
            self._init_local_credentials()
        else:
            raise ValueError("credential_method must be 'keyvault' or 'local'")
        
        # Initialize Azure services
        self._initialize_azure_services()

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"✅ Configuration loaded from {config_file}")
                return config
            else:
                # Create default configuration
                default_config = {
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
                
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                print(f"✅ Default configuration created: {config_file}")
                return default_config
                
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            raise

    def _get_azure_credential(self):
        """Get appropriate Azure credential based on environment"""
        try:
            credentials = [
                ManagedIdentityCredential(),
                AzureCliCredential(),
                DefaultAzureCredential()
            ]
            credential = ChainedTokenCredential(*credentials)
            print("✅ Azure credentials configured successfully")
            return credential
        except Exception as e:
            print(f"❌ Error setting up Azure credentials: {e}")
            raise

    def _init_keyvault_credentials(self):
        """Initialize credentials from Azure Key Vault"""
        if not self.key_vault_url:
            raise ValueError("key_vault_url is required when using keyvault credential method")
        
        try:
            print("🔑 Connecting to Azure Key Vault...")
            self.credential = self._get_azure_credential()
            
            self.key_vault_client = SecretClient(
                vault_url=self.key_vault_url,
                credential=self.credential
            )
            
            print("   📥 Loading storage-connection-string...")
            self.storage_connection_string = self.key_vault_client.get_secret("storage-connection-string").value
            
            print("   📥 Loading vision-endpoint...")
            self.vision_endpoint = self.key_vault_client.get_secret("vision-endpoint").value
            
            print("   📥 Loading vision-key...")
            self.vision_key = self.key_vault_client.get_secret("vision-key").value
            
            print("✅ All secrets loaded successfully from Key Vault")
            
        except Exception as e:
            print(f"❌ Error loading secrets from Key Vault: {e}")
            raise

    def _init_local_credentials(self):
        """Initialize credentials from local file"""
        creds_file = "creds.txt"
        
        if not os.path.exists(creds_file):
            print(f"❌ Credentials file '{creds_file}' not found!")
            print("Please create a creds.txt file with the following format:")
            print("storage_connection_string=your_storage_connection_string")
            print("vision_endpoint=your_vision_endpoint")
            print("vision_key=your_vision_key")
            raise FileNotFoundError(f"Credentials file '{creds_file}' not found")
        
        try:
            print(f"🔑 Loading credentials from {creds_file}...")
            
            credentials = {}
            with open(creds_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        credentials[key.strip()] = value.strip()
            
            self.storage_connection_string = credentials.get('storage_connection_string')
            self.vision_endpoint = credentials.get('vision_endpoint')
            self.vision_key = credentials.get('vision_key')
            
            # Validate required credentials
            missing_creds = []
            if not self.storage_connection_string:
                missing_creds.append('storage_connection_string')
            if not self.vision_endpoint:
                missing_creds.append('vision_endpoint')
            if not self.vision_key:
                missing_creds.append('vision_key')
            
            if missing_creds:
                raise ValueError(f"Missing required credentials: {', '.join(missing_creds)}")
            
            print("✅ All credentials loaded successfully from local file")
            
        except Exception as e:
            print(f"❌ Error loading credentials from local file: {e}")
            raise

    def _initialize_azure_services(self):
        """Initialize Azure Blob Storage and AI Vision services"""
        try:
            # Initialize Blob Storage client
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.storage_connection_string
            )
            
            # Clean up endpoint URL
            self.vision_endpoint = self.vision_endpoint.rstrip('/')
            
            # Get container names from config
            self.input_container_name = self.config["containers"]["input_container"]
            self.results_container_name = self.config["containers"]["results_container"]
            
            # Ensure containers exist
            self._ensure_containers_exist()
            
            print("✅ Azure services initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing Azure services: {e}")
            raise

    def _ensure_containers_exist(self):
        """Create containers if they don't exist"""
        containers = [self.input_container_name, self.results_container_name]
        
        for container_name in containers:
            try:
                container_client = self.blob_service_client.get_container_client(container_name)
                
                try:
                    container_client.get_container_properties()
                    print(f"✅ Container '{container_name}' already exists")
                except Exception:
                    container_client.create_container()
                    print(f"✅ Created container '{container_name}'")
                    
            except Exception as e:
                print(f"⚠️  Warning: Could not ensure container '{container_name}' exists: {e}")

    def upload_sample_images(self, images_folder: str = "images"):
        """Upload sample images from local folder to blob storage"""
        if not os.path.exists(images_folder):
            print(f"⚠️  Sample images folder '{images_folder}' not found. Skipping upload.")
            return
        
        try:
            container_client = self.blob_service_client.get_container_client(self.input_container_name)
            uploaded_count = 0
            
            # Supported image extensions
            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif')
            
            for file_path in Path(images_folder).glob('*'):
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    blob_name = file_path.name
                    
                    # Check if blob already exists
                    try:
                        container_client.get_blob_client(blob_name).get_blob_properties()
                        print(f"   📁 Skipping {blob_name} (already exists)")
                        continue
                    except:
                        pass  # Blob doesn't exist, proceed to upload
                    
                    # Upload the file
                    with open(file_path, 'rb') as data:
                        container_client.upload_blob(name=blob_name, data=data, overwrite=False)
                        print(f"   📤 Uploaded {blob_name}")
                        uploaded_count += 1
            
            print(f"✅ Uploaded {uploaded_count} sample images to '{self.input_container_name}' container")
            
        except Exception as e:
            print(f"❌ Error uploading sample images: {e}")

    def get_image_list(self) -> List[str]:
        """Get all image files from the input container"""
        try:
            container_client = self.blob_service_client.get_container_client(self.input_container_name)
            images = []
            
            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif')
            
            for blob in container_client.list_blobs():
                if blob.name.lower().endswith(image_extensions):
                    images.append(blob.name)
            
            print(f"Found {len(images)} images in container '{self.input_container_name}'")
            return images
            
        except Exception as e:
            print(f"❌ Error accessing container '{self.input_container_name}': {e}")
            return []

    def analyze_image_with_rest(self, blob_name: str) -> Optional[Dict[str, Any]]:
        """Download and analyze a single image using REST API"""
        try:
            # Download image
            blob_client = self.blob_service_client.get_blob_client(
                container=self.input_container_name, 
                blob=blob_name
            )
            image_data = blob_client.download_blob().readall()
            print(f"   Downloaded {len(image_data)} bytes")
            
            # Prepare REST API call
            headers = {
                'Ocp-Apim-Subscription-Key': self.vision_key,
                'Content-Type': 'application/octet-stream'
            }
            
            # API endpoint for image analysis
            url = f"{self.vision_endpoint}/computervision/imageanalysis:analyze"
            
            # Get features from config
            features = ','.join(self.config["analysis_settings"]["features"])
            
            params = {
                'api-version': '2024-02-01',
                'features': features
            }
            
            # Make API call
            response = requests.post(url, headers=headers, params=params, data=image_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   API call successful")
                return self.process_api_response(result, blob_name)
            else:
                print(f"   API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error analyzing {blob_name}: {e}")
            return None

    def process_api_response(self, result: Dict[str, Any], blob_name: str) -> Dict[str, Any]:
        """Process the API response into our format"""
        settings = self.config["analysis_settings"]
        target_keywords = settings["target_keywords"]
        confidence_threshold = settings["confidence_threshold"]
        max_tags = settings["max_tags"]
        
        analysis = {
            'filename': blob_name,
            'analyzed_at': datetime.now().isoformat(),
            'caption': "No description",
            'confidence': 0,
            'tags': [],
            'objects': [],
            'target_objects_detected': []
        }
        
        # Extract caption
        if 'captionResult' in result and result['captionResult']:
            caption_data = result['captionResult']
            analysis['caption'] = caption_data.get('text', 'No description')
            analysis['confidence'] = round(caption_data.get('confidence', 0), 2)
        
        # Extract tags
        if 'tagsResult' in result and 'values' in result['tagsResult']:
            for tag in result['tagsResult']['values'][:max_tags]:
                if tag['confidence'] >= confidence_threshold:
                    analysis['tags'].append({
                        'name': tag['name'],
                        'confidence': round(tag['confidence'], 2)
                    })
        
        # Extract objects
        if 'objectsResult' in result and 'values' in result['objectsResult']:
            for obj in result['objectsResult']['values']:
                if 'tags' in obj and obj['tags']:
                    obj_confidence = obj['tags'][0]['confidence']
                    if obj_confidence >= confidence_threshold:
                        analysis['objects'].append({
                            'object': obj['tags'][0]['name'],
                            'confidence': round(obj_confidence, 2),
                            'bounding_box': obj.get('boundingBox', {})
                        })
        
        # Look for target keywords
        all_terms = []
        
        # Add tag names
        if 'tagsResult' in result and 'values' in result['tagsResult']:
            all_terms.extend([tag['name'] for tag in result['tagsResult']['values'] 
                             if tag['confidence'] >= confidence_threshold])
        
        # Add object names
        if 'objectsResult' in result and 'values' in result['objectsResult']:
            for obj in result['objectsResult']['values']:
                if 'tags' in obj and obj['tags']:
                    if obj['tags'][0]['confidence'] >= confidence_threshold:
                        all_terms.append(obj['tags'][0]['name'])
        
        # Find target keyword matches
        for term in all_terms:
            for keyword in target_keywords:
                if keyword.lower() in term.lower():
                    if term not in analysis['target_objects_detected']:
                        analysis['target_objects_detected'].append(term)
        
        print(f"   Found {len(analysis['tags'])} tags, {len(analysis['target_objects_detected'])} target objects")
        return analysis

    def analyze_all_images(self):
        """Analyze all images and display results"""
        # Upload sample images if they exist
        self.upload_sample_images()
        
        images = self.get_image_list()
        
        if not images:
            print("No images found!")
            return
        
        target_keywords = self.config["analysis_settings"]["target_keywords"]
        
        print("\n" + "="*60)
        print("🔍 AZURE AI IMAGE ANALYSIS RESULTS")
        print(f"🎯 Target Keywords: {', '.join(target_keywords)}")
        print("="*60)
        
        for i, image_name in enumerate(images, 1):
            print(f"\n[{i}/{len(images)}] Analyzing: {image_name}")
            
            result = self.analyze_image_with_rest(image_name)
            if result:
                self.results.append(result)
                self.display_single_result(result)
        
        # Show summary and save results
        self.show_summary()
        self.save_results_to_blob()

    def display_single_result(self, result: Dict[str, Any]):
        """Display results for one image"""
        print(f"📸 {result['filename']}")
        print(f"📝 Description: {result['caption']} (confidence: {result['confidence']})")
        
        if result['target_objects_detected']:
            print(f"🎯 Target objects found: {', '.join(set(result['target_objects_detected']))}")
        else:
            print("🔍 No target objects detected")
        
        if result['tags']:
            top_tags = [f"{tag['name']} ({tag['confidence']})" for tag in result['tags'][:5]]
            print(f"🏷️  Top tags: {', '.join(top_tags)}")
        
        print("-" * 50)

    def show_summary(self):
        """Show analysis summary"""
        total_images = len(self.results)
        images_with_targets = sum(1 for r in self.results if r['target_objects_detected'])
        target_keywords = self.config["analysis_settings"]["target_keywords"]
        
        print(f"\n📊 SUMMARY:")
        print(f"   • Total images analyzed: {total_images}")
        print(f"   • Images with target objects: {images_with_targets}")
        print(f"   • Detection rate: {(images_with_targets/total_images)*100:.0f}%" if total_images > 0 else "")
        print(f"   • Target keywords: {', '.join(target_keywords)}")
        
        # Most common objects found
        all_objects = []
        for result in self.results:
            all_objects.extend(result['target_objects_detected'])
        
        if all_objects:
            from collections import Counter
            common_objects = Counter(all_objects).most_common(3)
            print(f"   • Most common: {', '.join([f'{obj} ({count})' for obj, count in common_objects])}")

    def save_results_to_blob(self):
        """Save results to Azure Blob Storage and locally"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        target_keywords = self.config["analysis_settings"]["target_keywords"]
        
        # Create comprehensive results structure
        results_data = {
            'analysis_metadata': {
                'total_images': len(self.results),
                'images_with_targets': sum(1 for r in self.results if r['target_objects_detected']),
                'analysis_date': datetime.now().isoformat(),
                'target_keywords': target_keywords,
                'confidence_threshold': self.config["analysis_settings"]["confidence_threshold"],
                'input_container': self.input_container_name,
                'results_container': self.results_container_name,
                'credential_method': self.credential_method,
                'analyzer_version': '3.0.0'
            },
            'summary_statistics': {
                'detection_rate': (sum(1 for r in self.results if r['target_objects_detected']) / len(self.results) * 100) if self.results else 0,
                'avg_confidence': sum(r['confidence'] for r in self.results) / len(self.results) if self.results else 0,
                'total_objects_found': sum(len(r['target_objects_detected']) for r in self.results),
                'avg_tags_per_image': sum(len(r['tags']) for r in self.results) / len(self.results) if self.results else 0
            },
            'configuration_used': self.config,
            'detailed_results': self.results
        }
        
        # Convert to JSON
        json_data = json.dumps(results_data, indent=2)
        
        # Save to Azure Blob Storage
        try:
            blob_name = f"image_analysis_{timestamp}.json"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.results_container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(json_data, overwrite=True)
            print(f"☁️  Results saved to Azure Blob: {self.results_container_name}/{blob_name}")
            
            # Also create a "latest.json" for easy access
            latest_blob_client = self.blob_service_client.get_blob_client(
                container=self.results_container_name,
                blob="image_analysis_latest.json"
            )
            latest_blob_client.upload_blob(json_data, overwrite=True)
            print(f"☁️  Latest results: {self.results_container_name}/image_analysis_latest.json")
            
        except Exception as e:
            print(f"⚠️  Could not save to blob storage: {e}")
        
        # Save locally as backup
        try:
            local_filename = f"image_analysis_results_{timestamp}.json"
            with open(local_filename, 'w') as f:
                f.write(json_data)
            print(f"💾 Local backup saved: {local_filename}")
        except Exception as e:
            print(f"⚠️  Could not save locally: {e}")


def generate_random_suffix(length: int = 6) -> str:
    """Generate random string for resource naming"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def main():
    """Main function with flexible credential management"""
    
    # Configuration from environment variables
    CREDENTIAL_METHOD = os.getenv("CREDENTIAL_METHOD", "keyvault")
    KEY_VAULT_URL = os.getenv("KEY_VAULT_URL")
    CONFIG_FILE = os.getenv("CONFIG_FILE", "config.json")
    
    print("🚀 Starting Azure AI Image Analyzer")
    print(f"🔑 Credential Method: {CREDENTIAL_METHOD}")
    
    if CREDENTIAL_METHOD == "keyvault":
        if not KEY_VAULT_URL:
            print("❌ KEY_VAULT_URL environment variable is required when using keyvault method")
            print("Set it with: export KEY_VAULT_URL='https://your-keyvault.vault.azure.net/'")
            return
        print(f"🔑 Key Vault: {KEY_VAULT_URL}")
    else:
        print("🔑 Using local credentials file (creds.txt)")
    
    try:
        # Create analyzer
        analyzer = AzureAIImageAnalyzer(
            credential_method=CREDENTIAL_METHOD,
            key_vault_url=KEY_VAULT_URL,
            config_file=CONFIG_FILE
        )
        
        # Display configuration
        print(f"📦 Input Container: {analyzer.input_container_name}")
        print(f"💾 Results Container: {analyzer.results_container_name}")
        print(f"🎯 Target Keywords: {', '.join(analyzer.config['analysis_settings']['target_keywords'])}")
        
        # Analyze all images and save results
        analyzer.analyze_all_images()
        
        print("\n✅ Analysis complete with results stored in Azure Blob Storage!")
        
    except Exception as e:
        print(f"❌ Error running analyzer: {e}")
        print("\n🔧 Troubleshooting:")
        if CREDENTIAL_METHOD == "keyvault":
            print("   1. Ensure you're logged in to Azure CLI: az login")
            print("   2. Check your Key Vault URL and permissions")
            print("   3. Verify secrets exist in Key Vault:")
            print("      - storage-connection-string")
            print("      - vision-endpoint") 
            print("      - vision-key")
        else:
            print("   1. Ensure creds.txt file exists in the project root")
            print("   2. Check the file format:")
            print("      storage_connection_string=your_connection_string")
            print("      vision_endpoint=your_endpoint")
            print("      vision_key=your_key")


if __name__ == "__main__":
    main()


"""
📊 ENHANCED FEATURES:

🔄 FLEXIBLE AUTHENTICATION:
✅ Azure Key Vault integration for production
✅ Local credentials file for development  
✅ Automatic credential validation
✅ Environment variable configuration

🎯 CONFIGURABLE ANALYSIS:
✅ Customizable target keywords
✅ Adjustable confidence thresholds
✅ Flexible feature selection
✅ Container name configuration

📦 AUTOMATED DEPLOYMENT:
✅ Sample image upload from local folder
✅ Automatic container creation
✅ Resource naming conventions
✅ Configuration file generation

📋 COMPREHENSIVE RESULTS:
{
  "analysis_metadata": {
    "total_images": 25,
    "images_with_targets": 18,
    "target_keywords": ["car", "person", "building"],
    "confidence_threshold": 0.5,
    "analyzer_version": "3.0.0"
  },
  "summary_statistics": {
    "detection_rate": 72.0,
    "avg_confidence": 0.78,
    "total_objects_found": 45,
    "avg_tags_per_image": 6.2
  },
  "configuration_used": {...},
  "detailed_results": [...]
}

🎯 USAGE EXAMPLES:

# Using Key Vault (Production)
export CREDENTIAL_METHOD="keyvault"
export KEY_VAULT_URL="https://my-kv.vault.azure.net/"
python azure_ai_image_analyzer.py

# Using Local Credentials (Development)
export CREDENTIAL_METHOD="local"
python azure_ai_image_analyzer.py

# Custom Configuration
export CONFIG_FILE="custom_config.json"
python azure_ai_image_analyzer.py
"""