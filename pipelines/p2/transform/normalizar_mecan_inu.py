import geopandas as gpd
import os
from datetime import datetime, timezone
from utils.s3 import upload, download

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")

# ── CARGAR DESDE SILVER ───────────────────────────
print("Descargando Silver...")
local_path = "data/processed/arpsis_malaga.geojson"
download(
    f"silver/p2-riesgo-hidrico/arpsis_malaga_{timestamp}.geojson",
    local_path
)

# ── TRANSFORMAR ───────────────────────────────────
gdf = gpd.read_file(local_path)
print(f"Registros cargados: {len(gdf)}")

valor_correcto = 'Superación natural de la capacidad'
gdf['MECAN_INU'] = valor_correcto

print(gdf['MECAN_INU'].value_counts())
print(f"\nTotal registros: {len(gdf)}")

# ── GUARDAR LOCAL ─────────────────────────────────
os.makedirs("data/processed", exist_ok=True)
gdf.to_file(local_path, driver='GeoJSON')
print("Guardado local.")

# ── SILVER: subir versión normalizada ─────────────
print("Subiendo Silver normalizado...")
upload(
    local_path,
    f"silver/p2-riesgo-hidrico/arpsis_malaga_normalizado_{timestamp}.geojson"
)

print("\nTransformación completada.")
print(f"  Silver: arpsis_malaga_normalizado_{timestamp}.geojson")