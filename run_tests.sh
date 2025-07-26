#!/bin/bash

# Test runner script for Qwen3-235B Docker setup
# Runs comprehensive tests against the running model server

set -e

echo "=== Qwen3-235B Test Runner ==="
echo "Testing server at http://localhost:8080"
echo

# Check if server is running
echo "Checking server health..."
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "❌ Server is not running or not healthy"
    echo "Please start the server with: docker compose up"
    exit 1
fi
echo "✅ Server is healthy"
echo

# Check Python dependencies
echo "Checking Python dependencies..."
python3 -c "import requests" 2>/dev/null || {
    echo "❌ Missing 'requests' library"
    echo "Install with: pip install requests"
    exit 1
}
echo "✅ Dependencies satisfied"
echo

# Make test scripts executable
chmod +x test_basic.py test_streaming.py test_load.py

# Run basic functionality tests
echo "===================="
echo "1. BASIC TESTS"
echo "===================="
python3 test_basic.py
echo

# Run streaming tests
echo "===================="
echo "2. STREAMING TESTS"
echo "===================="
python3 test_streaming.py
echo

# Run light load test
echo "===================="
echo "3. LIGHT LOAD TEST"
echo "===================="
python3 test_load.py --requests 20 --concurrent 3 --tokens 50 --prompt "What is machine learning?"
echo

# Run moderate load test
echo "===================="
echo "4. MODERATE LOAD TEST"
echo "===================="
python3 test_load.py --requests 10 --concurrent 2 --tokens 150 --prompt "Write a short explanation of artificial intelligence"
echo

echo "=== All Tests Complete ==="
echo
echo "To run individual tests:"
echo "  python3 test_basic.py       # Basic functionality"
echo "  python3 test_streaming.py   # Streaming responses"
echo "  python3 test_load.py -h     # Load testing (see help for options)"
echo
echo "To run heavy load test:"
echo "  python3 test_load.py --requests 100 --concurrent 10"