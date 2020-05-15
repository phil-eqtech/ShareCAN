sudo apt-get update
sudo apt-get install mongodb
sudo apt-get install can-utils
sudo apt-get install python3-pip
sudo apt-get install python3-pyqt5

pip3 install pyqt5
pip3 install bcrypt
if [ -e "/usr/bin/raspi-config" ]
then
	pip3 install 'pymongo==3.4.0'
else
	pip3 install pymongo
fi
pip3 install uuid
pip3 install qtawesome
pip3 install python-can
pip3 install bitstring
pip3 install websockets


mongo ShareCAN --eval 'db.devices.remove({"name":"Pican Duo"})'
mongo ShareCAN --eval 'db.devices.update({"name" : "Pican"},{"name" : "Pican", "interfaces" : [ { "type" : "can", "mode" : "builtincan", "label" : "can" } ], "ref" : "mcp251x", "builtin" : true }, true)'
mongo ShareCAN --eval 'db.devices.update({"name" : "Peak"},{"name" : "Peak", "interfaces" : [ { "type" : "can", "mode" : "builtincan", "label" : "can" } ], "ref" : "peak_usb", "builtin" : true }, true)'
mongo ShareCAN --eval 'db.devices.update({"name" : "Virtual CAN"},{"name" : "VCAN", "interfaces" : [ { "type" : "can", "label" : "VCAN", "mode" : "builtincan" } ], "ref" : "vcan", "builtin" : true }, true)'
mongo ShareCAN --eval 'db.devices.update({"name" : "Macchina M2"},{"name" : "Macchina M2", "interfaces" : [ { "type" : "can", "label" : "CAN 1", "mode" : "serial", "id" : "can1" }, { "type" : "lin", "label" : "LIN", "mode" : "serial", "id" : "lin" }, { "type" : "kln", "label" : "K-LINE", "mode" : "serial", "id" : "kline" }, { "type" : "can", "label" : "CAN 2", "mode" : "serial", "id" : "can2" } ], "ref" : "Arduino_LLC_Arduino_Due", "builtin" : false }, true)'
mongo ShareCAN --eval 'db.devices.update({"name" : "Canable"},{"name" : "Canable", "interfaces" : [ { "type" : "can", "label" : "CAN", "mode" : "slcan", "id" : "can0" } ], "ref" : "CANtact_CANtact_dev", "builtin" : false }, true )'
mongo ShareCAN --eval 'db.devices.update({"name" : "Nano-can"},{ "name" : "Nano-can", "interfaces" : [ { "type" : "can", "label" : "CAN", "mode" : "slcan", "id" : "can0" } ], "ref" : "FTDI_FT232R_USB_UART_", "builtin" : false, "baudrate":500000 }, true)'
mongo ShareCAN --eval 'db.analysis.updateMany({},{$set:{"bus.$[].padding":""}})'
