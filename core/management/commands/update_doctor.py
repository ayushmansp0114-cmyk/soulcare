from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import *
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Update doctor name to Dr. Ayushman Panda'
    
    def handle(self, *args, **kwargs):
        # Update existing doctor
        try:
            doctor_user = User.objects.get(username='doctor1')
            doctor_user.first_name = 'Dr. Ayushman'
            doctor_user.last_name = 'Panda'
            doctor_user.save()
            
            doctor = Doctor.objects.get(user=doctor_user)
            doctor.specialization = 'Psychiatrist'
            doctor.qualification = 'MBBS, MD (Psychiatry), Fellowship in Child Psychology'
            doctor.experience = 12
            doctor.save()
            
            self.stdout.write(self.style.SUCCESS('✅ Doctor updated to Dr. Ayushman Panda'))
        except:
            self.stdout.write(self.style.ERROR('Doctor not found'))
