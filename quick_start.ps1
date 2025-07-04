# Azure AI Image Analyzer - Quick Start Script (Windows PowerShell)
# This script deploys all Azure resources and runs the analyzer automatically

param(
    [string]$ResourceGroup = "my-ai-analyzer-rg",
    [string]$Location = "eastus"
)

# Enable strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "🚀 Azure AI Image Analyzer - Quick Start" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is installed
try {
    $azVersion = az version 2>$null
    if (-not $azVersion) {
        throw "Azure CLI not found"
    }
} catch {
    Write-Host "❌ Azure CLI is not installed!" -ForegroundColor Red
    Write-Host "Please install Azure CLI first:" -ForegroundColor Yellow
    Write-Host "  - Download from: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    Write-Host "  - Or use winget: winget install Microsoft.AzureCLI" -ForegroundColor Yellow
    exit 1
}

# Check if user is logged in to Azure
Write-Host "🔍 Checking Azure authentication..." -ForegroundColor Yellow
try {
    $account = az account show 2>$null | ConvertFrom-Json
    if (-not $account) {
        throw "Not logged in"
    }
} catch {
    Write-Host "❌ Not logged in to Azure!" -ForegroundColor Red
    Write-Host "Please run: az login" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Azure CLI authenticated" -ForegroundColor Green

# Check if Python is installed
$pythonCmd = $null
try {
    python --version 2>$null | Out-Null
    $pythonCmd = "python"
} catch {
    try {
        python3 --version 2>$null | Out-Null
        $pythonCmd = "python3"
    } catch {
        Write-Host "❌ Python is not installed!" -ForegroundColor Red
        Write-Host "Please install Python 3.12+ first from: https://python.org" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "✅ Python found: $pythonCmd" -ForegroundColor Green

# Install dependencies if requirements.txt exists
if (Test-Path "requirements.txt") {
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
    try {
        & $pythonCmd -m pip install -r requirements.txt
        Write-Host "✅ Dependencies installed" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Warning: Could not install some dependencies" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  requirements.txt not found - skipping dependency installation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🏗️  Starting deployment..." -ForegroundColor Cyan
Write-Host "📍 Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "📍 Location: $Location" -ForegroundColor White
Write-Host ""

# Deploy Azure resources
Write-Host "1️⃣  Deploying Azure resources (this may take 5-10 minutes)..." -ForegroundColor Yellow
try {
    & $pythonCmd deploy_azure_resources.py --resource-group $ResourceGroup --location $Location
    if ($LASTEXITCODE -ne 0) {
        throw "Deployment failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Write-Host "Please check the error messages above and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "2️⃣  Extracting Key Vault URL from deployment..." -ForegroundColor Yellow

# Extract Key Vault URL from config.json
$keyVaultUrl = $null
if (Test-Path "config.json") {
    try {
        $pythonScript = @"
import json
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        print(config['deployment_info']['key_vault_url'])
except Exception:
    pass
"@
        $keyVaultUrl = & $pythonCmd -c $pythonScript 2>$null
        
        if ($keyVaultUrl) {
            Write-Host "✅ Key Vault URL found: $keyVaultUrl" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Could not extract Key Vault URL from config.json" -ForegroundColor Yellow
            Write-Host "Falling back to local credentials..." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Error reading config.json, using local credentials..." -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  config.json not found, using local credentials..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "3️⃣  Running the AI Image Analyzer..." -ForegroundColor Yellow

# Set environment variables and run analyzer
if ($keyVaultUrl) {
    $env:KEY_VAULT_URL = $keyVaultUrl
    $env:CREDENTIAL_METHOD = "keyvault"
    Write-Host "🔑 Using Key Vault authentication" -ForegroundColor Green
} else {
    $env:CREDENTIAL_METHOD = "local"
    Write-Host "🔑 Using local credentials" -ForegroundColor Green
}

# Run the analyzer
try {
    & $pythonCmd azure_ai_image_analyzer.py
    if ($LASTEXITCODE -ne 0) {
        throw "Analyzer failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host ""
    Write-Host "❌ Analysis failed! Check the error messages above." -ForegroundColor Red
    exit 1
}

# Success message
Write-Host ""
Write-Host "🎉 SUCCESS! Analysis completed!" -ForegroundColor Green
Write-Host "📊 Check your Azure Storage account for detailed results" -ForegroundColor White
Write-Host "💾 Local backup files were also created" -ForegroundColor White
Write-Host ""
Write-Host "🔗 To run again later:" -ForegroundColor Cyan
if ($keyVaultUrl) {
    Write-Host "   `$env:KEY_VAULT_URL = `"$keyVaultUrl`"" -ForegroundColor White
    Write-Host "   `$env:CREDENTIAL_METHOD = `"keyvault`"" -ForegroundColor White
} else {
    Write-Host "   `$env:CREDENTIAL_METHOD = `"local`"" -ForegroundColor White
}
Write-Host "   $pythonCmd azure_ai_image_analyzer.py" -ForegroundColor White
