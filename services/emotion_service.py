"""Emotion tracking and analysis service."""


def categorize_emotion(mood_text):
    """
    Categorize emotion from text.
    
    Args:
        mood_text: Text describing an emotion
    
    Returns:
        str: Categorized emotion (happy, sad, anxious, angry, calm, neutral)
    """
    
    mood_text = mood_text.lower()
    
    # Emotion keywords mapping
    emotions = {
        'happy': ['happy', 'joyful', 'excited', 'great', 'wonderful', 'fantastic', 'amazing', 'good', 'cheerful', 'delighted'],
        'sad': ['sad', 'down', 'depressed', 'unhappy', 'miserable', 'blue', 'disappointed', 'sorry', 'gloomy'],
        'anxious': ['anxious', 'worried', 'nervous', 'stressed', 'afraid', 'scared', 'uneasy', 'tense', 'uptight'],
        'angry': ['angry', 'furious', 'mad', 'frustrated', 'irritated', 'resentful', 'livid'],
        'calm': ['calm', 'peaceful', 'relaxed', 'serene', 'tranquil', 'content', 'zen', 'composed'],
        'neutral': ['okay', 'fine', 'normal', 'usual', 'average', 'standard']
    }
    
    for emotion, keywords in emotions.items():
        for keyword in keywords:
            if keyword in mood_text:
                return emotion
    
    return 'neutral'


def get_emotion_description(emotion):
    """Get a description for an emotion."""
    descriptions = {
        'happy': 'You seem to be in a positive mood with joy and contentment.',
        'sad': 'You appear to be experiencing sadness or melancholy.',
        'anxious': 'It sounds like you might be feeling worried or stressed.',
        'angry': 'You seem to be experiencing frustration or anger.',
        'calm': 'You appear to be in a peaceful and relaxed state.',
        'neutral': 'You seem to be in a neutral or stable emotional state.'
    }
    return descriptions.get(emotion, 'Thank you for sharing your feelings.')


def get_emotion_description_mk(emotion):
    """Get a description for an emotion in Macedonian."""
    descriptions = {
        'happy': 'Изгледа дека си во позитивно расположение со радост и задоволство.',
        'sad': 'Изгледа дека ги доживуваш тагата или меланхолијата.',
        'anxious': 'Звучи дека можеби чувствуваш забринатост или стрес.',
        'angry': 'Изгледа дека доживуваш фрустрација или гнев.',
        'calm': 'Изгледа дека си во мирна и релаксирана состојба.',
        'neutral': 'Изгледа дека си во неутрална или стабилна емоционална состојба.'
    }
    return descriptions.get(emotion, 'Благодарам што ги делиш твоите чувства.')


def log_emotion_metric(emotion, intensity):
    """
    Create a metric for emotion tracking.
    
    Args:
        emotion: Emotion type
        intensity: Intensity level (1-10)
    
    Returns:
        dict: Emotion metric
    """
    return {
        'emotion': emotion,
        'intensity': max(1, min(10, intensity)),  # Clamp to 1-10
        'normalized_intensity': max(1, min(10, intensity)) / 10.0
    }
