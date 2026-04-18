#!/usr/bin/env python3
"""
setup_db.py — One-time MongoDB setup script
Run this ONCE to create collections, indexes, and seed initial data.

Usage:
    cd f:\Rafay\resume_checker\backend
    venv\Scripts\activate
    python setup_db.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
from db.mongo import get_db, setup_indexes

# ── Run ────────────────────────────────────────────────────────────────────────

def main():
    print("🔧  Connecting to MongoDB...")
    try:
        db = get_db()
        # Ping to confirm connection
        db.client.admin.command("ping")
        print(f"✅  Connected to: {db.name}")
    except Exception as e:
        print(f"❌  Could not connect to MongoDB: {e}")
        print("    Make sure MongoDB is running: mongod --dbpath C:\\data\\db")
        sys.exit(1)

    # ── Create all 5 collections ───────────────────────────────────────────────
    print("\n📂  Creating collections...")
    existing = db.list_collection_names()
    collections = {
        "users":    "Stores user accounts and authentication info",
        "resumes":  "Stores uploaded resume text (encrypted)",
        "reports":  "Stores analysis results and AI suggestions",
        "sessions": "Stores refresh tokens (TTL auto-expire)",
        "messages": "Stores AI chat history per user",
    }

    for name, desc in collections.items():
        if name not in existing:
            db.create_collection(name)
            print(f"  ✅  Created: {name:10s}  — {desc}")
        else:
            print(f"  ℹ️   Exists:  {name:10s}  — {desc}")

    # ── Create indexes ─────────────────────────────────────────────────────────
    print("\n📇  Creating indexes...")
    setup_indexes()

    # ── Seed: Default admin user ───────────────────────────────────────────────
    print("\n👤  Checking seed data...")
    if not db.users.find_one({"email": "admin@resumechecker.local"}):
        import bcrypt
        admin_pw = bcrypt.hashpw(b"Admin@1234", bcrypt.gensalt())
        db.users.insert_one({
            "name":          "Admin",
            "email":         "admin@resumechecker.local",
            "passwordHash":  admin_pw,
            "role":          "admin",
            "industry":      None,
            "createdAt":     datetime.now(timezone.utc),
            "lastLoginAt":   None,
            "loginAttempts": 0,
            "lockedUntil":   None,
        })
        print("  ✅  Seeded: admin user (email: admin@resumechecker.local, password: Admin@1234)")
        print("  ⚠️   CHANGE THIS PASSWORD before going to production!")
    else:
        print("  ℹ️   Admin user already exists")

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n✨  Database ready! Collections:")
    for name in db.list_collection_names():
        count = db[name].count_documents({})
        print(f"  📁  {name:12s} {count} documents")

    print(f"\n🚀  You can now run: python app.py")


if __name__ == "__main__":
    main()
