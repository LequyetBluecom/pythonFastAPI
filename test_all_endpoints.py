#!/usr/bin/env python3
"""
Script test tất cả endpoints với token
"""

import requests
import json

def get_admin_token():
    """Lấy token admin"""
    print("🔑 Đang lấy token admin...")
    
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
                print(f"✅ Token: {access_token[:50]}...")
                return access_token
        return None
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def test_all_endpoints(token):
    """Test tất cả endpoints"""
    print("🧪 Đang test tất cả endpoints...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        ("/auth/me", "GET", "Thông tin user hiện tại"),
        ("/students/", "GET", "Danh sách học sinh"),
        ("/students/search", "GET", "Tìm kiếm học sinh"),
        ("/payments/", "GET", "Danh sách thanh toán"),
        ("/payments/status", "GET", "Trạng thái thanh toán"),
        ("/invoices/", "GET", "Danh sách hóa đơn"),
        ("/invoices/generate", "GET", "Tạo hóa đơn"),
        ("/dashboard/stats", "GET", "Thống kê dashboard"),
        ("/dashboard/reports", "GET", "Báo cáo dashboard"),
        ("/orders/", "GET", "Danh sách đơn hàng"),
        ("/users/", "GET", "Danh sách người dùng")
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
            elif response.status_code == 422:
                print(f"  ⚠️  {endpoint}: {description} - Validation Error")
                results.append(False)
            else:
                print(f"  ❌ {endpoint}: {description} - {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"  ❌ {endpoint}: {description} - Error: {e}")
            results.append(False)
    
    return results

def test_specific_endpoints(token):
    """Test các endpoint cụ thể"""
    print("\n🔍 Đang test các endpoint cụ thể...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test /auth/me
    try:
        response = requests.get("http://localhost:8000/api/v1/auth/me", headers=headers, timeout=10)
        if response.status_code == 200:
            user_info = response.json()
            print(f"  ✅ /auth/me: User info retrieved")
            print(f"     User: {user_info.get('data', {}).get('name')}")
            print(f"     Role: {user_info.get('data', {}).get('role')}")
            print(f"     Email: {user_info.get('data', {}).get('email')}")
    except Exception as e:
        print(f"  ❌ /auth/me: Error - {e}")
    
    # Test /students/
    try:
        response = requests.get("http://localhost:8000/api/v1/students/", headers=headers, timeout=10)
        if response.status_code == 200:
            students = response.json()
            print(f"  ✅ /students/: Students retrieved")
            print(f"     Count: {len(students.get('data', []))}")
        else:
            print(f"  ⚠️  /students/: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ /students/: Error - {e}")
    
    # Test /payments/
    try:
        response = requests.get("http://localhost:8000/api/v1/payments/", headers=headers, timeout=10)
        if response.status_code == 200:
            payments = response.json()
            print(f"  ✅ /payments/: Payments retrieved")
            print(f"     Count: {len(payments.get('data', []))}")
        else:
            print(f"  ⚠️  /payments/: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ /payments/: Error - {e}")

def main():
    """Hàm chính"""
    print("🚀 Test tất cả endpoints với authentication")
    print("=" * 60)
    
    # Bước 1: Lấy token
    token = get_admin_token()
    if not token:
        print("❌ Không thể lấy token")
        return False
    
    # Bước 2: Test tất cả endpoints
    results = test_all_endpoints(token)
    
    # Bước 3: Test các endpoint cụ thể
    test_specific_endpoints(token)
    
    # Tổng kết
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TỔNG KẾT:")
    print("=" * 60)
    print(f"✅ Admin Token: {token[:50]}...")
    print(f"📈 Endpoints: {passed}/{total} hoạt động")
    
    if passed == total:
        print("🎉 Tất cả endpoints hoạt động tốt!")
    else:
        print("⚠️  Một số endpoints cần kiểm tra thêm")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
