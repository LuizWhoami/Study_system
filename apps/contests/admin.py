from django.contrib import admin
from .models import Contest
@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'exam_date']
    list_filter = ['status', 'user']
    search_fields = ['name', 'organization']
