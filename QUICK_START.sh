#!/bin/bash
# Empathia + Supabase Quick Setup Script
# Run this after you have your Supabase credentials

# ============ SETUP INSTRUCTIONS ============

echo "🎯 Empathia + Supabase Setup"
echo "============================"
echo ""
echo "Step 1: Verify you have the project dependencies"
echo "Run: pip install -r requirements.txt"
echo ""

echo "Step 2: Create your Supabase account"
echo "Go to: https://supabase.com"
echo "- Create new project"
echo "- Save project name and password"
echo ""

echo "Step 3: Copy your Supabase credentials"
echo "In Supabase dashboard:"
echo "- Go to Project Settings → API"
echo "- Copy Project URL"
echo "- Copy anon key"
echo "- Copy service_role key"
echo ""

echo "Step 4: Get your OpenAI API key"
echo "Go to: https://platform.openai.com/api-keys"
echo "- Create new API key"
echo "- Copy it"
echo ""

echo "Step 5: Create .env file with your credentials"
echo "Copy .env.example to .env:"
echo "$ cp .env.example .env"
echo ""
echo "Edit .env and add:"
echo "SUPABASE_URL=https://your-project.supabase.co"
echo "SUPABASE_ANON_KEY=eyJ..."
echo "SUPABASE_SERVICE_KEY=eyJ..."
echo "OPENAI_API_KEY=sk-..."
echo "SECRET_KEY=any-random-string"
echo ""

echo "Step 6: Create database tables in Supabase"
echo "In Supabase, go to SQL Editor and run migrations (see run_migration.py)"
echo ""

echo "Step 7: Run the application!"
echo "$ python app.py"
echo ""
echo ""

echo "Step 8: Open in browser"
echo "🌐 http://localhost:5001/login"
echo ""

echo "============================================"
echo "✅ That's it! Sign up and start chatting"
echo "============================================"

# ============ QUICK COMMANDS ============

echo ""
echo "📋 Quick Command Reference:"
echo ""
echo "# Activate virtual environment"
echo "source venv/bin/activate"
echo ""
echo "# Install dependencies"
echo "pip install -r requirements.txt"
echo ""
echo "# Run the full app (recommended)"
echo "python app.py"
echo ""
echo "# Test API"
echo "curl http://localhost:5001/health"
echo ""
echo ""

echo "📖 Documentation:"
echo "- README.md - Setup, API, and project structure"
echo "- .env.example - Environment variables template"
echo ""

echo "🔗 Useful links:"
echo "- Supabase: https://supabase.com"
echo "- OpenAI API: https://platform.openai.com"
echo "- Flask Docs: https://flask.palletsprojects.com"
echo ""

echo "💬 Need help?"
echo "1. Check README.md"
echo "2. Look at terminal output for errors"
echo "3. Check browser console for frontend errors"
echo "4. Review Supabase dashboard for database issues"
