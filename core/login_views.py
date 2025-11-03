from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from core.models import UserProfile, Doctor, Institute, LoginActivity, AdminApprovalRequest
from django.core.mail import send_mail

def is_bot_access(request):
    '''Detect bot access patterns'''
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # Bot patterns
    bot_patterns = ['bot', 'crawler', 'spider', 'scraper', 'selenium', 'automation', 'headless']
    
    for pattern in bot_patterns:
        if pattern in user_agent:
            return True
    
    # Check for automation tools
    if 'x-requested-with' in request.META.get('HTTP_ACCEPT', '').lower():
        return True
    
    return False

def login_view(request):
    '''Enhanced login with bot detection and approval system'''
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Get system info
        ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Bot Detection
        is_bot = is_bot_access(request)
        
        # Try authentication
        user = authenticate(request, username=username, password=password)
        
        if is_bot:
            # Bot detected - BLOCK
            LoginActivity.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                role='bot',
                status='blocked_bot',
                is_bot=True
            )
            return render(request, 'core/blocked_bot.html', {
                'admin_contact': 'https://t.me/coder_chandan'
            })
        
        if user is not None:
            # Get user profile
            try:
                profile = UserProfile.objects.get(user=user)
                role = profile.role
            except:
                role = 'unknown'
            
            # Check approval status for doctors and institute managers
            needs_approval = False
            approval_reason = ''
            
            if role == 'doctor':
                try:
                    doctor = Doctor.objects.get(user=user)
                    if doctor.status != 'approved':
                        needs_approval = True
                        approval_reason = f'Doctor account pending verification'
                except:
                    pass
            
            elif role == 'institute':
                try:
                    institute = Institute.objects.get(manager=user)
                    if institute.status != 'approved':
                        needs_approval = True
                        approval_reason = f'Institute {institute.name} pending verification'
                except:
                    pass
            
            if needs_approval:
                # Create login activity for approval
                login_act = LoginActivity.objects.create(
                    user=user,
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    role=role,
                    status='pending',
                    is_bot=False
                )
                
                # Create approval request
                AdminApprovalRequest.objects.get_or_create(
                    login_activity=login_act,
                    defaults={
                        'reason': approval_reason,
                        'status': 'pending'
                    }
                )
                
                # Notify admin
                send_mail(
                    f'🔔 New {role.title()} Login Approval Required',
                    f'{user.get_full_name()} ({username}) from {ip_address} is waiting for approval.',
                    'noreplaysoulcare@gmail.com',
                    ['admin@soulcare.com'],
                    fail_silently=True
                )
                
                return render(request, 'core/pending_approval.html', {
                    'user': user,
                    'role': role.title(),
                    'reason': approval_reason
                })
            
            # Login successful - record activity
            LoginActivity.objects.create(
                user=user,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                role=role,
                status='success',
                is_bot=False
            )
            
            login(request, user)
            
            # Redirect based on role
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
            # Failed login
            LoginActivity.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                role='unknown',
                status='failed',
                is_bot=False
            )
            messages.error(request, '❌ Invalid username or password!')
    
    return render(request, 'core/login.html')
