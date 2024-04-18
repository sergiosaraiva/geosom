from sklearn.preprocessing import MinMaxScaler
import rasterio
from rasterio.transform import from_origin
from rasterio.features import rasterize
from scipy.ndimage import gaussian_filter
import geopandas as gpd
import numpy as np
from minisom import MiniSom

class DataProcessor:
    @staticmethod
    def run_som(input_file, som_output_file, attributes, sigma, learning_rate, som_x, som_y, num_iterations, target_crs, geo_weight):
        gdf = gpd.read_file(input_file)
        gdf = gdf.to_crs(epsg=target_crs)

        # Calculate centroids and extract them as separate float columns
        gdf['centroid_lon'] = gdf.geometry.centroid.x
        gdf['centroid_lat'] = gdf.geometry.centroid.y

        # Append geographic coordinates to attributes for normalization and SOM processing
        attributes = attributes + ['centroid_lon', 'centroid_lat']
        data = gdf[attributes].to_numpy()

        # Normalize the data
        scaler = MinMaxScaler()
        data = scaler.fit_transform(data)
        data[:, -2:] *= geo_weight  # Apply geo_weight to longitude and latitude

        # Initialize and train SOM
        som = MiniSom(som_x, som_y, len(attributes), sigma=sigma, learning_rate=learning_rate)
        som.train_random(data, num_iterations)

        # Decompose tuple and store as separate columns for grid coordinates
        winners = np.array([som.winner(d) for d in data])
        gdf['cluster_x'] = winners[:, 0].astype(int)
        gdf['cluster_y'] = winners[:, 1].astype(int)
        gdf['cluster'] = gdf['cluster_x'] * som_y + gdf['cluster_y']  # Create a single numeric cluster ID

        # Remove centroid columns if no longer needed
        gdf.drop(columns=['centroid_lon', 'centroid_lat'], inplace=True)

        # Save to file
        gdf.to_file(som_output_file, driver='GPKG')

    @staticmethod
    def convert_to_raster(gdf_or_file, raster_output_file, cell_size=0.5, max_cells=10000000):
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
