# 🔍 Azure AI Image Analyzer

A flexible Azure AI-powered application that analyzes images using Azure Computer Vision API. The application processes images from Azure Blob Storage, analyzes them using Azure AI Vision services, and stores comprehensive results back to Azure Blob Storage with automatic deployment and credential management.

## ✨ Features

- **🔍 Smart Image Analysis**: Comprehensive image analysis with captions, tags, and object detection
- **🏷️ Flexible Detection**: Configurable keyword detection for any object types or categories
- **📝 Rich Metadata**: Generates detailed captions and extracts objects with confidence scores
- **☁️ Azure Integration**: Seamless integration with Azure Blob Storage and Key Vault
- **📊 Comprehensive Results**: Stores detailed analysis results with metadata and statistics
- **🔒 Secure Credentials**: Supports both Azure Key Vault and local credential files
- **🚀 Auto-Deployment**: Automatic setup of Azure resources and sample image upload
- **🐳 Containerized**: Docker support for easy deployment
- **⚙️ Configurable**: Easy configuration through environment variables and config files

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Azure Blob    │    │   Azure AI       │    │   Azure Key     │
│   Storage       │◄──►│   Vision API     │    │   Vault         │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Azure AI Image  │
                    │ Analyzer        │
                    │ Application     │
                    └─────────────────┘
```

## 📋 Prerequisites

- **Python**: 3.12.6 or higher
- **Azure Subscription** with the following services:
  - Azure Computer Vision (AI Vision)
  - Azure Blob Storage
  - Azure Key Vault (optional)
- **Azure CLI** (for authentication and deployment)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/azure-ai-image-analyzer.git
cd azure-ai-image-analyzer
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Choose Your Credential Method

#### Option A: Azure Key Vault (Recommended for Production)

```bash
# Set environment variable
export CREDENTIAL_METHOD="keyvault"
export KEY_VAULT_URL="https://your-keyvault.vault.azure.net/"
```

#### Option B: Local Credentials File (Development)

Create a `creds.txt` file in the project root:

```
storage_connection_string=DefaultEndpointsProtocol=https;AccountName=...
vision_endpoint=https://your-vision-service.cognitiveservices.azure.com/
vision_key=your_vision_api_key
```

```bash
# Set environment variable
export CREDENTIAL_METHOD="local"
```

### 4. Deploy Azure Resources (Optional)

Use the built-in deployment script to create all Azure resources:

```bash
# Login to Azure
az login

# Run deployment script
python deploy_azure_resources.py --resource-group my-analyzer-rg --location eastus
```

This will create:
- Resource Group
- Storage Account with containers
- AI Vision Service
- Key Vault (if using keyvault method)
- Upload sample images

### 5. Configure Analysis Settings

Edit `config.json` to customize your analysis:

```json
{
  "analysis_settings": {
    "target_keywords": ["car", "person", "animal", "building"],
    "confidence_threshold": 0.5,
    "max_tags": 10,
    "features": ["caption", "tags", "objects"]
  },
  "containers": {
    "input_container": "input-images",
    "results_container": "analysis-results"
  }
}
```

### 6. Run the Analyzer

```bash
python azure_ai_image_analyzer.py
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CREDENTIAL_METHOD` | `keyvault` or `local` | `keyvault` | Yes |
| `KEY_VAULT_URL` | Azure Key Vault URL | None | If using keyvault |
| `RESOURCE_GROUP` | Azure Resource Group | None | For deployment |
| `STORAGE_ACCOUNT_NAME` | Storage Account Name | `aiimageanalyzer{random}` | No |
| `AI_VISION_NAME` | AI Vision Service Name | `ai-vision-{random}` | No |

### Credential Files

#### creds.txt (Local Development)
```
storage_connection_string=DefaultEndpointsProtocol=https;AccountName=...
vision_endpoint=https://your-vision-service.cognitiveservices.azure.com/
vision_key=your_vision_api_key
```

#### Key Vault Secrets
| Secret Name | Description |
|-------------|-------------|
| `storage-connection-string` | Azure Storage connection string |
| `vision-endpoint` | Azure AI Vision endpoint URL |
| `vision-key` | Azure AI Vision API key |

### Configuration File (config.json)

```json
{
  "analysis_settings": {
    "target_keywords": ["object1", "object2", "category1"],
    "confidence_threshold": 0.5,
    "max_tags": 10,
    "features": ["caption", "tags", "objects", "faces"]
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
```

## 📊 Output Format

The analyzer generates comprehensive JSON results:

```json
{
  "analysis_metadata": {
    "total_images": 25,
    "images_with_targets": 18,
    "analysis_date": "2025-07-04T13:29:23",
    "target_keywords": ["car", "person", "building"],
    "confidence_threshold": 0.5,
    "analyzer_version": "3.0.0"
  },
  "summary_statistics": {
    "detection_rate": 72.0,
    "avg_confidence": 0.78,
    "most_common_objects": ["person", "car", "building"]
  },
  "detailed_results": [
    {
      "filename": "street_scene_01.jpg",
      "analyzed_at": "2025-07-04T13:29:23",
      "caption": "a busy street with cars and people",
      "confidence": 0.87,
      "tags": [
        {"name": "outdoor", "confidence": 0.95},
        {"name": "street", "confidence": 0.89}
      ],
      "objects": [
        {
          "object": "car",
          "confidence": 0.92,
          "bounding_box": {"x": 100, "y": 150, "w": 200, "h": 120}
        }
      ],
      "target_objects_detected": ["car", "person"]
    }
  ]
}
```

## 🚀 Deployment Options

### Azure Container Instances

```bash
# Build and deploy
docker build -t azure-ai-image-analyzer .

# Deploy to ACI
az container create \
  --resource-group my-analyzer-rg \
  --name image-analyzer \
  --image azure-ai-image-analyzer \
  --environment-variables \
    CREDENTIAL_METHOD="keyvault" \
    KEY_VAULT_URL="https://your-kv.vault.azure.net/" \
  --assign-identity \
  --cpu 2 \
  --memory 4
```

### Azure Functions

The project includes Azure Functions deployment templates in the `deployment/` folder.

### Local Docker

```bash
# Build
docker build -t azure-ai-image-analyzer .

# Run with local credentials
docker run -it \
  -v $(pwd)/creds.txt:/app/creds.txt:ro \
  -v $(pwd)/images:/app/images:ro \
  -e CREDENTIAL_METHOD="local" \
  azure-ai-image-analyzer
```

## 📁 Project Structure

```
azure-ai-image-analyzer/
├── README.md
├── requirements.txt
├── Dockerfile
├── azure_ai_image_analyzer.py     # Main application
├── deploy_azure_resources.py      # Azure deployment script
├── config.json                    # Configuration file
├── creds.txt                      # Local credentials (gitignored)
├── .gitignore
├── LICENSE
├── images/                        # Sample images (uploaded automatically)
│   ├── sample_001.jpg
│   ├── sample_002.jpg
│   └── ...
├── deployment/                    # Deployment templates
│   ├── azure-functions/
│   ├── container-instances/
│   └── kubernetes/
└── docs/
    ├── setup-guide.md
    ├── api-reference.md
    ├── configuration-guide.md
    └── troubleshooting.md
```

## 🔍 Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff)
- GIF (.gif)

## 🎯 Use Cases

- **Content Analysis**: Analyze and categorize image collections
- **Quality Control**: Automated image content verification
- **Inventory Management**: Catalog and analyze product images
- **Research**: Academic research with image datasets
- **Content Moderation**: Automated content screening
- **Asset Management**: Digital asset organization and tagging

## 🛠️ Development

### Sample Images Setup

The project includes sample images in the `images/` folder. These are automatically uploaded to your storage account during deployment:

```bash
# Manual upload of sample images
python upload_sample_images.py --container input-images --folder images/
```

### Custom Analysis

Extend the analyzer by modifying the `process_api_response` method:

```python
def process_api_response(self, result, blob_name, target_keywords):
    # Add custom analysis logic here
    # Example: facial recognition, custom object detection, etc.
    pass
```

### Configuration Examples

#### Analyze Vehicles
```json
{
  "analysis_settings": {
    "target_keywords": ["car", "truck", "motorcycle", "bus", "vehicle"],
    "confidence_threshold": 0.6
  }
}
```

#### Analyze People and Activities
```json
{
  "analysis_settings": {
    "target_keywords": ["person", "people", "crowd", "activity", "sport"],
    "confidence_threshold": 0.7
  }
}
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/azure-ai-image-analyzer/issues)
- **Documentation**: [Project Wiki](https://github.com/yourusername/azure-ai-image-analyzer/wiki)
- **Azure Support**: [Azure Documentation](https://docs.microsoft.com/azure/)

## 🏆 Acknowledgments

- Built with [Azure Computer Vision](https://azure.microsoft.com/services/cognitive-services/computer-vision/)
- Designed for flexibility and enterprise deployment
- Community-driven development and enhancement

---

**⭐ If this project helped you, please consider giving it a star!**