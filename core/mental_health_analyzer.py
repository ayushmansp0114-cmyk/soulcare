import re

# Crisis keywords and their severity
MENTAL_HEALTH_KEYWORDS = {
    'critical': ['suicide', 'kill myself', 'end my life', 'want to die', 'no reason to live', 'better off dead'],
    'high': ['self harm', 'cutting', 'hurt myself', 'suicidal', 'hopeless', 'worthless', 'can\'t take it'],
    'medium': ['depressed', 'depression', 'anxiety', 'panic attack', 'stressed out', 'overwhelming', 'breakdown'],
    'low': ['worried', 'anxious', 'pressure', 'stressed', 'sad', 'upset', 'struggling', 'difficult'],
}

def analyze_mental_health_text(text):
    '''
    Analyzes text for mental health keywords
    Returns: (severity, detected_keywords)
    '''
    text_lower = text.lower()
    detected = []
    severity = None
    
    # Check critical keywords first
    for level in ['critical', 'high', 'medium', 'low']:
        for keyword in MENTAL_HEALTH_KEYWORDS[level]:
            if keyword in text_lower:
                detected.append(keyword)
                if not severity:
                    severity = level
    
    return severity, detected

def get_instant_recommendations(severity):
    '''
    Returns immediate activity recommendations based on severity
    '''
    recommendations = []
    
    if severity in ['critical', 'high']:
        recommendations = [
            {
                'type': 'breathing',
                'title': '5-Minute Emergency Calm Down',
                'url': 'https://www.youtube.com/embed/tybOi4hjZFQ',
                'points': 20
            },
            {
                'type': 'meditation',
                'title': 'Guided Meditation for Anxiety',
                'url': 'https://www.youtube.com/embed/O-6f5wQXSu8',
                'points': 25
            },
        ]
    elif severity == 'medium':
        recommendations = [
            {
                'type': 'yoga',
                'title': 'Yoga for Stress Relief',
                'url': 'https://www.youtube.com/embed/COp7BR_Dvps',
                'points': 15
            },
            {
                'type': 'music',
                'title': 'Calming Music - Reduce Anxiety',
                'url': 'https://www.youtube.com/embed/1ZYbU82GVz4',
                'points': 10
            },
        ]
    else:  # low
        recommendations = [
            {
                'type': 'exercise',
                'title': 'Quick Mood Booster Exercise',
                'url': 'https://www.youtube.com/embed/UBMk30rjy0o',
                'points': 10
            },
            {
                'type': 'breathing',
                'title': 'Box Breathing Technique',
                'url': 'https://www.youtube.com/embed/tEmt1Znux58',
                'points': 10
            },
        ]
    
    return recommendations
