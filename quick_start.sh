#!/bin/bash

# Azure AI Image Analyzer - Quick Start Script (Linux/macOS)
# This script deploys all Azure resources and runs the analyzer automatically

set -e  # Exit on any error

echo "🚀 Azure AI Image Analyzer - Quick Start"
echo "=========================================="
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed!"
    echo "Please install Azure CLI first:"
    echo "  - Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    echo "  - macOS: brew install azure-cli"
    echo "  - Or visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if user is logged in to Azure
echo "🔍 Checking Azure authentication..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure!"
    echo "Please run: az login"
    exit 1
fi

echo "✅ Azure CLI authenticated"

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed!"
    echo "Please install Python 3.12+ first"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "✅ Python found: $PYTHON_CMD"

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found - skipping dependency installation"
fi

# Set default resource group name
RESOURCE_GROUP=${1:-"my-ai-analyzer-rg"}
LOCATION=${2:-"eastus"}

echo ""
echo "🏗️  Starting deployment..."
echo "📍 Resource Group: $RESOURCE_GROUP"
echo "📍 Location: $LOCATION"
echo ""

# Deploy Azure resources
echo "1️⃣  Deploying Azure resources (this may take 5-10 minutes)..."
$PYTHON_CMD deploy_azure_resources.py --resource-group "$RESOURCE_GROUP" --location "$LOCATION"

# Check if deployment was successful
if [ $? -ne 0 ]; then
    echo "❌ Deployment failed!"
    echo "Please check the error messages above and try again."
    exit 1
fi

echo ""
echo "2️⃣  Extracting Key Vault URL from deployment..."

# Extract Key Vault URL from config.json
if [ -f "config.json" ]; then
    KEY_VAULT_URL=$($PYTHON_CMD -c "
import json
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        print(config['deployment_info']['key_vault_url'])
except Exception as e:
    print('')
" 2>/dev/null)
    
    if [ -n "$KEY_VAULT_URL" ]; then
        echo "✅ Key Vault URL found: $KEY_VAULT_URL"
    else
        echo "⚠️  Could not extract Key Vault URL from config.json"
        echo "Falling back to local credentials..."
        export CREDENTIAL_METHOD="local"
    fi
else
    echo "⚠️  config.json not found, using local credentials..."
    export CREDENTIAL_METHOD="local"
fi

echo ""
echo "3️⃣  Running the AI Image Analyzer..."

# Set environment variables and run analyzer
if [ -n "$KEY_VAULT_URL" ]; then
    export KEY_VAULT_URL="$KEY_VAULT_URL"
    export CREDENTIAL_METHOD="keyvault"
    echo "🔑 Using Key Vault authentication"
else
    export CREDENTIAL_METHOD="local"
    echo "🔑 Using local credentials"
fi

# Run the analyzer
$PYTHON_CMD azure_ai_image_analyzer.py

# Check if analysis was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Analysis completed!"
    echo "📊 Check your Azure Storage account for detailed results"
    echo "💾 Local backup files were also created"
    echo ""
    echo "🔗 To run again later:"
    if [ -n "$KEY_VAULT_URL" ]; then
        echo "   export KEY_VAULT_URL=\"$KEY_VAULT_URL\""
        echo "   export CREDENTIAL_METHOD=\"keyvault\""
    else
        echo "   export CREDENTIAL_METHOD=\"local\""
    fi
    echo "   $PYTHON_CMD azure_ai_image_analyzer.py"
else
    echo ""
    echo "❌ Analysis failed! Check the error messages above."
    exit 1
fi