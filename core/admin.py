from django.contrib import admin
from .models import UserProfile, Doctor, CheckIn, Assessment, Badge, Consultation, ChatMessage, GitaVerse

admin.site.register(UserProfile)
admin.site.register(Doctor)
admin.site.register(CheckIn)
admin.site.register(Assessment)
admin.site.register(Badge)
admin.site.register(Consultation)
admin.site.register(ChatMessage)
admin.site.register(GitaVerse)
