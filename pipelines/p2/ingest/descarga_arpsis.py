import geopandas as gpd
import zipfile
import os
from datetime import datetime, timezone
from utils.s3 import upload

# ── PATHS ────────────────────────────────────────
zip_path = "data/raw/informacion-arpsi.zip"
timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")

# ── BRONZE: subir raw ────────────────────────────
print("Subiendo Bronze...")
upload(zip_path, f"bronze/p2-riesgo-hidrico/arpsis_raw_{timestamp}.zip")

# ── PROCESAR ─────────────────────────────────────
print("Descomprimiendo...")
with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall("data/raw/arpsis/")
    print(f"Archivos: {z.namelist()}")

shp_files = [f for f in os.listdir("data/raw/arpsis/") if f.endswith(".shp")]
print(f"Shapefiles encontrados: {shp_files}")

gdf = gpd.read_file(f"data/raw/arpsis/{shp_files[0]}")
print(f"Total ARPSIs España: {len(gdf)}")

malaga = gdf[gdf.apply(
    lambda row: "laga" in str(row.values).lower() or "29" in str(row.values),
    axis=1
)]
print(f"ARPSIs Málaga: {len(malaga)}")

# ── GUARDAR LOCAL ─────────────────────────────────
os.makedirs("data/processed", exist_ok=True)
geojson_path = "data/processed/arpsis_malaga.geojson"
malaga.to_file(geojson_path, driver="GeoJSON")
print(f"Guardado local: {geojson_path}")

# ── SILVER: subir procesado ───────────────────────
print("Subiendo Silver...")
upload(geojson_path, f"silver/p2-riesgo-hidrico/arpsis_malaga_{timestamp}.geojson")

print("\nPipeline completado.")
print(f"  Bronze: arpsis_raw_{timestamp}.zip")
print(f"  Silver: arpsis_malaga_{timestamp}.geojson")