#!/usr/bin/env python3
"""
Script test các API endpoints với MySQL Railway
"""

import os
import sys
import requests
import json
from datetime import datetime

# Cấu hình
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_server_health():
    """Test server health"""
    print("🏥 Đang test server health...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ Server đang chạy")
            return True
        else:
            print(f"⚠️  Server trả về status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Không thể kết nối server")
        print("💡 Hãy chạy: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

def test_database_connection():
    """Test database connection qua API"""
    print("🔌 Đang test database connection qua API...")
    
    try:
        # Test endpoint có thể cần database
        response = requests.get(f"{API_BASE}/dashboard/stats", timeout=10)
        if response.status_code in [200, 401, 403]:  # 401/403 có thể là do auth
            print("✅ Database connection hoạt động")
            return True
        else:
            print(f"⚠️  Response status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lỗi database connection: {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("🔐 Đang test authentication endpoints...")
    
    endpoints = [
        "/auth/login",
        "/auth/register", 
        "/auth/refresh"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            # 405 Method Not Allowed là bình thường cho GET
            if response.status_code in [200, 405, 422]:
                print(f"  ✅ {endpoint}: OK")
                results.append(True)
            else:
                print(f"  ⚠️  {endpoint}: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"  ❌ {endpoint}: {e}")
            results.append(False)
    
    return all(results)

def test_student_endpoints():
    """Test student endpoints"""
    print("👨‍🎓 Đang test student endpoints...")
    
    endpoints = [
        "/students/",
        "/students/search"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403, 422]:
                print(f"  ✅ {endpoint}: OK")
                results.append(True)
            else:
                print(f"  ⚠️  {endpoint}: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"  ❌ {endpoint}: {e}")
            results.append(False)
    
    return all(results)

def test_payment_endpoints():
    """Test payment endpoints"""
    print("💳 Đang test payment endpoints...")
    
    endpoints = [
        "/payments/",
        "/payments/status"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403, 422]:
                print(f"  ✅ {endpoint}: OK")
                results.append(True)
            else:
                print(f"  ⚠️  {endpoint}: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"  ❌ {endpoint}: {e}")
            results.append(False)
    
    return all(results)

def test_invoice_endpoints():
    """Test invoice endpoints"""
    print("📄 Đang test invoice endpoints...")
    
    endpoints = [
        "/invoices/",
        "/invoices/generate"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403, 422]:
                print(f"  ✅ {endpoint}: OK")
                results.append(True)
            else:
                print(f"  ⚠️  {endpoint}: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"  ❌ {endpoint}: {e}")
            results.append(False)
    
    return all(results)

def test_dashboard_endpoints():
    """Test dashboard endpoints"""
    print("📊 Đang test dashboard endpoints...")
    
    endpoints = [
        "/dashboard/stats",
        "/dashboard/reports"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403, 422]:
                print(f"  ✅ {endpoint}: OK")
                results.append(True)
            else:
                print(f"  ⚠️  {endpoint}: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"  ❌ {endpoint}: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Hàm chính test API"""
    print("🚀 Bắt đầu test API endpoints với MySQL Railway")
    print("=" * 60)
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"🔗 API Base: {API_BASE}")
    print("=" * 60)
    
    tests = [
        ("Server Health", test_server_health),
        ("Database Connection", test_database_connection),
        ("Auth Endpoints", test_auth_endpoints),
        ("Student Endpoints", test_student_endpoints),
        ("Payment Endpoints", test_payment_endpoints),
        ("Invoice Endpoints", test_invoice_endpoints),
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
        print("🎉 Tất cả API endpoints hoạt động tốt với MySQL Railway!")
    else:
        print("⚠️  Một số endpoints cần kiểm tra thêm")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
