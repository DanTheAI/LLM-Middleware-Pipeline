"""
Basic usage example of the LLM Pipeline
"""

import sys
import os
import time

# Add parent directory to path so we can import the pipeline
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import LLMPipeline, PipelineConfig

def basic_example():
    # Create a pipeline with default config
    pipeline = LLMPipeline()
    
    # Process a simple query
    result = pipeline.process(
        input_text="Explain quantum computing in simple terms",
        context={"audience": "beginners"}
    )
    
    print("\n=== Basic Example ===")
    print(f"Input: Explain quantum computing in simple terms")
    print(f"Output: {result['final_output']}")
    print(f"Processing time: {result.get('timestamp', 0) - time.time():.2f}s")
    print(f"Token usage: {result.get('token_usage', {})}")

def custom_config_example():
    # Create a pipeline with custom configuration
    config = PipelineConfig(
        model_name="gpt-3.5-turbo",
        max_retries=5,
        uppercase_output=True
    )
    pipeline = LLMPipeline(config)
    
    # Process a query with the custom config
    result = pipeline.process(
        input_text="Write a haiku about programming",
    )
    
    print("\n=== Custom Config Example ===")
    print(f"Input: Write a haiku about programming")
    print(f"Output: {result['final_output']}")
    print(f"Note: Output is uppercase due to configuration")

def custom_hooks_example():
    # Create hooks
    def add_timestamp_hook(result):
        result["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        return result
        
    def log_and_enhance_input(input_data):
        print(f"Pre-hook processing input: {input_data['input_text']}")
        input_data["input_text"] = f"{input_data['input_text']} (Enhanced by hook)"
        return input_data
    
    # Create pipeline and add hooks
    pipeline = LLMPipeline()
    pipeline.add_pre_hook(log_and_enhance_input)
    pipeline.add_post_hook(add_timestamp_hook)
    
    # Process with hooks
    result = pipeline.process("Tell me a fun fact about space")
    
    print("\n=== Custom Hooks Example ===")
    print(f"Input: Tell me a fun fact about space (Enhanced by hook)")
    print(f"Output: {result['final_output']}")
    print(f"Generated at: {result.get('generated_at', '')}")

def custom_template_example():
    # First ensure custom template exists
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompt_templates")
    template_path = os.path.join(template_dir, "code_explanation.txt")
    
    if not os.path.exists(template_path):
        with open(template_path, 'w') as f:
            f.write("Please explain this code: {user_input}\nMake it simple for {context} developers.")
    
    # Create pipeline
    pipeline = LLMPipeline()
    
    # Process with custom template
    result = pipeline.process(
        input_text="def hello(): print('world')",
        context="beginner",
        template_name="code_explanation.txt"
    )
    
    print("\n=== Custom Template Example ===")
    print(f"Input: def hello(): print('world')")
    print(f"Using template: code_explanation.txt")
    print(f"Output: {result['final_output']}")

if __name__ == "__main__":
    print("LLM Pipeline Examples")
    print("=" * 50)
    
    try:
        basic_example()
        custom_config_example()
        custom_hooks_example()
        custom_template_example()
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Note: Some examples may require an API key set in .env file")