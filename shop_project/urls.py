from django.contrib import admin
from django.urls import path, include

# ❗️Ces deux lignes sont nécessaires pour servir les fichiers médias
from django.conf import settings
from django.conf.urls.static import static

from shop import views as shop_views

urlpatterns = [
    path('', include('shop.urls')),  # Toutes les URLs de l'application
    path('accounts/', include('allauth.urls')), # Allauth (Google OAuth)
    path('django-admin/', admin.site.urls),
    path('h/', shop_views.home, name='home'), # Nom global pour Allauth
]

# Ajoute ceci pour servir les fichiers médias quand DEBUG = True
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
