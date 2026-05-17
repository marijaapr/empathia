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

# Import services
from database.db import (
    init_db, get_or_create_user, add_message, get_user_messages,
    add_mood_entry, get_mood_history, get_weekly_mood_summary,
    update_user_settings, get_user_settings
)
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

# Initialize database
init_db()


# Routes
@app.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('index.html')


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

        # Get or create user
        user_id = get_or_create_user(user_id_str)

        # Update user settings
        update_user_settings(user_id, language, persona)

        # Extract sentiment
        mood_detected = extract_sentiment(user_message)

        # Add user message to database
        add_message(user_id, 'user', user_message, persona, language, mood_detected)

        # Get recent conversation context
        recent_messages = get_user_messages(user_id, limit=10)
        conversation_context = [
            {'role': 'user' if msg['role'] == 'user' else 'assistant', 'content': msg['content']}
            for msg in reversed(recent_messages[1:])  # Skip the one we just added
        ]

        # Get AI response
        messages_for_api = conversation_context + [{'role': 'user', 'content': user_message}]
        ai_response = get_chat_response(messages_for_api, persona, language)

        # Add assistant message to database
        add_message(user_id, 'assistant', ai_response, persona, language)

        # Get emotion details
        emotion = categorize_emotion(user_message)
        if language == 'mk':
            emotion_note = get_emotion_description_mk(emotion)
        else:
            emotion_note = get_emotion_description(emotion)

        # Log mood entry silently
        add_mood_entry(user_id, mood_detected, intensity=5, notes=emotion_note)

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

        # Get or create user
        user_id = get_or_create_user(user_id_str)

        # Add mood entry
        add_mood_entry(user_id, mood, intensity=5, notes=f'Mood logged at {datetime.now().isoformat()}')

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

        # Get or create user
        user_id = get_or_create_user(user_id_str)

        # Get mood history
        history = get_mood_history(user_id, days)

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

        # Get or create user
        user_id = get_or_create_user(user_id_str)

        # Get weekly summary
        summary_data = get_weekly_mood_summary(user_id)

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
    print(f'📝 Database: {os.getenv("DATABASE_PATH", "empathia.db")}')
    print(f'🔧 Debug mode: {debug}')
    print(f'{"=" * 60}\n')

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
