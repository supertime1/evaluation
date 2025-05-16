# test from generating evaluation results from a LLM system and stream data to the backend
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.dataset import EvaluationDataset
from deepeval.metrics import GEval
from deepeval.evaluate import evaluate
import httpx


from openai import OpenAI
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import PyPDF2
import dotenv
import asyncio
from urllib.parse import urljoin

from app.schemas.run import RunCreate
from app.schemas.test_case import TestCase
from app.schemas.experiment import ExperimentCreate
from app.models.test_case import TestCaseType

# Load environment variables from .env file
dotenv.load_dotenv()
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

# Function to serialize MetricData objects to dictionaries
def serialize_metric_data(metric_data):
    """Convert MetricData objects to dictionaries."""
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

BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/jwt/login"
EXPERIMENTS_URL = f"{BASE_URL}/experiments/"
RUNS_URL = f"{BASE_URL}/runs/"
TEST_RESULTS_URL = f"{BASE_URL}/test-results/"
TEST_CASES_URL = f"{BASE_URL}/test-cases/"

# Test user credentials
EMAIL = "luzhang@fortinet-us.com"
PASSWORD = "strongpassword"


prompt_template = """
  You are an AI assistant tasked with summarizing software engineer resume
  concisely and accurately. Given the following resume, generate
  a summary that captures the key points. Be concise as possible, but
  DO NOT omit any details from the document. Ensure neutrality and refrain
  from interpreting beyond the provided text.
"""
model = "gpt-3.5-turbo"

def extract_text(pdf_path):
    """
    Extract text from a PDF file.
    """
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    return text


def llm_summarize(text):
    """
    Call OpenAI's API to summarize the text.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{prompt_template} Please summarize the following text:\n{text}"}
        ]
    )
    return response.choices[0].message.content.strip()

concision_metric = GEval(
    name="Concision",
    criteria="Assess if the actual output remains concise while preserving all essential information.",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
)

completeness_metric = GEval(
    name="Completeness",
    criteria="Assess whether the actual output retains all key information from the input.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
)



async def main():
    async with httpx.AsyncClient() as client:
        # register first
        response = await client.post(f"{BASE_URL}/auth/register", data={"username": EMAIL, "password": PASSWORD})
        if response.status_code == 200:
            print(f"✅ Registration successful")
        else:
            print(f"✅ User {EMAIL} already exists")
        
        # sign in first
        login_response = await client.post(LOGIN_URL, data={"username": EMAIL, "password": PASSWORD})
        if login_response.status_code in [200, 204]:
            print(f"✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return

        cookies = login_response.cookies
        # create test cases
        print("\n📝 Creating test case...")

        test_cases = []
        pdf_folder = "tests/pdfs"
        documents = []

        for pdf_file in os.listdir(pdf_folder):
            if pdf_file.endswith(".pdf"):
                pdf_path = os.path.join(pdf_folder, pdf_file)
                document_text = extract_text(pdf_path)
                documents.append(document_text)

        for i, document in enumerate(documents):
            test_case_payload = {
                "name": f"Test Case {i}",
                "type": TestCaseType.LLM.lower(),
                "input": document,
                "expected_output": llm_summarize(document),
                "context": [],
                "retrieval_context": [],
                "additional_metadata": {},
            }



            # FIXME: doesn't seem like the test case is created in database, even though the response code is 200
            response = await client.post(urljoin(TEST_CASES_URL, ""), json=test_case_payload, cookies=cookies)
            if response.status_code == 200:
                print(f"✅ Test case created with id: {response.json()['id']}")
            else:
                print(f"❌ Test case creation failed: {response.status_code}")
                return


        # CLI ask for experiment id
        print("\n📝 Creating run...")
        # create a new experiment and get the id
        experiment_in = ExperimentCreate(
            name="Local Experiment",
            description="Local Experiment",
            status="pending",
        )
        experiment_id = None
        experiment_response = await client.post(urljoin(EXPERIMENTS_URL, ""), json=experiment_in.model_dump(), cookies=cookies) 
        if experiment_response.status_code == 200:
            experiment_id = experiment_response.json()["id"]
            print(f"✅ Experiment created with id: {experiment_id}")
        else:
            print(f"❌ Experiment creation failed: {experiment_response.status_code}")
            return

        # ask user to input the experiment id
        experiment_id = input("Enter experiment id: ")
        experiment_response = await client.get(urljoin(EXPERIMENTS_URL, experiment_id), cookies=cookies)
        if experiment_response.status_code == 404:
            print(f"❌ Experiment not found, you can create a new experiment in the web UI")
            return
        
        print(f"✅ Experiment found with id: {experiment_id}")

        # TODO: fix here
        # create a local run
        run_in = RunCreate(
            experiment_id=experiment_id,
            git_commit="abc123",
            hyperparameters={
                "model": model,
                "prompt_template": prompt_template,
            }
        )

        run_response = await client.post(urljoin(RUNS_URL, ""), json=run_in.model_dump(), cookies=cookies)
        if run_response.status_code == 200:
            print(f"✅ Run created with id: {run_response.json()['id']}")
        else:
            print(f"❌ Run creation failed: {run_response.status_code}")
            return

        run = run_response.json()

        # run evaluation on the llm system
        # pull the test cases
        test_cases_response = await client.get(urljoin(TEST_CASES_URL, "type/llm"), cookies=cookies)
        if test_cases_response.status_code == 200:
            print(f"✅ {len(test_cases_response.json())} test cases found with type: llm")
        else:
            print(f"❌ Test cases not found with type: llm")
            return
        test_cases = test_cases_response.json()

        # Keep the original approach of processing one test case at a time
        # This guarantees correct mapping between test cases and results
        test_result_payloads = []

        for test_case in test_cases:
            # Process one test case at a time to ensure mapping
            single_test_case = LLMTestCase(input=test_case["input"], actual_output=test_case["expected_output"])
            dataset = EvaluationDataset(test_cases=[single_test_case])
            
            llm_result = evaluate(dataset, 
                    metrics=[concision_metric, completeness_metric], 
                    hyperparameters={
                        "model": model,
                        "prompt_template": prompt_template,
                    }
                )
            
            # Since we're evaluating one test case, we know the result is for this test case
            test_result = llm_result.test_results[0]
            print(f"test result: {test_result}")
            print(f"run id: {run['id']}")
            print(f"test case id: {test_case['id']}")
            # create a test result payload  
            test_result_payloads.append({
                "run_id": run["id"],
                "test_case_id": test_case["id"],
                "name": test_result.name,
                "success": test_result.success,
                "conversational": test_result.conversational,
                "input": test_result.input,
                "actual_output": test_result.actual_output,
                "expected_output": test_result.expected_output,
                "context": test_result.context,
                "retrieval_context": test_result.retrieval_context,
                "metrics_data": serialize_metric_data(test_result.metrics_data),
                "additional_metadata": test_result.additional_metadata
            })

        # Send batch request with all results
        save_response = await client.post(urljoin(TEST_RESULTS_URL, "batch"), json=test_result_payloads, cookies=cookies)
        if save_response.status_code == 200:
            created_results = save_response.json()
            print(f"✅ {len(created_results)} test results created in batch")
        else:
            print(f"❌ Batch test result creation failed: {save_response.status_code}")
            print(save_response.text)
            return

if __name__ == "__main__":
    asyncio.run(main())


