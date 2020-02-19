
import time
import datetime
import json
import uuid
import can
import threading
import sys

# GLOBAL

# CONSTANTS
UDS_STD = 'UDS_STD'
strictMode = True
minDelay = 0.2
canReplyTimeout = 2

class BUSCAN:
  def __init__(self, socketio, name, interface, speed):
    self.wishes = {}
    self.name = name
    self.speed = speed
    self.threads = {}
    self.stopThread = {}
    self.canDelWishes = threading.Event()
    self.canDelWishes.set()
    self.padding = 0x00
    self.idDB = {}
    self.bus = can.interface.Bus(channel=interface, bustype='socketcan_native')
    self.socketio = socketio

  def __getitem__(self, key):
    return getattr(self, key)

  def __setitem__(self, key, value):
    return setattr(self, key, value)

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
    self.stopThread["watchBus"] = threading.Event()
    lastUpdate = 0
    while not self.stopThread["watchBus"].is_set():
      msg = self.bus.recv(0.0)
      if (msg):
        # A reply is awaited ?
        timer = time.time()
        arbId = '0x{0:0{1}X}'.format(msg.arbitration_id,3)

        if len(self.wishes) > 0:
          self.checkWishes(msg)

        if (not hasattr(self.idDB, arbId)):
          self.idDB[arbId] = {"data":[]}
        self.idDB[arbId]['data'] = list(msg.data)

        if (lastUpdate + minDelay) < timer:
          lastUpdate = timer
          self.socketio.emit('log',
                        {'data': json.dumps(self.idDB)},
                        namespace='/')

  def craftMsg(self, arbId, msg, extended_id = 0):
    if self.padding != None:
      for i in range (len(msg), 8):
        msg.append(self.padding)
    return can.Message(arbitration_id=arbId, data=msg, extended_id=extended_id)

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
