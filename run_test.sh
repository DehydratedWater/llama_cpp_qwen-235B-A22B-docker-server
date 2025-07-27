#!/bin/bash

echo "🧪 Starting llama.cpp Concurrent Performance Test"
echo "=================================================="

# Check if server is running
echo "🔍 Checking if llama-server is running..."
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "❌ Server not responding at http://localhost:8080"
    echo "💡 Start the server with: docker-compose up -d"
    exit 1
fi

echo "✅ Server is running!"

# Install dependencies if needed
if ! python3 -c "import aiohttp" 2>/dev/null; then
    echo "📦 Installing required Python packages..."
    pip3 install aiohttp
fi

# Run the test
echo "🚀 Running concurrent test..."
python3 concurrent_test.py

echo "✅ Test completed!"