# this is a class which pulls and stores a derived np array and dict of height map data
# this is done to remove dependencies on gdal and make access more user friendly
# additioanlly, this class can be used to keep track of the takeoff height and location, and then be used to calculate the ground height at any point
# relative to the takeoff height, allowing for "safer" low level flying

import numpy as np
import pickle

class HeightMap:
    def __init__(self, data_pickle_path:str, safety_floor:int=7) -> None:
        '''initialize the height map object'''
        self.takeoff_height = None # must be set before calculating ground height
        self.elevation_offset = None # calculated from takeoff height
        self.takeoff_location = None # lat/long of the takeoff location
        self.safety_floor = safety_floor # used to calculate if a point is safe to fly (note this is not the entire path!, just a point)

        # load the data from the pickle file
        self._load_map_from_pickle(data_pickle_path)

    def _load_map_from_pickle(self, data_pickle_path:str) -> None:
        '''load the height map data from a pickle file
        the file will contain a dict with the following keys:
        - elevation_data: the numpy array of elevation data
        - transform: the geotransform data for the elevation data
        - sat_source: the source of the satellite data (ex SRTMGL1)
        - description: a description of the data
        '''
        # load the data from the pickle file
        with open(data_pickle_path, "rb") as f:
            data = pickle.load(f)
        # unpack the data
        self.elevation_data = data["elevation_data"]
        self.transform = data["transform"]
        self.sat_source = data["sat_source"]
        self.description = data["description"]
        

    def set_takeoff_height(self, lat, lon, takeoff_height=0) -> None:
        '''set the takeoff height for the drone
        use the vehicle's takeoff location and height to calculate the ground height at any point
        normally the takeoff height is 0, but it can be set to a different value if needed
        ex, after taking off from a building, the takeoff height would be the height of the building'''
        self.takeoff_height = takeoff_height
        self.takeoff_location = (lat, lon)
        self.elevation_offset = self.get_elevation(lat, lon) + takeoff_height
        print(f"Takeoff height set to {takeoff_height} meters at {lat}, {lon}.")
        print(f"Elevation offset calculated as {self.elevation_offset} meters.")

    def get_ground_height(self, lat, lon) -> float:
        '''get the ground height at a specific lat/long point
        THIS IS RELATIVE TO THE TAKEOFF HEIGHT, NOT THE ABSOLUTE ELEVATION!
        THIS IS AS ACCURATE AS THE ELEVATION DATA, WHICH IS NOT PERFECT OR HIGH RESOLUTION'''

        # ensure the takeoff height is set
        if self.takeoff_height is None:
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
    
    def set_safety_floor(self, safety_floor:int) -> None:
        '''set the safety floor for the drone
        the safety floor is the minimum height above the ground that the drone should maintain
        this is used to calculate if a point is safe to fly'''
        self.safety_floor = safety_floor
        print(f"Safety floor set to {safety_floor} meters.")
        # warn if the safety floor is negative
        if safety_floor < 0:
            print("Warning: The safety floor is set to a negative value. This could cause the drone to fly below the ground level!")

    def check_height_safe_to_fly(self, lat, lon, alt) -> bool:
        '''check if it is safe to fly at a specific point of lat/long/alt
        this is determined by comparing the ground height + safety floor to the altitude
        if the alt is greater than the safety floor + ground, it is safe to fly'''
        ground_height = self.get_ground_height(lat, lon)
        if ground_height is None:
            print("Ground height could not be calculated. \
                  Set the takeoff height and location before checking if it is safe to fly.\
                  ensure the elevation data is loaded and the lat/long is within the bounds of the data.")
            return None
        if alt >= ground_height + self.safety_floor:
            # print(f"ground height + safety floor: {ground_height + self.safety_floor} meters")
            return True
        else:
            return False
        
    def get_safe_altitude(self, lat, lon) -> float:
        '''get the safe altitude at a specific lat/long point
        the safe altitude is the ground height + safety floor'''
        ground_height = self.get_ground_height(lat, lon)
        if ground_height is None:
            print("Ground height could not be calculated. \
                  Set the takeoff height and location before checking if it is safe to fly.\
                  ensure the elevation data is loaded and the lat/long is within the bounds of the data.")
            return None
        return ground_height + self.safety_floor

    def get_elevation(self, lat, lon, verbose=False) -> float:
        '''get the elevation at a specific lat/long point'''

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


if __name__ == "__main__":
    import pickle
    import argparse
    # create, save, load and access the height map
    PULL_NEW_MAP = False # set true to test pulling a new map
    file_path = "map_data/heightmap_data.pkl"

    # get the elevation at a specific lat/long
    lat =  35.725727
    lon = -78.696716
    
    # create the height map object
    height_map = HeightMap(data_pickle_path=file_path)

    # get the elevation at a specific lat/long
    elevation = height_map.get_elevation(lat, lon, verbose=True)

    # set the takeoff height
    takeoff_height = 0 # zero is typical for drones (ground level) but can be set to a different value (ie building height)
    height_map.set_takeoff_height(lat, lon, takeoff_height=takeoff_height)
    print(f"Takeoff height: {takeoff_height} meters")

    # get the ground height at a specific lat/long
    ground_height = height_map.get_ground_height(lat, lon)
    print(f"Ground height at {lat}, {lon}: {ground_height} meters")

    # print the takeoff location
    print(f"Takeoff location: {height_map.takeoff_location}")
    # print the takeoff height
    print(f"Takeoff height: {height_map.takeoff_height}")
    # print the elevation offset
    print(f"Elevation offset: {height_map.elevation_offset}")
    # print the safety floor
    print(f"Safety floor: {height_map.safety_floor}")

    # give an example of a point that is safe to fly
    safe_lat = lat + 0.0001
    safe_lon = lon + 0.0001
    check_alt = 7
    safe_height = height_map.get_ground_height(safe_lat, safe_lon)
    print(f"Ground height at {safe_lat}, {safe_lon}: {safe_height} meters")
    is_safe = height_map.check_height_safe_to_fly(safe_lat, safe_lon, check_alt)
    print(f"Is it safe to fly at {lat}, {lon}, {check_alt}?: {is_safe}")

    print()
    # give an example of a point that is NOT safe to fly
    unsafe_lat = lat + 0.001
    unsafe_lon = lon + 0.001
    unsafe_height = height_map.get_ground_height(unsafe_lat, unsafe_lon)
    print(f"Ground height at {unsafe_lat}, {unsafe_lon}: {unsafe_height} meters")
    is_safe = height_map.check_height_safe_to_fly(unsafe_lat, unsafe_lon, check_alt)
    print(f"Is it safe to fly at {unsafe_lat}, {unsafe_lon}, {check_alt}?: {is_safe}")

    # get the safe altitude at a specific lat/long
    safe_alt = height_map.get_safe_altitude(unsafe_lat, unsafe_lon)
    print(f"Safe altitude at {unsafe_lat}, {unsafe_lon}: {safe_alt} meters")
    # check if it is safe to fly at a specific point
    is_safe = height_map.check_height_safe_to_fly(lat, lon, safe_alt)
    print(f"Is it safe to fly at {unsafe_lat}, {unsafe_lon}, {safe_alt}?: {is_safe}")