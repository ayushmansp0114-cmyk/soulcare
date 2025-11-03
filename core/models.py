from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.utils import timezone
from datetime import timedelta
import os
import json

# Encryption key
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('user', 'User/Student'),
        ('doctor', 'Doctor'),
        ('institute', 'Institute Manager'),
        ('moderator', 'Moderator/Developer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    age = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True, help_text='Weight in kg')
    height = models.FloatField(null=True, blank=True, help_text='Height in cm')
    phone = models.CharField(max_length=15, null=True, blank=True)
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_checkin_date = models.DateField(null=True, blank=True)
    institute = models.ForeignKey('Institute', on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_bot_suspected = models.BooleanField(default=False)
    registration_data = models.TextField(blank=True)
    
    def update_level(self):
        self.level = (self.points // 100) + 1
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Institute(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=200)
    manager = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.TextField()
    registration_number = models.CharField(max_length=100, unique=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    id_document = models.FileField(upload_to='institute_docs/')
    license_document = models.FileField(upload_to='institute_docs/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Doctor(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name='doctors')
    license_number = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    experience = models.IntegerField(help_text='Years of experience')
    qualification = models.CharField(max_length=200)
    id_document = models.FileField(upload_to='doctor_docs/')
    license_document = models.FileField(upload_to='doctor_docs/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"

class UserApproval(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspicious', 'Suspicious - Manual Review'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    ml_score = models.FloatField(default=0.0, help_text='ML bot detection score (0-1)')
    is_bot_suspected = models.BooleanField(default=False)
    requested_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approvals_made')
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"

class CheckIn(models.Model):
    MOOD_CHOICES = [
        (1, '😢 Very Sad'),
        (2, '😟 Sad'),
        (3, '😐 Neutral'),
        (4, '🙂 Happy'),
        (5, '😄 Very Happy'),
    ]
    
    ENERGY_CHOICES = [
        (1, '🔋 Low'),
        (2, '⚡ Medium'),
        (3, '💪 High'),
    ]
    
    SLEEP_CHOICES = [
        (1, 'Poor'),
        (2, 'Fair'),
        (3, 'Good'),
        (4, 'Excellent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    mood = models.IntegerField(choices=MOOD_CHOICES)
    energy = models.IntegerField(choices=ENERGY_CHOICES)
    sleep_quality = models.IntegerField(choices=SLEEP_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"

class Assessment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    total_score = models.IntegerField()
    depression_score = models.IntegerField()
    anxiety_score = models.IntegerField()
    stress_score = models.IntegerField()
    severity = models.CharField(max_length=20)
    recommendations = models.TextField()
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.severity} ({self.date.date()})"

class Badge(models.Model):
    BADGE_TYPES = [
        ('streak_3', '3-Day Streak 🔥'),
        ('streak_7', '7-Day Streak 🔥'),
        ('streak_14', '14-Day Streak 🔥'),
        ('streak_30', '30-Day Streak 🔥'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    earned_date = models.DateTimeField(auto_now_add=True)
    claimed = models.BooleanField(default=False)
    points_awarded = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'badge_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_badge_type_display()}"

class Consultation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    ]
    
    URGENCY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_consultations')
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='doctor_consultations')
    issue = models.TextField()
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_date = models.DateTimeField(auto_now_add=True)
    accepted_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Consultation: {self.patient.username} - {self.status}"

class ChatMessage(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    encrypted_message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def encrypt_message(self, plain_text):
        self.encrypted_message = cipher_suite.encrypt(plain_text.encode()).decode()
    
    def decrypt_message(self):
        try:
            return cipher_suite.decrypt(self.encrypted_message.encode()).decode()
        except:
            return '[Decryption Error]'
    
    def __str__(self):
        return f"{self.sender.username} - {self.timestamp}"

class GitaVerse(models.Model):
    verse_number = models.CharField(max_length=20)
    sanskrit = models.TextField()
    english = models.TextField()
    meaning = models.TextField()
    
    def __str__(self):
        return self.verse_number

class InstituteLeaderboard(models.Model):
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_points = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['institute', '-total_points']
    
    def __str__(self):
        return f"{self.institute.name} - {self.user.username} - Rank {self.rank}"

class RemovalRequest(models.Model):
    ENTITY_TYPES = [
        ('doctor', 'Doctor'),
        ('institute', 'Institute'),
        ('user', 'User'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='removal_requests')
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    entity_id = models.IntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='removals_processed')
    
    def __str__(self):
        return f"{self.entity_type} removal - {self.status}"

class ActivityRecommendation(models.Model):
    ACTIVITY_TYPES = [
        ('yoga', 'Yoga'),
        ('exercise', 'Exercise'),
        ('outdoor', 'Outdoor Activity'),
        ('meditation', 'Meditation'),
        ('breathing', 'Breathing Exercise'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.IntegerField(help_text='Duration in minutes')
    difficulty = models.CharField(max_length=20)
    recommended_date = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class MentalHealthAlert(models.Model):
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High - Urgent'),
        ('critical', 'Critical - Immediate Action'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    detected_keywords = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    context = models.TextField(help_text='Where was this detected')
    message_content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    doctor_notified = models.BooleanField(default=False)
    institute_notified = models.BooleanField(default=False)
    action_taken = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f'{self.user.username} - {self.severity} - {self.timestamp}'

class InstantRecommendation(models.Model):
    ACTIVITY_TYPES = [
        ('yoga', 'Yoga'),
        ('breathing', 'Breathing Exercise'),
        ('music', 'Calming Music'),
        ('meditation', 'Meditation'),
        ('exercise', 'Physical Exercise'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    youtube_url = models.URLField()
    bonus_points = models.IntegerField(default=10)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user.username} - {self.title}'
class LoginActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} logged in at {self.timestamp}"