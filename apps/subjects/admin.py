from django.contrib import admin
from .models import Subject, Topic
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'contest', 'order']
    list_filter = ['contest']
    search_fields = ['name']
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'parent', 'status', 'priority']
    list_filter = ['status', 'subject']
    search_fields = ['name']
