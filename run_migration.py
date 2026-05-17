#!/usr/bin/env python3
"""
Run SQL migrations to create chat_sessions and session_messages tables
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

SQL_MIGRATION = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS session_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    persona TEXT,
    language TEXT,
    mood_detected TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at);
CREATE INDEX IF NOT EXISTS idx_session_messages_session_id ON session_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_session_messages_user_id ON session_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_session_messages_created_at ON session_messages(created_at);

ALTER TABLE chat_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE session_messages DISABLE ROW LEVEL SECURITY;
"""

try:
    print("Running SQL migration...")
    response = supabase.rpc('exec_sql', {'sql': SQL_MIGRATION}).execute()
    print("✓ Migration completed successfully")
except Exception as e:
    print(f"Note: {e}")
    print("If error about exec_sql function, run migration manually in Supabase SQL Editor:")
    print(SQL_MIGRATION)
