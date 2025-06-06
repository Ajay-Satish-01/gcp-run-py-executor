# Python Code Execution Service

A secure API service that executes arbitrary Python scripts in a sandboxed environment using nsjail. The service accepts Python scripts via REST API and returns the execution results safely.

## Features

- 🔒 **Secure Execution**: Uses nsjail for sandboxing user scripts
- 🐍 **Python Support**: Supports Python 3.11 with common libraries (pandas, numpy, os)
- 🚀 **Fast & Lightweight**: Optimized Docker image for quick deployments
- 📊 **Structured Response**: Separates main() function results from stdout
- ✅ **Input Validation**: Basic validation and error handling
- 🏥 **Health Checks**: Built-in health monitoring

## Quick Start

### Local Development

1. **Build and run with Docker:**

```bash
docker build -t python-executor .
docker run -p 8080:8080 python-executor
```

2. **Test the service:**

```bash
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    import pandas as pd\n    return {\"message\": \"Hello World!\", \"data\": [1, 2, 3]}"
  }'
```

## API Documentation

### Execute Python Script

**Endpoint:** `POST /execute`

**Request Body:**

```json
{
  "script": "def main():\n    return {'result': 'your_data'}"
}
```

**Response:**

```json
{
  "result": {
    "result": "your_data"
  },
  "stdout": ""
}
```

**Requirements:**

- Script must contain a `main()` function
- The `main()` function must return JSON-serializable data
- Script size limited to 50KB
- Execution timeout: 30 seconds

### Health Check

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy"
}
```

## Example Usage

### Basic Example

```bash
curl -X POST https://YOUR_CLOUD_RUN_URL/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    return {\"message\": \"Hello from the cloud!\"}"
  }'
```

### Data Processing Example

```bash
curl -X POST https://YOUR_CLOUD_RUN_URL/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    import pandas as pd\n    import numpy as np\n    \n    # Create sample data\n    data = pd.DataFrame({\"values\": [1, 2, 3, 4, 5]})\n    mean_val = data[\"values\"].mean()\n    \n    print(\"Processing data...\")\n    \n    return {\n        \"mean\": mean_val,\n        \"count\": len(data),\n        \"data_type\": \"pandas_dataframe\"\n    }"
  }'
```

### File System Example

```bash
curl -X POST https://YOUR_CLOUD_RUN_URL/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    import os\n    \n    # Safe file operations\n    current_dir = os.getcwd()\n    files = os.listdir(\".\")\n    \n    print(f\"Current directory: {current_dir}\")\n    \n    return {\n        \"directory\": current_dir,\n        \"file_count\": len(files),\n        \"available_files\": files\n    }"
  }'
```

## Security Features

- **Sandboxing**: All scripts run in nsjail containers with restricted permissions
- **Resource Limits**: CPU, memory, and execution time limits
- **Network Isolation**: No network access for executed scripts
- **File System Restrictions**: Limited file system access
- **User Isolation**: Scripts run as unprivileged user

## Available Libraries

The following Python libraries are pre-installed and available for use:

- `os` - Operating system interface
- `pandas` - Data manipulation and analysis
- `numpy` - Numerical computing
- `json` - JSON encoder and decoder
- `sys` - System-specific parameters and functions
- `io` - Core tools for working with streams

## Error Handling

The service provides detailed error messages for common issues:

- **400 Bad Request**: Invalid input, missing main() function, or validation errors
- **500 Internal Server Error**: Script execution failures or runtime errors

Example error response:

```json
{
  "error": "Validation error: Script must contain a main() function"
}
```

## Deployment

### Google Cloud Run

1. **Build and push to Google Container Registry:**

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and tag
docker build -t gcr.io/YOUR_PROJECT_ID/python-executor .
docker push gcr.io/YOUR_PROJECT_ID/python-executor
```

2. **Deploy to Cloud Run:**

```bash
gcloud run deploy python-executor \
  --image gcr.io/YOUR_PROJECT_ID/python-executor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 60s \
  --max-instances 10
```

3. **Get the service URL:**

```bash
gcloud run services describe python-executor \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

## Live Service URL


```bash
curl -X POST https://gcp-run-py-executor-XXXXXXX.us-XXX.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    import pandas as pd\n    import numpy as np\n    \n    print(\"Executing on Google Cloud Run!\")\n    \n    data = np.array([1, 2, 3, 4, 5])\n    result = {\n        \"platform\": \"Google Cloud Run\",\n        \"sum\": int(np.sum(data)),\n        \"mean\": float(np.mean(data)),\n        \"library_versions\": {\n            \"pandas\": pd.__version__,\n            \"numpy\": np.__version__\n        }\n    }\n    return result"
  }'
```

## Development

### Local Testing

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test execution with simple script
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    return {\"status\": \"working\"}"}'
```

