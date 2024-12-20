import face_recognition
import numpy as np
import os
import jwt
import cv2
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from .models import Face, Reportes
from jwt.exceptions import InvalidTokenError
import base64
from io import BytesIO
from PIL import Image
from django.utils import timezone

class ProctoringView(APIView):
    def post(self, request):
        if 'images' not in request.data or 'createdId' not in request.data or 'token' not in request.data:
            return JsonResponse({'error': 'No se han proporcionado imágenes o faltan parametros.'}, status=400)

        image_data_list = request.data['images']
        token = request.data['token']
        created_id = request.data['createdId']

        try:
            decoded_token = jwt.decode(token, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
            document_id = decoded_token.get("userId")
            if not document_id:
                return JsonResponse({'error': 'El token no contiene un documento de identidad válido.'}, status=401)
        except InvalidTokenError:
            return JsonResponse({'error': 'Token inválido o expirado.'}, status=401)

        existing_face = Face.objects.filter(document_id=document_id).first()
        if not existing_face:
            return JsonResponse({'error': 'No se ha encontrado un registro con ese documento de identidad.'},
                                status=404)

        known_face_encoding_path = existing_face.encoding_path
        if not os.path.exists(known_face_encoding_path):
            return JsonResponse(
                {'error': 'No se ha encontrado el archivo de codificación para el documento de identidad.'}, status=500)
        known_face_encoding = np.load(known_face_encoding_path, allow_pickle=True)
        #
        # # Diccionario para registrar si ocurrió cada incidencia
        # incidencias_detectadas = {
        #     "no_face_detected": False,
        #     "multiple_faces_detected": False,
        #     "identity_mismatch": False,
        #     "low_image_quality": False,
        # }
        #
        # # Procesar las imágenes
        # no_face_detected_count = 0
        # max_consecutive_no_face = 3  # Umbral de imágenes consecutivas sin rostro

        for image_data in image_data_list:
            try:
                header, encoded = image_data.split(';base64,')
                img_bytes = base64.b64decode(encoded)
                image = np.array(Image.open(BytesIO(img_bytes)))

                if image.shape[2] == 4:
                    image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

                # Evaluar la nitidez de la imagen
                gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                laplacian_var = cv2.Laplacian(gray_image, cv2.CV_64F).var()

                # Inicializar incidencias
                incidencias = []

                if laplacian_var < 100:  # Umbral para nitidez
                    incidencias.append("low_image_quality")

                face_encodings = face_recognition.face_encodings(image)

                # Verificar si no hay rostros detectados
                # TODO: Puede ser que no face detected no funcione porque tenemos este faceEncoding
                if len(face_encodings) == 0:
                    incidencias.append("no_face_detected")
                elif len(face_encodings) > 1:  # Múltiples rostros detectados
                    incidencias.append("multiple_faces_detected")
                else:
                    # Comparar la cara detectada con la conocida
                    face_encoding = face_encodings[0]
                    match = face_recognition.compare_faces([known_face_encoding], face_encoding, tolerance=0.6)
                    if not match[0]:
                        incidencias.append("identity_mismatch")

                # Guardar incidencias una por una
                for incidencia in incidencias:
                    print(incidencia)
                    Reportes.objects.create(
                        created_id=created_id,
                        imagenes_base64=image_data,  # Guardar la imagen con incidencia
                        tipo_incidencia=incidencia,  # Guardar una incidencia individualmente
                        fecha_captura=timezone.now()
                    )


            except Exception as e:
                print(f"Error procesando la imagen: {str(e)}")

            return JsonResponse({'success': True, 'message': 'Reporte guardado debido a incidencias'}, status=200)

        # Respuesta genérica para el cliente
        return JsonResponse({'success': True, 'message': 'Proceso capturado'}, status=200)
