from django.contrib import admin
from .models import StudySession, DailyProgress

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'start_time', 'duration_minutes']
    list_filter = ['user', 'topic']
    search_fields = ['user__username', 'topic__name']

@admin.register(DailyProgress)
class DailyProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'hours_studied', 'questions_solved']
    list_filter = ['user']
    search_fields = ['user__username']
