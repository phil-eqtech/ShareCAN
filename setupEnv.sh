#!/bin/bash

tools=/home/flynn/CarHackingTools
d=$(pwd)
sudo $tools/ICSim/setup_vcan.sh

cd $tools/ICSim
$tools/ICSim/icsim vcan0 &
$tools/ICSim/controls vcan0 &
cd $tools/uds-server
$tools/uds-server/uds-server -V WF0WXXGCDW7E79924 vcan0 &
cd $d
