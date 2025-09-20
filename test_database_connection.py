#!/usr/bin/env python3
"""
Script test database connection trong app
"""

import os
import sys
from app.database import SessionLocal
from app.models import User, UserRole
from sqlalchemy import text

def test_database_in_app():
    """Test database connection trong app"""
    print("🔍 Đang test database connection trong app...")
    
    # Set environment variable để sử dụng MySQL
    os.environ["DATABASE_URL"] = "mysql+pymysql://root:ghsuZYkyyMNrBjvIukthudfDXVpMzpgh@maglev.proxy.rlwy.net:10410/railway"
    
    db = SessionLocal()
    try:
        # Test connection
        result = db.execute(text("SELECT 1 as test"))
        test_result = result.fetchone()
        print(f"✅ Database connection: {test_result[0]}")
        
        # Test user query
        user = db.query(User).filter(User.email == "admin@school.com").first()
        if user:
            print(f"✅ User found:")
            print(f"   ID: {user.id}")
            print(f"   Name: {user.name}")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role}")
            print(f"   Role == UserRole.ADMIN: {user.role == UserRole.ADMIN}")
            print(f"   Is active: {user.is_active}")
        else:
            print("❌ User not found")
            
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_database_in_app()
