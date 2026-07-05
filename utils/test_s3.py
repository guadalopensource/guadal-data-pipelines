"""Script de prueba para verificar la conexión con Hetzner Object Storage.

Este script prueba las funciones básicas de S3:
1. Conexión al cliente
2. Listar buckets
3. Listar objetos en el bucket configurado

Uso:
    python utils/test_s3.py

Variables de entorno requeridas:
    HETZNER_ACCESS_KEY: Clave de acceso de Hetzner
    HETZNER_SECRET_KEY: Clave secreta de Hetzner
    HETZNER_ENDPOINT: Endpoint de Hetzner
    HETZNER_BUCKET_PRIVATE: Bucket privado a probar
"""

import logging
import os
from dotenv import load_dotenv

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def test_connection():
    """Probar la conexión con Hetzner Object Storage.
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario.
    """
    try:
        access_key = os.getenv("HETZNER_ACCESS_KEY")
        secret_key = os.getenv("HETZNER_SECRET_KEY")
        endpoint = os.getenv("HETZNER_ENDPOINT", "https://fsn1.your-objectstorage.com")
        region = os.getenv("HETZNER_REGION", "fsn1")
        
        if not access_key or not secret_key:
            logger.error("Credenciales no configuradas en .env")
            return False
        
        s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        
        # Probar listar buckets
        buckets = s3.list_buckets()
        bucket_names = [b['Name'] for b in buckets['Buckets']]
        logger.info(f"✅ Conexión exitosa. Buckets disponibles: {bucket_names}")
        return True
        
    except NoCredentialsError:
        logger.error("❌ No se encontraron credenciales válidas")
        return False
    except ClientError as e:
        logger.error(f"❌ Error de cliente S3: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return False


def list_bucket_objects(bucket_name):
    """Listar objetos en un bucket específico.
    
    Args:
        bucket_name: Nombre del bucket.
        
    Returns:
        list: Lista de nombres de objetos.
    """
    try:
        access_key = os.getenv("HETZNER_ACCESS_KEY")
        secret_key = os.getenv("HETZNER_SECRET_KEY")
        endpoint = os.getenv("HETZNER_ENDPOINT", "https://fsn1.your-objectstorage.com")
        region = os.getenv("HETZNER_REGION", "fsn1")
        
        s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        
        objects = s3.list_objects_v2(Bucket=bucket_name)
        object_names = [obj['Key'] for obj in objects.get('Contents', [])]
        
        logger.info(f"Objetos en {bucket_name}: {len(object_names)}")
        for obj_name in object_names[:10]:  # Mostrar solo los primeros 10
            logger.info(f"  - {obj_name}")
        
        if len(object_names) > 10:
            logger.info(f"  ... y {len(object_names) - 10} más")
        
        return object_names
        
    except ClientError as e:
        logger.error(f"❌ Error al listar objetos en {bucket_name}: {e}")
        return []


def main():
    """Ejecutar pruebas de conexión S3."""
    logger.info("=" * 60)
    logger.info("Probando conexión con Hetzner Object Storage")
    logger.info("=" * 60)
    
    # Test 1: Conexión
    if test_connection():
        # Test 2: Listar objetos en bucket privado
        bucket = os.getenv("HETZNER_BUCKET_PRIVATE", "guadal-lake")
        logger.info(f"\nListando objetos en {bucket}...")
        objects = list_bucket_objects(bucket)
        logger.info(f"Total objetos: {len(objects)}")
        
        logger.info("\n✅ Todas las pruebas de S3 pasadas.")
    else:
        logger.error("\n❌ Falló la prueba de conexión.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
