import re
import pickle
import os

# Load trained bot detection model
MODEL_PATH = 'core/bot_detection_model.pkl'
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, 'rb') as f:
        bot_model = pickle.load(f)
else:
    bot_model = None

def detect_bot_registration(username, email, first_name, last_name, age, phone=None):
    '''
    ML-based bot detection for user registration
    Returns: (is_bot, confidence_score, reasons_list)
    '''
    features = []
    reasons = []
    
    # Feature 1: Username pattern (user123, test456 = suspicious)
    username_pattern = 1 if re.match(r'^(user|test|bot|admin)\d+$', username.lower()) else 0
    features.append(username_pattern)
    if username_pattern:
        reasons.append('Generic username pattern detected')
    
    # Feature 2: Email domain check
    suspicious_domains = ['tempmail', 'throwaway', 'guerrillamail', '10minute', 'trash', 'fake']
    email_suspicious = 1 if any(domain in email.lower() for domain in suspicious_domains) else 0
    features.append(email_suspicious)
    if email_suspicious:
        reasons.append('Suspicious email domain')
    
    # Feature 3: Name length (very short names = suspicious)
    name_length = len(first_name) + len(last_name)
    features.append(name_length)
    if name_length < 5:
        reasons.append('Very short name (possible bot)')
    
    # Feature 4: Age validation
    age_suspicious = 1 if (age and (age < 10 or age > 100)) else 0
    features.append(age_suspicious)
    if age_suspicious:
        reasons.append('Unrealistic age provided')
    
    # Use ML model if available
    if bot_model:
        try:
            prediction = bot_model.predict([features])[0]
            confidence = bot_model.predict_proba([features])[0][1]
            is_bot = prediction == 1
            score = round(confidence, 2)
        except:
            # Fallback to rule-based
            score = sum(features) / len(features)
            is_bot = score >= 0.5
    else:
        # Simple rule-based scoring
        score = sum(features) / len(features)
        is_bot = score >= 0.5
    
    return is_bot, score, reasons

def generate_activity_recommendations(age, weight, height):
    '''Generate personalized fitness activities based on user profile'''
    bmi = weight / ((height/100) ** 2) if height and weight else 22
    
    activities = []
    
    if age < 18:
        activities = [
            {'type': 'outdoor', 'title': 'Outdoor Play & Sports', 'description': 'Play cricket, football, or run outside for 60 minutes', 'duration': 60, 'difficulty': 'Easy'},
            {'type': 'yoga', 'title': 'Kids Yoga & Stretching', 'description': 'Simple yoga poses and breathing exercises', 'duration': 20, 'difficulty': 'Easy'},
            {'type': 'music', 'title': 'Dance to Music', 'description': 'Fun dancing to energetic music', 'duration': 30, 'difficulty': 'Easy'},
        ]
    elif age < 40:
        if bmi > 25:
            activities = [
                {'type': 'exercise', 'title': 'HIIT Cardio Workout', 'description': 'High-intensity training to burn calories', 'duration': 30, 'difficulty': 'Hard'},
                {'type': 'yoga', 'title': 'Power Yoga Flow', 'description': 'Dynamic yoga for weight management', 'duration': 45, 'difficulty': 'Medium'},
            ]
        else:
            activities = [
                {'type': 'exercise', 'title': 'Strength Training', 'description': 'Build muscle and stamina', 'duration': 40, 'difficulty': 'Medium'},
                {'type': 'yoga', 'title': 'Vinyasa Yoga', 'description': 'Flowing yoga sequence for flexibility', 'duration': 45, 'difficulty': 'Medium'},
            ]
    else:  # Age 40+
        activities = [
            {'type': 'yoga', 'title': 'Gentle Hatha Yoga', 'description': 'Relaxing yoga for joints and flexibility', 'duration': 30, 'difficulty': 'Easy'},
            {'type': 'exercise', 'title': 'Brisk Walking', 'description': 'Cardiovascular health through walking', 'duration': 40, 'difficulty': 'Easy'},
            {'type': 'meditation', 'title': 'Mindfulness Meditation', 'description': 'Calm your mind with guided meditation', 'duration': 20, 'difficulty': 'Easy'},
        ]
    
    return activities
