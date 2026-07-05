"""Pipeline P2: Descarga y procesamiento de datos ARPSI (Áreas de Riesgo Potencial Significativo de Inundación).

Este script:
1. Descarga el ZIP con datos ARPSI de España
2. Sube el archivo crudo a Bronze layer
3. Extrae el shapefile y filtra solo Málaga
4. Sube el resultado procesado a Silver layer

Uso:
    python -m pipelines.p2.ingest.descarga_arpsis

Variables de entorno requeridas:
    HETZNER_ACCESS_KEY: Clave de acceso de Hetzner
    HETZNER_SECRET_KEY: Clave secreta de Hetzner
    HETZNER_BUCKET_PRIVATE: Bucket privado (default: guadal-lake)
    DATA_RAW_DIR: Directorio de datos crudos (default: data/raw)
    DATA_PROCESSED_DIR: Directorio de datos procesados (default: data/processed)
"""

import logging
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
from dotenv import load_dotenv

from utils.s3 import upload

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constantes
DATA_RAW_DIR = Path(os.getenv("DATA_RAW_DIR", "data/raw"))
DATA_PROCESSED_DIR = Path(os.getenv("DATA_PROCESSED_DIR", "data/processed"))
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d")

# Paths
ZIP_PATH = DATA_RAW_DIR / "informacion-arpsi.zip"
ARPSI_DIR = DATA_RAW_DIR / "arpsis"
OUTPUT_GEOJSON = DATA_PROCESSED_DIR / "arpsis_malaga.geojson"


def descargar_y_extraer_zip():
    """Descargar y extraer el ZIP con datos ARPSI.
    
    Returns:
        Path: Directorio donde se extrajeron los archivos.
        
    Raises:
        FileNotFoundError: Si el archivo ZIP no existe.
    """
    if not ZIP_PATH.exists():
        logger.error(f"Archivo ZIP no encontrado: {ZIP_PATH}")
        raise FileNotFoundError(f"No existe el archivo: {ZIP_PATH}")
    
    logger.info(f"Descomprimiendo {ZIP_PATH}...")
    ARPSI_DIR.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(ARPSI_DIR)
        logger.info(f"Archivos extraídos: {z.namelist()}")
    
    return ARPSI_DIR


def filtrar_malaga(gdf):
    """Filtrar el GeoDataFrame para obtener solo ARPSIs de Málaga.
    
    Args:
        gdf: GeoDataFrame con todos los ARPSIs de España.
        
    Returns:
        GeoDataFrame: Solo ARPSIs de Málaga.
    """
    logger.info(f"Total ARPSIs España: {len(gdf)}")
    
    # Filtrar por código provincial "29" (Málaga) o nombre que contenga "malaga"
    malaga = gdf[gdf.apply(
        lambda row: "malaga" in str(row.values).lower() or "29" in str(row.values),
        axis=1
    )]
    
    logger.info(f"ARPSIs Málaga: {len(malaga)}")
    return malaga


def main():
    """Ejecutar el pipeline completo de ARPSI."""
    try:
        # Crear directorios si no existen
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        # ── BRONZE: subir raw ────────────────────────────
        logger.info("Subiendo a Bronze...")
        upload(
            str(ZIP_PATH),
            f"bronze/p2-riesgo-hidrico/arpsis_raw_{TIMESTAMP}.zip"
        )
        
        # ── PROCESAR ─────────────────────────────────────
        logger.info("Procesando datos...")
        extract_dir = descargar_y_extraer_zip()
        
        # Buscar shapefiles
        shp_files = list(extract_dir.glob("*.shp"))
        if not shp_files:
            logger.error(f"No se encontraron shapefiles en {extract_dir}")
            raise FileNotFoundError(f"No shapefiles found in {extract_dir}")
        
        logger.info(f"Shapefiles encontrados: {[f.name for f in shp_files]}")
        
        # Leer y filtrar
        gdf = gpd.read_file(str(shp_files[0]))
        malaga = filtrar_malaga(gdf)
        
        # ── GUARDAR LOCAL ─────────────────────────────────
        logger.info(f"Guardando local: {OUTPUT_GEOJSON}")
        malaga.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
        
        # ── SILVER: subir procesado ───────────────────────
        logger.info("Subiendo a Silver...")
        upload(
            str(OUTPUT_GEOJSON),
            f"silver/p2-riesgo-hidrico/arpsis_malaga_{TIMESTAMP}.geojson"
        )
        
        logger.info("\n✅ Pipeline ARPSI completado.")
        logger.info(f"  Bronze: bronze/p2-riesgo-hidrico/arpsis_raw_{TIMESTAMP}.zip")
        logger.info(f"  Silver: silver/p2-riesgo-hidrico/arpsis_malaga_{TIMESTAMP}.geojson")
        
    except Exception as e:
        logger.error(f"❌ Error en pipeline ARPSI: {e}")
        raise


if __name__ == "__main__":
    main()
