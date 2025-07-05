# 🔍 Azure AI Image Analyzer

A flexible Azure AI-powered application that analyzes images using Azure Computer Vision API. The application processes images from Azure Blob Storage, analyzes them using Azure AI Vision services, and stores comprehensive results back to Azure Blob Storage with automatic deployment and credential management.

![Python](https://img.shields.io/badge/python-v3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Azure](https://img.shields.io/badge/azure-AI%20Vision-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## ✨ Features

- **🔍 Smart Image Analysis**: Comprehensive image analysis with captions, tags, and object detection
- **🏷️ Flexible Detection**: Configurable keyword detection for any object types or categories
- **📝 Rich Metadata**: Generates detailed captions and extracts objects with confidence scores
- **☁️ Azure Integration**: Seamless integration with Azure Blob Storage and Key Vault
- **📊 Comprehensive Results**: Stores detailed analysis results with metadata and statistics
- **🔒 Secure Credentials**: Supports both Azure Key Vault and local credential files
- **🚀 Auto-Deployment**: Fully automated Azure resource creation and configuration
- **📦 Sample Dataset**: Includes 100 high-quality sample images for immediate testing
- **🐳 Containerized**: Docker support for easy deployment
- **⚙️ Configurable**: Easy configuration through environment variables and config files
- **🖥️ Cross-Platform**: Works on Windows, macOS, and Linux

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

## 🚀 One-Command Quick Start

### Prerequisites
- **Azure CLI** installed and logged in (`az login`)
- **Python 3.12+** installed
- **Active Azure subscription**

### Linux/macOS
```bash
git clone https://github.com/net9876/azure-ai-image-analyzer.git
cd azure-ai-image-analyzer
chmod +x quick_start.sh
./quick_start.sh
```

### Windows (PowerShell)
```powershell
git clone https://github.com/net9876/azure-ai-image-analyzer.git
cd azure-ai-image-analyzer
.\quick_start.ps1
```

**That's it!** ⚡ The script automatically:
- ✅ Deploys all Azure resources
- ✅ Uploads 100 sample images  
- ✅ Configures authentication
- ✅ Runs the analysis
- ✅ Shows comprehensive results

## 📸 Sample Dataset

The repository includes **100 high-quality sample images** featuring:
- **Cat Breeds**: Abyssinian, Bengal, Birman, Bombay, British Shorthair, Egyptian Mau, Maine Coon, Persian, Ragdoll, Russian Blue, Siamese, Sphynx
- **Dog Breeds**: American Bulldogs, American Pit Bull Terriers, Basset Hounds, Beagles, Boxers, English Cocker Spaniels, English Setters, German Shorthaired Pointers, Great Pyrenees, Havanese, Japanese Chin, Keeshonds, Leonbergers, Miniature Pinschers, Newfoundlands, Pomeranians, Pugs, Saint Bernards, Samoyeds, Scottish Terriers, Shiba Inus, Staffordshire Bull Terriers, Wheaten Terriers, Yorkshire Terriers

Perfect for testing AI analysis capabilities and demonstrating breed identification!

## ⚙️ Manual Setup (Advanced Users)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Deploy Azure Resources
```bash
# Automated deployment
python deploy_azure_resources.py --resource-group my-ai-analyzer-rg --location eastus
```

### 3. Choose Authentication Method

#### Option A: Azure Key Vault (Production)
```bash
export CREDENTIAL_METHOD="keyvault"
export KEY_VAULT_URL="https://your-keyvault.vault.azure.net/"
```

#### Option B: Local Credentials (Development)
Create `creds.txt`:
```
storage_connection_string=DefaultEndpointsProtocol=https;AccountName=...
vision_endpoint=https://your-vision-service.cognitiveservices.azure.com/
vision_key=your_vision_api_key
```

```bash
export CREDENTIAL_METHOD="local"
```

### 4. Run Analysis
```bash
python azure_ai_image_analyzer.py
```

## 🔧 Configuration

The analyzer automatically creates a `config.json` file during deployment. You can customize analysis settings:

```json
{
  "analysis_settings": {
    "target_keywords": ["cat", "dog", "animal", "pet"],
    "confidence_threshold": 0.5,
    "max_tags": 10,
    "features": ["caption", "tags", "objects"]
  }
}
```

### Customization Examples

#### Analyze Vehicles
```json
{
  "analysis_settings": {
    "target_keywords": ["car", "truck", "motorcycle", "bus", "vehicle"],
    "confidence_threshold": 0.6
  }
}
```

#### Analyze Architecture
```json
{
  "analysis_settings": {
    "target_keywords": ["building", "house", "architecture", "structure"],
    "confidence_threshold": 0.7
  }
}
```

## 📊 Output Format

The analyzer generates comprehensive JSON results:

```json
{
  "analysis_metadata": {
    "total_images": 100,
    "images_with_targets": 98,
    "analysis_date": "2025-07-04T13:29:23",
    "target_keywords": ["cat", "dog", "animal", "pet"],
    "confidence_threshold": 0.5,
    "analyzer_version": "3.0.0"
  },
  "summary_statistics": {
    "detection_rate": 98.0,
    "avg_confidence": 0.82,
    "total_objects_found": 245,
    "avg_tags_per_image": 7.3
  },
  "detailed_results": [
    {
      "filename": "Maine_Coon_37.jpg",
      "analyzed_at": "2025-07-04T13:29:23",
      "caption": "a large cat sitting on a wooden surface",
      "confidence": 0.89,
      "tags": [
        {"name": "cat", "confidence": 0.95},
        {"name": "maine coon", "confidence": 0.87},
        {"name": "indoor", "confidence": 0.82}
      ],
      "objects": [
        {
          "object": "cat",
          "confidence": 0.91,
          "bounding_box": {"x": 150, "y": 200, "w": 300, "h": 400}
        }
      ],
      "target_objects_detected": ["cat", "maine coon"]
    }
  ]
}
```

## 🐳 Docker Deployment

The project includes automatic Docker deployment for production environments:

```bash
# Deploy as scalable Container App with web interface
python deploy_container_app.py --resource-group my-ai-analyzer-rg

# Result: Web-accessible container with monitoring and auto-scaling
```

### Web Interface Features
- 🔍 **One-click analysis** of 100 sample images
- 📊 **Real-time status** monitoring
- 📋 **Results viewer** with JSON formatting
- 🔄 **Health checks** and logging

### Container App Benefits
- 🚀 **Auto-scaling** (0-3 replicas based on demand)
- 📊 **Monitoring** with Log Analytics integration
- 🔒 **Secure** with managed identity
- 🌍 **Public endpoint** for web access

## 📁 Project Structure

```
azure-ai-image-analyzer/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Container deployment
├── azure_ai_image_analyzer.py         # Main application
├── deploy_azure_resources.py          # Automated deployment
├── quick_start.sh                     # Linux/macOS quick start
├── quick_start.ps1                    # Windows PowerShell quick start
├── config.json                        # Configuration (auto-generated)
├── .gitignore                         # Git ignore rules
├── LICENSE                            # MIT license
└── images/                            # Sample dataset (100 images)
    ├── Abyssinian_77.jpg
    ├── american_bulldog_48.jpg
    ├── Maine_Coon_37.jpg
    └── ... (97 more images)
```

## 🔍 Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff)
- GIF (.gif)

## 🎯 Use Cases

- **Pet Photography**: Analyze and categorize pet photos by breed
- **Content Moderation**: Automated animal detection in user content
- **Research & Education**: Academic research with comprehensive datasets
- **Inventory Management**: Catalog and analyze product images
- **Quality Control**: Automated image content verification
- **Asset Management**: Digital asset organization and tagging

## 🛠️ Development

### Local Development Setup
```bash
# Clone and setup
git clone https://github.com/net9876/azure-ai-image-analyzer.git
cd azure-ai-image-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Deploy Azure resources
./quick_start.sh
```

## 🧹 Cleanup

To remove all Azure resources:
```bash
# Delete entire resource group (WARNING: This deletes everything!)
az group delete --name my-ai-analyzer-rg --yes --no-wait
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/net9876/azure-ai-image-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/net9876/azure-ai-image-analyzer/discussions)
- **Azure Documentation**: [Azure Computer Vision](https://docs.microsoft.com/azure/cognitive-services/computer-vision/)

## 🏆 Acknowledgments

- Built with [Azure Computer Vision](https://azure.microsoft.com/services/cognitive-services/computer-vision/)
- Sample dataset curated for comprehensive AI testing
- Designed for educational, research, and production use
- Community-driven development and enhancement

---

**⭐ If this project helped you, please consider giving it a star!**

## 🚀 What's Next?

- 🔄 **Batch Processing**: Handle thousands of images efficiently
- 🌐 **Web Interface**: Browser-based image upload and analysis
- 📱 **Mobile App**: iOS/Android companion app
- 🤖 **Custom Models**: Train specialized detection models
- 🔔 **Real-time Processing**: Live image analysis capabilities
- 🌍 **Multi-language**: Support for multiple languages
- 📈 **Analytics Dashboard**: Advanced reporting and insights