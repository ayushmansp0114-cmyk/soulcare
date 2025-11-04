import requests
from .mental_health_analyzer import analyze_mental_health_text, get_instant_recommendations
from .models import MentalHealthAlert, InstantRecommendation, UserProfile, Doctor

API_KEY = 'AIzaSyCXSC42nZ03lzZ_kIB-CzTh3Vf8k9l8SUw'
MODEL = 'gemini-2.0-flash-exp'

def query_gemini_api(user_text, user):
    '''
    Query Gemini API and analyze for mental health concerns
    '''
    # Analyze text for mental health keywords
    severity, keywords = analyze_mental_health_text(user_text)
    
    # If mental health issue detected, create alert
    if severity:
        alert = MentalHealthAlert.objects.create(
            user=user,
            detected_keywords=', '.join(keywords),
            severity=severity,
            context='AI Chatbot Conversation',
            message_content=user_text,
            doctor_notified=False,
            institute_notified=False
        )
        
        # Get instant recommendations
        recommendations = get_instant_recommendations(severity)
        for rec in recommendations:
            InstantRecommendation.objects.create(
                user=user,
                activity_type=rec['type'],
                title=rec['title'],
                youtube_url=rec['url'],
                bonus_points=rec['points']
            )
        
        # Notify doctor and institute manager
        notify_staff_about_alert(user, alert)
    
    # Query Gemini API
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}'
    headers = {'Content-Type': 'application/json'}
    payload = {
        'contents': [{
            'parts': [{
                'text': f'You are a compassionate mental health support assistant. Help the user with empathy and care. Never mention that you are AI. User says: {user_text}'
            }]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            bot_response = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'I understand. Please talk to a doctor for better support.')
            return bot_response, severity
        else:
            return 'I am here to listen. Please share what you are feeling.', severity
    except Exception as e:
        return 'I am having trouble responding. Please contact your doctor.', severity

def notify_staff_about_alert(user, alert):
    '''
    Secretly notify doctor and institute manager
    '''
    profile = UserProfile.objects.get(user=user)
    
    # Notify institute manager
    if profile.institute:
        alert.institute_notified = True
    
    # Find doctor in same institute
    doctors = Doctor.objects.filter(institute=profile.institute, status='approved')
    if doctors.exists():
        alert.doctor_notified = True
    
    alert.save()
