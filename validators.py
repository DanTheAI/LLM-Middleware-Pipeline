"""
Schema validators and utility functions for LLM Pipeline
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("llm_pipeline.validators")

try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    logger.warning("Pydantic not available. Schema validation disabled.")

if PYDANTIC_AVAILABLE:
    class PipelineInput(BaseModel):
        """Schema for validating pipeline input"""
        input_text: str
        context: Any = None
        
        @validator('input_text')
        def input_not_empty(cls, v):
            if not v.strip():
                raise ValueError('input_text cannot be empty')
            return v

    class PipelineOutput(BaseModel):
        """Schema for validating pipeline output"""
        final_output: str
        context_used: Any = None
        timestamp: float
        token_usage: Optional[Dict[str, int]] = None
        
        @validator('final_output')
        def output_not_empty(cls, v):
            if not v.strip():
                raise ValueError('final_output cannot be empty')
            return v

def validate_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate input data against schema if pydantic is available"""
    if not PYDANTIC_AVAILABLE:
        return input_data
    
    try:
        validated = PipelineInput(**input_data)
        return validated.dict()
    except Exception as e:
        logger.error(f"Input validation error: {e}")
        raise e

def validate_output(output_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate output data against schema if pydantic is available"""
    if not PYDANTIC_AVAILABLE:
        return output_data
    
    try:
        validated = PipelineOutput(**output_data)
        return validated.dict()
    except Exception as e:
        logger.error(f"Output validation error: {e}")
        raise e
