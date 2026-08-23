from django.urls import path
from . import views

app_name = 'study_config'
urlpatterns = [
    path('', views.config_view, name='config'),
    path('preview/', views.preview_config, name='preview'),
    path('save/', views.save_config, name='save'),
    path('estatisticas/', views.stats_view, name='stats'),
]
