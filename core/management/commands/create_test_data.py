from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import *
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Create dummy test data'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating test data...')
        
        # Create Institute 1
        if not Institute.objects.filter(registration_number='INST001').exists():
            manager_user = User.objects.create_user(
                username='institute1',
                email='institute1@soulcare.com',
                password='demo123',
                first_name='Manager',
                last_name='One'
            )
            UserProfile.objects.create(user=manager_user, role='institute')
            
            institute = Institute.objects.create(
                name='Peace Mental Health Institute',
                manager=manager_user,
                address='123 Wellness Street, Mumbai',
                registration_number='INST001',
                contact_email='contact@peaceinstitute.com',
                contact_phone='+919876543210',
                status='approved',
                approved_date=datetime.now()
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Created Institute: {institute.name}'))
        else:
            institute = Institute.objects.get(registration_number='INST001')
            self.stdout.write('Institute already exists')
        
        # Create 10 test users
        for i in range(1, 11):
            username = f'user{i}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@soulcare.com',
                    password='demo123',
                    first_name=f'Student{i}',
                    last_name='Test'
                )
                
                profile = UserProfile.objects.create(
                    user=user,
                    role='user',
                    age=random.randint(18, 25),
                    weight=random.randint(50, 80),
                    height=random.randint(150, 180),
                    phone=f'+919{random.randint(100000000, 999999999)}',
                    institute=institute,
                    is_approved=True,
                    points=random.randint(50, 300)
                )
                profile.update_level()
                
                # Create leaderboard entry
                InstituteLeaderboard.objects.create(
                    institute=institute,
                    user=user,
                    total_points=profile.points
                )
                
                # Add some check-ins
                for day in range(random.randint(3, 10)):
                    CheckIn.objects.create(
                        user=user,
                        date=datetime.now().date() - timedelta(days=day),
                        mood=random.randint(1, 5),
                        energy=random.randint(1, 3),
                        sleep_quality=random.randint(1, 4)
                    )
                
                self.stdout.write(self.style.SUCCESS(f'✅ Created User: {username}'))
        
        # Create Doctor
        if not User.objects.filter(username='doctor1').exists():
            doctor_user = User.objects.create_user(
                username='doctor1',
                email='doctor1@soulcare.com',
                password='demo123',
                first_name='Dr. Rajesh',
                last_name='Kumar'
            )
            UserProfile.objects.create(user=doctor_user, role='doctor')
            
            Doctor.objects.create(
                user=doctor_user,
                institute=institute,
                license_number='MED123456',
                specialization='Psychiatrist',
                experience=10,
                qualification='MBBS, MD (Psychiatry)',
                status='approved',
                approved_date=datetime.now()
            )
            self.stdout.write(self.style.SUCCESS('✅ Created Doctor: doctor1'))
        
        # Create Gita verses
        verses = [
            {
                'verse_number': 'BG 2.47',
                'sanskrit': 'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन',
                'english': 'You have a right to perform your duty, but not to the fruits of action.',
                'meaning': 'Focus on your actions, not results. Do your best and let go.'
            },
            {
                'verse_number': 'BG 6.5',
                'sanskrit': 'उद्धरेदात्मनात्मानं नात्मानमवसादयेत्',
                'english': 'One must elevate oneself by ones own mind, not degrade oneself.',
                'meaning': 'Be your own friend. Lift yourself through positive thoughts.'
            },
        ]
        
        for verse_data in verses:
            GitaVerse.objects.get_or_create(
                verse_number=verse_data['verse_number'],
                defaults=verse_data
            )
        
        self.stdout.write(self.style.SUCCESS('✅ Created Gita verses'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Test data created successfully!'))
        self.stdout.write(self.style.SUCCESS('\n📝 Login Credentials:'))
        self.stdout.write('  Admin: admin / 1234')
        self.stdout.write('  Institute: institute1 / demo123')
        self.stdout.write('  Users: user1-10 / demo123')
        self.stdout.write('  Doctor: doctor1 / demo123')
