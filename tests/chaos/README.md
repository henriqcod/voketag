# Chaos Engineering

## Overview

Proactive resilience testing for VokeTag platform using chaos engineering principles.

**LOW ENHANCEMENT**: Validate system behavior under failure conditions.

## Philosophy

> "Chaos Engineering is the discipline of experimenting on a system to build confidence in the system's capability to withstand turbulent conditions in production."
> — Principles of Chaos Engineering

### Goals
- ✅ **Discover weaknesses** before they cause outages
- ✅ **Validate resilience mechanisms** (circuit breakers, fallbacks)
- ✅ **Build confidence** in production deployments
- ✅ **Improve incident response** through practice

## Experiments

### 1. Redis Failure (`chaos_experiments.py`)

**Hypothesis**: When Redis fails, the system should:
- ✅ Fall back to PostgreSQL database
- ✅ Continue serving requests (with higher latency)
- ✅ Return 200 OK (not 500 errors)
- ✅ Recover automatically when Redis is restored

**Test**:
1. Measure baseline (Redis healthy)
2. Stop Redis container
3. Observe fallback behavior
4. Restart Redis
5. Measure recovery

**Expected Results**:
- Fallback success rate: >80%
- Error rate: <10%
- Latency increase: <5x
- Recovery time: <30 seconds

### 2. Database Failure

**Hypothesis**: When PostgreSQL fails, the system should:
- ✅ Return 503 Service Unavailable (not 500)
- ✅ Circuit breaker opens after threshold
- ✅ Fail fast (no long timeouts)
- ✅ Recover when database is restored

### 3. Network Latency

**Hypothesis**: Under high network latency, the system should:
- ✅ Handle timeouts gracefully
- ✅ Not block indefinitely
- ✅ Return appropriate error codes
- ✅ Maintain stability

### 4. Pod Failure (Kubernetes)

**Hypothesis**: When a pod fails, the system should:
- ✅ Route traffic to healthy pods
- ✅ Zero downtime (with 2+ replicas)
- ✅ Restart failed pod automatically
- ✅ Re-balance traffic

### 5. High CPU Usage

**Hypothesis**: Under high CPU load, the system should:
- ✅ Maintain acceptable latency
- ✅ Not crash or OOM
- ✅ Autoscale (if configured)
- ✅ Prioritize critical requests

## Running Experiments

### Prerequisites

```bash
# Install Python dependencies
pip install requests

# Ensure Docker is running
docker ps

# Ensure services are running
docker-compose up -d
```

### Basic Run

```bash
# Run all experiments
python tests/chaos/chaos_experiments.py

# Set service URL
SERVICE_URL=http://staging.voketag.com python tests/chaos/chaos_experiments.py
```

### Individual Experiments

```python
from chaos_experiments import RedisFailureExperiment

experiment = RedisFailureExperiment("http://localhost:8080")
experiment.run()
```

### Advanced: Litmus Chaos (Kubernetes)

For production Kubernetes clusters, use Litmus Chaos:

```bash
# Install Litmus
kubectl apply -f https://litmuschaos.github.io/litmus/litmus-operator-v2.0.0.yaml

# Create chaos experiment
kubectl apply -f tests/chaos/k8s/redis-pod-delete.yaml

# Monitor experiment
kubectl get chaosengine -n voketag
```

## Safety Guidelines

### ⚠️ CRITICAL: Do NOT Run in Production (Initially)

1. **Start with staging/test environments**
2. **Run during business hours** (not midnight)
3. **Have team on standby** to respond
4. **Start with smallest blast radius** (single pod)
5. **Gradually increase scope** as confidence grows

### Rollout Strategy

**Week 1-2**: Development environment only  
**Week 3-4**: Staging environment  
**Week 5-6**: Production (single pod, 5% traffic)  
**Week 7+**: Production (gradually increase scope)

### Emergency Stop

If experiment causes issues:

```bash
# Stop all containers
docker-compose down

# Or stop specific container
docker stop voketag-redis

# Restart services
docker-compose up -d
```

## Monitoring During Experiments

### Key Metrics to Watch

1. **Error Rate**: Should stay <1%
2. **Latency**: P95 should stay <500ms
3. **Throughput**: Should not drop >20%
4. **CPU/Memory**: Should not spike >80%
5. **Circuit Breaker State**: Should open/close correctly

### Dashboard

Create a Grafana dashboard to monitor:
- Request success rate
- Response time (P50, P95, P99)
- Circuit breaker state
- Cache hit ratio
- Database connections

### Alerts

Set up alerts before running experiments:
- High error rate (>5%)
- High latency (P95 >1s)
- Circuit breaker open
- Database connection pool exhausted

## Experiment Template

```python
class MyExperiment(ChaosExperiment):
    def __init__(self, service_url: str):
        super().__init__(
            name="My Experiment",
            description="Test X under Y conditions"
        )
        self.service_url = service_url
    
    def measure_baseline(self) -> Dict:
        # Measure normal behavior
        pass
    
    def inject_chaos(self):
        # Inject failure
        pass
    
    def observe_impact(self) -> Dict:
        # Observe system behavior
        pass
    
    def cleanup(self):
        # Restore system
        pass
    
    def measure_recovery(self) -> Dict:
        # Measure recovery
        pass
    
    def analyze_results(self, baseline, impact, recovery):
        # Analyze and report
        pass
```

## CI/CD Integration

### GitHub Actions (Weekly)

```yaml
name: Chaos Engineering

on:
  schedule:
    - cron: '0 10 * * 3' # Wednesday 10 AM
  workflow_dispatch:

jobs:
  chaos:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Run chaos experiments
        run: |
          python tests/chaos/chaos_experiments.py
        env:
          SERVICE_URL: ${{ secrets.STAGING_URL }}
      
      - name: Notify team
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "❌ Chaos experiment failed!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "Chaos experiment failed. Review system resilience."
                  }
                }
              ]
            }
```

## Results Analysis

### Successful Experiment

```
📊 REDIS FAILURE EXPERIMENT RESULTS:
  Baseline response time: 0.085s
  Impact response time: 0.250s
  Recovery response time: 0.090s
  Fallback success rate: 95%

✅ HYPOTHESIS VALIDATION:
  ✅ PASS: System successfully falls back to database
  ✅ PASS: System recovered after Redis restoration
  ✅ PASS: Latency degradation is acceptable
```

### Failed Experiment

```
📊 REDIS FAILURE EXPERIMENT RESULTS:
  Baseline response time: 0.085s
  Impact response time: timeout
  Fallback success rate: 0%

❌ HYPOTHESIS VALIDATION:
  ❌ FAIL: Fallback mechanism not working properly
  ❌ FAIL: System did not recover properly
```

**Action Items**:
1. Review circuit breaker configuration
2. Check database connection pooling
3. Verify fallback logic in code
4. Add more logging for debugging

## Best Practices

### 1. Define Clear Hypotheses
✅ "When Redis fails, system falls back to database"  
❌ "Let's see what happens when Redis fails"

### 2. Start Small
✅ Single pod, 5% traffic  
❌ All pods, 100% traffic

### 3. Measure Everything
- Baseline metrics
- Impact metrics
- Recovery metrics

### 4. Automate Cleanup
Always implement `cleanup()` method to restore system.

### 5. Document Findings
Record what you learned from each experiment.

### 6. Iterate
Improve resilience based on findings, then re-test.

## Advanced Experiments

### Game Days

Quarterly "game day" exercises:
1. **Red Team**: Introduces chaos
2. **Blue Team**: Responds to incidents
3. **Observers**: Document learnings

### Multi-Service Failures

Test cascading failures:
1. Redis + Database fail simultaneously
2. Network partition between services
3. Multiple pods fail at once

### Real-World Scenarios

Simulate actual production incidents:
1. AWS region outage
2. DDoS attack
3. Deployment gone wrong
4. Configuration error

## Cost

**Infrastructure**: $0 (uses existing staging)  
**Time**: 30-60 minutes per experiment  
**Maintenance**: 2-4 hours/month

## ROI

**Prevents outages**: Early detection = $10,000+ saved per incident  
**Faster recovery**: Practice = 50% faster incident response  
**Confidence**: Sleep better knowing systems are resilient

---

**Estimated Effort**: 4-6 hours (initial setup) + 1 hour per new experiment  
**Priority**: MEDIUM (important but not urgent)
