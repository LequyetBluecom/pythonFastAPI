#!/usr/bin/env python3
"""
Script kiểm tra admin user trong database
"""

from app.database import SessionLocal
from sqlalchemy import text

def check_admin():
    """Kiểm tra admin user"""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT id, name, email, role FROM users WHERE email = 'admin@school.com'"))
        admin = result.fetchone()
        
        if admin:
            print(f"✅ Admin user found:")
            print(f"   ID: {admin[0]}")
            print(f"   Name: {admin[1]}")
            print(f"   Email: {admin[2]}")
            print(f"   Role: {admin[3]} (type: {type(admin[3])})")
            return True
        else:
            print("❌ Admin user not found")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    check_admin()
