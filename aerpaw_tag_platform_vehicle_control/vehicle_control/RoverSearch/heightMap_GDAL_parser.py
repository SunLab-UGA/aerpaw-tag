# this is a class which stores and provides access to a topological elevation map
# the data itself is pulled from a geotiff file aquired through opentopology, but because the data is unwieldy and requiring gdal to access
# we convert/store it in a more manageable format numpy array with easy access methods and place the data in a pickle file
# this is not ideal, but it is a solid workaround to reduce online dependencies while also providing a more user-friendly interface

import requests
import numpy as np
import pickle

aerpaw_bounds = {
            "north": 35.731096,
            "south": 35.722299,
            "west": -78.701711,
            "east": -78.689380,
            "description": "AERPAW Testbed Area (Lake Wheeler, Raleigh, NC)"
        }
demo_api_key = "demoapikeyot2022"

class HeightMap:
    def __init__(self, api_key=demo_api_key, cardinal_bounds=aerpaw_bounds) -> None:
        '''initialize the height map object'''
        self.api_key = api_key # api key for opentopography, required to pull data, removed when pickling
        self.cardinal_bounds = cardinal_bounds
        #unpacked bounds
        self.north = cardinal_bounds["north"]; self.south = cardinal_bounds["south"]
        self.west = cardinal_bounds["west"]; self.east = cardinal_bounds["east"]
        self.description = cardinal_bounds["description"] if "description" in cardinal_bounds else None
        self.takeoff_height = None # must be set before calculating ground height
        self.elevation_offset = None # calculated from takeoff height
        self.takeoff_location = None # lat/long of the takeoff location

        self.sat_source = "SRTMGL1" # SRTMGL1 is the best available source (30m resolution)
        # also available: SRTMGL3 (90m resolution), and more https://portal.opentopography.org/apidocs/#/Public/getGlobalDem

    
    def pull_geoTif(self, file_path:str, verbose=False) -> bool:
        '''pull a geotiff file from opentopography and save it to the local directory'''
        # keep the path to the saved file
        self.file_path = file_path

        print("Bounding Box:", self.south, self.north, self.west, self.east) if verbose else None
        url = f"https://portal.opentopography.org/API/globaldem?demtype={self.sat_source}&south={self.south:.6f}&north={self.north:.6f}&west={self.west}&east={self.east}&outputFormat=GTiff&API_Key={self.api_key}"
        print("URL:", url) if verbose else None
        try:
            response = requests.get(url)
            print("Response:", response.headers) if verbose else None
            # Check if the request was successful
            if response.status_code != 200:
                print(f"Error: Received response with status code {response.status_code}") if verbose else None
                print(f"{response.text}") if verbose else None
                raise Exception(f"Error: Received response with status code {response.status_code}")
            # save the response to a file
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"GeoTiff file saved to {file_path}") if verbose else None
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def load_map_from_geoTif(self, file_path_override = None, verbose:bool=False) -> None:
        '''load a geotiff file and parse/store the relavant elevation data in a numpy array
        THIS REQUIRES GDAL TO BE INSTALLED, Do not run this function if you do not have GDAL installed
        Just use the access methods to get the data from the pickle file
        NOTE: this function does not have many error checks, it is assumed that the file pull is successful and the file is valid WGS84 etc
        '''
        # we import here to avoid the need for gdal to be installed if the method is not used
        from osgeo import gdal

        # check if the file path is overridden
        file_path = file_path_override if file_path_override else self.file_path

        # Open the file
        ds = gdal.Open(file_path)
        if ds is None:
            print(f"Could not open the geotiff file: {file_path}")
            return None
        
        # get the geotransform information
        transform = ds.GetGeoTransform()
        print("Transform:", transform) if verbose else None
        print("Raster Size:", ds.RasterXSize, ds.RasterYSize) if verbose else None
        self.transform = transform # store the transform for later use

        # calculate the extent of the raster in geographic coordinates (note the multi lines)
        min_lon = transform[0]; max_lon = transform[0] + (ds.RasterXSize * transform[1])
        min_lat = transform[3] + (ds.RasterYSize * transform[5]); max_lat = transform[3]
        print(f"Raster Bounds: {min_lat=}, {max_lat=}, {min_lon=}, {max_lon=}") if verbose else None
        
        proj = ds.GetProjection()
        print("Projection", proj) if verbose else None

        # get the raster band
        band = ds.GetRasterBand(1)

        # get the elevation data
        elevation_data = band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize) # read the entire raster

        # put the data in a numpy array and store it in the object
        self.elevation_data = np.array(elevation_data)
        print("Elevation Data Shape:", self.elevation_data.shape) if verbose else None

    def set_takeoff_height(self, lat, lon, takeoff_height=0) -> None:
        '''set the takeoff height for the drone
        use the vehicle's takeoff location and height to calculate the ground height at any point
        normally the takeoff height is 0, but it can be set to a different value if needed
        ex, after taking off from a building, the takeoff height would be the height of the building'''
        self.takeoff_height = takeoff_height
        self.takeoff_location = (lat, lon)
        self.elevation_offset = self.get_elevation(lat, lon) - takeoff_height

    def get_ground_height(self, lat, lon) -> float:
        '''get the ground height at a specific lat/long point
        THIS IS RELATIVE TO THE TAKEOFF HEIGHT, NOT THE ABSOLUTE ELEVATION!
        THIS IS AS ACCURATE AS THE ELEVATION DATA, WHICH IS NOT PERFECT OR HIGH RESOLUTION'''
        # ensure the map data is loaded
        if not hasattr(self, "elevation_data"):
            print("Elevation data not loaded. Please load the data from a geotiff file first.")
            return None
        # ensure the takeoff height is set
        if not self.takeoff_height:
            print("Takeoff height not set. Please set the takeoff height before calculating ground height.")
            return None

        # calculate the pixel offset for the given lat/long
        x_offset = int((lon - self.transform[0]) / self.transform[1])
        y_offset = int((lat - self.transform[3]) / self.transform[5])

        # check if the lat/long is within the bounds of the raster
        if not (0 <= x_offset < self.elevation_data.shape[1] and 0 <= y_offset < self.elevation_data.shape[0]):
            print("The lat/long is not within the bounds of the raster data.")
            return None

        # read the data from the raster band
        elevation = self.elevation_data[y_offset, x_offset]
        ground_height = elevation - self.elevation_offset

        return ground_height

    def get_elevation(self, lat, lon, verbose=False) -> float:
        '''get the elevation at a specific lat/long point'''
        # ensure the map data is loaded
        if not hasattr(self, "elevation_data"):
            print("Elevation data not loaded. Please load the data from a geotiff file first.")
            return None

        # calculate the pixel offset for the given lat/long
        x_offset = int((lon - self.transform[0]) / self.transform[1])
        y_offset = int((lat - self.transform[3]) / self.transform[5])
        print("Pixel Offset:", x_offset, y_offset) if verbose else None

        # check if the lat/long is within the bounds of the raster
        if not (0 <= x_offset < self.elevation_data.shape[1] and 0 <= y_offset < self.elevation_data.shape[0]):
            print("The lat/long is not within the bounds of the raster data.")
            return None

        # read the data from the raster band
        elevation = self.elevation_data[y_offset, x_offset]
        print(f"Elevation at {lat}, {lon}: {elevation} meters") if verbose else None

        return elevation
    
    def save(self, file_path:str = "heightmap.pkl") -> None:
        '''save the elevation data to a pickle file'''
        with open(file_path, "wb") as f:
            pickle.dump(self, f)
        print(f"HeightMap object saved to {file_path}")

    def save_data(self, file_path:str = "heightmap_data.pkl") -> None:
        '''save the elevation data to a pickle file
        this creates a dict with the elevation data and other relavant information for a smaller support class to load the data'''

        # create the data dict
        data = {
            "elevation_data": self.elevation_data,
            "transform": self.transform,
            "cardinal_bounds": self.cardinal_bounds,
            "sat_source": self.sat_source,
            "description": self.description
        }
        with open(file_path, "wb") as f:
            pickle.dump(data, f)
        print(f"HeightMap data saved to {file_path}")

    @staticmethod # this is a static method because it does not require the object to be first instantiated
    def load(file_path:str = "heightmap.pkl") -> None:
        '''load the object from a pickle file'''
        # try to load the object from the pickle file
        try:
            with open(file_path, "rb") as f:
                obj = pickle.load(f)
            print(f"HeightMap object loaded from {file_path}")
            return obj
        except (FileNotFoundError, EOFError, pickle.PickleError, pickle.UnpicklingError) as e:
            print(f"An error occurred while loading the object: {e}")
            return None
        


if __name__ == "__main__":
    import pickle
    import argparse
    # create, save, load and access the height map
    PULL_NEW_MAP = False # set true to test pulling a new map

    # get the elevation at a specific lat/long
    lat =  35.725727
    lon = -78.696716
    
    # load the api key from args
    parser = argparse.ArgumentParser(description="Test the HeightMap class")
    parser.add_argument("--api_key", help="The api key for OpenTopography", required=False)
    args = parser.parse_args()
    if not args.api_key:
        print("No api key provided. Using the demo key.")
        args.api_key = demo_api_key

    # create the height map object
    height_map = HeightMap(args.api_key)

    # # pull the geotiff file
    file_path = f"map_data/map{height_map.sat_source}.tif"
    height_map.pull_geoTif(file_path, verbose=True) if PULL_NEW_MAP else None

    # load the map from the geotiff file
    height_map.load_map_from_geoTif(file_path, verbose=True)


    # # should return 107 meters, 351.05 feet
    # elevation = height_map.get_elevation(lat, lon, verbose=True)
    # print(f"Elevation at {lat}, {lon}: {elevation} meters, {elevation * 3.28084:.2f} feet")

    # save the height map object
    height_map.save("map_data/heightmap.pkl")
    height_map.save_data("map_data/heightmap_data.pkl")

    # # load the height map object
    # print("Loading the height map object from the pickle file")
    # with open("heightmap.pkl", "rb") as f:
    #     height_map2:HeightMap = pickle.load(f)

    # # get the elevation at the same point
    # print("Getting the elevation from the loaded object")
    # elevation = height_map2.get_elevation(lat, lon, verbose=True)
    # print(f"Elevation at {lat}, {lon}: {elevation} meters, {elevation * 3.28084:.2f} feet")

    # test the static load method
    print("Testing the static load method")
    height_map3:HeightMap = HeightMap.load(file_path="map_data/heightmap.pkl")
    elevation = height_map3.get_elevation(lat, lon)
    print(f"Elevation at {lat}, {lon}: {elevation} meters, {elevation * 3.28084:.2f} feet")

    # plot the elevation data
    import matplotlib.pyplot as plt
    plt.imshow(height_map.elevation_data, cmap='terrain')
    # give the axis labels the lat/long values
    plt.xticks([0, height_map.elevation_data.shape[1]], [height_map.west, height_map.east])
    plt.yticks([0, height_map.elevation_data.shape[0]], [height_map.north, height_map.south])
    plt.colorbar()
    plt.show()