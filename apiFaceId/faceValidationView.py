import face_recognition
import numpy as np
import os
from django.http import JsonResponse
from rest_framework.views import APIView
from .models import Face

class FaceValidationView(APIView):

    def post(self, request):
        # Verificar si se han proporcionado la imagen y el documento de identidad
        if 'image' not in request.FILES or 'document_id' not in request.data:
            return JsonResponse({'error': 'No se han proporcionado una imagen o un documento de identidad.'}, status=400)

        image_file = request.FILES['image']
        document_id = request.data['document_id']

        try:
            # Cargar la imagen y codificar la cara
            image = face_recognition.load_image_file(image_file)
            face_encodings = face_recognition.face_encodings(image)

            if len(face_encodings) == 0:
                return JsonResponse({'error': 'No se ha detectado ninguna cara en la imagen.'}, status=400)

            face_encoding = face_encodings[0]  # Usar la primera cara detectada

            # Verificar si el document_id está registrado
            existing_face = Face.objects.filter(document_id=document_id).first()
            if not existing_face:
                return JsonResponse({'error': 'No se ha encontrado un registro con ese documento de identidad.'}, status=404)

            # Obtener la ruta del archivo de codificación de la cara
            known_face_encoding_path = existing_face.encoding_path  # Usa el campo encoding_path

            # Verificar si el archivo de codificación de la cara existe
            if not os.path.exists(known_face_encoding_path):
                return JsonResponse({'error': 'No se ha encontrado el archivo de codificación para el documento de identidad.'}, status=500)

            # Cargar la codificación de la cara registrada y comparar
            known_face_encoding = np.load(known_face_encoding_path, allow_pickle=True)
            results = face_recognition.compare_faces([known_face_encoding], face_encoding, tolerance=0.5)

            if results[0]:  # Si las caras coinciden
                return JsonResponse({'success': True, 'message': 'Login successful'}, status=200)
            else:
                return JsonResponse({'success': False, 'message': 'La cara no coincide con la registrada.'}, status=401)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
