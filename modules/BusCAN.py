import time
#import datetime
import uuid
import can
import threading
import sys
import math
import subprocess
import pexpect

# GLOBAL
from modules.Constants import *


class BusCAN:
  def __init__(self, bus, signals, session):

    self.bus = bus
    self.threads = {}
    self.threadStopManager = {}
    self.slcanProcess = None
    self.appSignals = signals
    self.idValues = {}
    self.session = session

    # Varaibles needed for UDS scan
    self.wish = None
    self.requestIsPositive = threading.Event()
    self.response = {"id":None, "msg":None, "error":None, "errorCode":None, "isoTp":False}

    self.initBus()


  def __getitem__(self, key):
    return getattr(self, key)

  def __setitem__(self, key, value):
    return setattr(self, key, value)


  def initBus(self):
    logging.debug("Initializing bus :\n%s\n"%self.bus)
    if self.bus['mode'] == 'slcan':
      if self.setSlcanSpeed() == True:
        time.sleep(0.2)
        self.callShellCmdIp('up') # Linux ONLY - need Windows update for COM devices
        self.canbus = can.interface.Bus(channel=self.bus['bus'], bustype='socketcan_native')
    elif self.bus['mode'] == 'builtincan':
      # update speed only
      self.setBuiltinSpeed()
      self.canbus = can.interface.Bus(channel=self.bus['bus'], bustype='socketcan_native')
    else:
      pass

    self.bus['active'] = True

    if self.session['mode'] >  SESSION_MODE.IDLE:
      self.startCapturing()


  def closeBus(self):
    # Closing threads first
    for daemon in self.threadStopManager:
      self.threadStopManager[daemon].set()
      self.threads[daemon].join()

    # Closing slcan interface
    if self.bus['mode'] == 'slcan' and self.bus['builtin'] == False:
      self.callShellCmdIp('down')
      self.closeSlcan()
    elif self.bus['mode'] == 'builtincan':
      self.callShellCmdIp('down')
    self.bus['active'] = False


  def callShellCmdIp(self, status = 'up'):
    if not "vcan" in self.bus['bus']:
      args = ['sudo','/sbin/ip', 'link', 'set', status, self.bus['bus']]
      p = subprocess.Popen(args)
      p.communicate()
      return p.returncode


  def slcanGetSpeedCode(self):
    slcanSpeedCode=[10,20,50,100,125,250,500,800,1000]
    try:
      idx = slcanSpeedCode.index(self.bus['speed'])
      return "-s%d"%idx
    except:
      return None


  def setSlcanSpeed(self):
    speed = self.slcanGetSpeedCode()
    if speed != None:
      if 'baudrate' in self.bus:
        speed += " -S %d"%self.bus['baudrate']
        logging.debug("Baudrate : %s"%speed)
        logging.debug("Spawn : ./utils/slcan.sh %s %s %s"%(speed,self.bus['port'],self.bus['bus']))
      self.slcanProcess = pexpect.spawn('./utils/slcan.sh %s %s %s'%(speed,self.bus['port'],self.bus['bus']))
      return True
    else:
      return False


  def setBuiltinSpeed(self):
    if not "vcan" in self.bus['bus']:
      args = ['sudo','/sbin/ip', 'link', 'set', 'down', self.bus['bus']]
      p = subprocess.Popen(args)
      p.communicate()
      time.sleep(0.2)
      args = ['sudo','/sbin/ip', 'link', 'set', 'up', self.bus['bus'], 'type','can','bitrate', str(math.floor(self.bus['speed']*1000))]
      p = subprocess.Popen(args)
      p.communicate()
      return p.returncode


  def closeSlcan(self):
    self.slcanProcess.sendcontrol("c")


  def startCapturing(self):
    if self.bus['mode'] == "slcan" or self.bus['mode'] == "builtincan":
      if not 'capturing' in self.threads:
        self.threads['capturing'] = threading.Thread(target=self.watchBus)
        self.threads['capturing'].start()
    elif self.bus['mode'] == "serial":
      pass
    else:
      pass # return ERROR


  def stopCapturing(self):
    if self.bus['mode'] == "slcan" or self.bus['mode'] == "builtincan":
      self.threadStopManager["capturing"].set()
      self.threads['capturing'].join()
      del self.threadStopManager['capturing']
      del self.threads['capturing']



  # Request / Wish
  def request(self, msg, mode = SCAN.MODE_LEGACY, padding=None):
    self.requestIsPositive.clear()
    self.response['id'] = None
    self.response['msg'] = None
    self.response['isoTp'] = False
    self.response['error'] = False
    self.response['errorCode'] = None
    self.setWish(msg, mode, padding)
    if not 'extendedId' in msg:
      if msg['id'] > 0x7FF:
        msg['extendedId'] = True
      else:
        msg['extendedId'] = False
    self.sendMsg(msg)

  def setWish(self, msg, mode, padding):
    self.wish = {"id": msg['id'], "msg": msg['msg'], "mode": mode, "padding":padding}


  def checkWish(self, msg):
    isValid = False
    if self.wish['mode'] < SCAN.MODE_SMART:
      if msg.arbitration_id == self.wish['id'] + UDS.REPLY_ID_INCREMENT:
        logging.debug("REQUEST : Get reply %s"%msg)
        self.analyseUDSMsg(msg)
      else:
        return False
    else:
      if (msg.data[0] <= 0x08 and msg.data[1] == UDS.ERROR_CODE and msg.data[2] == self.wish['msg'][1]) or ((msg.data[0] <= 0x08 or msg.data[0] & 0xF0 == 0x10) and msg.data[1] == self.wish['msg'][1] + UDS.REPLY_VALID_SERVICE):
        logging.debug("REQUEST : Get reply %s"%msg)
        self.analyseUDSMsg(msg)
      else:
        return False


  def analyseUDSMsg(self, msg):
    if (msg.data[0] &0xF0) == 0x10: #ISOTP init
      self.wish['mode'] = SCAN.MODE_LEGACY
      self.wish['srcId'] =  self.wish['id']
      self.wish['id'] = msg.arbitration_id - UDS.REPLY_ID_INCREMENT

      self.wish['isoTpLen'] = (msg.data[0] & 0x0F)*256 + msg.data[1]
      self.wish['counter'] = 0
      if self.wish['msg'][0] == 0x01:
        start = 3
      else:
        start = 4
      self.wish['isoTpMsg'] = []
      for i in range(start, 8):
        self.wish['isoTpMsg'].append(msg.data[i])
        self.wish['counter'] += 1

      reply = UDS.ISOTP_CONTINUE
      if self.wish['padding'] != None:
        for i in range(len(reply), 8):
          reply.append(self.wish['padding'])
      self.sendMsg(self.wish['srcId'], reply)
    elif (msg.data[0] & 0xF0) == 0x20:
      for i in range(1, len(msg["data"])):
        if self.wish['counter'] < self.wish['isoTpLen'] - 2:
          self.wish['isoTpMsg'].append(msg.data[i])
          self.wish['counter'] += 1
      if self.wish['counter'] >= self.wish['isoTpLen'] - 2:
        self.response['id'] = msg.arbitration_id
        self.response['msg'] = self.wish['isoTpMsg']
        self.response['isoTp'] = True
        self.response['status'].set()
      if msg.data[0] == 0x2F:
        reply = UDS.ISOTP_CONTINUE
        if self.wish['padding'] != None:
          for i in range(len(reply), 8):
            reply.append(self.wish['padding'])
        self.sendMsg(self.wish['srcId'], reply)

    elif msg.data[1] == UDS.ERROR_CODE:
      self.response['id'] = msg.arbitration_id
      self.response['msg'] = list(msg.data)
      self.response['error'] = True
      self.response['errorCode'] = msg.data[3]
      self.requestIsPositive.set()
    else:
      self.response['id'] = msg.arbitration_id
      self.response['msg'] = list(msg.data)
      self.requestIsPositive.set()



  def watchBus(self):
    self.threadStopManager["capturing"] = threading.Event()
    self._lock = threading.Lock()

    lastUpdate = 0
    msg = None

    while not self.threadStopManager["capturing"].is_set():
      if msg is not None:
        with self._lock:
          if (msg):
            if self.wish != None:
              self.checkWish(msg)

            # Gw Management
            if self.bus['gw'] != None:
              if self.bus['label'] + " - " in self.bus['presetLabel']:
                busRef = self.bus['presetLabel']
              else:
                busRef = "%s : %s"%(self.bus['label'],self.bus['presetLabel'])
              if not busRef in self.session['filters'] or not msg.arbitration_id in self.session['idList'][busRef] or (busRef in self.session['filters']  and not msg.arbitration_id in self.session['filters'][busRef]):
                self.appSignals.gatewayForward.emit({"dst":self.bus['gw'], "msg":msg})

            # Parsing details from message
            timer = time.time()
            data = {}
            data['id'] = msg.arbitration_id
            data['extendedId'] = msg.is_extended_id
            data['len'] = msg.dlc
            data['msg'] = list(msg.data)
            data['type'] = "can"
            data['ts'] = time.time()
            data['preset'] =  self.bus['preset']
            data['presetLabel'] =  self.bus['presetLabel']
            data['busName'] = self.bus['label']

            self.appSignals.frameRecv.emit({"msg":data})
      msg = self.canbus.recv(0.1)


  def sendMsg(self, msg, raw=False):
    # TO IMPROVE
    # Manage serial and error
    try:
      if raw == True:
        self.canbus.send(msg)
      else:
        craftedMsg = self.craftMsg(msg['id'], msg['msg'], msg['extendedId'])
        #logging.debug(craftedMsg)
        self.canbus.send(craftedMsg)
    except:
      logging.error(sys.exc_info()[0])


  def craftMsg(self, arbId, msg, extended_id = 0):
    return can.Message(arbitration_id=arbId, data=msg, extended_id=extended_id)
