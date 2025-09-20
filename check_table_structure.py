#!/usr/bin/env python3
"""
Script kiểm tra cấu trúc bảng users
"""

from app.database import SessionLocal
from sqlalchemy import text

def check_table_structure():
    """Kiểm tra cấu trúc bảng"""
    print("🔍 Đang kiểm tra cấu trúc bảng users...")
    
    db = SessionLocal()
    try:
        # Kiểm tra cấu trúc bảng
        result = db.execute(text("DESCRIBE users"))
        columns = result.fetchall()
        
        print("📊 Cấu trúc bảng users:")
        for column in columns:
            print(f"   {column[0]}: {column[1]} {column[2]} {column[3]} {column[4]} {column[5]}")
        
        # Kiểm tra enum values
        result = db.execute(text("SHOW COLUMNS FROM users LIKE 'role'"))
        role_column = result.fetchone()
        if role_column:
            print(f"\n📊 Role column: {role_column}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    check_table_structure()
