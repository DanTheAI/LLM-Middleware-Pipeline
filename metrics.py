"""
Metrics collection and exporters for LLM Pipeline
"""
import time
import logging
import os
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger("llm_pipeline.metrics")

# Try to import prometheus client if available
try:
    import prometheus_client as prom
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info("Prometheus client not available. Metrics export disabled.")

class MetricsCollector:
    """Collect and export metrics for the LLM pipeline"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.metrics = {}
        
        # Initialize Prometheus metrics if available
        if self.enabled and PROMETHEUS_AVAILABLE:
            # Request counters
            self.metrics["requests_total"] = prom.Counter(
                'llm_pipeline_requests_total', 
                'Total number of requests processed'
            )
            self.metrics["success_total"] = prom.Counter(
                'llm_pipeline_success_total', 
                'Total number of successful requests'
            )
            self.metrics["failure_total"] = prom.Counter(
                'llm_pipeline_failure_total', 
                'Total number of failed requests'
            )
            
            # Token usage
            self.metrics["prompt_tokens_total"] = prom.Counter(
                'llm_pipeline_prompt_tokens_total', 
                'Total number of prompt tokens used'
            )
            self.metrics["completion_tokens_total"] = prom.Counter(
                'llm_pipeline_completion_tokens_total', 
                'Total number of completion tokens used'
            )
            self.metrics["total_tokens"] = prom.Counter(
                'llm_pipeline_total_tokens', 
                'Total number of tokens used'
            )
            
            # Latency histograms
            self.metrics["pipeline_latency"] = prom.Histogram(
                'llm_pipeline_latency_seconds', 
                'Time taken for complete pipeline execution',
                buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
            )
            self.metrics["inference_latency"] = prom.Histogram(
                'llm_inference_latency_seconds', 
                'Time taken for LLM inference only',
                buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
            )
    
    def record_request(self):
        """Record a request being processed"""
        if self.enabled and PROMETHEUS_AVAILABLE:
            self.metrics["requests_total"].inc()
    
    def record_success(self):
        """Record a successful request"""
        if self.enabled and PROMETHEUS_AVAILABLE:
            self.metrics["success_total"].inc()
    
    def record_failure(self):
        """Record a failed request"""
        if self.enabled and PROMETHEUS_AVAILABLE:
            self.metrics["failure_total"].inc()
    
    def record_token_usage(self, usage_data: Dict[str, int]):
        """Record token usage metrics"""
        if not self.enabled or not PROMETHEUS_AVAILABLE:
            return
            
        prompt_tokens = usage_data.get('prompt_tokens', 0)
        completion_tokens = usage_data.get('completion_tokens', 0)
        total_tokens = usage_data.get('total_tokens', 0)
        
        self.metrics["prompt_tokens_total"].inc(prompt_tokens)
        self.metrics["completion_tokens_total"].inc(completion_tokens)
        self.metrics["total_tokens"].inc(total_tokens)
        
        logger.info(f"Token usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
    
    def time_pipeline(self, start_time: float):
        """Record pipeline execution time"""
        if self.enabled and PROMETHEUS_AVAILABLE:
            execution_time = time.time() - start_time
            self.metrics["pipeline_latency"].observe(execution_time)
            return execution_time
        return None
    
    def time_inference(self, start_time: float):
        """Record inference execution time"""
        if self.enabled and PROMETHEUS_AVAILABLE:
            execution_time = time.time() - start_time
            self.metrics["inference_latency"].observe(execution_time)
            return execution_time
        return None
    
    def start_http_server(self, port: int = 8000):
        """Start a Prometheus HTTP metrics server"""
        if self.enabled and PROMETHEUS_AVAILABLE:
            try:
                prom.start_http_server(port)
                logger.info(f"Prometheus metrics server started on port {port}")
            except Exception as e:
                logger.error(f"Failed to start Prometheus metrics server: {e}")
