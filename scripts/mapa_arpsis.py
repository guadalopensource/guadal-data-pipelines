import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as ctx
from pathlib import Path

# Rutas
INPUT = Path("data/processed/arpsis_malaga.geojson")
OUTPUT = Path("data/processed/mapa_arpsis_malaga.png")

# Cargar datos
print("Cargando ARPSIs Málaga...")
gdf = gpd.read_file(INPUT)
print(f"  {len(gdf)} ARPSIs cargadas")
print(f"  CRS original: {gdf.crs}")

# Reproyectar a Web Mercator para contextily
gdf = gdf.to_crs(epsg=3857)
gdf = gdf.cx[-560000:-290000, 4340000:4520000]

# Colorear por mecanismo de inundación
mecanismos = gdf["MECAN_INU"].unique()
print(f"  Mecanismos de inundación: {mecanismos}")

colores = {m: c for m, c in zip(mecanismos, plt.cm.tab10.colors)}
gdf["color"] = gdf["MECAN_INU"].map(colores)

# Generar mapa
fig, ax = plt.subplots(figsize=(12, 10))

for mecanismo, grupo in gdf.groupby("MECAN_INU"):
    grupo.plot(ax=ax, color=colores[mecanismo], linewidth=2.5, label=mecanismo)

# Capa base
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=9)

# Fijar extent a Málaga
ax.set_xlim(-560000, -290000)
ax.set_ylim(4340000, 4520000)

# Leyenda y títulos
leyenda = [mpatches.Patch(color=colores[m], label=m) for m in colores]
ax.legend(handles=leyenda, loc="lower right", fontsize=8, title="Mecanismo inundación")
ax.set_title("ARPSIs Málaga — Áreas de Riesgo Potencial Significativo de Inundación", fontsize=13)
ax.set_axis_off()

plt.tight_layout()
plt.savefig(OUTPUT, dpi=150, bbox_inches="tight")
print(f"Mapa guardado en {OUTPUT}")