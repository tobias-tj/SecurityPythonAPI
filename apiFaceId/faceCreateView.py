import face_recognition
import numpy as np
import uuid
import os
import jwt
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from .models import Face
from jwt.exceptions import InvalidTokenError


class FaceCreateView(APIView):

    def post(self, request):
        # Verificar si se han proporcionado la imagen y el documento de identidad
        if 'image' not in request.FILES or 'token' not in request.data:
            return JsonResponse({'error': 'No se han proporcionado una imagen o un documento de identidad.'}, status=400)

        image_file = request.FILES['image']
        token = request.data['token']

        # Decodificar el token para obtener el document_id
        try:
            decoded_token = jwt.decode(token, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
            document_id = decoded_token.get("userId")
            print(document_id)
            if not document_id:
                return JsonResponse({'error': 'El token no contiene el documento de identidad.'}, status=401)
        except InvalidTokenError:
            return JsonResponse({'error': 'Token inválido o expirado.'}, status=401)

        try:
            # Cargar la imagen y codificar la cara
            image = face_recognition.load_image_file(image_file)
            face_encodings = face_recognition.face_encodings(image)

            if len(face_encodings) == 0:
                return JsonResponse({'error': 'No se ha detectado ninguna cara en la imagen.'}, status=400)

            face_encoding = face_encodings[0]  # Usar la primera cara detectada

            # Verificar si el document_id ya está registrado
            if Face.objects.filter(document_id=document_id).exists():
                return JsonResponse({'error': 'El documento de identidad ya está registrado con otra cara.'}, status=400)

            # Asegúrate de que la carpeta exista
            os.makedirs('face_encodings', exist_ok=True)

            # Crear un nuevo faceId y guardar la codificación de la cara
            face_id = str(uuid.uuid4())
            encoding_file_path = os.path.join('face_encodings', f"{face_id}.npy")
            np.save(encoding_file_path, face_encoding.astype(np.float32))  # Guardar la codificación

            # Crear una nueva entrada en la base de datos
            new_face = Face(face_id=face_id, image=image_file, document_id=document_id, encoding_path=encoding_file_path)
            new_face.save()

            return JsonResponse({'faceId': face_id, 'document_id': document_id}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
