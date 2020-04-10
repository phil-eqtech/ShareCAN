sudo apt-get install mongodb
sudo apt-get install can-utils
sudo apt-get install pip3

pip3 install pyqt5
pip3 install bcrypt
pip3 install pymongo
pip3 install uuid
pip3 install qtawesome


mongo ShareCAN --eval 'db.devices.update({"name" : "Pican Duo"},{"name" : "Pican Duo", "interfaces" : [ { "type" : "can", "mode" : "slcan", "label" : "CAN A" }, { "type" : "can", "mode" : "slcan", "label" : "CAN B" } ], "ref" : "SPI", "builtin" : true }, true)'
mongo ShareCAN --eval 'db.devices.update({"name" : "Pican"},{"name" : "Pican", "interfaces" : [ { "type" : "can", "mode" : "slcan", "label" : "CAN" } ], "ref" : "SPI 2", "builtin" : false }, true)'
mongo ShareCAN --eval 'db.devices.update({"name" : "Virtual CAN"},{"name" : "Virtual CAN", "interfaces" : [ { "type" : "can", "label" : "VCAN", "mode" : "slcan", "id" : "vcan0" } ], "ref" : "VCAN-DEMO", "builtin" : true }, true)'
mongo ShareCAN --eval 'db.devices.update({"name" : "Macchina M2"},{"name" : "Macchina M2", "interfaces" : [ { "type" : "can", "label" : "CAN 1", "mode" : "serial", "id" : "can1" }, { "type" : "lin", "label" : "LIN", "mode" : "serial", "id" : "lin" }, { "type" : "kln", "label" : "K-LINE", "mode" : "serial", "id" : "kline" }, { "type" : "can", "label" : "CAN 2", "mode" : "serial", "id" : "can2" } ], "ref" : "Arduino_LLC_Arduino_Due", "builtin" : false }, true)'
mongo ShareCAN --eval 'db.devices.update({"name" : "Canable"},{"name" : "Canable", "interfaces" : [ { "type" : "can", "label" : "CAN", "mode" : "slcan", "id" : "can0" } ], "ref" : "CANtact_CANtact_dev", "builtin" : false }, true )'
