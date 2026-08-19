from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    photo = models.ImageField(upload_to='users/%Y/%m/', blank=True, null=True)
    main_goal = models.CharField(max_length=255, blank=True)
    daily_goal_hours = models.DecimalField(max_digits=5, decimal_places=2, default=3.0)
    preferred_study_time = models.TimeField(blank=True, null=True)
    available_days = models.JSONField(default=list)
    available_hours_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=4.0)

    def __str__(self):
        return self.username
