# LLM Pipeline: Production-Ready Middleware for LLM-Powered Systems

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![API](https://img.shields.io/badge/api-FastAPI-green)

A modular, configurable LLM middleware pipeline that transforms raw prompts into enterprise-ready microservices.

Originally developed as part of a recursive architecture research project exploring symbolic and sub-symbolic hybrid systems. This production-grade middleware pipeline is for large language model (LLM) interactions designed for robustness, extensibility, and observability.

## Features

- **Complete Processing Pipeline**: Input preprocessing, prompt composition, model inference, and output processing
- **Externalized Prompt Templates**: Edit and iterate on prompts without code changes
- **Robust Error Handling**: Graceful failure modes with exponential backoff
- **Schema Validation**: Optional input/output validation with Pydantic
- **Extension Points**: Pre/post-processing hooks for custom logic injection
- **Metrics Collection**: Prometheus-compatible metrics for request rates, token usage, and latency
- **Thorough Logging**: Detailed operational logs with timing information
- **REST API**: FastAPI wrapper with OpenAPI documentation
- **Containerized**: Ready-to-deploy Docker setup

## Architecture Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          LLM Pipeline System                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             Pre-Hook Layer                              │
│                                                                         │
│   ┌─────────┐       ┌─────────┐        ┌─────────┐       ┌─────────┐    │
│   │ Pre-Hook│  ──▶  │ Pre-Hook│   ──▶  │ Pre-Hook│  ──▶  │   ...   │    │
│   │    1    │       │    2    │        │    3    │       │         │    │
│   └─────────┘       └─────────┘        └─────────┘       └─────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             Core Pipeline                               │
│                                                                         │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐  │
│   │    Input   │    │   Prompt   │    │    LLM     │    │   Output   │  │
│   │ Preprocess │──▶ │ Composition│──▶ │ Inference  │──▶ │Postprocess │  │
│   │            │    │            │    │            │    │            │  │
│   └────────────┘    └────────────┘    └────────────┘    └────────────┘  │
│         │                 │                 │                 │         │
│         ▼                 ▼                 ▼                 ▼         │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐  │
│   │  Normalize │    │  Template  │    │  Retries/  │    │   Format   │  │
│   │   Input    │    │  Loading   │    │  Backoff   │    │   Output   │  │
│   └────────────┘    └────────────┘    └────────────┘    └────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            Post-Hook Layer                              │
│                                                                         │
│   ┌─────────┐       ┌─────────┐        ┌─────────┐       ┌─────────┐    │
│   │Post-Hook│  ──▶  │Post-Hook│   ──▶  │Post-Hook│  ──▶  │   ...   │    │
│   │    1    │       │    2    │       │     3    │       │         │    │
│   └─────────┘       └─────────┘        └─────────┘       └─────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Observability & Export Layer                       │
│                                                                         │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│   │    Logs     │    │   Metrics   │    │   Result    │                 │
│   │             │    │             │    │             │                 │
│   └─────────────┘    └─────────────┘    └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## Implementation Flow

```
     ┌───────────┐          ┌──────────────┐
     │  Client   │          │ Environment  │
     │ Request   │────┬────▶│  Variables   │
     └───────────┘    │     └──────────────┘
           │          │            │
           ▼          │            ▼
┌────────────────────┐│    ┌──────────────┐
│    API Layer       ││    │ Configuration │
│    (FastAPI)       │├───▶│   Loading    │
└────────────────────┘│    └──────────────┘
           │          │            │
           ▼          │            ▼
┌────────────────────┐│    ┌──────────────┐
│   Input Validation ││    │    Prompt    │
│     (Pydantic)     │├───▶│  Templates   │
└────────────────────┘│    └──────────────┘
           │          │            │
           ▼          │            ▼
┌────────────────────┐│    ┌──────────────┐
│  Pipeline Process  │└───▶│  Metrics &   │
│     Execution      │     │   Logging    │
└────────────────────┘     └──────────────┘
           │                       ▲
           ▼                       │
┌────────────────────┐     ┌──────────────┐
│   LLM Provider     │────▶│ Usage Stats  │
│      (API)         │     │  Collection  │
└────────────────────┘     └──────────────┘
```

## Installation

### Option 1: Direct Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-pipeline.git
cd llm-pipeline

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp env.example .env
# Edit .env with your configuration
```

### Option 2: Docker

```bash
# Build the Docker image
docker build -t llm-pipeline .

# Run the container
docker run -p 8000:8000 --env-file .env llm-pipeline
```

## ⚡ Quick Start

### As a Python Library

```python
from core import LLMPipeline, PipelineConfig

# Create a pipeline with default config
pipeline = LLMPipeline()

# Process a query
result = pipeline.process(
    input_text="Explain quantum computing in simple terms",
    context={"audience": "beginners"}
)

print(result["final_output"])
```

### As a REST API

```bash
# Start the server
python main.py

# In another terminal, send a request
curl -X POST \
  http://localhost:8000/process \
  -H 'Content-Type: application/json' \
  -d '{
    "input_text": "Explain quantum computing in simple terms",
    "context": {"audience": "beginners"}
  }'
```

## Pipeline Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ┌───────────┐     ┌────────────┐     ┌────────────┐     ┌───────────────┐      │
│  │   Input   │     │  Template  │     │    API     │     │    Format     │      │
│  │   Text    │────▶│  Selection │────▶│   Request  │────▶│    Output     │      │
│  │           │     │            │     │            │     │               │      │
│  └───────────┘     └────────────┘     └────────────┘     └───────────────┘      │
│        │                 ▲                  │                    ▲               │
│        │                 │                  │                    │               │
│        ▼                 │                  ▼                    │               │
│  ┌───────────┐     ┌────────────┐     ┌────────────┐     ┌───────────────┐      │
│  │  Context  │     │   Prompt   │     │  Response  │     │    Context    │      │
│  │  Object   │────▶│ Generation │────▶│  Parsing   │────▶│  Integration  │      │
│  │           │     │            │     │            │     │               │      │
│  └───────────┘     └────────────┘     └────────────┘     └───────────────┘      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Configuration

The pipeline is configured via environment variables or a `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_URL` | API endpoint for LLM provider | OpenAI chat endpoint |
| `LLM_API_KEY` | API key for LLM provider | None (mock responses) |
| `MODEL_NAME` | Model to use for inference | gpt-3.5-turbo |
| `TIMEOUT_SECONDS` | Request timeout | 10 |
| `MAX_RETRIES` | Number of retries for failed requests | 3 |
| `TEMPLATE_DIR` | Directory for prompt templates | prompt_templates |
| `DEFAULT_TEMPLATE` | Default template file | default.txt |
| `METRICS_PORT` | Port for Prometheus metrics | 8000 |
| `EXPOSE_METRICS` | Whether to expose metrics endpoint | False |
| `API_PORT` | Port for the FastAPI server | 8000 |

## Metrics and Monitoring

```
┌───────────────────────────────────┐
│           Metrics System          │
└───────────────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐       ┌────────────┐
│ Request │       │   Token    │
│ Metrics │       │   Usage    │
└─────────┘       └────────────┘
    │                   │
    ▼                   ▼
┌─────────┐       ┌────────────┐
│ Success │       │   Prompt   │
│  Rate   │       │   Tokens   │
└─────────┘       └────────────┘
    │                   │
    ▼                   ▼
┌─────────┐       ┌────────────┐
│ Latency │       │ Completion │
│ Timing  │       │   Tokens   │
└─────────┘       └────────────┘
    │                   │
    └─────────┬─────────┘
              ▼
┌───────────────────────────────────┐
│     Prometheus Exporter (8000)    │
└───────────────────────────────────┘
```

When enabled, the pipeline exports Prometheus-compatible metrics:

- `llm_pipeline_requests_total`: Total request count
- `llm_pipeline_success_total`: Successful request count
- `llm_pipeline_failure_total`: Failed request count
- `llm_pipeline_prompt_tokens_total`: Prompt token usage
- `llm_pipeline_completion_tokens_total`: Completion token usage
- `llm_pipeline_total_tokens`: Total token usage
- `llm_pipeline_latency_seconds`: Full pipeline latency histogram
- `llm_inference_latency_seconds`: LLM inference latency histogram

## API Reference

When running the FastAPI server, visit `http://localhost:8000/docs` for interactive API documentation.

## Error Handling Strategy

```
┌─────────────────────────────────────────────────┐
│              Error Detection Point              │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│               Error Classification              │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
        ▼                        ▼
┌───────────────┐       ┌─────────────────┐
│  Temporary    │       │   Permanent     │
│    Error      │       │     Error       │
└───────┬───────┘       └────────┬────────┘
        │                        │
        ▼                        ▼
┌───────────────┐       ┌─────────────────┐
│   Retry with  │       │  Return Error   │
│ Exp. Backoff  │       │    Response     │
└───────┬───────┘       └────────┬────────┘
        │                        │
        ▼                        │
┌───────────────┐                │
│Retry Exceeded?│───Yes──────────┘
│               │
└───────┬───────┘
        │ No
        ▼
┌───────────────┐
│ Retry Request │
└───────────────┘
```

## Testing

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_pipeline
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact 

e: artisanllmframeworks@gmail.com IN: www.linkedin.com/in/danleebrown
