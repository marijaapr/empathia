-- DROP old tables with foreign key constraints
DROP TABLE IF EXISTS session_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;

-- Now recreate with correct foreign keys pointing to auth.users
CREATE TABLE chat_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE session_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    persona TEXT,
    language TEXT,
    mood_detected TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_updated_at ON chat_sessions(updated_at);
CREATE INDEX idx_session_messages_session_id ON session_messages(session_id);
CREATE INDEX idx_session_messages_user_id ON session_messages(user_id);
CREATE INDEX idx_session_messages_created_at ON session_messages(created_at);

-- Disable RLS
ALTER TABLE chat_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE session_messages DISABLE ROW LEVEL SECURITY;
