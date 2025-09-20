#!/usr/bin/env python3
"""
Script test kết nối MySQL với Railway
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Cấu hình Railway MySQL
RAILWAY_MYSQL_URL = "mysql+pymysql://root:ghsuZYkyyMNrBjvIukthudfDXVpMzpgh@maglev.proxy.rlwy.net:10410/railway"

def test_mysql_connection():
    """Test kết nối MySQL với Railway"""
    print("🔌 Đang test kết nối MySQL với Railway...")
    print(f"URL: {RAILWAY_MYSQL_URL}")
    print("=" * 60)
    
    try:
        # Tạo engine với cấu hình MySQL
        engine = create_engine(
            RAILWAY_MYSQL_URL,
            echo=True,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "charset": "utf8mb4",
                "autocommit": True
            }
        )
        
        # Test kết nối
        with engine.connect() as connection:
            print("✅ Kết nối thành công!")
            
            # Test query cơ bản
            result = connection.execute(text("SELECT VERSION() as version"))
            version = result.fetchone()
            print(f"📊 MySQL Version: {version[0]}")
            
            # Test tạo database nếu chưa có
            try:
                connection.execute(text("CREATE DATABASE IF NOT EXISTS school_payment_db"))
                print("✅ Database 'school_payment_db' đã sẵn sàng")
            except Exception as e:
                print(f"⚠️  Lỗi tạo database: {e}")
            
            # Test sử dụng database
            connection.execute(text("USE school_payment_db"))
            print("✅ Đã chuyển sang database 'school_payment_db'")
            
            # Test tạo bảng test
            try:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS test_connection (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        message VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("✅ Bảng test đã được tạo")
                
                # Test insert
                connection.execute(text("""
                    INSERT INTO test_connection (message) VALUES ('Test connection successful')
                """))
                print("✅ Insert test thành công")
                
                # Test select
                result = connection.execute(text("SELECT * FROM test_connection ORDER BY id DESC LIMIT 1"))
                row = result.fetchone()
                print(f"✅ Select test: {row}")
                
            except Exception as e:
                print(f"⚠️  Lỗi test bảng: {e}")
            
        print("=" * 60)
        print("🎉 Kết nối MySQL Railway thành công!")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Lỗi kết nối database: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        return False

def test_app_database_config():
    """Test cấu hình database trong app"""
    print("\n🔧 Đang test cấu hình database trong app...")
    
    try:
        # Import app modules
        sys.path.append('.')
        from app.core.config import settings
        from app.database import engine
        
        print(f"📊 Database URL: {settings.database_url}")
        print(f"📊 DB Echo: {settings.DB_ECHO}")
        
        # Test engine
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_result = result.fetchone()
            print(f"✅ App database test: {test_result[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi test app database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Bắt đầu test kết nối MySQL Railway")
    print("=" * 60)
    
    # Test 1: Kết nối trực tiếp
    success1 = test_mysql_connection()
    
    # Test 2: Cấu hình app
    if success1:
        success2 = test_app_database_config()
        
        if success1 and success2:
            print("\n🎉 Tất cả test đều thành công!")
            print("💡 Bạn có thể chạy ứng dụng với MySQL Railway")
        else:
            print("\n⚠️  Một số test thất bại, kiểm tra cấu hình")
    else:
        print("\n❌ Kết nối database thất bại")
        print("💡 Kiểm tra thông tin kết nối Railway")
