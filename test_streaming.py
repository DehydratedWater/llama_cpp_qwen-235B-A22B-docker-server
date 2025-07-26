#!/usr/bin/env python3
"""
Streaming test script for Qwen3-235B llama-server API
Tests streaming responses and concurrent requests
"""

import json
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Server configuration
BASE_URL = "http://localhost:8080"
CHAT_URL = f"{BASE_URL}/v1/chat/completions"

def test_streaming_chat(prompt, max_tokens=200):
    """Test streaming chat completion"""
    payload = {
        "model": "qwen3",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True
    }
    
    try:
        response = requests.post(CHAT_URL, json=payload, stream=True, timeout=120)
        response.raise_for_status()
        
        tokens = []
        start_time = time.time()
        first_token_time = None
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    if data_str.strip() == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        delta = data.get('choices', [{}])[0].get('delta', {})
                        content = delta.get('content', '')
                        
                        if content and first_token_time is None:
                            first_token_time = time.time()
                        
                        if content:
                            tokens.append(content)
                            print(content, end='', flush=True)
                    except json.JSONDecodeError:
                        continue
        
        total_time = time.time() - start_time
        ttft = first_token_time - start_time if first_token_time else 0
        
        print()  # New line after streaming
        return {
            'tokens': len(tokens),
            'total_time': total_time,
            'ttft': ttft,
            'tokens_per_second': len(tokens) / total_time if total_time > 0 else 0
        }
        
    except Exception as e:
        print(f"Streaming error: {e}")
        return None

def concurrent_request(prompt_id):
    """Single request for concurrent testing"""
    prompt = f"Tell me an interesting fact about space. Request #{prompt_id}"
    start_time = time.time()
    
    payload = {
        "model": "qwen3",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response = requests.post(CHAT_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        elapsed = time.time() - start_time
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        return {
            'id': prompt_id,
            'success': True,
            'time': elapsed,
            'length': len(content)
        }
    except Exception as e:
        return {
            'id': prompt_id,
            'success': False,
            'error': str(e),
            'time': time.time() - start_time
        }

def test_concurrent_requests(num_requests=5):
    """Test concurrent requests"""
    print(f"Testing {num_requests} concurrent requests...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(concurrent_request, i+1) for i in range(num_requests)]
        results = [future.result() for future in futures]
    
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r['success'])
    
    print(f"Results: {successful}/{num_requests} successful")
    print(f"Total time: {total_time:.2f}s")
    
    if successful > 0:
        avg_time = sum(r['time'] for r in results if r['success']) / successful
        print(f"Average response time: {avg_time:.2f}s")
    
    return results

def main():
    print("=== Qwen3-235B Streaming Test Suite ===\n")
    
    # Test streaming responses
    streaming_tests = [
        {
            "name": "Short Story Generation",
            "prompt": "Write a short story about a robot learning to paint.",
            "max_tokens": 300
        },
        {
            "name": "Technical Explanation",
            "prompt": "Explain how neural networks work in simple terms.",
            "max_tokens": 250
        },
        {
            "name": "Code with Comments",
            "prompt": "Write a Python class for a simple calculator with detailed comments.",
            "max_tokens": 400
        }
    ]
    
    for i, test in enumerate(streaming_tests, 1):
        print(f"{i}. {test['name']}")
        print(f"Prompt: {test['prompt']}")
        print("Streaming response:")
        print("-" * 40)
        
        stats = test_streaming_chat(test['prompt'], test['max_tokens'])
        
        if stats:
            print(f"\nStats:")
            print(f"  Tokens: {stats['tokens']}")
            print(f"  Time to First Token: {stats['ttft']:.2f}s")
            print(f"  Total Time: {stats['total_time']:.2f}s")
            print(f"  Tokens/Second: {stats['tokens_per_second']:.2f}")
        else:
            print("❌ Streaming test failed")
        
        print("=" * 60)
    
    # Test concurrent requests
    print(f"{len(streaming_tests)+1}. Concurrent Request Test")
    concurrent_results = test_concurrent_requests(3)
    
    print("\nDetailed Results:")
    for result in concurrent_results:
        if result['success']:
            print(f"  Request {result['id']}: ✅ {result['time']:.2f}s ({result['length']} chars)")
        else:
            print(f"  Request {result['id']}: ❌ {result['error']}")
    
    print("\n=== Streaming Test Suite Complete ===")

if __name__ == "__main__":
    main()