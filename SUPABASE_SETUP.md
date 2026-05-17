# Supabase Integration Setup Guide

## 1. Create Supabase Account
- Go to https://supabase.com
- Sign up with email or GitHub
- Create a new project
- Choose your region (closest to your location)
- Set a strong database password
- Wait for project to be created

## 2. Get Your Credentials
After project creation, go to **Project Settings** → **API**:
- Copy your **Project URL** (looks like: `https://xxxxx.supabase.co`)
- Copy your **anon key** (public key for frontend)
- Copy your **service_role key** (private key for backend)

## 3. Create Database Tables

Go to **SQL Editor** in Supabase and run these queries:

### Table 1: Users
```sql
create table users (
  id uuid primary key default auth.uid(),
  email text unique,
  username text unique,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

alter table users enable row level security;

create policy "Users can read own data"
  on users for select
  using (auth.uid() = id);

create policy "Users can update own data"
  on users for update
  using (auth.uid() = id);
```

### Table 2: Messages (Chat History)
```sql
create table messages (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  role text, -- 'user' or 'assistant'
  content text,
  persona text,
  language text,
  mood_detected text,
  created_at timestamp default now()
);

alter table messages enable row level security;

create policy "Users can read own messages"
  on messages for select
  using (auth.uid() = user_id);

create policy "Users can insert own messages"
  on messages for insert
  with check (auth.uid() = user_id);
```

### Table 3: Mood Entries
```sql
create table mood_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  mood text,
  intensity integer,
  created_at timestamp default now()
);

alter table mood_entries enable row level security;

create policy "Users can read own moods"
  on mood_entries for select
  using (auth.uid() = user_id);

create policy "Users can insert own moods"
  on mood_entries for insert
  with check (auth.uid() = user_id);
```

## 4. Environment Variables

Add to your `.env` file:
```
SUPABASE_URL=your_project_url_here
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
OPENAI_API_KEY=your_openai_key_here
```

## 5. Install Dependencies
```bash
pip install supabase
```

Done! Your database is ready.
