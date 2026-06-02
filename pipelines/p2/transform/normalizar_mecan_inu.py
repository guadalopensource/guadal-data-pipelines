import geopandas as gpd

# Cargar
gdf = gpd.read_file('data/processed/arpsis_malaga.geojson')

# Normalizar
valor_correcto = 'Superación natural de la capacidad'
gdf['MECAN_INU'] = valor_correcto

# Verificar
print(gdf['MECAN_INU'].value_counts())
print(f"\nTotal registros: {len(gdf)}")

# Guardar
gdf.to_file('data/processed/arpsis_malaga.geojson', driver='GeoJSON')
print("\nGuardado correctamente.")