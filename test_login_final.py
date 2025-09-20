#!/usr/bin/env python3
"""
Script test login cuối cùng
"""

import requests
import json

def test_login():
    """Test login"""
    print("🔑 Đang test login cuối cùng...")
    
    login_data = {
        "email": "admin@school.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                token_data = data.get("data", {})
                access_token = token_data.get("access_token")
                print(f"✅ Token: {access_token[:50]}...")
                return access_token
        return None
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def test_api_with_token(token):
    """Test API với token"""
    print("🧪 Đang test API với token...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test /auth/me
    try:
        response = requests.get("http://localhost:8000/api/v1/auth/me", headers=headers, timeout=10)
        print(f"  /auth/me: {response.status_code}")
        if response.status_code == 200:
            user_info = response.json()
            print(f"    User: {user_info.get('data', {}).get('name')}")
            print(f"    Role: {user_info.get('data', {}).get('role')}")
    except Exception as e:
        print(f"  /auth/me: Error - {e}")
    
    # Test /students/
    try:
        response = requests.get("http://localhost:8000/api/v1/students/", headers=headers, timeout=10)
        print(f"  /students/: {response.status_code}")
        if response.status_code == 200:
            students = response.json()
            print(f"    Students: {len(students.get('data', []))}")
    except Exception as e:
        print(f"  /students/: Error - {e}")
    
    # Test /payments/
    try:
        response = requests.get("http://localhost:8000/api/v1/payments/", headers=headers, timeout=10)
        print(f"  /payments/: {response.status_code}")
    except Exception as e:
        print(f"  /payments/: Error - {e}")

def main():
    """Hàm chính"""
    print("🚀 Test login cuối cùng")
    print("=" * 40)
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Không thể lấy token")
        return False
    
    # Test API
    test_api_with_token(token)
    
    print("\n✅ Hoàn thành!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
