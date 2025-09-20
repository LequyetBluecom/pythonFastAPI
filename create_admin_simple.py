#!/usr/bin/env python3
"""
Script tạo tài khoản admin đơn giản
"""

import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal

def create_admin_directly():
    """Tạo admin trực tiếp trong database"""
    print("👤 Đang tạo tài khoản admin trực tiếp...")
    
    db = SessionLocal()
    try:
        # Kiểm tra xem admin đã tồn tại chưa
        result = db.execute(text("SELECT * FROM users WHERE email = 'admin@school.com'"))
        existing_admin = result.fetchone()
        
        if existing_admin:
            print("✅ Tài khoản admin đã tồn tại")
            print(f"   Email: {existing_admin[2]}")
            print(f"   Role: {existing_admin[4]}")
            return True
        
        # Tạo admin mới với SQL trực tiếp
        # Hash password: admin123 -> $2b$12$...
        hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8Q8Q8Q8"  # admin123
        
        db.execute(text("""
            INSERT INTO users (name, email, phone, role, hashed_password, is_active, created_at)
            VALUES ('System Administrator', 'admin@school.com', '0900000000', 'admin', :password, 1, NOW())
        """), {"password": hashed_password})
        
        db.commit()
        print("✅ Tài khoản admin đã được tạo thành công!")
        print("   Email: admin@school.com")
        print("   Password: admin123")
        print("   Role: admin")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi tạo admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_admin_token():
    """Lấy token từ tài khoản admin"""
    print("🔑 Đang lấy token từ tài khoản admin...")
    
    import requests
    
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
        
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                token_data = data.get("data", {})
                access_token = token_data.get("access_token")
                
                print("✅ Lấy token thành công!")
                print(f"   Access Token: {access_token[:50]}...")
                
                return access_token
            else:
                print(f"❌ Lỗi response: {data}")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Không thể kết nối server")
        print("💡 Hãy chạy: uvicorn app.main:app --reload")
        return None
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def test_with_token(token):
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
            print(f"    User info: {response.json()}")
    except Exception as e:
        print(f"  /auth/me: Error - {e}")
    
    # Test /students/
    try:
        response = requests.get("http://localhost:8000/api/v1/students/", headers=headers, timeout=10)
        print(f"  /students/: {response.status_code}")
    except Exception as e:
        print(f"  /students/: Error - {e}")

def main():
    """Hàm chính"""
    print("🚀 Tạo admin và test authentication")
    print("=" * 50)
    
    # Bước 1: Tạo admin
    if not create_admin_directly():
        return False
    
    # Bước 2: Lấy token
    token = get_admin_token()
    if not token:
        return False
    
    # Bước 3: Test với token
    test_with_token(token)
    
    print("\n✅ Hoàn thành!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
