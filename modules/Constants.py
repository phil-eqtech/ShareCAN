import logging

class SESSION_MODE:
  RECORDING = 2
  LIVE = 1
  IDLE = 0
  REPLAYING = -1
  FORENSIC = -2

class REPLAY:
  SESSION = 0
  SELECTION = 1
  COMMAND = 2
  UPDATE_SESSION = 2
  FINISH = 1
  SUPPORTED_BUS_TYPE = ['can']
  LABEL = ["SESSION","SELECTION","COMMAND"]

class SLICE:
  NEXT = 1
  PREVIOUS = -1
  SELF = 0

class SIGNALS:
  SRC = {"ANALYSIS":1, "ENGINE_CODE":2, "MODEL":3, "MANUFACTURER":4}
  DEFAULT = 2

class DISPLAY:
  DURATION = {"1 sec":1, "5 sec":5, "30 sec":30, "1 min": 60}

LOG_LEVEL = logging.DEBUG

CSS_FILE = "./static/ui.css"

WIRE_COLOR = ["BK","BN","BU","GN","GY","OG","RD","VT","WH","YE"]

OBD_PORTS = []
for i in range(0, 16):
  OBD_PORTS.append(i+1)

PRIVACY_MODE = {"private":"PRIVATE","restricted":"RESTRICTED","public":"PUBLIC"}
PRIVACY_ICON = {"private":"fa5s.user","restricted":"fa5s.user-friends","public":"mdi.earth"}

SUPPORTED_VEHICLE = {"car":"CAR","bike":"MOTORBIKE","truck":"TRUCK","device":"DEVICE"}
SUPPORTED_VEHICLE_ICON = {"car":"fa.car","bike":"fa.motorcycle","truck":"mdi.truck","device":"fa.microchip"}

SUPPORTED_ENGINE = {"gasol":"GASOLINE","diesel":"DIESEL","electric":"ELECTRIC","hybrid":"HYBRID","other":"OTHER"}

SUPPORTED_BUS_TYPE = {"can":"CAN", "kln":"K-LINE", "lin":"LIN"}
SUPPORTED_SPEED = {"can":[1000,800,500,250,125,100,50,25,10]}
SUPPORTED_SPEED_UNIT = {"can":"Kbps"}

SPECIAL_MANUFACTURER = ["TEST"]

# If session frame above limit, slice inserts
FRAME_RECORD_GROUP_LIMIT = 8000

# Frame window params
TABLE_REFRESH_RATE = 0.2
FRAME_CHANGE_TIME = 1

FRAME_WINDOW_MODEL = [{'label':'ID', 'field':'id', 'w':5},{'label':'BUS', 'field':'busName','w':5},
                      {'label':'ECU', 'field':'ecu','w':5}, {'label':'DATA', 'field':'msg','w':180},
                      {'label':'ASCII', 'field':'ascii','w':5}, {'label':'COUNT', 'field':'count','w':5},
                      {'label':'TIME', 'field':'ts','w':5}, {'label':'SIGNAL', 'field':'signal'}]

BIT_WINDOW_MODEL = [{'label':'BIT_8', 'field':'b8','w':5}, {'label':'BIT_7', 'field':'b7','w':5},
                    {'label':'BIT_6', 'field':'b6','w':5}, {'label':'BIT_5', 'field':'b5','w':5},
                    {'label':'BIT_4', 'field':'b4','w':5}, {'label':'BIT_3', 'field':'b3'},
                    {'label':'BIT_2', 'field':'b2'}, {'label':'BIT_1', 'field':'b1'},
                    {'label':'BYTE', 'field':'byte'}]
