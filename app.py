"""
Empathia - Emotional Support & Self-Reflection Assistant
A bilingual Flask application powered by OpenAI API
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables FIRST, from the app directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client

# Import services
from database.supabase_db import SupabaseDB
from services.auth_service import AuthService
from services.openai_service import get_chat_response, extract_sentiment
from services.emotion_service import categorize_emotion, get_emotion_description, get_emotion_description_mk
from services.reflection_service import generate_reflection_prompt, suggest_reflection_activity
from services.safety_service import (
    is_content_safe, get_safety_warning, sanitize_input,
    validate_persona, validate_language
)
from services.emotion_analyzer import EmotionDetector
from services.psychologist.service import PsychologistService
from routes.psychologist_routes import psychologist_bp

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_KEY")
)

# Register blueprints
app.register_blueprint(psychologist_bp)


# Routes
@app.route('/')
def index():
    """Serve the landing page if not authenticated, otherwise chat."""
    token = request.cookies.get('access_token') or request.headers.get('Authorization', '').split(' ')[-1] if 'Authorization' in request.headers else None
    
    if token:
        return render_template('chat.html')
    else:
        return render_template('landing.html')


@app.route('/login')
def login():
    """Serve the login page."""
    return render_template('login.html')


@app.route('/chat')
def chat_page():
    """Serve the chat interface."""
    return render_template('chat.html')


@app.route('/psychologist/register')
def psychologist_register():
    """Serve the psychologist registration page."""
    return render_template('psychologist/register.html')


@app.route('/psychologist/dashboard')
def psychologist_dashboard():
    """Serve the psychologist dashboard."""
    return render_template('psychologist/dashboard.html')


# Authentication Endpoints
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """
    Sign up endpoint for new users.
    POST /api/auth/signup
    {
        "email": "user@example.com",
        "password": "password123",
        "username": "john_doe",
        "role": "user" or "psychologist",
        // For psychologists only:
        "license": "license_number",
        "bio": "professional bio",
        "specializations": "anxiety, depression, etc"
    }
    """
    try:
        data = request.json
        print(f"\n🔍 SIGNUP REQUEST RECEIVED")
        print(f"   Role: {data.get('role')}")
        print(f"   Email: {data.get('email')}")
        print(f"   Username: {data.get('username')}")
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        username = data.get('username', '').strip()
        role = data.get('role', 'user').lower()  # Default to 'user'
        
        print(f"   Role received: '{role}' (type: {type(role)})")

        # Validate input
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        if role not in ['user', 'psychologist']:
            return jsonify({'error': 'Invalid role. Must be "user" or "psychologist"'}), 400

        # For psychologists, validate required fields
        if role == 'psychologist':
            license_number = data.get('license', '').strip()
            bio = data.get('bio', '').strip()
            specializations = data.get('specializations', '').strip()
            
            print(f"   License: {license_number}")
            print(f"   Bio: {bio[:50] if bio else 'MISSING'}...")
            print(f"   Specializations: {specializations}")
            
            if not license_number or not bio or not specializations:
                error_msg = 'For psychologists: license, bio, and specializations are required'
                print(f"   ❌ {error_msg}")
                return jsonify({'error': error_msg}), 400
            
            print(f"   ✅ All psychologist fields provided")

        # Sign up with Supabase Auth
        result = AuthService.sign_up(email, password, username)

        if not result['success']:
            return jsonify({'error': result.get('error', 'Signup failed')}), 400

        user = result.get('user')
        session = result.get('session')

        # Create user profile in database
        if user:
            user_id = user.id
            SupabaseDB.get_or_create_user(user_id, email, username or email.split('@')[0])
            
            # If psychologist, create psychologist profile
            if role == 'psychologist':
                try:
                    print(f"   📝 Creating psychologist profile for {user_id}...")
                    
                    # Parse specializations from comma-separated string
                    spec_list = [s.strip().lower() for s in specializations.split(',')]
                    
                    # Use direct Supabase client insert with service key
                    insert_response = supabase.table("psychologist_profiles").insert({
                        "user_id": user_id,
                        "full_name": username or email.split('@')[0],
                        "specializations": spec_list,
                        "bio": bio,
                        "license_number": license_number,
                        "years_of_experience": None,
                        "languages_spoken": ["English"]
                    }).execute()
                    
                    if insert_response.data:
                        print(f"   ✅ Created psychologist profile successfully")
                    else:
                        print(f"   ⚠️ No data returned from insert")
                    
                except Exception as e:
                    print(f"   ❌ Error creating psychologist profile: {str(e)}")
                    import traceback
                    traceback.print_exc()

        return jsonify({
            'success': True,
            'message': 'Signup successful! Please check your email to verify.',
            'user_id': user.id if user else None,
            'email': email,
            'role': role,
            'access_token': session.access_token if session else None
        }), 201

    except Exception as e:
        print(f'Error in signup: {str(e)}')
        return jsonify({'error': 'Signup failed'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login_user():
    """
    Login endpoint for existing users.
    POST /api/auth/login
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        print(f"🔐 Login attempt for email: {email}")

        # Validate input
        if not email or not password:
            print(f"❌ Login failed: Missing email or password")
            return jsonify({'error': 'Email and password are required'}), 400

        # Sign in with Supabase Auth
        result = AuthService.sign_in(email, password)

        if not result['success']:
            error_msg = result.get('error', 'Invalid email or password')
            print(f"❌ Login failed for {email}: {error_msg}")
            return jsonify({'error': error_msg}), 401

        user = result.get('user')
        session = result.get('session')
        access_token = result.get('access_token')
        user_id = user.id if user else None

        # Get user role
        role = SupabaseDB.get_user_role(user_id) if user_id else 'user'

        print(f"✅ Login successful for {email} (role: {role}, user_id: {user_id})")

        return jsonify({
            'success': True,
            'user_id': user_id,
            'email': email,
            'role': role,
            'access_token': access_token,
            'refresh_token': session.refresh_token if session else None
        }), 200

    except Exception as e:
        print(f'❌ Error in login: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Login failed'}), 500


@app.route('/api/user/profile', methods=['GET', 'PUT'])
def user_profile():
    """Get or update user profile (including full_name)"""
    try:
        # Get user ID from header
        user_id = request.headers.get('X-User-ID')
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not user_id or not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        if request.method == 'GET':
            # Get user profile
            response = supabase.table('users').select('*').eq('id', user_id).single().execute()
            
            if response.data:
                return jsonify(response.data), 200
            else:
                return jsonify({'error': 'User not found'}), 404
                
        elif request.method == 'PUT':
            # Update user profile
            data = request.json
            full_name = data.get('full_name', '').strip()
            
            if not full_name or len(full_name) < 2:
                return jsonify({'error': 'Name must be at least 2 characters'}), 400
            
            # Update user
            response = supabase.table('users').update({
                'full_name': full_name,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            
            if response.data:
                return jsonify(response.data[0]), 200
            else:
                return jsonify({'error': 'Failed to update profile'}), 500
                
    except Exception as e:
        print(f"Error in user_profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout_user():
    """
    Logout endpoint.
    POST /api/auth/logout
    """
    try:
        # Get access token from header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Invalid Authorization header'}), 401

        access_token = auth_header.split(' ')[1]

        # Sign out with Supabase Auth
        result = AuthService.sign_out(access_token)

        if not result['success']:
            return jsonify({'error': result.get('error', 'Logout failed')}), 400

        return jsonify({'success': True}), 200

    except Exception as e:
        print(f'Error in logout: {str(e)}')
        return jsonify({'error': 'Logout failed'}), 500


@app.route('/api/auth/verify', methods=['GET'])
def verify_token():
    """
    Verify token endpoint.
    GET /api/auth/verify
    """
    try:
        # Get access token from header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Invalid Authorization header'}), 401

        access_token = auth_header.split(' ')[1]

        # Verify token with Supabase Auth
        result = AuthService.verify_token(access_token)

        if not result['success']:
            return jsonify({'error': 'Invalid token'}), 401

        user = result.get('user')
        return jsonify({
            'success': True,
            'user_id': user.id if user else None,
            'email': user.email if user else None
        }), 200

    except Exception as e:
        print(f'Error in verify token: {str(e)}')
        return jsonify({'error': 'Token verification failed'}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for handling user messages.
    POST /api/chat
    {
        "message": "user message",
        "language": "en",
        "persona": "supportive_friend",
        "userId": "unique_user_id"
    }
    """
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        language = validate_language(data.get('language', 'en'))
        persona = validate_persona(data.get('persona', 'supportive_friend'))
        user_id_str = data.get('userId', 'default_user')

        # Validate input
        is_safe, safety_reason = is_content_safe(user_message)
        if not is_safe:
            warning_msg = get_safety_warning(safety_reason, language)
            return jsonify({
                'response': warning_msg,
                'mood_detected': None,
                'error': True
            }), 400

        # Sanitize input
        user_message = sanitize_input(user_message)

        # Get or create user (in Supabase we use the user_id_str directly)
        user_id = user_id_str

        # Extract sentiment
        mood_detected = extract_sentiment(user_message)

        # Add user message to database
        SupabaseDB.add_message(user_id, 'user', user_message, persona, language, mood_detected)

        # Get recent conversation context
        recent_messages = SupabaseDB.get_chat_history(user_id, limit=10)
        conversation_context = [
            {'role': 'user' if msg['role'] == 'user' else 'assistant', 'content': msg['content']}
            for msg in reversed(recent_messages[1:])  # Skip the one we just added
        ]

        # Get AI response
        messages_for_api = conversation_context + [{'role': 'user', 'content': user_message}]
        ai_response = get_chat_response(messages_for_api, persona, language)

        # Add assistant message to database
        SupabaseDB.add_message(user_id, 'assistant', ai_response, persona, language)

        # Get emotion details
        emotion = categorize_emotion(user_message)
        if language == 'mk':
            emotion_note = get_emotion_description_mk(emotion)
        else:
            emotion_note = get_emotion_description(emotion)

        # Log mood entry silently
        SupabaseDB.add_mood_entry(user_id, mood_detected, intensity=5)

        return jsonify({
            'response': ai_response,
            'mood_detected': mood_detected,
            'emotion': emotion
        }), 200

    except Exception as e:
        print(f'Error in chat endpoint: {str(e)}')
        error_messages = {
            'en': 'An error occurred processing your message. Please try again.',
            'mk': 'Грешка се случи при обработката на вашата порака. Ве молиме обидитесе повторно.'
        }
        language = validate_language(request.json.get('language', 'en')) if request.json else 'en'
        return jsonify({
            'response': error_messages.get(language, error_messages['en']),
            'error': True
        }), 500


@app.route('/api/mood', methods=['POST'])
def log_mood():
    """
    Log mood endpoint for manual mood logging.
    POST /api/mood
    {
        "mood": "happy",
        "userId": "unique_user_id",
        "language": "en"
    }
    """
    try:
        data = request.json
        mood = data.get('mood', '').lower()
        user_id_str = data.get('userId', 'default_user')
        language = validate_language(data.get('language', 'en'))

        valid_moods = ['happy', 'sad', 'anxious', 'angry', 'calm', 'neutral']
        if mood not in valid_moods:
            return jsonify({'error': 'Invalid mood'}), 400

        # Get or create user (use user_id_str directly for Supabase)
        user_id = user_id_str

        # Add mood entry
        SupabaseDB.add_mood_entry(user_id, mood, intensity=5)

        # Get reflection suggestion
        reflection_suggestion = suggest_reflection_activity(mood, language)

        messages = {
            'en': 'Thank you for sharing your mood! ',
            'mk': 'Благодарам што го поделиш твоето расположение! '
        }

        return jsonify({
            'message': reflection_suggestion,
            'mood': mood
        }), 200

    except Exception as e:
        print(f'Error in mood endpoint: {str(e)}')
        return jsonify({'error': 'Failed to log mood'}), 500


@app.route('/api/mood-history', methods=['GET'])
def mood_history():
    """
    Get mood history endpoint.
    GET /api/mood-history?userId=unique_user_id&days=30
    """
    try:
        user_id_str = request.args.get('userId', 'default_user')
        days = int(request.args.get('days', 30))

        # Get or create user (use user_id_str directly for Supabase)
        user_id = user_id_str

        # Get mood history
        history = SupabaseDB.get_mood_history(user_id, days)

        # Format response
        entries = [
            {
                'date': entry['date'],
                'mood': entry['mood'],
                'count': entry['count']
            }
            for entry in history
        ]

        return jsonify({'entries': entries}), 200

    except Exception as e:
        print(f'Error in mood history endpoint: {str(e)}')
        return jsonify({'error': 'Failed to retrieve mood history'}), 500


@app.route('/api/weekly-summary', methods=['GET'])
def weekly_summary():
    """
    Get weekly mood summary endpoint.
    GET /api/weekly-summary?userId=unique_user_id
    """
    try:
        user_id_str = request.args.get('userId', 'default_user')

        # Get or create user (use user_id_str directly for Supabase)
        user_id = user_id_str

        # Get weekly summary
        summary_data = SupabaseDB.get_weekly_mood_summary(user_id)

        # Format response
        summary = [
            {
                'mood': item['mood'],
                'count': item['count'],
                'avg_intensity': item['avg_intensity'] or 5
            }
            for item in summary_data
        ]

        # Generate insight text
        if summary:
            dominant_mood = max(summary, key=lambda x: x['count'])
            insight = f"This week, your most frequent mood was {dominant_mood['mood']}."
        else:
            insight = "Start tracking your mood to see weekly insights!"

        return jsonify({
            'summary': summary,
            'insight': insight
        }), 200

    except Exception as e:
        print(f'Error in weekly summary endpoint: {str(e)}')
        return jsonify({'error': 'Failed to retrieve weekly summary'}), 500


@app.route('/api/chat-history', methods=['GET'])
def get_chat_history():
    """
    Get chat history for authenticated user.
    GET /api/chat-history?userId=uuid&limit=50
    """
    try:
        user_id = request.args.get('userId')
        limit = int(request.args.get('limit', 50))
        
        if not user_id:
            return jsonify({'error': 'userId is required'}), 400
        
        # Get chat history from database
        messages = SupabaseDB.get_chat_history(user_id, limit=limit)
        
        # Format messages for frontend
        formatted_messages = [
            {
                'id': msg.get('id'),
                'role': msg.get('role'),
                'content': msg.get('content'),
                'timestamp': msg.get('created_at'),
                'mood': msg.get('mood_detected'),
                'persona': msg.get('persona')
            }
            for msg in messages
        ]
        
        return jsonify({
            'messages': formatted_messages,
            'count': len(formatted_messages)
        }), 200
    
    except Exception as e:
        print(f'Error in chat history endpoint: {str(e)}')
        return jsonify({'error': 'Failed to retrieve chat history'}), 500


@app.route('/api/chat-sessions', methods=['POST'])
def create_chat_session():
    try:
        data = request.json
        user_id = data.get('userId')
        title = data.get('title')
        
        if not user_id:
            return jsonify({'error': 'userId is required'}), 400
        
        session = SupabaseDB.create_chat_session(user_id, title)
        
        return jsonify({
            'success': True,
            'session': session
        }), 201
    
    except Exception as e:
        print(f'Error in create chat session: {str(e)}')
        return jsonify({'error': 'Failed to create chat session'}), 500


@app.route('/api/chat-sessions', methods=['GET'])
def get_chat_sessions():
    try:
        user_id = request.args.get('userId')
        
        if not user_id:
            return jsonify({'error': 'userId is required'}), 400
        
        sessions = SupabaseDB.get_user_chat_sessions(user_id)
        
        return jsonify({
            'sessions': sessions,
            'count': len(sessions)
        }), 200
    
    except Exception as e:
        print(f'Error in get chat sessions: {str(e)}')
        return jsonify({'error': 'Failed to retrieve chat sessions'}), 500


@app.route('/api/chat-sessions/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    try:
        limit = int(request.args.get('limit', 50))
        
        messages = SupabaseDB.get_session_messages(session_id, limit)
        
        # Get chat session info to fetch psychologist details
        session_response = supabase.table('chat_sessions').select('psychologist_id, has_psychologist').eq('id', session_id).single().execute()
        
        psychologist_name = None
        if session_response.data and session_response.data.get('has_psychologist') and session_response.data.get('psychologist_id'):
            psychologist_id = session_response.data['psychologist_id']
            # Fetch psychologist's full name
            psych_response = supabase.table('psychologist_profiles').select('full_name').eq('id', psychologist_id).single().execute()
            if psych_response.data:
                psychologist_name = psych_response.data.get('full_name', 'Psychologist')
        
        formatted_messages = [
            {
                'id': msg.get('id'),
                'role': msg.get('role'),
                'content': msg.get('content'),
                'timestamp': msg.get('created_at'),
                'mood': msg.get('mood_detected'),
                'persona': msg.get('persona'),
                'user_id': msg.get('user_id')
            }
            for msg in messages
        ]
        
        return jsonify({
            'messages': formatted_messages,
            'count': len(formatted_messages),
            'psychologist_name': psychologist_name,  # Include psychologist name in response
            'has_psychologist': session_response.data.get('has_psychologist', False) if session_response.data else False  # Include psychologist status
        }), 200
    
    except Exception as e:
        print(f'Error in get session messages: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to retrieve session messages'}), 500


@app.route('/api/chat-sessions/<session_id>/chat', methods=['POST'])
def send_session_message(session_id):
    """
    Send a message to a specific chat session.
    POST /api/chat-sessions/<session_id>/chat
    {
        "message": "user message",
        "language": "en",
        "persona": "supportive_friend",
        "userId": "unique_user_id",
        "role": "user" or "psychologist"  # Optional, defaults to "user"
    }
    """
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        language = validate_language(data.get('language', 'en'))
        persona = validate_persona(data.get('persona', 'supportive_friend'))
        user_id = data.get('userId')
        message_role = data.get('role', 'user')  # 'user' or 'psychologist'

        if not user_id:
            return jsonify({'error': 'userId is required'}), 400

        # Validate input
        is_safe, safety_reason = is_content_safe(user_message)
        if not is_safe:
            warning_msg = get_safety_warning(safety_reason, language)
            return jsonify({
                'response': warning_msg,
                'mood_detected': None,
                'error': True
            }), 400

        # Sanitize input
        user_message = sanitize_input(user_message)

        # If psychologist is sending a message, just save it and return
        if message_role == 'psychologist':
            print(f"🧑‍⚕️ Psychologist message in session {session_id}")
            SupabaseDB.add_session_message(session_id, user_id, 'psychologist', user_message, persona, language, None)
            return jsonify({
                'success': True,
                'message': 'Psychologist message sent'
            }), 200

        # Extract sentiment
        mood_detected = extract_sentiment(user_message)

        # Add user message to session
        SupabaseDB.add_session_message(session_id, user_id, 'user', user_message, persona, language, mood_detected)

        # Check if session has a psychologist - if so, don't send AI response
        from database.supabase_db import supabase
        session_check = supabase.table('chat_sessions').select('has_psychologist').eq('id', session_id).single().execute()
        
        if session_check.data and session_check.data.get('has_psychologist'):
            print(f"👥 Session has psychologist - no AI response")
            # Log mood entry
            SupabaseDB.add_mood_entry(user_id, mood_detected, intensity=5)
            
            return jsonify({
                'response': None,  # No AI response when psychologist is present
                'mood_detected': mood_detected,
                'has_psychologist': True
            }), 200

        # Get recent session context
        recent_messages = SupabaseDB.get_session_messages(session_id, limit=10)
        conversation_context = [
            {'role': 'user' if msg['role'] == 'user' else 'assistant', 'content': msg['content']}
            for msg in reversed(recent_messages[:-1])  # Skip the one we just added
        ]

        # Get AI response
        messages_for_api = conversation_context + [{'role': 'user', 'content': user_message}]
        ai_response = get_chat_response(messages_for_api, persona, language)

        # Add assistant message to session
        SupabaseDB.add_session_message(session_id, user_id, 'assistant', ai_response, persona, language)

        # Get emotion details
        emotion = categorize_emotion(user_message)
        if language == 'mk':
            emotion_note = get_emotion_description_mk(emotion)
        else:
            emotion_note = get_emotion_description(emotion)

        # Log mood entry
        SupabaseDB.add_mood_entry(user_id, mood_detected, intensity=5)

        return jsonify({
            'response': ai_response,
            'mood_detected': mood_detected,
            'emotion': emotion
        }), 200

    except Exception as e:
        print(f'Error in send session message: {str(e)}')
        import traceback
        traceback.print_exc()
        error_messages = {
            'en': 'An error occurred processing your message. Please try again.',
            'mk': 'Грешка се случи при обработката на вашата порака. Ве молиме обидитесе повторно.'
        }
        language = validate_language(request.json.get('language', 'en')) if request.json else 'en'
        return jsonify({
            'response': error_messages.get(language, error_messages['en']),
            'error': True
        }), 500


@app.route('/api/chat-sessions/<session_id>', methods=['DELETE'])
def delete_chat_session(session_id):
    """
    Delete a chat session and all its messages.
    DELETE /api/chat-sessions/<session_id>
    """
    try:
        success = SupabaseDB.delete_chat_session(session_id)
        if success:
            return jsonify({'success': True, 'message': 'Chat session deleted'}), 200
        else:
            return jsonify({'error': 'Failed to delete chat session'}), 500
    except Exception as e:
        print(f'Error in delete chat session: {str(e)}')
        return jsonify({'error': 'Failed to delete chat session'}), 500


@app.route('/api/reflection-prompt', methods=['GET'])
def reflection_prompt():
    """
    Get a reflection prompt endpoint.
    GET /api/reflection-prompt?language=en
    """
    try:
        language = validate_language(request.args.get('language', 'en'))
        prompt = generate_reflection_prompt(language)

        return jsonify({'prompt': prompt}), 200

    except Exception as e:
        print(f'Error in reflection prompt endpoint: {str(e)}')
        return jsonify({'error': 'Failed to generate reflection prompt'}), 500


@app.route('/api/psychologist/analyze-emotion', methods=['POST'])
def analyze_emotion():
    """Analyze message for emotion and urgency level - NO AUTH REQUIRED"""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        # Analyze emotion
        emotion = categorize_emotion(message)
        
        # Detect urgency - comprehensive keyword matching
        high_urgency_keywords = [
            'suicide', 'suicidal', 'kill myself', 'kill myself', 'hurt myself', 'harm myself', 
            'end it', 'die', 'death', 'dead', 'panic attack', 'crisis', 'emergency', 'urgent',
            'self harm', 'self-harm', 'cutting', 'depressed', 'depression', 'hopeless',
            'worthless', 'can\'t take it', 'can\'t go on', 'no point', 'give up', 'overwhelmed',
            'anxious', 'anxiety', 'scared', 'afraid', 'terrified', 'urgent help needed'
        ]
        
        medium_urgency_keywords = [
            'sad', 'worried', 'stressed', 'stressed out', 'nervous', 'sick', 'ill'
        ]
        
        message_lower = message.lower()
        urgency_level = 'low'
        
        # Check high urgency first
        for keyword in high_urgency_keywords:
            if keyword in message_lower:
                urgency_level = 'high'
                break
        
        # Check medium urgency if not high
        if urgency_level == 'low':
            for keyword in medium_urgency_keywords:
                if keyword in message_lower:
                    urgency_level = 'medium'
                    break
        
        print(f"📊 Emotion analysis - Message: {message[:50]}... | Emotion: {emotion} | Urgency: {urgency_level}")
        
        return jsonify({
            'emotion': emotion,
            'urgency_level': urgency_level
        }), 200
    except Exception as e:
        print(f'❌ Error in analyze-emotion endpoint: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to analyze emotion'}), 500


@app.route('/api/psychologist/recommended', methods=['GET'])
def get_recommended_psychologists():
    """Get list of recommended psychologists"""
    try:
        # Get psychologists from database
        response = supabase.table("psychologist_profiles").select(
            "id, user_id, full_name, bio, profile_image_url, specializations, languages_spoken, is_online, session_rate_usd"
        ).eq("is_online", True).limit(5).execute()
        
        psychologists = response.data if response.data else []
        
        # Calculate rating for each psychologist
        for psych in psychologists:
            rating_response = supabase.table("psychologist_ratings").select(
                "rating"
            ).eq("psychologist_id", psych['id']).execute()
            
            ratings = rating_response.data if rating_response.data else []
            if ratings:
                avg_rating = sum(r['rating'] for r in ratings) / len(ratings)
                psych['average_rating'] = avg_rating
                psych['review_count'] = len(ratings)
            else:
                psych['average_rating'] = 5.0
                psych['review_count'] = 0
        
        return jsonify(psychologists), 200
    except Exception as e:
        print(f'Error in recommended psychologists endpoint: {str(e)}')
        return jsonify({'error': 'Failed to get psychologists'}), 500


@app.route('/api/chat-sessions/<session_id>/end-psychologist-session', methods=['POST'])
def end_user_psychologist_session(session_id):
    """
    User ends the psychologist session and optionally provides a rating.
    POST /api/chat-sessions/<session_id>/end-psychologist-session
    {
        "rating": 4.5,
        "feedback": "Great session, very helpful!"
    }
    """
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 401
        
        data = request.json or {}
        rating = data.get('rating')
        feedback = data.get('feedback', '').strip()
        
        # Verify this is the user's session
        session_response = supabase.table('chat_sessions').select(
            'id, user_id, psychologist_id, has_psychologist'
        ).eq('id', session_id).single().execute()
        
        if not session_response.data:
            return jsonify({'error': 'Session not found'}), 404
        
        session = session_response.data
        
        if session['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if not session['has_psychologist'] or not session['psychologist_id']:
            return jsonify({'error': 'No psychologist in this session'}), 400
        
        psychologist_id = session['psychologist_id']
        
        # Find the psychologist_sessions record
        psych_session_response = supabase.table('psychologist_sessions').select(
            'id'
        ).eq('chat_session_id', session_id).is_('ended_at', 'null').execute()
        
        if psych_session_response.data and len(psych_session_response.data) > 0:
            psych_session_id = psych_session_response.data[0]['id']
            
            # End the psychologist session (only update ended_at, no status column)
            supabase.table('psychologist_sessions').update({
                'ended_at': datetime.utcnow().isoformat()
            }).eq('id', psych_session_id).execute()
            
            print(f"✅ User ended psychologist session {psych_session_id}")
        
        # Update chat session to remove psychologist
        supabase.table('chat_sessions').update({
            'has_psychologist': False
        }).eq('id', session_id).execute()
        
        # If rating is provided, save it
        if rating is not None:
            try:
                rating = float(rating)
                if not (1 <= rating <= 5):
                    return jsonify({'error': 'Rating must be between 1 and 5'}), 400
                
                # Insert rating (use review_text not feedback)
                supabase.table('psychologist_ratings').insert({
                    'user_id': user_id,
                    'psychologist_id': psychologist_id,
                    'session_id': session_id,
                    'rating': rating,
                    'review_text': feedback if feedback else None,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
                
                print(f"⭐ User rated psychologist: {rating}/5")
            except ValueError:
                return jsonify({'error': 'Invalid rating value'}), 400
        
        print(f"✅ User successfully ended session {session_id}")
        
        return jsonify({
            'success': True,
            'message': 'Session ended successfully'
        }), 200
        
    except Exception as e:
        print(f'Error ending user psychologist session: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to end session'}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


# Entry point
if __name__ == '__main__':
    # Ensure API key is configured
    if not os.getenv('OPENAI_API_KEY'):
        print('⚠️  Warning: OPENAI_API_KEY not found in environment variables.')
        print('Please set your OpenAI API key in .env file or as an environment variable.')
        print('See .env.example for setup instructions.')

    # Run the Flask app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f'\n{"=" * 60}')
    print('🎯 Empathia - Emotional Support Assistant')
    print(f'{"=" * 60}')
    print(f'🌐 Starting Flask server on http://localhost:{port}')
    print(f'� Database: Supabase ({os.getenv("SUPABASE_URL", "not configured")})')
    print(f'🔧 Debug mode: {debug}')
    print(f'{"=" * 60}\n')

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
