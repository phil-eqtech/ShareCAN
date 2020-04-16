import sys
import subprocess
import time
import uuid
import re
from pymongo import MongoClient

from modules.Constants import *

class Interfaces:
  def __init__(self, config, appSignals):
    self.devices = {}
    self.bus = {}
    self.config = config
    self.appSignals = appSignals

    mongoDB = MongoClient()
    self.db = mongoDB[config['MONGO']['base']]

    self.loadKnownDevices()
    self.listDevices()
    self.autoMountBuiltInInterfaces()
    self.autoMountPermanentInterfaces()


  def __getitem__(self, key):
    return getattr(self, key)


  def __setitem__(self, key, value):
    return setattr(self, key, value)


  def loadKnownDevices(self):
    deviceDb = self.db.devices.find({},{"_id":0})
    self.knownDevices = []
    for d in deviceDb:
      self.knownDevices.append(d)


  def listDevices(self):
    tmpDevicesList = {}
    searchUSB = subprocess.check_output(["./utils/searchUSB.sh"])
    if searchUSB != subprocess.CalledProcessError:
      deviceList = searchUSB.decode('utf-8').split("\n")
      for i in range(0, len(deviceList) - 1):
        usbInfo = deviceList[i].split(" - ")

        for knownDevice in self.knownDevices:
          if knownDevice['ref'] in usbInfo[1]:
            if not deviceList[i] in self.devices:
              tmpDevicesList[deviceList[i]] = {"name":knownDevice['name'], "label":knownDevice['name'][0:8], "builtin":knownDevice['builtin'], "port":usbInfo[0], "ref":usbInfo[1], "permanent":False, "active":False}
              if 'baudrate' in knownDevice:
                tmpDevicesList[deviceList[i]]['baudrate'] = knownDevice['baudrate']
            else:
              tmpDevicesList[deviceList[i]] = self.devices[deviceList[i]]
            break
      # Look for disconnected devices
      if len(self.devices) > len(tmpDevicesList):
        for ref in self.devices:
          if not ref in tmpDevicesList:
            print("Manage disconnected device")
            print(ref)

    # Look for builtin devices

    for knownDevice in self.knownDevices:
      if knownDevice['builtin'] == True:
        process = subprocess.Popen(['dmesg'], stdout=subprocess.PIPE)
        dmesg = subprocess.Popen(['grep',knownDevice['ref']], stdin=process.stdout, stdout=subprocess.PIPE)
        process.wait()
        out, err = output = dmesg.communicate()
        if len(out) > 0:
          if type(out) == bytes:
            out = out.decode()
          devices = re.findall("([v]*can[0-9]*):", out)
          for device in devices:
            if device == "vcan":
              device = "vcan0"
            if not device in self.devices:
              tmpDevicesList[device] = {"name":"%s (%s)"%(knownDevice['name'], device), "label":"%s (%s)"%(knownDevice['name'], device), "builtin":knownDevice['builtin'], "port":device, "ref":knownDevice['ref'], "permanent":False, "active":False}
            else:
              tmpDevicesList[device] = self.devices[device]
    self.devices = tmpDevicesList


  def autoMountBuiltInInterfaces(self):
    for knownDevice in self.knownDevices:
      if knownDevice['builtin'] == True:
        for device in self.devices:
          if self.devices[device]["ref"] in knownDevice['ref']:
            self.devices[device]['builtin'] = True
            self.activateDevice(device, checkAltName = True)


  def autoMountPermanentInterfaces(self):
    permanentDevices = self.db.config.find({"autoconnect":{"$exists": True}},{"_id":0})
    for permanentDevice in permanentDevices:
      for device in self.devices:
        if permanentDevice["autoconnect"] == self.devices[device]["ref"]:
          self.devices[device]['label'] = permanentDevice["label"]
          self.devices[device]['permanent'] = True
          self.activateDevice(device, checkAltName = True)
          break


  def activateDevice(self, id, setPermanent = False, checkAltName = False):
    if id in self.devices:
      for knownDevice in self.knownDevices:
        if knownDevice['ref'] in self.devices[id]['ref']:
          self.devices[id]['active'] = True
          if checkAltName == True:
            mongoCursor = self.db.config.find({"busAltName": self.devices[id]['ref'] },{"_id":0})
            busAltName = []
            for elt in mongoCursor:
              busAltName.append(elt)
          else:
            busAltName = None
          for iface in knownDevice['interfaces']:
            if knownDevice['builtin'] == True:
              busId = id
              iface['id'] = id
            else:
              busId = str(uuid.uuid4())[0:13]

            self.bus[busId] = {"id":busId, "name":iface['label'], "label": "", "type": iface['type'],
                                "mode": iface['mode'], "ref": iface['id'], "active": False, "speed":None, "spec": None,
                                "device": id, "port": self.devices[id]['port'], "deviceLabel": self.devices[id]['label'],
                                "gw": None, "preset":None, "presetLabel":None, "builtin":self.devices[id]['builtin']}
            if 'baudrate' in self.devices[id]:
              self.bus[busId]['baudrate'] = self.devices[id]['baudrate']
            if self.bus[busId]['mode'] == "slcan" or self.bus[busId]['mode'] == "builtincan":
              if knownDevice['builtin'] == True:
                self.bus[busId]['bus'] = busId
              else:
                self.bus[busId]['bus'] =  (iface['id'] + "-" + busId)[0:15]
            if checkAltName == True and len(busAltName) > 0:
              for altName in busAltName:
                if altName['busAltName'] == self.devices[self.bus[busId]['device']]['ref'] and altName['bus'] == iface['id']:
                  self.bus[busId]['name'] = altName['name']
                  self.bus[busId]['label'] = altName['name']
                  break
          if setPermanent == True:
            self.devices[self.bus[busId]['device']]['permanent'] = True
            self.db.config.insert({"autoconnect":self.devices[id]['ref'], "label": self.devices[id]['label']})


  def deactivateDevice(self, id):
    if id in self.devices and self.devices[id]['active'] == True:
      print("Deactivating device %s with id %s "%(self.devices[id]['name'],id))
      self.devices[id]['active'] = False
      busToDel = []
      for uid in self.bus:
        if self.bus[uid]['device'] == id:
          busToDel.append(uid)
      for uid in busToDel:
        del self.bus[uid]
          # Kill thread if exists
      if self.devices[id]['permanent'] == True:
        self.db.config.remove({"autoconnect":self.devices[id]['ref']})
        self.db.config.remove({"busAltName":self.devices[id]['ref']})
        self.devices[id]['permanent'] = False
