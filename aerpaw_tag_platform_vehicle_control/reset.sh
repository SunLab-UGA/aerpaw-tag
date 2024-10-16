#!/bin/bash

source /root/.ap-set-experiment-env.sh 

#python3 /root/AERPAW-Dev/DCS/Emulation/RemoteControl/reset.py --ips '192.168.153.192,192.168.153.1,192.168.153.2'
#python3 /root/AERPAW-Dev/DCS/Emulation/RemoteControl/reset.py --ips "$AP_EXPENV_CHEMVM_XE,$AP_EXPENV_CVM_1_XE,$AP_EXPENV_CVM_2_XE"
N="$(($AP_EXPENV_NUM_NODES + 0))"
var1=""
for ((i = 1 ; i <= $N ; i++)); do
  var2="AP_EXPENV_CVM_${i}_XE"
  if [[ $var1 == "" ]]; then
     var1=${!var2}
  else
     var1="${var1},${!var2}"
  fi
done

var1="${var1},${AP_EXPENV_CHEMVM_XE}"

python3 /root/AERPAW-Dev/DCS/Emulation/RemoteControl/reset.py --ips "$var1"
