# Empathia Supabase Integration - Setup Checklist

## 📋 Pre-Setup Checklist

Before you start, make sure you have:

- [ ] Python 3.9+ installed
- [ ] Virtual environment created (`venv/`)
- [ ] Project files in: `/Users/marijaprastova/Desktop/empathia`
- [ ] Internet connection (for Supabase and OpenAI)
- [ ] A web browser
- [ ] Text editor for editing `.env`

## ✅ Step-by-Step Setup

### Phase 1: Supabase Account Setup (10 minutes)

- [ ] Go to https://supabase.com
- [ ] Click "Sign Up"
- [ ] Sign up with email or GitHub
- [ ] Verify email
- [ ] Go to Supabase dashboard

### Phase 2: Create Supabase Project (5-10 minutes)

- [ ] Click "New Project"
- [ ] Project name: `empathia`
- [ ] Set strong database password (save this!)
- [ ] Select region closest to you
- [ ] Click "Create new project"
- [ ] Wait for project creation (5-10 minutes)
- [ ] ✅ Project is ready when you see the dashboard

### Phase 3: Get API Credentials (5 minutes)

- [ ] Click "Project Settings" (gear icon, bottom left)
- [ ] Click "API" in left sidebar
- [ ] Copy **Project URL** (looks like `https://xxx.supabase.co`)
- [ ] Copy **anon key** (starts with `eyJ...`)
- [ ] Copy **service_role key** (starts with `eyJ...`)
- [ ] Save these to a temporary file

### Phase 4: Get OpenAI API Key (3 minutes)

- [ ] Go to https://platform.openai.com/api-keys
- [ ] Sign in or create account
- [ ] Click "Create new secret key"
- [ ] Copy the key (starts with `sk-`)
- [ ] Save this to your temporary file

### Phase 5: Setup Local Environment (5 minutes)

- [ ] Open terminal and navigate to project:
  ```bash
  cd /Users/marijaprastova/Desktop/empathia
  ```

- [ ] Activate virtual environment:
  ```bash
  source venv/bin/activate
  ```

- [ ] Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
  (Wait for all packages to install)

- [ ] ✅ Check successful installation:
  ```bash
  python -c "import supabase, flask, openai; print('✅ All imports successful')"
  ```

### Phase 6: Create .env File (5 minutes)

- [ ] Copy template:
  ```bash
  cp .env.example .env
  ```

- [ ] Open `.env` in text editor

- [ ] Fill in your Supabase credentials:
  ```env
  SUPABASE_URL=https://your-project-name.supabase.co
  SUPABASE_ANON_KEY=eyJ0eXAiOiJKV1QiLC...
  SUPABASE_SERVICE_KEY=eyJ0eXAiOiJKV1QiLC...
  ```

- [ ] Fill in your OpenAI API key:
  ```env
  OPENAI_API_KEY=sk-...
  ```

- [ ] Generate a secret key:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Copy the output and paste:
  ```env
  SECRET_KEY=output_from_above
  ```

- [ ] Save `.env` file

- [ ] ✅ Verify .env has all required variables:
  ```bash
  grep "SUPABASE_URL\|SUPABASE_ANON_KEY\|OPENAI_API_KEY" .env
  ```

### Phase 7: Create Database Tables (5-10 minutes)

This is the most important step!

- [ ] In Supabase dashboard, go to "SQL Editor"
- [ ] Click "+ New Query"
- [ ] Copy **entire first SQL block** from `SUPABASE_SETUP.md`
  (The "users" table creation)
- [ ] Paste into SQL editor
- [ ] Click "Run"
- [ ] ✅ You should see "Success"
- [ ] Repeat for the second query (messages table)
- [ ] Repeat for the third query (mood_entries table)

**Tip**: If you see errors, make sure:
- You copied the entire SQL block
- You ran them one at a time
- You waited for each to complete before running the next

### Phase 8: Start the Application (2 minutes)

- [ ] In terminal (with venv activated), run:
  ```bash
  python app_supabase.py
  ```

- [ ] ✅ You should see:
  ```
  ============================================================
  🎯 Empathia - Emotional Support Assistant
  ============================================================
  🌐 Starting Flask server on http://localhost:5001
  📚 Database: Supabase (https://your-project.supabase.co)
  🔧 Debug mode: True
  ============================================================
  ```

- [ ] If you see errors, check:
  - All .env variables are filled in
  - Supabase project is active
  - Database tables were created successfully
  - Internet connection is working

### Phase 9: Test the Application (5-10 minutes)

- [ ] Open web browser
- [ ] Go to: `http://localhost:5001/login`
- [ ] ✅ You should see login/signup page
- [ ] Fill in sign up form:
  - Email: (your email)
  - Username: (your name)
  - Password: (secure password)
- [ ] Click "Sign Up"
- [ ] ✅ You should get success message
- [ ] Switch to "Login" tab
- [ ] Enter your email and password
- [ ] Click "Login"
- [ ] ✅ Should redirect to `/chat` page
- [ ] ✅ You should see chat interface
- [ ] Type a message and send
- [ ] ✅ AI should respond!

### Phase 10: Test Chat Features (10 minutes)

- [ ] **Test Chat**:
  - [ ] Type: "I'm feeling anxious"
  - [ ] ✅ Should get response
  - [ ] Should see detected mood

- [ ] **Test Mood Tracker**:
  - [ ] Click a mood button (e.g., "😊 Happy")
  - [ ] ✅ Should show reflection suggestion

- [ ] **Test History**:
  - [ ] Click "View Chat History"
  - [ ] ✅ Should see your messages

- [ ] **Test Logout**:
  - [ ] Click "Logout" button
  - [ ] ✅ Should go back to login page

## 🎉 Success Checklist

If you've checked all boxes and everything works, you're done! ✅

- [ ] Supabase project created
- [ ] API credentials retrieved
- [ ] OpenAI API key obtained
- [ ] .env file configured
- [ ] Database tables created
- [ ] App starts without errors
- [ ] Login page loads
- [ ] Sign up works
- [ ] Login works
- [ ] Chat page appears
- [ ] Can send messages
- [ ] AI responds
- [ ] Can log moods
- [ ] Can view history
- [ ] Logout works

## ⚠️ Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'supabase'"
**Solution**: 
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Connection refused" or "Can't reach Supabase"
**Solution**: Check your .env file:
```bash
grep "SUPABASE_URL" .env
```
Make sure the URL is correct and starts with `https://`

### Issue: "Invalid credentials" on login
**Solution**:
1. Check you created a user account with sign up
2. Use exact email and password you signed up with
3. Check .env for SUPABASE_ANON_KEY

### Issue: Tables don't exist error
**Solution**:
1. Go to Supabase SQL Editor
2. Check if tables appear in left sidebar
3. If not, re-run the SQL queries from SUPABASE_SETUP.md
4. Make sure to copy the ENTIRE query block

### Issue: Port 5001 already in use
**Solution**:
```bash
# Change port in .env
echo "PORT=5002" >> .env

# Or kill the process using port 5001
lsof -i :5001
kill -9 <PID>
```

### Issue: OpenAI API errors
**Solution**:
1. Check your OpenAI API key in .env is correct
2. Log into https://platform.openai.com/api-keys and verify key exists
3. Make sure your OpenAI account has credits/is not rate limited

## 📖 Next Steps

After successful setup:

1. **Customize the chat experience**:
   - Edit templates/chat.html to add more features
   - Modify services to add new personas

2. **Deploy to production**:
   - Follow instructions in INTEGRATION_GUIDE.md
   - Use Heroku, Railway, or similar platform

3. **Add more features**:
   - Video calls
   - Integration with therapy resources
   - Mobile app using Flutter/React Native

4. **Gather analytics**:
   - See how users interact with the app
   - Track mood trends
   - Improve based on feedback

## 🆘 Still Need Help?

1. **Check Documentation**:
   - Read INTEGRATION_GUIDE.md (has more details)
   - Read SUPABASE_SETUP.md (for database help)
   - Read README.md (overview)

2. **Debug Terminal Output**:
   - Look at terminal errors when app starts
   - Look at browser console (F12) for frontend errors

3. **Check Supabase Dashboard**:
   - Go to SQL Editor → verify tables exist
   - Go to Authentication → verify users created
   - Go to API → verify credentials are correct

4. **Test with curl**:
   ```bash
   # Test health endpoint
   curl http://localhost:5001/health
   
   # Test login
   curl -X POST http://localhost:5001/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"your@email.com","password":"yourpassword"}'
   ```

## ✅ Verification Checklist

Run this to verify everything is set up correctly:

```bash
# Check Python and packages
python --version
python -c "import supabase, flask, openai; print('✅ Packages OK')"

# Check .env file
ls -la .env
grep "SUPABASE_URL" .env

# Check database
# (In Supabase, go to SQL Editor and run:)
# SELECT * FROM users;
# SELECT * FROM messages;
# SELECT * FROM mood_entries;

# Start app and test
python app_supabase.py
# Then open http://localhost:5001/login
```

---

**🎉 Congratulations! Your Empathia app is ready to provide emotional support!**

Questions? Review the documentation or check the terminal for error messages.
