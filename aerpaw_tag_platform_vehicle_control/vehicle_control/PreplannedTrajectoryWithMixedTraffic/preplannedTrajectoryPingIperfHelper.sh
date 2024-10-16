#!/bin/bash
#
# This script will start the preplanned trajectory ping iperf sample application
#

if [ -z ${MISSION} ]; then
    echo "\$MISSION must be specified for preplanned trajectory"
    exit 1
fi

#cd $PROFILE_DIR"/vehicle_control/PreplannedTrajectoryWithMixedTraffic"
$AERPAW_PYTHON -u -m aerpawlib \
    --vehicle $VEHICLE_TYPE \
    --script guided_mission_ping_iperf \
    --conn /dev/ttyACM0 \
    --file $MISSION\
    --output $RESULTS_DIR/$LOG_PREFIX\_vehicleOut.txt\
    --destination_ip $DESTINATION_IP
