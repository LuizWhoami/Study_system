from django.contrib import admin
from .models import StudyConfig, PlannedSession

@admin.register(StudyConfig)
class StudyConfigAdmin(admin.ModelAdmin):
    list_display = ['user', 'objective', 'priority', 'is_active', 'updated_at']
    list_filter = ['objective', 'priority', 'is_active']
    search_fields = ['user__username']

@admin.register(PlannedSession)
class PlannedSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'subject_name', 'session_type', 'duration_minutes']
    list_filter = ['user', 'session_type', 'date']
    search_fields = ['subject_name']
