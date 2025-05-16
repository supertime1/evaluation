# LLM Evaluation Platform

A self-hosted dashboard for defining, running, and visualizing LLM evaluation experiments powered by deepeval.

## Overview

This platform allows users to:
- Create experiments to evaluate LLM systems
- Define runs with specific git commits and hyperparameters
- Create and manage test cases (LLM, conversational, multimodal)
- Record and analyze test results with metrics

## Technology Stack

- **Backend**: FastAPI with SQLAlchemy (async)
- **Database**: PostgreSQL
- **Validation**: Pydantic v2
- **Migration**: Alembic
- **Authentication**: JWT tokens with cookie transport
- **User Management**: FastAPI-Users
- **Testing**: Async httpx client for API testing
- **LLM Evaluation**: Integration with deepeval library

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL database
- OpenAI API key (for deepeval integration)

### Setup

1. Create and activate your virtual environment:
   ```sh
   micromamba create -n evaluation python=3.10
   micromamba activate evaluation
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Copy and edit environment variables:
   ```sh
   cp .env.example .env
   # Edit .env as needed with your database credentials and OpenAI API key
   ```

4. Initialize the database:
   ```sh
   alembic upgrade head
   ```

5. Create a superuser (optional):
   ```sh
   python -m scripts.create_superuser
   ```

6. Run the FastAPI app:
   ```sh
   uvicorn app.main:app --reload
   ```

### Health Check
Visit [http://localhost:8000/health](http://localhost:8000/health) to verify the backend is running.

### API Documentation
API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs) when the server is running.

## Architecture

### Data Model

- **Experiment**: A high-level container for evaluation of an LLM system
- **Run**: A specific evaluation run with hyperparameters
- **TestCase**: Test cases used for evaluation (llm, conversational, multimodal)
- **TestResult**: Results of evaluating test cases for a run

### API Endpoints

#### Authentication
- `POST /api/v1/auth/register`: Register a new user
- `POST /api/v1/auth/jwt/login`: Login and get JWT token
- `POST /api/v1/auth/jwt/logout`: Logout and clear JWT token

#### Experiments
- `POST /api/v1/experiments/`: Create a new experiment
- `GET /api/v1/experiments/`: List all experiments for the current user
- `GET /api/v1/experiments/{experiment_id}`: Get a specific experiment
- `PUT /api/v1/experiments/{experiment_id}`: Update an experiment
- `DELETE /api/v1/experiments/{experiment_id}`: Delete an experiment

#### Runs
- `POST /api/v1/runs/`: Create a new run for an experiment
- `GET /api/v1/runs/{run_id}`: Get a specific run with its test results
- `PUT /api/v1/runs/{run_id}`: Update a run's details
- `DELETE /api/v1/runs/{run_id}`: Delete a run (cascades to test results)

#### Test Cases
- `POST /api/v1/test-cases/`: Create a new test case
- `GET /api/v1/test-cases/`: List all test cases for the current user
- `GET /api/v1/test-cases/global`: List all global test cases
- `GET /api/v1/test-cases/type/{test_case_type}`: Get test cases by type
- `GET /api/v1/test-cases/{test_case_id}`: Get a specific test case
- `PUT /api/v1/test-cases/{test_case_id}`: Update a test case
- `DELETE /api/v1/test-cases/{test_case_id}`: Delete a test case

#### Test Results
- `POST /api/v1/test-results/`: Create a new test result
- `POST /api/v1/test-results/batch`: Create multiple test results at once
- `GET /api/v1/test-results/{test_result_id}`: Get a specific test result

## Typical Workflow

1. Create an experiment to evaluate your LLM system
2. Create test cases with inputs and expected outputs
3. Create a run for your experiment with specific hyperparameters
4. Submit test results for the run, including metrics data
5. Analyze the results to improve your LLM system

## Integration Example

Here's an example of how to integrate with the API from Python:

```python
import httpx
import asyncio
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval
from deepeval.evaluate import evaluate

# Function to serialize MetricData objects
def serialize_metric_data(metric_data):
    return [
        {
            "name": metric.name,
            "score": metric.score,
            "threshold": metric.threshold,
            "success": metric.success,
            "reason": metric.reason,
            "strict_mode": metric.strict_mode,
            "evaluation_model": metric.evaluation_model,
            "error": metric.error,
            "evaluation_cost": metric.evaluation_cost,
            "verbose_logs": metric.verbose_logs
        }
        for metric in metric_data
    ] if metric_data else []

async def run_evaluation():
    # Authenticate
    async with httpx.AsyncClient() as client:
        login_response = await client.post(
            "http://localhost:8000/api/v1/auth/jwt/login",
            data={"username": "user@example.com", "password": "password"}
        )
        cookies = login_response.cookies
        
        # Create experiment
        experiment_response = await client.post(
            "http://localhost:8000/api/v1/experiments/",
            json={"name": "Test Experiment", "description": "Testing GPT-4"},
            cookies=cookies
        )
        experiment_id = experiment_response.json()["id"]
        
        # Create run
        run_response = await client.post(
            "http://localhost:8000/api/v1/runs/",
            json={
                "experiment_id": experiment_id,
                "git_commit": "abc123",
                "hyperparameters": {"model": "gpt-4", "temperature": 0.7}
            },
            cookies=cookies
        )
        run_id = run_response.json()["id"]
        
        # Submit results
        test_result_payload = {
            "run_id": run_id,
            "test_case_id": "tc_12345678",  # Your test case ID
            "name": "Test Result",
            "success": True,
            "conversational": False,
            "input": "What is the capital of France?",
            "actual_output": "The capital of France is Paris.",
            "expected_output": "Paris",
            "metrics_data": serialize_metric_data([...]),  # Your metrics data
            "additional_metadata": {}
        }
        
        await client.post(
            "http://localhost:8000/api/v1/test-results/",
            json=test_result_payload,
            cookies=cookies
        )

if __name__ == "__main__":
    asyncio.run(run_evaluation())
```

## Running Tests

To run the end-to-end tests:

```sh
python -m tests.test_experiments_api
```

For the evaluation integration tests:

```sh
python -m tests.end_to_end_test
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

[MIT License](LICENSE)