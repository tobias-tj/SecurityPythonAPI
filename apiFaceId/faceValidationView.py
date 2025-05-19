import tempfile
import face_recognition
import os
import jwt
import requests
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from jwt.exceptions import InvalidTokenError


class FaceValidationView(APIView):

    def post(self, request):
        # Verificar si se han proporcionado la imagen y el documento de identidad
        if 'image' not in request.FILES or 'token' not in request.data:
            return JsonResponse({'error': 'No se han proporcionado una imagen o un documento de identidad.'}, status=400)

        image_file = request.FILES['image']
        token = request.data['token']
        connection_db = ''

        # Decodificar el token para obtener el document_id
        try:
            decoded_token = jwt.decode(token, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
            document_id = decoded_token.get("userId")
            connection_db= decoded_token.get("connectionDb")
            name_university = decoded_token.get("universityName")
            if not document_id:
                return JsonResponse({'error': 'El token no contiene el documento de identidad.'}, status=401)
        except InvalidTokenError:
            return JsonResponse({'error': 'Token inválido o expirado.'}, status=401)

        try:
            # Cargar la imagen y codificar la cara
            uploaded_img = face_recognition.load_image_file(image_file)
            uploaded_face_encodings = face_recognition.face_encodings(uploaded_img)

            if len(uploaded_face_encodings) == 0:
                return JsonResponse(
                    {'error': 'No se detectó ninguna cara en la imagen enviada.'},
                    status=400
                )

            uploaded_encoding = uploaded_face_encodings[0]

            # Normalizar nombre de universidad (sin espacios ni caracteres raros)
            safe_university_name = name_university.strip().replace(" ", "_").lower()

            # Concatenar carpeta principal con subcarpeta de la universidad
            cloudinary_folder = f"{settings.CLOUDINARY['folder']}/{safe_university_name}"

            # 2. Obtener imagen de referencia de Cloudinary
            cloudinary_url = f"{settings.CLOUDINARY['base_url']}/{cloudinary_folder}/user_{document_id}"
            print(cloudinary_url)

            # Descargar imagen temporalmente
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                # Descargar imagen desde Cloudinary
                response = requests.get(cloudinary_url)
                if response.status_code != 200:
                    return JsonResponse(
                        {'error': 'No se encontró la imagen de referencia en Cloudinary.'},
                        status=404
                    )

                temp_file.write(response.content)
                temp_file.flush()

                # Procesar imagen de referencia
                reference_img = face_recognition.load_image_file(temp_file.name)
                reference_face_encodings = face_recognition.face_encodings(reference_img)

                if len(reference_face_encodings) == 0:
                    return JsonResponse(
                        {'error': 'No se detectó ninguna cara en la imagen de referencia.'},
                        status=500
                    )

                reference_encoding = reference_face_encodings[0]

                # 3. Comparar las caras
                results = face_recognition.compare_faces(
                    [reference_encoding],
                    uploaded_encoding,
                    tolerance=0.6
                )

                # Limpiar el archivo temporal si existe
                if 'temp_file' in locals() and os.path.exists(temp_file.name):
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass

                if results[0]:
                    return JsonResponse(
                        {'success': True, 'message': 'Autenticación facial exitosa.'},
                        status=200
                    )
                else:
                    return JsonResponse(
                        {'success': False, 'error': 'La cara no coincide con la registrada.'},
                        status=401
                    )

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
