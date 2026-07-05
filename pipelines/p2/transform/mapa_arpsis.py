"""Generar mapa visual de ARPSIs de Málaga.

Este script:
1. Carga los datos ARPSI de Málaga desde GeoJSON
2. Genera un mapa visual con diferentes colores por mecanismo de inundación
3. Guarda el mapa como imagen PNG

Uso:
    python -m pipelines.p2.transform.mapa_arpsis

Requisitos:
    - El archivo data/processed/arpsis_malaga.geojson debe existir
    - Se necesitan datos de contexto (OpenStreetMap) para el fondo
"""

import logging
import os
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as ctx
from dotenv import load_dotenv

# Cargar variables de entorno (para directorios)
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Paths
DATA_PROCESSED_DIR = Path(os.getenv("DATA_PROCESSED_DIR", "data/processed"))
INPUT = DATA_PROCESSED_DIR / "arpsis_malaga.geojson"
OUTPUT = DATA_PROCESSED_DIR / "mapa_arpsis_malaga.png"


def generar_mapa(gdf):
    """Generar mapa visual con los ARPSIs de Málaga.
    
    Args:
        gdf: GeoDataFrame con los ARPSIs de Málaga.
        
    Returns:
        None. Guarda el mapa en OUTPUT.
        
    Raises:
        ValueError: Si el GeoDataFrame está vacío.
    """
    if gdf.empty:
        logger.error("GeoDataFrame vacío. No hay datos para mapear.")
        raise ValueError("GeoDataFrame is empty")
    
    # Reproyectar a Web Mercator para contextily
    gdf = gdf.to_crs(epsg=3857)
    
    # Filtrar por bbox de Málaga en coordenadas Web Mercator
    # (aproximado: -5.6 a -3.8 lon, 36.4 a 37.3 lat)
    # En Web Mercator: x ≈ -560000 a -290000, y ≈ 4340000 a 4520000
    gdf = gdf.cx[-560000:-290000, 4340000:4520000]
    
    # Colorear por mecanismo de inundación
    mecanismos = gdf["MECAN_INU"].unique()
    logger.info(f"Mecanismos de inundación encontrados: {list(mecanismos)}")
    
    if len(mecanismos) == 0:
        logger.warning("No se encontró columna MECAN_INU. Usando color único.")
        colores = {"default": plt.cm.tab10(0)}
        gdf["color"] = plt.cm.tab10(0)
    else:
        colores = {m: c for m, c in zip(mecanismos, plt.cm.tab10.colors)}
        gdf["color"] = gdf["MECAN_INU"].map(colores)
    
    # Generar mapa
    fig, ax = plt.subplots(figsize=(12, 10))
    
    if len(mecanismos) > 0:
        for mecanismo, grupo in gdf.groupby("MECAN_INU"):
            grupo.plot(ax=ax, color=colores[mecanismo], linewidth=2.5, label=mecanismo)
    else:
        gdf.plot(ax=ax, color=colores["default"], linewidth=2.5, label="ARPSI")
    
    # Capa base
    try:
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=9)
    except Exception as e:
        logger.warning(f"No se pudo añadir capa base: {e}")
    
    # Fijar extent a Málaga
    ax.set_xlim(-560000, -290000)
    ax.set_ylim(4340000, 4520000)
    
    # Leyenda y títulos
    if len(mecanismos) > 0:
        leyenda = [mpatches.Patch(color=colores[m], label=m) for m in colores]
        ax.legend(handles=leyenda, loc="lower right", fontsize=8, title="Mecanismo inundación")
    
    ax.set_title(
        "ARPSIs Málaga — Áreas de Riesgo Potencial Significativo de Inundación",
        fontsize=13
    )
    ax.set_axis_off()
    
    plt.tight_layout()
    plt.savefig(OUTPUT, dpi=150, bbox_inches="tight")
    logger.info(f"✅ Mapa guardado en {OUTPUT}")


def main():
    """Ejecutar la generación del mapa."""
    try:
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info("Cargando ARPSIs Málaga...")
        if not INPUT.exists():
            logger.error(f"Archivo de entrada no encontrado: {INPUT}")
            raise FileNotFoundError(f"No existe: {INPUT}")
        
        gdf = gpd.read_file(INPUT)
        logger.info(f"  {len(gdf)} ARPSIs cargadas")
        logger.info(f"  CRS original: {gdf.crs}")
        
        generar_mapa(gdf)
        logger.info("✅ Generación de mapa completada.")
        
    except Exception as e:
        logger.error(f"❌ Error generando mapa: {e}")
        raise


if __name__ == "__main__":
    main()
