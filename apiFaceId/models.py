from django.db import models

class Face(models.Model):
    face_id = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='faces/')  # Asegúrate de que MEDIA_URL esté configurado correctamente
    document_id = models.CharField(max_length=255, unique=True)  # Campo para almacenar el documento de identidad
    encoding_path = models.CharField(max_length=255, null=True, blank=True)  # Permitir valores nulos

    def __str__(self):
        return self.document_id
