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

        # 5. Test unauthorized access to specific run
        get_run_url = urljoin(RUNS_URL, run_id)
        await test_unauthorized_access(client, get_run_url)

        # 6. Get the run (with authentication)
        print(f"\n📝 Getting run {run_id}...")
        get_run_response = await client.get(get_run_url, cookies=cookies)
        if get_run_response.status_code != 200:
            print(f"❌ Get run failed: {get_run_response.status_code}")
            print(get_run_response.text)
        else:
            run = get_run_response.json()
            print(f"✅ Got run")
            print(json.dumps(run, indent=2))

        # 7. Test unauthorized access to update run
        update_payload = {"git_commit": "def456", "hyperparameters": {"model": "gpt-4", "temperature": 0.9}}
        await test_unauthorized_access(client, get_run_url, "PUT", update_payload)

        # 8. Update the run (with authentication)
        print(f"\n📝 Updating run {run_id}...")
        update_run_response = await client.put(get_run_url, json=update_payload, cookies=cookies)
        if update_run_response.status_code != 200:
            print(f"❌ Update run failed: {update_run_response.status_code}")
            print(update_run_response.text)
        else:
            updated_run = update_run_response.json()
            print(f"✅ Updated run")
            print(json.dumps(updated_run, indent=2))

        # 9. Test unauthorized access to delete run
        await test_unauthorized_access(client, get_run_url, "DELETE")

        # 10. Delete the run (with authentication)
        print(f"\n📝 Deleting run {run_id}...")
        delete_run_response = await client.delete(get_run_url, cookies=cookies)
        if delete_run_response.status_code != 200:
            print(f"❌ Delete run failed: {delete_run_response.status_code}")
            print(delete_run_response.text)
        else:
            print(f"✅ Deleted run")

        # 11. Verify run deletion
        print(f"\n📝 Verifying deletion of run {run_id}...")
        verify_run_response = await client.get(get_run_url, cookies=cookies)
        if verify_run_response.status_code == 404:
            print(f"✅ Run no longer exists (404 Not Found)")
            print(f"✅ Error message: {verify_run_response.json()['detail']}")
        else:
            print(f"❌ Unexpected response: {verify_run_response.status_code}")
            print(verify_run_response.text)

        # 12. Test unauthorized access to experiments
        await test_unauthorized_access(client, EXPERIMENTS_URL)
        await test_unauthorized_access(client, urljoin(EXPERIMENTS_URL, experiment_id))

        # 13. Get all experiments
        print("\n📝 Getting all experiments...")
        list_response = await client.get(EXPERIMENTS_URL, cookies=cookies)
        
        if list_response.status_code != 200:
            print(f"❌ List failed: {list_response.status_code}")
            print(list_response.text)
        else:
            experiments = list_response.json()
            print(f"✅ Got {len(experiments)} experiments")
            print(json.dumps(experiments, indent=2))
        
        # 14. Get single experiment
        print(f"\n📝 Getting experiment {experiment_id}...")
        get_url = urljoin(EXPERIMENTS_URL, experiment_id)
        get_response = await client.get(get_url, cookies=cookies)
        
        if get_response.status_code != 200:
            print(f"❌ Get failed: {get_response.status_code}")
            print(get_response.text)
        else:
            experiment = get_response.json()
            print(f"✅ Got experiment")
            print(json.dumps(experiment, indent=2))
        
        # 15. Update experiment
        print(f"\n📝 Updating experiment {experiment_id}...")
        update_url = urljoin(EXPERIMENTS_URL, experiment_id)
        update_response = await client.put(
            update_url,
            json={"name": "Updated Experiment", "description": "This is updated"},
            cookies=cookies
        )
        
        if update_response.status_code != 200:
            print(f"❌ Update failed: {update_response.status_code}")
            print(update_response.text)
        else:
            updated = update_response.json()
            print(f"✅ Updated experiment")
            print(json.dumps(updated, indent=2))
        
        # 16. Delete experiment
        print(f"\n📝 Deleting experiment {experiment_id}...")
        delete_url = urljoin(EXPERIMENTS_URL, experiment_id)
        delete_response = await client.delete(delete_url, cookies=cookies)
        
        if delete_response.status_code != 200:
            print(f"❌ Delete failed: {delete_response.status_code}")
            print(delete_response.text)
        else:
            print(f"✅ Deleted experiment")
        
        # 17. Verify deletion
        print(f"\n📝 Verifying deletion of {experiment_id}...")
        verify_response = await client.get(get_url, cookies=cookies)
        
        if verify_response.status_code == 404:
            print(f"✅ Experiment no longer exists (404 Not Found)")
            print(f"✅ Error message: {verify_response.json()['detail']}")
        else:
            print(f"❌ Unexpected response: {verify_response.status_code}")
            print(verify_response.text)
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    asyncio.run(main()) 