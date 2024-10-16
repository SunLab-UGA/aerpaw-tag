#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
usage: python guided_mission_from_file.py <*mission_file> --connect <*connection_string>
This script reads drone waypoints from a .plan file in JSON format. Trough dronekit commands
the drone will navigate through the waypoints and then return to launch.
"""

from __future__ import print_function

import json
import time
import math
import sys
from pymavlink import mavutil
from dronekit import connect, VehicleMode, LocationGlobalRelative

# mavlink command number for takeoff
TAKEOFF = 22
# mavlink command number for return to launch
RETURN_TO_LAUNCH = 20
# Portion of TARGET_ALTITUDE at which we will break from takeoff loop
ALTITUDE_REACH_THRESHOLD = 0.95
# Maximum distance (in meters) from waypoint at which drone has "reached" waypoint
# This is used instead of 0 since distanceToWaypoint funciton is not 100% accurate
WAYPOINT_LIMIT = 2
# Parameters to keep track of if joystick to arm has returned to center
rcin_4_center_once = False
rcin_4_center_twice = False


def readmission(filePath):
    """
    Reads mission from file located at filePath
    """
    # array of waypoints for mission
    missionWaypoints = []
    with open(filePath) as f:
        data = json.load(f)
    if (data['fileType'] != 'Plan'):
        raise Exception('Wrong File Type. Please use a .plan file.')
    for i in range(len(data['mission']['items'])):
        # mav command number
        command = data['mission']['items'][i]['command']
        # x,y,z coordinates of waypoint
        x = data['mission']['items'][i]['params'][4]
        y = data['mission']['items'][i]['params'][5]
        z = data['mission']['items'][i]['params'][6]
        waypointID = data['mission']['items'][i]['doJumpId']
        # create new waypoint and appends to missionWaypoints
        waypoint = [command, x, y, z, waypointID]
        missionWaypoints.append(waypoint)
    x_home = data['mission']['plannedHomePosition'][0]
    y_home = data['mission']['plannedHomePosition'][1]
    z_home = missionWaypoints[0][3]
    waypoint_home = [16, x_home, y_home, z_home, len(missionWaypoints) + 1]
    missionWaypoints.append(waypoint_home)
    return missionWaypoints

def get_distance_metres(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.
    This method is an approximation, and will not be accurate over large distances and close to the 
    earth's poles. It comes from the ArduPilot test code: 
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    dalt = aLocation2.alt - aLocation1.alt
    latLonDistance = math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5
    return math.sqrt(latLonDistance*latLonDistance + dalt*dalt)

def distanceToWaypoint(coordinates):
    """
    Returns distance between vehicle and specified coordinates
    """
    distance = get_distance_metres(vehicle.location.global_relative_frame, coordinates)
    return distance


def doAtWaypoint(waypointID):
    """
    Prints waypointId. Called when vehicle reached a waypoint.
    """
    print('Reached Waypoint: ' + str(waypointID))
    time.sleep(5)

def doInTransit(nextWaypointID, progress):
    """
    Prints waypointID of next waypoint. Called periodically when travelling to waypoint.
    """
    print(nextWaypointID)
    print(progress)

def abortFunction():
    """
    Abort function called when vehicle mode changes.
    """
    print('Aborted')

def condition_yaw(heading, relative=False):
    """
    Send MAV_CMD_CONDITION_YAW message to point vehicle at a specified heading (in degrees).

    This method sets an absolute heading by default, but you can set the `relative` parameter
    to `True` to set yaw relative to the current yaw heading.

    By default the yaw of the vehicle will follow the direction of travel. After setting 
    the yaw using this function there is no way to return to the default yaw "follow direction 
    of travel" behaviour (https://github.com/diydrones/ardupilot/issues/2427)

    For more information see: 
    http://copter.ardupilot.com/wiki/common-mavlink-mission-command-messages-mav_cmd/#mav_cmd_condition_yaw
    """
    if relative:
        is_relative = 1 #yaw relative to direction of travel
    else:
        is_relative = 0 #yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
        0, #confirmation
        heading,    # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        1,          # param 3, direction -1 ccw, 1 cw
        is_relative, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)

    # delay to wait until yaw of copter is at desired yaw angle
    time.sleep(3)

# Set up option parsing to get connection string and mission plan file
import argparse
parser = argparse.ArgumentParser(description='Commands vehicle using vehicle.simple_goto.')
parser.add_argument("file", help="Mission plan file path.")
parser.add_argument('--connect', help="Vehicle connection target string.")
args = parser.parse_args()

# read mission from file and store array of mission waypoints
missionWaypoints = readmission(args.file)

# aquire connection_string
connection_string = args.connect

# Exit if no connection string specified
if not connection_string:
    sys.exit('Please specify connection string')

# Connect to the Vehicle
print('Connecting to vehicle on: %s' % connection_string)
vehicle = connect(connection_string, wait_ready=True)

print('Succesfully connected to vehicle')

"""
Listens for RC_CHANNELS mavlink messages with the goal of determining when the RCIN_4 joystick
has returned to center for two consecutive seconds.
"""
@vehicle.on_message('RC_CHANNELS')
def rc_listener(self, name, message):
    global rcin_4_center
    rcin_4_center = (message.chan4_raw < 1550 and message.chan4_raw > 1450)

if vehicle.version.vehicle_type == mavutil.mavlink.MAV_TYPE_HEXAROTOR:
    vehicle.mode = VehicleMode("ALT_HOLD")

# If rover, set all target altitudes to 0.
if vehicle.version.vehicle_type == mavutil.mavlink.MAV_TYPE_GROUND_ROVER:
	for waypoint in missionWaypoints:
		waypoint[3] = 0

# Wait for pilot before proceeding
print('Waiting for safety pilot to arm...')

# Wait until safety pilot arms drone
while not vehicle.armed:
    time.sleep(1)

vehicle.mode = VehicleMode("GUIDED")

if vehicle.version.vehicle_type == mavutil.mavlink.MAV_TYPE_HEXAROTOR:

    rcin_4_center_once = False
    rcin_4_center_twice = False
    while not rcin_4_center_twice:
        if rcin_4_center:
            if rcin_4_center_once:
                rcin_4_center_twice = True
            else:
                rcin_4_center_once = True
        else:
            rcin_4_center_once = False
        time.sleep(1)

    # Takeoff to altitude specified in mission file
    print("Taking off!")
    targetAltitude = missionWaypoints[0][3]
    vehicle.simple_takeoff(targetAltitude)  # Take off to target altitude

    while True:
        # Call doInTransit periodically when taking off
        doInTransit(1, vehicle.location.global_relative_frame.alt / targetAltitude)
         # Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt >= targetAltitude * ALTITUDE_REACH_THRESHOLD:
            break
        time.sleep(1)

    # yaw north
    condition_yaw(0)

# Loop through waypoints in list
for waypoint in missionWaypoints:
    # Ignore takeoff command
    if waypoint[0] == TAKEOFF:
        continue
    # Break out of loop when return to launch command encountered
    if waypoint[0] == RETURN_TO_LAUNCH:
        break
    # Get coordinates of next waypoint and start proceeding towards waypoint
    coordinates = LocationGlobalRelative(waypoint[1], waypoint[2], waypoint[3])
    totalDistance = distanceToWaypoint(coordinates)
    vehicle.simple_goto(coordinates)
    # Loop until very close to waypoint
    while(distanceToWaypoint(coordinates) > WAYPOINT_LIMIT):
        # Call abortFunction() if vehicle mode changes from GUIDED
        if vehicle.mode != VehicleMode("GUIDED"):
            abortFunction()
        # Calculate progress to waypoint and call doInTransit
        progress = (totalDistance - distanceToWaypoint(coordinates)) / totalDistance
        doInTransit(waypoint[4], progress)
        time.sleep(2)
    # Call doAtWaypoint after reaching waypoing
    doAtWaypoint(waypoint[4])

# Get coordinates to home location and start proceeding towards it
coordinates = LocationGlobalRelative(vehicle.home_location.lat, vehicle.home_location.lon, vehicle.location.global_relative_frame.alt)  
totalDistance = distanceToWaypoint(coordinates)
vehicle.simple_goto(coordinates)
# Loop until reached home
while(distanceToWaypoint(coordinates) > WAYPOINT_LIMIT):
    # Call abortFunction() if vehicle mode changes from GUIDED
    if vehicle.mode != VehicleMode("GUIDED"):
        abortFunction()
    # Calculate progress to waypoint and call doInTransit
    progress = (totalDistance - distanceToWaypoint(coordinates)) / totalDistance
    doInTransit("Home", progress)
    time.sleep(2)

if vehicle.version.vehicle_type == mavutil.mavlink.MAV_TYPE_HEXAROTOR:
    # Land Copter
    vehicle.mode = VehicleMode("LAND")

if vehicle.version.vehicle_type == mavutil.mavlink.MAV_TYPE_GROUND_ROVER:
    # disarm Rover
    vehicle.armed = False

# Stay connected to vehicle until landed and disarmed
while vehicle.armed:
    time.sleep(1)

print("Done!")

# Close vehicle object before exiting script
vehicle.close()
