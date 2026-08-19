from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    path('accounts/', include('apps.accounts.urls')),
    path('concursos/', include('apps.contests.urls')),
    path('materias/', include('apps.subjects.urls')),
    path('notas/', include('apps.notes.urls')),
    path('estudo/', include('apps.study.urls')),
    path('flashcards/', include('apps.flashcards.urls')),  # <-- adicione esta linha
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
