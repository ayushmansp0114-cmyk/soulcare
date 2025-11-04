# Django Views - SoulCare Mental Health Platform
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
from datetime import datetime, timedelta
import json
import random
import os

from .models import (
    UserProfile, Doctor, Institute, ActivityRecommendation, 
    UserApproval, CheckIn, Assessment, Badge, 
    Consultation, ChatMessage, GitaVerse, 
    InstituteLeaderboard, RemovalRequest, MentalHealthAlert,
    InstantRecommendation
)
from .forms import (
    UserRegistrationForm, InstituteRegistrationForm, 
    DoctorApplicationForm, CheckInForm, ConsultationRequestForm,
    RemovalRequestForm
)
from .ml_utils import detect_bot_registration, generate_activity_recommendations
from .mental_health_analyzer import analyze_mental_health_text, get_instant_recommendations
from .gemini_chatbot import query_gemini_api

# ============= BOT DETECTION =============

def is_bot_access(request):
    '''Detect bot access patterns'''
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    bot_patterns = ['bot', 'crawler', 'spider', 'scraper', 'selenium', 'automation', 'headless']
    for pattern in bot_patterns:
        if pattern in user_agent:
            return True
    return False

# ============= PUBLIC VIEWS =============

def home(request):
    '''Home page'''
    return render(request, 'core/home.html')

def login_view(request):
    '''Enhanced login with bot detection and approval system'''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        is_bot = is_bot_access(request)
        user = authenticate(request, username=username, password=password)

        if is_bot:
            messages.error(request, '❌ Access denied: Bot detected')
            return render(request, 'core/login.html')

        if user is not None:
            try:
                profile = UserProfile.objects.get(user=user)
                role = profile.role
            except:
                role = 'unknown'

            needs_approval = False
            if role == 'doctor':
                try:
                    doctor = Doctor.objects.get(user=user)
                    needs_approval = doctor.status != 'approved'
                except:
                    pass
            elif role == 'institute':
                try:
                    institute = Institute.objects.get(manager=user)
                    needs_approval = institute.status != 'approved'
                except:
                    pass

            if needs_approval:
                return render(request, 'core/pending_approval.html', {'user': user, 'role': role.title()})

            login(request, user)

            if role == 'moderator':
                return redirect('moderator_dashboard')
            elif role == 'user':
                return redirect('dashboard')
            elif role == 'doctor':
                return redirect('doctor_dashboard')
            elif role == 'institute':
                return redirect('institute_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, '❌ Invalid credentials!')

    return render(request, 'core/login.html')

def logout_view(request):
    '''User logout'''
    logout(request)
    messages.success(request, '✅ You have been logged out!')
    return redirect('home')

# ============= USER REGISTRATION =============

def register_view(request):
    '''User/Student registration with ML bot detection'''
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

            # Validate passwords
            if password1 != password2:
                messages.error(request, '❌ Passwords do not match!')
                return render(request, 'core/register.html')

            # Check institute
            try:
                institute = Institute.objects.get(registration_number=institute_code, status='approved')
            except Institute.DoesNotExist:
                messages.error(request, '❌ Invalid institute code or institute not approved yet!')
                return render(request, 'core/register.html')

            # Check username
            if User.objects.filter(username=username).exists():
                messages.error(request, '❌ Username already taken!')
                return render(request, 'core/register.html')

            # ML Bot Detection
            is_bot, score, reasons = detect_bot_registration(username, email, first_name, last_name, age, phone)

            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )

            # Create profile
            profile = UserProfile.objects.create(
                user=user,
                role='user',
                age=age,
                weight=weight,
                height=height,
                phone=phone,
                institute=institute,
                is_approved=not is_bot,
                is_bot_suspected=is_bot
            )
            profile.update_level()

            # Create approval request
            UserApproval.objects.create(
                user=user,
                institute=institute,
                status='approved' if not is_bot else 'suspicious',
                ml_score=score,
                is_bot_suspected=is_bot,
                notes=f'ML Alert: {", ".join(reasons)}' if reasons else 'Auto-approved'
            )

            # Generate activities
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
                messages.warning(request, f'⚠️ Your registration is under review')
            else:
                messages.success(request, '✅ Registration successful! You can login now.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return render(request, 'core/register.html')

    return render(request, 'core/register.html')

def institute_register_view(request):
    '''Institute registration'''
    if request.method == 'POST':
        try:
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

            if password != password_confirm:
                messages.error(request, '❌ Passwords do not match!')
                return render(request, 'core/institute_register.html')

            if User.objects.filter(username=username).exists():
                messages.error(request, '❌ Username already taken!')
                return render(request, 'core/institute_register.html')

            # Create manager user
            manager_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            UserProfile.objects.create(user=manager_user, role='institute')

            # Create institute
            institute = Institute.objects.create(
                name=name,
                manager=manager_user,
                registration_number=registration_number,
                address=address,
                contact_email=contact_email,
                contact_phone=contact_phone,
                status='pending'
            )

            id_file = request.FILES.get('id_document')
            license_file = request.FILES.get('license_document')

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

def doctor_apply_view(request):
    '''Doctor application'''
    existing_doctor = Doctor.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    if existing_doctor:
        return render(request, 'core/doctor_apply.html', {'existing_application': existing_doctor})

    if request.method == 'POST':
        try:
            if not request.user.is_authenticated:
                messages.error(request, '❌ Please login first!')
                return redirect('login')

            license_number = request.POST.get('license_number')
            specialization = request.POST.get('specialization')
            experience = int(request.POST.get('experience', 0))
            qualification = request.POST.get('qualification')
            institute_code = request.POST.get('institute_code')

            try:
                institute = Institute.objects.get(registration_number=institute_code, status='approved')
            except Institute.DoesNotExist:
                messages.error(request, '❌ Invalid institute code!')
                return render(request, 'core/doctor_apply.html')

            doctor = Doctor.objects.create(
                user=request.user,
                institute=institute,
                license_number=license_number,
                specialization=specialization,
                experience=experience,
                qualification=qualification,
                status='pending'
            )

            id_file = request.FILES.get('id_document')
            license_file = request.FILES.get('license_document')

            if id_file:
                doctor.id_document = id_file
            if license_file:
                doctor.license_document = license_file
            doctor.save()

            messages.success(request, '✅ Doctor application submitted! Awaiting moderator approval.')
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return render(request, 'core/doctor_apply.html')

    return render(request, 'core/doctor_apply.html')

# ============= USER DASHBOARD =============

@login_required
def dashboard(request):
    '''User dashboard'''
    profile = UserProfile.objects.get(user=request.user)

    if profile.role != 'user':
        messages.error(request, 'Access denied.')
        return redirect('home')

    if not profile.is_approved:
        return render(request, 'core/pending_approval.html')

    today = timezone.now().date()
    checkins = CheckIn.objects.filter(user=request.user).order_by('-date')
    today_checkin = CheckIn.objects.filter(user=request.user, date=today).first()
    recent_checkins = CheckIn.objects.filter(user=request.user)[:7]
    latest_assessment = Assessment.objects.filter(user=request.user).first()
    gita_verse = GitaVerse.objects.order_by('?').first()
    recommendations = ActivityRecommendation.objects.filter(user=request.user, completed=False)[:3]
    badges = Badge.objects.filter(user=request.user)

    context = {
        'profile': profile,
        'today_checkin': today_checkin,
        'recent_checkins': recent_checkins,
        'latest_assessment': latest_assessment,
        'gita_verse': gita_verse,
        'badges': badges,
        'recommendations': recommendations,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def checkin_view(request):
    '''Daily check-in'''
    today = timezone.now().date()
    existing_checkin = CheckIn.objects.filter(user=request.user, date=today).first()

    if request.method == 'POST':
        if existing_checkin:
            messages.warning(request, 'You have already checked in today!')
            return redirect('dashboard')

        form = CheckInForm(request.POST)
        if form.is_valid():
            checkin = form.save(commit=False)
            checkin.user = request.user
            checkin.date = today
            checkin.save()

            profile = UserProfile.objects.get(user=request.user)
            profile.points += 5
            profile.update_level()

            messages.success(request, 'Check-in completed! +5 points earned.')
            return redirect('dashboard')
    else:
        form = CheckInForm()

    return render(request, 'core/checkin.html', {'form': form, 'existing_checkin': existing_checkin})

@login_required
def assessment_view(request):
    '''Mental health assessment'''
    questions = get_assessment_questions()

    if request.method == 'POST':
        answers = []
        for i in range(len(questions)):
            answer = request.POST.get(f'q{i}')
            if answer:
                answers.append(int(answer))

        if len(answers) == len(questions):
            total_score = sum(answers)

            if total_score < len(questions) * 0.3:
                severity = 'Minimal'
            elif total_score < len(questions) * 0.6:
                severity = 'Mild'
            elif total_score < len(questions) * 0.9:
                severity = 'Moderate'
            else:
                severity = 'Severe'

            recommendations = get_recommendations(severity)

            assessment = Assessment.objects.create(
                user=request.user,
                total_score=total_score,
                severity=severity,
                recommendations=recommendations
            )

            profile = UserProfile.objects.get(user=request.user)
            profile.points += 10
            profile.update_level()

            messages.success(request, 'Assessment completed! +10 points earned.')
            return redirect('assessment_result', assessment_id=assessment.id)

    return render(request, 'core/assessment.html', {'questions': questions})

@login_required
def assessment_result(request, assessment_id):
    '''Assessment result'''
    assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
    return render(request, 'core/assessment_result.html', {'assessment': assessment})

@login_required
def rewards_view(request):
    '''Rewards and badges'''
    profile = UserProfile.objects.get(user=request.user)
    badges = Badge.objects.filter(user=request.user)

    context = {
        'profile': profile,
        'badges': badges,
    }
    return render(request, 'core/rewards.html', context)

@login_required
def consultation_request_view(request):
    '''Request consultation with doctor'''
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'user':
        messages.error(request, 'Access denied.')
        return redirect('home')

    doctors = Doctor.objects.filter(institute=profile.institute, status='approved')

    if request.method == 'POST':
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.patient = request.user
            consultation.save()
            messages.success(request, 'Consultation request submitted!')
            return redirect('dashboard')
    else:
        form = ConsultationRequestForm()

    my_consultations = Consultation.objects.filter(patient=request.user).order_by('-requested_date')

    return render(request, 'core/consultation_request.html', {
        'form': form,
        'doctors': doctors,
        'my_consultations': my_consultations
    })

@login_required
def chat_view(request, consultation_id):
    '''Chat with doctor'''
    consultation = get_object_or_404(Consultation, id=consultation_id)

    if request.user != consultation.patient and request.user != consultation.doctor:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if consultation.status != 'accepted':
        messages.warning(request, 'Consultation not accepted yet.')
        return redirect('dashboard')

    messages_list = ChatMessage.objects.filter(consultation=consultation)

    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            chat_message = ChatMessage(consultation=consultation, sender=request.user)
            chat_message.save()
            return redirect('chat', consultation_id=consultation_id)

    return render(request, 'core/chat.html', {
        'consultation': consultation,
        'messages': messages_list,
    })

@login_required
def activities_view(request):
    '''Activities and recommendations'''
    profile = UserProfile.objects.get(user=request.user)
    recommendations = ActivityRecommendation.objects.filter(user=request.user).order_by('-recommended_date')

    if request.method == 'POST':
        activity_id = request.POST.get('activity_id')
        activity = get_object_or_404(ActivityRecommendation, id=activity_id, user=request.user)
        if not activity.completed:
            activity.completed = True
            activity.save()
            profile.points += 10
            profile.update_level()
            messages.success(request, 'Activity completed! +10 points earned.')
            return redirect('activities')

    return render(request, 'core/activities.html', {'recommendations': recommendations, 'profile': profile})

# ============= DOCTOR DASHBOARD =============

@login_required
def doctor_dashboard(request):
    '''Doctor dashboard'''
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('home')

    try:
        doctor = Doctor.objects.get(user=request.user)
        if doctor.status != 'approved':
            messages.warning(request, 'Your application is pending approval.')
            return redirect('home')
    except Doctor.DoesNotExist:
        messages.error(request, 'You are not registered as a doctor.')
        return redirect('home')

    pending_consultations = Consultation.objects.filter(status='pending').order_by('-requested_date')
    active_consultations = Consultation.objects.filter(doctor=request.user, status='accepted').order_by('-accepted_date')
    completed_consultations = Consultation.objects.filter(doctor=request.user, status='completed').order_by('-completed_date')[:10]

    if request.method == 'POST':
        action = request.POST.get('action')
        consultation_id = request.POST.get('consultation_id')
        consultation = get_object_or_404(Consultation, id=consultation_id)

        if action == 'accept':
            consultation.status = 'accepted'
            consultation.doctor = request.user
            consultation.accepted_date = timezone.now()
            consultation.save()
            messages.success(request, 'Consultation accepted!')
        elif action == 'decline':
            consultation.status = 'declined'
            consultation.save()
            messages.info(request, 'Consultation declined.')
        elif action == 'complete':
            consultation.status = 'completed'
            consultation.completed_date = timezone.now()
            consultation.save()
            messages.success(request, 'Consultation marked as completed.')

        return redirect('doctor_dashboard')

    context = {
        'doctor': doctor,
        'pending_consultations': pending_consultations,
        'active_consultations': active_consultations,
        'completed_consultations': completed_consultations,
    }
    return render(request, 'core/doctor_dashboard.html', context)

# ============= INSTITUTE DASHBOARD =============

@login_required
def institute_dashboard(request):
    '''Institute dashboard'''
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'institute':
        messages.error(request, 'Access denied.')
        return redirect('home')

    institute = Institute.objects.get(manager=request.user)
    pending_approvals = UserApproval.objects.filter(institute=institute, status__in=['pending', 'suspicious']).order_by('-requested_date')
    approved_users = UserProfile.objects.filter(institute=institute, is_approved=True)
    leaderboard = InstituteLeaderboard.objects.filter(institute=institute).order_by('-total_points')[:10]
    doctors = Doctor.objects.filter(institute=institute, status='approved')

    total_users = UserProfile.objects.filter(institute=institute, is_approved=True).count()
    total_doctors = doctors.count()
    total_consultations = Consultation.objects.filter(patient__userprofile__institute=institute).count()

    if request.method == 'POST':
        action = request.POST.get('action')
        approval_id = request.POST.get('approval_id')
        approval = get_object_or_404(UserApproval, id=approval_id, institute=institute)

        if action == 'approve':
            approval.status = 'approved'
            approval.approved_date = timezone.now()
            approval.approved_by = request.user
            approval.save()

            user_profile = UserProfile.objects.get(user=approval.user)
            user_profile.is_approved = True
            user_profile.save()

            InstituteLeaderboard.objects.create(
                institute=institute,
                user=approval.user,
                total_points=user_profile.points
            )

            messages.success(request, f'User {approval.user.username} approved!')
        elif action == 'reject':
            approval.status = 'rejected'
            approval.save()
            messages.info(request, f'User {approval.user.username} rejected.')

        return redirect('institute_dashboard')

    context = {
        'institute': institute,
        'pending_approvals': pending_approvals,
        'approved_users': approved_users,
        'leaderboard': leaderboard,
        'doctors': doctors,
        'total_users': total_users,
        'total_doctors': total_doctors,
        'total_consultations': total_consultations,
    }
    return render(request, 'core/institute_dashboard.html', context)

# ============= MODERATOR DASHBOARD =============

@login_required
def moderator_dashboard(request):
    '''Moderator dashboard'''
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'moderator':
        messages.error(request, 'Access denied.')
        return redirect('home')

    pending_institutes = Institute.objects.filter(status='pending')
    approved_institutes = Institute.objects.filter(status='approved')
    pending_doctors = Doctor.objects.filter(status='pending')
    approved_doctors = Doctor.objects.filter(status='approved')
    removal_requests = RemovalRequest.objects.filter(status='pending')

    total_users = UserProfile.objects.filter(role='user', is_approved=True).count()
    total_institutes = Institute.objects.filter(status='approved').count()
    total_doctors = Doctor.objects.filter(status='approved').count()

    if request.method == 'POST':
        action = request.POST.get('action')
        entity_type = request.POST.get('entity_type')
        entity_id = request.POST.get('entity_id')

        if entity_type == 'institute':
            institute = get_object_or_404(Institute, id=entity_id)
            if action == 'approve':
                institute.status = 'approved'
                institute.approved_date = timezone.now()
                institute.save()
                messages.success(request, f'{institute.name} approved!')
            elif action == 'reject':
                institute.status = 'rejected'
                institute.save()
                messages.info(request, f'{institute.name} rejected.')

        elif entity_type == 'doctor':
            doctor = get_object_or_404(Doctor, id=entity_id)
            if action == 'approve':
                doctor.status = 'approved'
                doctor.approved_date = timezone.now()
                doctor.save()
                messages.success(request, f'Dr. {doctor.user.get_full_name()} approved!')
            elif action == 'reject':
                doctor.status = 'rejected'
                doctor.save()
                messages.info(request, f'Dr. {doctor.user.get_full_name()} rejected.')

        return redirect('moderator_dashboard')

    context = {
        'pending_institutes': pending_institutes,
        'approved_institutes': approved_institutes,
        'pending_doctors': pending_doctors,
        'approved_doctors': approved_doctors,
        'removal_requests': removal_requests,
        'total_users': total_users,
        'total_institutes': total_institutes,
        'total_doctors': total_doctors,
    }
    return render(request, 'core/moderator_dashboard.html', context)

@login_required
def removal_request_view(request):
    '''Submit removal request'''
    if request.method == 'POST':
        form = RemovalRequestForm(request.POST)
        if form.is_valid():
            removal_request = form.save(commit=False)
            removal_request.requested_by = request.user
            removal_request.save()
            messages.success(request, 'Removal request submitted to moderator.')
            return redirect('institute_dashboard' if request.user.userprofile.role == 'institute' else 'moderator_dashboard')
    else:
        form = RemovalRequestForm()

    return render(request, 'core/removal_request.html', {'form': form})

# ============= CHATBOT =============

@login_required
def chatbot_ui(request):
    '''Chatbot UI'''
    return render(request, 'core/chatbot_ui.html')

@csrf_exempt
@login_required
def chatbot_api(request):
    '''Chatbot API'''
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message')

        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)

        bot_response = query_gemini_api(user_message, request.user)

        pending_recs = InstantRecommendation.objects.filter(
            user=request.user,
            completed=False
        ).order_by('-created_at')[:2]

        recommendations_data = [{
            'id': rec.id,
            'title': rec.title,
            'points': rec.bonus_points,
            'type': rec.activity_type
        } for rec in pending_recs]

        return JsonResponse({
            'response': bot_response,
            'recommendations': recommendations_data
        })
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def complete_recommendation(request, rec_id):
    '''Complete instant recommendation'''
    recommendation = get_object_or_404(InstantRecommendation, id=rec_id, user=request.user)
    if not recommendation.completed:
        recommendation.completed = True
        recommendation.save()

        profile = UserProfile.objects.get(user=request.user)
        profile.points += recommendation.bonus_points
        profile.update_level()

        messages.success(request, f'Great job! +{recommendation.bonus_points} bonus points earned!')
    return redirect('chatbot_ui')

# ============= HELPER FUNCTIONS =============

def get_assessment_questions():
    '''Get assessment questions'''
    categories = {
        'Depression': [
            'Little interest or pleasure in doing things',
            'Feeling down, depressed, or hopeless',
            'Trouble falling or staying asleep',
            'Feeling tired or having little energy',
            'Poor appetite or overeating',
        ],
        'Anxiety': [
            'Feeling nervous or on edge',
            'Not being able to stop worrying',
            'Worrying too much about different things',
            'Trouble relaxing',
            'Being so restless',
        ],
        'Stress': [
            'Difficulty unwinding',
            'Nervous energy',
            'Easily upset',
            'Irritable',
            'Impatient',
        ],
    }

    all_questions = []
    for category, questions in categories.items():
        for q in questions:
            all_questions.append({'category': category, 'question': q})

    return all_questions

def get_recommendations(severity):
    '''Get health recommendations based on severity'''
    recommendations = {
        'Minimal': 'Your mental health appears to be good. Continue with daily check-ins and self-care practices.',
        'Mild': 'Consider talking to a counselor. Practice relaxation techniques and maintain a healthy routine.',
        'Moderate': 'We recommend consulting with a mental health professional. Consider therapy or counseling.',
        'Severe': 'Please seek immediate professional help. Contact a psychiatrist or crisis hotline.',
    }
    return recommendations.get(severity, '')

# ============= AUTHENTICATION VIEWS =============

class CustomPasswordResetView(PasswordResetView):
    '''Custom password reset view'''
    template_name = 'core/password_reset.html'
    email_template_name = 'core/password_reset_email.html'
    subject_template_name = 'core/password_reset_subject.txt'
    success_url = '/password-reset/done/'

class CustomPasswordResetDoneView(PasswordResetDoneView):
    '''Password reset done view'''
    template_name = 'core/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    '''Password reset confirm view'''
    template_name = 'core/password_reset_confirm.html'
    success_url = '/password-reset/complete/'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    '''Password reset complete view'''
    template_name = 'core/password_reset_complete.html'

# ============= UTILITY VIEWS =============

def terms_policy_view(request):
    '''Show terms and privacy policy'''
    if request.method == 'POST':
        agree_privacy = request.POST.get('agree_privacy')
        agree_terms = request.POST.get('agree_terms')
        agree_accuracy = request.POST.get('agree_accuracy')

        if agree_privacy and agree_terms and agree_accuracy:
            request.session['terms_agreed'] = True
            messages.success(request, '✅ Thank you for agreeing to our terms!')
            return redirect('register')
        else:
            messages.error(request, '❌ Please agree to all terms to continue')

    return render(request, 'core/terms_policy.html')

@login_required
def pending_approval_view(request):
    '''Show pending approval page'''
    return render(request, 'core/pending_approval.html')

def api_test(request):
    '''Test backend connectivity'''
    try:
        total_users = User.objects.count()
        total_students = UserProfile.objects.filter(role='user').count()
        total_doctors = Doctor.objects.count()
        total_institutes = Institute.objects.count()

        return JsonResponse({
            'status': 'Backend Connected ✅',
            'database': {
                'total_users': total_users,
                'total_students': total_students,
                'total_doctors': total_doctors,
                'total_institutes': total_institutes,
            },
            'timestamp': str(timezone.now())
        })
    except Exception as e:
        return JsonResponse({'status': f'Error: {str(e)}'}, status=500)
