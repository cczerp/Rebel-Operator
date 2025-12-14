#!/usr/bin/env python3
"""
Admin User Management Script - PostgreSQL Version
==================================================
Usage:
  python create_admin.py                    # List all users
  python create_admin.py <email>            # Promote user to admin by email
  python create_admin.py --username <name>  # Promote user to admin by username

Examples:
  python create_admin.py                              # Show all users
  python create_admin.py admin@example.com            # Make this email an admin
  python create_admin.py --username johndoe           # Make this username an admin
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import Database

def list_users(db):
    """List all users in the database"""
    cursor = db._get_cursor()
    cursor.execute("""
        SELECT id, username, email, is_admin, supabase_uid, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    users = cursor.fetchall()
    cursor.close()

    print("\n" + "="*80)
    print("CURRENT USERS:")
    print("="*80)

    if users:
        for user in users:
            admin_badge = "🔑 ADMIN" if user['is_admin'] else "👤 User"
            supabase_badge = "🔐 OAuth" if user.get('supabase_uid') else "🔒 Password"
            print(f"{admin_badge} | {supabase_badge}")
            print(f"  ID: {user['id']}")
            print(f"  Username: {user['username']}")
            print(f"  Email: {user['email']}")
            print(f"  Created: {user['created_at']}")
            print("-" * 80)
    else:
        print("No users found!")
        print("\nPlease register your first user at your app URL, then run:")
        print("  python create_admin.py <email>")

    print("="*80 + "\n")

def promote_to_admin(db, email=None, username=None):
    """Promote a user to admin status"""

    # Find user
    if email:
        print(f"🔍 Looking for user with email: {email}")
        user = db.get_user_by_email(email)
        search_field = "email"
        search_value = email
    elif username:
        print(f"🔍 Looking for user with username: {username}")
        user = db.get_user_by_username(username)
        search_field = "username"
        search_value = username
    else:
        print("❌ Please provide either email or username")
        return False

    if not user:
        print(f"❌ No user found with {search_field}: {search_value}")
        print("\nAvailable users:")
        list_users(db)
        return False

    # Check if already admin
    if user.get('is_admin'):
        print(f"ℹ️  User '{user['username']}' ({user['email']}) is already an admin!")
        return True

    # Promote to admin
    cursor = db._get_cursor()
    cursor.execute(
        "UPDATE users SET is_admin = true WHERE id = %s",
        (user['id'],)
    )
    db.conn.commit()
    cursor.close()

    print(f"🎉 SUCCESS! User '{user['username']}' ({user['email']}) is now an admin!")
    return True

def main():
    """Main entry point"""
    db = Database()

    try:
        # Parse arguments
        if len(sys.argv) == 1:
            # No arguments - list all users
            list_users(db)
        elif len(sys.argv) == 2:
            # One argument - assume it's an email
            email = sys.argv[1]
            promote_to_admin(db, email=email)
        elif len(sys.argv) == 3 and sys.argv[1] == '--username':
            # --username flag with username
            username = sys.argv[2]
            promote_to_admin(db, username=username)
        else:
            print("Invalid usage!")
            print(__doc__)
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
