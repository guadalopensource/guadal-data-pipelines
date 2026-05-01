import geopandas as gpd
import zipfile
import os

zip_path = "data/raw/informacion-arpsi.zip"

# Descomprimir
print("Descomprimiendo...")
with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall("data/raw/arpsis/")
    print(f"Archivos: {z.namelist()}")

# Buscar shapefile
shp_files = [f for f in os.listdir("data/raw/arpsis/") if f.endswith(".shp")]
print(f"Shapefiles encontrados: {shp_files}")

# Cargar
gdf = gpd.read_file(f"data/raw/arpsis/{shp_files[0]}")
print(f"Total ARPSIs España: {len(gdf)}")
print(f"Columnas: {list(gdf.columns)}")
print(gdf.head(3))

# Filtrar Málaga
malaga = gdf[gdf.apply(
    lambda row: "laga" in str(row.values).lower() or "29" in str(row.values),
    axis=1
)]
print(f"\nARPSIs Málaga: {len(malaga)}")

# Guardar
os.makedirs("data/processed", exist_ok=True)
malaga.to_file("data/processed/arpsis_malaga.geojson", driver="GeoJSON")
print("Guardado en data/processed/arpsis_malaga.geojson")