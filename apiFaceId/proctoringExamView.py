import face_recognition
import numpy as np
import os
import jwt
import cv2
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from .models import Face
from jwt.exceptions import InvalidTokenError
import base64
from io import BytesIO
from PIL import Image

class ProctoringView(APIView):
    def post(self, request):
        if 'images' not in request.data or 'token' not in request.data:
            return JsonResponse({'error': 'No se han proporcionado imágenes o un token de autenticación.'}, status=400)

        image_data_list = request.data['images']
        token = request.data['token']

        try:
            decoded_token = jwt.decode(token, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
            document_id = decoded_token.get("userId")
            if not document_id:
                return JsonResponse({'error': 'El token no contiene un documento de identidad válido.'}, status=401)
        except InvalidTokenError:
            return JsonResponse({'error': 'Token inválido o expirado.'}, status=401)

        existing_face = Face.objects.filter(document_id=document_id).first()
        if not existing_face:
            return JsonResponse({'error': 'No se ha encontrado un registro con ese documento de identidad.'}, status=404)

        known_face_encoding_path = existing_face.encoding_path
        if not os.path.exists(known_face_encoding_path):
            return JsonResponse({'error': 'No se ha encontrado el archivo de codificación para el documento de identidad.'}, status=500)
        known_face_encoding = np.load(known_face_encoding_path, allow_pickle=True)

        incidencias = []
        multiple_faces_count = 0
        no_face_detected_count = 0

        for image_data in image_data_list:
            try:
                header, encoded = image_data.split(';base64,')
                img_bytes = base64.b64decode(encoded)
                image = np.array(Image.open(BytesIO(img_bytes)))

                if image.shape[2] == 4:
                    image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

                # Verificar calidad de la imagen (iluminación y claridad)
                gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                brightness = np.mean(gray_image)
                if brightness < 50:
                    incidencias.append("Baja iluminación en la imagen")

                face_encodings = face_recognition.face_encodings(image)

                # Verificar si no hay rostros detectados
                if len(face_encodings) == 0:
                    no_face_detected_count += 1
                    incidencias.append("No se detectó ninguna cara en la imagen")
                elif len(face_encodings) > 1:
                    multiple_faces_count += 1
                    incidencias.append("Múltiples rostros detectados")
                else:
                    face_encoding = face_encodings[0]
                    match = face_recognition.compare_faces([known_face_encoding], face_encoding, tolerance=0.6)
                    if not match[0]:
                        incidencias.append("Identidad no coincide")

            except Exception as e:
                print(f"Error procesando la imagen: {str(e)}")
                incidencias.append("Error procesando la imagen")

        # Alertar si hay muchas imágenes consecutivas sin un rostro
        if no_face_detected_count > 3:
            incidencias.append("Se detectaron múltiples imágenes consecutivas sin rostro")

        # Alertar si se detectaron muchas imágenes con múltiples rostros
        if multiple_faces_count > 3:
            incidencias.append("Se detectaron múltiples imágenes con más de un rostro")

        return JsonResponse({'success': True, 'incidencias': incidencias}, status=200)