#!/usr/bin/python3

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import qtawesome as qta

import time
import datetime
import uuid
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import bcrypt
import configparser
import threading
import sys
import subprocess
import atexit
import logging

from modules.Constants import *
from modules.FrameWindow import *
from modules.Interfaces import Interfaces
from modules.Signals import CustomSignals
from modules.BusCAN import BusCAN

from ui.MainWindow import Ui_MainWindow
from ui.AnalysisWindow import Ui_AnalysisWindow
from ui.DevicesDialog import *
from ui.BusDialog import *
from ui.SessionDialog import *
from ui.SignalDialog import *
from ui.ReplayDialog import *
from ui.CommandDialog import *
from ui.AnalysisParamsDialog import *
from ui.NotepadDialog import *


class MainWindow(QMainWindow, Ui_MainWindow):
  def __init__(self, *args, obj=None, **kwargs):
    super(MainWindow, self).__init__(*args, **kwargs)
    self.setupUi(self)

    # config
    self.config = configparser.ConfigParser()
    self.config.read("config.ini")
    self.config.sections()

    logging.getLogger().setLevel(LOG_LEVEL)

    # DB
    mongoDB = MongoClient()
    self.db = mongoDB[self.config['MONGO']['base']]

    # Main variables declaration
    self.activeBus = {}     # Bus threads mgmt
    self.interfaces = {}

    self.initUserObject()
    self.initAnalysisObject()
    self.initSession()
    self.sessionLive()
    self.initDisplayObject()
    self.initSignals()

    self.filterWidgets = {}

    self.threads = {}
    self.threadStopManager = {}

    self.msgBuffer = []
    self.maskStatic = False

    self.appSignals = CustomSignals()
    self.interfaces = Interfaces(self.config, self.appSignals)

    self.signalFrameSrc = None

    self.activeWindows = {}

    logging.debug("BUS :\n %s"%self.interfaces.bus)

    #
    # -- UI Init --
    # Signals
    self.appSignals.startAnalysis.connect(lambda: self.openAnalysisWindow())

    self.appSignals.switchBus.connect(lambda eventDict:self.switchBus(eventDict['id'], eventDict['dialog']))
    self.appSignals.stopSessionRecording.connect(self.stopSessionRecording)
    self.appSignals.startSessionLive.connect(lambda eventBool: self.sessionLive())
    self.appSignals.frameRecv.connect(lambda eventDict: self.appendNewBusMsg(eventDict['msg']))
    self.appSignals.gatewayForward.connect(lambda eventDict: self.forwardBusMsg(eventDict['dst'], eventDict['msg']))
    self.appSignals.signalReload.connect(lambda eventBool: self.loadSignals())
    self.appSignals.filterHideId.connect(lambda eventList : self.filterHideId(eventList))
    self.appSignals.filterShowId.connect(lambda eventList : self.filterShowId(eventList))
    self.appSignals.unFilterId.connect(lambda eventBool : self.unFilterId())
    self.appSignals.replaySelection.connect(lambda eventList: self.openReplayDialog(REPLAY.SELECTION, eventList))
    self.appSignals.replayCommand.connect(lambda eventDict: self.openReplayDialog(REPLAY.COMMAND, eventDict['frames'], eventDict['initMsg'], eventDict['startPause'], eventDict['endPause'], eventDict['hasFuzzing']))

    # Login - BTN signals
    # If no user is set, the user is prompted for his desired login/pwd
    userCursor = self.db.config.find({"localUsername":{"$exists":True}})
    userExists = userCursor.count() # Could not use count_documents for old pymongo compatibility
    if userExists > 0:
      self.fldConfirmPassword.hide()
      self.labelProfileName.hide()
      self.fldProfileName.hide()
      self.newUserMsg.hide()
      self.btnLogin.clicked.connect(lambda: self.login())
    else:
      self.btnLogin.clicked.connect(lambda: self.createUser())

    # Dashboard - BTN signals
    self.btnNewAnalysis.clicked.connect(lambda: self.openAnalysisParamsDialog(True))
    self.btnMainMenu.clicked.connect(lambda: self.openDashboardWindow())
    self.btnDevices.released.connect(self.openDevicesDialog)

    # Analysis window - frame table
    self.frameModel = framesTableModel(FRAME_WINDOW_MODEL, [], self.msgTable, self.appSignals)
    self.msgTable.setModel(self.frameModel)
    self.msgTable.setItemDelegate(CustomDelegate(self))
    self.msgTable.linkAppSignals(self.appSignals)

    h = self.msgTable.horizontalHeader()
    self.msgTable.resizeColumnsToContents()
    h.setStretchLastSection(True)

    for i in range(0, len(FRAME_WINDOW_MODEL)):
      if 'w' in FRAME_WINDOW_MODEL[i]:
        self.msgTable.setColumnWidth(i,FRAME_WINDOW_MODEL[i]['w'])


    # Analysis Window - BTN signals
    self.btnBusCan.clicked.connect(lambda: self.openBusDialog('can'))
    self.btnBusLin.clicked.connect(lambda: self.openBusDialog('lin'))
    self.btnBusKln.clicked.connect(lambda: self.openBusDialog('kln'))
    self.btnEditVehicle.clicked.connect(lambda: self.openAnalysisParamsDialog(False))
    self.btnShowRightMenu.clicked.connect(self.showRightMenu)

    self.btnCollapseDisplay.clicked.connect(lambda: self.collapsePanel(self.btnCollapseDisplay, self.cardBodyDisplay))
    self.btnCollapseFilter.clicked.connect(lambda: self.collapsePanel(self.btnCollapseFilter, self.cardBodyFilter))
    self.btnCollapseSession.clicked.connect(lambda: self.collapsePanel(self.btnCollapseSession, self.cardBodySession))

    self.checkMaskStatic.clicked.connect(lambda x: self.maskStaticFrames(x))
    self.comboKeepDuration.currentIndexChanged.connect(lambda: self.updateStaticDuration())
    self.comboSignalsSrc.currentIndexChanged.connect(lambda: self.loadSignals())
    self.btnSessionLive.clicked.connect(lambda: self.sessionLive())
    self.btnSessionPause.clicked.connect(lambda: self.sessionPause())
    self.btnSessionRec.clicked.connect(lambda: self.sessionRecord())
    self.btnSessionReplay.clicked.connect(lambda: self.openReplayDialog(REPLAY.SESSION))
    self.btnSessionLoad.clicked.connect(lambda: self.openSessionLoadDialog())
    self.btnSessionSave.clicked.connect(lambda: self.openSessionSaveDialog())
    self.btnSessionForensic.clicked.connect(lambda: self.sessionForensic())
    self.btnSessionNew.clicked.connect(lambda: self.sessionNew())
    self.btnCmdEditor.clicked.connect(lambda :self.openCmdEditorDialog(cmdId=False))
    self.btnSnap.clicked.connect(lambda: self.snapBus())
    self.btnSnapClear.clicked.connect(lambda: self.snapBus(clear=True))
    self.msgTable.doubleClicked.connect(lambda x:self.openSignalDialog(x))
    self.btnNotes.clicked.connect(lambda:self.openNotesDialog())

    self.comboKeepDuration.setDisabled(True)
    for k in DISPLAY.DURATION:
      self.comboKeepDuration.addItem(k, DISPLAY.DURATION[k])
    self.maskStatic = False

    # Buttons & logo
    logoIcon = qta.icon('fa5s.car', options=[{'opacity': 0.7, 'color_disabled': 'white'}])
    self.loginLogo.setIcon(logoIcon)



    # Analysis Window - BTN Icons & labels
    self.btnCollapseDisplay.setIcon(qta.icon("ei.chevron-down"))
    self.btnCollapseFilter.setIcon(qta.icon("ei.chevron-down"))
    self.btnCollapseSession.setIcon(qta.icon("ei.chevron-down"))
    btn_options=[{"color":"white","color_disabled":"black"}]
    self.btnBusCan.setIcon(qta.icon('fa5s.network-wired', options=btn_options))
    self.btnBusLin.setIcon(qta.icon('fa.linode', options=btn_options))
    self.btnBusLin.setDisabled(True)
    self.btnBusKln.setIcon(qta.icon('fa5b.kickstarter-k', options=btn_options))
    self.btnBusKln.setDisabled(True)
    self.btnSessionReplay.setIcon(qta.icon("mdi.replay", options=btn_options))
    self.btnSessionNew.setIcon(qta.icon("ei.file-new", options=btn_options))
    self.btnSessionRec.setIcon(qta.icon("mdi.record", options=btn_options))
    self.btnSessionPause.setIcon(qta.icon("fa5s.pause", options=btn_options))
    self.btnSessionForensic.setIcon(qta.icon("mdi.magnify-scan", options=btn_options))
    self.btnSessionLive.setIcon(qta.icon("fa.play", options=btn_options))
    self.btnSessionLoad.setIcon(qta.icon("fa5.folder-open", options=btn_options))
    self.btnSessionSave.setIcon(qta.icon("fa5.save", options=btn_options))
    self.btnCmdEditor.setIcon(qta.icon("fa5s.terminal", options=btn_options))
    self.btnNotes.setIcon(qta.icon("mdi.notebook", options=btn_options))
    self.btnSnap.setIcon(qta.icon("fa5s.camera-retro", options=btn_options))
    self.btnSnapClear.setIcon(qta.icon("mdi.camera-off", options=btn_options))

    # Signals source
    for src in SIGNALS.SRC:
      self.comboSignalsSrc.addItem(QCoreApplication.translate("SIGNALS", src), SIGNALS.SRC[src])
      self.comboSignalsSrc.setCurrentIndex(SIGNALS.DEFAULT)
    self.comboSignalsSrc.currentIndexChanged.connect(lambda: self.loadSignals())

    # -- UI Init --
    #

    mongoDB = MongoClient()
    self.db = mongoDB[self.config['MONGO']['base']]

    # Set stylesheet
    self.cssContent = ""
    with open(CSS_FILE,"r") as fh:
      self.cssContent = self.cssContent + fh.read()
    self.setStyleSheet(self.cssContent)

    # Mandatory - generate menu buttons
    self.setMenuBtn()

    #
    # DEV ONLY - REMOVE IN PRODUCTION
    #
    autoLog = False
    if 'DEV' in self.config:
      if 'defaultUser' in self.config['DEV']:
        credentials = self.db.config.find({"localUsername": self.config['DEV']['defaultUser']},{"_id":0})
        if credentials.count() == 1:
          userData = credentials[0]
          logging.debug('[DEV] Autologged as %s with uuid %s'%(userData['localUsername'],userData['uid']))
          self.user = {"localUsername":userData['localUsername'],"profileName":userData['profileName'], "uid":userData['uid']}
          autoLog = True
          self.openDashboardWindow()
    if autoLog == False:
      self.openLoginWindow()
    #
    # DEV ONLY - REMOVE IN PRODUCTION
    #

    # Set login window
    #self.openLoginWindow()


  #
  # Main variables init methods
  #
  def initUserObject(self):
    self.user = {"localUsername":None, "uid":None}

  def initAnalysisObject(self):
    self.analysis = {"vehicleType":None, "manufacturer":None, "model":None, "VIN":None, "engineCode":None,
                      "year":None,"engine":None, "privacy":None, "id":None}  # Car data - VIN & co

  def initSessionObject(self):
    self.session = {"name":None, "id":None, "mode":SESSION_MODE.LIVE, "share": False,
                      "frames":[], "filters":{}, "idList":{}, "owner":None, "frameHistory":{}}

  def initDisplayObject(self):
    self.display = {"mask": False, "keep": 30, "signalSrc":SIGNALS.DEFAULT, "hideMenu":False}

  def initSignals(self):
    self.signals = {}

  #
  # Generic UI methods
  #
  def setMenuBtn(self):
    #Main menu
    self.btnMainMenu.setIcon(qta.icon('mdi.menu', color='#E2E2E2'))
    self.btnMainMenu.setToolTip(QCoreApplication.translate("MainWindow","MAIN_MENU"))
    self.btnDevices.setIcon(qta.icon('mdi.video-input-svideo', color='#E2E2E2'))
    self.btnDevices.setToolTip(QCoreApplication.translate("MainWindow","DEVICES"))
    self.btnDevices.setIcon(qta.icon('mdi.video-input-svideo', color='#E2E2E2'))
    self.btnServer.setToolTip(QCoreApplication.translate("MainWindow","SERVER"))
    self.btnServer.setIcon(qta.icon('fa5s.server', color='#E2E2E2'))
    self.btnAnalysis.setToolTip(QCoreApplication.translate("MainWindow","ANALYSIS"))
    self.btnAnalysis.setIcon(qta.icon('fa.dashboard', color='#E2E2E2'))
    self.btnNotification.setToolTip(QCoreApplication.translate("MainWindow","NOTIFICATION"))
    self.btnNotification.setIcon(qta.icon('fa5.bell', color='#E2E2E2'))
    self.btnProfile.setToolTip(QCoreApplication.translate("MainWindow","PROFILE"))
    self.btnProfile.setIcon(qta.icon('fa.user-circle', color='#E2E2E2'))
    self.btnConfig.setToolTip(QCoreApplication.translate("MainWindow","CONFIG"))
    self.btnConfig.setIcon(qta.icon('fa.cog', color='#E2E2E2'))


  def hideMenuBtn(self):
    self.btnDevices.hide()
    self.btnProfile.hide()
    self.btnNotification.hide()
    self.btnAnalysis.hide()
    self.btnServer.hide()
    self.btnConfig.hide()


  def showMenuBtn(self):
    self.btnDevices.show()
    self.btnProfile.show()
    self.btnNotification.show()
    self.btnAnalysis.show()
    self.btnServer.show()
    self.btnConfig.show()

  def removeLines(self, layout):
    rows = layout.rowCount()
    if rows > 1:
      for r in range(rows -1, 0, -1):
        for c in range(0,layout.columnCount()):
          w = layout.itemAtPosition(r, c)
          if w != None:
            w = w.widget()
            if w.layout():
              sll = w.layout()
              for y in range(0, sll.count()):
                subW = sll.itemAt(0)
                if subW != None:
                  subW = subW.widget()
                  sll.removeWidget(subW)
                  subW.deleteLater()
                  del subW
              del sll
            layout.removeWidget(w)
            w.deleteLater()

  def collapsePanel(self, btnWidget, panelWidget):
    if panelWidget.isHidden() == True:
      btnWidget.setIcon(qta.icon("ei.chevron-down"))
      panelWidget.show()
    else:
      btnWidget.setIcon(qta.icon("ei.chevron-right"))
      panelWidget.hide()
    if self.cardBodyFilter.isHidden() == False:
      pass
      #self.expandPanelFilter()

  def expandPanelFilter(self):
    spacer = 10
    w =  self.cardFilter
    availableSpace = self.rightMenu.height() - self.cardDisplay.height() - self.cardSession.height()
    availableSpace -= spacer * 2
    w.setMinimumSize(w.width(), availableSpace)


  #
  # LOGIN PAGE methods
  #
  def openLoginWindow(self):
    self.hideMenuBtn()
    self.btnMainMenu.setDisabled(True)

    self.errorMsg.hide()
    self.initUserObject()


  def login(self):
    username = self.fldUsername.text()
    if len(username) < 0:
      self.errorMsg.setText(QCoreApplication.translate("LOGIN","USER_NAME_TOO_SHORT"))
      return False

    password = self.fldPassword.text()
    credentials = self.db.config.find({"localUsername": username},{"_id":0})

    if credentials.count() == 1:
      userData = credentials[0]
      if bcrypt.checkpw(password.encode('utf-8'), userData['pwd']):
        self.user = {"localUsername":userData['localUsername'],"uid":userData['uid']}
        self.openDashboardWindow()
      else:
        self.errorMsg.show()
        self.errorMsg.setText(QCoreApplication.translate("LOGIN","INVALID_PWD"))
        return False
    else:
      self.errorMsg.show()
      self.errorMsg.setText(QCoreApplication.translate("LOGIN","INVALID_USERNAME"))
      return False


  def createUser(self):
    username = self.fldUsername.text()
    if len(username) < 0:
      self.errorMsg.setText(QCoreApplication.translate("LOGIN","USER_NAME_TOO_SHORT"))
      return False

    profileName = self.fldProfileName.text()
    if len(profileName) < 0:
      self.errorMsg.setText(QCoreApplication.translate("LOGIN","PROFILE_NAME_TOO_SHORT"))
      return False

    password = self.fldPassword.text()
    pwdConfirmation = self.fldConfirmPassword.text()

    if password != pwdConfirmation:
      self.errorMsg.show()
      self.errorMsg.setText(QCoreApplication.translate("LOGIN","PWD_NOT_MATCH"))
      return False

    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashedPwd = bcrypt.hashpw(password, salt)
    userUUID = str(uuid.uuid4())
    self.db.config.insert({"localUsername": username, "profileName":profileName , "pwd": hashedPwd, "uid":userUUID })

    self.user = {"localUsername":username,"profileName":profileName ,"uid":userUUID}
    self.btnLogin.clicked.disconnect()
    self.btnLogin.clicked.connect(lambda: self.login())

    self.openDashboardWindow()


  #
  # DASHBOARD PAGE methods
  #
  def openDashboardWindow(self):
    self.showMenuBtn()
    self.showLastAnalysis()

    self.btnMainMenu.setDisabled(False)
    self.stackedWidget.setCurrentIndex(1)


  def showLastAnalysis(self):
    self.removeLines(self.analysisGridLayout)
    analysisCursor = self.db.analysis.find({"owner":self.user['uid']})
    analysisCursor.sort("lastUpdate",-1)
    analysisCursor.limit(5)
    if analysisCursor.count() > 0:
      for analysis in analysisCursor:
        self.addLastAnalysisLine(analysis)
    else:
      noAnalysisLabel = QLabel(QCoreApplication.translate("DASHBOARD","NO_ANALYSIS"))
      self.analysisGridLayout.addWidget(noAnalysisLabel, 1, 0, 1, 5, Qt.AlignCenter)


  def addLastAnalysisLine(self, analysis):
    rowIndex = self.analysisGridLayout.rowCount()

    sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)

    sizePolicyCompact = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    # Analysis Label
    widgetLabel = QLabel(self.setAnalysisLabel(analysis))
    widgetLabel.setSizePolicy(sizePolicy)
    self.analysisGridLayout.addWidget(widgetLabel, rowIndex, 0, 1, 1)

    widgetType = QPushButton(qta.icon(SUPPORTED_VEHICLE_ICON[analysis['vehicleType']]),"")
    widgetType.setDisabled(True)
    widgetType.setSizePolicy(sizePolicyCompact)
    self.analysisGridLayout.addWidget(widgetType, rowIndex, 1, 1, 1, Qt.AlignCenter)

    widgetDate = QLabel(str(analysis['lastUpdate']))
    widgetDate.setSizePolicy(sizePolicy)
    self.analysisGridLayout.addWidget(widgetDate, rowIndex, 2, 1, 1)

    widgetIcon = QPushButton(qta.icon(PRIVACY_ICON[analysis['privacy']]),"")
    widgetIcon.setDisabled(True)
    widgetIcon.setSizePolicy(sizePolicyCompact)
    self.analysisGridLayout.addWidget(widgetIcon, rowIndex, 3, 1, 1, Qt.AlignCenter)

    widgetOpen = QPushButton(qta.icon("fa.upload",color='white'),QCoreApplication.translate("GENERIC","LOAD"))
    widgetOpen.setProperty("cssClass","btn-primary")
    widgetOpen.setCursor(Qt.PointingHandCursor)
    widgetOpen.clicked.connect(lambda: self.loadAnalysis(analysis['id']))
    self.analysisGridLayout.addWidget(widgetOpen, rowIndex, 4, 1, 1, Qt.AlignCenter)


  def loadAnalysis(self, analysisId):
    analysisCursor = self.db.analysis.find({"id": analysisId, "owner":self.user['uid']}, {"_id":0})
    if analysisCursor.count() == 1:
      self.analysis = analysisCursor[0]
      # Reset session, display options...
      self.initSessionObject()
      self.initDisplayObject()
      self.showRightMenu(True)
      # Set bus presets
      # Load commands & definitions
      # Signals
      self.loadSignals()
      self.db.analysis.update({"id": analysisId}, {"$set":{"lastUpdate":time.time()}})
      self.openAnalysisWindow()

  def setAnalysisLabel(self, analysis = None):
    spacer = ("<br />"," - ","","<br />")
    if analysis == None:
      analysis = self.analysis
      spacer = (" ("," - ",")"," : ")

    label = ""
    if analysis['manufacturer'] != None:
      label += "<b>" + analysis['manufacturer'] + "</b>"
    else:
      label += "<b><i>" + QCoreApplication.translate("ANALYSIS","UNKNOWN_MANUFACTURER") + "</i></b>"
    if analysis['model'] != None:
      label += " <b>" + analysis['model'] + "</b>"
    else:
      label += " <i>" + QCoreApplication.translate("ANALYSIS","UNKNOWN_MODEL") + "</i>"

    if analysis['year'] != None or analysis['engine'] != None:
      label += spacer[0]
    if analysis['year'] != None:
      label += analysis['year']
    if analysis['year'] != None and analysis['engine'] != None:
      label += spacer[1]
    if analysis['engine'] != None:
      label += QCoreApplication.translate("ANALYSIS", analysis['engine'])
      if analysis['year'] != None or analysis['engine'] != None:
        label += spacer[2]
    if analysis['VIN'] != None:
      label += spacer[3]
      label +=  analysis['VIN']

    return label


  #
  # ANALYSIS PAGE methods
  #
  def loadSignals(self):
    self.signals = {}
    signalSrc = self.comboSignalsSrc.currentData()
    if signalSrc == None:
      signalSrc = SIGNALS.DEFAULT

    query = {"manufacturer":self.analysis['manufacturer']}

    if signalSrc == SIGNALS.SRC['ANALYSIS']:
      query['analysis'] = self.analysis['id']
      query['owner'] = self.user['uid']
    if signalSrc <= SIGNALS.SRC['ENGINE_CODE'] :
      query['engineCode'] = self.analysis['engineCode']
    if signalSrc <= SIGNALS.SRC['MODEL'] :
      query['model'] = self.analysis['model']
    signalsCursor = self.db.signals.find(query,{"_id":0})
    if signalsCursor.count() > 0:
      for signal in signalsCursor:
        if not signal['type'] in self.signals:
          self.signals[signal['type']] = {}
        if not signal['preset'] in self.signals[signal['type']]:
          self.signals[signal['type']][signal['preset']] = {}
        if not signal['id'] in self.signals[signal['type']][signal['preset']]:
          self.signals[signal['type']][signal['preset']][signal['id']] = []

        self.signals[signal['type']][signal['preset']][signal['id']].append(signal)
    self.frameModel.updateSignals(self.signals)

  def openAnalysisWindow(self):
    # Main buttons

    # Analysis info
    self.vehicleTitle.setText(self.setAnalysisLabel())
    self.btnEditVehicle.setIcon(qta.icon("fa5s.edit", color='white'))

    # Right menu
    self.comboSignalsSrc.setCurrentIndex(self.display['signalSrc'])

    # ID filter
    headerItem  = QTreeWidgetItem()
    item    = QTreeWidgetItem()
    self.idFilter.sortItems(0,Qt.AscendingOrder)
    self.idFilter.clicked.connect(lambda: self.checkActiveIdFilters())

    # Devices dialog
    self.stackedWidget.setCurrentIndex(2)


  def filterHideId(self, cells):
    if len(cells) > 0:
      r = []
      for cell in cells:
        if not cell['row'] in r:
          lbl = "c_%s%s"%(self.frameModel.filteredFrames[cell['row']]['presetLabel'], self.frameModel.filteredFrames[cell['row']]['id'])
          if lbl in self.filterWidgets:
            self.filterWidgets[lbl].setCheckState(0,Qt.Unchecked)
          r.append(cell['row'])
      self.msgTable.clearSelection()
      self.checkActiveIdFilters()

  def filterShowId(self, cells):
    if len(cells) > 0:
      r = []
      for widget in self.filterWidgets:
        self.filterWidgets[widget].setCheckState(0,Qt.Unchecked)
      for cell in cells:
        if not cell['row'] in r:
          lbl = "c_%s%s"%(self.frameModel.filteredFrames[cell['row']]['presetLabel'], self.frameModel.filteredFrames[cell['row']]['id'])
          if lbl in self.filterWidgets:
            self.filterWidgets[lbl].setCheckState(0,Qt.Checked)
          r.append(cell['row'])
      self.msgTable.clearSelection()
      self.checkActiveIdFilters()


  def unFilterId(self):
    for widget in self.filterWidgets:
      self.filterWidgets[widget].setCheckState(0,Qt.Checked)
    self.msgTable.clearSelection()
    self.checkActiveIdFilters()


  def maskStaticFrames(self, state):
    if state == True:
      self.comboKeepDuration.setDisabled(False)
      self.maskStatic = self.comboKeepDuration.currentData()

    else:
      self.comboKeepDuration.setDisabled(True)
      self.maskStatic = False

  def updateStaticDuration(self):
    self.maskStatic = self.comboKeepDuration.currentData()

  def snapBus(self, clear=False):
    for bus in self.session['frameHistory']:
      for id in self.session['frameHistory'][bus]:
        if clear == False:
          for i in self.session['frameHistory'][bus][id]['values']:
            self.session['frameHistory'][bus][id]['snapValues'][i] = self.session['frameHistory'][bus][id]['values'][i].copy()
        else:
          self.session['frameHistory'][bus][id]['snapValues'] = {}

  #
  # SESSION Methods
  #
  def initSession(self):
    btnToDisabled = [self.btnSessionSave, self.btnSessionForensic,self.btnSessionReplay]
    self.toggleButtonStatus(btnToDisabled, "btn-disabled", True)

    btnToEnabled = [self.btnSessionPause,self.btnSessionLive, self.btnSessionRec]
    self.toggleButtonStatus(btnToEnabled)

    self.lblSessionFrames.setText("0")
    self.lblSessionName.setText(QCoreApplication.translate("MainWindow","NO_SESSION"))
    self.initSessionObject()

  def unlockSessionBtn(self):
    if self.session['owner'] == None or self.session['owner'] == self.user['uid']:
      btnToEnabled = [self.btnSessionSave, self.btnSessionForensic,self.btnSessionReplay]
    else:
      btnToEnabled = [self.btnSessionForensic,self.btnSessionReplay]
    self.toggleButtonStatus(btnToEnabled)

  def toggleButtonStatus(self, buttonList, newClass="btn-primary", isDisabled = False):
    for btn in buttonList:
      btn.setDisabled(isDisabled)
      btn.setProperty("cssClass",newClass)
      btn.setStyle(btn.style())

  def sessionSetActiveBtn(self, btnWidget):
    sessionBtn = [self.btnSessionReplay, self.btnSessionNew, self.btnSessionRec,
                  self.btnSessionPause,self.btnSessionForensic,
                  self.btnSessionLive,self.btnSessionLoad,self.btnSessionSave]
    for btn in sessionBtn:
      if btn.isEnabled() and btn != btnWidget:
        btn.setProperty("cssClass","btn-primary")
        btn.setStyle(btn.style())
      elif not btn.isEnabled() and btn != btnWidget:
        btn.setProperty("cssClass","btn-disabled")
        btn.setStyle(btn.style())
    btnWidget.setProperty("cssClass","btn-success")
    btnWidget.setStyle(btnWidget.style())

  def sessionNew(self):
    msgBox = QMessageBox()
    msgBox.setText(QCoreApplication.translate("SESSION","SESSION_SET_NEW"))
    msgBox.setWindowTitle(QCoreApplication.translate("SESSION","SESSION_SET_NEW"))
    msgBox.setInformativeText(QCoreApplication.translate("SESSION","SESSION_SET_NEW_DETAILS"))
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msgBox.setDefaultButton(QMessageBox.Ok)
    self.centerMsg(msgBox)
    choice = msgBox.exec()

    if choice == QMessageBox.Ok:
      isOnPause = False
      if self.session["mode"] == SESSION_MODE.IDLE:
        isOnPause = True
      self.sessionPause()
      # Clear / update filters
      self.initSession()
      self.idFilter.clear()
      self.filterWidgets = {}
      self.frameModel.lastRefresh = 0
      self.frameModel.clearElt()
      self.frameModel.sort(self.frameModel.sortCol, self.frameModel.sortOrder)

      if isOnPause == True:
        self.sessionPause()
      else:
        self.sessionLive()

  def sessionSave(self):
    if self.session['id'] == None:
      self.session['id'] = str(uuid.uuid4())
      self.session['createTime'] = time.time()
      self.session['owner'] = self.user['uid']

    self.db.sessions.update({"id": self.session['id']},
                            {"analysis": self.analysis['id'], "comment": self.session['comment'],
                              "id": self.session['id'], "name": self.session['name'], "owner": self.user['uid'],
                              "updateTime": time.time(), "share": self.session['share'],
                              "createTime":self.session['createTime']}, True)
    msgGroupList = []
    self.db.frames.remove({"session": self.session['id']})
    progress = self.openProgressDialog("SAVE_SESSION","SAVE_SESSION_DETAILS",len(self.session['frames']))
    i = 1
    for msg in self.session['frames']:
      i += 1
      msg['msg'] = list(msg['msg'])
      progress.setValue(i)
      QApplication.processEvents()
      msgGroupList.append({"session":self.session['id'], "msg":{
                            "id":msg['id'], "ts":msg['ts'], "len":msg['len'], "type":msg['type'],
                            "extendedId":msg['extendedId'],"msg":msg['msg'], "preset":msg['preset'],
                            "presetLabel":msg['presetLabel'], "busName": msg['busName']}})

      if len(msgGroupList) > FRAME_RECORD_GROUP_LIMIT:
        try:
          self.db.frames.insert_many(msgGroupList)
        except BulkWriteError as bwe:
          pprint(bwe.details)
        msgGroupList = []
    if len(msgGroupList) > 0:
      try:
        self.db.frames.insert_many(msgGroupList)
      except BulkWriteError as bwe:
        pprint(bwe.details)
    progress.close()

    self.lblSessionName.setText(self.session['name'])

  def sessionLive(self):
    if self.session["mode"] <= SESSION_MODE.IDLE:
      self.frameModel.clearElt()
    self.session["mode"] = SESSION_MODE.LIVE
    self.sessionSetActiveBtn(self.btnSessionLive)
    for id in self.activeBus:
      if not 'capturing' in self.activeBus[id]['threads']:
        self.activeBus[id].startCapturing()

  def sessionPause(self):
    self.session["mode"] = SESSION_MODE.IDLE
    self.sessionSetActiveBtn(self.btnSessionPause)
    for id in self.activeBus:
      if 'capturing' in self.activeBus[id]['threads']:
        self.activeBus[id].stopCapturing()

  def sessionForensic(self):
    self.session["mode"] = SESSION_MODE.FORENSIC
    self.sessionSetActiveBtn(self.btnSessionForensic)
    for id in self.activeBus:
      if 'capturing' in self.activeBus[id]['threads']:
        self.activeBus[id].stopCapturing()

    self.frameModel.clearElt()

    for msg in self.session['frames']:
      self.appendNewBusMsg(msg)
    self.frameModel.sort(self.frameModel.sortCol, self.frameModel.sortOrder)

  def sessionRecord(self):
    if self.session["mode"] == SESSION_MODE.FORENSIC:
      self.frameModel.clearElt()
    self.sessionSetActiveBtn(self.btnSessionRec)
    self.session["mode"] = SESSION_MODE.RECORDING
    for id in self.activeBus:
      if not 'capturing' in self.activeBus[id]['threads']:
        self.activeBus[id].startCapturing()

  def stopActiveThreads(self):
    self.session["mode"] = SESSION_MODE.RECORDING


  #
  # Commands
  #
  def showRightMenu(self, force=False):
    if force!=False:
      currentStatus = not force
    else:
      currentStatus = self.rightMenu.isVisible()
    if currentStatus == True:
      self.rightMenu.setVisible(False)
      self.btnShowRightMenu.setText(QCoreApplication.translate("MainWindow","SHOW_MENU"))
      self.btnShowRightMenu.setIcon(qta.icon('ei.eye-open', options=[{"color":"white","color_disabled":"black"}]))
    else:
      self.rightMenu.setVisible(True)
      self.btnShowRightMenu.setText(QCoreApplication.translate("MainWindow","HIDE_MENU"))
      self.btnShowRightMenu.setIcon(qta.icon('ei.eye-close', options=[{"color":"white","color_disabled":"black"}]))

  def haltSession(self):
    self.session['mode'] = SESSION_MODE.IDLE
    self.activeBus[id].stopCapture()

  def stopSessionRecording(self):
    for id in self.activeBus:
      self.activeBus[id].stopCapture()

  def switchBus(self, busId, dialog = None):
    if self.interfaces.bus[busId]['type'] == "can":
      if self.interfaces.bus[busId]['active'] == True:
        logging.debug("Stopping bus %s"%busId)
        self.activeBus[busId].closeBus()
        if dialog != None:
          dialog.lockBusParams(busId, 0)
      else:
        logging.debug("Starting bus %s"%busId)
        self.activeBus[busId] = BusCAN(self.interfaces.bus[busId], self.appSignals, self.session)
        if dialog != None:
          dialog.lockBusParams(busId, 1)

  #
  # Frame management
  #
  def checkActiveIdFilters(self):
    filterList = {}
    for type in self.session['idList']:
      filterList[type] = []
      for id in self.session['idList'][type]:
        if self.filterWidgets["c_" + type + str(id)].checkState(0) == False:
          filterList[type].append(id)
    if filterList != self.session['filters']:
      self.session['filters'] = filterList
      self.frameModel.updateFilters(self.session['filters'])


  def checkIfFilterExists(self, msg):
    if not msg['presetLabel'] in self.session['idList']:
      self.session['idList'][msg['presetLabel']] = []
      self.session['filters'][msg['presetLabel']] = []
      self.frameModel.filters[msg['presetLabel']] = []

      # Gen Parent in Tree view
      self.filterWidgets['p_' + msg['presetLabel']] = QTreeWidgetItem(self.idFilter)
      self.filterWidgets['p_' + msg['presetLabel']].setText(0, msg['presetLabel']) # TRANSLATE !
      self.filterWidgets['p_' + msg['presetLabel']].setExpanded(True)
      self.filterWidgets['p_' + msg['presetLabel']].setFlags(self.filterWidgets['p_' + msg['presetLabel']].flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

    if not msg['id'] in self.session['idList'][msg['presetLabel']]:
      self.session['idList'][msg['presetLabel']].append(msg['id'])
      id = "c_" + msg['presetLabel'] + str(msg['id'])
      self.filterWidgets[id] = QTreeWidgetItem(self.filterWidgets['p_' + msg['presetLabel']])
      self.filterWidgets[id].setFlags(self.filterWidgets[id].flags() | Qt.ItemIsUserCheckable)
      if msg['extendedId']==True:
        self.filterWidgets[id].setText(0, "{0:#0{1}x}".format(msg['id'],10))
      else:
        self.filterWidgets[id].setText(0, "{0:#0{1}x}".format(msg['id'],5))
      self.filterWidgets[id].setCheckState(0, Qt.Checked)


  def forwardBusMsg(self, dst, msg):
    if self.interfaces.bus[dst]['active'] == True:
      self.activeBus[dst].sendMsg(msg, raw=True)


  # Add new message to frame Tables
  def appendNewBusMsg(self, msg):
    # If record selected, add frame to session
    if self.session['mode'] == SESSION_MODE.RECORDING:
      if len(self.session['frames']) == 0:
        self.unlockSessionBtn()
      self.session['frames'].append(msg.copy())
      self.lblSessionFrames.setText(str(len(self.session['frames'])))

    # Live mode only, overwrite ID & apply static mask
    if self.session['mode'] > SESSION_MODE.IDLE:
      timer = time.time()
      for idx in range(0,len(self.frameModel['frames'])):
        if self.frameModel['frames'][idx]['id'] == msg['id'] and self.frameModel['frames'][idx]['preset'] == msg['preset']:
            self.frameModel['frames'].pop(idx)
            break

      if self.maskStatic != False:
        for idx in range(0,len(self.frameModel['frames'])):
          if self.frameModel['frames'][idx]['lastChange'] + self.maskStatic < timer:
            self.frameModel['frames'].pop(idx)
            break

    # Analyse message to hightlight changing values
    msg = self.analyseMsg(msg)

    # Signals & ecu
    if msg['type'] in self.signals and msg['preset'] in self.signals[msg['type']] and msg['id'] in self.signals[msg['type']][msg['preset']]:
      ecu = []
      for elt in self.signals[msg['type']][msg['preset']][msg['id']]:
        if not elt['ecu'] in ecu and len(elt['ecu']) > 0:
          ecu.append(elt['ecu'])
      msg['ecu'] = "<br />".join(ecu)
    else:
      msg['ecu'] = ""

    if msg['type'] in self.signals and msg['preset'] in self.signals[msg['type']] and msg['id'] in self.signals[msg['type']][msg['preset']]:
      signals = []
      for elt in self.signals[msg['type']][msg['preset']][msg['id']]:
        signals.append(self.parseSignal(elt, msg['msg']))
      msg['signals'] = "<br>".join(signals)
    else:
      msg['signals'] = ""

    if self.session['mode'] != SESSION_MODE.IDLE:
      self.checkIfFilterExists(msg)
      msg['ascii'] = ""
      msg['msgColored'] = ""
      timer = time.time()
      for i in range(0, msg['len']):
        b = "{0:0{1}x}".format(msg['bytes'][i]['value'],2)
        if msg['bytes'][i]['value'] >= 32 and msg['bytes'][i]['value'] <= 126:
          a = chr(msg['bytes'][i]['value'])
        else:
          a = "."
        if msg['bytes'][i]['isChanged'] == True or (msg['bytes'][i]['prevByte'] != msg['bytes'][i]['value'] and msg['bytes'][i]['lastChange'] + FRAME_CHANGE_TIME > timer):
          msg['msgColored'] += "<span style='color:#FF0000'>%s</span> "%b
          msg['ascii'] += "<span style='color:#FF0000'>%s</span>"%a
        else:
          msg['msgColored'] += "%s "%b
          msg['ascii'] += a

      if not( self.maskStatic != False and msg['lastChange'] + self.maskStatic < timer and self.session['mode'] > SESSION_MODE.IDLE):
        self.frameModel.addElt(msg)

      if self.signalFrameSrc != None:
        if self.signalFrameSrc['id'] == msg['id'] and self.signalFrameSrc['preset'] == msg['preset']:
          self.appSignals.signalEditorRefresh.emit(msg)


  def analyseMsg(self, msg):
    id = str(msg['id'])
    if not msg['preset'] in self.session['frameHistory']:
      self.session['frameHistory'][msg['preset']] = {}

    if not id in self.session['frameHistory'][msg['preset']]:
      self.session['frameHistory'][msg['preset']][id] = {"lastValue": [], "values": {}, "snapValues": {},
                                    "lastTs":0, "lastChange":0, "count":0, "prevBytes":[], "lastChanges":[]}



    self.session['frameHistory'][msg['preset']][id]['count'] += 1
    msg['count'] = self.session['frameHistory'][msg['preset']][id]['count']

    if self.session['frameHistory'][msg['preset']][id]['lastTs'] == 0:
      msg['period'] = 0
    else:
      msg['period'] = int((msg['ts'] - self.session['frameHistory'][msg['preset']][id]['lastTs'])*1000)

    if msg['period'] < 0:
      msg['period'] = 0

    self.session['frameHistory'][msg['preset']][id]['lastTs'] = msg['ts']

    msgDetails = self.analyseMsgBytes(id, msg)

    msg['bytes'] = msgDetails[0]
    msg['hasChangedValue'] = msgDetails[1]

    if msg['hasChangedValue'] == True:
      self.session['frameHistory'][msg['preset']][id]['lastChange'] = msg['ts']
    msg['lastChange'] = self.session['frameHistory'][msg['preset']][id]['lastChange']

    self.session['frameHistory'][msg['preset']][id]['lastValue'] = msg['msg']

    return msg


  def analyseMsgBytes(self, id, msg):
    results = []
    hasChangedValue = False

    prevValues = self.session['frameHistory'][msg['preset']][id]

    for i in range(0, len(msg['msg'])):
      byteDetails = {}
      byteRef = str(i)
      byteDetails['value'] = msg['msg'][i]

      if len(prevValues["lastValue"]) >= i+1:
        if prevValues["lastValue"][i] != msg['msg'][i]:
          if not byteRef in prevValues['snapValues'] or not msg['msg'][i] in prevValues['snapValues'][byteRef]:
              byteDetails['isChanged'] = True
              byteDetails['lastChange'] = time.time()
              byteDetails['prevByte'] = prevValues["lastValue"][i]
              hasChangedValue = True
          else:
            byteDetails['isChanged'] = False
            byteDetails['prevByte'] = prevValues["prevBytes"][i]
            byteDetails['lastChange'] = prevValues["lastChanges"][i]
        else:
          byteDetails['isChanged'] = False
          byteDetails['prevByte'] = prevValues["prevBytes"][i]
          byteDetails['lastChange'] = prevValues["lastChanges"][i]
      else:
        byteDetails['isChanged'] = True
        byteDetails['prevByte'] = None
        byteDetails['lastChange'] = time.time()

        self.session['frameHistory'][msg['preset']][id]['prevBytes'].append(None)
        self.session['frameHistory'][msg['preset']][id]['lastChanges'].append(None)
        hasChangedValue = True
      self.session['frameHistory'][msg['preset']][id]['prevBytes'][i] = byteDetails['prevByte']
      self.session['frameHistory'][msg['preset']][id]['lastChanges'][i] = byteDetails['lastChange']

      if not byteRef in prevValues['values']:
        self.session['frameHistory'][msg['preset']][id]['values'][byteRef] = []

      if not msg['msg'][i] in self.session['frameHistory'][msg['preset']][id]['values'][byteRef]:
        self.session['frameHistory'][msg['preset']][id]['values'][byteRef].append(msg['msg'][i])

      results.append(byteDetails)
    return [results, hasChangedValue]


  def parseSignal(self, signal, msg):
    bitArray = ''.join(format(byte, '08b') for byte in msg)
    bitLen = int(signal['len'])
    bit = bitArray[int(signal['start']): int(signal['start']) + int(signal['len'])]
    #if signal['endian'] == 0:
    #  bit = bit[::-1]
    if signal['signed'] == True:
      value = BitArray(bin=bit).int
    else:
      value = BitArray(bin=bit).uint

    if signal['factor'] != None and len(signal['factor']) > 0:
      value *= float(signal['factor'])
    if signal['offset'] != None and len(signal['offset']) > 0:
      value += float(signal['offset'])
    if signal['min'] != None and len(signal['min']) > 0:
      if value < float(signal['min']):
        value = float(signal['min'])
    if signal['max'] != None and len(signal['max']) > 0:
      if value > float(signal['max']):
        value = float(signal['max'])
    value = round(value,3)
    if len(signal['values']) > 0:
      for v in signal['values']:
        if int(v['value']) == value:
          value = v['label']
          break
    str_ = "<b>" + signal['name'] + " : </b>"
    str_ += str(value)

    if signal['unit'] != None:
      str_ += " " + signal['unit']
    return str_
    # Filters Update
  #
  # Dialogs -
  #

  # Progress bar
  def openProgressDialog(self, title="", text="", max=100):
    progress = QProgressDialog("", "", 0, 0, self)
    progress.setCancelButton(None)
    progress.setWindowModality(Qt.WindowModal)
    progress.setWindowTitle(QCoreApplication.translate("GENERIC",title))
    progress.setLabelText(QCoreApplication.translate("GENERIC",text))
    progress.setMinimum(0)
    progress.setMaximum(max)
    progress.setAutoClose(True)
    progress.show()
    return progress


  #New analysis management
  def openAnalysisParamsDialog(self, newAnalysis=True):
    dlg = AnalysisParamsDialog(self, newAnalysis)
    dlg.setWindowFlags(Qt.Dialog)
    self.setDialogSize(dlg, 460, 200)
    dlg.setStyleSheet(self.cssContent)
    dlg.exec_()


  #Devices management
  def openDevicesDialog(self):
    dlg = DevicesDialog(self.interfaces)
    dlg.setWindowFlags(Qt.Dialog)
    self.setDialogSize(dlg, 800, 200)
    dlg.setStyleSheet(self.cssContent)
    dlg.exec_()


  # Bus management
  def openBusDialog(self, busType = None):
    dlg = BusDialog(self, busType)
    dlg.setWindowFlags(Qt.Dialog)
    self.setDialogSize(dlg, 800, 400)
    dlg.setStyleSheet(self.cssContent)
    dlg.exec_()


  # Session management
  def openSessionSaveDialog(self):
    self.sessionPause()
    dlg = SessionDialog(self, saveSession = True)
    dlg.setWindowFlags(Qt.Dialog)
    self.setDialogSize(dlg, 640, 260)
    dlg.setStyleSheet(self.cssContent)
    r = dlg.exec_()
    if r == 1:
      self.sessionSave()


  def openSessionLoadDialog(self):
    self.sessionPause()
    dlg = SessionDialog(self, loadSession = True)
    dlg.setWindowFlags(Qt.Dialog)
    self.setDialogSize(dlg, 640, 300)
    dlg.setStyleSheet(self.cssContent)
    r = dlg.exec_()
    if r == 1:
      sessionCursor = self.db.sessions.find({"id": self.session['id']}, {"_id":0})
      progress = None
      self.idFilter.clear()
      self.filterWidgets = {}
      if sessionCursor.count() == 1:
        self.initSessionObject()
        for elt in sessionCursor[0]:
          self.session[elt] = sessionCursor[0][elt]
        # Load frames
        framesCursor = self.db.frames.find({"session": self.session['id']}, {"_id":0})
        if framesCursor.count() > 0:
          progress = self.openProgressDialog("LOAD_SESSION","LOAD_SESSION_DETAILS",framesCursor.count())
          i = 1
          self.session['mode'] = SESSION_MODE.RECORDING
          for frame in framesCursor:
            self.appendNewBusMsg(frame['msg'])
            progress.setValue(i)
            i+= 1
            QApplication.processEvents()

          self.sessionForensic()
        self.session['mode'] = SESSION_MODE.FORENSIC

      if self.session['owner'] != self.user["uid"]:
        btnClass = "btn-disabled"
        isDisabled = True
      else:
        btnClass = "btn-primary"
        isDisabled = False

      btnToUpdate = [self.btnSessionSave, self.btnSessionRec, self.btnSessionLive,
                      self.btnSessionPause]
      self.toggleButtonStatus(btnToUpdate, btnClass, isDisabled)
      self.toggleButtonStatus([self.btnSessionReplay,self.btnSessionForensic])

      self.lblSessionName.setText(self.session['name'])
      self.lblSessionFrames.setText(str(len(self.session['frames'])))

      self.frameModel.lastRefresh = 0
      self.frameModel.clearElt()
      self.frameModel.sort(self.frameModel.sortCol, self.frameModel.sortOrder)
      if progress != None:
        progress.close()
      self.sessionForensic()


  # Message replay
  def openReplayDialog(self, mode=REPLAY.SESSION, cells=None, initMsg = [], startPause=0, endPause=0, hasFuzzing=False):
    if 'replay' in self.activeWindows:
      return False

    if self.session['mode'] == SESSION_MODE.RECORDING:
      self.sessionPause()

    frames = None
    if mode == REPLAY.SELECTION:
      if len(cells) == 0:
        return None
      else:
        r = []
        frames = []
        for cell in cells:
          if not cell['row'] in r:
            frames.append(self.frameModel.filteredFrames[cell['row']])
            r.append(cell['row'])
    elif mode == REPLAY.COMMAND:
      frames = cells

    self.activeWindows['replay'] = ReplayDialog(self, mode, frames, initMsg, startPause, endPause, hasFuzzing)
    self.activeWindows['replay'].setWindowFlags(Qt.Dialog)
    self.setDialogSize(self.activeWindows['replay'], 640, 320)
    self.activeWindows['replay'].setStyleSheet(self.cssContent)
    self.activeWindows['replay'].setWindowTitle(QCoreApplication.translate("REPLAY","REPLAY_WINDOW"))
    self.activeWindows['replay'].setWindowModality(Qt.NonModal)
    self.activeWindows['replay'].show()
    r = self.activeWindows['replay'].exec_()
    if r == REPLAY.UPDATE_SESSION:
      self.lblSessionFrames.setText(str(len(self.session['frames'])))
      self.idFilter.clear()
      self.filterWidgets = {}
      self.frameModel.lastRefresh = 0
      # Reimport data
      frames = self.session['frames'].copy()
      self.initSessionObject()
      self.sessionRecord()
      for f in frames:
        self.appendNewBusMsg(f)
      self.frameModel.clearElt()
      self.frameModel.sort(self.frameModel.sortCol, self.frameModel.sortOrder)
      self.sessionForensic()
    del self.activeWindows['replay']


  # Signal editor
  def openSignalDialog(self, frameId=None):
    if frameId != None:
      src = self.frameModel.filteredFrames[frameId.row()]
      self.signalFrameSrc =  {"id":src['id'], "preset":src['preset']}

      dlg = SignalDialog(self, src)
      dlg.setWindowFlags(Qt.Dialog)
      self.setDialogSize(dlg, 800, 320)
      dlg.setStyleSheet(self.cssContent)
      r = dlg.exec_()
      self.signalFrameSrc = None


  # Command editor
  def openCmdEditorDialog(self, cmdId=False):
    if 'cmdEditor' in self.activeWindows:
      return False
    self.activeWindows['cmdEditor'] = CommandDialog(self, cmdId)
    self.setDialogSize(self.activeWindows['cmdEditor'], 1024, 320)
    self.activeWindows['cmdEditor'].setStyleSheet(self.cssContent)
    self.activeWindows['cmdEditor'].setWindowTitle(QCoreApplication.translate("CMD","CMD_EDITOR"))
    self.activeWindows['cmdEditor'].setWindowModality(Qt.NonModal)
    self.activeWindows['cmdEditor'].show()
    self.activeWindows['cmdEditor'].exec_()
    del self.activeWindows['cmdEditor']


  # Notepad
  def openNotesDialog(self):
    if 'notepad' in self.activeWindows:
      return False
    self.activeWindows['notepad'] = NotepadDialog(self)
    self.setDialogSize(self.activeWindows['notepad'], 800, 320)
    self.activeWindows['notepad'].setStyleSheet(self.cssContent)
    self.activeWindows['notepad'].setWindowTitle(QCoreApplication.translate("GENERIC","NOTEPAD"))
    self.activeWindows['notepad'].setWindowModality(Qt.NonModal)
    self.activeWindows['notepad'].show()
    self.activeWindows['notepad'].exec_()
    del self.activeWindows['notepad']


  def setDialogSize(self, dialog, width=800, height=600, top=90):
    dialog.setGeometry(dialog.x(), dialog.y(), width, height)
    dialog.move(self.x() + (self.width() - dialog.width()) / 2,  self.y() + top)


  def centerMsg(self, msgWidget):
    msgWidget.setGeometry(self.x(), self.y(), 300, 180)
    msgWidget.move(self.x() + (self.width() - msgWidget.width()) / 2,
                   self.y() + (self.height() - msgWidget.height()) / 2)


  # Clean Ctrl+C / Ctrl+X commands to clean HTML tags
  def keyPressEvent(self, event):
    if event.matches(QKeySequence.Copy) or event.matches(QKeySequence.Cut):
      if self.msgTable.hasFocus():
        s = self.msgTable.selectionModel().selection().indexes()
        indexes = self.msgTable.selectionModel().selection().indexes()
        for index in sorted(indexes):
          print('Cell %d/%s is selected' % (index.row(), index.column()))
        #print(s.column())

      #QApplication.clipboard().setText("YO")
      #event.accept()
    event.ignore()
  # -- Copy/Cut hack


  #
  # Close Event - shut down every running  threads
  #
  def closeEvent(self, event):
    self.killRunningThreads()
    event.accept()

  def killRunningThreads(self):
    for id in self.activeBus:
      for threadName in self.activeBus[id]['threads']:
        self.activeBus[id]['threadStopManager'][threadName].set()
        if threadName in self.activeBus[id]['threads']:
          self.activeBus[id]['threads'][threadName].join()

    for threadName in self.threadStopManager:
      self.threadStopManager[threadName].set()
      if threadName in self.threads:
        self.threads[threadName].join()

    for windowName in self.activeWindows:
      self.activeWindows[windowName].close()


if __name__ == '__main__':
  app = QApplication(sys.argv)
  # Internationalization support
  translator = QTranslator()
  locale = QLocale.system().name()
  translations_found = translator.load("./i18n/%s.qm"%locale)
  if not translations_found:
    translator.load("./i18n/en_EN.qm")
  app.installTranslator(translator)

  window = MainWindow()
  # On application close, clean stuff
  atexit.register(window.killRunningThreads)
  window.show()

  # Start the event loop.
  app.exec_()
