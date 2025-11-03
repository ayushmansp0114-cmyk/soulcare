from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .forms import *
from .ml_utils import detect_bot_registration, generate_activity_recommendations
from .mental_health_analyzer import analyze_mental_health_text
import random
import json
import os

# User/Student Registration with ML Bot Detection
def register_user_student(request):
    '''Register as student with ML bot detection'''
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            age = int(request.POST.get('age', 0))
            weight = float(request.POST.get('weight', 0)) if request.POST.get('weight') else 0
            height = float(request.POST.get('height', 0)) if request.POST.get('height') else 0
            phone = request.POST.get('phone', '')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            institute_code = request.POST.get('institute_code')
            
            # Validate passwords match
            if password1 != password2:
                messages.error(request, '❌ Passwords do not match!')
                return render(request, 'core/register_user.html')
            
            # Check institute exists and approved
            try:
                institute = Institute.objects.get(registration_number=institute_code, status='approved')
            except Institute.DoesNotExist:
                messages.error(request, '❌ Invalid institute code or institute not approved yet!')
                return render(request, 'core/register_user.html')
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, '❌ Username already taken!')
                return render(request, 'core/register_user.html')
            
            # 🤖 ML BOT DETECTION
            is_bot, ml_score, reasons = detect_bot_registration(username, email, first_name, last_name, age, phone)
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                role='user',
                age=age,
                weight=weight,
                height=height,
                phone=phone,
                institute=institute,
                is_approved=not is_bot,  # Auto-approve if not bot
                is_bot_suspected=is_bot
            )
            profile.update_level()
            
            # Create approval record
            UserApproval.objects.create(
                user=user,
                institute=institute,
                status='approved' if not is_bot else 'suspicious',
                ml_score=ml_score,
                is_bot_suspected=is_bot,
                notes=f'ML Alert: {", ".join(reasons)}' if reasons else 'Auto-approved (legitimate user)'
            )
            
            # 👟 Generate personalized activity recommendations
            activities = generate_activity_recommendations(age, weight or 65, height or 170)
            for activity in activities:
                ActivityRecommendation.objects.create(
                    user=user,
                    activity_type=activity['type'],
                    title=activity['title'],
                    description=activity['description'],
                    duration=activity['duration'],
                    difficulty=activity['difficulty']
                )
            
            if is_bot:
                messages.warning(request, f'⚠️ Your registration is under review by institute manager (ML Score: {ml_score})')
                return redirect('login')
            else:
                messages.success(request, '✅ Registration successful! You can login now.')
                return redirect('login')
                
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return render(request, 'core/register_user.html')
    
    return render(request, 'core/register_user.html')

# Institute Registration with OCR ID Card Scanning
def institute_register_view(request):
    '''Register institute with OCR document verification'''
    if request.method == 'POST':
        try:
            from .id_scanner import verify_id_document
            
            name = request.POST.get('name')
            registration_number = request.POST.get('registration_number')
            address = request.POST.get('address')
            contact_email = request.POST.get('contact_email')
            contact_phone = request.POST.get('contact_phone')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            # Validate passwords
            if password != password_confirm:
                messages.error(request, '❌ Passwords do not match!')
                return render(request, 'core/institute_register.html')
            
            # Check if username exists
            if User.objects.filter(username=username).exists():
                messages.error(request, '❌ Username already taken!')
                return render(request, 'core/institute_register.html')
            
            # 📄 OCR SCAN - Manager ID Document
            id_file = request.FILES.get('id_document')
            license_file = request.FILES.get('license_document')
            
            if not id_file or not license_file:
                messages.error(request, '❌ Please upload all required documents!')
                return render(request, 'core/institute_register.html')
            
            # Process ID document with OCR
            id_result = verify_id_document(id_file, 'temp_id.jpg')
            if not id_result['success']:
                messages.error(request, f"❌ Error scanning ID: {id_result['error']}")
                return render(request, 'core/institute_register.html')
            
            # Create manager user
            manager_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create user profile for manager
            UserProfile.objects.create(
                user=manager_user,
                role='institute'
            )
            
            # Create institute
            institute = Institute.objects.create(
                name=name,
                manager=manager_user,
                registration_number=registration_number,
                address=address,
                contact_email=contact_email,
                contact_phone=contact_phone,
                status='pending'  # Awaiting moderator approval
            )
            
            # Save documents
            if id_file:
                institute.id_document = id_file
            if license_file:
                institute.license_document = license_file
            institute.save()
            
            messages.success(request, '✅ Institute registered! Awaiting moderator approval.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return render(request, 'core/institute_register.html')
    
    return render(request, 'core/institute_register.html')

# Doctor Registration with OCR and ML validation
def doctor_apply_view(request):
    '''Doctor application with document verification'''
    if request.method == 'POST':
        try:
            from .id_scanner import verify_id_document
            
            license_number = request.POST.get('license_number')
            specialization = request.POST.get('specialization')
            experience = int(request.POST.get('experience', 0))
            qualification = request.POST.get('qualification')
            institute_code = request.POST.get('institute_code')
            
            id_file = request.FILES.get('id_document')
            license_file = request.FILES.get('license_document')
            
            if not id_file or not license_file:
                messages.error(request, '❌ Please upload all required documents!')
                return render(request, 'core/register_doctor.html')
            
            # Check institute exists
            try:
                institute = Institute.objects.get(registration_number=institute_code, status='approved')
            except Institute.DoesNotExist:
                messages.error(request, '❌ Invalid institute code!')
                return render(request, 'core/register_doctor.html')
            
            # 📄 OCR SCAN - Medical License
            license_result = verify_id_document(license_file, 'temp_license.jpg')
            if not license_result['success']:
                messages.warning(request, '⚠️ Could not read license image clearly, but saved for manual review')
            
            # Get current user or create
            user = request.user if request.user.is_authenticated else None
            
            if not user:
                messages.error(request, '❌ Please login first or register!')
                return render(request, 'core/register_doctor.html')
            
            # Create doctor profile
            doctor = Doctor.objects.create(
                user=user,
                institute=institute,
                license_number=license_number,
                specialization=specialization,
                experience=experience,
                qualification=qualification,
                status='pending'  # Awaiting moderator approval
            )
            
            # Save documents
            if id_file:
                doctor.id_document = id_file
            if license_file:
                doctor.license_document = license_file
            doctor.save()
            
            messages.success(request, '✅ Doctor application submitted! Awaiting moderator approval.')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return render(request, 'core/register_doctor.html')
    
    return render(request, 'core/register_doctor.html')
