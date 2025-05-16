#!/usr/bin/env python3
"""
Simple script to test the experiment API endpoints manually.
Usage: python -m tests.manual_tests.test_experiments_api
"""

import asyncio
import json
import httpx
import os
from urllib.parse import urljoin
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/jwt/login"
EXPERIMENTS_URL = f"{BASE_URL}/experiments/"
RUNS_URL = f"{BASE_URL}/runs/"
TEST_RESULTS_URL = f"{BASE_URL}/test-results/"
TEST_CASES_URL = f"{BASE_URL}/test-cases/"

# Test user credentials
EMAIL = "luzhang@fortinet-us.com"
PASSWORD = "strongpassword"
OTHER_USER_EMAIL = "other@example.com"
OTHER_USER_PASSWORD = "otherpassword"

# Superuser credentials from environment
SUPERUSER_EMAIL = os.getenv("TEST_SUPERUSER_EMAIL", "admin@example.com")
SUPERUSER_PASSWORD = os.getenv("TEST_SUPERUSER_PASSWORD", "adminpassword")

if not SUPERUSER_EMAIL or not SUPERUSER_PASSWORD:
    raise ValueError(
        "Superuser credentials not found in environment variables. "
        "Please set TEST_SUPERUSER_EMAIL and TEST_SUPERUSER_PASSWORD in your .env file."
    )

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

async def setup_other_user(client: httpx.AsyncClient) -> dict:
    """Set up the other user for cross-user access testing."""
    print(f"\n📝 Setting up other user {OTHER_USER_EMAIL}...")
    
    # Try to register the other user
    print(f"📝 Registering other user {OTHER_USER_EMAIL}...")
    register_response = await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": OTHER_USER_EMAIL,
            "password": OTHER_USER_PASSWORD,
            "is_active": True,
            "is_superuser": False,
            "is_verified": False
        }
    )
    
    if register_response.status_code == 409:  # User already exists
        print(f"✅ User {OTHER_USER_EMAIL} already exists, proceeding with authentication")
    elif register_response.status_code not in [200, 201]:
        print(f"❌ Other user registration failed: {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return None
    else:
        print(f"✅ Successfully registered user {OTHER_USER_EMAIL}")
    
    # Authenticate as other user
    print(f"📝 Authenticating as other user {OTHER_USER_EMAIL}...")
    auth_response = await client.post(
        LOGIN_URL,
        data={"username": OTHER_USER_EMAIL, "password": OTHER_USER_PASSWORD}
    )
    
    if auth_response.status_code not in [200, 204]:
        print(f"❌ Other user authentication failed: {auth_response.status_code}")
        print(f"Response: {auth_response.text}")
        return None
    
    other_cookies = auth_response.cookies
    print(f"✅ Other user authentication successful")
    return other_cookies

async def test_cross_user_access(client: httpx.AsyncClient, url: str, method: str = "GET", json_data: dict = None, other_cookies: dict = None):
    """Test that access to other user's resources is rejected."""
    print(f"\n📝 Testing cross-user access to {url}...")
    
    if not other_cookies:
        print("❌ No other user cookies provided for cross-user access test")
        return
    
    # Create a client with other user's cookies
    async with httpx.AsyncClient() as other_client:
        try:
            # Try to access the resource with other user's cookies
            if method == "GET":
                response = await other_client.get(url, cookies=other_cookies)
            elif method == "POST":
                response = await other_client.post(url, json=json_data, cookies=other_cookies)
            elif method == "PUT":
                # For PUT requests, skip if the URL contains test-results as it's not supported
                if "test-results" in url:
                    print(f"⚠️ Skipping PUT cross-user access test for test-results as it's not supported")
                    return
                response = await other_client.put(url, json=json_data, cookies=other_cookies)
            elif method == "DELETE":
                # For DELETE requests, skip if the URL contains test-results as it's not supported
                if "test-results" in url:
                    print(f"⚠️ Skipping DELETE cross-user access test for test-results as it's not supported")
                    return
                response = await other_client.delete(url, cookies=other_cookies)
            
            if response.status_code == 403:
                print(f"✅ Cross-user access correctly rejected (403 Forbidden)")
                print(f"✅ Error message: {response.json()['detail']}")
            elif response.status_code == 404:
                print(f"✅ Resource not found (404) - this is acceptable as the resource might not exist for other user")
            else:
                print(f"❌ Unexpected response for cross-user access: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Error testing cross-user access: {str(e)}")
            import traceback
            print(traceback.format_exc())

async def test_experiments_api(client: httpx.AsyncClient, cookies: dict, other_cookies: dict):
    """Test the experiments API endpoints."""
    print("\n🧪 Testing Experiments API...")

    # 1. Create an experiment
    print("\n📝 Creating experiment...")
    create_response = await client.post(
        EXPERIMENTS_URL,
        json={"name": "Test Experiment", "description": "This is a test experiment"},
        cookies=cookies
    )
    
    if create_response.status_code != 200:
        print(f"❌ Create failed: {create_response.status_code}")
        print(create_response.text)
        return None
        
    experiment = create_response.json()
    experiment_id = experiment["id"]
    print(f"✅ Created experiment: {experiment_id}")
    print(json.dumps(experiment, indent=2))

    # 2. Test cross-user access to experiment
    await test_cross_user_access(
        client,
        f"{EXPERIMENTS_URL}{experiment_id}",
        method="GET",
        other_cookies=other_cookies
    )
    await test_cross_user_access(
        client,
        f"{EXPERIMENTS_URL}{experiment_id}",
        method="PUT",
        json_data={"name": "Unauthorized Update"},
        other_cookies=other_cookies
    )
    await test_cross_user_access(
        client,
        f"{EXPERIMENTS_URL}{experiment_id}",
        method="DELETE",
        other_cookies=other_cookies
    )

    return experiment_id

async def test_runs_api(client: httpx.AsyncClient, cookies: dict, experiment_id: str, other_cookies: dict):
    """Test the runs API endpoints."""
    print("\n🧪 Testing Runs API...")

    # 1. Create a run
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
        return None
    run = create_run_response.json()
    run_id = run["id"]
    print(f"✅ Created run: {run_id}")
    print(json.dumps(run, indent=2))

    # 2. Test cross-user access to run
    await test_cross_user_access(
        client,
        f"{RUNS_URL}{run_id}",
        method="GET",
        other_cookies=other_cookies
    )
    await test_cross_user_access(
        client,
        f"{RUNS_URL}{run_id}",
        method="PUT",
        json_data={"git_commit": "unauthorized"},
        other_cookies=other_cookies
    )
    await test_cross_user_access(
        client,
        f"{RUNS_URL}{run_id}",
        method="DELETE",
        other_cookies=other_cookies
    )

    return run_id

async def test_test_cases_api(client: httpx.AsyncClient, cookies: dict, other_cookies: dict):
    """Test the test cases API endpoints."""
    print("\n🧪 Testing Test Cases API...")

    # 1. Create a test case
    print("\n📝 Creating test case...")
    test_case_payload = {
        "name": "Test Case 1",
        "type": "llm",
        "input": "What is the capital of France?",
        "expected_output": "Paris",
        "context": ["This is a test context"],
        "retrieval_context": ["This is a test retrieval context"],
        "additional_metadata": {"difficulty": "easy"},
        "is_global": False
    }
    create_test_case_response = await client.post(
        TEST_CASES_URL,
        json=test_case_payload,
        cookies=cookies
    )
    if create_test_case_response.status_code != 200:
        print(f"❌ Create test case failed: {create_test_case_response.status_code}")
        print(create_test_case_response.text)
        return None
    test_case = create_test_case_response.json()
    test_case_id = test_case["id"]
    print(f"✅ Created test case: {test_case_id}")
    print(json.dumps(test_case, indent=2))

    # 2. Test cross-user access to test case
    await test_cross_user_access(
        client,
        f"{TEST_CASES_URL}{test_case_id}",
        method="GET",
        other_cookies=other_cookies
    )
    await test_cross_user_access(
        client,
        f"{TEST_CASES_URL}{test_case_id}",
        method="PUT",
        json_data={"name": "Unauthorized Update", "type": "llm"},  # Added type field
        other_cookies=other_cookies
    )
    await test_cross_user_access(
        client,
        f"{TEST_CASES_URL}{test_case_id}",
        method="DELETE",
        other_cookies=other_cookies
    )

    # 3. Get all test cases
    print("\n📝 Getting all test cases...")
    get_test_cases_response = await client.get(TEST_CASES_URL, cookies=cookies)
    if get_test_cases_response.status_code != 200:
        print(f"❌ Get test cases failed: {get_test_cases_response.status_code}")
        print(get_test_cases_response.text)
    else:
        test_cases = get_test_cases_response.json()
        print(f"✅ Got {len(test_cases)} test cases")
        print(json.dumps(test_cases, indent=2))

    # 4. Get global test cases
    print("\n📝 Getting global test cases...")
    get_global_test_cases_response = await client.get(f"{TEST_CASES_URL}global", cookies=cookies)
    if get_global_test_cases_response.status_code != 200:
        print(f"❌ Get global test cases failed: {get_global_test_cases_response.status_code}")
        print(get_global_test_cases_response.text)
    else:
        global_test_cases = get_global_test_cases_response.json()
        print(f"✅ Got {len(global_test_cases)} global test cases")
        print(json.dumps(global_test_cases, indent=2))

    # 5. Get specific test case
    print(f"\n📝 Getting test case {test_case_id}...")
    get_test_case_response = await client.get(f"{TEST_CASES_URL}{test_case_id}", cookies=cookies)
    if get_test_case_response.status_code != 200:
        print(f"❌ Get test case failed: {get_test_case_response.status_code}")
        print(get_test_case_response.text)
    else:
        test_case = get_test_case_response.json()
        print(f"✅ Got test case")
        print(json.dumps(test_case, indent=2))

    # 6. Update test case
    print(f"\n📝 Updating test case {test_case_id}...")
    update_payload = {
        "name": "Updated Test Case 1",
        "expected_output": "Paris, France",
        "type": "llm"  # Added type field which is required
    }
    update_test_case_response = await client.put(
        f"{TEST_CASES_URL}{test_case_id}",
        json=update_payload,
        cookies=cookies
    )
    if update_test_case_response.status_code != 200:
        print(f"❌ Update test case failed: {update_test_case_response.status_code}")
        print(update_test_case_response.text)
    else:
        updated_test_case = update_test_case_response.json()
        print(f"✅ Updated test case")
        print(json.dumps(updated_test_case, indent=2))

    return test_case_id

async def test_test_results_api(client: httpx.AsyncClient, cookies: dict, run_id: str, test_case_id: str, other_cookies: dict):
    """Test the test results API endpoints."""
    print("\n🧪 Testing Test Results API...")

    # 1. Create a test result
    print("\n📝 Creating test result...")
    test_result_payload = {
        "run_id": run_id,
        "test_case_id": test_case_id,
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
        return None
    test_result = create_test_result_response.json()
    test_result_id = test_result["id"]
    print(f"✅ Created test result: {test_result_id}")
    print(json.dumps(test_result, indent=2))

    # 2. Test cross-user access to test result (GET only, as PUT/DELETE are not supported)
    await test_cross_user_access(
        client,
        f"{TEST_RESULTS_URL}{test_result_id}",
        method="GET",
        other_cookies=other_cookies
    )
    
    # Note: We skip testing PUT/DELETE as they're not supported endpoints
    print(f"\n⚠️ Skipping PUT/DELETE tests for test results as these methods are not supported by the API")

    # 3. Get the test result
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

    return test_result_id

async def cleanup_resources(client: httpx.AsyncClient, cookies: dict, test_case_id: str, run_id: str, experiment_id: str, test_result_id: str = None):
    """Clean up all created resources."""
    print("\n🧹 Cleaning up resources...")

    # 1. Delete the run (which will cascade delete test results)
    print(f"\n📝 Deleting run {run_id}...")
    delete_run_response = await client.delete(f"{RUNS_URL}{run_id}", cookies=cookies)
    if delete_run_response.status_code != 200:
        print(f"❌ Delete run failed: {delete_run_response.status_code}")
        print(delete_run_response.text)
    else:
        print(f"✅ Deleted run and associated test results (cascade delete)")

    # 2. Delete the test case
    print(f"\n📝 Deleting test case {test_case_id}...")
    delete_test_case_response = await client.delete(f"{TEST_CASES_URL}{test_case_id}", cookies=cookies)
    if delete_test_case_response.status_code != 200:
        print(f"❌ Delete test case failed: {delete_test_case_response.status_code}")
        print(delete_test_case_response.text)
    else:
        print(f"✅ Deleted test case")

    # 3. Delete experiment
    print(f"\n📝 Deleting experiment {experiment_id}...")
    delete_url = urljoin(EXPERIMENTS_URL, experiment_id)
    delete_response = await client.delete(delete_url, cookies=cookies)
    
    if delete_response.status_code != 200:
        print(f"❌ Delete failed: {delete_response.status_code}")
        print(delete_response.text)
    else:
        print(f"✅ Deleted experiment")

async def cleanup_test_users(client: httpx.AsyncClient, superuser_cookies: dict):
    """Clean up test users from the database."""
    print("\n🧹 Cleaning up test users...")
    
    if not superuser_cookies:
        print("❌ No superuser cookies provided for cleanup")
        return
    
    # Delete other user
    print(f"\n📝 Deleting other user {OTHER_USER_EMAIL}...")
    try:
        delete_response = await client.delete(
            f"{BASE_URL}/users/by-email/{OTHER_USER_EMAIL}",
            cookies=superuser_cookies
        )
        if delete_response.status_code == 200:
            print(f"✅ Deleted other user {OTHER_USER_EMAIL}")
        elif delete_response.status_code == 404:
            print(f"ℹ️ Other user {OTHER_USER_EMAIL} not found")
        elif delete_response.status_code == 403:
            print(f"❌ Permission denied. Superuser authentication may have failed.")
            print(f"Response: {delete_response.text}")
            print(f"Superuser cookies: {dict(superuser_cookies)}")
        else:
            print(f"❌ Failed to delete other user: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
    except Exception as e:
        print(f"❌ Error deleting other user: {str(e)}")
    
    # Delete main user
    print(f"\n📝 Deleting main user {EMAIL}...")
    try:
        delete_response = await client.delete(
            f"{BASE_URL}/users/by-email/{EMAIL}",
            cookies=superuser_cookies
        )
        if delete_response.status_code == 200:
            print(f"✅ Deleted main user {EMAIL}")
        elif delete_response.status_code == 404:
            print(f"ℹ️ Main user {EMAIL} not found")
        elif delete_response.status_code == 403:
            print(f"❌ Permission denied. Superuser authentication may have failed.")
            print(f"Response: {delete_response.text}")
            print(f"Superuser cookies: {dict(superuser_cookies)}")
        else:
            print(f"❌ Failed to delete main user: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
    except Exception as e:
        print(f"❌ Error deleting main user: {str(e)}")

async def check_user_details(client: httpx.AsyncClient, email: str, cookies: dict) -> dict:
    """Check user details from the API."""
    print(f"\n📝 Checking details for user {email}...")
    try:
        response = await client.get(
            f"{BASE_URL}/users/me",
            cookies=cookies
        )
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ User details retrieved:")
            print(f"Email: {user_data.get('email')}")
            print(f"Is superuser: {user_data.get('is_superuser')}")
            print(f"Is active: {user_data.get('is_active')}")
            print(f"Is verified: {user_data.get('is_verified')}")
            return user_data
        else:
            print(f"❌ Failed to get user details: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error checking user details: {str(e)}")
        return None

async def update_user_to_superuser(client: httpx.AsyncClient, email: str, superuser_cookies: dict) -> bool:
    """Update an existing user to be a superuser."""
    print(f"\n📝 Updating user {email} to superuser...")
    
    # Check if the email matches the superuser email from env
    if email != SUPERUSER_EMAIL:
        print(f"❌ Cannot update user {email} to superuser - only {SUPERUSER_EMAIL} can be a superuser")
        return False
        
    try:
        # First get the user's current data
        user_data = await check_user_details(client, email, superuser_cookies)
        if not user_data:
            return False
            
        # Update the user to be a superuser using superuser's cookies
        update_response = await client.patch(  # Use PATCH as per FastAPI-Users convention
            f"{BASE_URL}/users/{user_data['id']}",  # Use the user's ID in the URL
            json={
                "is_superuser": True,
                "is_verified": True
            },
            cookies=superuser_cookies  # Use superuser's cookies
        )
        
        if update_response.status_code == 200:
            print(f"✅ Successfully updated user {email} to superuser")
            # Verify the update
            updated_data = await check_user_details(client, email, superuser_cookies)
            if updated_data and updated_data.get('is_superuser'):
                print("✅ Verified superuser status after update")
                return True
            else:
                print("❌ Failed to verify superuser status after update")
                return False
        else:
            print(f"❌ Failed to update user: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating user: {str(e)}")
        return False

async def ensure_superuser_exists(client: httpx.AsyncClient) -> dict:
    """Ensure superuser exists and return their cookies."""
    print("\n📝 Ensuring superuser exists...")
    
    # First try to register the superuser
    print(f"📝 Registering superuser {SUPERUSER_EMAIL}...")
    register_response = await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": SUPERUSER_EMAIL,
            "password": SUPERUSER_PASSWORD,
            "is_active": True,
            "is_superuser": True,
            "is_verified": True
        }
    )
    
    if register_response.status_code == 400 and "REGISTER_USER_ALREADY_EXISTS" in register_response.text:
        print(f"✅ Superuser {SUPERUSER_EMAIL} already exists")
    elif register_response.status_code not in [200, 201]:
        print(f"❌ Superuser registration failed: {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return None
    else:
        print(f"✅ Successfully registered superuser {SUPERUSER_EMAIL}")
    
    # Authenticate as superuser
    print(f"📝 Authenticating as superuser {SUPERUSER_EMAIL}...")
    auth_response = await client.post(
        LOGIN_URL,
        data={"username": SUPERUSER_EMAIL, "password": SUPERUSER_PASSWORD}
    )
    
    if auth_response.status_code not in [200, 204]:
        print(f"❌ Superuser authentication failed: {auth_response.status_code}")
        print(f"Response: {auth_response.text}")
        return None
    
    superuser_cookies = auth_response.cookies
    print(f"✅ Superuser authentication successful")
    
    # Verify superuser status
    user_data = await check_user_details(client, SUPERUSER_EMAIL, superuser_cookies)
    if not user_data:
        print("❌ Failed to verify superuser status")
        return None
    
    if not user_data.get('is_superuser'):
        print("❌ User is not a superuser, attempting to update...")
        if not await update_user_to_superuser(client, SUPERUSER_EMAIL, superuser_cookies):
            print("❌ Failed to update user to superuser")
            return None
    
    print("✅ Verified superuser status")
    return superuser_cookies

async def main():
    print("🧪 Testing Experiment API...")
    
    async with httpx.AsyncClient() as client:
        # 0. First ensure superuser exists and get their cookies
        superuser_cookies = await ensure_superuser_exists(client)
        if not superuser_cookies:
            print("❌ Failed to set up superuser")
            return
            
        # Clean up test users
        await cleanup_test_users(client, superuser_cookies)

        # 1. Test unauthorized access to protected endpoints (no cookies)
        print("\n🔒 Testing unauthorized access to protected endpoints...")
        await test_unauthorized_access(client, EXPERIMENTS_URL)
        await test_unauthorized_access(client, RUNS_URL)
        await test_unauthorized_access(client, TEST_RESULTS_URL)
        await test_unauthorized_access(client, TEST_CASES_URL)
        
        # 2. Register and authenticate main user
        print("\n📝 Registering main user...")
        register_response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": EMAIL,
                "password": PASSWORD,
                "is_active": True,
                "is_superuser": False,
                "is_verified": True
            }
        )
        
        if register_response.status_code == 400 and "REGISTER_USER_ALREADY_EXISTS" in register_response.text:
            print(f"✅ Main user {EMAIL} already exists")
        elif register_response.status_code not in [200, 201]:
            print(f"❌ Main user registration failed: {register_response.status_code}")
            print(f"Response: {register_response.text}")
            return
        else:
            print(f"✅ Successfully registered main user {EMAIL}")
        
        print("\n📝 Authenticating main user...")
        try:
            auth_response = await client.post(
                LOGIN_URL,
                data={"username": EMAIL, "password": PASSWORD}
            )
            
            if auth_response.status_code not in [200, 204]:
                print(f"❌ Authentication failed: {auth_response.status_code}")
                print(f"URL: {LOGIN_URL}")
                print(f"Response: {auth_response.text}")
                return
                
            cookies = auth_response.cookies
            print(f"✅ Authentication successful")
            print(f"Cookies: {dict(cookies)}")
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return

        # 3. Set up other user for cross-user access testing
        other_cookies = await setup_other_user(client)
        if not other_cookies:
            print("❌ Failed to set up other user for cross-user access testing")
            return

        # 4. Test experiments API
        experiment_id = await test_experiments_api(client, cookies, other_cookies)
        if not experiment_id:
            print("❌ Experiments API testing failed")
            return

        # 5. Test runs API
        run_id = await test_runs_api(client, cookies, experiment_id, other_cookies)
        if not run_id:
            print("❌ Runs API testing failed")
            return

        # 6. Test test cases API
        test_case_id = await test_test_cases_api(client, cookies, other_cookies)
        if not test_case_id:
            print("❌ Test cases API testing failed")
            return

        # 7. Test test results API
        test_result_id = await test_test_results_api(client, cookies, run_id, test_case_id, other_cookies)
        if not test_result_id:
            print("❌ Test results API testing failed")
            return

        # 8. Clean up all resources
        await cleanup_resources(client, cookies, test_case_id, run_id, experiment_id, test_result_id)
        
        # 9. Clean up test users
        await cleanup_test_users(client, superuser_cookies)
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    asyncio.run(main()) 