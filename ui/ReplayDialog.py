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
  def __init__(self, refWindow, mode=REPLAY.SESSION, frames=None):
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

    # Replay variables
    self.framesBuffer = []

    self.progressIndex = 0
    self.threadStopManager['replay'] = threading.Event()
    self.replayLock = threading.Event()

    self.loop = False

    if self.replayMode == REPLAY.SESSION:
      self.frames = self.session['frames']
    if self.replayMode == REPLAY.SELECTION:
      orderedFrames= sorted(frames,
                            key=lambda k: (k['ts']))

      self.frames = orderedFrames

      #self.btnUpdateSession.hide()

    self.sliceNumber = 0
    self.slices = [{},{},{}]

    # Defining required BUS
    self.requiredBusWidgets = []
    self.requiredBus = {}
    self.validBus = {}

    for frame in self.frames:
      if frame['type'] in REPLAY.SUPPORTED_BUS_TYPE and not frame['preset'] in self.requiredBus:
        busCursor = self.db.bus.find({"hash":frame['preset']},{"_id":0})
        if busCursor.count() > 0:
          self.requiredBus[frame['preset']] = busCursor[0]
          self.requiredBus[frame['preset']]['presetLabel'] = busCursor[0]['name'] + " - " + str(busCursor[0]['speed'])  + SUPPORTED_SPEED_UNIT[busCursor[0]['type']]

    self.requiredBusOrder = sorted(self.requiredBus,
                          key=lambda k: (self.requiredBus[k]['type'], self.requiredBus[k]['name'], self.requiredBus[k]['speed']))

    # Signals
    #self.body.btnSmartReplay.clicked.connect(lambda: self.initReplay(True))
    self.body.btnReplayAll.clicked.connect(lambda: self.initReplay())
    self.body.btnCancel.clicked.connect(lambda: self.cancelReplay())
    self.body.btnSmartReplay.clicked.connect(lambda: self.initReplay(smartMode=True))
    self.body.btnRevert.clicked.connect(lambda: self.sliceFrames(revert=True))
    self.body.btnSlice.clicked.connect(lambda: self.sliceFrames())
    self.body.btnNext.clicked.connect(lambda: self.switchSlice(SLICE.NEXT))
    self.body.btnPrevious.clicked.connect(lambda: self.switchSlice(SLICE.PREVIOUS))
    self.body.btnReplay.clicked.connect(lambda: self.switchSlice(SLICE.SELF))
    self.body.btnStop.clicked.connect(self.threadStopManager['replay'].set)
    self.body.btnUpdate.clicked.connect(lambda: self.convertSliceToSession())
    self.body.btnUpdateSession.clicked.connect(lambda: self.updateSession())
    #self.body.btnAddCommand.clicked.connect(lambda: self.createCommand())
    self.body.checkLoop.toggled.connect(lambda x:self.updateLoop(x))

    # Editing grid
    self.drawDialogBody()

  def closeDialog(self):
    self.threadStopManager['replay'].set()
    self.reject()

  def closeEvent(self, event):
    self.threadStopManager['replay'].set()

  def selfInitInterfaces(self):
    self.validBus = {}

    for elt in self.requiredBusWidgets:
      widget = elt['widget']
      bus = self.requiredBus[elt['preset']]
      if widget.currentIndex() > 0:
        iface = widget.currentData()
        logging.debug("Updating bus %s data : \n%s\n"%(iface['id'], iface))
        self.validBus[elt['preset']] = iface['id']
        if self.interfaces.bus[iface['id']]['active'] == False or self.interfaces.bus[iface['id']]['preset'] != elt['preset']:
          if self.interfaces.bus[iface['id']]['gw'] != None:
            self.interfaces.bus[self.interfaces.bus[iface['id']]['gw']] = None
          self.interfaces.bus[iface['id']]['gw'] = None
          self.interfaces.bus[iface['id']]['preset'] = bus['hash']
          self.interfaces.bus[iface['id']]['speed'] = bus['speed']
          self.interfaces.bus[iface['id']]['label'] = bus['name']
          self.interfaces.bus[iface['id']]['presetLabel'] = bus['presetLabel']
          logging.debug("Switching bus : %s\n\n"% self.interfaces.bus[iface['id']])
          self.appSignals.switchBus.emit({"id":iface['id'], "dialog":None})


  def updateLoop(self, value):
    self.loop = value

  def switchSlice(self, sliceOrder = SLICE.NEXT):
    self.threadStopManager['replay'].clear()
    self.sliceNumber += sliceOrder
    if self.sliceNumber > 2:
      self.sliceNumber = 0
    elif self.sliceNumber < 0:
      self.sliceNumber = 2

    self.framesBuffer = self.slices[self.sliceNumber]['frames']
    self.bufferLen = len(self.framesBuffer)
    logging.debug("Frame buffer start at %s and stop at %s"%(self.slices[self.sliceNumber]['start'],self.slices[self.sliceNumber]['end']))
    logging.debug("Slices frame buffer in switchSlice : %s"%len(self.framesBuffer))
    self.setProgressBar()
    self.displayBufferRange(self.slices[self.sliceNumber]['start'], self.slices[self.sliceNumber]['end'])
    self.replayBufferedFrames()


  def sliceFrames(self, init=False, revert=False):
    self.threadStopManager['replay'].set()
    if init == True:
      start = 0
      end = len(self.frames)
    elif revert == True:
      logging.debug("Reverting")
      start = self.slices[0]["start"]
      end = self.slices[2]['end']*2
      if (end >= len(self.frames)):
        end = len(self.frames)
        start = round(self.slices[0]["start"]/2)
    else:
      start = self.slices[self.sliceNumber]['start']
      end = self.slices[self.sliceNumber]['end']

    sliceLen = round((end - start)/ 2)
    sliceInc = round(sliceLen / 2)
    logging.debug("Slicing start at %s and stop at %s"%(start, end))
    logging.debug("Slice length %s"%(sliceLen))
    logging.debug("Slice inc %s"%(sliceInc))

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
    self.switchMainButtons(disabled = False)

  def updateSession(self):
    self.session['frames'] = self.frames.copy()
    self.done(REPLAY.UPDATE_SESSION)

  def initReplay(self, smartMode = False):
    self.selfInitInterfaces()
    time.sleep(0.3)

    logging.debug("Bus : %s\n\n"%self.interfaces.bus)
    logging.debug("Active bus : %s\n\n"%self.activeBus)

    if smartMode == True:
      self.switchSmartButtons(visible=True)
      self.smartMode = True
      self.switchMainButtons(disabled=True)
      self.setProgressBar()
      self.sliceFrames(init=True)
    else:
      self.smartMode = False
      self.switchSmartButtons(visible=False)
      self.framesBuffer = self.frames.copy()
      self.bufferLen = len(self.framesBuffer)
      self.switchMainButtons(disabled=True)
      self.setProgressBar()
      self.displayBufferRange(0, len(self.framesBuffer))
      self.replayBufferedFrames()


  def replayBufferedFrames(self):
    currentFrame = 0
    self.threadStopManager['replay'].clear()
    logging.debug("Valid bus : \n%s\n"%self.validBus)
    while not self.threadStopManager['replay'].is_set():
      if currentFrame < self.bufferLen:
        f = self.framesBuffer[currentFrame]

        if f['preset'] in self.validBus:
          busId = self.validBus[f['preset']]
          self.activeBus[busId].sendMsg(f)

        if currentFrame < self.bufferLen -1:
          waitTime = self.framesBuffer[currentFrame + 1]['ts'] - f['ts']
          if waitTime > 1:
            waitTime = 1
          time.sleep(waitTime)

      currentFrame += 1

      if currentFrame >= self.bufferLen:
        if self.loop == False:
          self.threadStopManager['replay'].set()
        else:
          currentFrame = 0
      self.body.progress.setValue(currentFrame)
      QApplication.processEvents()

    if self.smartMode == False:
      self.switchMainButtons(disabled=False)
      self.switchSmartButtons(visible=False)

  def cancelReplay(self):
    self.smartMode = False
    self.threadStopManager['replay'].set()
    self.switchMainButtons(disabled=False)
    self.switchSmartButtons(visible=False)

  def setProgressBar(self):
    self.body.progress.show()
    self.body.titlePlaying.show()
    self.body.lblFrameCount.show()
    self.body.progress.setValue(0)
    self.body.progress.setMaximum(len(self.framesBuffer ))


  def hideProgressBar(self):
    self.body.progress.hide()
    self.body.titlePlaying.hide()
    self.body.lblFrameCount.hide()


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

    busLabel = QLabel(bus['presetLabel'])
    self.body.replayBusGridLayout.addWidget(busLabel, rowIndex, 1, 1, 1)

    busIface = QComboBox()
    busIface.addItem("-", None)

    selectedIndex = None
    for k in self.busListOrder:
      if self.interfaces.bus[k]['type'] == bus['type']:
        busIface.addItem(self.interfaces.bus[k]['deviceLabel'] + " " + self.interfaces.bus[k]['name'], self.interfaces.bus[k])
        if key == self.interfaces.bus[k]['preset']:
          selectedIndex = busIface.count() -1
          busIface.setCurrentIndex(selectedIndex)
    self.body.replayBusGridLayout.addWidget(busIface, rowIndex, 2, 1, 1)
    self.requiredBusWidgets.append({"widget":busIface, "preset":key})


  def switchSmartButtons(self, visible=True):
    self.body.btnPrevious.setVisible(visible)
    self.body.btnRevert.setVisible(visible)
    self.body.btnSlice.setVisible(visible)
    self.body.btnNext.setVisible(visible)
    self.body.btnUpdate.setVisible(visible)
    self.body.btnReplay.setVisible(visible)
    self.body.btnStop.setVisible(visible)



  def switchMainButtons(self, disabled = True):
    if disabled == True:
      cssClass="btn-disabled"
      self.body.btnCancel.setVisible(True)

    else:
      cssClass="btn-primary"
      self.body.btnCancel.setVisible(False)

    self.body.checkLoop.setDisabled(disabled)

    widgets = [self.body.btnSmartReplay, self.body.btnReplayAll,self.body.btnUpdateSession, self.body.btnAddCommand]
    for w in widgets:
      w.setDisabled(disabled)
      w.setProperty("cssClass", cssClass)
      w.setStyle(w.style())

    for elt in self.requiredBusWidgets:
      elt['widget'].setDisabled(disabled)

  def drawDialogBody(self):
    self.switchMainButtons(disabled=False)
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

    self.body.lblFrames.setText(str(len(self.frames)))
    self.body.lblMode.setText(QCoreApplication.translate("REPLAY",REPLAY.LABEL[self.replayMode]))

    self.busListOrder = sorted(self.interfaces.bus, key=lambda x: (self.interfaces.bus[x]['deviceLabel'], self.interfaces.bus[x]['name']))

    for key in self.requiredBusOrder:
      self.addRequiredBus(key)
