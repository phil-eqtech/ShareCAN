from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import qtawesome as qta
import time
import threading

from modules.Constants import *
from ui.ModelDialog import ModelDialog
from ui.ReplayForm import Ui_REPLAY


class ReplayUi(QWidget, Ui_REPLAY):
  def __init__(self):
   super().__init__()
   self.setupUi(self)


class ReplayDialog(ModelDialog):
  def __init__(self, refWindow, mode=REPLAY.SESSION, frames=None, initMsg=[], startPause=0, endPause=0, hasFuzzing=False):
    super().__init__()

    self.getMainVariables(refWindow)

    # Close btn
    self.closeBtn = QPushButton()
    self.closeBtn.setIcon(qta.icon('fa.close',color='white'))
    self.closeBtn.setText(QCoreApplication.translate("DIALOG", "CLOSE"))
    self.closeBtn.setProperty("cssClass","btn-danger")
    self.closeBtn.setCursor(Qt.PointingHandCursor)
    self.closeBtn.clicked.connect(lambda: self.closeDialog())
    self.setBottomButtons(self.closeBtn)

    # Loading body template
    self.dialogTitle.setText(QCoreApplication.translate("REPLAY","REPLAY_TITLE"))
    self.body = ReplayUi()
    self.dialogBody.addWidget(self.body)

    # Load selected frames
    self.replayMode = mode

    self.smartMode = False
    self.frames = []
    self.initMsg = initMsg
    self.startPause = startPause
    self.endPause = endPause
    self.hasFuzzing = hasFuzzing

    # Replay variables
    self.framesBuffer = []

    self.progressIndex = 0
    self.progressLastUpdate = 0
    self.threadStopManager['replay'] = threading.Event()
    self.replayLock = threading.Event()

    self.loop = False
    self.timer = None
    self.feedback = REPLAY.FEEDBACK_NONE

    self.replayCurrentFrame = 0
    self.replayIsPaused = False

    if self.replayMode == REPLAY.SESSION:
      self.frames = self.session['frames']
    elif self.replayMode == REPLAY.SELECTION:
      orderedFrames= sorted(frames,
                            key=lambda k: (k['ts']))
      self.frames = orderedFrames
    elif self.replayMode == REPLAY.COMMAND:
      self.frames = frames

    self.sliceNumber = 0
    self.slices = [{},{},{}]

    # Defining required BUS
    self.requiredBusWidgets = []
    self.requiredBus = {}
    self.setBus = {}

    for frame in self.frames:
      if frame['busName'] + " - " in frame['presetLabel']:
        busName = frame['presetLabel']
      else:
        busName = "%s : %s"%(frame['busName'],frame['presetLabel'])
      if frame['type'] in REPLAY.SUPPORTED_BUS_TYPE and not busName in self.requiredBus:
        busCursor = self.db.bus.find({"hash":frame['preset']},{"_id":0})
        if busCursor.count() > 0:
          self.requiredBus[busName] = busCursor[0]
          self.requiredBus[busName]['label'] = frame['busName']
          self.requiredBus[busName]['preset'] = frame['preset']
          self.requiredBus[busName]['presetLabel'] = "%s - %s %s"%(busCursor[0]['name'],busCursor[0]['speed'],SUPPORTED_SPEED_UNIT[busCursor[0]['type']])

    self.requiredBusOrder = sorted(self.requiredBus,
                          key=lambda k: (self.requiredBus[k]['type'], self.requiredBus[k]['name'], self.requiredBus[k]['speed'], self.requiredBus[k]['label']))

    # Signals
    self.appSignals.updateProgressBar.connect(lambda eventList: self.updateProgressBar(eventList))

    self.body.btnReplayAll.clicked.connect(lambda: self.initReplay())
    self.body.btnCancel.clicked.connect(lambda: self.cancelReplay())
    self.body.btnCancelAll.clicked.connect(lambda: self.cancelReplay())
    self.body.btnSmartReplay.clicked.connect(lambda: self.initReplay(smartMode=True))
    self.body.btnRevert.clicked.connect(lambda: self.sliceFrames(revert=True))
    self.body.btnSlice.clicked.connect(lambda: self.sliceFrames())
    self.body.btnNext.clicked.connect(lambda: self.switchSlice(SLICE.NEXT))
    self.body.btnPrevious.clicked.connect(lambda: self.switchSlice(SLICE.PREVIOUS))
    self.body.btnReplay.clicked.connect(lambda: self.switchSlice(SLICE.SELF))
    self.body.btnStop.clicked.connect(self.threadStopManager['replay'].set)
    self.body.btnUpdate.clicked.connect(lambda: self.convertSliceToSession())
    self.body.btnUpdateSession.clicked.connect(lambda: self.updateSession())
    self.body.btnPause.clicked.connect(lambda: self.pauseReplay())
    self.body.btnBack.clicked.connect(lambda: self.replayGetBackward())
    self.body.btnSliceAll.clicked.connect(lambda: self.sliceFrames(startAtCurrentIndex=True))
    #self.body.btnAddCommand.clicked.connect(lambda: self.createCommand())
    self.body.checkLoop.toggled.connect(lambda x:self.updateLoop(x))
    self.body.comboFeedback.currentIndexChanged.connect(lambda x:self.updateFeedback(x))

    # Editing grid
    self.drawDialogBody()


  def closeDialog(self):
    self.threadStopManager['replay'].set()
    self.reject()


  def closeEvent(self, event):
    self.threadStopManager['replay'].set()


  def selfInitInterfaces(self):
    self.setBus = {}

    for elt in self.requiredBusWidgets:
      widget = elt['widget']
      bus = self.requiredBus[elt['busName']] # Manque element
      if widget.currentIndex() > 0:
        iface = widget.currentData()
        self.setBus[elt['busName']] = iface['id']
        initBus = False
        if self.interfaces.bus[iface['id']]['active'] == False:
          initBus = True
        else:
          initBus = True
          for bus_ in self.setBus:
            if self.setBus[bus_] == iface['id'] and bus_ != elt['busName']:
              initBus = False
        if initBus == True:
          if self.interfaces.bus[iface['id']]['gw'] != None:
            self.interfaces.bus[self.interfaces.bus[iface['id']]['gw']] = None
          self.interfaces.bus[iface['id']]['gw'] = None
          self.interfaces.bus[iface['id']]['preset'] = bus['hash']
          self.interfaces.bus[iface['id']]['speed'] = bus['speed']
          self.interfaces.bus[iface['id']]['presetLabel'] = bus['presetLabel']
          self.appSignals.switchBus.emit({"id":iface['id'], "dialog":None})
          self.interfaces.bus[iface['id']]['label'] = elt['busInfo']['label']


  def updateFeedback(self, index):
    self.feedback = index


  def updateLive(self, value):
    self.live = value


  def switchSlice(self, sliceOrder = SLICE.NEXT):
    self.threadStopManager['replay'].clear()
    self.sliceNumber += sliceOrder
    if self.sliceNumber > 2:
      self.sliceNumber = 0
    elif self.sliceNumber < 0:
      self.sliceNumber = 2

    self.framesBuffer = self.slices[self.sliceNumber]['frames']
    self.bufferLen = len(self.framesBuffer)
    self.setProgressBar()
    self.displayBufferRange(self.slices[self.sliceNumber]['start'], self.slices[self.sliceNumber]['end'])
    self.replayCurrentFrame = 0
    self.replayBufferedFrames()


  def sliceFrames(self, init=False, revert=False, startAtCurrentIndex=False):
    self.threadStopManager['replay'].set()
    if init == True:
      start = 0
      end = len(self.frames)
    elif revert == True:
      start = self.slices[0]["start"]
      end = self.slices[2]['end']*2
      if (end >= len(self.frames)):
        end = len(self.frames)
        start = round(self.slices[0]["start"]/2)
    elif startAtCurrentIndex != False:
      if self.replayCurrentFrame !=0:
        idx = self.replayCurrentFrame
        start = 0
        ts = self.framesBuffer[self.replayCurrentFrame]['ts']
        for i in range(0, idx):
          if ts - self.framesBuffer[idx - i]['ts'] >= REPLAY.BACKTIME:
            start = idx - i
            break
        delta = idx - start
        end = start + delta * 2
        if end > len(self.frames):
          end = len(self.frames)
      else:
        start = 0
        end = len(self.frames)
      self.switchSmartButtons(visible=True)
      self.switchAltButtons(visible=False)
      self.smartMode = True
      self.replayCurrentFrame = 0
    else:
      start = self.slices[self.sliceNumber]['start']
      end = self.slices[self.sliceNumber]['end']

    sliceLen = round((end - start)/ 2)
    sliceInc = round(sliceLen / 2)

    self.slices[0] = {"start": start, "end":start+sliceLen, "frames":self.frames[start: (start+sliceLen)]}
    self.slices[1] = {"start": start+sliceInc, "end":start+sliceLen+sliceInc, "frames":self.frames[(start+sliceInc): (start+sliceLen+sliceInc)]}
    self.slices[2] = {"start": start+sliceLen, "end":end, "frames":self.frames[(start+sliceLen): end]}

    self.sliceNumber = 0
    self.switchSlice(SLICE.SELF)


  def convertSliceToSession(self):
    self.threadStopManager['replay'].set()
    self.frames = self.slices[self.sliceNumber]['frames']
    self.body.lblFrames.setText(str(len(self.frames)))
    self.switchSmartButtons(visible=False)
    self.switchAltButtons(visible=False)
    self.switchMainButtons(disabled = False)


  def updateSession(self):
    self.session['frames'] = self.frames.copy()
    self.done(REPLAY.UPDATE_SESSION)


  def initReplay(self, smartMode = False):
    self.selfInitInterfaces()
    time.sleep(0.1)
    self.timer = time.time()

    if self.hasFuzzing == True:
      self.fuzzId = None
      self.fuzzMsg = None

    if self.feedback == REPLAY.FEEDBACK_LIVE:
      self.appSignals.startSessionLive.emit(True)
    elif self.feedback == REPLAY.FEEDBACK_RECORD:
      self.appSignals.startSessionRecording.emit(False)
    elif self.feedback == REPLAY.FEEDBACK_RECORD_NEW_SESSION:
      if self.replayIsPaused == False:
        self.appSignals.startSessionRecording.emit(True)
      else:
        self.appSignals.startSessionRecording.emit(False)

    if smartMode == True:
      self.switchSmartButtons(visible=True)
      self.switchAltButtons(visible=False)
      self.smartMode = True
      self.switchMainButtons(disabled=True)
      self.setProgressBar()
      self.sliceFrames(init=True)
    else:
      self.smartMode = False
      self.switchSmartButtons(visible=False)
      self.switchAltButtons(visible=True)
      self.framesBuffer = self.frames.copy()
      self.bufferLen = len(self.framesBuffer)
      self.switchMainButtons(disabled=True)
      self.setProgressBar()
      self.displayBufferRange(0, len(self.framesBuffer))
      if self.replayIsPaused == True:
        self.replayIsPaused = False
      else:
        self.replayCurrentFrame = 0

      self.replayBufferedFrames()


  def replayBufferedFrames(self):
    self.threads['replay'] = threading.Thread(target = self.threadReplayBufferedFrames)
    self.threads['replay'].start()


  def threadReplayBufferedFrames(self):
    self.threadStopManager['replay'].clear()
    replayDuration =  self.framesBuffer[len(self.framesBuffer)-1]['ts']
    cumulatedSleep = 0

    if self.replayCurrentFrame != 0 and len(self.initMsg) > 0:
      logging.debug("INIT %s\n%s"%(self.initMsg, self.setBus))
      for f in self.initMsg:
        if f['busName'] + " - " in f['presetLabel']:
          busRef = f['presetLabel']
        else:
          busRef = "%s : %s"%(f['busName'], f['presetLabel'])

        if busRef in self.setBus:
          busId = self.setBus[busRef]
          if not busRef in self.session['filters'] or not f['id'] in self.session['idList'][busRef] or (busRef in self.session['filters']  and not f['id'] in self.session['filters'][busRef]):
            self.activeBus[busId].sendMsg(f)

    if self.startPause > 0 and self.replayCurrentFrame == 0:
      time.sleep(self.startPause / 1000)

    while not self.threadStopManager['replay'].is_set():
      if self.replayCurrentFrame < self.bufferLen:

        f = self.framesBuffer[self.replayCurrentFrame]

        if 'isFuzzed' in f:
          if f['id'] != self.fuzzId:
            self.fuzzId = f['id']
            if f['extendedId'] == True:
              self.body.lblId.setText("{0:0{1}x}".format(f['id'],8))
            else:
              self.body.lblId.setText("{0:0{1}x}".format(f['id'],3))
          if f['msg'] != self.fuzzMsg:
            self.fuzzMsg = f['msg'].copy()
            str = ""
            for byte in f['msg']:
              str += "{0:0{1}x}".format(byte,2) + " "
            self.body.lblMsg.setText(str)

        if f['busName'] + " - " in f['presetLabel']:
          busRef = f['presetLabel']
        else:
          busRef = "%s : %s"%(f['busName'], f['presetLabel'])

        if busRef in self.setBus:
          busId = self.setBus[busRef]

          if not busRef in self.session['filters'] or not f['id'] in self.session['idList'][busRef] or (busRef in self.session['filters']  and not f['id'] in self.session['filters'][busRef]):
            self.activeBus[busId].sendMsg(f)

        if self.feedback > REPLAY.FEEDBACK_NONE:
          f_ = f.copy()
          f_['ts'] = time.time()
          self.appSignals.frameRecv.emit({"msg":f_})
          del f_

        if self.replayCurrentFrame < self.bufferLen -1:
          waitTime = self.framesBuffer[self.replayCurrentFrame + 1]['ts'] - f['ts']
          if waitTime > REPLAY.MAX_WAIT_TIME:
            waitTime = REPLAY.MAX_WAIT_TIME
          if waitTime >= 0.010 or cumulatedSleep > 0.010:
            time.sleep(waitTime + cumulatedSleep) #INACCURATE - CUMULATE PER MS
            cumulatedSleep = 0
          else:
            cumulatedSleep += waitTime

      self.replayCurrentFrame += 1

      if self.replayCurrentFrame >= self.bufferLen:
        if self.loop == False:
          self.threadStopManager['replay'].set()
        else:
          if self.endPause > 0:
            time.sleep(self.endPause / 1000)
          self.replayCurrentFrame = 0

      rTime = self.getRemainingTime(replayDuration-f['ts'])
      replayInfo = "%s : %s - %s : %s:%s:%s"%(
                      QCoreApplication.translate("REPLAY","CURRENT_FRAME"), self.replayCurrentFrame,
                      QCoreApplication.translate("REPLAY","TIME_REMAINING"),rTime[0],rTime[1],rTime[2])

      if self.progressLastUpdate + REPLAY.PROGRESSBAR_UPDATE_DELAY < time.time() or self.bufferLen < REPLAY.PROGRESSBAR_SMALL_BUFFER or self.replayCurrentFrame >= self.bufferLen:
        self.appSignals.updateProgressBar.emit([self.replayCurrentFrame, replayInfo])
        self.progressLastUpdate = time.time()

    if self.feedback >= REPLAY.FEEDBACK_RECORD:
      self.appSignals.startSessionForensic.emit(True)
    elif self.feedback == REPLAY.FEEDBACK_LIVE:
      self.appSignals.pauseSession.emit(True)

    if self.smartMode == False and self.replayIsPaused == False:
      self.switchMainButtons(disabled=False)
      self.switchSmartButtons(visible=False)
      self.switchAltButtons(visible=False)


  def updateProgressBar(self, data):
    self.body.progress.setValue(data[0])
    self.body.lblFrameId.setText(data[1])

  def getRemainingTime(self, timestamp):
    seconds=str(int((timestamp)%60)).zfill(2)
    minutes=str(int((timestamp/60)%60)).zfill(2)
    hours=str(int(timestamp/(60*60))).zfill(2)
    return hours, minutes, seconds

  def replayGetBackward(self):
    idx = self.replayCurrentFrame
    newIdx = 0
    ts = self.framesBuffer[self.replayCurrentFrame]['ts']
    for i in range(0, idx):
      if ts - self.framesBuffer[idx - i]['ts'] >= REPLAY.BACKTIME:
        newIdx = idx - i
        break
    self.replayCurrentFrame = newIdx

    if self.replayIsPaused == True:
      self.pauseReplay()


  def pauseReplay(self):
    options = [{"color":"white","color_disabled":"black"}]
    if self.replayIsPaused == False:
      self.replayIsPaused = True
      self.threadStopManager['replay'].set()
      self.body.btnPause.setIcon(qta.icon("fa5s.play-circle",options=options))
      self.body.btnPause.setProperty("cssClass","btn-success")
      self.body.btnPause.setStyle(self.body.btnPause.style())
      self.body.btnPause.setText(QCoreApplication.translate("REPLAY","PLAY"))
      if self.feedback == REPLAY.FEEDBACK_LIVE:
        self.appSignals.pauseSession.emit(True)
    else:
      self.initReplay(smartMode= False)
      self.body.btnPause.setIcon(qta.icon("fa5s.pause-circle",options=options))
      self.body.btnPause.setProperty("cssClass","btn-danger")
      self.body.btnPause.setStyle(self.body.btnPause.style())
      self.body.btnPause.setText(QCoreApplication.translate("REPLAY","PAUSE"))


  def cancelReplay(self):
    self.smartMode = False
    self.replayIsPaused = False
    self.threadStopManager['replay'].set()
    self.switchMainButtons(disabled=False)
    self.switchSmartButtons(visible=False)
    self.switchAltButtons(visible=False)


  def setProgressBar(self):
    self.body.progress.show()
    self.body.titlePlaying.show()
    self.body.lblFrameCount.show()
    self.body.progress.setValue(0)
    self.body.progress.setMaximum(len(self.framesBuffer ))
    self.body.lblFrameId.show()
    self.body.lblFrameId.setText("")


  def hideProgressBar(self):
    self.body.progress.hide()
    self.body.titlePlaying.hide()
    self.body.lblFrameCount.hide()
    self.body.lblFrameId.hide()


  def displayBufferRange(self, start=0, stop=0):
    self.body.lblFrameCount.setText(str(start) + " - " + str(stop) + " ("+str(stop-start)+")")


  def addRequiredBus(self, key):
    bus = self.requiredBus[key]
    rowIndex = self.body.replayBusGridLayout.rowCount()

    sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)

    busType = QLabel(SUPPORTED_BUS_TYPE[bus['type']])
    self.body.replayBusGridLayout.addWidget(busType, rowIndex, 0, 1, 1)

    busName = QLabel(bus['label'])
    self.body.replayBusGridLayout.addWidget(busName, rowIndex, 1, 1, 1)
    busLabel = QLabel(bus['presetLabel'])

    self.body.replayBusGridLayout.addWidget(busLabel, rowIndex, 2, 1, 1)

    busIface = QComboBox()
    busIface.addItem("-", None)

    selectedIndex = None
    for k in self.busListOrder:
      if self.interfaces.bus[k]['type'] == bus['type']:
        busIface.addItem(self.interfaces.bus[k]['deviceLabel'] + " " + self.interfaces.bus[k]['name'], self.interfaces.bus[k])
        if bus['preset'] == self.interfaces.bus[k]['preset'] and bus['label'] == self.interfaces.bus[k]['label']:
          selectedIndex = busIface.count() -1
          busIface.setCurrentIndex(selectedIndex)
    self.body.replayBusGridLayout.addWidget(busIface, rowIndex, 3, 1, 1)
    self.requiredBusWidgets.append({"widget":busIface, "busName":key, "busInfo":bus})


  def updateLoop(self, checked):
    self.loop = checked

  def switchSmartButtons(self, visible=True):
    self.body.btnPrevious.setVisible(visible)
    self.body.btnRevert.setVisible(visible)
    self.body.btnSlice.setVisible(visible)
    self.body.btnNext.setVisible(visible)
    self.body.btnUpdate.setVisible(visible)
    self.body.btnReplay.setVisible(visible)
    self.body.btnStop.setVisible(visible)
    self.body.btnCancel.setVisible(visible)


  def switchAltButtons(self, visible=True):
    options = [{"color":"white","color_disabled":"black"}]
    self.body.btnBack.setVisible(visible)
    self.body.btnSliceAll.setVisible(visible)
    self.body.btnPause.setVisible(visible)
    self.body.btnCancelAll.setVisible(visible)
    self.body.btnPause.setText(QCoreApplication.translate("REPLAY","PAUSE"))
    self.body.btnPause.setIcon(qta.icon("fa5s.pause-circle",options=options))
    self.body.btnPause.setProperty("cssClass","btn-danger")
    self.body.btnPause.setStyle(self.body.btnPause.style())


  def switchMainButtons(self, disabled = True):
    self.body.checkLoop.setDisabled(disabled)
    self.body.comboFeedback.setDisabled(disabled)

    if disabled == True:
      cssClass="btn-disabled"
    else:
      cssClass="btn-primary"

    widgets = [self.body.btnSmartReplay, self.body.btnReplayAll,self.body.btnUpdateSession, self.body.btnAddCommand]
    for w in widgets:
      w.setDisabled(disabled)
      w.setProperty("cssClass", cssClass)
      w.setStyle(w.style())

    for elt in self.requiredBusWidgets:
      elt['widget'].setDisabled(disabled)


  def drawDialogBody(self):
    self.switchMainButtons(disabled=False)
    self.switchAltButtons(visible=False)
    self.switchSmartButtons(visible=False)
    self.hideProgressBar()

    options = [{"color":"white","color_disabled":"black"}]
    self.body.btnSmartReplay.setIcon(qta.icon("fa.magic",options=options))
    self.body.btnReplayAll.setIcon(qta.icon("mdi.playlist-play", options=options))
    self.body.btnUpdateSession.setIcon(qta.icon("mdi.playlist-edit",options=options))
    self.body.btnAddCommand.setIcon(qta.icon("mdi.script",options=options))
    self.body.btnStop.setIcon(qta.icon("fa5s.stop-circle",options=options))
    self.body.btnPrevious.setIcon(qta.icon("mdi.rewind",options=options))
    self.body.btnRevert.setIcon(qta.icon("fa5b.rev",options=options))
    self.body.btnSlice.setIcon(qta.icon("fa5s.cut",options=options))
    self.body.btnNext.setIcon(qta.icon("mdi.forward",options=options))
    self.body.btnUpdate.setIcon(qta.icon("mdi.playlist-edit",options=options))
    self.body.btnReplay.setIcon(qta.icon("mdi.replay",options=options))
    self.body.btnCancel.setIcon(qta.icon("mdi.cancel",options=options))
    self.body.btnCancelAll.setIcon(qta.icon("mdi.cancel",options=options))
    self.body.btnBack.setIcon(qta.icon("mdi.replay",options=options))
    self.body.btnSliceAll.setIcon(qta.icon("fa5s.cut",options=options))
    self.body.btnPause.setIcon(qta.icon("fa5s.pause-circle",options=options))

    self.body.lblFrames.setText(str(len(self.frames)))
    self.body.lblMode.setText(QCoreApplication.translate("REPLAY",REPLAY.LABEL[self.replayMode]))

    self.busListOrder = sorted(self.interfaces.bus, key=lambda x: (self.interfaces.bus[x]['deviceLabel'], self.interfaces.bus[x]['name']))

    if self.hasFuzzing == True:
      display = True
    else:
      display = False

    self.body.titleId.setVisible(display)
    self.body.titleMsg.setVisible(display)
    self.body.lblId.setVisible(display)
    self.body.lblMsg.setVisible(display)
    self.body.titleFeedback.setVisible(display)

    for key in self.requiredBusOrder:
      self.addRequiredBus(key)
