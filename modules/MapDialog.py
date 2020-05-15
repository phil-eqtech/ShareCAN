from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from modules.Constants import *

import qtawesome as qta
import time
import logging
import uuid
import re
import sys
import threading
import math

from ui.ModelDialog import ModelDialog, UCValidator
from ui.MapForm import Ui_MAP

#
# Dialog classes
#
class ECUMapForm(QWidget, Ui_MAP):
  def __init__(self):
   super().__init__()
   self.setupUi(self)


class ECUMapDialog(ModelDialog):
  def __init__(self, refWindow):
    super().__init__()

    self.getMainVariables(refWindow)

    self.startId = 0
    self.endId = 0
    self.padding = None
    self.services = []
    self.iface = None
    self.scanMode = SCAN.MODE_LEGACY
    self.feedbackMode = REPLAY.FEEDBACK_NONE

    self.currentId = 0
    self.currentSession = 0
    self.currentSubfunction = 0

    self.threadStopManager['scan'] = threading.Event()

    self.scanResult = {}

    # Bottom buttons
    self.closeBtn = QPushButton()
    self.closeBtn.setIcon(qta.icon('fa.close',color='white'))
    self.closeBtn.setText(QCoreApplication.translate("DIALOG", "CLOSE"))
    self.closeBtn.setProperty("cssClass","btn-danger")
    self.closeBtn.setCursor(Qt.PointingHandCursor)
    self.closeBtn.clicked.connect(lambda: self.closeDialog())
    self.setBottomButtons(self.closeBtn)

    # Loading body template
    self.body = ECUMapForm()
    self.dialogTitle.setText(QCoreApplication.translate("MainWindow", "ECU_MAP_SCAN_UDS"))
    self.dialogBody.addWidget(self.body)

    # Btn
    options=[{'color_disabled': 'black', 'color':'white'}]
    self.body.btnApply.setIcon(qta.icon("fa5.save", options=options))
    self.body.btnSave.setIcon(qta.icon("fa5.save", options=options))
    self.body.btnStop.setIcon(qta.icon("fa5.stop-circle", options=options))
    self.body.btnScan.setIcon(qta.icon("mdi.magnify-scan", options=options))

    self.body.progress.hide()
    self.body.btnStop.hide()
    self.body.btnSave.hide()
    self.body.errorMsg.hide()


    # Signals
    self.body.comboBus.currentIndexChanged.connect(lambda : self.updateDeviceCombo())
    self.body.btnScan.clicked.connect(lambda: self.scanEcu())
    self.appSignals.scanEnded.connect(lambda: self.setBtnStatus(False))
    self.body.btnStop.clicked.connect(lambda: self.threadStopManager['scan'].set())

    # Context menu

    # Validators
    regexId = QRegExp("[0-9a-fA-F!]{1,8}") #\\-*+|^&/
    regexPadding = QRegExp("[0-9a-fA-F!]{1,2}")
    self.body.fldStart.setValidator(QRegExpValidator(regexId))
    self.body.fldEnd.setValidator(QRegExpValidator(regexId))
    self.body.fldPadding.setValidator(QRegExpValidator(regexPadding))

    #Regex
    self.regexpNonBytes = "([\\+\\*\\-/^|&~\\<\\>s])+"
    self.regexpFormula  = "([\\+\\*\\-/^|&~\\<\\>\\$])+"
    self.regexpOperands = "([\\+\\*\\-/^|&~\\<\\>])"


    # Bus list
    self.body.comboBus.addItem("")
    self.availableBus = sorted(self.analysis['bus'], key=lambda x: (x['type'], x['name']))
    for bus in self.availableBus:
      presetLabel = "%s : %s - %s %s"%(SUPPORTED_BUS_TYPE[bus['type']], bus['name'], bus['speed'], SUPPORTED_SPEED_UNIT[bus['type']])
      bus['presetLabel'] = presetLabel
      self.body.comboBus.addItem(presetLabel, bus)


  def closeDialog(self):
    self.threadStopManager['scan'].set()
    self.reject()


  def closeEvent(self, event):
    self.threadStopManager['scan'].set()


  def updateDeviceCombo(self):
    self.body.comboDevice.clear()

    idx = 0
    self.body.comboDevice.addItem("")

    if self.body.comboBus.currentIndex() > 0:
      self.body.comboDevice.setDisabled(False)
      bus = self.body.comboBus.currentData()
      if len(bus['padding']) > 0 and len(self.body.fldPadding.text()) == 0:
        self.body.fldPadding.setText(bus['padding'])
      busOrder = sorted(self.interfaces.bus, key=lambda x: (self.interfaces.bus[x]['deviceLabel'], self.interfaces.bus[x]['name']))
      for id in busOrder:
        if self.interfaces.bus[id]['type'] == bus['type']:
          self.body.comboDevice.addItem("%s %s"%(self.interfaces.bus[id]['deviceLabel'],self.interfaces.bus[id]['name']),
                                          self.interfaces.bus[id])
          if self.interfaces.bus[id]['active'] == True and self.interfaces.bus[id]['preset'] == bus['hash']:
            idx = self.body.comboDevice.count() - 1
      self.body.comboDevice.setCurrentIndex(idx)
    else:
      self.body.comboDevice.setDisabled(True)


  def initInterfaces(self):
    bus = self.body.comboBus.currentData()
    iface = self.body.comboDevice.currentData()

    if self.interfaces.bus[iface['id']]['active'] == False or self.interfaces.bus[iface['id']]['preset'] != bus['hash']:
      if self.interfaces.bus[iface['id']]['gw'] != None:
        self.interfaces.bus[self.interfaces.bus[iface['id']]['gw']] = None
      self.interfaces.bus[iface['id']]['gw'] = None
      self.interfaces.bus[iface['id']]['preset'] = bus['hash']
      self.interfaces.bus[iface['id']]['speed'] = bus['speed']
      self.interfaces.bus[iface['id']]['label'] = bus['name']
      self.interfaces.bus[iface['id']]['presetLabel'] = bus['presetLabel']
      self.appSignals.switchBus.emit({"id":iface['id'], "dialog":None})
      time.sleep(0.5)

    self.iface = self.activeBus[iface['id']]


  def scanEcu(self):
    if self.checkScanParams() == True:
      self.setBtnStatus(True)
      self.initInterfaces()

      self.feedback = self.body.comboFeedback.currentIndex()
      if self.feedback == REPLAY.FEEDBACK_LIVE:
        self.appSignals.startSessionLive.emit(True)
      elif self.feedback == REPLAY.FEEDBACK_RECORD:
        self.appSignals.startSessionRecording.emit(False)
      elif self.feedback == REPLAY.FEEDBACK_RECORD_NEW_SESSION:
          self.appSignals.startSessionRecording.emit(True)

      self.scanMode = self.body.comboMode.currentIndex()

      self.threads['scan'] = threading.Thread(target = self.threadScanUDS)
      self.threads['scan'].start()


  def threadScanUDS(self):
    self.threadStopManager['scan'].clear()
    self.currentId = self.startId

    while self.currentId <= self.endId and not self.threadStopManager['scan'].isSet():
      self.idScanSequence()
      self.currentId += 1

    self.threadStopManager['scan'].set()

    if self.feedback >= REPLAY.FEEDBACK_RECORD:
      self.appSignals.startSessionForensic.emit(True)
    elif self.feedback == REPLAY.FEEDBACK_LIVE:
      self.appSignals.pauseSession.emit(True)

    self.appSignals.scanEnded.emit(True)


  def idScanSequence(self):
    currentSession = 0x01
    if self.scanMode == SCAN.MODE_QUICK or self.scanMode == SCAN.MODE_SMART_QUICK:
      maxValue = SCAN.QUICK_MODE_MAX_SUBFUNCTION
    else:
      maxValue = SCAN.STANDAD_MODE_MAX_SUBFUNCTION
    ecuDefaultSession = self.udsRequest([0x02, 0x10, currentSession])

    if ecuDefaultSession:
      self.scanResult[self.currentId] = {"listen": self.currentId, "reply": ecuDefaultSession['id'],
                                          "session": [currentSession], "name":"ECU #"}
      ecuName = self.udsRequest([0x02, 0x09, 0x0A])
      if ecuName:
        self.scanResult[self.currentId]['name'] = "OBD2 name"

      if SCAN.SERVICE_TESTER in self.services and not self.threadStopManager['scan'].isSet():
        testerPresent =  self.udsRequest([0x02, 0x3E, 0x00])
        if testerPresent:
          self.scanResult[self.currentId]['testerPresent'] = True
        else:
          self.scanResult[self.currentId]['testerPresent'] = False

      if not self.threadStopManager['scan'].isSet():
        self.scanServices(currentSession)
    elif SCAN.SERVICE_ROUTINE in self.services and not self.threadStopManager['scan'].isSet():
      pass
      # Force routine control scan

  def scanServices(self, maxValue):
    pass

  """
      while currentSession <= maxValue and self.threadStopManager['scan'].isSet():

    else:
      pass
      # Update listResults
      # Gather name / ref
      # Scan session
        # Scan tester
        # Scan routine
        # Scan read
        # Scan request
        # Scan security
        # Scan reset
  """


  def udsRequest(self, msg, awaitIsoTP = False):
    if self.padding != None:
      if len(msg) < 8:
        for i in range(len(msg), 8):
          msg.append(self.padding)
    if awaitIsoTP == True:
      waitTime = SCAN.WAIT_TIME_ISOTP
    else:
      waitTime = SCAN.WAIT_TIME
    self.iface.request({"id":self.currentId, "msg":msg}, mode=self.scanMode, padding=self.padding)
    if self.iface.requestIsPositive.wait(waitTime):
      return self.iface.response
    else:
      return False


  def checkScanParams(self):
    if self.body.comboBus.currentIndex() == 0:
      return self.showCmdError("NO_BUS_SELECTED")
    elif self.body.comboDevice.currentIndex() == 0:
      return self.showCmdError("NO_DEVICE_SELECTED")
    else:
      startId = self.body.fldStart.text()
      endId = self.body.fldEnd.text()
      padding = self.body.fldPadding.text()
      if len(startId) == 0:
        start = "0"
      if len(endId) == 0:
        return self.showCmdError("END_VALUE_NOT_SET")
      startId = int(startId,16)
      endId = int(endId,16)
      if endId < startId:
        return self.showCmdError("END_ID_LOWER_THAN_START_ID")
      if endId > 0x80000000:
        return self.showCmdError("INCORRECT_END_VALUE")

      self.startId = startId
      self.endId = endId
      if len(padding) == 0:
        self.padding = None
      else:
        self.padding = int(padding, 16)

      services = []
      if self.body.checkTester.checkState() == True:
        services.append(SCAN.SERVICE_TESTER)
      if self.body.checkReset.checkState() == True:
        services.append(SCAN.SERVICE_RESET)
      if self.body.checkSecurity.checkState() == True:
        services.append(SCAN.SERVICE_SECURITY)
      if self.body.checkRoutine.checkState() == True:
        services.append(SCAN.SERVICE_ROUTINE)
      if self.body.checkRead.checkState() == True:
        services.append(SCAN.SERVICE_READ)
      if self.body.checkRequest.checkState() == True:
        services.append(SCAN.SERVICE_REQUEST)
      if self.body.checkOBD2.checkState() == True:
        services.append(SCAN.SERVICE_OBD2)
      self.services = services
    return True


  def changeSrc(self):
    self.cmdSrc = self.body.comboCmdSrc.currentData()
    self.loadComboSelector()


  def showCmdError(self, errMsg, data=None):
    self.body.errorMsg.show()
    if data != None:
      logging.debug("ERROR %s ON %s"%(errMsg, data))
      self.body.errorMsg.setText(QCoreApplication.translate("MAP",errMsg + " : " + data))
    else:
      logging.debug("ERROR %s"%(errMsg))
      self.body.errorMsg.setText(QCoreApplication.translate("MAP",errMsg))
    return False

  def loadComboSelector(self):
    self.comboCmdLock = True
    idx = self.body.comboCmdSelector.count()
    for i in range(0, idx):
      self.body.comboCmdSelector.removeItem(0)
    self.body.comboCmdSelector.addItem("---", None)

    if self.cmdSrc == CMD.SRC['ANALYSIS']:
      query = {"analysis": self.analysis['id']}
    else:
      query = {"owner":{"$ne": self.user['uid']}, "manufacturer": self.analysis['manufacturer']}
      if self.cmdSrc >= CMD.SRC["MODEL"]:
        query["model"] = self.analysis["model"]
      if self.cmdSrc == CMD.SRC["ENGINE_CODE"]:
        query["engineCode"] = self.analysis["engineCode"]

    cmdCursor = self.db.commands.find(query,{"_id":0})
    if cmdCursor.count() > 0:
      cmdOrder = sorted(cmdCursor, key=lambda x: x['name'])

      for cmd in cmdOrder:
        lbl = cmd['name']
        if cmd['owner'] != self.user['uid']:
          if cmd['engineCode'] == self.analysis['engineCode']:
            lbl += " (%s)" % QCoreApplication.translate("GENERIC","ENGINE_CODE")
          elif cmd['model'] == self.analysis['model']:
            lbl += " (%s)" % QCoreApplication.translate("GENERIC","MODEL")
          else:
            lbl += " (%s)" % QCoreApplication.translate("GENERIC","MANUFACTURER")
        self.body.comboCmdSelector.addItem(lbl, cmd)
      self.comboCmdLock = False

  def setBtnStatus(self, status= True, ended=False):
    self.body.errorMsg.setVisible(not status)
    self.body.btnScan.setVisible(not status)
    self.body.btnStop.setVisible(status)
    self.body.progress.setVisible(status)
    self.body.btnSave.setVisible(ended)
    self.body.comboBus.setDisabled(status)
    self.body.comboDevice.setDisabled(status)
    self.body.fldStart.setDisabled(status)
    self.body.fldEnd.setDisabled(status)
    self.body.fldPadding.setDisabled(status)
    self.body.comboMode.setDisabled(status)
    self.body.comboFeedback.setDisabled(status)
    self.body.checkTester.setDisabled(status)
    self.body.checkReset.setDisabled(status)
    self.body.checkSecurity.setDisabled(status)
    self.body.checkRoutine.setDisabled(status)
    self.body.checkRead.setDisabled(status)
    self.body.checkRequest.setDisabled(status)
    self.body.checkOBD2.setDisabled(status)
