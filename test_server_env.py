#!/usr/bin/env python3
"""
Script test environment variable của server
"""

import requests

def test_server_environment():
    """Test server environment"""
    print("🔍 Đang test server environment...")
    
    try:
        # Test server health
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server đang chạy")
        else:
            print(f"⚠️  Server status: {response.status_code}")
            return False
        
        # Test database connection qua API
        response = requests.get("http://localhost:8000/api/v1/students/", timeout=5)
        print(f"   /students/ status: {response.status_code}")
        
        # Test auth endpoint
        login_data = {
            "email": "admin@school.com",
            "password": "admin123"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            timeout=10
        )
        
        print(f"   /auth/login status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_server_environment()
