#!/usr/bin/env python3
"""
Script tạo admin user mới
"""

import os
import sys
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.core.security import get_password_hash

def delete_old_admin():
    """Xóa admin cũ"""
    print("🗑️  Đang xóa admin cũ...")
    
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM users WHERE email = 'admin@school.com'"))
        db.commit()
        print("✅ Admin cũ đã được xóa")
        return True
    except Exception as e:
        print(f"❌ Lỗi xóa admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def create_new_admin():
    """Tạo admin mới"""
    print("👤 Đang tạo admin mới...")
    
    db = SessionLocal()
    try:
        # Hash password
        password = "admin123"
        hashed_password = get_password_hash(password)
        
        # Tạo admin với role đúng
        db.execute(text("""
            INSERT INTO users (name, email, phone, role, hashed_password, is_active, created_at)
            VALUES ('System Administrator', 'admin@school.com', '0900000000', 'ADMIN', :password, 1, NOW())
        """), {"password": hashed_password})
        
        db.commit()
        print("✅ Admin mới đã được tạo!")
        print("   Email: admin@school.com")
        print("   Password: admin123")
        print("   Role: ADMIN")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi tạo admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_login():
    """Test login"""
    print("🔑 Đang test login...")
    
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
        print(f"❌ Lỗi login: {e}")
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
    print("🚀 Tạo admin mới và test authentication")
    print("=" * 50)
    
    # Bước 1: Xóa admin cũ
    if not delete_old_admin():
        return False
    
    # Bước 2: Tạo admin mới
    if not create_new_admin():
        return False
    
    # Bước 3: Test login
    token = test_login()
    if not token:
        return False
    
    # Bước 4: Test API
    test_api_with_token(token)
    
    print("\n✅ Hoàn thành!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
