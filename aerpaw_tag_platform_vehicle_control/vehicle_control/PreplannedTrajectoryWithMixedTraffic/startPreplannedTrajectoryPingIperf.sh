#!/bin/bash

export AERPAW_REPO=${AERPAW_REPO:-~/AERPAW-Dev}
export PROFILE_DIR=$AERPAW_REPO"/AHN/E-VM/Profile_software"
export AERPAW_PYTHON=${AERPAW_PYTHON:-python3}
export LAUNCH_MODE=${LAUNCH_MODE:-'EMULATION'}
export EXP_NUMBER=${EXP_NUMBER:-1}

export RESULTS_DIR="${RESULTS_DIR:-/home/pi/Results}"
export TS_FORMAT="${TS_FORMAT:-'[%Y-%m-%d %H:%M:%.S]'}"
export LOG_PREFIX="$(date +%Y-%m-%d_%H:%M:%S)"

export VEHICLE_TYPE="${VEHICLE_TYPE:-drone}"

export DESTINATION_IP="${DESTINATION_IP:-192.168.110.3}"

# Preplanned trajectory ping iperf sample application

# mission should be the aboslute path to a mission .plan file to run
export MISSION="Missions/square200alt305070.plan"

screen -S vehicle -dm \
       bash -c "./preplannedTrajectoryPingIperfHelper.sh \
       | ts $TS_FORMAT \
       | tee $RESULTS_DIR/$LOG_PREFIX\_vehicle_log.txt"
