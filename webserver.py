from flask import Flask, render_template, session, redirect, url_for, request, make_response, jsonify
from flask_restful import Resource, Api, reqparse
from flask_socketio import SocketIO, emit

import time
import datetime
import json
from pymongo import MongoClient
import bcrypt
from modules.CANbus import BUSCAN
import configparser

import can
import threading
import sys


# CONFIGS
config = configparser.ConfigParser()
config.read("config.ini")
config.sections()


# Define webserver
app = Flask(__name__)
async_mode = None
app.config['SECRET_KEY'] = config['WEBSERVER']['secret']
socketio = SocketIO(app, async_mode='threading')

# CONSTANTS
UDS_STD = 'UDS_STD'

# Global Variables
analysisType = None # Value - Car / Object
mongoDB = MongoClient()
db = mongoDB.autoProject

# Define CAN channels
networks = {} # DB - store networks information about the car
bus = {} # Up to X, active channels - name, bus, type
ids = {}
mainThread = None
minDelay = 0.2
canReplyTimeout = 2
test = threading.Event()
wishEvent = threading.Event()
strictMode = True




def udsRequestVin(busName):
  print("Sending UDS request")
  vin = bus[busName].request(0x7D0, [0x02, 0x09, 0x02])
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
  if not 'username' in session:
    return render_template('login.html', title=config['WEBSERVER']['title'])
  else:
    return render_template('index.html', title = config['WEBSERVER']['title'])

@app.route('/login', methods=['POST'])
def login():
  if request.method == "POST":
    # Define if read from .htpasswd or mongoDB
    if request.form['username'] == "root":
      session['username'] = "root"
      return redirect("/", code=302)
    else:
      return render_template('login.html', title = config['WEBSERVER']['title'], error=True, username=request.form['username'])

@app.route('/config')
def loadConf():
  if not 'username' in session:
    return make_response(jsonify({'error': 'INVALID_SESSION'}))
  else:
    return make_response(jsonify({'analysisType': analysisType}))

@app.route('/loadVehicleOptionsMenu')
def queryVehicleOptionMenu():
  manufacturerDB = db.manufacturers.find({},{"_id":0})
  results = {}
  for manufacturer in manufacturerDB:
    results[manufacturer['name']] = manufacturer
  return make_response(jsonify({"manufacturers":results}))

@socketio.on('connect', namespace='/')
def test_connect():
  global main_thread
  add_log("Connected")

@socketio.on('api', namespace='/')
def apiRoute(jsonData):
  global bus
  #jsonData = json.loads(str(jsonData))
  if "module" in jsonData:
    if jsonData["module"] == "openCAN":
      bus["canHS"] = BUSCAN(socketio, "canHS","can0",9600)
      bus["canHS"]["threads"] = {"watchBus": socketio.start_background_task(bus["canHS"].watchBus)}
    elif jsonData["module"] == "closeCAN":
      bus["canHS"]["stopThreads"]["watchBus"].set()
      bus["canHS"]["threads"]["watchBus"].join()
      del bus["canHS"]
    elif jsonData["module"] == "sendUDS":
       bus["canHS"]["threads"] = {"vinRequest": socketio.start_background_task(udsRequestVin, 'canHS')}


if __name__ == '__main__':
    socketio.run(app, "127.0.0.1", 5000, debug=True)
