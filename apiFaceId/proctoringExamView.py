from datetime import datetime

import requests
import face_recognition
import numpy as np
import jwt
import cv2
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView

from .dynamic_db import DynamicDbConnection
from jwt.exceptions import InvalidTokenError
import base64
from io import BytesIO
from PIL import Image

class ProctoringView(APIView):
    def post(self, request):
        if 'images' not in request.data or 'createdId' not in request.data or 'token' not in request.data:
            return JsonResponse({'error': 'No se han proporcionado imágenes o faltan parametros.'}, status=400)

        image_data_list = request.data['images']
        token = request.data['token']
        created_id = request.data['createdId']
        db_connection = None

        try:
            decoded_token = jwt.decode(token, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
            document_id = decoded_token.get("userId")
            connection_db = decoded_token.get("connectionDb")
            if not document_id:
                return JsonResponse({'error': 'El token no contiene un documento de identidad válido.'}, status=401)
        except InvalidTokenError:
            return JsonResponse({'error': 'Token inválido o expirado.'}, status=401)

        try:
            # Inicializar conexión dinámica
            db_connection = DynamicDbConnection(connection_db)
            db_connection.initialize_pool()

            # 1. Obtener imagen de referencia desde Cloudinary
            cloudinary_url = f"{settings.CLOUDINARY['base_url']}/{settings.CLOUDINARY['folder']}/user_{document_id}"
            response = requests.get(cloudinary_url)

            if response.status_code != 200:
                return JsonResponse(
                    {'error': 'No se encontró la imagen de referencia en Cloudinary.'},
                    status=404
                )


            # Procesar imagen de referencia
            reference_img = face_recognition.load_image_file(BytesIO(response.content))
            reference_face_encodings = face_recognition.face_encodings(reference_img)

            if not reference_face_encodings:
                return JsonResponse(
                    {'error': 'No se detectó ninguna cara en la imagen de referencia.'},
                    status=500
                )

            known_face_encoding = reference_face_encodings[0]


            # 2. Procesar imágenes recibidas
            for image_data in image_data_list:
                try:
                    # Decodificar imagen base64
                    header, encoded = image_data.split(';base64,')
                    img_bytes = base64.b64decode(encoded)
                    image = np.array(Image.open(BytesIO(img_bytes)))

                    # Convertir RGBA a RGB si es necesario
                    if image.shape[2] == 4:
                        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

                    # Evaluar calidad de imagen
                    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                    laplacian_var = cv2.Laplacian(gray_image, cv2.CV_64F).var()

                    incidencias = []
                    if laplacian_var < 100:
                        incidencias.append("low_image_quality")

                    # Detección de rostros
                    face_encodings = face_recognition.face_encodings(image)

                    if len(face_encodings) == 0:
                        incidencias.append("no_face_detected")
                    elif len(face_encodings) > 1:
                        incidencias.append("multiple_faces_detected")
                    else:
                        # Comparación facial
                        match = face_recognition.compare_faces(
                            [known_face_encoding],
                            face_encodings[0],
                            tolerance=0.6
                        )
                        if not match[0]:
                            incidencias.append("identity_mismatch")

                    print(incidencias)
                    # Registrar incidencias en la base de datos dinámica
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    for incidencia in incidencias:
                        db_connection.execute_query(
                            "INSERT INTO reportes (created_id, imagenes_base64, tipo_incidencia, fecha_captura) VALUES (%s, %s, %s, %s)",
                            (created_id, image_data, incidencia, timestamp)
                        )

                except Exception as e:
                    print(f"Error procesando imagen: {str(e)}")
                    continue

                return JsonResponse({'success': True, 'message': 'Procesamiento completado'}, status=200)

        except Exception as e:
            return JsonResponse({'error': f'Error en el procesamiento: {str(e)}'}, status=500)
        finally:
            if db_connection:
                db_connection.close()
