from django.urls import path
from . import views

app_name = 'calendar'
urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('set-activity/', views.set_activity, name='set_activity'),
]
