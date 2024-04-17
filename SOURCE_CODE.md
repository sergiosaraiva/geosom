## **Exploring the Code Behind Clustering Lisbon's Geographic Data with SOMs**

### **Introduction**

Self-Organizing Maps (SOMs) are a potent tool in machine learning for managing and visualizing complex data. This article details the source code used in a Python-based project aimed at clustering the Lisbon Metropolitan Area's population data. This example demonstrates how SOMs can be practically applied to understand urban demographics.

### **Overview of the Project Structure**

The project is structured into two main Python scripts:

- `main.py`: This script handles the user interface, command-line arguments, and orchestrates the flow of data through various processing stages.
- `data_processor.py`: This script contains all the logic for data handling, including loading data, running the SOM, converting the results to a raster format, and generating heatmaps.

### **Breakdown of the `main.py` Script**

#### **Import Statements and Argument Parsing**

```python
import sys
import argparse
from data_processor import DataProcessor

def main():
    parser = argparse.ArgumentParser(description='Process geospatial data using a Self-Organizing Map (SOM).')
    # Various argument definitions
    args = parser.parse_args()

    # Calls to data processing functions
```

- **Purpose**: `main.py` starts by importing necessary libraries and defining a function `main()` that uses `argparse` to handle command-line arguments.
- **Functionality**: The script configures what inputs it requires, such as paths to data files, configuration for the SOM, and where to save outputs.

#### **Data Processing Calls**

```python
    DataProcessor.run_som(args.input_file, clusters_output_file, args.attributes, args.sigma, args.cell_size, args.som_x, args.som_y, args.num_iterations, args.crs)
    DataProcessor.convert_to_raster(clusters_output_file, raster_output_file, args.cell_size)
    DataProcessor.generate_heatmap(raster_output_file, heatmap_output_file, args.sigma)
```

- **Execution**: After parsing input parameters, `main.py` calls methods from `data_processor.py` to execute data loading, SOM processing, rasterization, and heatmap generation.

### **Details of the `data_processor.py` Script**

The `DataProcessor` class is designed to function as a utility class that provides static methods for handling different stages of data processing. This includes reading and preparing geospatial data, executing the SOM algorithm, transforming the resulting clusters into a raster format, and generating heatmaps from these rasters.

### Breakdown of Methods

#### 1. **run_som**
This method is the core of the geographic data analysis, applying the Self-Organizing Map to the input data to identify clusters based on various attributes.

```python
@staticmethod
def run_som(input_file, som_output_file, attributes, sigma, learning_rate, som_x, som_y, num_iterations, target_crs):
    import geopandas as gpd
    import numpy as np
    from minisom import MiniSom

    # Load data
    gdf = gpd.read_file(input_file)
    gdf = gdf.to_crs(epsg=target_crs)  # Convert CRS

    # Select attributes and normalize data
    data = gdf[attributes].to_numpy()
    data_normalized = (data - np.min(data, axis=0)) / (np.ptp(data, axis=0))

    # Initialize SOM
    som = MiniSom(som_x, som_y, len(attributes), sigma=sigma, learning_rate=learning_rate)
    som.train_random(data_normalized, num_iterations)

    # Tagging data with clusters
    gdf['cluster'] = [som.winner(d) for d in data_normalized]
    gdf.to_file(som_output_file, driver='GPKG')
```

- **Functionality**: The method starts by loading geospatial data using GeoPandas, then it normalizes the selected attributes to ensure effective learning. It initializes a SOM with the specified parameters, trains it with the normalized data, and assigns each data point to a cluster. Finally, it saves the clustered data back to a GeoPackage file.

#### 2. **convert_to_raster**
This method converts the clustered geospatial data into a raster format, which is useful for visual representation and further analysis.

```python
@staticmethod
def convert_to_raster(gdf_or_file, raster_output_file, cell_size):
    import geopandas as gpd
    import rasterio
    from rasterio.features import rasterize
    from rasterio.transform import from_origin

    # Load GeoDataFrame if a file path is provided
    if isinstance(gdf_or_file, str):
        gdf = gpd.read_file(gdf_or_file)
    else:
        gdf = gdf_or_file

    # Setup raster parameters
    bounds = gdf.total_bounds
    transform = from_origin(bounds[0], bounds[3], cell_size, cell_size)
    raster_shape = (int((bounds[3] - bounds[1]) / cell_size), int((bounds[2] - bounds[0]) / cell_size))

    # Rasterization
    raster = rasterize(
        [(shape, value) for shape, value in zip(gdf.geometry, gdf['cluster'])],
        out_shape=raster_shape,
        transform=transform,
        fill=0,
        all_touched=True,
        dtype='int32'
    )

    # Saving raster
    with rasterio.open(raster_output_file, 'w', driver='GTiff', height=raster_shape[0], width=raster_shape[1], count=1, dtype='int32', crs=gdf.crs, transform=transform) as dst:
        dst.write(raster, 1)
```

- **Functionality**: It checks whether the input is a file path or a GeoDataFrame, configures the raster transformation, and performs the rasterization using `rasterio`. It defines the spatial resolution and dimensions of the raster based on the `cell_size` and geographical bounds.

#### 3. **generate_heatmap**
This method applies a Gaussian filter to the raster data to produce a heatmap, which can be used to visually analyze the density and distribution of the clusters.

```python
@staticmethod
def generate_heatmap(raster_input_file, heatmap_output_file, sigma):
    import rasterio
    from scipy.ndimage import gaussian_filter

    # Load raster
    with rasterio.open(raster_input_file) as src:
        raster = src.read(1)  # read the first band

    # Apply Gaussian filter
    heatmap = gaussian_filter(raster, sigma=sigma)

    # Save the heatmap
    with rasterio.open(heatmap_output_file,

 'w', driver='GTiff', height=src.height, width=src.width, count=1, dtype='float32', crs=src.crs, transform=src.transform) as dst:
        dst.write(heatmap.astype('float32'), 1)
```

- **Functionality**: The method loads a raster file, applies a Gaussian blur to smooth it, and saves the result as a new raster. This is useful for creating visual representations that highlight larger trends in the data rather than individual data points.

### Conclusion

The `DataProcessor` class efficiently encapsulates all necessary functionalities for processing geographic data through SOMs, from data preparation to advanced visual output. Each method is designed to be modular, allowing them to be reused or adapted for different datasets or different types of analyses. This design not only streamlines the project workflow but also enhances the usability and extendibility of the code.
