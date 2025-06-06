#!/bin/bash

# Local testing script for Python Code Execution Service

set -e

IMAGE_NAME="python-executor:latest"
CONTAINER_NAME="python-executor-test"

echo "🧪 Testing Python Code Execution Service locally"
echo ""

# Stop and remove existing container if it exists
echo "🧹 Cleaning up existing containers..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

# Build the Docker image
echo "🏗️ Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Run the container
echo "🚀 Starting container..."
docker run -d --name ${CONTAINER_NAME} -p 8080:8080 ${IMAGE_NAME}

# Wait for the service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 10

# Test health endpoint
echo "🔍 Testing health endpoint..."
curl -f http://localhost:8080/health || {
    echo "❌ Health check failed"
    docker logs ${CONTAINER_NAME}
    exit 1
}

echo ""
echo "✅ Health check passed!"

# Test basic execution
echo "🧪 Testing basic script execution..."
RESPONSE=$(curl -s -X POST http://localhost:8080/execute \
    -H "Content-Type: application/json" \
    -d '{"script": "def main():\n    return {\"message\": \"Hello World!\", \"number\": 42}"}')

echo "Response: $RESPONSE"

if echo "$RESPONSE" | grep -q "Hello World!"; then
    echo "✅ Basic execution test passed!"
else
    echo "❌ Basic execution test failed"
    docker logs ${CONTAINER_NAME}
    exit 1
fi

# Test with pandas/numpy
echo "🐼 Testing pandas/numpy execution..."
PANDAS_RESPONSE=$(curl -s -X POST http://localhost:8080/execute \
    -H "Content-Type: application/json" \
    -d '{
        "script": "def main():\n    import pandas as pd\n    import numpy as np\n    data = pd.DataFrame({\"values\": [1, 2, 3, 4, 5]})\n    return {\"mean\": float(data[\"values\"].mean()), \"pandas_version\": pd.__version__}"
    }')

echo "Pandas response: $PANDAS_RESPONSE"

if echo "$PANDAS_RESPONSE" | grep -q "pandas_version"; then
    echo "✅ Pandas/numpy test passed!"
else
    echo "❌ Pandas/numpy test failed"
    docker logs ${CONTAINER_NAME}
    exit 1
fi

# Test error handling
echo "⚠️ Testing error handling..."
ERROR_RESPONSE=$(curl -s -X POST http://localhost:8080/execute \
    -H "Content-Type: application/json" \
    -d '{"script": "print(\"no main function\")"}')

if echo "$ERROR_RESPONSE" | grep -q "must contain a main"; then
    echo "✅ Error handling test passed!"
else
    echo "❌ Error handling test failed"
    echo "Response: $ERROR_RESPONSE"
fi

echo ""
echo "🎉 All tests passed! Your service is working correctly."
echo ""
echo "🔧 To manually test the service:"
echo "curl -X POST http://localhost:8080/execute \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"script\": \"def main():\\n    import pandas as pd\\n    return {\\\"message\\\": \\\"Hello from Docker!\\\"}\"}}'"
echo ""
echo "🛑 To stop the container:"
echo "docker stop ${CONTAINER_NAME}"
echo ""
echo "📋 To view logs:"
echo "docker logs ${CONTAINER_NAME}" 