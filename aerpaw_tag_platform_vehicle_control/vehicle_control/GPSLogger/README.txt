gps_logger.py
Ardupilot GPS and Battery Logger

Original code by Mark Funderburk and Byron Qi
Reworked by John Kesler

Requirements can be installed with:
    pip install -r requirements.txt

This script will take periodic snapshots of the autopilot's state and dump it
to a CSV file. The information included is the vehicle's position (lat, lon,
altitude), the vehicle's battery voltage, and the GPS status.

This script will continually run once started, even if it loses connection to
the vehicle. If it loses its connection (heartbeat), it should complain in the
standard output. Also, it won't dump new rows to the log without a connection.

This can be run by using:
    sudo python gps_logger.py --conn <connection>
or, with more params,
    sudo python gps_logger.py --conn <connection> --output <filename> --samplerate <Hz>

There is a bit of help offered by using the --help flag.

Defaults:
    <filename>: gps_data_YYYY-MM-DD_HH:MM:SS.csv
    <Hz>:       1 sample per second

A given row in the file dump looks like:
    index,YYYY-MM-DD HH:MM:SS.000000,longitude,latitude,altitude,voltage,gps status,satellites

Because the script doesn't close automatically or on connection loss, you will
need to kill it manually by either sending it a keyboard interrupt, or with
something like:
    kill $(ps aux | grep gps_logger | awk '/python/ {print $s}')

It's probably wise to pipe the output of this script into a log file to capture
connect/disconnect times.
