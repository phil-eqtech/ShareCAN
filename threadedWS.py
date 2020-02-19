from flask import Flask, render_template
from flask_restful import Resource, Api, reqparse
from flask_socketio import SocketIO, emit
import time
import datetime
import json
import uuid

import can
import threading
import sys

# Define webserver
app = Flask(__name__)
async_mode = None
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

# Define CAN channels
networks = {} # DB - store networks information about the car
channels = {} # Up to X, active channels - name, bus, type
ids = {}
mainThread = None
minDelay = 0.5
canReplyTimeout = 2
test = threading.Event()
wishEvent = threading.Event()
strictMode = True

#
# WISHES
# Wait for specific CAN/LIN/K-Line message
#
def setWish(bus, name, id=None, validReply=None, errorReply = False, strictReply = False, validId = None):
  if not name in channels[bus]["wishes"]:
    wish = {"occurs": threading.Event(), "id": id, "validReply": validReply, "errorReply": errorReply, "strictReply": strictReply, "validId":validId}
    channels[bus]["wishes"][name] = wish

def delWish(bus, name):
  del channels[bus]["wishes"][name]

def validateWish(bus, name, msg):
  channels[bus]["wishes"][name]["replyMsg"] = msg.data
  channels[bus]["wishes"][name]["replyId"] = msg.arbitration_id
  channels[bus]["wishes"][name]["occurs"].set()


def checkWishes(bus, msg):
  wishes = dict(channels[bus]["wishes"])
  for name in wishes:
    if wishes[name]["validId"] != None and msg.arbitration_id == wishes[name]["validId"]:
      validateWish(bus, name, msg)
      return True
    if (wishes[name]["strictReply"] == False or wishes[name]["id"] + 0x08 == msg.arbitration_id):
      validBytes = 0
      if msg.data[0] & 0xF0 == 0x10:
        isotp = 1
      else:
        isotp = 0
      for bytePos in wishes[name]["validReply"]:
        b = bytePos + isotp
        if msg.data[b] == wishes[name]["validReply"][bytePos]:
          validBytes += 1
      if validBytes == len(wishes[name]["validReply"]):
        validateWish(bus, name, msg)
        return True
      if wishes[name]["errorReply"] != False:
        validBytes = 0
        for bytePos in wishes[name]["errorReply"]:
          if msg.data[bytePos] == wishes[name]["errorReply"][bytePos]:
            validBytes += 1
        if validBytes == len(wishes[name]["errorReply"]):
          validateWish(bus, name, msg)
          return True
  return False

#
# CAN Request
#
def canRequest(bus, arbId, msg, trigger="std", checkError = False, strictReply=strictMode, replyTimeout=canReplyTimeout):
  data = can.Message(arbitration_id=arbId, data=msg,extended_id=0)
  wishName = uuid.uuid4().hex
  replyLen = 0
  replyMsg = []

  if msg[0] == 0x01:
    validReply = {1: msg[1] + 0x40}
  else:
    validReply = {1: msg[1] + 0x40, 2: msg[2]}
  if (checkError == True):
    errorReply = {1: 0x7F, 2:msg[1]}
  else:
    errorReply = False
  setWish(bus, wishName, arbId, validReply, errorReply, strictReply)

  channels[bus]["wishes"][wishName]
  channels[bus]["bus"].send(data)

  channels[bus]["wishes"][wishName]["occurs"].wait(replyTimeout)
  if channels[bus]["wishes"][wishName]["occurs"].is_set():
    if checkError != False and channels[bus]["wishes"][wishName]["replyMsg"][1] == 0x7F:
      delWish(bus, wishName)
      return {"status": "error", "replyId":channels[bus]["wishes"][wishName]["replyId"], "replyLen":None, "replyMsg":None}
    else:
      if channels[bus]["wishes"][wishName]["replyMsg"][0] & 0xF0 == 0x10: # ISOTP
        replyLen = (channels[bus]["wishes"][wishName]["replyMsg"][0] & 0x0F)*256 + channels[bus]["wishes"][wishName]["replyMsg"][1]
        counter = 0
        if msg[0] == 0x01:
          start = 3
        else:
          start = 4
        for i in range(start, 8):
          replyMsg.append(channels[bus]["wishes"][wishName]["replyMsg"][i])
          counter += 1
        replyId = channels[bus]["wishes"][wishName]["replyId"]
        delWish(bus, wishName)
        setWish(bus, wishName, validId = replyId)

        isoTPFollowCommand = can.Message(arbitration_id = arbId, data = [0x30, 0x00, 0x00, 0x00, 0x00, 0x00,0x00, 0x00], extended_id=0)
        channels[bus]["bus"].send(isoTPFollowCommand)
        timer = time.time()
        while counter < replyLen - 2 and timer + replyTimeout > time.time():
          channels[bus]["wishes"][wishName]["occurs"].wait(replyTimeout)
          if channels[bus]["wishes"][wishName]["occurs"].is_set():
            for i in range(1, len(channels[bus]["wishes"][wishName]["replyMsg"])):
              if counter < replyLen - 2:
                replyMsg.append(channels[bus]["wishes"][wishName]["replyMsg"][i])
                counter += 1
            if counter < replyLen - 2 and channels[bus]["wishes"][wishName]["replyMsg"][0] == 0x29:
              isoTPFollowCommand = can.Message(arbitration_id = arbId, data = [0x30, 0x00, 0x00, 0x00, 0x00, 0x00,0x00, 0x00], extended_id=0)
              channels[bus]["bus"].send(isoTPFollowCommand)

            delWish(bus, wishName)
            setWish(bus, wishName, validId = replyId)
            timer = time.time()
      else:
        replyMsg = channels[bus]["wishes"][wishName]["replyMsg"]
        replyLen = len(channels[bus]["wishes"][wishName]["replyMsg"])
      return {"status": "success", "replyId":replyId, "replyLen":replyLen, "replyMsg":replyMsg}
  else:
    delWish(bus, wishName)
    return {"status": "noreply", "replyId":None, "replyLen":None, "replyMsg":None}

def canSocket(id, interface, speed):
  print("Starting canSocket")
  # localVar
  localIds = {}
  lastUpdate = 0

  # Open BUS
  channels[id]["bus"] = can.interface.Bus(channel=interface, bustype='socketcan_native')
  while not channels[id]["stopEvent"].is_set():
    msg = channels[id]["bus"].recv(0.0)
    if (msg):
      # A reply is awaited ?
      timer = time.time()
      arbId = hex(msg.arbitration_id)

      if len(channels[id]["wishes"]) > 0:
        checkWishes(id, msg)

      if (not hasattr(localIds, arbId)):
        localIds[arbId] = {"data":[]}
      localIds[arbId]['data'] = list(msg.data)

      if (lastUpdate + minDelay) < timer:
        lastUpdate = timer
        socketio.emit('log',
                      {'data': json.dumps(localIds)},
                      namespace='/')

def udsRequestVin(bus):
  print("Sending UDS request")
  vin = canRequest(bus, 0x726, [0x02, 0x09, 0x02], trigger="std")
  if vin["status"] == "success":
    print(vin)
    decodedVIN = ""
    for i in range(1, len(vin["replyMsg"])):
      decodedVIN += chr(vin["replyMsg"][i])
    print(decodedVIN)

def main_thread_worker():
    while True:
        socketio.sleep(1)
        #the following emit works fine
        socketio.emit('log',
                      {'data': 'main_thread_data'},
                      namespace='/')
        #this does not work, out of context error.
        #add_log("add this to log")

def add_log(msg):
    #this works when called from test_connect(), seems strange. Shouldn't it be socketio.emit(..) like below ????
    emit('log', {'time': time.ctime(), 'data': msg})
    #this does not work when called from test_connect(), why? confused?
    #socketio.emit('log', {'time': time.ctime(), 'data': msg})

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect', namespace='/')
def test_connect():
    global main_thread
    # OR globals()["myfunction"]()
    #here add_log works fine...
    add_log("Connected")
    #if(main_thread is None):
    #    main_thread = socketio.start_background_task(target=main_thread_worker)
        #here also.
    #    add_log("Started main thread.")

@socketio.on('api', namespace='/')
def apiRoute(jsonData):
  global mainThread
  global channels
  #jsonData = json.loads(str(jsonData))
  if "module" in jsonData:
    if jsonData["module"] == "openCAN":
      channels["canHS"] = {"stopEvent": threading.Event(), "wishes":{}, "thread":None}
      channels["canHS"]["thread"] = socketio.start_background_task(canSocket, 'canHS', 'vcan0', '9600')
    elif jsonData["module"] == "closeCAN":
      channels["canHS"]["stopEvent"].set()
      channels["canHS"]["thread"].join()
      del channels["canHS"]
    elif jsonData["module"] == "sendUDS":
      altThread = socketio.start_background_task(udsRequestVin, 'canHS')


if __name__ == '__main__':
    socketio.run(app, "127.0.0.1", 5000, debug=True)
