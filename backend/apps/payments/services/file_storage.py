"""
Servicio híbrido para manejo de archivos
Funciona tanto con almacenamiento local como con Cloudinary
"""
import os
import base64
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class HybridFileStorage:
    """
    Servicio híbrido para manejo de archivos
    - Local: Para desarrollo y testing
    - Cloudinary: Para producción
    """
    
    @staticmethod
    def save_file(file_data, folder_path="bank_transfers", filename=None):
        """
        Guarda un archivo usando el método configurado
        
        Args:
            file_data: Archivo (FileField, InMemoryUploadedFile, o base64 string)
            folder_path: Carpeta donde guardar
            filename: Nombre del archivo (opcional)
            
        Returns:
            dict: {
                'success': bool,
                'file_url': str,
                'file_path': str,
                'filename': str,
                'storage_type': str
            }
        """
        try:
            # Determinar el tipo de almacenamiento
            if getattr(settings, 'USE_CLOUDINARY', False):
                return HybridFileStorage._save_to_cloudinary(file_data, folder_path, filename)
            else:
                return HybridFileStorage._save_to_local(file_data, folder_path, filename)
                
        except Exception as e:
            logger.error(f"Error guardando archivo: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_url': None,
                'file_path': None,
                'filename': None,
                'storage_type': 'error'
            }
    
    @staticmethod
    def _save_to_local(file_data, folder_path, filename):
        """Guarda archivo en almacenamiento local"""
        try:
            # Crear directorio si no existe
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            full_path = os.path.join(media_root, folder_path)
            os.makedirs(full_path, exist_ok=True)
            
            # Generar nombre de archivo si no se proporciona
            if not filename:
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                if hasattr(file_data, 'name'):
                    ext = os.path.splitext(file_data.name)[1]
                    filename = f"receipt_{timestamp}{ext}"
                else:
                    filename = f"receipt_{timestamp}.pdf"
            
            # Ruta completa del archivo
            file_path = os.path.join(folder_path, filename)
            full_file_path = os.path.join(media_root, file_path)
            
            # Guardar archivo
            if isinstance(file_data, str) and file_data.startswith('data:'):
                # Es base64
                file_content = HybridFileStorage._decode_base64_file(file_data)
                with open(full_file_path, 'wb') as f:
                    f.write(file_content)
            else:
                # Es un archivo normal
                with open(full_file_path, 'wb') as f:
                    for chunk in file_data.chunks():
                        f.write(chunk)
            
            # URL del archivo
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            file_url = f"{media_url}{file_path}"
            
            logger.info(f"Archivo guardado localmente: {file_path}")
            
            return {
                'success': True,
                'file_url': file_url,
                'file_path': file_path,
                'filename': filename,
                'storage_type': 'local'
            }
            
        except Exception as e:
            logger.error(f"Error guardando archivo local: {str(e)}")
            raise e
    
    @staticmethod
    def _save_to_cloudinary(file_data, folder_path, filename):
        """Guarda archivo en Cloudinary"""
        try:
            import cloudinary.uploader
            
            # Generar nombre de archivo si no se proporciona
            if not filename:
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                if hasattr(file_data, 'name'):
                    ext = os.path.splitext(file_data.name)[1]
                    filename = f"receipt_{timestamp}{ext}"
                else:
                    filename = f"receipt_{timestamp}.pdf"
            
            # Preparar archivo para Cloudinary
            if isinstance(file_data, str) and file_data.startswith('data:'):
                # Es base64
                file_content = HybridFileStorage._decode_base64_file(file_data)
                file_obj = ContentFile(file_content, name=filename)
            else:
                # Es un archivo normal
                file_obj = file_data
            
            # Subir a Cloudinary
            result = cloudinary.uploader.upload(
                file_obj,
                folder=folder_path,
                public_id=filename.split('.')[0],  # Sin extensión
                resource_type="auto",
                overwrite=True
            )
            
            logger.info(f"Archivo subido a Cloudinary: {result['public_id']}")
            
            return {
                'success': True,
                'file_url': result['secure_url'],
                'file_path': result['public_id'],
                'filename': filename,
                'storage_type': 'cloudinary'
            }
            
        except Exception as e:
            logger.error(f"Error subiendo a Cloudinary: {str(e)}")
            raise e
    
    @staticmethod
    def _decode_base64_file(base64_string):
        """Decodifica un archivo base64"""
        try:
            # Extraer datos base64 del data URL
            header, file_data = base64_string.split(',', 1)
            return base64.b64decode(file_data)
        except Exception as e:
            logger.error(f"Error decodificando base64: {str(e)}")
            raise e
    
    @staticmethod
    def delete_file(file_path, storage_type=None):
        """
        Elimina un archivo del almacenamiento correspondiente
        
        Args:
            file_path: Ruta del archivo a eliminar
            storage_type: Tipo de almacenamiento ('local' o 'cloudinary')
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            if storage_type == 'cloudinary' or getattr(settings, 'USE_CLOUDINARY', False):
                return HybridFileStorage._delete_from_cloudinary(file_path)
            else:
                return HybridFileStorage._delete_from_local(file_path)
                
        except Exception as e:
            logger.error(f"Error eliminando archivo: {str(e)}")
            return False
    
    @staticmethod
    def _delete_from_local(file_path):
        """Elimina archivo del almacenamiento local"""
        try:
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            full_path = os.path.join(media_root, file_path)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"Archivo eliminado localmente: {file_path}")
                return True
            else:
                logger.warning(f"Archivo no encontrado para eliminar: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error eliminando archivo local: {str(e)}")
            return False
    
    @staticmethod
    def _delete_from_cloudinary(public_id):
        """Elimina archivo de Cloudinary"""
        try:
            import cloudinary.uploader
            
            result = cloudinary.uploader.destroy(public_id)
            
            if result.get('result') == 'ok':
                logger.info(f"Archivo eliminado de Cloudinary: {public_id}")
                return True
            else:
                logger.warning(f"Error eliminando de Cloudinary: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error eliminando de Cloudinary: {str(e)}")
            return False
    
    @staticmethod
    def get_file_url(file_path, storage_type=None):
        """
        Obtiene la URL completa de un archivo
        
        Args:
            file_path: Ruta del archivo
            storage_type: Tipo de almacenamiento
            
        Returns:
            str: URL completa del archivo
        """
        if storage_type == 'cloudinary' or getattr(settings, 'USE_CLOUDINARY', False):
            # Para Cloudinary, la URL ya está completa
            return file_path
        else:
            # Para local, construir URL completa
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            return f"{media_url}{file_path}"
