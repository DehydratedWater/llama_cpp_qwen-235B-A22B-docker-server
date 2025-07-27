#!/usr/bin/env python3
"""
Comprehensive concurrent test for llama.cpp server
Tests both short and long contexts with detailed performance metrics
"""

import asyncio
import aiohttp
import time
import json
import random
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResult:
    request_id: str
    context_type: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    analysis_time: float  # Time to first token
    inference_time: float  # Time for remaining tokens
    total_time: float
    tokens_per_second: float
    response_preview: str
    error: str = None

class ConcurrentTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        
    def generate_short_prompts(self, count: int) -> List[str]:
        """Generate varied short prompts to ensure different responses"""
        topics = [
            "machine learning", "quantum physics", "cooking recipes", "space exploration",
            "ancient history", "renewable energy", "artificial intelligence", "oceanography",
            "philosophy", "biotechnology", "music theory", "climate change"
        ]
        
        templates = [
            "Explain {topic} in simple terms.",
            "What are the latest developments in {topic}?",
            "Write a brief introduction to {topic}.",
            "Discuss the challenges in {topic}.",
            "How does {topic} impact society?",
            "Compare different approaches to {topic}."
        ]
        
        prompts = []
        for i in range(count):
            topic = random.choice(topics)
            template = random.choice(templates)
            # Add unique element to ensure different responses
            unique_aspect = f" Focus on aspect #{i+1}."
            prompts.append(template.format(topic=topic) + unique_aspect)
        
        return prompts
    
    def generate_context_length_prompt(self, target_tokens: int) -> str:
        """Generate a prompt with approximately target_tokens length"""
        base_text = """In the realm of artificial intelligence and machine learning, we are witnessing unprecedented advances in natural language processing, computer vision, and autonomous systems. These technologies are revolutionizing industries from healthcare and finance to transportation and entertainment. The development of large language models has particularly transformed how we interact with AI systems, enabling more natural and context-aware conversations. Meanwhile, computer vision algorithms are achieving human-level performance in image recognition tasks, enabling applications in medical diagnosis, autonomous vehicles, and security systems. The integration of these technologies is creating new possibilities for automation, decision-making, and human-AI collaboration across various domains."""
        
        # Repeat and expand text to reach target length
        words = base_text.split()
        current_text = base_text
        
        while len(current_text.split()) < target_tokens * 0.9:  # Account for tokenization differences
            # Add varied content to avoid repetition
            expansion = f" Furthermore, the implications of these advances extend to {random.choice(['healthcare', 'education', 'manufacturing', 'research', 'entertainment', 'communication'])} where {random.choice(['efficiency', 'accuracy', 'innovation', 'accessibility', 'scalability', 'reliability'])} improvements are particularly notable."
            current_text += expansion
        
        # Add a specific question at the end
        question = f"\n\nBased on this comprehensive overview, please analyze the key trends and provide your insights on the most promising developments. What are the potential challenges and opportunities ahead?"
        
        return current_text + question
    
    def generate_long_prompts(self, count: int) -> List[str]:
        """Generate varied long context prompts"""
        base_contexts = [
            """You are analyzing a complex software architecture document. The system consists of multiple microservices including user authentication, payment processing, inventory management, and notification services. Each service has its own database and communicates through REST APIs and message queues. The authentication service uses JWT tokens with refresh mechanisms. The payment service integrates with multiple providers including Stripe, PayPal, and bank transfers. The inventory service tracks products across multiple warehouses with real-time stock updates. The notification service handles email, SMS, and push notifications through various providers.""",
            
            """You are reviewing a scientific research paper on climate change mitigation strategies. The paper discusses carbon capture technologies, renewable energy integration, sustainable agriculture practices, and policy frameworks. It covers atmospheric carbon dioxide levels, greenhouse gas emissions from various sectors, the role of forests in carbon sequestration, ocean acidification effects, and international cooperation mechanisms. The research includes data from the past 50 years showing temperature trends, precipitation patterns, and extreme weather events.""",
            
            """You are examining a detailed financial analysis of a multinational corporation. The company operates in technology, healthcare, and renewable energy sectors across 30 countries. The analysis covers revenue streams, profit margins, market share, competitive positioning, regulatory compliance, and risk assessment. It includes quarterly earnings reports, balance sheets, cash flow statements, and forward-looking projections. The company has recently made several acquisitions and is planning an expansion into emerging markets."""
        ]
        
        prompts = []
        for i in range(count):
            base = random.choice(base_contexts)
            specific_question = f"""
            
Based on this context, please provide a detailed analysis addressing the following specific question #{i+1}:
- What are the key challenges and opportunities?
- How would you recommend improving the current situation?
- What metrics would you use to measure success?
- What are the potential risks and mitigation strategies?

Please provide a comprehensive response with specific examples and actionable recommendations.
"""
            prompts.append(base + specific_question)
        
        return prompts
    
    async def send_request(self, session: aiohttp.ClientSession, prompt: str, request_id: str, context_type: str) -> TestResult:
        """Send a single request and measure performance"""
        payload = {
            "prompt": prompt,
            "n_predict": 200,  # Limit tokens for consistent comparison
            "temperature": 0.7,
            "top_p": 0.80,
            "top_k": 20,
            "min_p": 0.00,
            "presence_penalty": 0.5,  # Reduce repetitions
            "stream": True
        }
        
        start_time = time.time()
        analysis_time = None
        tokens_received = 0
        response_text = ""
        
        try:
            async with session.post(f"{self.base_url}/completion", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return TestResult(
                        request_id=request_id,
                        context_type=context_type,
                        prompt_tokens=len(prompt.split()),
                        completion_tokens=0,
                        total_tokens=len(prompt.split()),
                        analysis_time=0,
                        inference_time=0,
                        total_time=time.time() - start_time,
                        tokens_per_second=0,
                        response_preview="",
                        error=f"HTTP {response.status}: {error_text}"
                    )
                
                async for line in response.content:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str == '[DONE]':
                                break
                            
                            try:
                                data = json.loads(data_str)
                                if 'content' in data:
                                    if analysis_time is None:
                                        analysis_time = time.time() - start_time
                                    
                                    tokens_received += 1
                                    response_text += data['content']
                            except json.JSONDecodeError:
                                continue
            
            end_time = time.time()
            total_time = end_time - start_time
            inference_time = total_time - (analysis_time or 0)
            
            return TestResult(
                request_id=request_id,
                context_type=context_type,
                prompt_tokens=len(prompt.split()),
                completion_tokens=tokens_received,
                total_tokens=len(prompt.split()) + tokens_received,
                analysis_time=analysis_time or 0,
                inference_time=inference_time,
                total_time=total_time,
                tokens_per_second=tokens_received / total_time if total_time > 0 else 0,
                response_preview=response_text[:100] + "..." if len(response_text) > 100 else response_text
            )
            
        except Exception as e:
            return TestResult(
                request_id=request_id,
                context_type=context_type,
                prompt_tokens=len(prompt.split()),
                completion_tokens=0,
                total_tokens=len(prompt.split()),
                analysis_time=0,
                inference_time=0,
                total_time=time.time() - start_time,
                tokens_per_second=0,
                response_preview="",
                error=str(e)
            )
    
    async def run_context_scaling_test(self):
        """Test individual requests with different context lengths"""
        context_sizes = [1000, 5000, 10000, 20000, 40000]  # Token counts
        
        print(f"📏 Starting context scaling test: {context_sizes} token contexts")
        print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
            for size in context_sizes:
                print(f"\n🔍 Testing {size:,} token context...")
                prompt = self.generate_context_length_prompt(size)
                
                start_time = time.time()
                result = await self.send_request(session, prompt, f"ctx_{size}", f"{size}k")
                test_time = time.time() - start_time
                
                if result.error:
                    print(f"   ❌ Failed: {result.error}")
                else:
                    print(f"   ✅ Success: {result.analysis_time:.3f}s analysis, {result.inference_time:.3f}s inference, {result.tokens_per_second:.1f} tok/s")
                
                self.results.append(result)
                
                # Wait between tests to avoid overwhelming
                if size != context_sizes[-1]:
                    await asyncio.sleep(2)
        
        print(f"\n📊 CONTEXT SCALING RESULTS:")
        print(f"{'Context':<10} {'Prompt Tokens':<12} {'Analysis':<10} {'Inference':<10} {'Total':<8} {'TPS':<6} {'Status'}")
        print(f"{'-'*70}")
        
        for result in self.results:
            status = "✅" if not result.error else "❌"
            print(f"{result.context_type:<10} {result.prompt_tokens:<12} "
                  f"{result.analysis_time:<10.3f} {result.inference_time:<10.3f} "
                  f"{result.total_time:<8.3f} {result.tokens_per_second:<6.1f} {status}")
    
    async def run_concurrent_test(self, short_requests: int = 3, long_requests: int = 2):
        """Run concurrent test with mixed short and long requests"""
        print(f"🚀 Starting concurrent test: {short_requests} short + {long_requests} long requests")
        print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Generate prompts
        short_prompts = self.generate_short_prompts(short_requests)
        long_prompts = self.generate_long_prompts(long_requests)
        
        # Create tasks
        tasks = []
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
            # Short context requests
            for i, prompt in enumerate(short_prompts):
                task = self.send_request(session, prompt, f"short_{i+1}", "short")
                tasks.append(task)
            
            # Long context requests
            for i, prompt in enumerate(long_prompts):
                task = self.send_request(session, prompt, f"long_{i+1}", "long")
                tasks.append(task)
            
            # Execute all requests concurrently
            print(f"⏳ Executing {len(tasks)} concurrent requests...")
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_test_time = time.time() - start_time
            
            # Process results
            for result in results:
                if isinstance(result, TestResult):
                    self.results.append(result)
                else:
                    print(f"❌ Exception: {result}")
        
        self.print_results(total_test_time)
    
    def print_results(self, total_test_time: float):
        """Print detailed performance analysis"""
        print(f"\n{'='*80}")
        print(f"🏁 CONCURRENT TEST RESULTS (Total Time: {total_test_time:.2f}s)")
        print(f"{'='*80}")
        
        # Separate results by context type
        short_results = [r for r in self.results if r.context_type == "short" and not r.error]
        long_results = [r for r in self.results if r.context_type == "long" and not r.error]
        errors = [r for r in self.results if r.error]
        
        # Print errors first
        if errors:
            print(f"\n❌ ERRORS ({len(errors)} requests):")
            for result in errors:
                print(f"   {result.request_id}: {result.error}")
        
        # Individual results
        print(f"\n📊 INDIVIDUAL RESULTS:")
        print(f"{'ID':<10} {'Type':<6} {'Analysis':<10} {'Inference':<10} {'Total':<8} {'TPS':<6} {'Preview':<50}")
        print(f"{'-'*100}")
        
        for result in self.results:
            if not result.error:
                print(f"{result.request_id:<10} {result.context_type:<6} "
                      f"{result.analysis_time:<10.3f} {result.inference_time:<10.3f} "
                      f"{result.total_time:<8.3f} {result.tokens_per_second:<6.1f} "
                      f"{result.response_preview:<50}")
        
        # Statistics
        if short_results:
            print(f"\n📈 SHORT CONTEXT STATS ({len(short_results)} requests):")
            self.print_stats(short_results)
        
        if long_results:
            print(f"\n📈 LONG CONTEXT STATS ({len(long_results)} requests):")
            self.print_stats(long_results)
        
        # Overall performance
        all_successful = short_results + long_results
        if all_successful:
            print(f"\n🎯 OVERALL PERFORMANCE:")
            print(f"   Successful requests: {len(all_successful)}/{len(self.results)}")
            print(f"   Average tokens/sec: {statistics.mean([r.tokens_per_second for r in all_successful]):.1f}")
            print(f"   Total throughput: {sum([r.completion_tokens for r in all_successful]) / total_test_time:.1f} tokens/sec")
            print(f"   Concurrent efficiency: {(len(all_successful) / total_test_time):.2f} requests/sec")
    
    def print_stats(self, results: List[TestResult]):
        """Print statistics for a group of results"""
        if not results:
            return
        
        analysis_times = [r.analysis_time for r in results]
        inference_times = [r.inference_time for r in results]
        total_times = [r.total_time for r in results]
        tps_values = [r.tokens_per_second for r in results]
        
        print(f"   Analysis time  - Min: {min(analysis_times):.3f}s, Max: {max(analysis_times):.3f}s, Avg: {statistics.mean(analysis_times):.3f}s")
        print(f"   Inference time - Min: {min(inference_times):.3f}s, Max: {max(inference_times):.3f}s, Avg: {statistics.mean(inference_times):.3f}s")
        print(f"   Total time     - Min: {min(total_times):.3f}s, Max: {max(total_times):.3f}s, Avg: {statistics.mean(total_times):.3f}s")
        print(f"   Tokens/sec     - Min: {min(tps_values):.1f}, Max: {max(tps_values):.1f}, Avg: {statistics.mean(tps_values):.1f}")

async def main():
    """Main test function"""
    import sys
    
    tester = ConcurrentTester()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "context":
        # Run context scaling test only
        await tester.run_context_scaling_test()
        return
    
    # Run context scaling test first
    print("🧪 PHASE 1: Context Scaling Test (Individual Requests)")
    print("=" * 60)
    await tester.run_context_scaling_test()
    tester.results.clear()
    
    print("\n⏸️  Waiting 15 seconds before concurrent tests...")
    await asyncio.sleep(15)
    
    # Then run concurrent tests
    print("\n🧪 PHASE 2: Concurrent Load Tests")
    print("=" * 60)
    
    test_configs = [
        (2, 1),  # 2 short, 1 long
        (3, 2),  # 3 short, 2 long  
        (4, 2),  # 4 short, 2 long (test parallel limit)
    ]
    
    for short_count, long_count in test_configs:
        print(f"\n🔄 Running test configuration: {short_count} short + {long_count} long")
        await tester.run_concurrent_test(short_count, long_count)
        tester.results.clear()  # Clear for next test
        
        if short_count + long_count < test_configs[-1][0] + test_configs[-1][1]:
            print("\n⏸️  Waiting 10 seconds before next test...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    print("🧪 llama.cpp Concurrent Performance Test")
    print("=" * 50)
    asyncio.run(main())