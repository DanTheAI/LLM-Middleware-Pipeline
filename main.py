"""
FastAPI wrapper for the LLM Pipeline
"""
import os
import logging
from typing import Dict, Any, Optional
import time

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from core import LLMPipeline, PipelineConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_api")

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
    status: str = Field("success", description="Status of the request")

# Create FastAPI app
app = FastAPI(
    title="LLM Pipeline API",
    description="API for processing text through the LLM Pipeline",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create pipeline instance
pipeline_config = PipelineConfig()
pipeline = LLMPipeline(pipeline_config)

# Request counter for generating request IDs
request_counter = 0

# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Health check endpoint
@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "timestamp": time.time()}

# Main pipeline endpoint
@app.post("/process", response_model=PipelineResponse)
def process_request(request: PipelineRequest, background_tasks: BackgroundTasks):
    """Process text through the LLM pipeline"""
    global request_counter
    request_counter += 1
    request_id = f"req_{int(time.time())}_{request_counter}"
    
    logger.info(f"Received request {request_id}: {request.input_text[:50]}...")
    
    start_time = time.time()
    
    try:
        # Process the request through the pipeline
        result = pipeline.process(
            input_text=request.input_text,
            context=request.context,
            template_name=request.template_name
        )
        
        if "error" in result:
            logger.error(f"Request {request_id} failed: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Calculate processing time
        process_time_ms = (time.time() - start_time) * 1000
        
        # Schedule background tasks if needed
        background_tasks.add_task(log_request_stats, request_id, process_time_ms, result)
        
        # Return the response
        return PipelineResponse(
            output=result["final_output"],
            request_id=request_id,
            processing_time_ms=process_time_ms,
            token_usage=result.get("token_usage"),
            status="success"
        )
        
    except Exception as e:
        logger.exception(f"Error processing request {request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for logging request stats
def log_request_stats(request_id: str, process_time_ms: float, result: Dict[str, Any]):
    """Log request statistics in the background"""
    logger.info(f"Request {request_id} completed in {process_time_ms:.2f}ms")
    
    # Log token usage if available
    if "token_usage" in result and result["token_usage"]:
        usage = result["token_usage"]
        logger.info(
            f"Token usage for {request_id}: {usage.get('total_tokens', 0)} "
            f"(prompt: {usage.get('prompt_tokens', 0)}, "
            f"completion: {usage.get('completion_tokens', 0)})"
        )

# Error handler for exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle exceptions gracefully"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "status": "error"}
    )

# Command-line interface
if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("API_PORT", "8000"))
    
    # Run the FastAPI app with uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
