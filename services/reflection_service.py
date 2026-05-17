"""Self-reflection guidance service."""


def generate_reflection_prompt(language='en'):
    """
    Generate a reflection prompt for the user.
    
    Args:
        language: Language code (en or mk)
    
    Returns:
        str: Reflection prompt
    """
    
    prompts = {
        'en': [
            'What brought you joy today?',
            'What was one challenge you overcame?',
            'How did you take care of yourself today?',
            'What are you grateful for right now?',
            'What would make tomorrow better?',
            'What did you learn about yourself today?',
            'Who or what made a positive impact on your day?',
            'What is one thing you would like to improve?'
        ],
        'mk': [
            'Што ти донесе радост денес?',
            'Кој беше еден предизвик што го надолази?',
            'Како се грижеше за себе денес?',
            'За што си благодарен сега?',
            'Што би направило утрешниот ден подобар?',
            'Што научи за себе денес?',
            'Кој или што имаше позитивно влијание на твојот ден?',
            'Која е една работа што би сакал да ја подобриш?'
        ]
    }
    
    import random
    prompt_list = prompts.get(language, prompts['en'])
    return random.choice(prompt_list)


def create_reflection_response(user_input, language='en'):
    """
    Create a guided reflection response.
    
    Args:
        user_input: User's reflection input
        language: Language code (en or mk)
    
    Returns:
        str: Reflection guidance
    """
    
    if language == 'mk':
        return f"Благодарам што се рефлектира: \"{user_input}\". Размисли поглубоко - што е позадината на овој исказ? Кои емоции се вклучени?"
    else:
        return f"Thank you for sharing this reflection: \"{user_input}\". Consider exploring deeper - what's beneath the surface? What emotions are at play?"


def suggest_reflection_activity(emotion, language='en'):
    """
    Suggest a reflection activity based on emotion.
    
    Args:
        emotion: Current emotion
        language: Language code (en or mk)
    
    Returns:
        str: Suggested activity
    """
    
    activities = {
        'en': {
            'happy': 'Consider journaling about what brought you this joy and how you can create more moments like this.',
            'sad': 'Try writing about what you\'re feeling and what support or self-care you need right now.',
            'anxious': 'Consider doing a grounding exercise - notice 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste.',
            'angry': 'Take a moment to explore what need isn\'t being met. What would help you feel heard or validated?',
            'calm': 'This is a good time to set an intention for what you\'d like to focus on or achieve.',
            'neutral': 'Notice what you\'re thinking and feeling without judgment. Simple observation can be powerful.'
        },
        'mk': {
            'happy': 'Размисли да напишеш за она што ти донесе оваа радост и како можеш да создадеш повеќе такви моменти.',
            'sad': 'Обиди се да напишеш за она што чувствуваш и каква поддршка или самозбрижување ти треба сега.',
            'anxious': 'Обиди се да направиш вежба на укорнување - забележи 5 работи што можеш да видиш, 4 што можеш да допреш, 3 што можеш да слушаш, 2 што можеш да мириш, 1 што можеш да вкусиш.',
            'angry': 'Земи момент да истражиш која потреба не е исполнета. Што би ти помогнало да се чувствуваш слушана или валидирана?',
            'calm': 'Ово е добро време да постави намера за она на што сакаш да се фокусираш или постигнеш.',
            'neutral': 'Забележи во што мислиш и чувствуваш без пресуда. Едноставното набљудување може да биде моќно.'
        }
    }
    
    return activities.get(language, activities['en']).get(emotion, activities['en']['neutral'])
