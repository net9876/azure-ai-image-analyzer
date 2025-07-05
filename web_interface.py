"""
Web Interface for Azure AI Image Analyzer Container App
Provides a simple web UI for triggering analysis and viewing results
"""

import os
import json
import subprocess
import glob
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI(
    title="Azure AI Image Analyzer", 
    description="Containerized AI Image Analysis with Web Interface",
    version="3.0.0"
)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main web interface"""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Azure AI Image Analyzer</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #0078d4; margin-bottom: 10px; }
        .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #107c10; }
        .button-group { margin: 20px 0; }
        button { background: #0078d4; color: white; border: none; padding: 12px 24px; margin: 8px; border-radius: 5px; cursor: pointer; font-size: 14px; transition: background 0.3s; }
        button:hover { background: #106ebe; }
        button.secondary { background: #107c10; }
        button.secondary:hover { background: #0e6e0e; }
        button.tertiary { background: #5c2d91; }
        button.tertiary:hover { background: #4c2579; }
        #output { background: #f8f9fa; padding: 20px; border-radius: 5px; white-space: pre-wrap; font-family: 'Courier New', monospace; border: 1px solid #dee2e6; max-height: 500px; overflow-y: auto; margin: 20px 0; }
        .loading { color: #0078d4; }
        .success { color: #107c10; }
        .error { color: #d13438; }
        .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }
        .info-card { background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #0078d4; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Azure AI Image Analyzer</h1>
        <div class="status">
            <strong>Container App Status:</strong> Running ✅ | <strong>Version:</strong> 3.0.0
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <h4>🎯 Analysis Features</h4>
                <ul>
                    <li>Object Detection</li>
                    <li>Image Captioning</li>
                    <li>Tag Extraction</li>
                    <li>Confidence Scoring</li>
                </ul>
            </div>
            <div class="info-card">
                <h4>📊 Sample Dataset</h4>
                <ul>
                    <li>100 High-Quality Images</li>
                    <li>Multiple Cat Breeds</li>
                    <li>Various Dog Breeds</li>
                    <li>Comprehensive Analysis</li>
                </ul>
            </div>
        </div>
        
        <h3>🚀 Actions:</h3>
        <div class="button-group">
            <button onclick="runAnalysis()">🔍 Run Full Analysis</button>
            <button class="secondary" onclick="getStatus()">📊 System Status</button>
            <button class="tertiary" onclick="getResults()">📋 View Latest Results</button>
            <button class="secondary" onclick="clearOutput()">🗑️ Clear Output</button>
        </div>
        
        <h3>📊 Output:</h3>
        <div id="output">Welcome to Azure AI Image Analyzer! 🎉

Click "Run Full Analysis" to process 100 sample images with Azure AI Vision.
The analysis will detect objects, generate captions, and provide confidence scores.

System ready for operation...</div>
    </div>
    
    <script>
        async function runAnalysis() {
            const output = document.getElementById('output');
            output.innerHTML = '🔄 Starting comprehensive image analysis...\\n\\nThis will process 100 sample images using Azure AI Vision.\\nPlease wait, this may take 5-10 minutes...\\n\\n';
            output.className = 'loading';
            
            try {
                const response = await fetch('/analyze', { method: 'POST', headers: {'Content-Type': 'application/json'} });
                const result = await response.json();
                
                if (result.status === 'success') {
                    output.className = 'success';
                    output.innerHTML = `✅ Analysis completed successfully!\\n\\n${result.message}\\n\\nOutput preview:\\n${result.output}\\n\\nTimestamp: ${result.timestamp}`;
                } else {
                    output.className = 'error';
                    output.innerHTML = `❌ Analysis failed:\\n\\n${result.message}\\n\\nError details:\\n${result.error || 'No additional details'}\\n\\nOutput:\\n${result.output || 'No output'}`;
                }
            } catch (error) {
                output.className = 'error';
                output.innerHTML = `❌ Network error: ${error.message}`;
            }
        }
        
        async function getStatus() {
            const output = document.getElementById('output');
            output.innerHTML = '🔍 Checking system status...';
            output.className = 'loading';
            
            try {
                const response = await fetch('/status');
                const result = await response.json();
                output.className = 'success';
                output.innerHTML = `📊 System Status Report:\\n\\n${JSON.stringify(result, null, 2)}`;
            } catch (error) {
                output.className = 'error';
                output.innerHTML = `❌ Error getting status: ${error.message}`;
            }
        }
        
        async function getResults() {
            const output = document.getElementById('output');
            output.innerHTML = '📋 Loading latest analysis results...';
            output.className = 'loading';
            
            try {
                const response = await fetch('/results');
                const result = await response.json();
                
                if (result.status === 'no_results') {
                    output.className = '';
                    output.innerHTML = `ℹ️ No analysis results found.\\n\\nRun an analysis first to see results here.`;
                } else if (result.status === 'error') {
                    output.className = 'error';
                    output.innerHTML = `❌ Error loading results: ${result.message}`;
                } else {
                    output.className = 'success';
                    output.innerHTML = `📊 Latest Analysis Results:\\n\\n${JSON.stringify(result, null, 2)}`;
                }
            } catch (error) {
                output.className = 'error';
                output.innerHTML = `❌ Error loading results: ${error.message}`;
            }
        }
        
        function clearOutput() {
            const output = document.getElementById('output');
            output.className = '';
            output.innerHTML = 'Output cleared. Ready for new operations...';
        }
        
        setInterval(async () => {
            try {
                const response = await fetch('/health');
                const result = await response.json();
                if (result.status !== 'healthy') {
                    console.warn('Health check failed:', result);
                }
            } catch (error) {
                console.warn('Health check error:', error);
            }
        }, 30000);
    </script>
</body>
</html>"""
    return html_content

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "Azure AI Image Analyzer",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def get_status():
    """Get system status"""
    try:
        # Check if config exists and load it
        config_exists = os.path.exists("config.json")
        config_info = {}
        
        if config_exists:
            try:
                with open("config.json", 'r') as f:
                    config = json.load(f)
                    config_info = {
                        "deployment_info_exists": "deployment_info" in config,
                        "containers_configured": "containers" in config,
                        "analysis_settings_configured": "analysis_settings" in config
                    }
            except Exception as e:
                config_info = {"config_read_error": str(e)}
        
        return {
            "status": "running",
            "container_info": {
                "credential_method": os.getenv("CREDENTIAL_METHOD", "unknown"),
                "key_vault_url_set": bool(os.getenv("KEY_VAULT_URL")),
                "port": os.getenv("PORT", "8000")
            },
            "configuration": {
                "config_file_exists": config_exists,
                **config_info
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Status check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.post("/analyze")
async def run_analysis():
    """Run the AI image analysis"""
    try:
        print("Starting analysis...")
        
        # Run the analyzer
        result = subprocess.run(
            ["python", "azure_ai_image_analyzer.py"], 
            capture_output=True, 
            text=True, 
            timeout=900  # 15 minute timeout
        )
        
        timestamp = datetime.now().isoformat()
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Image analysis completed successfully! Check Azure Blob Storage for detailed results.",
                "output": result.stdout[-2000:],  # Last 2000 chars
                "timestamp": timestamp,
                "exit_code": result.returncode
            }
        else:
            return {
                "status": "error", 
                "message": "Analysis process failed",
                "error": result.stderr[-1500:] if result.stderr else "No error details",
                "output": result.stdout[-1500:] if result.stdout else "No output",
                "timestamp": timestamp,
                "exit_code": result.returncode
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error", 
            "message": "Analysis timed out after 15 minutes",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Unexpected error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/results")
async def get_latest_results():
    """Get the latest analysis results"""
    try:
        # Look for result files
        result_files = glob.glob("image_analysis_results_*.json")
        
        if result_files:
            # Get the most recent file
            latest_file = max(result_files, key=os.path.getctime)
            
            try:
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    
                # Return a summary instead of the full data
                summary = {
                    "file": latest_file,
                    "analysis_metadata": data.get("analysis_metadata", {}),
                    "summary_statistics": data.get("summary_statistics", {}),
                    "sample_results": data.get("detailed_results", [])[:3],  # First 3 results
                    "total_detailed_results": len(data.get("detailed_results", [])),
                    "file_size_mb": round(os.path.getsize(latest_file) / (1024*1024), 2)
                }
                return summary
                
            except Exception as e:
                return {
                    "status": "error", 
                    "message": f"Error reading results file: {str(e)}"
                }
        else:
            return {
                "status": "no_results", 
                "message": "No analysis results found. Run an analysis first."
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Error searching for results: {str(e)}"
        }

@app.get("/api/info")
async def get_api_info():
    """Get API information"""
    return {
        "service": "Azure AI Image Analyzer",
        "version": "3.0.0",
        "endpoints": {
            "/": "Web interface",
            "/health": "Health check",
            "/status": "System status",
            "/analyze": "Run analysis (POST)",
            "/results": "Get latest results",
            "/api/info": "This endpoint"
        },
        "description": "Containerized Azure AI Vision image analysis service"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting Azure AI Image Analyzer Web Interface")
    print(f"🌐 Server will be available at: http://{host}:{port}")
    print(f"📊 Health check endpoint: http://{host}:{port}/health")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info"
    )