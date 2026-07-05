#!/usr/bin/env python3
"""
Script para sincronizar datos de la capa Gold (privada) a guadal-lake-public (pública).
Uso:
    python -m pipelines.p2.utils.sync_public

Las credenciales se pueden proporcionar mediante:
1. Variables de entorno en archivo .env
2. Argumentos de línea de comandos

Variables de entorno (archivo .env):
    HETZNER_ACCESS_KEY=tu_access_key
    HETZNER_SECRET_KEY=tu_secret_key
    HETZNER_ENDPOINT=https://fsn1.your-objectstorage.com
    HETZNER_REGION=fsn1
    PRIVATE_BUCKET=guadal-lake
    PUBLIC_BUCKET=guadal-lake-public
    PREFIX=gold/

Argumentos de línea de comandos (opcionales, sobreescriben el .env):
    --access-key    Clave de acceso de Hetzner Object Storage.
    --secret-key    Clave secreta de Hetzner Object Storage.
    --endpoint      Endpoint de Hetzner (por defecto: https://fsn1.your-objectstorage.com).
    --region        Región de Hetzner (por defecto: fsn1).
    --private-bucket  Bucket privado (por defecto: guadal-lake).
    --public-bucket   Bucket público (por defecto: guadal-lake-public).
    --prefix         Prefijo para sincronizar (por defecto: gold/).
"""

import argparse
import logging
import os
import sys
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError
import boto3

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def get_s3_client(access_key, secret_key, endpoint, region):
    """Crear cliente S3 para Hetzner Object Storage."""
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        return s3
    except NoCredentialsError:
        logger.error("No se proporcionaron credenciales de Hetzner. Usa --access-key y --secret-key.")
        raise
    except Exception as e:
        logger.error(f"Error al crear cliente S3: {e}")
        raise


def list_objects(s3, bucket, prefix=""):
    """Listar todos los objetos en un bucket con un prefijo dado."""
    objects = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if "Contents" in page:
            objects.extend(page["Contents"])
    return objects


def sync_gold_to_public(s3, private_bucket, public_bucket, prefix):
    """Sincronizar todos los archivos de gold/ en el bucket privado al público."""
    logger.info(f"Listando objetos en {private_bucket}/{prefix}...")
    private_objects = list_objects(s3, private_bucket, prefix)

    if not private_objects:
        logger.warning(f"No se encontraron objetos en {private_bucket}/{prefix}")
        return 0

    logger.info(f"Encontrados {len(private_objects)} objetos en {private_bucket}/{prefix}")

    copied_count = 0
    for obj in private_objects:
        key = obj["Key"]
        public_key = key  # Mismo nombre en el bucket público

        # Verificar si ya existe en el bucket público
        try:
            s3.head_object(Bucket=public_bucket, Key=public_key)
            logger.info(f"El objeto {key} ya existe en {public_bucket}. Saltando...")
            continue
        except ClientError as e:
            if e.response["Error"]["Code"] != "404":
                logger.error(f"Error al verificar {public_key} en {public_bucket}: {e}")
                continue

        # Copiar el objeto
        copy_source = {"Bucket": private_bucket, "Key": key}
        try:
            s3.copy_object(
                Bucket=public_bucket,
                Key=public_key,
                CopySource=copy_source,
                ACL="public-read",  # Hacer el objeto público
            )
            logger.info(f"Copiado: {key} -> {public_bucket}/{public_key}")
            copied_count += 1
        except ClientError as e:
            logger.error(f"Error al copiar {key}: {e}")

    logger.info(f"Sincronización completa. Objetos copiados: {copied_count}/{len(private_objects)}")
    return copied_count


def verify_public_access(s3, public_bucket, prefix):
    """Verificar que los objetos en el bucket público son accesibles."""
    logger.info(f"Verificando acceso público a {public_bucket}/{prefix}...")
    public_objects = list_objects(s3, public_bucket, prefix)

    if not public_objects:
        logger.warning(f"No se encontraron objetos en {public_bucket}/{prefix}")
        return []

    accessible_urls = []
    endpoint_url = s3.meta.endpoint_url
    bucket_domain = f"{public_bucket}.{endpoint_url.split('//')[1]}"

    for obj in public_objects:
        key = obj["Key"]
        public_url = f"https://{bucket_domain}/{key}"
        accessible_urls.append(public_url)
        logger.info(f"Objeto accesible: {public_url}")

    return accessible_urls


def main():
    """Función principal."""
    # Cargar variables de entorno desde .env
    load_dotenv()

    # Obtener valores por defecto desde variables de entorno
    default_access_key = os.getenv("HETZNER_ACCESS_KEY")
    default_secret_key = os.getenv("HETZNER_SECRET_KEY")
    default_endpoint = os.getenv("HETZNER_ENDPOINT", "https://fsn1.your-objectstorage.com")
    default_region = os.getenv("HETZNER_REGION", "fsn1")
    default_private_bucket = os.getenv("PRIVATE_BUCKET", "guadal-lake")
    default_public_bucket = os.getenv("PUBLIC_BUCKET", "guadal-lake-public")
    default_prefix = os.getenv("PREFIX", "gold/")

    parser = argparse.ArgumentParser(
        description="Sincroniza datos de la capa Gold a guadal-lake-public."
    )
    parser.add_argument(
        "--access-key",
        default=default_access_key,
        help="Clave de acceso (Access Key) de Hetzner Object Storage. Se puede omitir si HETZNER_ACCESS_KEY está en .env."
    )
    parser.add_argument(
        "--secret-key",
        default=default_secret_key,
        help="Clave secreta (Secret Key) de Hetzner Object Storage. Se puede omitir si HETZNER_SECRET_KEY está en .env."
    )
    parser.add_argument(
        "--endpoint",
        default=default_endpoint,
        help="Endpoint de Hetzner Object Storage (por defecto: .env o https://fsn1.your-objectstorage.com)."
    )
    parser.add_argument(
        "--region",
        default=default_region,
        help="Región de Hetzner (por defecto: .env o fsn1)."
    )
    parser.add_argument(
        "--private-bucket",
        default=default_private_bucket,
        help="Nombre del bucket privado (por defecto: .env o guadal-lake)."
    )
    parser.add_argument(
        "--public-bucket",
        default=default_public_bucket,
        help="Nombre del bucket público (por defecto: .env o guadal-lake-public)."
    )
    parser.add_argument(
        "--prefix",
        default=default_prefix,
        help="Prefijo para sincronizar (por defecto: .env o gold/)."
    )

    args = parser.parse_args()

    # Validar que se proporcionaron credenciales (por CLI o por .env)
    if not args.access_key or not args.secret_key:
        logger.error("No se proporcionaron credenciales de Hetzner.")
        logger.error("Proporciónalas mediante:")
        logger.error("  1. Archivo .env con HETZNER_ACCESS_KEY y HETZNER_SECRET_KEY")
        logger.error("  2. Argumentos --access-key y --secret-key")
        return 1

    try:
        s3 = get_s3_client(
            args.access_key,
            args.secret_key,
            args.endpoint,
            args.region
        )
        copied_count = sync_gold_to_public(
            s3,
            args.private_bucket,
            args.public_bucket,
            args.prefix
        )

        if copied_count > 0:
            accessible_urls = verify_public_access(
                s3,
                args.public_bucket,
                args.prefix
            )
            logger.info("\n=== URLs PÚBLICAS VERIFICADAS ===")
            for url in accessible_urls:
                logger.info(url)

    except Exception as e:
        logger.error(f"Error en la sincronización: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
