#!/usr/bin/env python3
"""
Script khởi tạo database MySQL cho Railway
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Import app modules
sys.path.append('.')
from app.core.config import settings
from app.database import engine, Base
from app.models import *  # Import all models

def create_database_tables():
    """Tạo tất cả bảng trong database"""
    print("🏗️  Đang tạo bảng database...")
    
    try:
        # Tạo tất cả bảng
        Base.metadata.create_all(bind=engine)
        print("✅ Tất cả bảng đã được tạo thành công!")
        return True
    except Exception as e:
        print(f"❌ Lỗi tạo bảng: {e}")
        return False

def test_database_connection():
    """Test kết nối database"""
    print("🔌 Đang test kết nối database...")
    
    try:
        with engine.connect() as connection:
            # Test basic connection
            result = connection.execute(text("SELECT 1 as test"))
            test_result = result.fetchone()
            print(f"✅ Kết nối database thành công: {test_result[0]}")
            
            # Test database info
            if settings.is_mysql:
                result = connection.execute(text("SELECT DATABASE() as db_name"))
                db_name = result.fetchone()
                print(f"📊 Database hiện tại: {db_name[0]}")
                
                result = connection.execute(text("SELECT VERSION() as version"))
                version = result.fetchone()
                print(f"📊 MySQL Version: {version[0]}")
            
            return True
    except Exception as e:
        print(f"❌ Lỗi kết nối database: {e}")
        return False

def list_tables():
    """Liệt kê các bảng trong database"""
    print("📋 Đang liệt kê các bảng...")
    
    try:
        with engine.connect() as connection:
            if settings.is_mysql:
                result = connection.execute(text("SHOW TABLES"))
                tables = result.fetchall()
                print(f"📊 Số bảng: {len(tables)}")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = result.fetchall()
                print(f"📊 Số bảng: {len(tables)}")
                for table in tables:
                    print(f"  - {table[0]}")
        return True
    except Exception as e:
        print(f"❌ Lỗi liệt kê bảng: {e}")
        return False

def main():
    """Hàm chính"""
    print("🚀 Khởi tạo database MySQL cho Railway")
    print("=" * 60)
    print(f"📊 Database URL: {settings.database_url}")
    print(f"📊 Database Type: {'MySQL' if settings.is_mysql else 'SQLite'}")
    print("=" * 60)
    
    # Test 1: Kết nối database
    if not test_database_connection():
        print("❌ Không thể kết nối database")
        return False
    
    # Test 2: Tạo bảng
    if not create_database_tables():
        print("❌ Không thể tạo bảng")
        return False
    
    # Test 3: Liệt kê bảng
    if not list_tables():
        print("❌ Không thể liệt kê bảng")
        return False
    
    print("=" * 60)
    print("🎉 Khởi tạo database thành công!")
    print("💡 Bạn có thể chạy ứng dụng FastAPI")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
