#!/usr/bin/env python3
"""
Script kiểm tra database mà server đang sử dụng
"""

import requests
import json

def check_server_database():
    """Kiểm tra database của server"""
    print("🔍 Đang kiểm tra database của server...")
    
    try:
        # Test endpoint có thể cho biết database info
        response = requests.get("http://localhost:8000/api/v1/auth/me", timeout=5)
        print(f"   /auth/me status: {response.status_code}")
        
        # Test với token giả
        headers = {
            "Authorization": "Bearer fake-token",
            "Content-Type": "application/json"
        }
        
        response = requests.get("http://localhost:8000/api/v1/auth/me", headers=headers, timeout=5)
        print(f"   /auth/me with fake token: {response.status_code}")
        
        # Test database connection qua API
        response = requests.get("http://localhost:8000/api/v1/students/", timeout=5)
        print(f"   /students/ status: {response.status_code}")
        
        # Test login với debug info
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
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_server_database()
