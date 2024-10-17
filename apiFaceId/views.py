import face_recognition
import numpy as np
import uuid
import os
from django.http import JsonResponse
from rest_framework.views import APIView
from .models import Face

class FaceRecognitionView(APIView):

    def post(self, request):
        # Verificar si se han proporcionado la imagen y el documento de identidad
        if 'image' not in request.FILES or 'document_id' not in request.data:
            return JsonResponse({'error': 'No se han proporcionado una imagen o un documento de identidad.'}, status=400)

        image_file = request.FILES['image']
        document_id = request.data['document_id']

        # Cargar la imagen
        try:
            image = face_recognition.load_image_file(image_file)
            face_encodings = face_recognition.face_encodings(image)

            if len(face_encodings) == 0:
                return JsonResponse({'error': 'No se ha detectado ninguna cara en la imagen.'}, status=400)

            face_encoding = face_encodings[0]  # Usar la primera cara detectada
            face_encoding_list = face_encoding.tolist()

            # Verificar si el document_id ya existe en la base de datos
            existing_face = Face.objects.filter(document_id=document_id).first()

            if existing_face:
                return JsonResponse({'error': 'El documento de identidad ya está registrado con otra cara.'}, status=400)

            # Buscar en la base de datos para ver si hay coincidencias
            existing_faces = Face.objects.all()

            for face in existing_faces:
                known_face_encoding_path = face.image.path  # Ruta del archivo de codificación

                # Comprobar si el archivo de codificación existe
                if os.path.exists(known_face_encoding_path):
                    known_face_encoding = np.load(known_face_encoding_path)  # Cargar la codificación de la cara guardada
                    results = face_recognition.compare_faces([known_face_encoding], face_encoding_list)

                    if results[0]:  # Si hay una coincidencia
                        return JsonResponse({'faceId': face.face_id, 'document_id': face.document_id})

            # Si no hay coincidencia, crear un nuevo faceId
            face_id = str(uuid.uuid4())
            encoding_file_path = os.path.join('face_encodings', f"{face_id}.npy")

            # Guardar la codificación de la cara como un archivo numpy
            np.save(encoding_file_path, face_encoding.astype(np.float32))  # Asegúrate de que sea un tipo de dato numérico

            # Crear una nueva entrada para el nuevo usuario
            new_face = Face(face_id=face_id, image=image_file, document_id=document_id)
            new_face.save()

            return JsonResponse({'faceId': face_id, 'document_id': document_id})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
