"""
Example showing how to use LLM Pipeline with FastAPI
"""

import sys
import os
import time
from typing import Dict, Any, Optional

# Add parent directory to path so we can import the pipeline
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from core import LLMPipeline, PipelineConfig

# Define API models
class PipelineRequest(BaseModel):
    """Input model for the pipeline API"""
    input_text: str = Field(..., description="The user's input text")
    context: Optional[Any] = Field(None, description="Optional context for the request")
    template_name: Optional[str] = Field(None, description="Optional template name to use")

class PipelineResponse(BaseModel):
    """Output model for the pipeline API"""
    output: str = Field(..., description="The generated output")
    request_id: str = Field(..., description="Unique ID for this request")
    processing_time_ms: float = Field(..., description="Time taken to process the request in ms")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics if available")

# Create FastAPI app
app = FastAPI(
    title="LLM Pipeline Example API",
    description="Example API for using LLM Pipeline with FastAPI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create pipeline with metrics enabled
pipeline_config = PipelineConfig(
    collect_metrics=True,
    expose_metrics=True,
    metrics_port=9090
)
pipeline = LLMPipeline(pipeline_config)

# Request counter
request_counter = 0

# Health check endpoint
@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "timestamp": time.time()}

# Main pipeline endpoint
@app.post("/process", response_model=PipelineResponse)
def process_request(request: PipelineRequest):
    """Process text through the LLM pipeline"""
    global request_counter
    request_counter += 1
    request_id = f"req_{int(time.time())}_{request_counter}"
    
    start_time = time.time()
    
    try:
        # Process the request through the pipeline
        result = pipeline.process(
            input_text=request.input_text,
            context=request.context,
            template_name=request.template_name
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Calculate processing time
        process_time_ms = (time.time() - start_time) * 1000
        
        # Return the response
        return PipelineResponse(
            output=result["final_output"],
            request_id=request_id,
            processing_time_ms=process_time_ms,
            token_usage=result.get("token_usage")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example hook adding request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

if __name__ == "__main__":
    # Start the server
    print("Starting example FastAPI server on port 8000")
    print("Prometheus metrics exposed on port 9090")
    print("Visit http://localhost:8000/docs for Swagger UI")
    uvicorn.run(app, host="0.0.0.0", port=8000)