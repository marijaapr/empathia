# Empathia - Emotional Support & Self-Reflection Assistant

> A bilingual Flask application powered by OpenAI API and Supabase, providing emotional support, mood tracking, and reflection prompts.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![Supabase](https://img.shields.io/badge/Supabase-2.0.0-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Features

- **🔐 User Authentication**: Sign up, login, logout with JWT tokens
- **💬 AI Chat**: Powered by OpenAI GPT with bilingual support (English & Macedonian)
- **😊 Mood Tracking**: Log moods and track emotional patterns over time
- **📊 Analytics**: View weekly mood summaries and emotional insights
- **💾 Chat History**: Persistent conversation storage with Supabase
- **🎭 Multiple Personas**: Choose from different support personas
- **🛡️ Safety Filters**: Content safety checks for sensitive messages
- **🌍 Bilingual**: Full support for English and Macedonian

## 📋 Prerequisites

- **Python 3.9+**
- **Supabase account** (free at https://supabase.com)
- **OpenAI API key** (get at https://platform.openai.com/api-keys)
- **Virtual environment** (recommended)

## 🚀 Quick Start

### 1. Navigate to project
```bash
cd /Users/marijaprastova/Desktop/empathia
```

### 2. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Supabase

1. Create account at https://supabase.com
2. Create new project
3. Run SQL in the Supabase SQL Editor (see `run_migration.py` for chat session tables)
4. Copy API credentials to `.env`

### 5. Configure environment variables
```bash
cp .env.example .env
```

Edit `.env` with your Supabase & OpenAI credentials:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
PORT=5001
FLASK_DEBUG=True
```

### 6. Run the application
```bash
python app.py
```

Server starts at: **http://localhost:5001/login**

### 7. Create account and start chatting!

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[README.md](./README.md)** | Setup, API overview, and project structure |
| **[.env.example](./.env.example)** | Environment variables template |

## 🏗️ Project Structure

```
empathia/
├── app.py                       # Flask application (single entry point)
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── routes/
│   └── psychologist_routes.py  # Psychologist API blueprint
├── database/
│   └── supabase_db.py          # Supabase database operations
├── services/
│   ├── auth_service.py         # Supabase authentication & JWT
│   ├── openai_service.py       # ChatGPT integration
│   ├── emotion_service.py      # Emotion detection
│   ├── reflection_service.py   # Reflection prompts
│   └── safety_service.py       # Content safety
├── templates/
│   ├── landing.html            # Landing page
│   ├── login.html              # Login / sign up
│   ├── chat.html               # Chat interface
│   └── psychologist/           # Psychologist dashboard (signup via /login)
└── static/
    ├── api.js                  # Shared apiFetch() helper
    ├── login.js                # Login & signup page logic
    ├── script.js               # Chat UI logic
    ├── style.css               # Main styling
    └── psychologist/           # Dashboard JS/CSS
```

## 🔌 API Endpoints

### Authentication (Public)
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user  
- `POST /api/auth/refresh` - Refresh access token

### Chat
- `POST /api/chat-sessions/<id>/chat` - Send message in a session
- `GET /api/chat-sessions` - List user chat sessions
- `GET /api/chat-history` - Legacy global message history

### Mood (Protected - requires auth token)
- `POST /api/mood` - Log mood entry
- `GET /api/mood-history` - Get mood history
- `GET /api/weekly-summary` - Get weekly mood stats

### Utilities (Public)
- `GET /api/reflection-prompt` - Get reflection prompt
- `GET /health` - Health check

## 📚 Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask 2.3.3 |
| Database | Supabase (PostgreSQL) |
| Authentication | Supabase Auth + JWT |
| AI | OpenAI GPT-3.5/4 |
| Frontend | HTML, CSS, JavaScript |

## 🔐 How Authentication Works

```
Sign Up / Login → Supabase Authentication
                       ↓
                  JWT Tokens Generated
                       ↓
          Access Token (short-lived, 1 hour)
          Refresh Token (long-lived, 7 days)
                       ↓
              Stored in localStorage
                       ↓
              Sent with API Requests
              Header: "Authorization: Bearer <token>"
                       ↓
              @require_auth validates token
```

## 💾 Database Schema

### users table
```
id (UUID, primary key)
email (text, unique)
username (text)
created_at (timestamp)
updated_at (timestamp)
```

### messages table
```
id (UUID)
user_id (UUID) → references users
role (text) - 'user' or 'assistant'
content (text)
persona (text)
language (text)
mood_detected (text)
created_at (timestamp)
```

### mood_entries table
```
id (UUID)
user_id (UUID) → references users
mood (text)
intensity (integer 1-10)
created_at (timestamp)
```

## 🛡️ Security Features

✅ **Row-Level Security (RLS)** - Users only see their own data
✅ **JWT Tokens** - Secure token-based authentication
✅ **Password Hashing** - Supabase handles secure storage
✅ **Content Safety** - Detects harmful content
✅ **HTTPS Ready** - Deploy with SSL/TLS
✅ **CORS Protection** - Configurable origins

## 🚢 Deployment

### Environment Setup
```bash
# Set FLASK_DEBUG=False for production
export FLASK_DEBUG=False

# Use strong SECRET_KEY
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

### Deploy to Heroku
```bash
heroku create your-empathia-app
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_ANON_KEY=your_key
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

## 🐛 Troubleshooting

### "Supabase connection failed"
- ✓ Check SUPABASE_URL and SUPABASE_ANON_KEY in .env
- ✓ Verify Supabase project is active
- ✓ Test connection: `curl http://localhost:5001/health`

### "Invalid token" error
- ✓ Token expired → Log out and log in again
- ✓ Check localStorage for tokens
- ✓ Verify Authorization header in requests

### "Authentication required" on protected endpoints
- ✓ Add `Authorization: Bearer <token>` header
- ✓ Check token is valid (not expired)
- ✓ Review browser Network tab for header

### Port already in use
```bash
# Change PORT in .env or kill process
lsof -i :5001
kill -9 <PID>
```

## 📝 Environment Variables

| Variable | Required | Example |
|----------|----------|---------|
| `SUPABASE_URL` | ✅ Yes | `https://xxx.supabase.co` |
| `SUPABASE_ANON_KEY` | ✅ Yes | `eyJ0eXAiOi...` |
| `SUPABASE_SERVICE_KEY` | ✅ Yes | `eyJ0eXAiOi...` |
| `OPENAI_API_KEY` | ✅ Yes | `sk-...` |
| `SECRET_KEY` | ✅ Yes | Random string |
| `PORT` | ❌ No | `5001` (default: 5000) |
| `FLASK_DEBUG` | ❌ No | `True` or `False` |

## 📞 Support

1. **Check Documentation**: Read README.md setup section first
2. **Check Errors**: Look at terminal output and browser console
3. **Test Endpoints**: Use curl or Postman to test API
4. **Review Logs**: Check Supabase dashboard for table contents
5. **Community**: Visit Supabase Docs or Flask Docs

## 📖 Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [OpenAI API Docs](https://platform.openai.com/docs/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [JWT Best Practices](https://jwt.io/)

## 🎓 What's New from SQLite Version?

| Feature | SQLite | Supabase |
|---------|--------|----------|
| **Multi-user Support** | ❌ No | ✅ Yes |
| **Authentication** | ❌ None | ✅ JWT + Supabase Auth |
| **Scalability** | ⚠️ Limited | ✅ Production-ready |
| **Data Persistence** | ✅ Local | ✅ Cloud-hosted |
| **Chat History** | ✅ Yes | ✅ Yes + Per User |
| **Mood Tracking** | ✅ Yes | ✅ Yes + Per User |
| **RLS (Row Security)** | ❌ No | ✅ Yes |
| **Real-time Updates** | ❌ No | ✅ Available |

## 📄 License

MIT License - Use freely for personal and commercial projects

---

**🌟 Made with ❤️ for emotional wellbeing**

Start your emotional support journey today with Empathia!
