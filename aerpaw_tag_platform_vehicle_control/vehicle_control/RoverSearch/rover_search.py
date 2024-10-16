# this is a script that controls the UAV to search for a wireless radio tag at a taget location
# the UAV will take off and move to the target location, then lower altitude and linger to wirelessly power the radio tag and collect data
# the UAV will then return to a cruise altitude and return to the launch location and land

import asyncio
import os
# import math
import datetime
# import csv

from typing import List
# from struct import unpack
from argparse import ArgumentParser

from aerpawlib.runner import StateMachine
from aerpawlib.vehicle import Vehicle, Drone
from aerpawlib.runner import state, timed_state, background, at_init
from aerpawlib.util import Coordinate, VectorNED
from aerpawlib.safetyChecker import SafetyCheckerClient

from heightMap_noGDAL import HeightMap

print("All imports were successful")



# TODO:
# template out the basic uav behavior
# add a function which checks the distance to the ground at the current location (default altitude is from takeoff)
# add battery checking

# Constants ----------------------------------------------
ALTITUDE_SEARCH = 30 # in meters (THIS NEEDS TO BE UPDATED TO the lowest resonable altitude the UAV can safely fly)
ALTITUDE_CRUSE = 40 # in meters
TARGET_LOCATION = Coordinate(35.727753, -78.696723, ALTITUDE_CRUSE) # in lat, lon, alt

MISSION_DURATION_LIMIT = 20 # max time (in minutes) the mission can run before returning (this is a minimum return value)
MISSION_BATTERY_LIMIT_PERCENT = 30 # min battery level in percent (this is a minimum return value)
BATTERY_S_SIZE = 6 # number of li cells in series
MISSION_BATTERY_LIMIT_VOLTAGE = 3.5 * BATTERY_S_SIZE # min battery voltage in volts (this is a minimum return value)
# the emulator will not simulate battery voltage, 4.2V is the max voltage for a li cell, 3.5V is a safe minimum for flight return

MISSION_LINGER_TIME = 60*5 # targeted time to linger at a target location (in seconds)

print("Constants initialized")
print(f"Search Altitude: {ALTITUDE_SEARCH}")
print(f"Cruise Altitude: {ALTITUDE_CRUSE}")
print(f"Target Location: {TARGET_LOCATION}")
print(f"Mission Duration Limit: {MISSION_DURATION_LIMIT} minutes")
print(f"Mission Battery Limit: {MISSION_BATTERY_LIMIT_PERCENT}%")
print(f"Mission Battery Voltage Limit: {MISSION_BATTERY_LIMIT_VOLTAGE}V")
print(f"Mission Linger Time: {MISSION_LINGER_TIME} seconds")


# Predefined Waypoint Construction ----------------------------------
# This is a list of waypoints that the UAV will fly to in order to search
# in this case we just use the target location as the only waypoint (but we could add more)
waypoints:list = [TARGET_LOCATION]

class RoverSearch(StateMachine):
    """State machine for a UAV searching for a rover using radio power measurements"""
    print("RoverSearch StateMachine initialized")

    def initialize_args(self, extra_args: List[str]):
        """Parse arguments passed to vehicle script"""
        parser = ArgumentParser()
        parser.add_argument("--safety_checker_ip", help="ip of the safety checker server")
        parser.add_argument("--safety_checker_port", help="port of the safety checker server")
        args = parser.parse_args(args=extra_args)
        self.safety_checker = SafetyCheckerClient(args.safety_checker_ip, args.safety_checker_port)

    def battery_low(self, vehicle: Drone, 
                    low_percent=MISSION_BATTERY_LIMIT_PERCENT, 
                    low_voltage=MISSION_BATTERY_LIMIT_VOLTAGE):
        """Check the battery level of the vehicle"""
        if vehicle.battery.level <= low_percent:
            print("Battery percentage is low, returning to launch")
            return True
        if vehicle.battery.voltage <= low_voltage:
            print("Battery voltage is low, returning to launch")
            return True
        return False
    
    def mission_timer_ended(self):
        """Check if the mission has exceeded the time limit"""
        if (datetime.datetime.now() - self.TIME_MISSION_START).total_seconds() > MISSION_DURATION_LIMIT*60:
            # print("Mission duration limit reached")
            return True
        return False
    
    def print_battery_and_mission_time(self, vehicle: Drone):
        """Print the battery level and mission time"""
        print(
            f"Current Battery Level: {vehicle.battery}%" ,
            f"Current Mission Duration: {(datetime.datetime.now() - self.TIME_MISSION_START).total_seconds()} seconds"
        )
    
    # # ============================================================== BACKGROUND TASKS
    # @background
    # async def check_end(self, vehicle: Drone):
    #     """Check if the mission should be ended due to battery or time"""
    #     if self.mission_timer_ended():
    #         print("watchdog: Mission duration limit reached") if not self.mission_end_watchdog else None
    #         self.print_battery_and_mission_time(vehicle) if not self.mission_end_watchdog else None
    #         self.mission_end_watchdog = True # set the mission end flag
    #     if self.battery_low(vehicle, MISSION_BATTERY_LIMIT_PERCENT, MISSION_BATTERY_LIMIT_VOLTAGE):
    #         print("watchdog: Battery is low, returning to launch") if not self.mission_end_watchdog else None
    #         self.print_battery_and_mission_time(vehicle) if not self.mission_end_watchdog else None
    #         self.mission_end_watchdog = True # set the mission end flag
    #     if datetime.datetime.now().second % 15 == 0: # print watchdog status every 15 seconds
    #         print("watchdog: Mission is still running")
    #     await asyncio.sleep(1)

    # ============================================================== AT INITIALIZATION
    @at_init
    async def at_init(self, vehicle: Vehicle):
        """Load the heightmap and wait for arming"""
        print(f"rover_search PID is: {os.getpid()}")
        print(f"Current working directory: {os.getcwd()}")
        self.heightmap:HeightMap = HeightMap("map_data/heightmap_data.pkl")
        print("Heightmap loaded")

        # self.mission_end_watchdog = False # if true, the mission should end

        print("Finished initialization")
        print()
        self.init_finished = True

    # ============================================================== START
    @state(name="start", first=True)
    async def start(self, vehicle: Drone):
        # record the start time of the search
        self.TIME_MISSION_START = datetime.datetime.now()
        self.START_COORDINATES = vehicle.position
        print(f"Starting mission coordinates: {self.START_COORDINATES}")
        print(f"Starting mission at: {self.TIME_MISSION_START}")
        print(f"Starting battery level: {vehicle.battery}%")
        if not self.init_finished:
            print("Initialization failed, ending mission")
            while True:
                await asyncio.sleep(0.1)
                
        # set the heightmap offset for the vehicle
        self.heightmap.set_takeoff_height(vehicle.position.lat, vehicle.position.lon, takeoff_height=0) # default zero altitude
        print(f"Heightmap offset set to {self.heightmap.elevation_offset}")
        print(f"Ground height estimate: {self.heightmap.get_ground_height(vehicle.position.lat, vehicle.position.lon)}")

        print("Waiting for arming, then taking off")
        await vehicle.takeoff(ALTITUDE_CRUSE)
        print(f"Took off and at cruise altitude: {vehicle.position.alt}")
        return "go_to_next_waypoint"

    # ============================================================== GO TO NEXT WAYPOINT
    @state(name="go_to_next_waypoint")
    async def go_to_next_waypoint(self, vehicle: Vehicle):
        '''Pops the next waypoint from the list and moves to it'''
        # check if the mission should end ---
        if self.mission_timer_ended() or self.battery_low(vehicle):
            print("Mission end triggered")
            return "end"

        print("Going to next waypoint")

        if len(waypoints) > 0:
            waypoint:Coordinate = waypoints.pop(0)
            print(f"Next waypoint: {waypoint}")
        else:
            print("No more waypoints, ending mission")
            return "end"

        # validate the target location
        valid_target, msg = self.safety_checker.validateWaypointCommand(vehicle.position, waypoint)
        if not valid_target:
            print("Can't go there:")
            print(msg)
            return "end" # end the mission if the target location is invalid

        print(f"Moving to target location: {waypoint}")
        distance = vehicle.position.distance(waypoint)
        print(f"Distance to target: {distance}")
       
        moving_task = asyncio.ensure_future(
            vehicle.goto_coordinates(waypoint)
        )

        # wait until the vehicle is done moving
        while not moving_task.done():
            await asyncio.sleep(0.1)

        await moving_task
        print("Arrived at target location")
        return "take_measurement"

    # ============================================================== TAKE MEASUREMENT
    @state(name="take_measurement") # we don't use a timed state because we don't know how long the task will take
    async def take_measurement(self, vehicle: Drone):
        '''Check the ground height, Lower the UAV altitude
        Linger to take a measurement
        Return to cruise altitude'''
        print("Moving to take measurement")

        # check the ground height
        ground_height = self.heightmap.get_ground_height(vehicle.position.lat, vehicle.position.lon)
        elevation = self.heightmap.get_elevation(vehicle.position.lat, vehicle.position.lon)
        print(f"Elevation @ pos: {elevation}")
        # print(f"Ground height offset: {self.heightmap.elevation_offset}")
        print(f"Ground height estimate @ pos: {ground_height}")
        min_safe_altitude = self.heightmap.get_safe_altitude(vehicle.position.lat, vehicle.position.lon)
        print(f"Minimum safe altitude ({self.heightmap.safety_floor} above ground): {min_safe_altitude}")

        safe_altitude = self.heightmap.get_safe_altitude(vehicle.position.lat, vehicle.position.lon)
        print(f"Safe altitude: {safe_altitude}")

        # check if the target altitude is safe
        is_safe = self.heightmap.check_height_safe_to_fly(vehicle.position.lat, vehicle.position.lon, ALTITUDE_SEARCH)
        if not is_safe:
            print(f"The target altitude ({ALTITUDE_SEARCH}) is not safe to fly, ending mission")
            return "end"
        else:
            print(f"The target altitude ({ALTITUDE_SEARCH}) is safe to fly")
        
        # slowly lower the UAV to the target altitude
        print(f"Lowering altitude to {ALTITUDE_SEARCH}")
        moving_task = asyncio.ensure_future(
            vehicle.goto_coordinates(Coordinate(vehicle.position.lat, vehicle.position.lon, ALTITUDE_SEARCH)))
        while not moving_task.done():
            await asyncio.sleep(0.1)
        await moving_task
        print("Arrived at target altitude")

        # linger at the target altitude to take a measurement
        print("Taking measurements")
        print(f"Current Battery Level: {vehicle.battery}%")
        print(f"Current Mission Duration: {(datetime.datetime.now() - self.TIME_MISSION_START).total_seconds()} seconds")
        print(f'attempting to linger for {MISSION_LINGER_TIME} seconds with updates every 10 seconds')
        # ----------------------------------------------------------------------------------------------------------- LINGER
        #TODO: how long should we linger? let's do some calculations and then update this?
        for i in range(1, MISSION_LINGER_TIME, 1):
            # check if the mission should end
            if self.mission_timer_ended() or self.battery_low(vehicle):
                print("mission end triggered")
                return "end"
            if i % 10 == 0: # print every 10 seconds
                time_elapsed = (datetime.datetime.now() - self.TIME_MISSION_START).total_seconds()
                print(f"Measurement {i} of {MISSION_LINGER_TIME}, Battery Level: {vehicle.battery.level}% @ {vehicle.battery.voltage}V, Mission Duration: {time_elapsed:.2f} seconds")
            await asyncio.sleep(1)
        print("Done taking measurements")
        # ----------------------------------------------------------------------------------------------------------- END LINGER
        # return to the cruise altitude
        print(f"Returning to cruise altitude ({ALTITUDE_CRUSE})")
        moving_task = asyncio.ensure_future(
            vehicle.goto_coordinates(Coordinate(vehicle.position.lat, vehicle.position.lon, ALTITUDE_CRUSE)))
        while not moving_task.done():
            await asyncio.sleep(0.1)
        await moving_task
        print("Arrived at cruise altitude")

        return "go_to_next_waypoint"

    # ============================================================== END
    @state(name="end")
    async def end(self, vehicle: Drone):
        '''From ANY state, this state will safely return to cruise altitude and then return to launch and land'''
        print("Ending mission")
        self.print_battery_and_mission_time(vehicle)
        # return to cruise altitude
        safe_cruse_alt = Coordinate(vehicle.position.lat, vehicle.position.lon, ALTITUDE_CRUSE)
        print(f"Returning to cruise altitude ({ALTITUDE_CRUSE})")
        moving_task = asyncio.ensure_future(vehicle.goto_coordinates(safe_cruse_alt))
        while not moving_task.done():
            await asyncio.sleep(0.1)
        await moving_task
        print("Arrived at cruise altitude")
        # return to launch and land
        return_coordinates = Coordinate(self.START_COORDINATES.lat, self.START_COORDINATES.lon, ALTITUDE_CRUSE)
        print(f"Returning to launch: {return_coordinates}")
        await vehicle.goto_coordinates(return_coordinates) 
        print("Landing")
        await vehicle.land()
        print("Landed")
        self.print_battery_and_mission_time(vehicle)
        print("Mission complete :D")
