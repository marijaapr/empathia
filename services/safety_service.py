"""Safety and content moderation service."""


def is_content_safe(text):
    """
    Check if content is safe to process.
    
    Args:
        text: Text to check
    
    Returns:
        tuple: (is_safe, reason)
    """
    
    # Check for harmful keywords
    harmful_keywords = [
        'suicide', 'self-harm', 'kill myself', 'hurt myself',
        'dangerous', 'weapon', 'violence'
    ]
    
    text_lower = text.lower()
    
    for keyword in harmful_keywords:
        if keyword in text_lower:
            return False, f'Content contains sensitive keywords that require professional help.'
    
    # Check for reasonable length
    if len(text) > 5000:
        return False, 'Message is too long. Please keep messages under 5000 characters.'
    
    if len(text.strip()) == 0:
        return False, 'Please enter a message.'
    
    return True, None


def get_safety_warning(reason, language='en'):
    """
    Get a safety warning message.
    
    Args:
        reason: Reason for the warning
        language: Language code (en or mk)
    
    Returns:
        str: Safety warning message
    """
    
    warnings = {
        'en': f'{reason} If you\'re in crisis, please reach out to a mental health professional or crisis line.',
        'mk': f'{reason} Ако си во криза, ве молиме контактирајте ментален здравствен професионалец или линија за криза.'
    }
    
    return warnings.get(language, warnings['en'])


def sanitize_input(text):
    """
    Sanitize user input.
    
    Args:
        text: Text to sanitize
    
    Returns:
        str: Sanitized text
    """
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove potentially harmful characters (keep basic punctuation)
    import re
    text = re.sub(r'[^\w\s\.\!\?\,\'\"\-]', '', text)
    
    return text.strip()


def validate_persona(persona):
    """
    Validate persona selection.
    
    Args:
        persona: Persona string
    
    Returns:
        str: Valid persona or default
    """
    
    valid_personas = ['supportive_friend', 'reflective_coach', 'neutral_assistant']
    
    if persona in valid_personas:
        return persona
    return 'supportive_friend'


def validate_language(language):
    """
    Validate language selection.
    
    Args:
        language: Language code
    
    Returns:
        str: Valid language code or default
    """
    
    valid_languages = ['en', 'mk']
    
    if language in valid_languages:
        return language
    return 'en'
