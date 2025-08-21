#!/usr/bin/env python3
"""
Test script for the subscription system
Run this after setting up the database and starting the application
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "testuser",
    "fullname": "Test User",
    "email": "test@example.com",
    "phone": "1234567890",
    "user_type": "individual",
    "password": "testpassword123"
}

def test_subscription_system():
    """Test the complete subscription system"""
    print("🧪 Testing Subscription System")
    print("=" * 50)
    
    # Test 1: Register user
    print("\n1. Testing User Registration...")
    try:
        response = requests.post(f"{BASE_URL}/register", json=TEST_USER)
        if response.status_code == 200:
            print("✅ User registered successfully")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    # Test 2: Login
    print("\n2. Testing User Login...")
    try:
        login_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
        response = requests.post(f"{BASE_URL}/login", data=login_data)
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens["access_token"]
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Set headers for authenticated requests
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test 3: Get subscription plans
    print("\n3. Testing Subscription Plans...")
    try:
        response = requests.get(f"{BASE_URL}/plans", headers=headers)
        if response.status_code == 200:
            plans = response.json()
            print(f"✅ Found {len(plans)} subscription plans:")
            for plan in plans:
                print(f"   - {plan['name']}: ${plan['price']}/month")
        else:
            print(f"❌ Failed to get plans: {response.text}")
    except Exception as e:
        print(f"❌ Plans error: {e}")
    
    # Test 4: Get user usage (should be free tier)
    print("\n4. Testing User Usage (Free Tier)...")
    try:
        response = requests.get(f"{BASE_URL}/user/usage", headers=headers)
        if response.status_code == 200:
            usage = response.json()
            print(f"✅ Free tier limits:")
            print(f"   - Chats: {usage['chats_used']}/{usage['max_chats']}")
            print(f"   - Documents: {usage['documents_uploaded']}/{usage['max_documents']}")
            print(f"   - HR Documents: {usage['hr_documents_uploaded']}/{usage['max_hr_documents']}")
            print(f"   - Videos: {usage['video_uploads']}/{usage['max_video_uploads']}")
        else:
            print(f"❌ Failed to get usage: {response.text}")
    except Exception as e:
        print(f"❌ Usage error: {e}")
    
    # Test 5: Subscribe to Basic plan
    print("\n5. Testing Subscription to Basic Plan...")
    try:
        # Get plan ID first
        response = requests.get(f"{BASE_URL}/plans", headers=headers)
        if response.status_code == 200:
            plans = response.json()
            basic_plan = next((p for p in plans if p['name'] == 'Basic'), None)
            
            if basic_plan:
                subscribe_data = {"plan_id": basic_plan["id"]}
                response = requests.post(f"{BASE_URL}/subscribe", json=subscribe_data, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Subscribed to {result['plan_name']} plan")
                    print(f"   Valid until: {result['end_date']}")
                else:
                    print(f"❌ Subscription failed: {response.text}")
            else:
                print("❌ Basic plan not found")
        else:
            print(f"❌ Failed to get plans for subscription: {response.text}")
    except Exception as e:
        print(f"❌ Subscription error: {e}")
    
    # Test 6: Get updated usage (should show Basic plan limits)
    print("\n6. Testing Updated Usage (Basic Plan)...")
    try:
        response = requests.get(f"{BASE_URL}/user/usage", headers=headers)
        if response.status_code == 200:
            usage = response.json()
            print(f"✅ Basic plan limits:")
            print(f"   - Chats: {usage['chats_used']}/{usage['max_chats']}")
            print(f"   - Documents: {usage['documents_uploaded']}/{usage['max_documents']}")
            print(f"   - HR Documents: {usage['hr_documents_uploaded']}/{usage['max_hr_documents']}")
            print(f"   - Videos: {usage['video_uploads']}/{usage['max_video_uploads']}")
        else:
            print(f"❌ Failed to get updated usage: {response.text}")
    except Exception as e:
        print(f"❌ Updated usage error: {e}")
    
    # Test 7: Get user profile
    print("\n7. Testing User Profile...")
    try:
        response = requests.get(f"{BASE_URL}/profile", headers=headers)
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ User profile:")
            print(f"   - Username: {profile['username']}")
            print(f"   - Email: {profile['email']}")
            print(f"   - Subscribed: {profile['is_subscribed']}")
            if profile['subscription_end_date']:
                print(f"   - Subscription ends: {profile['subscription_end_date']}")
        else:
            print(f"❌ Failed to get profile: {response.text}")
    except Exception as e:
        print(f"❌ Profile error: {e}")
    
    # Test 8: Test chat usage tracking
    print("\n8. Testing Chat Usage Tracking...")
    try:
        response = requests.post(f"{BASE_URL}/chat", params={"query": "Hello, this is a test message"}, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat message sent successfully")
            if "usage" in result:
                usage = result["usage"]
                print(f"   - Usage updated: {usage['chats_used']}/{usage['max_chats']} chats")
        else:
            print(f"❌ Chat failed: {response.text}")
    except Exception as e:
        print(f"❌ Chat error: {e}")
    
    # Test 9: Cancel subscription
    print("\n9. Testing Subscription Cancellation...")
    try:
        response = requests.post(f"{BASE_URL}/cancel", headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Cancellation failed: {response.text}")
    except Exception as e:
        print(f"❌ Cancellation error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Subscription system test completed!")
    print("\nTo run the frontend:")
    print("cd Frontend && npm run dev")
    print("\nTo test the API endpoints:")
    print("curl -H 'Authorization: Bearer YOUR_TOKEN' http://localhost:8000/plans")

if __name__ == "__main__":
    test_subscription_system()
