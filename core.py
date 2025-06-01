"""
LLM Middleware Pipeline - Production Ready Implementation
Handles preprocessing, prompt composition, model inference, and postprocessing
with error handling, logging, and configuration management.
"""

import logging
import json
from typing import Dict, Any, Callable, Optional, Union, List
from dataclasses import dataclass
import time
import os
from dotenv import load_dotenv
import requests
from functools import wraps
import pathlib

# Local imports
from utils.validators import validate_input, validate_output
from utils.metrics import MetricsCollector

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_pipeline")

# Configuration
@dataclass
class PipelineConfig:
    """Configuration for the LLM Pipeline"""
    llm_api_url: str = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    timeout_seconds: int = int(os.getenv("TIMEOUT_SECONDS", "10"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    strip_input: bool = True
    lowercase_input: bool = True
    uppercase_output: bool = False
    template_dir: str = os.getenv("TEMPLATE_DIR", "prompt_templates")
    default_template: str = os.getenv("DEFAULT_TEMPLATE", "default.txt")
    validate_schemas: bool = True
    collect_metrics: bool = True
    metrics_port: int = int(os.getenv("METRICS_PORT", "8000"))
    expose_metrics: bool = os.getenv("EXPOSE_METRICS", "False").lower() == "true"

class PipelineError(Exception):
    """Custom error for pipeline failures"""
    pass

# Timing decorator for performance monitoring
def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} executed in {(end_time - start_time)*1000:.2f}ms")
        return result
    return wrapper

class LLMPipeline:
    """Production-ready LLM middleware pipeline"""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the pipeline with configuration"""
        self.config = config or PipelineConfig()
        self.metrics = MetricsCollector(enabled=self.config.collect_metrics)
        
        # Extension points (hooks)
        self.pre_hooks: List[Callable] = []
        self.post_hooks: List[Callable] = []
        
        # Start metrics server if configured
        if self.config.expose_metrics and self.config.collect_metrics:
            self.metrics.start_http_server(self.config.metrics_port)
            
        logger.info(f"Pipeline initialized with model: {self.config.model_name}")
    
    def add_pre_hook(self, hook: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """
        Add a pre-processing hook that runs before the main pipeline
        Hook should take and return a dict with 'input_text' and 'context'
        """
        self.pre_hooks.append(hook)
        logger.info(f"Added pre-processing hook: {hook.__name__}")
    
    def add_post_hook(self, hook: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """
        Add a post-processing hook that runs after the main pipeline
        Hook should take and return the result dictionary
        """
        self.post_hooks.append(hook)
        logger.info(f"Added post-processing hook: {hook.__name__}")
    
    def _load_template(self, template_name: Optional[str] = None) -> str:
        """
        Load a prompt template from file
        """
        template_file = template_name or self.config.default_template
        template_path = pathlib.Path(self.config.template_dir) / template_file
        
        try:
            with open(template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Template file not found: {template_path}, using fallback template")
            return "User: {user_input}\nContext: {context}\nResponse:"
    
    @timing_decorator
    def preprocess_input(self, input_text: str, context: Any) -> Dict[str, Any]:
        """
        Stage 1: Input Preprocessing
        Normalizes input based on configuration
        """
        if not isinstance(input_text, str):
            raise PipelineError(f"Input must be a string, got {type(input_text)}")
            
        processed_input = input_text
        
        if self.config.strip_input:
            processed_input = processed_input.strip()
            
        if self.config.lowercase_input:
            processed_input = processed_input.lower()
            
        logger.debug(f"Preprocessed input: '{processed_input}'")
        
        return {
            "input": processed_input,
            "context": context
        }
    
    @timing_decorator
    def compose_prompt(self, preprocessed_data: Dict[str, Any], template_name: Optional[str] = None) -> str:
        """
        Stage 2: Prompt Composer
        Creates the actual prompt sent to the LLM using an external template
        """
        try:
            user_input = preprocessed_data["input"]
            context = preprocessed_data["context"]
            
            # Load template from file
            template = self._load_template(template_name)
            
            # Format template with user input and context
            prompt = template.format(user_input=user_input, context=context)
            
            logger.debug(f"Composed prompt: {prompt}")
            return prompt
            
        except KeyError as e:
            raise PipelineError(f"Missing required key in preprocessed data: {e}")
    
    @timing_decorator
    def run_inference(self, prompt: str) -> Dict[str, Any]:
        """
        Stage 3: LLM Model Inference
        Sends prompt to LLM API and returns response with usage statistics
        """
        if not prompt:
            raise PipelineError("Cannot run inference with empty prompt")
            
        # If in testing/development mode without API key
        if not self.config.llm_api_key:
            logger.warning("Using mock LLM response (no API key provided)")
            return {
                "content": f"[Development Mode] Mock response for: {prompt[:50]}...",
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": 10,
                    "total_tokens": len(prompt.split()) + 10
                }
            }
        
        # Track inference time for metrics
        inference_start = time.time()
        
        # Actual API implementation
        headers = {
            "Authorization": f"Bearer {self.config.llm_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        }
        
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(
                    self.config.llm_api_url, 
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout_seconds
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    # Record metrics if available
                    if self.config.collect_metrics and 'usage' in result:
                        self.metrics.record_token_usage(result['usage'])
                        self.metrics.time_inference(inference_start)
                    
                    return {
                        "content": content,
                        "usage": result.get('usage', {})
                    }
                else:
                    logger.error(f"API error: {response.status_code}, {response.text}")
                    
            except (requests.RequestException, json.JSONDecodeError) as e:
                logger.error(f"Request failed (attempt {attempt+1}/{self.config.max_retries}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise PipelineError(f"Failed to get response after {self.config.max_retries} attempts")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise PipelineError("Inference failed")
    
    @timing_decorator
    def postprocess_output(self, inference_result: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Stage 4: Output Postprocessing
        Formats the output as needed
        """
        output = inference_result.get("content", "")
        usage = inference_result.get("usage", {})
        
        if not isinstance(output, str):
            raise PipelineError(f"Output must be a string, got {type(output)}")
            
        processed_output = output
        
        if self.config.uppercase_output:
            processed_output = processed_output.upper()
        
        return {
            "final_output": processed_output,
            "context_used": context,
            "timestamp": time.time(),
            "token_usage": usage if usage else None
        }
    
    def process(self, input_text: str, context: Any = None, template_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the complete pipeline from input to output with hooks and validation
        """
        pipeline_start = time.time()
        self.metrics.record_request()
        
        try:
            # Initial input data
            input_data = {
                "input_text": input_text,
                "context": context
            }
            
            # Run pre-hooks if any
            for hook in self.pre_hooks:
                input_data = hook(input_data)
            
            # Validate input if configured
            if self.config.validate_schemas:
                input_data = validate_input(input_data)
            
            logger.info(f"Processing input: '{input_data['input_text'][:50]}...'")
            
            # Main pipeline steps
            preprocessed = self.preprocess_input(input_data["input_text"], input_data["context"])
            prompt = self.compose_prompt(preprocessed, template_name)
            inference_result = self.run_inference(prompt)
            result = self.postprocess_output(inference_result, input_data["context"])
            
            # Add token usage metrics if available
            if "token_usage" in result and result["token_usage"]:
                logger.info(
                    f"Token usage: {result['token_usage'].get('total_tokens', 0)} "
                    f"(prompt: {result['token_usage'].get('prompt_tokens', 0)}, "
                    f"completion: {result['token_usage'].get('completion_tokens', 0)})"
                )
            
            # Validate output if configured
            if self.config.validate_schemas:
                result = validate_output(result)
            
            # Run post-hooks if any
            for hook in self.post_hooks:
                result = hook(result)
            
            # Record metrics
            self.metrics.record_success()
            self.metrics.time_pipeline(pipeline_start)
            
            logger.info("Processing completed successfully")
            return result
            
        except PipelineError as e:
            logger.error(f"Pipeline error: {e}")
            self.metrics.record_failure()
            return {
                "error": str(e),
                "input": input_text,
                "context": context,
                "status": "failed"
            }
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            self.metrics.record_failure()
            return {
                "error": "Internal pipeline error",
                "status": "failed"
            }

# Example use
if __name__ == "__main__":
    # Create pipeline with default config
    pipeline = LLMPipeline()
    
    # Example custom hooks
    def log_input_hook(input_data):
        logger.info(f"Pre-hook processing input: {input_data}")
        return input_data
        
    def add_timestamp_hook(result):
        result["processed_at"] = time.time()
        return result
    
    # Add hooks
    pipeline.add_pre_hook(log_input_hook)
    pipeline.add_post_hook(add_timestamp_hook)
    
    # Process a sample input
    x = "Hello there, how are you?"
    c = "Polite Tone"
    
    result = pipeline.process(x, c)
    print(json.dumps(result, indent=2))