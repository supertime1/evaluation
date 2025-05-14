#!/usr/bin/env python3
"""
Simple script to test the experiment API endpoints manually.
Usage: python -m tests.manual_tests.test_experiments_api
"""

import asyncio
import json
import httpx
from urllib.parse import urljoin

# API base URL - update this to match your server
BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = f"{BASE_URL}/auth/jwt/login"
EXPERIMENTS_URL = f"{BASE_URL}/experiments/"

# Test user credentials
EMAIL = "luzhang@fortinet-us.com"
PASSWORD = "strongpassword"

async def main():
    print("🧪 Testing Experiment API...")
    
    # 1. Authenticate
    print("\n📝 Authenticating...")
    async with httpx.AsyncClient() as client:
        auth_response = await client.post(
            AUTH_URL,
            data={"username": EMAIL, "password": PASSWORD}
        )
        
        if auth_response.status_code not in [200, 204]:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            print(auth_response.text)
            return
            
        cookies = auth_response.cookies
        print(f"✅ Authentication successful")
        
        # 2. Create an experiment
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
        
        # 3. Get all experiments
        print("\n📝 Getting all experiments...")
        list_response = await client.get(EXPERIMENTS_URL, cookies=cookies)
        
        if list_response.status_code != 200:
            print(f"❌ List failed: {list_response.status_code}")
            print(list_response.text)
        else:
            experiments = list_response.json()
            print(f"✅ Got {len(experiments)} experiments")
            print(json.dumps(experiments, indent=2))
        
        # 4. Get single experiment
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
        
        # 5. Update experiment
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
        
        # 6. Delete experiment
        print(f"\n📝 Deleting experiment {experiment_id}...")
        delete_url = urljoin(EXPERIMENTS_URL, experiment_id)
        delete_response = await client.delete(delete_url, cookies=cookies)
        
        if delete_response.status_code != 200:
            print(f"❌ Delete failed: {delete_response.status_code}")
            print(delete_response.text)
        else:
            print(f"✅ Deleted experiment")
        
        # 7. Verify deletion
        print(f"\n📝 Verifying deletion of {experiment_id}...")
        verify_response = await client.get(f"{EXPERIMENTS_URL}/{experiment_id}", cookies=cookies)
        
        if verify_response.status_code == 404:
            print(f"✅ Experiment no longer exists (404 Not Found)")
        else:
            print(f"❌ Unexpected response: {verify_response.status_code}")
            print(verify_response.text)
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    asyncio.run(main()) 