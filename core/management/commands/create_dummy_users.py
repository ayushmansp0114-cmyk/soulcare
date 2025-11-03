from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, Doctor, CheckIn, Assessment, Badge, GitaVerse
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Create dummy users and data'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating dummy data...')
        
        # Indian names
        first_names = ['Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Arnav', 'Ayaan', 'Krishna', 'Ishaan',
                       'Ananya', 'Aadhya', 'Saanvi', 'Diya', 'Pari', 'Anvi', 'Kavya', 'Navya', 'Priya', 'Riya',
                       'Rohan', 'Kabir', 'Reyansh', 'Shivansh', 'Atharv', 'Advait', 'Rudra', 'Kiaan', 'Dhruv', 'Aarush']
        last_names = ['Sharma', 'Verma', 'Kumar', 'Singh', 'Gupta', 'Patel', 'Reddy', 'Nair', 'Iyer', 'Joshi']
        
        # Create 50 users
        for i in range(1, 51):
            username = f'user{i}'
            if User.objects.filter(username=username).exists():
                continue
            
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f'{username}@soulcare.demo'
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password='demo123',
                first_name=first_name,
                last_name=last_name
            )
            
            # Create profile
            profile = UserProfile.objects.create(
                user=user,
                role='user',
                age=random.randint(18, 45),
                points=random.randint(50, 500),
            )
            profile.update_level()
            
            # Create check-ins (7-60 days)
            num_days = random.randint(7, 60)
            today = datetime.now().date()
            
            for day in range(num_days):
                checkin_date = today - timedelta(days=day)
                CheckIn.objects.get_or_create(
                    user=user,
                    date=checkin_date,
                    defaults={
                        'mood': random.randint(1, 5),
                        'energy': random.randint(1, 3),
                        'sleep_quality': random.randint(1, 4),
                    }
                )
            
            # Create assessment
            Assessment.objects.create(
                user=user,
                total_score=random.randint(10, 80),
                depression_score=random.randint(3, 27),
                anxiety_score=random.randint(3, 27),
                stress_score=random.randint(3, 27),
                severity=random.choice(['Minimal', 'Mild', 'Moderate']),
                recommendations='Practice self-care and mindfulness.'
            )
        
        # Create 5 doctors
        specializations = ['Psychiatrist', 'Clinical Psychologist', 'Counselor', 'Therapist', 'Mental Health Specialist']
        hospitals = ['AIIMS Delhi', 'Apollo Hospital', 'Fortis Hospital', 'Max Hospital', 'Manipal Hospital']
        
        for i in range(1, 6):
            username = f'doctor{i}'
            if User.objects.filter(username=username).exists():
                continue
            
            user = User.objects.create_user(
                username=username,
                email=f'{username}@soulcare.demo',
                password='demo123',
                first_name=f'Dr. {random.choice(first_names)}',
                last_name=random.choice(last_names)
            )
            
            UserProfile.objects.create(
                user=user,
                role='doctor',
                age=random.randint(30, 55),
            )
        
        # Create 2 moderators
        for i in range(1, 3):
            username = f'moderator{i}'
            if User.objects.filter(username=username).exists():
                continue
            
            user = User.objects.create_user(
                username=username,
                email=f'{username}@soulcare.demo',
                password='demo123',
                first_name='Moderator',
                last_name=str(i)
            )
            
            UserProfile.objects.create(
                user=user,
                role='moderator',
            )
        
        # Create Gita verses
        verses = [
            {
                'verse_number': 'BG 2.47',
                'sanskrit': 'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन',
                'english': 'You have a right to perform your duty, but not to the fruits of action.',
                'meaning': 'Focus on your actions, not on the results. Do your best and let go of attachment to outcomes.'
            },
            {
                'verse_number': 'BG 6.5',
                'sanskrit': 'उद्धरेदात्मनात्मानं नात्मानमवसादयेत्',
                'english': 'One must elevate oneself by one own mind, not degrade oneself.',
                'meaning': 'Be your own friend, not your enemy. Lift yourself up through positive thoughts and actions.'
            },
            {
                'verse_number': 'BG 2.14',
                'sanskrit': 'मात्रास्पर्शास्तु कौन्तेय शीतोष्णसुखदुःखदाः',
                'english': 'The contact of senses with objects brings pleasure and pain, which come and go.',
                'meaning': 'Understand that happiness and suffering are temporary. Learn to remain balanced.'
            },
        ]
        
        for verse_data in verses:
            GitaVerse.objects.get_or_create(
                verse_number=verse_data['verse_number'],
                defaults=verse_data
            )
        
        self.stdout.write(self.style.SUCCESS('✅ Dummy data created successfully!'))
        self.stdout.write(self.style.SUCCESS('50 users, 5 doctors, 2 moderators created'))
        self.stdout.write(self.style.SUCCESS('Login credentials: username (user1-50, doctor1-5, moderator1-2), password: demo123'))
