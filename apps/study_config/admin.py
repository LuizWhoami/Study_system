from django.contrib import admin
from .models import StudyConfig, PlannedSession

@admin.register(StudyConfig)
class StudyConfigAdmin(admin.ModelAdmin):
    list_display = ['user', 'objective', 'priority', 'is_active', 'updated_at']
    list_filter = ['objective', 'priority', 'is_active']
    search_fields = ['user__username']

@admin.register(PlannedSession)
class PlannedSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'contest', 'topic', 'session_type', 'status']
    list_filter = ['user', 'session_type', 'status', 'date']
    search_fields = ['user__username', 'contest__name', 'topic__name']
