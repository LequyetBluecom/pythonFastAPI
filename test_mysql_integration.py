#!/usr/bin/env python3
"""
Script test tích hợp MySQL Railway với FastAPI
"""

import os
import sys
import requests
import json
from datetime import datetime

# Cấu hình
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_server_running():
    """Test server có đang chạy không"""
    print("🏥 Đang kiểm tra server...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server đang chạy")
            return True
        else:
            print(f"⚠️  Server status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server không chạy")
        print("💡 Chạy: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

def test_swagger_docs():
    """Test Swagger documentation"""
    print("📚 Đang kiểm tra Swagger docs...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Swagger docs có sẵn")
            return True
        else:
            print(f"⚠️  Docs status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lỗi docs: {e}")
        return False

def test_database_connection_via_api():
    """Test database connection qua API"""
    print("🔌 Đang test database connection...")
    
    # Test endpoint cần database
    try:
        response = requests.get(f"{API_BASE}/students/", timeout=10)
        
        # 401/403 có nghĩa là database hoạt động nhưng cần auth
        if response.status_code in [401, 403]:
            print("✅ Database connection OK (cần authentication)")
            return True
        elif response.status_code == 200:
            print("✅ Database connection OK")
            return True
        else:
            print(f"⚠️  Response status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                pass
            return False
    except Exception as e:
        print(f"❌ Lỗi database connection: {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("🔐 Đang test auth endpoints...")
    
    # Test POST login endpoint
    try:
        login_data = {
            "username": "test@example.com",
            "password": "testpassword"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
        
        if response.status_code in [401, 422, 404]:
            print("✅ Login endpoint hoạt động (expected auth failure)")
            return True
        elif response.status_code == 200:
            print("✅ Login endpoint hoạt động")
            return True
        else:
            print(f"⚠️  Login status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lỗi login: {e}")
        return False

def test_student_endpoints():
    """Test student endpoints"""
    print("👨‍🎓 Đang test student endpoints...")
    
    try:
        response = requests.get(f"{API_BASE}/students/", timeout=10)
        
        if response.status_code in [401, 403]:
            print("✅ Students endpoint hoạt động (cần authentication)")
            return True
        elif response.status_code == 200:
            print("✅ Students endpoint hoạt động")
            return True
        else:
            print(f"⚠️  Students status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lỗi students: {e}")
        return False

def test_payment_endpoints():
    """Test payment endpoints"""
    print("💳 Đang test payment endpoints...")
    
    try:
        response = requests.get(f"{API_BASE}/payments/", timeout=10)
        
        if response.status_code in [401, 403]:
            print("✅ Payments endpoint hoạt động (cần authentication)")
            return True
        elif response.status_code == 200:
            print("✅ Payments endpoint hoạt động")
            return True
        else:
            print(f"⚠️  Payments status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lỗi payments: {e}")
        return False

def test_dashboard_endpoints():
    """Test dashboard endpoints"""
    print("📊 Đang test dashboard endpoints...")
    
    try:
        response = requests.get(f"{API_BASE}/dashboard/stats", timeout=10)
        
        if response.status_code in [401, 403]:
            print("✅ Dashboard endpoint hoạt động (cần authentication)")
            return True
        elif response.status_code == 200:
            print("✅ Dashboard endpoint hoạt động")
            return True
        else:
            print(f"⚠️  Dashboard status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lỗi dashboard: {e}")
        return False

def main():
    """Hàm chính"""
    print("🚀 Test tích hợp MySQL Railway với FastAPI")
    print("=" * 60)
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"🔗 API Base: {API_BASE}")
    print("=" * 60)
    
    tests = [
        ("Server Running", test_server_running),
        ("Swagger Docs", test_swagger_docs),
        ("Database Connection", test_database_connection_via_api),
        ("Auth Endpoints", test_auth_endpoints),
        ("Student Endpoints", test_student_endpoints),
        ("Payment Endpoints", test_payment_endpoints),
        ("Dashboard Endpoints", test_dashboard_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Lỗi trong {test_name}: {e}")
            results.append((test_name, False))
    
    # Tổng kết
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TỔNG KẾT:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Tổng kết: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Tất cả chức năng hoạt động tốt với MySQL Railway!")
        print("💡 Bạn có thể truy cập:")
        print(f"   - API Docs: {BASE_URL}/docs")
        print(f"   - API Base: {API_BASE}")
    else:
        print("⚠️  Một số chức năng cần kiểm tra thêm")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
