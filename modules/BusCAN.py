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

# CONSTANTS
UDS_STD = 'UDS_STD'
strictMode = True
minDelay = 0.1
canReplyTimeout = 2

class BusCAN:
  def __init__(self, bus, signals, session):
    self.wishes = {}
    self.bus = bus
    self.threads = {}
    self.threadStopManager = {}
    self.slcanProcess = None
    self.appSignals = signals
    self.idValues = {}
    self.session = session

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
    if self.bus['bus'] != "vcan0":
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
    if self.bus['bus'] != "vcan0":
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


  def setWish(self, name, id=None, validReply=None, errorReply = False, strictReply = False, validId = None):
    if not name in self.wishes:
      wish = {"occurs": threading.Event(), "id": id, "validReply": validReply, "errorReply": errorReply, "strictReply": strictReply, "validId":validId}
      self.wishes[name] = wish


  def checkWishes(self, msg):
    self.canDelWishes.clear()
    for name in self.wishes:
      if self.wishes[name]["validId"] != None and msg.arbitration_id == self.wishes[name]["validId"]:
        self.validateWish(name, msg)
        self.canDelWishes.set()
        return True

      if (self.wishes[name]["strictReply"] == False or self.wishes[name]["id"] + 0x08 == msg.arbitration_id):
        isotp = 0
        validBytes = 0
        if msg.data[0] & 0xF0 == 0x10:
          isotp = 1
        if (self.wishes[name]["validReply"] != None):
          for bytePos in self.wishes[name]["validReply"]:
            b = bytePos + isotp
            if msg.data[b] == self.wishes[name]["validReply"][bytePos]:
              validBytes += 1
          if validBytes == len(self.wishes[name]["validReply"]):
            self.validateWish(name, msg)
            self.canDelWishes.set()
            return True

        if isotp == 0 and self.wishes[name]["errorReply"] != False:
          validBytes = 0
          for bytePos in self.wishes[name]["errorReply"]:
            if msg.data[bytePos] == self.wishes[name]["errorReply"][bytePos]:
              validBytes += 1
          if validBytes == len(self.wishes[name]["errorReply"]):
            self.validateWish(name, msg)
            self.canDelWishes.set()
            return True
    self.canDelWishes.set()
    return False


  def validateWish(self, name, msg):
    self.wishes[name]["replyMsg"] = msg.data
    self.wishes[name]["replyId"] = msg.arbitration_id
    self.wishes[name]["occurs"].set()


  def delWish(self, name):
    self.canDelWishes.wait()
    del self.wishes[name]


  def watchBus(self):
    self.threadStopManager["capturing"] = threading.Event()
    self._lock = threading.Lock()

    lastUpdate = 0
    msg = None

    while not self.threadStopManager["capturing"].is_set():
      if msg is not None:
        with self._lock:
          if (msg):
            # A reply is awaited ?
            #if len(self.wishes) > 0:
            #  self.checkWishes(msg)

            # Gw Management
            if self.bus['gw'] != None:
              self.appSignals.gatewayForward.emit({"dst":self.bus['gw'], "msg":msg})

            # Parsing details from message
            timer = time.time()
            data = {}
            data['id'] = msg.arbitration_id
            data['extendedId'] = msg.is_extended_id
            data['len'] = msg.dlc
            data['msg'] = msg.data
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
    """if self.padding != None:
      for i in range (len(msg), 8):
        msg.append(self.padding)
    """
    return can.Message(arbitration_id=arbId, data=msg, extended_id=extended_id)

  # TO REWRITE
  def request(self, arbId, msg, trigger=UDS_STD, checkError = False, strictReply=strictMode, replyTimeout=canReplyTimeout):
    data = self.craftMsg(arbId, msg)
    wishName = uuid.uuid4().hex

    replyLen = 0
    replyMsg = []

    if trigger == UDS_STD:
      if msg[0] == 0x01:
        validReply = {1: msg[1] + 0x40}
      else:
        validReply = {1: msg[1] + 0x40, 2: msg[2]}
    else:
      validReply = trigger

    if (checkError != False):
      if (checkError == True):
        errorReply = {1: 0x7F, 2:msg[1]}
      else:
        errorReply = checkError
    else:
      errorReply = False

    self.setWish(wishName, arbId, validReply, errorReply, strictReply)

    self.bus.send(data)

    self.wishes[wishName]["occurs"].wait(replyTimeout)
    if self.wishes[wishName]["occurs"].is_set():
      if checkError != False and self.wishes[wishName]["replyMsg"][1] == 0x7F:
        self.delWish(wishName)
        return {"status": "error", "replyId":self.wishes[wishName]["replyId"], "replyLen":None, "replyMsg":None}
      else:
        if self.wishes[wishName]["replyMsg"][0] & 0xF0 == 0x10: # ISOTP
          replyLen = (self.wishes[wishName]["replyMsg"][0] & 0x0F)*256 + self.wishes[wishName]["replyMsg"][1]
          counter = 0
          if msg[0] == 0x01:
            start = 3
          else:
            start = 4
          for i in range(start, 8):
            replyMsg.append(self.wishes[wishName]["replyMsg"][i])
            counter += 1
          replyId = self.wishes[wishName]["replyId"]

          self.delWish(wishName)
          wishName = uuid.uuid4().hex
          self.setWish(wishName, validId = replyId)

          isoTPFollowCommand = self.craftMsg(arbId,[0x30, 0x00, 0x00])
          self.bus.send(isoTPFollowCommand)
          timer = time.time()
          while counter < replyLen - 2 and timer + replyTimeout > time.time():
            self.wishes[wishName]["occurs"].wait(replyTimeout)
            if self.wishes[wishName]["occurs"].is_set():
              for i in range(1, len(self.wishes[wishName]["replyMsg"])):
                if counter < replyLen - 2:
                  replyMsg.append(self.wishes[wishName]["replyMsg"][i])
                  counter += 1
              if counter < replyLen - 2 and self.wishes[wishName]["replyMsg"][0] == 0x29:
                self.bus.send(isoTPFollowCommand)
                self.delWish(wishName)
                self.setWish(wishName, validId = replyId)
              else:
                self.wishes[wishName]["occurs"].clear()
              timer = time.time()
        else:
          replyMsg = self.wishes[wishName]["replyMsg"]
          replyLen = len(self.wishes[wishName]["replyMsg"])
        self.delWish(wishName)
        return {"status": "success", "replyId":replyId, "replyLen":replyLen, "replyMsg":replyMsg}
    else:
      self.delWish(wishName)
      return {"status": "noreply", "replyId":None, "replyLen":None, "replyMsg":None}
