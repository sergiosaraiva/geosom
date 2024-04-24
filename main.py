import sys
import argparse
from geosom import GeoSom

def split_comma_separated(string):
    return string.split(',')

def main():
    parser = argparse.ArgumentParser(description='Process geospatial data using a Self-Organizing Map (SOM).')
    parser.add_argument('input_file', help='Path to the input GeoPackage containing geospatial data.')
    parser.add_argument('output_base', help='Base path for the output files.')
    parser.add_argument('--attributes', type=split_comma_separated, help='Comma-separated list of attribute names to include in the analysis.')
    parser.add_argument('--sigma', type=float, default=1, help='Sigma for Gaussian filter in heatmap generation.')
    parser.add_argument('--cell_size', type=float, default=0.001, help='Cell size for the output raster.')
    parser.add_argument('--som_x', type=int, default=5, help='Width of the SOM grid.')
    parser.add_argument('--som_y', type=int, default=5, help='Height of the SOM grid.')
    parser.add_argument('--num_iterations', type=int, default=1000, help='Number of iterations for the SOM algorithm.')
    parser.add_argument('--crs', type=int, default=3763, help='EPSG code for the CRS to which to convert the geospatial data.')
    parser.add_argument('--geo_weight', type=float, default=1.0, help='Weight to apply to geographic coordinates during normalization.')
    args = parser.parse_args()

    clusters_output_file = f"{args.output_base}.clusters.gpkg"
    raster_output_file = f"{args.output_base}.raster.tif"
    heatmap_output_file = f"{args.output_base}.heatmap.tif"

    GeoSom.run(args.input_file, clusters_output_file, args.attributes, args.sigma, args.cell_size, args.som_x, args.som_y, args.num_iterations, args.crs, args.geo_weight)
    GeoSom.to_raster(clusters_output_file, raster_output_file, args.cell_size)
    GeoSom.to_heatmap(raster_output_file, heatmap_output_file, args.sigma)

    print(f"Process completed successfully. Output files saved with base name {args.output_base}")

if __name__ == "__main__":
    main()