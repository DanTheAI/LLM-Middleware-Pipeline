"""
Unit tests for LLM Pipeline
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
import time

# Add parent directory to path so we can import the pipeline
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import LLMPipeline, PipelineConfig, PipelineError

class TestLLMPipeline(unittest.TestCase):
    """Test cases for the LLM Pipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a test configuration
        self.config = PipelineConfig()
        self.config.validate_schemas = False  # Disable schema validation for tests
        self.config.collect_metrics = False  # Disable metrics for tests
        
        # Create a pipeline instance with the test config
        self.pipeline = LLMPipeline(self.config)
    
    def test_preprocess_input(self):
        """Test input preprocessing"""
        # Test with default config (strip and lowercase)
        result = self.pipeline.preprocess_input("  TEST Input  ", "test context")
        self.assertEqual(result["input"], "test input")
        self.assertEqual(result["context"], "test context")
        
        # Test with custom config
        self.pipeline.config.strip_input = False
        self.pipeline.config.lowercase_input = False
        result = self.pipeline.preprocess_input("  TEST Input  ", "test context")
        self.assertEqual(result["input"], "  TEST Input  ")
    
    def test_compose_prompt(self):
        """Test prompt composition"""
        # Mock the _load_template method
        with patch.object(self.pipeline, '_load_template', return_value="User: {user_input}\nContext: {context}\nResponse:"):
            prompt = self.pipeline.compose_prompt({"input": "hello", "context": "greeting"})
            self.assertEqual(prompt, "User: hello\nContext: greeting\nResponse:")
    
    @patch('requests.post')
    def test_run_inference_success(self, mock_post):
        """Test successful LLM inference"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello, how can I help you?"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 7, "total_tokens": 17}
        }
        mock_post.return_value = mock_response
        
        # Set API key for this test
        self.pipeline.config.llm_api_key = "test_key"
        
        result = self.pipeline.run_inference("Test prompt")
        self.assertEqual(result["content"], "Hello, how can I help you?")
        self.assertEqual(result["usage"]["total_tokens"], 17)
    
    @patch('requests.post')
    def test_run_inference_api_error(self, mock_post):
        """Test LLM inference with API error"""
        # Mock API error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response
        
        # Set API key for this test
        self.pipeline.config.llm_api_key = "test_key"
        self.pipeline.config.max_retries = 1
        
        with self.assertRaises(PipelineError):
            self.pipeline.run_inference("Test prompt")
    
    def test_postprocess_output(self):
        """Test output postprocessing"""
        # Test with default config
        result = self.pipeline.postprocess_output({"content": "test output", "usage": {"total_tokens": 10}}, "test context")
        self.assertEqual(result["final_output"], "test output")
        self.assertEqual(result["context_used"], "test context")
        self.assertEqual(result["token_usage"]["total_tokens"], 10)
        
        # Test with uppercase output
        self.pipeline.config.uppercase_output = True
        result = self.pipeline.postprocess_output({"content": "test output"}, None)
        self.assertEqual(result["final_output"], "TEST OUTPUT")
    
    @patch.object(LLMPipeline, 'run_inference')
    def test_process_end_to_end(self, mock_run_inference):
        """Test end-to-end pipeline processing"""
        # Mock the inference to avoid API calls
        mock_run_inference.return_value = {
            "content": "Test response", 
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}
        }
        
        # Mock template loading
        with patch.object(self.pipeline, '_load_template', return_value="User: {user_input}\nContext: {context}"):
            result = self.pipeline.process("test input", "test context")
            self.assertEqual(result["final_output"], "Test response")
            self.assertEqual(result["context_used"], "test context")
            self.assertEqual(result["token_usage"]["total_tokens"], 7)
    
    def test_hooks(self):
        """Test pre and post hooks"""
        # Define test hooks
        def pre_hook(data):
            data["input_text"] = data["input_text"] + " PRE"
            return data
            
        def post_hook(result):
            result["final_output"] = result["final_output"] + " POST"
            return result
        
        # Add hooks
        self.pipeline.add_pre_hook(pre_hook)
        self.pipeline.add_post_hook(post_hook)
        
        # Mock inference and template loading
        with patch.object(self.pipeline, 'run_inference', return_value={"content": "Test"}):
            with patch.object(self.pipeline, '_load_template', return_value="{user_input}"):
                result = self.pipeline.process("Hello")
                self.assertEqual(result["final_output"], "Test POST")

if __name__ == '__main__':
    unittest.main()
