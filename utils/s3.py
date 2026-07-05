"""Módulo de utilidades para interacción con Hetzner Object Storage (S3).

Este módulo proporciona funciones para subir, descargar y listar objetos
en el data lake de Guadal (Hetzner Object Storage).

Variables de entorno requeridas:
    HETZNER_ACCESS_KEY: Clave de acceso de Hetzner
    HETZNER_SECRET_KEY: Clave secreta de Hetzner
    HETZNER_ENDPOINT: Endpoint de Hetzner (default: https://fsn1.your-objectstorage.com)
    HETZNER_REGION: Región de Hetzner (default: fsn1)
    HETZNER_BUCKET_PRIVATE: Bucket privado (default: guadal-lake)
    HETZNER_BUCKET_PUBLIC: Bucket público (default: guadal-lake-public)
"""

import logging
import os
from pathlib import Path
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logger = logging.getLogger(__name__)


def get_s3_client():
    """Crear y devolver un cliente S3 configurado para Hetzner Object Storage.
    
    Returns:
        boto3.client: Cliente S3 configurado.
        
    Raises:
        NoCredentialsError: Si no se encuentran credenciales.
        ValueError: Si las variables de entorno necesarias no están configuradas.
    """
    access_key = os.getenv("HETZNER_ACCESS_KEY")
    secret_key = os.getenv("HETZNER_SECRET_KEY")
    endpoint = os.getenv("HETZNER_ENDPOINT", "https://fsn1.your-objectstorage.com")
    region = os.getenv("HETZNER_REGION", "fsn1")
    
    if not access_key or not secret_key:
        logger.error("Credenciales de Hetzner no configuradas.")
        logger.error("Configura HETZNER_ACCESS_KEY y HETZNER_SECRET_KEY en .env")
        raise NoCredentialsError(
            "HETZNER_ACCESS_KEY y HETZNER_SECRET_KEY deben estar configuradas"
        )
    
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        logger.debug("Cliente S3 creado correctamente")
        return s3
    except Exception as e:
        logger.error(f"Error al crear cliente S3: {e}")
        raise


# Buckets por defecto
BUCKET_PRIVATE = os.getenv("HETZNER_BUCKET_PRIVATE", "guadal-lake")
BUCKET_PUBLIC = os.getenv("HETZNER_BUCKET_PUBLIC", "guadal-lake-public")


def upload(
    local_path: str,
    s3_key: str,
    bucket: Optional[str] = None,
) -> None:
    """Subir un archivo local a Hetzner Object Storage.
    
    Args:
        local_path: Ruta local del archivo a subir.
        s3_key: Clave (path) del objeto en S3 (ej: bronze/dataset/file.zip).
        bucket: Bucket de destino. Si None, usa HETZNER_BUCKET_PRIVATE.
        
    Raises:
        FileNotFoundError: Si local_path no existe.
        ClientError: Si falla la subida a S3.
    """
    bucket = bucket or BUCKET_PRIVATE
    local_path = Path(local_path)
    
    if not local_path.exists():
        logger.error(f"Archivo no encontrado: {local_path}")
        raise FileNotFoundError(f"No existe el archivo: {local_path}")
    
    try:
        s3 = get_s3_client()
        s3.upload_file(str(local_path), bucket, s3_key)
        logger.info(f"Archivo subido: {local_path} -> {bucket}/{s3_key}")
    except ClientError as e:
        logger.error(f"Error al subir {local_path} a {bucket}/{s3_key}: {e}")
        raise


def download(
    s3_key: str,
    local_path: str,
    bucket: Optional[str] = None,
) -> None:
    """Descargar un archivo de Hetzner Object Storage a local.
    
    Args:
        s3_key: Clave (path) del objeto en S3.
        local_path: Ruta local donde guardar el archivo.
        bucket: Bucket de origen. Si None, usa HETZNER_BUCKET_PRIVATE.
        
    Raises:
        ClientError: Si falla la descarga de S3.
    """
    bucket = bucket or BUCKET_PRIVATE
    local_path = Path(local_path)
    
    try:
        # Crear directorio padre si no existe
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        s3 = get_s3_client()
        s3.download_file(bucket, s3_key, str(local_path))
        logger.info(f"Archivo descargado: {bucket}/{s3_key} -> {local_path}")
    except ClientError as e:
        logger.error(f"Error al descargar {bucket}/{s3_key} a {local_path}: {e}")
        raise


def list_objects(
    prefix: str = "",
    bucket: Optional[str] = None,
) -> List[str]:
    """Listar todos los objetos en un bucket con un prefijo dado.
    
    Args:
        prefix: Prefijo para filtrar objetos (ej: 'bronze/' o 'silver/p2/'').
        bucket: Bucket a listar. Si None, usa HETZNER_BUCKET_PRIVATE.
        
    Returns:
        List[str]: Lista de claves (paths) de los objetos encontrados.
    """
    bucket = bucket or BUCKET_PRIVATE
    objects = []
    
    try:
        s3 = get_s3_client()
        paginator = s3.get_paginator("list_objects_v2")
        
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if "Contents" in page:
                objects.extend(obj["Key"] for obj in page["Contents"])
        
        logger.debug(f"Encontrados {len(objects)} objetos en {bucket}/{prefix}")
        return objects
    except ClientError as e:
        logger.error(f"Error al listar objetos en {bucket}/{prefix}: {e}")
        raise
