"""
URL configuration for apiFaceId project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from .faceCreateView import FaceCreateView
from .faceValidationView import FaceValidationView
from .proctoringExamView import ProctoringView
from .views import FaceRecognitionView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('detect-face/', FaceRecognitionView.as_view(), name='detect-face'),
    path('create-face/', FaceCreateView.as_view(), name='create-face'),
    path('validation-face/', FaceValidationView.as_view(), name='validation-face'),
    path('proctoring-exam/', ProctoringView.as_view(), name= 'proctoring-exam')
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)