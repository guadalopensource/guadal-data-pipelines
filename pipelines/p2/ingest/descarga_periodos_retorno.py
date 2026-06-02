# pipelines/p2/ingest/descarga_periodos_retorno.py
import geopandas as gpd
import zipfile
import os
from datetime import datetime, timezone
from utils.s3 import upload

PERIODOS = {
    'T10':  'data/raw/periodos_retorno/zi_t10_manual.zip',
    'T50':  'data/raw/periodos_retorno/zi_t50_manual.zip',
    'T100': 'data/raw/periodos_retorno/zi_t100_manual.zip',
    'T500': 'data/raw/periodos_retorno/zi_t500_manual.zip',
}

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
os.makedirs("data/processed", exist_ok=True)

for periodo, zip_path in PERIODOS.items():
    print(f"\n── {periodo} ──────────────────")

    # ── BRONZE: subir raw ────────────────────────
    print(f"Subiendo Bronze...")
    upload(zip_path, f"bronze/p2-riesgo-hidrico/zi_{periodo.lower()}_{timestamp}.zip")

    # ── PROCESAR: descomprimir y filtrar Málaga ───
    extract_dir = f"data/raw/periodos_retorno/zi_{periodo.lower()}/"
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_dir)

    shp = [f for f in os.listdir(extract_dir) if f.endswith('.shp')][0]
    gdf = gpd.read_file(f"{extract_dir}{shp}")
    print(f"Total España: {len(gdf)}")

    # Filtrar por bbox de Málaga (EPSG:4326)
    malaga_bbox = (-5.6, 36.4, -3.8, 37.3)
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    malaga = gdf.cx[malaga_bbox[0]:malaga_bbox[2], malaga_bbox[1]:malaga_bbox[3]]
    print(f"Málaga {periodo}: {len(malaga)} polígonos")

    # ── SILVER: subir filtrado ────────────────────
    silver_path = f"data/processed/zi_{periodo.lower()}_malaga.geojson"
    malaga.to_file(silver_path, driver='GeoJSON')
    upload(silver_path, f"silver/p2-riesgo-hidrico/zi_{periodo.lower()}_malaga_{timestamp}.geojson")

    # ── GOLD: subir listo para dashboard ─────────
    upload(silver_path, f"gold/p2-riesgo-hidrico/zi_{periodo.lower()}_malaga_{timestamp}.geojson")
    print(f"  Gold: zi_{periodo.lower()}_malaga_{timestamp}.geojson")

print("\nPipeline períodos de retorno completado.")