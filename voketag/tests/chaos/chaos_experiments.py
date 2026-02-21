"""
Chaos Engineering experiments for VokeTag platform.

LOW ENHANCEMENT: Proactive resilience testing.

Tests system behavior under failure conditions:
- Service failures
- Network issues
- Database failures
- Cache failures
- High latency
"""
import os
import time
import random
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class ChaosExperiment:
    """Base class for chaos experiments."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: List[Dict] = []
    
    def run(self):
        """Run the chaos experiment."""
        print(f"\n🔥 Starting experiment: {self.name}")
        print(f"📝 Description: {self.description}")
        
        self.start_time = datetime.now()
        
        try:
            # Baseline (before chaos)
            print("📊 Measuring baseline...")
            baseline = self.measure_baseline()
            
            # Inject chaos
            print("💥 Injecting chaos...")
            self.inject_chaos()
            
            # Observe impact
            print("👀 Observing system behavior...")
            impact = self.observe_impact()
            
            # Recovery
            print("🔧 Cleaning up...")
            self.cleanup()
            
            # Post-chaos
            print("📊 Measuring recovery...")
            recovery = self.measure_recovery()
            
            self.end_time = datetime.now()
            
            # Analyze results
            self.analyze_results(baseline, impact, recovery)
            
            print(f"✅ Experiment completed successfully")
            
        except Exception as e:
            print(f"❌ Experiment failed: {e}")
            self.cleanup()
            raise
    
    def measure_baseline(self) -> Dict:
        """Measure baseline metrics."""
        raise NotImplementedError
    
    def inject_chaos(self):
        """Inject chaos into the system."""
        raise NotImplementedError
    
    def observe_impact(self) -> Dict:
        """Observe the impact of chaos."""
        raise NotImplementedError
    
    def cleanup(self):
        """Clean up after the experiment."""
        raise NotImplementedError
    
    def measure_recovery(self) -> Dict:
        """Measure recovery metrics."""
        raise NotImplementedError
    
    def analyze_results(self, baseline: Dict, impact: Dict, recovery: Dict):
        """Analyze experiment results."""
        print("\n📊 RESULTS:")
        print(f"  Baseline: {baseline}")
        print(f"  Impact: {impact}")
        print(f"  Recovery: {recovery}")


class RedisFailureExperiment(ChaosExperiment):
    """Test system behavior when Redis fails."""
    
    def __init__(self, service_url: str):
        super().__init__(
            name="Redis Failure",
            description="Simulate Redis unavailability to test cache fallback"
        )
        self.service_url = service_url
        self.redis_container = "voketag-redis"
    
    def measure_baseline(self) -> Dict:
        """Measure baseline with Redis healthy."""
        response_times = []
        error_count = 0
        
        for _ in range(10):
            try:
                start = time.time()
                response = requests.get(f"{self.service_url}/v1/scan/550e8400-e29b-41d4-a716-446655440000")
                duration = time.time() - start
                
                response_times.append(duration)
                
                if response.status_code != 200:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
        
        return {
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'error_rate': error_count / 10,
            'cache_available': True,
        }
    
    def inject_chaos(self):
        """Stop Redis container."""
        os.system(f"docker stop {self.redis_container}")
        time.sleep(5)  # Wait for circuit breaker to open
    
    def observe_impact(self) -> Dict:
        """Observe system behavior without Redis."""
        response_times = []
        error_count = 0
        fallback_count = 0
        
        for _ in range(10):
            try:
                start = time.time()
                response = requests.get(f"{self.service_url}/v1/scan/550e8400-e29b-41d4-a716-446655440000")
                duration = time.time() - start
                
                response_times.append(duration)
                
                if response.status_code == 200:
                    # Successfully fell back to database
                    fallback_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
            
            time.sleep(1)
        
        return {
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'error_rate': error_count / 10,
            'fallback_success_rate': fallback_count / 10,
            'cache_available': False,
        }
    
    def cleanup(self):
        """Restart Redis container."""
        os.system(f"docker start {self.redis_container}")
        time.sleep(10)  # Wait for Redis to be ready
    
    def measure_recovery(self) -> Dict:
        """Measure recovery after Redis is restored."""
        time.sleep(30)  # Wait for circuit breaker to close
        
        response_times = []
        error_count = 0
        
        for _ in range(10):
            try:
                start = time.time()
                response = requests.get(f"{self.service_url}/v1/scan/550e8400-e29b-41d4-a716-446655440000")
                duration = time.time() - start
                
                response_times.append(duration)
                
                if response.status_code != 200:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
            
            time.sleep(1)
        
        return {
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'error_rate': error_count / 10,
            'cache_available': True,
        }
    
    def analyze_results(self, baseline: Dict, impact: Dict, recovery: Dict):
        """Analyze Redis failure experiment."""
        print("\n📊 REDIS FAILURE EXPERIMENT RESULTS:")
        print(f"  Baseline response time: {baseline['avg_response_time']:.3f}s")
        print(f"  Impact response time: {impact['avg_response_time']:.3f}s")
        print(f"  Recovery response time: {recovery['avg_response_time']:.3f}s")
        print(f"  Fallback success rate: {impact['fallback_success_rate']:.0%}")
        
        # Hypothesis validation
        print("\n✅ HYPOTHESIS VALIDATION:")
        
        # Should fall back to database
        if impact['fallback_success_rate'] > 0.8:
            print("  ✅ PASS: System successfully falls back to database")
        else:
            print("  ❌ FAIL: Fallback mechanism not working properly")
        
        # Should recover within 30s
        if recovery['error_rate'] < 0.1:
            print("  ✅ PASS: System recovered after Redis restoration")
        else:
            print("  ❌ FAIL: System did not recover properly")
        
        # Latency should increase but stay reasonable
        if impact['avg_response_time'] < baseline['avg_response_time'] * 5:
            print("  ✅ PASS: Latency degradation is acceptable")
        else:
            print("  ⚠️  WARN: Latency degraded significantly")


class NetworkLatencyExperiment(ChaosExperiment):
    """Test system behavior under high network latency."""
    
    def __init__(self, service_url: str):
        super().__init__(
            name="Network Latency",
            description="Inject network latency to test timeout handling"
        )
        self.service_url = service_url
        self.interface = "eth0"
    
    def measure_baseline(self) -> Dict:
        """Measure baseline latency."""
        latencies = []
        
        for _ in range(5):
            start = time.time()
            try:
                requests.get(f"{self.service_url}/v1/health", timeout=5)
                latencies.append(time.time() - start)
            except:
                pass
        
        return {
            'avg_latency': sum(latencies) / len(latencies) if latencies else 0,
        }
    
    def inject_chaos(self):
        """Add 500ms latency using tc (traffic control)."""
        os.system(f"sudo tc qdisc add dev {self.interface} root netem delay 500ms")
    
    def observe_impact(self) -> Dict:
        """Observe behavior under latency."""
        latencies = []
        timeouts = 0
        
        for _ in range(5):
            start = time.time()
            try:
                requests.get(f"{self.service_url}/v1/health", timeout=2)
                latencies.append(time.time() - start)
            except requests.exceptions.Timeout:
                timeouts += 1
        
        return {
            'avg_latency': sum(latencies) / len(latencies) if latencies else 0,
            'timeout_rate': timeouts / 5,
        }
    
    def cleanup(self):
        """Remove latency."""
        os.system(f"sudo tc qdisc del dev {self.interface} root")
    
    def measure_recovery(self) -> Dict:
        """Measure recovery latency."""
        time.sleep(5)
        return self.measure_baseline()
    
    def analyze_results(self, baseline: Dict, impact: Dict, recovery: Dict):
        """Analyze latency experiment."""
        print("\n📊 NETWORK LATENCY EXPERIMENT RESULTS:")
        print(f"  Baseline latency: {baseline['avg_latency']:.3f}s")
        print(f"  Impact latency: {impact['avg_latency']:.3f}s")
        print(f"  Timeout rate: {impact['timeout_rate']:.0%}")
        
        # Hypothesis: Timeouts should be handled gracefully
        if impact['timeout_rate'] < 1.0:
            print("  ✅ PASS: Some requests completed despite latency")
        else:
            print("  ⚠️  WARN: All requests timed out")


class DatabaseFailureExperiment(ChaosExperiment):
    """Test system behavior when database fails."""
    
    def __init__(self, service_url: str):
        super().__init__(
            name="Database Failure",
            description="Simulate database unavailability to test error handling"
        )
        self.service_url = service_url
        self.db_container = "voketag-postgres"
    
    def measure_baseline(self) -> Dict:
        """Measure baseline with database healthy."""
        success_count = 0
        
        for _ in range(5):
            try:
                response = requests.get(f"{self.service_url}/v1/scan/550e8400-e29b-41d4-a716-446655440000")
                if response.status_code == 200:
                    success_count += 1
            except:
                pass
            
            time.sleep(1)
        
        return {'success_rate': success_count / 5}
    
    def inject_chaos(self):
        """Stop database container."""
        os.system(f"docker stop {self.db_container}")
        time.sleep(5)
    
    def observe_impact(self) -> Dict:
        """Observe behavior without database."""
        error_500_count = 0
        error_503_count = 0
        
        for _ in range(5):
            try:
                response = requests.get(f"{self.service_url}/v1/scan/550e8400-e29b-41d4-a716-446655440000")
                
                if response.status_code == 500:
                    error_500_count += 1
                elif response.status_code == 503:
                    error_503_count += 1
                    
            except:
                error_503_count += 1
            
            time.sleep(1)
        
        return {
            'error_500_rate': error_500_count / 5,
            'error_503_rate': error_503_count / 5,
        }
    
    def cleanup(self):
        """Restart database container."""
        os.system(f"docker start {self.db_container}")
        time.sleep(15)  # Wait for database to be ready
    
    def measure_recovery(self) -> Dict:
        """Measure recovery."""
        time.sleep(10)
        return self.measure_baseline()
    
    def analyze_results(self, baseline: Dict, impact: Dict, recovery: Dict):
        """Analyze database failure experiment."""
        print("\n📊 DATABASE FAILURE EXPERIMENT RESULTS:")
        print(f"  Baseline success rate: {baseline['success_rate']:.0%}")
        print(f"  Impact 500 error rate: {impact['error_500_rate']:.0%}")
        print(f"  Impact 503 error rate: {impact['error_503_rate']:.0%}")
        print(f"  Recovery success rate: {recovery['success_rate']:.0%}")
        
        # Hypothesis: Should return 503 (not 500)
        if impact['error_503_rate'] > 0.5:
            print("  ✅ PASS: Circuit breaker returning 503 Service Unavailable")
        else:
            print("  ⚠️  WARN: Not handling database failure gracefully")


# Main execution
if __name__ == "__main__":
    SERVICE_URL = os.getenv("SERVICE_URL", "http://localhost:8080")
    
    print("🔥 CHAOS ENGINEERING EXPERIMENTS")
    print(f"🎯 Target: {SERVICE_URL}")
    print("=" * 60)
    
    # Run experiments
    experiments = [
        RedisFailureExperiment(SERVICE_URL),
        # NetworkLatencyExperiment(SERVICE_URL),  # Requires root
        # DatabaseFailureExperiment(SERVICE_URL),
    ]
    
    for experiment in experiments:
        try:
            experiment.run()
        except Exception as e:
            print(f"❌ Experiment failed: {e}")
        
        print("\n" + "=" * 60)
        time.sleep(10)  # Cool down between experiments
    
    print("\n✅ All chaos experiments completed!")
