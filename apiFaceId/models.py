from django.db import models

class Face(models.Model):
    face_id = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='faces/')  # Asegúrate de que MEDIA_URL esté configurado correctamente
    document_id = models.CharField(max_length=255, unique=True)  # Campo para almacenar el documento de identidad
    encoding_path = models.CharField(max_length=255, null=True, blank=True)  # Permitir valores nulos

    def __str__(self):
        return self.document_id


class Reportes(models.Model):
    created_id = models.IntegerField()  # Relacionado con Examenes_Usuarios.id
    imagenes_base64 = models.TextField()  # Para imágenes en formato base64
    tipo_incidencia = models.TextField()  # Tipo de incidencia
    fecha_captura = models.DateTimeField(auto_now_add=True)  # Fecha de captura

    class Meta:
        app_label = 'reportes'  # Asegura que el router lo detecte
        db_table = 'reportes'  # Nombre exacto de la tabla en Neon