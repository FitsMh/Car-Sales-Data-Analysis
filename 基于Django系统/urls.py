from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from app import views

urlpatterns = [
    path('', RedirectView.as_view(url='/app/login/')),
    path('admin/', admin.site.urls),
    path('app/', include('app.urls')),
    path('largescreen/', views.largescreen, name='largescreen'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)