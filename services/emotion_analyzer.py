"""
Emotion Detection Service
Analyzes user messages to detect emotional states and determine urgency
"""

from typing import Dict, List, Tuple
import re


class EmotionDetector:
    """Service for detecting emotional states and urgency levels"""

    # Define emotion keywords and their categories
    EMOTION_KEYWORDS = {
        "depression": {
            "keywords": [
                "depressed", "depression", "hopeless", "worthless", "empty",
                "no point", "can't get out of bed", "dark", "empty inside",
                "never going to", "always fail", "never enough"
            ],
            "specializations": ["depression", "mental_health", "therapy"],
            "urgency": "high"
        },
        "anxiety": {
            "keywords": [
                "anxious", "anxiety", "worried", "panic", "nervous",
                "can't sleep", "stress", "overwhelming", "scared",
                "afraid", "terror", "dread", "heart racing"
            ],
            "specializations": ["anxiety", "panic_disorders", "stress_management"],
            "urgency": "high"
        },
        "panic": {
            "keywords": [
                "panic attack", "panic", "can't breathe", "chest pain",
                "going to die", "losing control", "suffocating",
                "hyperventilating", "heart attack", "fainting"
            ],
            "specializations": ["panic_disorders", "anxiety", "emergency_response"],
            "urgency": "high"
        },
        "loneliness": {
            "keywords": [
                "lonely", "loneliness", "alone", "no one cares", "isolated",
                "nobody likes me", "abandoned", "forgotten", "disconnected"
            ],
            "specializations": ["social_anxiety", "depression", "relationship_therapy"],
            "urgency": "medium"
        },
        "grief": {
            "keywords": [
                "grief", "death", "died", "loss", "mourn", "crying",
                "miss you", "can't cope", "lost someone", "devastated"
            ],
            "specializations": ["grief_counseling", "bereavement", "loss_management"],
            "urgency": "medium"
        },
        "burnout": {
            "keywords": [
                "burnout", "burned out", "exhausted", "tired", "worn out",
                "no energy", "can't work", "overwhelmed at work", "giving up"
            ],
            "specializations": ["burnout", "stress_management", "career_counseling"],
            "urgency": "medium"
        },
        "suicidal_ideation": {
            "keywords": [
                "suicide", "suicidal", "want to die", "kill myself", "end it",
                "no reason to live", "better off dead", "hurt myself",
                "harm myself", "cutting"
            ],
            "specializations": ["crisis_intervention", "mental_health", "emergency"],
            "urgency": "high"
        },
        "substance_abuse": {
            "keywords": [
                "drinking", "alcohol", "drugs", "cocaine", "heroin",
                "addiction", "addicted", "using", "high", "drunk",
                "party", "substance abuse"
            ],
            "specializations": ["addiction_counseling", "substance_abuse", "recovery"],
            "urgency": "high"
        },
        "trauma": {
            "keywords": [
                "trauma", "traumatic", "abuse", "raped", "assault",
                "ptsd", "flashback", "nightmares", "triggered",
                "violent", "attacked", "domestic violence"
            ],
            "specializations": ["trauma_therapy", "ptsd", "abuse_recovery"],
            "urgency": "high"
        },
        "eating_disorder": {
            "keywords": [
                "eating disorder", "anorexia", "bulimia", "binge eating",
                "fat", "weight", "restrict", "purge", "body image",
                "don't eat", "starving", "overweight"
            ],
            "specializations": ["eating_disorders", "nutrition_therapy", "body_image"],
            "urgency": "medium"
        }
    }

    # Positive indicators
    POSITIVE_KEYWORDS = [
        "happy", "great", "wonderful", "amazing", "better", "improved",
        "feeling good", "grateful", "blessed", "love", "enjoying",
        "progress", "proud", "excited", "hopeful", "positive"
    ]

    @classmethod
    def detect_emotions(cls, message: str) -> Tuple[List[str], List[Dict]]:
        """
        Detect emotional states in a message
        
        Args:
            message: User message text
            
        Returns:
            Tuple of (detected_emotions, emotion_details)
        """
        message_lower = message.lower()
        detected_emotions = []
        emotion_details = []

        for emotion, data in cls.EMOTION_KEYWORDS.items():
            for keyword in data["keywords"]:
                if cls._keyword_match(message_lower, keyword):
                    if emotion not in detected_emotions:
                        detected_emotions.append(emotion)
                        emotion_details.append({
                            "emotion": emotion,
                            "specializations": data["specializations"],
                            "urgency": data["urgency"],
                            "keyword_matched": keyword
                        })
                    break

        return detected_emotions, emotion_details

    @classmethod
    def determine_urgency_level(
        cls,
        emotions: List[str],
        message: str
    ) -> str:
        """
        Determine urgency level based on detected emotions
        
        Args:
            emotions: List of detected emotions
            message: Original message
            
        Returns:
            Urgency level: 'low', 'medium', or 'high'
        """
        # Check for highest urgency emotions
        high_urgency_emotions = [
            "panic", "suicidal_ideation", "trauma", "substance_abuse"
        ]

        if any(e in high_urgency_emotions for e in emotions):
            return "high"

        # Check for high-urgency indicators in message
        danger_indicators = [
            "hurt myself", "harm myself", "kill myself", "end it",
            "can't take it", "can't go on", "no way out"
        ]

        if any(indicator in message.lower() for indicator in danger_indicators):
            return "high"

        # Check for medium urgency emotions
        medium_urgency_emotions = [
            "depression", "anxiety", "loneliness", "grief", "burnout"
        ]

        if any(e in medium_urgency_emotions for e in emotions):
            return "medium"

        return "low"

    @classmethod
    def get_recommended_specializations(
        cls,
        emotions: List[Dict]
    ) -> List[str]:
        """
        Get recommended psychologist specializations
        
        Args:
            emotions: List of emotion details
            
        Returns:
            List of recommended specializations
        """
        specializations = set()

        for emotion_detail in emotions:
            specializations.update(emotion_detail["specializations"])

        # Sort by frequency and importance
        specialization_counts = {}
        for emotion_detail in emotions:
            for spec in emotion_detail["specializations"]:
                specialization_counts[spec] = specialization_counts.get(spec, 0) + 1

        # Sort by count (descending)
        sorted_specs = sorted(
            specialization_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [spec for spec, count in sorted_specs]

    @classmethod
    def is_positive_message(cls, message: str) -> bool:
        """
        Check if message contains positive sentiment
        
        Args:
            message: User message text
            
        Returns:
            Boolean indicating positive sentiment
        """
        message_lower = message.lower()

        positive_count = sum(
            1 for keyword in cls.POSITIVE_KEYWORDS
            if cls._keyword_match(message_lower, keyword)
        )

        return positive_count > 0

    @classmethod
    def _keyword_match(cls, text: str, keyword: str) -> bool:
        """
        Check if keyword matches in text (word boundary aware)
        
        Args:
            text: Text to search in
            keyword: Keyword to find
            
        Returns:
            Boolean indicating match
        """
        # Use word boundaries for more accurate matching
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    @classmethod
    def analyze_message(cls, message: str) -> Dict:
        """
        Complete analysis of a message
        
        Args:
            message: User message text
            
        Returns:
            Dictionary with complete analysis
        """
        emotions, emotion_details = cls.detect_emotions(message)
        urgency_level = cls.determine_urgency_level(emotions, message)
        specializations = cls.get_recommended_specializations(emotion_details)
        is_positive = cls.is_positive_message(message)

        return {
            "detected_emotions": emotions,
            "emotion_details": emotion_details,
            "urgency_level": urgency_level,
            "recommended_specializations": specializations,
            "is_positive": is_positive,
            "should_recommend_psychologist": urgency_level in ["medium", "high"],
            "recommendation_priority": {
                "high": 1,
                "medium": 2,
                "low": 3
            }.get(urgency_level, 3)
        }
