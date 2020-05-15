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
  BACKTIME = 3
  MAX_WAIT_TIME = 5

  FEEDBACK_NONE = 0
  FEEDBACK_LIVE = 1
  FEEDBACK_RECORD = 2
  FEEDBACK_RECORD_NEW_SESSION = 3

  PROGRESSBAR_UPDATE_DELAY = 1
  PROGRESSBAR_SMALL_BUFFER = 500

class SLICE:
  NEXT = 1
  PREVIOUS = -1
  SELF = 0

class SIGNALS:
  SRC = {"ANALYSIS":1, "ENGINE_CODE":2, "MODEL":3, "MANUFACTURER":4}
  DEFAULT = 2

class DISPLAY:
  DURATION = {"1 sec":1, "5 sec":5, "30 sec":30, "1 min": 60}

class CMD:
  SRC = {"ANALYSIS":1, "ENGINE_CODE":2, "MODEL":3, "MANUFACTURER":4}
  FUZZ_QTY_WARN = 60000
  FUZZ_QTY_LIMIT = FUZZ_QTY_WARN*60

class SCAN:
  MODE_QUICK = 0
  MODE_LEGACY = 1
  MODE_SMART_QUICK = 2
  MODE_SMART = 3


  QUICK_MODE_MAX_SUBFUNCTION = 0xF
  STANDAD_MODE_MAX_SUBFUNCTION = 0xFF
  RESET_RESTORE_TIME = 5

  SERVICE_SESSION = 1
  SERVICE_TESTER = 2
  SERVICE_RESET = 3
  SERVICE_SECURITY = 4
  SERVICE_ROUTINE = 5
  SERVICE_READ = 6
  SERVICE_REQUEST = 7
  SERVICE_OBD2 = 8

  WAIT_TIME = 0.2
  WAIT_TIME_ISOTP = 2

  MODE_LEGACY = 1
  MODE_SMART = 2

class UDS:
  REPLY_ID_INCREMENT = 0x08
  REPLY_VALID_SERVICE = 0x40
  ERROR_CODE = 0x7F

  ISOTP_CONTINUE = [0x30, 0x00, 0x00]

  SERVICES = {"SESSION_CONTROL": 0x10, "TESTER_PRESENT":0x3E,"ECU_RESET":0x11,
              "SECURITY_ACCESS": 0x27, "CONTROL_DTC":0x85, "READ_DATA_BY_IDENTIFIER":0x24,
              "READ_DATA_BY_ADDRESS": 0x23, "ROUTINE_CONTROL": 0x31, "REQUEST_UPLOAD": 0x35,
              "REQUEST_DOWNLOAD": 0x35}

LOG_LEVEL = logging.DEBUG

CSS_FILE = "./static/ui.css"

WIRE_COLOR = ["BK","BN","BU","GN","GY","OG","RD","VT","WH","YE"]

OBD_PORTS = []
for i in range(0, 16):
  OBD_PORTS.append(i+1)

ID_MAX_VALUE = 536870911
BYTE_MAX_VALUE = 255

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

FRAME_WINDOW_MODEL = [{'label':'ID', 'field':'id', 'w':8},{'label':'BUS', 'field':'busName','w':20},
                      {'label':'ECU', 'field':'ecu','w':10}, {'label':'DATA', 'field':'msg','w':170},
                      {'label':'ASCII', 'field':'ascii','w':10}, {'label':'COUNT', 'field':'count','w':8},
                      {'label':'PERIOD', 'field':'period','w':8}, {'label':'TIME', 'field':'ts','w':15},
                      {'label':'SIGNAL', 'field':'signals'}]

BIT_WINDOW_MODEL = [{'label':'BIT_8', 'field':'b8','w':5}, {'label':'BIT_7', 'field':'b7','w':5},
                    {'label':'BIT_6', 'field':'b6','w':5}, {'label':'BIT_5', 'field':'b5','w':5},
                    {'label':'BIT_4', 'field':'b4','w':5}, {'label':'BIT_3', 'field':'b3'},
                    {'label':'BIT_2', 'field':'b2'}, {'label':'BIT_1', 'field':'b1'},
                    {'label':'BYTE', 'field':'byte'}]
