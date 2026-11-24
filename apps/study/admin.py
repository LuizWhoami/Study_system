from django.contrib import admin
from .models import StudySession, DailyProgress, Goal, StudyContent


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'status', 'start_time', 'duration_minutes']
    list_filter = ['status', 'user']
    search_fields = ['user__username', 'topic__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DailyProgress)
class DailyProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'hours_studied', 'questions_solved']
    list_filter = ['user']
    search_fields = ['user__username']


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'period', 'target_hours', 'active']
    list_filter = ['user', 'period', 'active']


@admin.register(StudyContent)
class StudyContentAdmin(admin.ModelAdmin):
    list_display = ['topic', 'user', 'difficulty', 'studied_at', 'next_review', 'review_count']
    list_filter = ['user', 'difficulty']
    search_fields = ['topic__name']
