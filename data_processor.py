import geopandas as gpd
import numpy as np  # Ensure numpy is imported
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
from scipy.ndimage import gaussian_filter
from minisom import MiniSom

class DataProcessor:
    @staticmethod
    def run_som(input_file, som_output_file, attributes, sigma=0.3, learning_rate=0.5, som_x=5, som_y=5, num_iteration=1000, target_crs=3763):
        # Load and simplify geometries
        gdf = gpd.read_file(input_file)
        gdf = gdf.to_crs(epsg=target_crs)
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.001, preserve_topology=True)

        # Normalize data for SOM
        data = gdf[attributes].to_numpy()
        data_normalized = (data - np.min(data, axis=0)) / (np.ptp(data, axis=0))

        # Initialize and train SOM
        som = MiniSom(som_x, som_y, len(attributes), sigma=sigma, learning_rate=learning_rate)
        som.train_random(data_normalized, num_iteration)

        # Assign clusters using a unique integer for each (x, y) position
        gdf['cluster'] = [x * som_y + y for x, y in (som.winner(d) for d in data_normalized)]

        # Save the GeoDataFrame with cluster assignments to a GeoPackage file
        gdf.to_file(som_output_file, driver='GPKG')

    @staticmethod
    def convert_to_raster(gdf_or_file, raster_output_file, cell_size=0.5, max_cells=10000000):
        if isinstance(gdf_or_file, str):
            gdf = gpd.read_file(gdf_or_file)
        else:
            gdf = gdf_or_file

        bounds = gdf.total_bounds
        x_min, y_min, x_max, y_max = bounds
        print(f"Bounds: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")

        # Calculate initial raster dimensions
        width = int((x_max - x_min) / cell_size)
        height = int((y_max - y_min) / cell_size)

        # Ensure dimensions are not zero
        if width == 0 or height == 0:
            raise ValueError(f"Calculated width or height is zero. Try a smaller cell_size. Current cell_size: {cell_size}")

        # Dynamic adjustment if necessary (optional)
        while width * height > max_cells:
            cell_size *= 2  # Double the cell size to reduce the number of cells
            width = int((x_max - x_min) / cell_size)
            height = int((y_max - y_min) / cell_size)
            if cell_size > max(x_max - x_min, y_max - y_min):
                raise ValueError("Cell size too large, resulting in zero dimensions.")
            print(f"Adjusted cell_size to {cell_size} with dimensions {width} x {height}")

        transform = from_origin(x_min, y_max, cell_size, cell_size)

        raster = rasterize(
            [(geom, value) for geom, value in zip(gdf.geometry, gdf['cluster'])],
            out_shape=(height, width),
            transform=transform,
            fill=0,
            all_touched=True,
            dtype='float32'
        )

        meta = {
            'driver': 'GTiff',
            'dtype': 'float32',
            'nodata': 0,
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
    def generate_heatmap(raster_input_file, heatmap_output_file, sigma=1):
        with rasterio.open(raster_input_file) as src:
            raster = src.read(1)  # Read first band
            meta = src.meta

        heatmap = gaussian_filter(raster, sigma=sigma)
        meta.update(dtype='float32', compress='lzw')

        with rasterio.open(heatmap_output_file, 'w', **meta) as dst:
            dst.write(heatmap, 1)
