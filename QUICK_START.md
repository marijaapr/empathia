# Empathia - Quick Start Guide

## 📋 Project Created Successfully!

Empathia is a bilingual emotional support and self-reflection assistant using Flask and OpenAI.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd /Users/marijaprastova/Desktop/empathia
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Then edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access in Browser
Open: http://localhost:5000

## 📁 Project Structure

```
empathia/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
├── README.md                       # Full documentation
│
├── database/
│   ├── __init__.py
│   └── db.py                       # SQLite database management
│
├── services/                       # Business logic
│   ├── __init__.py
│   ├── openai_service.py          # OpenAI API integration
│   ├── emotion_service.py         # Emotion analysis
│   ├── reflection_service.py      # Reflection prompts
│   └── safety_service.py          # Content validation
│
├── templates/
│   └── index.html                 # Main UI
│
└── static/
    ├── style.css                  # Styling
    └── script.js                  # Frontend logic
```

## 🎯 Features Implemented

✅ **Bilingual Support** (English / Macedonian)
✅ **Multiple Personas** (Supportive Friend, Reflective Coach, Neutral Assistant)
✅ **Chat Interface** - Real-time conversation with AI
✅ **Mood Tracking** - Log and visualize emotional entries
✅ **Weekly Summary** - Mood trends and insights
✅ **Safety Checks** - Content validation and harmful content filtering
✅ **SQLite Database** - Persistent data storage (users, messages, moods)

## 🔌 API Endpoints

- `POST /api/chat` - Send message to AI assistant
- `POST /api/mood` - Log manual mood entry
- `GET /api/mood-history` - Retrieve mood entries (30 days)
- `GET /api/weekly-summary` - Get weekly mood analysis
- `GET /api/reflection-prompt` - Get reflection suggestion
- `GET /health` - Health check

## 🎨 UI Features

- Responsive design (mobile, tablet, desktop)
- Real-time chat interface
- Language selector
- Persona selector
- Quick mood buttons
- Mood history visualization
- Weekly summary display
- Modern gradient styling

## 🔒 Security

- Input sanitization
- Content safety checks
- Environment variable protection
- No hardcoded credentials

## 💡 Next Steps

1. Get OpenAI API key from https://platform.openai.com
2. Configure your `.env` file
3. Install dependencies
4. Run `python app.py`
5. Open browser to http://localhost:5000

## 📝 Database Schema

- **users**: Store user preferences (language, persona)
- **messages**: Store chat history with sentiment
- **mood_entries**: Store mood logs with intensity

## ⚙️ Environment Variables

```
OPENAI_API_KEY=<your-api-key>      # Required
FLASK_ENV=development               # Optional
FLASK_DEBUG=True                    # Optional
SECRET_KEY=<secret-key>            # Optional
DATABASE_PATH=empathia.db          # Optional
PORT=5000                          # Optional
```

## 🐛 Troubleshooting

### Missing OpenAI API Key
- Error will appear on startup
- Add key to `.env` file
- Restart the application

### Database Issues
- Delete `empathia.db` to reset
- Database will recreate automatically

### Port Already in Use
- Change PORT in `.env`
- Or kill process on port 5000

## 📚 Languages & Personas

**Languages:**
- English (en)
- Macedonian (mk)

**Personas:**
- Supportive Friend (warm, encouraging)
- Reflective Coach (thoughtful, guiding)
- Neutral Assistant (balanced, factual)

**Moods:**
- Happy, Sad, Anxious, Angry, Calm, Neutral

---

Enjoy using Empathia! 🌟
