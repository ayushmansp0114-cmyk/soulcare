from django.urls import path
from . import views

urlpatterns = [
    # ============= PUBLIC PAGES =============
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('terms-policy/', views.terms_policy_view, name='terms_policy'),
    
    # ============= REGISTRATION PATHS =============
    path('register/', views.register_view, name='register'),  # ✅ THIS WAS MISSING!
    path('register/institute/', views.institute_register_view, name='institute_register'),
    path('register/doctor/', views.doctor_apply_view, name='doctor_apply'),
    
    # ============= USER DASHBOARD =============
    path('dashboard/', views.dashboard, name='dashboard'),
    path('checkin/', views.checkin_view, name='checkin'),
    path('assessment/', views.assessment_view, name='assessment'),
    path('assessment/result/<int:assessment_id>/', views.assessment_result, name='assessment_result'),
    path('activities/', views.activities_view, name='activities'),
    path('rewards/', views.rewards_view, name='rewards'),
    path('consultation/request/', views.consultation_request_view, name='consultation_request'),
    path('chat/<int:consultation_id>/', views.chat_view, name='chat'),
    
    # ============= DOCTOR DASHBOARD =============
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    
    # ============= INSTITUTE DASHBOARD =============
    path('institute/dashboard/', views.institute_dashboard, name='institute_dashboard'),
    
    # ============= MODERATOR DASHBOARD =============
    path('moderator/dashboard/', views.moderator_dashboard, name='moderator_dashboard'),
    path('moderator/removal-request/', views.removal_request_view, name='removal_request'),
    
    # ============= CHATBOT =============
    path('chatbot/', views.chatbot_ui, name='chatbot_ui'),
    path('chatbot/api/', views.chatbot_api, name='chatbot_api'),
    path('chatbot/complete/<int:rec_id>/', views.complete_recommendation, name='complete_recommendation'),
    
    # ============= PASSWORD RESET =============
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # ============= API/UTILITY =============
    path('api/test/', views.api_test, name='api_test'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),
]
