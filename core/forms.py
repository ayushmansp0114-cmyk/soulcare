from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *

class UserRegistrationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('user', 'User/Student'),
        ('doctor', 'Doctor'),
        ('institute', 'Institute Manager'),
    ]
    
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    age = forms.IntegerField(required=True, min_value=10, max_value=100, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age'}))
    weight = forms.FloatField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight (kg)'}))
    height = forms.FloatField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Height (cm)'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}))
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input', 'style': 'margin-right:10px; margin-bottom:10px'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

class CheckInForm(forms.Form):
    MOOD_CHOICES = [('happy', 'Happy'), ('sad', 'Sad'), ('neutral', 'Neutral'), ('anxious', 'Anxious')]
    mood = forms.ChoiceField(choices=MOOD_CHOICES, widget=forms.RadioSelect(), required=True)
    energy = forms.ChoiceField(choices=MOOD_CHOICES, widget=forms.RadioSelect(), required=True)
    sleep_quality = forms.ChoiceField(choices=MOOD_CHOICES, widget=forms.RadioSelect(), required=True)
    notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes...'}), required=False)

class ConsultationRequestForm(forms.Form):
    URGENCY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')]
    issue = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your issue...'}), required=True)
    urgency = forms.ChoiceField(choices=URGENCY_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), required=True)

class RemovalRequestForm(forms.Form):
    entity_type = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    entity_id = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    reason = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason...'}))

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class DoctorApplicationForm(forms.Form):
    license_number = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Medical License Number'}))
    specialization = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specialization'}))
    experience = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Years of Experience'}))
    qualification = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qualifications'}))
    institute_code = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Institute Code'}))

class InstituteRegistrationForm(forms.Form):
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Institute Name'}))
    registration_number = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Registration Number'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    contact_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    contact_phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
