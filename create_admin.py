"""
Quick script to create admin account or check existing users
Run this with: python create_admin.py
"""
import sys
from werkzeug.security import generate_password_hash
from src.database.db import get_db

# Get database connection
db = get_db()

# Check existing users
users = db.get_all_users(include_inactive=True)

print("\n" + "="*60)
print("CURRENT USERS:")
print("="*60)
if users:
    for user in users:
        admin_status = "ADMIN" if user.get('is_admin') else "User"
        active_status = "Active" if user.get('is_active') else "Inactive"
        print(f"ID: {user['id']} | Username: {user['username']} | Email: {user['email']} | Role: {admin_status} | Status: {active_status}")
else:
    print("No users found!")
print("="*60)

# Create admin if no users exist
if len(users) == 0:
    print("\nCreating default admin account...")
    password_hash = generate_password_hash('admin')

    # Create user with admin privileges
    user_id = db.create_user('admin', 'admin@resellgenius.local', password_hash)

    # Make user admin (toggle from False to True)
    db.toggle_user_admin(user_id)

    print("\n✓ Admin account created!")
    print("Username: admin")
    print("Password: admin")
    print("\nYou can now login at http://localhost:5000/login")
else:
    print("\nUsers already exist.")
    print("\nTo make an existing user admin, run:")
    print(f"  python create_admin.py USERNAME")

print("="*60 + "\n")

# If argument provided, make that user admin
if len(sys.argv) > 1:
    username = sys.argv[1]
    user = db.get_user_by_username(username)

    if user:
        # Toggle admin status (or just set to True)
        if not user.get('is_admin'):
            db.toggle_user_admin(user['id'])
            print(f"\n✓ User '{username}' is now an admin!")
        else:
            print(f"\nℹ User '{username}' is already an admin.")
    else:
        print(f"\n✗ User '{username}' not found")
