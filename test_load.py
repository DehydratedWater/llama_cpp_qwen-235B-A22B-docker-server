#!/usr/bin/env python3
"""
Load testing script for Qwen3-235B llama-server API
Tests server performance under sustained load
"""

import requests
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor
import argparse

# Server configuration
BASE_URL = "http://localhost:8080"
CHAT_URL = f"{BASE_URL}/v1/chat/completions"

class LoadTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.chat_url = f"{base_url}/v1/chat/completions"
        self.results = []
        self.lock = threading.Lock()
    
    def single_request(self, request_id, prompt, max_tokens=100):
        """Execute a single request and record metrics"""
        start_time = time.time()
        
        payload = {
            "model": "qwen3",
            "messages": [
                {"role": "user", "content": f"{prompt} (Request #{request_id})"}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False
        }
        
        try:
            response = requests.post(self.chat_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            usage = result.get('usage', {})
            
            metrics = {
                'id': request_id,
                'success': True,
                'response_time': elapsed,
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0),
                'content_length': len(content),
                'timestamp': start_time
            }
            
        except Exception as e:
            metrics = {
                'id': request_id,
                'success': False,
                'response_time': time.time() - start_time,
                'error': str(e),
                'timestamp': start_time
            }
        
        with self.lock:
            self.results.append(metrics)
        
        return metrics
    
    def run_load_test(self, num_requests, concurrent_users, prompt, max_tokens=100):
        """Run load test with specified parameters"""
        print(f"Starting load test:")
        print(f"  Requests: {num_requests}")
        print(f"  Concurrent Users: {concurrent_users}")
        print(f"  Prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
        print(f"  Max Tokens: {max_tokens}")
        print()
        
        self.results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for i in range(num_requests):
                future = executor.submit(self.single_request, i+1, prompt, max_tokens)
                futures.append(future)
                
                # Add small delay between request submissions to avoid overwhelming
                if i > 0 and i % concurrent_users == 0:
                    time.sleep(0.1)
            
            # Wait for all requests to complete
            completed = 0
            for future in futures:
                future.result()
                completed += 1
                if completed % 10 == 0 or completed == num_requests:
                    print(f"Completed: {completed}/{num_requests}")
        
        total_time = time.time() - start_time
        return self.analyze_results(total_time)
    
    def analyze_results(self, total_time):
        """Analyze test results and print statistics"""
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        print(f"\n=== Load Test Results ===")
        print(f"Total Requests: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Success Rate: {len(successful)/len(self.results)*100:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Requests/Second: {len(self.results)/total_time:.2f}")
        
        if successful:
            response_times = [r['response_time'] for r in successful]
            
            print(f"\nResponse Time Statistics:")
            print(f"  Average: {statistics.mean(response_times):.2f}s")
            print(f"  Median: {statistics.median(response_times):.2f}s")
            print(f"  Min: {min(response_times):.2f}s")
            print(f"  Max: {max(response_times):.2f}s")
            print(f"  95th percentile: {statistics.quantiles(response_times, n=20)[18]:.2f}s")
            print(f"  99th percentile: {statistics.quantiles(response_times, n=100)[98]:.2f}s")
            
            # Token statistics
            total_tokens = [r.get('total_tokens', 0) for r in successful if 'total_tokens' in r]
            if total_tokens:
                avg_tokens = statistics.mean(total_tokens)
                total_generated = sum(total_tokens)
                
                print(f"\nToken Statistics:")
                print(f"  Average tokens per response: {avg_tokens:.1f}")
                print(f"  Total tokens generated: {total_generated}")
                print(f"  Tokens per second: {total_generated/total_time:.1f}")
        
        if failed:
            print(f"\nFailure Analysis:")
            error_types = {}
            for failure in failed:
                error = failure.get('error', 'Unknown')
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in error_types.items():
                print(f"  {error}: {count}")
        
        return {
            'total_requests': len(self.results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful)/len(self.results)*100,
            'total_time': total_time,
            'requests_per_second': len(self.results)/total_time,
            'avg_response_time': statistics.mean(response_times) if successful else 0
        }

def main():
    parser = argparse.ArgumentParser(description='Load test Qwen3-235B server')
    parser.add_argument('--requests', '-r', type=int, default=50, help='Number of requests')
    parser.add_argument('--concurrent', '-c', type=int, default=5, help='Concurrent users')
    parser.add_argument('--tokens', '-t', type=int, default=100, help='Max tokens per response')
    parser.add_argument('--prompt', '-p', type=str, default='Explain quantum computing', help='Test prompt')
    
    args = parser.parse_args()
    
    tester = LoadTester()
    
    # Quick health check
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server health check failed")
            return
    except:
        print("❌ Cannot connect to server")
        return
    
    print("✅ Server is healthy")
    
    # Run the load test
    results = tester.run_load_test(
        num_requests=args.requests,
        concurrent_users=args.concurrent,
        prompt=args.prompt,
        max_tokens=args.tokens
    )
    
    # Performance assessment
    print(f"\n=== Performance Assessment ===")
    if results['success_rate'] >= 95:
        print("✅ Excellent reliability")
    elif results['success_rate'] >= 90:
        print("⚠️  Good reliability")
    else:
        print("❌ Poor reliability")
    
    if results['avg_response_time'] <= 2.0:
        print("✅ Excellent response time")
    elif results['avg_response_time'] <= 5.0:
        print("⚠️  Acceptable response time")
    else:
        print("❌ Slow response time")
    
    if results['requests_per_second'] >= 5:
        print("✅ Good throughput")
    elif results['requests_per_second'] >= 2:
        print("⚠️  Moderate throughput")
    else:
        print("❌ Low throughput")

if __name__ == "__main__":
    main()