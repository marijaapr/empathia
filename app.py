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

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_KEY")
)


# Routes
@app.route('/')
def index():
    """Serve the login page if not authenticated, otherwise chat."""
    token = request.cookies.get('access_token') or request.headers.get('Authorization', '').split(' ')[-1] if 'Authorization' in request.headers else None
    
    if token:
        return render_template('chat.html')
    else:
        return render_template('login.html')


@app.route('/login')
def login():
    """Serve the login page."""
    return render_template('login.html')


@app.route('/chat')
def chat_page():
    """Serve the chat interface."""
    return render_template('chat.html')


# Authentication Endpoints
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """
    Sign up endpoint for new users.
    POST /api/auth/signup
    {
        "email": "user@example.com",
        "password": "password123",
        "username": "john_doe"
    }
    """
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        username = data.get('username', '').strip()

        # Validate input
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        # Sign up with Supabase Auth
        result = AuthService.sign_up(email, password, username)

        if not result['success']:
            return jsonify({'error': result.get('error', 'Signup failed')}), 400

        user = result.get('user')
        session = result.get('session')

        # Create user profile in database
        if user:
            SupabaseDB.get_or_create_user(user.id, email, username or email.split('@')[0])

        return jsonify({
            'success': True,
            'message': 'Signup successful! Please check your email to verify.',
            'user_id': user.id if user else None,
            'email': email,
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

        # Validate input
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Sign in with Supabase Auth
        result = AuthService.sign_in(email, password)

        if not result['success']:
            return jsonify({'error': 'Invalid email or password'}), 401

        user = result.get('user')
        session = result.get('session')
        access_token = result.get('access_token')

        return jsonify({
            'success': True,
            'user_id': user.id if user else None,
            'email': email,
            'access_token': access_token,
            'refresh_token': session.refresh_token if session else None
        }), 200

    except Exception as e:
        print(f'Error in login: {str(e)}')
        return jsonify({'error': 'Login failed'}), 500


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
        print(f'Error in get session messages: {str(e)}')
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
        "userId": "unique_user_id"
    }
    """
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        language = validate_language(data.get('language', 'en'))
        persona = validate_persona(data.get('persona', 'supportive_friend'))
        user_id = data.get('userId')

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

        # Extract sentiment
        mood_detected = extract_sentiment(user_message)

        # Add user message to session
        SupabaseDB.add_session_message(session_id, user_id, 'user', user_message, persona, language, mood_detected)

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
