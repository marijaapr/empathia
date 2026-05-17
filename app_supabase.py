"""
Empathia - Emotional Support & Self-Reflection Assistant
A bilingual Flask application powered by OpenAI API and Supabase
"""

import os
import json
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

# Load environment variables FIRST, from the app directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from flask import Flask, render_template, request, jsonify, redirect

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

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')


# Middleware: Authentication decorator
def require_auth(f):
    """Decorator to require valid auth token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid Authorization header'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token required'}), 401
        
        # Verify token
        result = AuthService.verify_token(token)
        if not result['success']:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Store user in request context
        request.user_id = result['user'].id
        request.user_email = result['user'].email
        
        return f(*args, **kwargs)
    
    return decorated_function


# ============ AUTHENTICATION ROUTES ============

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """
    Sign up new user
    POST /api/auth/signup
    {
        "email": "user@example.com",
        "password": "password123",
        "username": "username"
    }
    """
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        username = data.get('username', '').strip()

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        # Sign up with Supabase
        result = AuthService.sign_up(email, password, username)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400

        # Create user profile in database
        user = result['user']
        SupabaseDB.get_or_create_user(user.id, email, username)

        return jsonify({
            'success': True,
            'message': 'Signup successful! Please verify your email.',
            'user_id': user.id,
            'email': email
        }), 201

    except Exception as e:
        print(f'Error in signup: {str(e)}')
        return jsonify({'error': 'Signup failed'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Sign in user
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

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        # Sign in with Supabase
        result = AuthService.sign_in(email, password)
        
        if not result['success']:
            return jsonify({'error': 'Invalid email or password'}), 401

        user = result['user']
        session = result['session']
        
        # Ensure user profile exists
        SupabaseDB.get_or_create_user(user.id, email)

        return jsonify({
            'success': True,
            'user_id': user.id,
            'email': user.email,
            'access_token': result['access_token'],
            'refresh_token': session.refresh_token if session else None
        }), 200

    except Exception as e:
        print(f'Error in login: {str(e)}')
        return jsonify({'error': 'Login failed'}), 500


@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """
    Sign out user
    POST /api/auth/logout
    Headers: Authorization: Bearer <token>
    """
    try:
        token = request.headers['Authorization'].split(" ")[1]
        result = AuthService.sign_out(token)
        
        return jsonify({'success': result['success']}), 200

    except Exception as e:
        print(f'Error in logout: {str(e)}')
        return jsonify({'error': 'Logout failed'}), 500


@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh access token
    POST /api/auth/refresh
    {
        "refresh_token": "refresh_token_value"
    }
    """
    try:
        data = request.json
        refresh_token = data.get('refresh_token', '')

        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400

        result = AuthService.refresh_session(refresh_token)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 401

        return jsonify({
            'access_token': result['access_token'],
            'refresh_token': result['session'].refresh_token if result['session'] else None
        }), 200

    except Exception as e:
        print(f'Error in refresh token: {str(e)}')
        return jsonify({'error': 'Token refresh failed'}), 500


# ============ MAIN APP ROUTES ============

@app.route('/')
def index():
    """Redirect to login page."""
    return redirect('/login')


@app.route('/login')
def login_page():
    """Serve the login/signup page."""
    return render_template('login.html')


@app.route('/chat')
def chat_page():
    """Serve the chat interface (requires authentication check on frontend)."""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    """
    Chat endpoint for handling user messages (requires authentication)
    POST /api/chat
    Headers: Authorization: Bearer <token>
    {
        "message": "user message",
        "language": "en",
        "persona": "supportive_friend"
    }
    """
    try:
        data = request.json
        user_id = request.user_id
        user_message = data.get('message', '').strip()
        language = validate_language(data.get('language', 'en'))
        persona = validate_persona(data.get('persona', 'supportive_friend'))

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

        # Extract sentiment
        mood_detected = extract_sentiment(user_message)

        # Add user message to database
        SupabaseDB.add_message(user_id, 'user', user_message, persona, language, mood_detected)

        # Get recent conversation context
        recent_messages = SupabaseDB.get_chat_history(user_id, limit=10)
        conversation_context = [
            {'role': 'user' if msg['role'] == 'user' else 'assistant', 'content': msg['content']}
            for msg in reversed(recent_messages[:-1]) if msg['role'] in ['user', 'assistant']
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

        # Log mood entry
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
@require_auth
def log_mood():
    """
    Log mood endpoint for manual mood logging (requires authentication)
    POST /api/mood
    Headers: Authorization: Bearer <token>
    {
        "mood": "happy",
        "intensity": 8,
        "language": "en"
    }
    """
    try:
        data = request.json
        user_id = request.user_id
        mood = data.get('mood', '').lower()
        intensity = int(data.get('intensity', 5))
        language = validate_language(data.get('language', 'en'))

        valid_moods = ['happy', 'sad', 'anxious', 'angry', 'calm', 'neutral']
        if mood not in valid_moods:
            return jsonify({'error': 'Invalid mood'}), 400

        # Validate intensity
        if not 1 <= intensity <= 10:
            intensity = 5

        # Add mood entry
        SupabaseDB.add_mood_entry(user_id, mood, intensity)

        # Get reflection suggestion
        reflection_suggestion = suggest_reflection_activity(mood, language)

        return jsonify({
            'message': reflection_suggestion,
            'mood': mood,
            'intensity': intensity
        }), 200

    except Exception as e:
        print(f'Error in mood endpoint: {str(e)}')
        return jsonify({'error': 'Failed to log mood'}), 500


@app.route('/api/mood-history', methods=['GET'])
@require_auth
def mood_history():
    """
    Get mood history endpoint (requires authentication)
    GET /api/mood-history?days=30
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.user_id
        days = int(request.args.get('days', 30))

        # Get mood history
        history = SupabaseDB.get_mood_history(user_id, days)

        # Format response
        entries = []
        for date, moods in history.items():
            for mood, data in moods.items():
                entries.append({
                    'date': date,
                    'mood': mood,
                    'count': data['count'],
                    'avg_intensity': round(data['avg_intensity'], 1)
                })

        return jsonify({'entries': entries}), 200

    except Exception as e:
        print(f'Error in mood history endpoint: {str(e)}')
        return jsonify({'error': 'Failed to retrieve mood history'}), 500


@app.route('/api/weekly-summary', methods=['GET'])
@require_auth
def weekly_summary():
    """
    Get weekly mood summary endpoint (requires authentication)
    GET /api/weekly-summary
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.user_id

        # Get weekly summary
        summary_data = SupabaseDB.get_weekly_mood_summary(user_id)

        # Format response
        summary = [
            {
                'mood': mood,
                'count': data['count'],
                'avg_intensity': round(data['avg_intensity'], 1)
            }
            for mood, data in summary_data.items()
        ]

        # Sort by count
        summary.sort(key=lambda x: x['count'], reverse=True)

        # Generate insight text
        if summary:
            dominant_mood = summary[0]
            insight = f"This week, your most frequent mood was {dominant_mood['mood']} ({dominant_mood['count']} times)."
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
@require_auth
def chat_history():
    """
    Get chat history endpoint (requires authentication)
    GET /api/chat-history?limit=50
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.user_id
        limit = int(request.args.get('limit', 50))

        # Get chat history
        messages = SupabaseDB.get_chat_history(user_id, limit)

        return jsonify({'messages': messages}), 200

    except Exception as e:
        print(f'Error in chat history endpoint: {str(e)}')
        return jsonify({'error': 'Failed to retrieve chat history'}), 500


@app.route('/api/reflection-prompt', methods=['GET'])
def reflection_prompt():
    """
    Get a reflection prompt endpoint
    GET /api/reflection-prompt?language=en
    """
    try:
        language = validate_language(request.args.get('language', 'en'))
        prompt = generate_reflection_prompt(language)

        return jsonify({'prompt': prompt}), 200

    except Exception as e:
        print(f'Error in reflection prompt endpoint: {str(e)}')
        return jsonify({'error': 'Failed to generate reflection prompt'}), 500


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
    # Ensure required variables are configured
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_ANON_KEY'):
        print('⚠️  Warning: Supabase configuration not found in environment variables.')
        print('Please set SUPABASE_URL and SUPABASE_ANON_KEY in .env file.')
        print('See SUPABASE_SETUP.md for setup instructions.')

    if not os.getenv('OPENAI_API_KEY'):
        print('⚠️  Warning: OPENAI_API_KEY not found in environment variables.')
        print('Please set your OpenAI API key in .env file.')

    # Run the Flask app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f'\n{"=" * 60}')
    print('🎯 Empathia - Emotional Support Assistant')
    print('=' * 60)
    print(f'🌐 Starting Flask server on http://localhost:{port}')
    print(f'📚 Database: Supabase ({os.getenv("SUPABASE_URL", "Not configured")})')
    print(f'🔧 Debug mode: {debug}')
    print('=' * 60 + '\n')

    app.run(host='0.0.0.0', port=port, debug=debug)
