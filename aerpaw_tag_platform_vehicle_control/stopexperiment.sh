#!/bin/bash

for scr in $(screen -ls | grep -wv -e 'There' -e 'No' -e 'remoteConsole' -e 'remoteServer' -e 'OEOConsole' -e 'OEOServer' -e 'Socket' -e 'Sockets' | awk '{print $1}')
do
echo "Quitting from $scr"
screen -S $scr -X quit
done
ip link delete ogstun
ip link delete tun_srsue
ip link delete srs_spgw_sgi 
# For channel sounder experiment
rm -f /root/Power /root/Quality
pkill open5g*

# stop zombie processes
kill -9 $(ps aux | awk '/srsenb/ && !/awk/ || /srsue/ && !/awk/{print $2}') >/dev/null 2>&1
