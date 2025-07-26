#!/usr/bin/env python3
"""
Basic test script for Qwen3-235B llama-server API
Tests basic functionality and response quality
"""

import json
import requests
import time
import sys

# Server configuration
BASE_URL = "http://localhost:8080"
HEALTH_URL = f"{BASE_URL}/health"
CHAT_URL = f"{BASE_URL}/v1/chat/completions"
COMPLETION_URL = f"{BASE_URL}/completion"

def check_health():
    """Check if the server is healthy"""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

def test_chat_completion(prompt, max_tokens=100):
    """Test chat completion endpoint"""
    payload = {
        "model": "qwen3",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response = requests.post(CHAT_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Chat completion error: {e}")
        return None

def test_completion(prompt, max_tokens=100):
    """Test raw completion endpoint"""
    payload = {
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response = requests.post(COMPLETION_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Completion error: {e}")
        return None

def main():
    print("=== Qwen3-235B Test Suite ===\n")
    
    # Check server health
    print("1. Checking server health...")
    if not check_health():
        print("❌ Server is not healthy. Make sure the Docker container is running.")
        sys.exit(1)
    print("✅ Server is healthy\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Simple Question",
            "prompt": "What is the capital of France?",
            "max_tokens": 50
        },
        {
            "name": "Math Problem",
            "prompt": "Solve: 2x + 5 = 17. Show your work.",
            "max_tokens": 100
        },
        {
            "name": "Creative Writing",
            "prompt": "Write a short poem about artificial intelligence.",
            "max_tokens": 150
        },
        {
            "name": "Code Generation",
            "prompt": "Write a Python function to calculate the factorial of a number.",
            "max_tokens": 200
        }
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i+1}. Testing: {test_case['name']}")
        print(f"Prompt: {test_case['prompt']}")
        
        start_time = time.time()
        
        # Test chat completion
        result = test_chat_completion(test_case['prompt'], test_case['max_tokens'])
        
        if result:
            elapsed = time.time() - start_time
            content = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
            
            print(f"✅ Response received in {elapsed:.2f}s")
            print(f"Response: {content[:200]}{'...' if len(content) > 200 else ''}")
            print(f"Usage: {result.get('usage', {})}")
        else:
            print("❌ Failed to get response")
        
        print("-" * 60)
    
    # Performance test
    print(f"{len(test_cases)+2}. Performance Test (10 quick requests)")
    start_time = time.time()
    successful_requests = 0
    
    for i in range(10):
        result = test_chat_completion("Count from 1 to 5.", 20)
        if result:
            successful_requests += 1
    
    total_time = time.time() - start_time
    print(f"✅ {successful_requests}/10 requests successful")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per request: {total_time/10:.2f}s")
    
    print("\n=== Test Suite Complete ===")

if __name__ == "__main__":
    main()