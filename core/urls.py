from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('terms-policy/', views.terms_policy_view, name='terms_policy'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('moderator/dashboard/', views.moderator_dashboard, name='moderator_dashboard'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('institute/dashboard/', views.institute_dashboard, name='institute_dashboard'),
]
