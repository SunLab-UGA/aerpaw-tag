This is the profile used to execute a preplanned mission (predetermined waypoint to be visited in order) with software hooks at each waypoint and between the waypoints.
usage: python guided_mission_from_file.py <*mission_file> --connect <*connection_string>

Creating Mission on QGroundControl:
1) Open QGroundControl on OEO-VM. (cd Downloads; ./QGroundControl.AppImage)
2) Navigate to the area on the map at which the drone mission will occur.
3) Click the mission icon in the top left. (Icon: A and B with path between them)
4) Select the black "Takeoff" icon in the upper left side of the screen.
5) Click on the map where the drone will takeoff.
6) To add waypoints select the "Waypiont" icon and click on the map to set the locations of the waypoints.
***Note: These waypoints must be within the predifined geofence.***
7) After adding the desired waypoints, click the "Return" icon.
8) The altidute on takeoff and at each waypoint can be modified by selecting waypoints (under Mission) on the right side of the screen and adjusting the altidute.
9) Once the mission is to your liking, click the "File" icon close to the top left of the screen.
10) Select "Save As...." to save the mission as a .plan file.
11) Transfer file to E-VM where it can be ran.


