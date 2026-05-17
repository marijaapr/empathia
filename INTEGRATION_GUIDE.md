# Empathia + Supabase Integration Guide

## Overview

This guide covers complete integration of Empathia with Supabase, including authentication, user management, chat history, and mood tracking.

---

## Part 1: Supabase Project Setup

### Step 1: Create Supabase Account
1. Go to https://supabase.com
2. Click "Sign Up"
3. Sign up with email or GitHub
4. Verify your email

### Step 2: Create a New Project
1. After login, click "New Project"
2. Enter a project name: `empathia`
3. Set a strong database password (save this!)
4. Select your region (closest to you for best performance)
5. Wait for project creation (5-10 minutes)

### Step 3: Get Your API Credentials

Once project is created:

1. **Go to Project Settings** (gear icon bottom-left)
2. **Click "API"** in the left sidebar
3. Copy and save these credentials:
   - **Project URL** (looks like: `https://xxxxxxxxxxxx.supabase.co`)
   - **anon key** (public key, starts with `eyJ...`)
   - **service_role key** (private key, starts with `eyJ...`)

⚠️ **IMPORTANT**: Keep the `service_role key` secret! Never share it or commit to GitHub.

---

## Part 2: Create Database Tables

### Step 1: Open SQL Editor
1. In Supabase dashboard, click **"SQL Editor"** (left sidebar)
2. Click **"+ New Query"**

### Step 2: Create Users Table
Copy and paste this SQL, then click "Run":

```sql
create table if not exists public.users (
  id uuid primary key default auth.uid(),
  email text unique not null,
  username text,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

alter table public.users enable row level security;

create policy "Users can read own data"
  on public.users for select
  using (auth.uid() = id);

create policy "Users can update own data"
  on public.users for update
  using (auth.uid() = id);
```

### Step 3: Create Messages Table
Create a **new query** and paste:

```sql
create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null,
  content text not null,
  persona text,
  language text,
  mood_detected text,
  created_at timestamp with time zone default now()
);

alter table public.messages enable row level security;

create index messages_user_id_idx on public.messages(user_id);

create policy "Users can read own messages"
  on public.messages for select
  using (auth.uid() = user_id);

create policy "Users can insert own messages"
  on public.messages for insert
  with check (auth.uid() = user_id);
```

### Step 4: Create Mood Entries Table
Create another **new query**:

```sql
create table if not exists public.mood_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  mood text not null,
  intensity integer default 5,
  created_at timestamp with time zone default now()
);

alter table public.mood_entries enable row level security;

create index mood_entries_user_id_idx on public.mood_entries(user_id);

create policy "Users can read own moods"
  on public.mood_entries for select
  using (auth.uid() = user_id);

create policy "Users can insert own moods"
  on public.mood_entries for insert
  with check (auth.uid() = user_id);
```

✅ All tables created!

---

## Part 3: Setup Your Local Application

### Step 1: Install New Dependencies

```bash
cd /Users/marijaprastova/Desktop/empathia
pip install -r requirements.txt
```

This installs:
- `supabase` - Supabase Python client
- `python-jwt` - JWT token handling
- And other dependencies

### Step 2: Configure Environment Variables

1. Open or create `.env` file in the empathia directory
2. Add your Supabase credentials:

```env
# Supabase
SUPABASE_URL=https://your-project-name.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# OpenAI
OPENAI_API_KEY=sk-...

# Flask
SECRET_KEY=your-random-secret-key-here
PORT=5001
FLASK_DEBUG=True
```

**Where to find values:**
- `SUPABASE_URL` → Project Settings → API → Project URL
- `SUPABASE_ANON_KEY` → Project Settings → API → anon key
- `SUPABASE_SERVICE_KEY` → Project Settings → API → service_role key
- `OPENAI_API_KEY` → https://platform.openai.com/api-keys

---

## Part 4: Run the Application

### Step 1: Start the Server

```bash
cd /Users/marijaprastova/Desktop/empathia
source venv/bin/activate
python app_supabase.py
```

Expected output:
```
============================================================
🎯 Empathia - Emotional Support Assistant
============================================================
🌐 Starting Flask server on http://localhost:5001
📚 Database: Supabase (https://your-project.supabase.co)
🔧 Debug mode: True
============================================================
```

### Step 2: Open in Browser

Go to: **http://localhost:5001/login**

---

## Part 5: Features & API Endpoints

### Authentication Endpoints

#### Sign Up
```bash
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "username": "john_doe"
}

Response:
{
  "success": true,
  "message": "Signup successful! Please verify your email.",
  "user_id": "uuid...",
  "email": "user@example.com"
}
```

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}

Response:
{
  "success": true,
  "user_id": "uuid...",
  "email": "user@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "refresh_token": "eyJhbGciOiJIUzI1NiI..."
}
```

#### Logout
```bash
POST /api/auth/logout
Authorization: Bearer <access_token>

Response:
{
  "success": true
}
```

### Chat Endpoints (Requires Authentication)

#### Send Message
```bash
POST /api/chat
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "I'm feeling anxious today",
  "language": "en",
  "persona": "supportive_friend"
}

Response:
{
  "response": "I understand you're feeling anxious...",
  "mood_detected": "anxious",
  "emotion": "fear"
}
```

#### Get Chat History
```bash
GET /api/chat-history?limit=50
Authorization: Bearer <access_token>

Response:
{
  "messages": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "role": "user",
      "content": "Hello",
      "mood_detected": "neutral",
      "created_at": "2026-05-17T10:30:00Z"
    },
    ...
  ]
}
```

### Mood Tracking Endpoints (Requires Authentication)

#### Log Mood
```bash
POST /api/mood
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "mood": "happy",
  "intensity": 8,
  "language": "en"
}

Response:
{
  "message": "Great! Here's a reflection activity...",
  "mood": "happy",
  "intensity": 8
}
```

#### Get Mood History
```bash
GET /api/mood-history?days=30
Authorization: Bearer <access_token>

Response:
{
  "entries": [
    {
      "date": "2026-05-17",
      "mood": "happy",
      "count": 2,
      "avg_intensity": 8.5
    },
    ...
  ]
}
```

#### Get Weekly Summary
```bash
GET /api/weekly-summary
Authorization: Bearer <access_token>

Response:
{
  "summary": [
    {
      "mood": "happy",
      "count": 5,
      "avg_intensity": 8.2
    },
    ...
  ],
  "insight": "This week, your most frequent mood was happy (5 times)."
}
```

---

## Part 6: How Authentication Works

### Token Flow

1. **User logs in** → Server authenticates with Supabase
2. **Supabase returns tokens**:
   - `access_token` - Short-lived (1 hour), for API requests
   - `refresh_token` - Long-lived (7 days), for getting new access tokens
3. **Frontend stores tokens** in localStorage
4. **Every API request** includes: `Authorization: Bearer <access_token>`
5. **Token expires?** Use refresh_token to get a new one

### Security

- Tokens are JWT-based (industry standard)
- All endpoints with `@require_auth` verify the token
- Row-Level Security (RLS) in Supabase ensures users only see their own data
- Passwords are hashed by Supabase (never stored as plain text)

---

## Part 7: Database Schema

### users table
```
id (uuid, primary key)
email (text, unique)
username (text)
created_at (timestamp)
updated_at (timestamp)
```

### messages table
```
id (uuid, primary key)
user_id (uuid, references users)
role (text) - 'user' or 'assistant'
content (text) - the message
persona (text) - which persona was used
language (text) - 'en' or 'mk'
mood_detected (text) - mood detected in message
created_at (timestamp)
```

### mood_entries table
```
id (uuid, primary key)
user_id (uuid, references users)
mood (text) - 'happy', 'sad', 'anxious', 'angry', 'calm', 'neutral'
intensity (integer) - 1-10
created_at (timestamp)
```

---

## Part 8: Frontend Integration

### Login Page (templates/login.html)
- Sign up form
- Login form
- Stores tokens in localStorage
- Redirects to /chat on success

### Chat Page (templates/chat.html)
- Checks for auth token before loading
- Shows logged-in user
- Chat interface with auth headers
- Mood tracker
- Chat history
- Weekly stats

### JavaScript (static/script.js)
- Add auth headers: `Authorization: Bearer <token>`
- Handle token refresh
- Redirect to login on 401 error

Example:
```javascript
const token = localStorage.getItem('access_token');

fetch('/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ message, language, persona })
})
```

---

## Part 9: Troubleshooting

### "Invalid token" error
- Token expired → Refresh it
- Token incorrect → Log out and log in again

### Can't see chat history
- Check row-level security in Supabase
- Verify user_id matches auth.uid()

### Getting 401 on protected endpoints
- Missing `Authorization` header
- Token is invalid or expired
- Check that token is stored correctly

### Can't create tables
- Database password incorrect
- Missing permissions
- Try creating in SQL editor one by one

### API requests fail
- Check `.env` has all required variables
- Verify Supabase project is active
- Check internet connection

---

## Part 10: Going to Production

### Before deploying:

1. **Set FLASK_DEBUG=False**
```env
FLASK_DEBUG=False
```

2. **Use strong SECRET_KEY**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

3. **Store secrets securely**
   - Never commit .env to GitHub
   - Use environment variables on hosting platform
   - Use GitHub Secrets for CI/CD

4. **Enable HTTPS**
   - Required for secure token transmission
   - Use Let's Encrypt (free)

5. **Enable CORS** if frontend is separate:
```python
from flask_cors import CORS
CORS(app, origins=["https://yourdomain.com"])
```

6. **Set Supabase RLS policies** to match production needs

---

## Quick Reference

### File Structure
```
empathia/
├── app_supabase.py           # Main application (Supabase version)
├── app.py                    # Old SQLite version (backup)
├── requirements.txt          # Python dependencies
├── .env                      # Your credentials (gitignored)
├── .env.example              # Template for .env
├── SUPABASE_SETUP.md         # Database setup guide
├── INTEGRATION_GUIDE.md      # This file
├── database/
│   ├── db.py                # Old SQLite layer (backup)
│   └── supabase_db.py       # New Supabase layer
├── services/
│   ├── auth_service.py       # Supabase authentication
│   ├── openai_service.py     # ChatGPT integration
│   ├── emotion_service.py    # Emotion analysis
│   ├── reflection_service.py # Reflection prompts
│   └── safety_service.py     # Content safety
├── templates/
│   ├── login.html            # Login/Signup page
│   ├── chat.html             # Chat interface (auth-required)
│   └── index.html            # Old index (backup)
└── static/
    ├── script.js             # Frontend logic
    └── style.css             # Styling
```

### Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Supabase
python app_supabase.py

# Run with SQLite (old version)
python app.py

# Test API
curl http://localhost:5001/health
```

---

## Support

If you encounter issues:

1. Check Supabase documentation: https://supabase.com/docs
2. Check Flask documentation: https://flask.palletsprojects.com/
3. Review database tables in Supabase dashboard
4. Check browser console for frontend errors
5. Check terminal for backend errors

---

**Congratulations! Your Empathia app is now integrated with Supabase! 🎉**
