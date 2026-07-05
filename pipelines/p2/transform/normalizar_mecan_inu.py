"""Normalizar el campo MECAN_INU en los datos ARPSI de Málaga.

Este script:
1. Descarga el archivo ARPSI de Silver
2. Normaliza el campo MECAN_INU a un valor estándar
3. Sube la versión normalizada a Silver

Uso:
    python -m pipelines.p2.transform.normalizar_mecan_inu

Variables de entorno requeridas:
    HETZNER_ACCESS_KEY: Clave de acceso de Hetzner
    HETZNER_SECRET_KEY: Clave secreta de Hetzner
    HETZNER_BUCKET_PRIVATE: Bucket privado (default: guadal-lake)
    DATA_PROCESSED_DIR: Directorio de datos procesados (default: data/processed)
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
from dotenv import load_dotenv

from utils.s3 import upload, download

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
DATA_PROCESSED_DIR = Path(os.getenv("DATA_PROCESSED_DIR", "data/processed"))
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d")

# Ruta local
LOCAL_PATH = DATA_PROCESSED_DIR / "arpsis_malaga.geojson"

# Valor normalizado
VALOR_CORRECTO = 'Superación natural de la capacidad'


def main():
    """Ejecutar la normalización del campo MECAN_INU."""
    try:
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        # ── CARGAR DESDE SILVER ───────────────────────────
        logger.info("Descargando desde Silver...")
        download(
            f"silver/p2-riesgo-hidrico/arpsis_malaga_{TIMESTAMP}.geojson",
            str(LOCAL_PATH)
        )
        
        # ── TRANSFORMAR ───────────────────────────────────
        logger.info("Normalizando campo MECAN_INU...")
        gdf = gpd.read_file(LOCAL_PATH)
        logger.info(f"Registros cargados: {len(gdf)}")
        
        # Contar valores actuales
        logger.info(f"Valores actuales de MECAN_INU:\n{gdf['MECAN_INU'].value_counts()}")
        
        # Normalizar
        gdf['MECAN_INU'] = VALOR_CORRECTO
        
        logger.info(f"\nValores después de normalización:\n{gdf['MECAN_INU'].value_counts()}")
        logger.info(f"\nTotal registros: {len(gdf)}")
        
        # ── GUARDAR LOCAL ─────────────────────────────────
        logger.info("Guardando local...")
        gdf.to_file(LOCAL_PATH, driver='GeoJSON')
        
        # ── SILVER: subir versión normalizada ─────────────
        logger.info("Subiendo a Silver normalizado...")
        upload(
            str(LOCAL_PATH),
            f"silver/p2-riesgo-hidrico/arpsis_malaga_normalizado_{TIMESTAMP}.geojson"
        )
        
        logger.info("\n✅ Transformación completada.")
        logger.info(f"  Silver: silver/p2-riesgo-hidrico/arpsis_malaga_normalizado_{TIMESTAMP}.geojson")
        
    except FileNotFoundError as e:
        logger.error(f"❌ Archivo no encontrado: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error en normalización: {e}")
        raise


if __name__ == "__main__":
    main()
