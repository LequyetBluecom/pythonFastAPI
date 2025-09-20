#!/usr/bin/env python3
"""
Script tạo tài khoản admin và lấy token
"""

import os
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import User, UserRole
from app.core.security import get_password_hash

def create_admin_user():
    """Tạo tài khoản admin"""
    print("👤 Đang tạo tài khoản admin...")
    
    db = SessionLocal()
    try:
        # Kiểm tra xem admin đã tồn tại chưa
        existing_admin = db.query(User).filter(User.email == "admin@school.com").first()
        if existing_admin:
            print("✅ Tài khoản admin đã tồn tại")
            print(f"   Email: {existing_admin.email}")
            print(f"   Role: {existing_admin.role}")
            print(f"   Active: {existing_admin.is_active}")
            return existing_admin
        
        # Tạo admin mới
        admin_user = User(
            name="System Administrator",
            email="admin@school.com",
            phone="0900000000",
            role=UserRole.ADMIN,
            hashed_password=get_password_hash("admin123"),
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Tài khoản admin đã được tạo thành công!")
        print(f"   Email: {admin_user.email}")
        print(f"   Password: admin123")
        print(f"   Role: {admin_user.role}")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Lỗi tạo admin: {e}")
        db.rollback()
        return None
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
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                token_data = data.get("data", {})
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                
                print("✅ Lấy token thành công!")
                print(f"   Access Token: {access_token[:50]}...")
                print(f"   Refresh Token: {refresh_token[:50]}...")
                print(f"   Token Type: {token_data.get('token_type')}")
                
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": token_data.get("token_type")
                }
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

def test_authenticated_endpoints(token):
    """Test các endpoint với authentication"""
    print("🧪 Đang test các endpoint với authentication...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        ("/auth/me", "GET", "Thông tin user hiện tại"),
        ("/students/", "GET", "Danh sách học sinh"),
        ("/payments/", "GET", "Danh sách thanh toán"),
        ("/invoices/", "GET", "Danh sách hóa đơn"),
        ("/dashboard/stats", "GET", "Thống kê dashboard")
    ]
    
    results = []
    
    for endpoint, method, description in endpoints:
        try:
            url = f"http://localhost:8000/api/v1{endpoint}"
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ {endpoint}: {description} - OK")
                results.append(True)
            elif response.status_code == 404:
                print(f"  ⚠️  {endpoint}: {description} - Not Found")
                results.append(False)
            else:
                print(f"  ❌ {endpoint}: {description} - {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"  ❌ {endpoint}: {description} - Error: {e}")
            results.append(False)
    
    return results

def main():
    """Hàm chính"""
    print("🚀 Tạo tài khoản admin và test authentication")
    print("=" * 60)
    
    # Bước 1: Tạo admin user
    admin_user = create_admin_user()
    if not admin_user:
        print("❌ Không thể tạo tài khoản admin")
        return False
    
    # Bước 2: Lấy token
    token_data = get_admin_token()
    if not token_data:
        print("❌ Không thể lấy token")
        return False
    
    # Bước 3: Test endpoints với token
    print("\n🧪 Test các endpoint với authentication:")
    results = test_authenticated_endpoints(token_data["access_token"])
    
    # Tổng kết
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ:")
    print("=" * 60)
    print(f"✅ Admin user: admin@school.com / admin123")
    print(f"✅ Access Token: {token_data['access_token'][:50]}...")
    print(f"📈 Endpoints: {passed}/{total} hoạt động")
    
    if passed == total:
        print("🎉 Tất cả chức năng hoạt động tốt!")
    else:
        print("⚠️  Một số endpoints cần kiểm tra thêm")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
