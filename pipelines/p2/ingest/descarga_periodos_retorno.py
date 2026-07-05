"""Pipeline P2: Descarga y procesamiento de períodos de retorno (T10, T50, T100, T500).

Este script procesa datos de períodos de retorno de inundaciones:
1. Sube cada ZIP crudo a Bronze layer
2. Extrae el shapefile y filtra por bbox de Málaga
3. Sube el resultado procesado a Silver layer
4. Sube a Gold layer (listo para dashboard)

Uso:
    python -m pipelines.p2.ingest.descarga_periodos_retorno

Variables de entorno requeridas:
    HETZNER_ACCESS_KEY: Clave de acceso de Hetzner
    HETZNER_SECRET_KEY: Clave secreta de Hetzner
    HETZNER_BUCKET_PRIVATE: Bucket privado (default: guadal-lake)
    DATA_RAW_DIR: Directorio de datos crudos (default: data/raw)
    DATA_PROCESSED_DIR: Directorio de datos procesados (default: data/processed)
"""

import logging
import os
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

# Períodos de retorno y sus archivos ZIP
PERIODOS = {
    'T10': 'data/raw/periodos_retorno/zi_t10_manual.zip',
    'T50': 'data/raw/periodos_retorno/zi_t50_manual.zip',
    'T100': 'data/raw/periodos_retorno/zi_t100_manual.zip',
    'T500': 'data/raw/periodos_retorno/zi_t500_manual.zip',
}

# Bounding box de Málaga (EPSG:4326)
MALAGA_BBOX = (-5.6, 36.4, -3.8, 37.3)


def procesar_periodo(periodo: str, zip_path: str) -> Path:
    """Procesar un período de retorno específico.
    
    Args:
        periodo: Identificador del período (T10, T50, T100, T500).
        zip_path: Ruta local al archivo ZIP.
        
    Returns:
        Path: Ruta al archivo GeoJSON procesado.
        
    Raises:
        FileNotFoundError: Si el ZIP o shapefile no existe.
    """
    import zipfile
    
    logger.info(f"\n── Procesando {periodo} ──────────────────")
    
    zip_path = Path(zip_path)
    if not zip_path.exists():
        logger.error(f"Archivo ZIP no encontrado: {zip_path}")
        raise FileNotFoundError(f"No existe: {zip_path}")
    
    # ── BRONZE: subir raw ────────────────────────────
    logger.info(f"Subiendo {periodo} a Bronze...")
    upload(
        str(zip_path),
        f"bronze/p2-riesgo-hidrico/zi_{periodo.lower()}_{TIMESTAMP}.zip"
    )
    
    # ── PROCESAR: descomprimir y filtrar Málaga ───
    extract_dir = DATA_RAW_DIR / "periodos_retorno" / f"zi_{periodo.lower()}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_dir)
    
    # Buscar shapefile
    shp_files = list(extract_dir.glob("*.shp"))
    if not shp_files:
        logger.error(f"No se encontraron shapefiles en {extract_dir}")
        raise FileNotFoundError(f"No shapefiles found in {extract_dir}")
    
    # Leer shapefile
    gdf = gpd.read_file(str(shp_files[0]))
    logger.info(f"Total España {periodo}: {len(gdf)}")
    
    # Filtrar por bbox de Málaga
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    
    malaga = gdf.cx[
        MALAGA_BBOX[0]:MALAGA_BBOX[2],
        MALAGA_BBOX[1]:MALAGA_BBOX[3]
    ]
    logger.info(f"Málaga {periodo}: {len(malaga)} polígonos")
    
    # Guardar procesado
    silver_path = DATA_PROCESSED_DIR / f"zi_{periodo.lower()}_malaga.geojson"
    malaga.to_file(silver_path, driver='GeoJSON')
    
    # ── SILVER: subir filtrado ────────────────────
    upload(
        str(silver_path),
        f"silver/p2-riesgo-hidrico/zi_{periodo.lower()}_malaga_{TIMESTAMP}.geojson"
    )
    
    # ── GOLD: subir listo para dashboard ─────────
    upload(
        str(silver_path),
        f"gold/p2-riesgo-hidrico/zi_{periodo.lower()}_malaga_{TIMESTAMP}.geojson"
    )
    logger.info(f"  Gold: gold/p2-riesgo-hidrico/zi_{periodo.lower()}_malaga_{TIMESTAMP}.geojson")
    
    return silver_path


def main():
    """Ejecutar el pipeline completo de períodos de retorno."""
    try:
        # Crear directorios
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        for periodo, zip_path in PERIODOS.items():
            try:
                procesar_periodo(periodo, zip_path)
            except Exception as e:
                logger.error(f"Error procesando {periodo}: {e}")
                # Continuar con el siguiente período
                continue
        
        logger.info("\n✅ Pipeline períodos de retorno completado.")
        
    except Exception as e:
        logger.error(f"❌ Error en pipeline períodos de retorno: {e}")
        raise


if __name__ == "__main__":
    main()
