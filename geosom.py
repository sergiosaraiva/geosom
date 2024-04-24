from sklearn.preprocessing import MinMaxScaler
import rasterio
from rasterio.transform import from_origin
from rasterio.features import rasterize
from scipy.ndimage import gaussian_filter
import pandas as pd
import geopandas as gpd
import numpy as np
from minisom import MiniSom

class GeoSom:
    @staticmethod
    def run(input_file, som_output_file, attributes, sigma=0.3, learning_rate=0.5, som_x=5, som_y=5, num_iteration=1000, target_crs=3763, geo_weight=1):
        # Load and reproject the geometries
        gdf = gpd.read_file(input_file)
        gdf = gdf.to_crs(epsg=target_crs)
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.001, preserve_topology=True)

        # Calculate centroids and extract them as separate float columns
        gdf['centroid_lon'] = gdf.geometry.centroid.x
        gdf['centroid_lat'] = gdf.geometry.centroid.y

        # Append geographic coordinates to attributes for normalization and SOM processing
        full_attributes = attributes + ['centroid_lon', 'centroid_lat']
        data = gdf[full_attributes].to_numpy()

        # Normalize the data
        scaler = MinMaxScaler()
        data_normalized = scaler.fit_transform(data)
        data_normalized[:, -2:] *= geo_weight  # Apply geo_weight to longitude and latitude

        # Initialize and train SOM
        #som = CircularMiniSom(som_x, som_y, len(full_attributes), sigma=sigma, learning_rate=learning_rate)
        som = MiniSom(som_x, som_y, len(full_attributes), sigma=sigma, learning_rate=learning_rate)
        som.train_random(data_normalized, num_iteration)

        # Assign clusters using a unique integer for each (x, y) position
        gdf['cluster'] = [x * som_y + y for x, y in (som.winner(d) for d in data_normalized)]

        # Create DataFrame for normalized data
        normalized_df = pd.DataFrame(data_normalized, columns=full_attributes, index=gdf.index)
        output_gdf = gdf[['geometry', 'cluster']].join(normalized_df)

        # Find and include the ID column if exists
        id_column = next((col for col in gdf.columns if col.upper() in ['ID', 'OBJECTID', 'OBJECT_ID', 'FID']), None)
        if id_column:
            output_gdf[id_column] = gdf[id_column]

        # Drop the '_normalized' suffix and save the output
        output_gdf.columns = [col.replace('_normalized', '') for col in output_gdf.columns]
        output_gdf.to_file(som_output_file, driver='GPKG')


    @staticmethod
    def to_raster(gdf_or_file, raster_output_file, cell_size=0.5, max_cells=10000000):
        if isinstance(gdf_or_file, str):
            gdf = gpd.read_file(gdf_or_file)
        else:
            gdf = gdf_or_file

        bounds = gdf.total_bounds
        x_min, y_min, x_max, y_max = bounds
        print(f"Initial Bounds: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")

        # Calculate initial raster dimensions
        width = int((x_max - x_min) / cell_size)
        height = int((y_max - y_min) / cell_size)

        # Ensure dimensions are not zero
        if width == 0 or height == 0:
            raise ValueError(f"Calculated width or height is zero with cell_size {cell_size}. Adjust cell size and retry.")

        # Dynamic adjustment if necessary
        while width * height > max_cells:
            cell_size *= 2  # Double the cell size to reduce the number of cells
            width = int((x_max - x_min) / cell_size)
            height = int((y_max - y_min) / cell_size)
            print(f"Adjusted cell_size to {cell_size} with dimensions {width} x {height}")
            if cell_size > max(x_max - x_min, y_max - y_min):
                raise ValueError("Adjusted cell size too large, resulting in zero dimensions.")

        transform = from_origin(x_min, y_max, cell_size, cell_size)

        raster = rasterize(
            [(geom, value) for geom, value in zip(gdf.geometry, gdf['cluster'])],
            out_shape=(height, width),
            transform=transform,
            fill=-1,
            all_touched=True,
            dtype='float32'
        )

        meta = {
            'driver': 'GTiff',
            'dtype': 'float32',
            'nodata': -1,
            'width': width,
            'height': height,
            'count': 1,
            'crs': gdf.crs,
            'transform': transform,
            'compress': 'lzw'
        }

        with rasterio.open(raster_output_file, 'w', **meta) as dst:
            dst.write(raster, 1)

        print(f"Raster created successfully with dimensions: {width} x {height}")


    @staticmethod
    def to_heatmap(raster_input_file, heatmap_output_file, sigma=1):
        with rasterio.open(raster_input_file) as src:
            raster = src.read(1)  # Read first band
            meta = src.meta

        heatmap = gaussian_filter(raster, sigma=sigma)
        heatmap[heatmap < 0] = -1

        # Round the values in the heatmap array to 2 decimal places
        heatmap_rounded = np.round(heatmap, decimals=2)
        
        meta.update(dtype='float32', compress='lzw')

        with rasterio.open(heatmap_output_file, 'w', **meta) as dst:
            dst.write(heatmap_rounded, 1)