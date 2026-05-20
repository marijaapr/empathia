#!/usr/bin/env python3
"""
Test script to verify Supabase database connectivity and message storage
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test if we can connect to Supabase"""
    print("=" * 60)
    print("🧪 Testing Supabase Database Connection")
    print("=" * 60)
    
    try:
        # Test 1: Check if credentials are loaded
        print("\n✅ Test 1: Checking credentials...")
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not url or not service_key:
            print("❌ FAILED: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
            return False
        
        print(f"   ✓ SUPABASE_URL: {url[:50]}...")
        print(f"   ✓ SERVICE_KEY: {service_key[:20]}...")
        
        # Test 2: Try to query users table
        print("\n✅ Test 2: Checking users table...")
        from supabase import create_client
        supabase = create_client(url, service_key)
        
        response = supabase.table("users").select("id, email").limit(5).execute()
        print(f"   ✓ Found {len(response.data)} users in database")
        if response.data:
            for user in response.data[:3]:
                print(f"     - {user['email']} ({user['id'][:8]}...)")
        
        # Test 3: Check messages table
        print("\n✅ Test 3: Checking messages table...")
        response = supabase.table("messages").select("id, user_id, content").limit(10).execute()
        print(f"   ✓ Found {len(response.data)} messages in database")
        if response.data:
            for msg in response.data[:3]:
                content_preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
                print(f"     - User {msg['user_id'][:8]}...: '{content_preview}'")
        
        # Test 4: Check mood_entries table
        print("\n✅ Test 4: Checking mood_entries table...")
        response = supabase.table("mood_entries").select("id, user_id, mood").limit(10).execute()
        print(f"   ✓ Found {len(response.data)} mood entries in database")
        if response.data:
            for mood in response.data[:3]:
                print(f"     - User {mood['user_id'][:8]}...: {mood['mood']}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Database is connected.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n" + "=" * 60)
        print("❌ Database connection failed!")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)
