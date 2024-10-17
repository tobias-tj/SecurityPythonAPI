from django.contrib import admin
from .models import Face

@admin.register(Face)
class FaceAdmin(admin.ModelAdmin):
    list_display = ('face_id', 'document_id', 'image')
