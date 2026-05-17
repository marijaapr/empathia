import os
import openai

# Read API key directly from .env file
api_key = None
env_file = os.path.join(os.path.dirname(__file__), '..', '.env')

try:
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('OPENAI_API_KEY='):
                # Extract the value after the = sign and handle multi-line values
                api_key = line.split('=', 1)[1].strip()
                break
except Exception as e:
    print(f'Warning: Could not read .env file: {e}')

# Also check environment variable as fallback
if not api_key:
    api_key = os.getenv('OPENAI_API_KEY')

if api_key and not api_key.startswith('your_'):
    openai.api_key = api_key
else:
    print('WARNING: OPENAI_API_KEY not properly configured in .env file')


def get_chat_response(messages, persona='supportive_friend', language='en'):
    """
    Get a response from OpenAI API.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        persona: The AI persona to use
        language: Language code (en or mk)
    
    Returns:
        str: response_text
    """
    
    system_prompts = {
        'supportive_friend': {
            'en': 'You are a warm, empathetic, and supportive friend. Listen actively, validate emotions, and offer gentle encouragement. Be genuine and compassionate in your responses. Always respond in English.',
            'mk': 'Ти си топол, емпатичен и поддржувачки пријател. Слушај активно, потврди емоции и нуди благо охрабрување. Биди искрен и сострадален во твоите одговори. ВАЖНО: Секогаш одговарај ИСКЛУЧИВО на македонски јазик, не на булгарски или еден друг јазик.'
        },
        'reflective_coach': {
            'en': 'You are a reflective coach who guides thoughtful self-exploration. Ask meaningful questions, help users understand their emotions, and encourage growth. Use reflection and gentle probing. Always respond in English.',
            'mk': 'Ти си рефлексивен тренер кој води замислливо самоисследување. Постави значајни прашања, помогни на корисниците да ги разберат нивните емоции и охрабри раст. Користи рефлексија и благо истражување. ВАЖНО: Секогаш одговарај ИСКЛУЧИВО на македонски јазик, не на булгарски или еден друг јазик.'
        },
        'neutral_assistant': {
            'en': 'You are a neutral, balanced assistant. Provide clear, factual information without judgment. Help organize thoughts and consider different perspectives objectively. Always respond in English.',
            'mk': 'Ти си неутрален, рамнотежен асистент. Обезбеди јасна, фактичка информација без пресуда. Помогни да се организираат мислите и разгледај различни перспективи објективно. ВАЖНО: Секогаш одговарај ИСКЛУЧИВО на македонски јазик, не на булгарски или еден друг јазик.'
        }
    }
    
    system_prompt = system_prompts.get(persona, system_prompts['supportive_friend']).get(language, system_prompts['supportive_friend']['en'])
    
    try:
        response = openai.ChatCompletion.create(
            model='gpt-4.1-mini',
            messages=[
                {'role': 'system', 'content': system_prompt},
                *messages
            ],
            temperature=0.7,
            max_tokens=500,
            top_p=0.95
        )
        
        response_text = response['choices'][0]['message']['content']
        return response_text
    
    except Exception as e:
        print(f'Error calling OpenAI API: {str(e)}')
        raise


def extract_sentiment(text):
    """
    Extract sentiment/mood from text using OpenAI.
    
    Args:
        text: Text to analyze
    
    Returns:
        str: Detected mood (positive, negative, neutral)
    """
    
    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    'role': 'system',
                    'content': 'Analyze the sentiment of the following text and respond with only one word: positive, negative, or neutral.'
                },
                {'role': 'user', 'content': text}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        mood = response['choices'][0]['message']['content'].lower().strip()
        if mood not in ['positive', 'negative', 'neutral']:
            mood = 'neutral'
        return mood
    
    except Exception as e:
        print(f'Error extracting sentiment: {str(e)}')
        return 'neutral'
