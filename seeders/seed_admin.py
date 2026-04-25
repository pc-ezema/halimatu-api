#!/usr/bin/env python
"""Database seeder for superadmin role and superadmin user"""

import sys
import os

# Add the project root to path (two levels up from seeders folder)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database.database import SessionLocal, engine, Base
from app.models.role import Role
from app.models.admin import Admin
from app.services.admin_auth_service import hash_password

def seed_admin_database():
    """Seed the database with superadmin role and superadmin user"""
    db = SessionLocal()
    
    try:
        print("🌱 Starting admin database seeding...")
        print("=" * 50)
        
        # Create tables if they don't exist
        print("\n📦 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables ready")
        
        # ==================== CREATE SUPERADMIN ROLE ====================
        print("\n👑 Creating superadmin role...")
        
        superadmin_role = db.query(Role).filter(Role.name == "superadmin").first()
        if not superadmin_role:
            superadmin_role = Role(
                name="superadmin"
            )
            db.add(superadmin_role)
            db.commit()
            print("  ✓ Superadmin role created")
        else:
            print("  ⚠️  Superadmin role already exists")
        
        # ==================== CREATE SUPERADMIN USER ====================
        print("\n👤 Creating superadmin user...")
        
        superadmin = db.query(Admin).filter(Admin.email == "admin@halimatu-sadiyyah.com.ng").first()
        if not superadmin:
            superadmin = Admin(
                name="Super Admin",
                email="admin@halimatu-sadiyyah.com.ng",
                password=hash_password("SuperAdmin123!"),
                role_id=superadmin_role.id,
                status="active"
            )
            db.add(superadmin)
            db.commit()
            print("  ✓ Superadmin user created")
            print("\n📋 Login Credentials:")
            print("  Email: admin@halimatu-sadiyyah.com.ng")
            print("  Password: SuperAdmin123!")
        else:
            print("  ⚠️  Superadmin user already exists")
        
        # ==================== SUMMARY ====================
        print("\n" + "=" * 50)
        print("🎉 Seeding completed!")
        print("=" * 50)
        print(f"\n📊 Summary:")
        print(f"  - Roles: {db.query(Role).count()}")
        print(f"  - Admins: {db.query(Admin).count()}")
        print("\n💡 Note: Permissions will be auto-generated when the app starts!\n")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin_database()