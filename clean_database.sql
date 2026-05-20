-- ============================================================================
-- CLEAN DATABASE - Delete all data but keep table structure
-- ============================================================================
-- Run this in Supabase SQL Editor to reset everything
-- WARNING: This will delete ALL data from all tables!

-- Disable triggers temporarily (optional, but helps with performance)
SET session_replication_role = 'replica';

-- Delete in correct order (respecting foreign key constraints)
-- Start with child tables that reference others

-- 1. Delete notifications (references psychologist_chat_requests, psychologist_sessions, users)
DELETE FROM public.notifications;

-- 2. Delete psychologist_session_messages (references psychologist_sessions, users)
DELETE FROM public.psychologist_session_messages;

-- 3. Delete psychologist_ratings (references psychologist_profiles, users)
DELETE FROM public.psychologist_ratings;

-- 4. Delete psychologist_sessions (references psychologist_chat_requests, psychologist_profiles, chat_sessions, users)
DELETE FROM public.psychologist_sessions;

-- 5. Delete session_messages (references chat_sessions, users)
DELETE FROM public.session_messages;

-- 6. Delete messages (references users)
DELETE FROM public.messages;

-- 7. Delete mood_entries (references users)
DELETE FROM public.mood_entries;

-- 8. Delete psychologist_chat_requests (references psychologist_profiles, chat_sessions, users)
DELETE FROM public.psychologist_chat_requests;

-- 9. Delete chat_sessions (references psychologist_profiles, users)
DELETE FROM public.chat_sessions;

-- 10. Delete psychologist_profiles (references users)
DELETE FROM public.psychologist_profiles;

-- 11. Delete users (this is in public.users, not auth.users)
DELETE FROM public.users;

-- 12. Delete auth.users (THIS WILL DELETE ALL AUTHENTICATION DATA)
-- Be careful! This deletes actual user accounts
DELETE FROM auth.users;

-- Re-enable triggers
SET session_replication_role = 'origin';

-- Verify all tables are empty
SELECT 'notifications' as table_name, COUNT(*) as count FROM public.notifications
UNION ALL
SELECT 'psychologist_session_messages', COUNT(*) FROM public.psychologist_session_messages
UNION ALL
SELECT 'psychologist_ratings', COUNT(*) FROM public.psychologist_ratings
UNION ALL
SELECT 'psychologist_sessions', COUNT(*) FROM public.psychologist_sessions
UNION ALL
SELECT 'session_messages', COUNT(*) FROM public.session_messages
UNION ALL
SELECT 'messages', COUNT(*) FROM public.messages
UNION ALL
SELECT 'mood_entries', COUNT(*) FROM public.mood_entries
UNION ALL
SELECT 'psychologist_chat_requests', COUNT(*) FROM public.psychologist_chat_requests
UNION ALL
SELECT 'chat_sessions', COUNT(*) FROM public.chat_sessions
UNION ALL
SELECT 'psychologist_profiles', COUNT(*) FROM public.psychologist_profiles
UNION ALL
SELECT 'users', COUNT(*) FROM public.users
UNION ALL
SELECT 'auth.users', COUNT(*) FROM auth.users;
