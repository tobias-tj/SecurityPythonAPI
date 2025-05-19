import cloudinary
import cv2
import face_recognition
import jwt
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from jwt.exceptions import InvalidTokenError
from rest_framework import status
from apiFaceId.dynamic_db import DynamicDbConnection




class FaceCreateView(APIView):

    def post(self, request):
        """
               Valida si una imagen cumple con los requisitos para generar un faceId.
               Validaciones:
                   - Presencia de exactamente una cara.
                   - Nitidez adecuada (Laplacian variance > 100).
                   - Formato de color RGB (convierte RGBA a RGB si es necesario).
                   - Token JWT válido.
               """
        # 1. Validar campos obligatorios
        if 'image' not in request.FILES or 'token' not in request.data:
            return JsonResponse(
                {'error': 'Se requieren la imagen y el token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        image_file = request.FILES['image']
        token = request.data['token']

        # 2. Validar token JWT
        try:
            decoded_token = jwt.decode(token, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
            id_file = decoded_token.get("userId")
            name_university = decoded_token.get("universityName")
            connection_db = decoded_token.get("connectionDb")
        except InvalidTokenError:
            return JsonResponse(
                {'error': 'Token inválido o expirado.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Inicializar conexión dinámica
            db_connection = DynamicDbConnection(connection_db)
            db_connection.initialize_pool()
            # Leer imagen
            image = face_recognition.load_image_file(image_file)
            incidencias = []

            # 3.1. Convertir RGBA a RGB si es necesario
            if image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

            # 3.2. Validar nitidez (Laplacian variance)
            gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            laplacian_var = cv2.Laplacian(gray_image, cv2.CV_64F).var()
            if laplacian_var < 40:
                incidencias.append("low_image_quality")

            # 3.3. Validar caras
            face_encodings = face_recognition.face_encodings(image)

            if not face_encodings:
                incidencias.append("no_face_detected")
            elif len(face_encodings) > 1:
                incidencias.append("multiple_faces_detected")

            # 4. Respuesta según validaciones
            if incidencias:
                return JsonResponse(
                    {
                        'status': 'rejected',
                        'incidencias': incidencias,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            # 5. Si pasa validaciones, subir a Cloudinary
            try:
                # Reiniciamos el puntero del archivo porque fue leído por face_recognition
                image_file.seek(0)
                # Generar un nombre de archivo único basado en el ID del usuario
                filename = f"user_{id_file}"

                # Normalizar nombre de universidad (sin espacios ni caracteres raros)
                safe_university_name = name_university.strip().replace(" ", "_").lower()

                # Concatenar carpeta principal con subcarpeta de la universidad
                cloudinary_folder = f"{settings.CLOUDINARY['folder']}/{safe_university_name}"

                upload_result = cloudinary.uploader.upload(
                    image_file,
                    folder=cloudinary_folder,
                    upload_preset=settings.CLOUDINARY.get('upload_preset'),
                    resource_type="image",
                    public_id=filename
                    # Puedes agregar más opciones como:
                    # allowed_formats=["jpg", "png", "jpeg"],
                    # transformation=[
                    #     {'width': 500, 'height': 500, 'crop': 'limit'}
                    # ]
                )

                # ✅ Actualizamos face_id y la validación
                update_query = "UPDATE usuarios SET is_student_valid = TRUE, face_id = %s WHERE id = %s"
                db_connection.execute_query(update_query, params=(upload_result['public_id'], id_file))

                # 6. Retornar éxito con la URL de Cloudinary
                return JsonResponse(
                    {
                        'status': 'success',
                        'message': 'La imagen cumple con todos los requisitos.',
                        # 'image_url': upload_result['secure_url'],
                        # 'public_id': upload_result['public_id']
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as upload_error:
                return JsonResponse(
                    {
                        'error': f'Error al subir la imagen a Cloudinary: {str(upload_error)}'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return JsonResponse(
                {'error': f'Error en el procesamiento: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
