#!/usr/bin/env python3
"""
Simple script to test the experiment API endpoints manually.
Usage: python -m tests.manual_tests.test_experiments_api
"""

import asyncio
import json
import httpx
from urllib.parse import urljoin

BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = f"{BASE_URL}/auth/jwt/login"  # This should match the FastAPI-Users auth router
EXPERIMENTS_URL = f"{BASE_URL}/experiments/"
RUNS_URL = f"{BASE_URL}/runs/"
TEST_RESULTS_URL = f"{BASE_URL}/test-results/"

# Test user credentials
EMAIL = "luzhang@fortinet-us.com"
PASSWORD = "strongpassword"

async def test_unauthorized_access(client: httpx.AsyncClient, url: str, method: str = "GET", json_data: dict = None):
    """Test that unauthorized access is rejected."""
    print(f"\n📝 Testing unauthorized access to {url}...")
    print(f"📝 Current client cookies: {dict(client.cookies)}")
    
    # Create a fresh client with no cookies
    async with httpx.AsyncClient() as fresh_client:
        try:
            if method == "GET":
                response = await fresh_client.get(url)
            elif method == "POST":
                response = await fresh_client.post(url, json=json_data)
            elif method == "PUT":
                response = await fresh_client.put(url, json=json_data)
            elif method == "DELETE":
                response = await fresh_client.delete(url)
            
            if response.status_code == 401:
                print(f"✅ Unauthorized access correctly rejected (401 Unauthorized)")
                print(f"✅ Error message: {response.json()['detail']}")
            elif response.status_code == 405:
                print(f"✅ Method not allowed (405) - this is expected for some endpoints")
            else:
                print(f"❌ Unexpected response for unauthorized access: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Error testing unauthorized access: {str(e)}")

async def main():
    print("🧪 Testing Experiment API...")
    
    async with httpx.AsyncClient() as client:
        # 1. Test unauthorized access to protected endpoints
        print("\n🔒 Testing unauthorized access to protected endpoints...")
        await test_unauthorized_access(client, EXPERIMENTS_URL)
        await test_unauthorized_access(client, RUNS_URL)
        await test_unauthorized_access(client, TEST_RESULTS_URL)
        
        # 2. Authenticate
        print("\n📝 Authenticating...")
        try:
            auth_response = await client.post(
                AUTH_URL,
                data={"username": EMAIL, "password": PASSWORD}
            )
            
            if auth_response.status_code not in [200, 204]:
                print(f"❌ Authentication failed: {auth_response.status_code}")
                print(f"URL: {AUTH_URL}")
                print(f"Response: {auth_response.text}")
                return
                
            cookies = auth_response.cookies
            print(f"✅ Authentication successful")
            print(f"Cookies: {dict(cookies)}")
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return

        # 3. Create an experiment
        print("\n📝 Creating experiment...")
        create_response = await client.post(
            EXPERIMENTS_URL,
            json={"name": "Test Experiment", "description": "This is a test experiment"},
            cookies=cookies
        )
        
        if create_response.status_code != 200:
            print(f"❌ Create failed: {create_response.status_code}")
            print(create_response.text)
            return
            
        experiment = create_response.json()
        experiment_id = experiment["id"]
        print(f"✅ Created experiment: {experiment_id}")
        print(json.dumps(experiment, indent=2))
        
        # 4. Create a run for the experiment
        print("\n📝 Creating run...")
        run_payload = {
            "experiment_id": experiment_id,
            "git_commit": "abc123",
            "hyperparameters": {"model": "gpt-4", "temperature": 0.7}
        }
        create_run_response = await client.post(RUNS_URL, json=run_payload, cookies=cookies)
        if create_run_response.status_code != 200:
            print(f"❌ Create run failed: {create_run_response.status_code}")
            print(create_run_response.text)
            return
        run = create_run_response.json()
        run_id = run["id"]
        print(f"✅ Created run: {run_id}")
        print(json.dumps(run, indent=2))

        # 5. Create a test case
        print("\n📝 Creating test case...")
        test_case_payload = {
            "name": "Test Case 1",
            "description": "A test case for testing the API",
            "input": "What is the capital of France?",
            "expected_output": "Paris",
            "context": ["This is a test context"],
            "retrieval_context": ["This is a test retrieval context"]
        }
        create_test_case_response = await client.post(
            f"{BASE_URL}/test-cases/",
            json=test_case_payload,
            cookies=cookies
        )
        if create_test_case_response.status_code != 200:
            print(f"❌ Create test case failed: {create_test_case_response.status_code}")
            print(create_test_case_response.text)
            return
        test_case = create_test_case_response.json()
        test_case_id = test_case["id"]
        print(f"✅ Created test case: {test_case_id}")
        print(json.dumps(test_case, indent=2))

        # 6. Test unauthorized access to test results
        await test_unauthorized_access(client, TEST_RESULTS_URL)
        test_result_id = "test_12345678"  # This will be replaced with actual ID after creation
        await test_unauthorized_access(client, urljoin(TEST_RESULTS_URL, test_result_id))

        # 7. Create a test result
        print("\n📝 Creating test result...")
        test_result_payload = {
            "run_id": run_id,
            "test_case_id": test_case_id,  # Use the actual test case ID
            "name": "Test Case 1",
            "success": True,
            "conversational": True,
            "input": "What is the capital of France?",
            "actual_output": "The capital of France is Paris.",
            "expected_output": "Paris",
            "context": ["This is a test context"],
            "retrieval_context": ["This is a test retrieval context"],
            "metrics_data": [
                {
                    "name": "accuracy",
                    "score": 1.0,
                    "threshold": 0.8,
                    "success": True,
                    "reason": "Score exceeds threshold",
                    "strict_mode": False,
                    "evaluation_model": "gpt-4",
                    "evaluation_cost": 0.001
                }
            ],
            "additional_metadata": {
                "model": "gpt-4",
                "temperature": 0.7
            }
        }
        create_test_result_response = await client.post(
            TEST_RESULTS_URL,
            json=test_result_payload,
            cookies=cookies
        )
        if create_test_result_response.status_code != 200:
            print(f"❌ Create test result failed: {create_test_result_response.status_code}")
            print(create_test_result_response.text)
            return
        test_result = create_test_result_response.json()
        test_result_id = test_result["id"]
        print(f"✅ Created test result: {test_result_id}")
        print(json.dumps(test_result, indent=2))

        # 8. Get the test result
        print(f"\n📝 Getting test result {test_result_id}...")
        get_test_result_url = urljoin(TEST_RESULTS_URL, test_result_id)
        get_test_result_response = await client.get(get_test_result_url, cookies=cookies)
        if get_test_result_response.status_code != 200:
            print(f"❌ Get test result failed: {get_test_result_response.status_code}")
            print(get_test_result_response.text)
        else:
            test_result = get_test_result_response.json()
            print(f"✅ Got test result")
            print(json.dumps(test_result, indent=2))

        # 9. Test unauthorized access to specific test result
        await test_unauthorized_access(client, get_test_result_url)

        # 10. Get the run to verify test results are included
        print(f"\n📝 Getting run {run_id} to verify test results...")
        get_run_url = urljoin(RUNS_URL, run_id)
        get_run_response = await client.get(get_run_url, cookies=cookies)
        if get_run_response.status_code != 200:
            print(f"❌ Get run failed: {get_run_response.status_code}")
            print(get_run_response.text)
        else:
            run = get_run_response.json()
            print(f"✅ Got run with test results")
            print(json.dumps(run, indent=2))

        # 11. Clean up - Delete the run (which will cascade delete test results)
        print(f"\n📝 Deleting run {run_id}...")
        delete_run_response = await client.delete(get_run_url, cookies=cookies)
        if delete_run_response.status_code != 200:
            print(f"❌ Delete run failed: {delete_run_response.status_code}")
            print(delete_run_response.text)
        else:
            print(f"✅ Deleted run")

        # 12. Delete experiment
        print(f"\n📝 Deleting experiment {experiment_id}...")
        delete_url = urljoin(EXPERIMENTS_URL, experiment_id)
        delete_response = await client.delete(delete_url, cookies=cookies)
        
        if delete_response.status_code != 200:
            print(f"❌ Delete failed: {delete_response.status_code}")
            print(delete_response.text)
        else:
            print(f"✅ Deleted experiment")
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    asyncio.run(main()) 