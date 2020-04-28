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

from ui.ModelDialog import ModelDialog, UCValidator
from ui.CommandsForm import Ui_COMMAND

#
# Dialog classes
#
class CommandForm(QWidget, Ui_COMMAND):
  def __init__(self):
   super().__init__()
   self.setupUi(self)


class CommandDialog(ModelDialog):
  def __init__(self, refWindow, cmdId=False):
    super().__init__()

    self.getMainVariables(refWindow)

    self.cmdId = cmdId
    self.comboCmdLock = False
    self.cmdSrc = CMD.SRC['ANALYSIS']

    self.progressIndex = 0
    self.threadStopManager['generateCmd'] = threading.Event()

    self.frameSrc = []
    self.initMsg = []
    self.startPause = 0
    self.endPause = 0

    self.initFuzzBytes()

    # Bottom buttons
    self.closeBtn = QPushButton()
    self.closeBtn.setIcon(qta.icon('fa.close',color='white'))
    self.closeBtn.setText(QCoreApplication.translate("DIALOG", "CLOSE"))
    self.closeBtn.setProperty("cssClass","btn-danger")
    self.closeBtn.setCursor(Qt.PointingHandCursor)
    self.closeBtn.clicked.connect(lambda: self.closeDialog())
    self.setBottomButtons(self.closeBtn)

    # Loading body template
    self.body = CommandForm()
    self.dialogTitle.setText(QCoreApplication.translate("CMD", "CMD_EDITOR"))
    self.dialogBody.addWidget(self.body)

    # Btn
    options=[{'color_disabled': 'black', 'color':'white'}]
    self.body.btnSave.setIcon(qta.icon('fa5.save',options=options))
    self.body.btnDelete.setIcon(qta.icon('mdi.delete',options=options))
    self.body.btnNewCmd.setIcon(qta.icon('ei.file-new',options=options))
    self.body.btnShare.setIcon(qta.icon('fa.share-alt',options=options))
    self.body.btnImport.setIcon(qta.icon('mdi.content-duplicate',options=options))
    self.body.btnPlay.setIcon(qta.icon('fa5.play-circle',options=options))
    self.body.btnAddActive.setIcon(qta.icon('mdi.playlist-plus',options=options))
    self.body.btnAddConstant.setIcon(qta.icon('mdi.playlist-plus',options=options))
    self.body.btnAddPause.setIcon(qta.icon('mdi.playlist-star',options=options))

    # Signals
    self.body.btnAddActive.clicked.connect(lambda: self.addMsg("activ",None))
    self.body.btnAddConstant.clicked.connect(lambda: self.addMsg("const",None))
    self.body.btnAddPause.clicked.connect(lambda: self.addPause(None))
    self.body.btnSave.clicked.connect(lambda: self.saveCmd())
    self.body.btnNewCmd.clicked.connect(lambda: self.newCmd())
    self.body.btnPlay.clicked.connect(lambda: self.playCmd())
    self.body.comboCmdSelector.currentIndexChanged.connect(lambda: self.loadCmd())
    self.body.comboCmdSrc.currentIndexChanged.connect(lambda: self.changeSrc())
    self.body.fldName.textChanged.connect(lambda: self.updateSaveBtn())
    self.body.btnImport.clicked.connect(lambda: self.importCmd())
    self.body.btnDelete.clicked.connect(lambda: self.delCmd())

    # Context menu
    self.body.constantMsg.setContextMenuPolicy(Qt.CustomContextMenu)
    self.body.activeMsg.setContextMenuPolicy(Qt.CustomContextMenu)
    self.body.constantMsg.customContextMenuRequested.connect(lambda eventPos: self.showContextMenu(eventPos, self.body.constantMsg))
    self.body.activeMsg.customContextMenuRequested.connect(lambda eventPos: self.showContextMenu(eventPos, self.body.activeMsg))

    # Validators
    regexId = QRegExp("[0-9a-fA-F!]{1,17}") #\\-*+|^&/
    regexByte = QRegExp("^[{0,1}[0-9a-fA-F!]{1,5}]{0,1}$")
    self.idValidator = UCValidator()
    self.byteValidator = UCValidator()
    self.upperCaseValidator = UCValidator(self)
    self.body.fldRepeat.setValidator(QIntValidator(0, 1000, self))

    #Regex
    self.regexpNonBytes = "([\\+\\*\\-/^|&~\\<\\>s])+"
    self.regexpFormula  = "([\\+\\*\\-/^|&~\\<\\>\\$])+"
    self.regexpOperands = "([\\+\\*\\-/^|&~\\<\\>])"

    # Bus list
    hashList = []
    for bus in self.analysis['bus']:
      hashList.append(bus['hash'])
    busCursor = self.db.bus.find({"hash":{"$in":hashList}},{"_id":0})
    self.avalaibleBus = []
    if busCursor.count() > 0:
      for bus in busCursor:
        self.avalaibleBus.append(bus)
      self.availableBus = sorted(self.avalaibleBus, key=lambda x: (x['type'], x['name']))


    self.drawDialogBody()


  def closeDialog(self):
    self.threadStopManager['generateCmd'].set()
    self.reject()


  def closeEvent(self, event):
    self.threadStopManager['generateCmd'].set()


  def initFuzzBytes(self):
    self.b1 = self.b2 = self.b3 = self.b4 = self.b5 = self.b6 = self.b7 = self.b8 = self.bi = 0
    self.fuzzBytes = []
    for i in range(0, 9):
      self.fuzzBytes.append({"isFuzzed":False, "min":0, "max":0})

  def showContextMenu(self, pos, widget):
    globalPos = widget.mapToGlobal(pos);

    self.menu = QMenu(self)
    filterHideAction = QAction(QCoreApplication.translate("MENU","DELETE_MSG"), self)
    filterHideAction.setIcon(qta.icon('mdi.delete'))
    filterHideAction.triggered.connect(lambda eventPos: self.delMsg(pos, widget))

    self.menu.addAction(filterHideAction)
    self.menu.exec(globalPos)


  def newCmd(self):
    self.cmdId = False
    self.body.fldName.setText("")
    self.body.fldRepeat.setText("")
    self.body.errorMsg.hide()

    self.body.btnSave.show()
    self.body.btnDelete.hide()
    self.body.btnShare.hide()
    self.body.btnImport.hide()
    self.body.btnAddPause.show()
    self.body.btnAddActive.show()
    self.body.btnAddConstant.show()
    self.body.activeMsg.setDisabled(False)
    self.body.constantMsg.setDisabled(False)
    self.body.fldName.setDisabled(False)
    self.body.fldRepeat.setDisabled(False)

    listWidgets = [self.body.activeMsg, self.body.constantMsg]
    for listWiget in listWidgets:
      row = listWiget.count()
      for i in range(0, row):
        listWiget.takeItem(row-i-1)
    self.body.comboCmdSelector.setCurrentIndex(0)
    self.updateSaveBtn()


  def loadCmd(self):
    if self.comboCmdLock == False and self.body.comboCmdSelector.currentIndex() > 0:
      cmd = self.body.comboCmdSelector.currentData()
      self.newCmd()
      self.cmdId = cmd['id']
      self.body.fldName.setText(cmd['name'])
      if 'repeat' in cmd:
        self.body.fldRepeat.setText(cmd['repeat'])

      logging.debug("LOAD : %s"%cmd)
      for cmd_ in cmd['cmd']['activ']:
        if cmd_['type'] == "pause":
          self.addPause(cmd_)
        else:
          self.addMsg('activ',cmd_)
      for cmd_ in cmd['cmd']['const']:
        self.addMsg('const',cmd_)

      if cmd['owner'] != self.user['uid']:
        self.body.btnSave.hide()
        self.body.btnDelete.hide()
        self.body.btnShare.hide()
        self.body.btnImport.show()
        self.body.btnAddPause.hide()
        self.body.btnAddActive.hide()
        self.body.btnAddConstant.hide()
        self.body.activeMsg.setDisabled(True)
        self.body.constantMsg.setDisabled(True)
        self.body.fldName.setDisabled(True)
        self.body.fldRepeat.setDisabled(True)
      else:
        self.body.btnDelete.show()
        self.body.btnShare.show()
        # SHARE status


  def importCmd(self):
    self.cmdId = False
    self.body.btnSave.show()
    self.body.btnAddPause.show()
    self.body.btnAddActive.show()
    self.body.btnAddConstant.show()
    self.body.btnImport.hide()
    self.body.activeMsg.setDisabled(False)
    self.body.constantMsg.setDisabled(False)
    self.body.fldName.setDisabled(False)
    self.body.fldRepeat.setDisabled(False)

  def saveCmd(self):
    newCmd = False

    cmdName = self.body.fldName.text()
    cmdRepeat = self.body.fldRepeat.text()
    if len(cmdName)== 0:
      return self.showCmdError("COMMAND_NAME_REQUIRED")

    cmdList = self.gatherCommands()

    if cmdList != False:
      if not self.cmdId:
        self.cmdId = str(uuid.uuid4())
        idExists = self.db.commands.find({"id":self.cmdId})
        while idExists.count() > 0:
          self.cmdId = str(uuid.uuid4())
          idExists = self.db.commands.find({"id":self.cmdId})
        newCmd = True
        self.body.btnDelete.show()
        self.body.btnShare.show()

      self.db.commands.update({"id": self.cmdId},
                              {"$set":{"id": self.cmdId, "name":cmdName, "owner":self.user['uid'], "repeat":cmdRepeat,
                                "analysis":self.analysis['id'], "manufacturer":self.analysis['manufacturer'],
                                "model":self.analysis['model'], "engineCode":self.analysis['engineCode'],
                                "cmd":cmdList, "update":time.time()}},
                              True)
      if newCmd == True:
        self.loadComboSelector()
        self.db.commands.update({"id": self.cmdId},{"$set":{"shared": False}})


  def delCmd(self):
    if self.cmdId != None:
      msgBox = QMessageBox()
      msgBox.setText(QCoreApplication.translate("COMMAND","DELETE_COMMAND"))
      msgBox.setInformativeText(QCoreApplication.translate("COMMAND","DELETE_COMMAND_DETAILS"))
      msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
      msgBox.setDefaultButton(QMessageBox.Ok)
      self.centerMsg(msgBox)
      choice = msgBox.exec()

      if choice == QMessageBox.Ok:
        self.db.commands.remove({"id":self.cmdId})

        self.loadComboSelector()
        self.newCmd()


  def delMsg(self, pos, widget):
    item = widget.itemAt(pos)
    r = widget.row(item)
    widget.takeItem(r)
    self.updateSaveBtn()


  def updateSaveBtn(self):
    name = self.body.fldName.text()
    row = self.body.activeMsg.count()
    if len(name)> 0 and row > 0:
      status = False
      cssClass = "btn-success"
    else:
      status = True
      cssClass = "btn-disabled"

    self.body.btnSave.setDisabled(status)
    self.body.btnPlay.setDisabled(status)
    self.body.btnSave.setProperty("cssClass", cssClass)
    self.body.btnPlay.setProperty("cssClass", cssClass)
    self.body.btnSave.setStyle(self.body.btnSave.style())
    self.body.btnPlay.setStyle(self.body.btnPlay.style())


  def addPause(self, msg=None):
    sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)

    item = QListWidgetItem(qta.icon("mdi.drag-vertical"),"", self.body.activeMsg)
    item.setSizeHint(QSize(item.sizeHint().width(), 36))

    itemWidget = QWidget()
    itemWidget.setProperty("type","pause")
    itemLayout = QGridLayout(itemWidget)
    itemLayout.setContentsMargins(0,6,0,6)

    titleBus = QLabel(QCoreApplication.translate("GENERIC","PAUSE") + " :")
    itemLayout.addWidget(titleBus, 0, 0)

    fldPause = QLineEdit()
    fldPause.setPlaceholderText("ms")
    fldPause.setMaximumWidth(60)
    fldPause.setValidator(QIntValidator(0, REPLAY.MAX_WAIT_TIME * 1000, self))
    if msg != None:
      fldPause.setText(msg['duration'])
    itemLayout.addWidget(fldPause, 0, 1, 1, 7)

    self.body.activeMsg.setItemWidget(item, itemWidget)
    self.updateSaveBtn()


  def addMsg(self, model="activ", msg=None):
    sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)

    if model=="activ":
      item = QListWidgetItem(qta.icon("mdi.drag-vertical"),"", self.body.activeMsg)
    else:
      item = QListWidgetItem(qta.icon("mdi.drag-vertical"),"", self.body.constantMsg)
    item.setSizeHint(QSize(item.sizeHint().width(), 66))

    itemWidget = QWidget()
    itemWidget.setProperty("type",model)
    itemLayout = QGridLayout(itemWidget)
    itemLayout.setContentsMargins(0,6,0,6)

    titleBus = QLabel(QCoreApplication.translate("GENERIC","BUS") + " :")
    itemLayout.addWidget(titleBus, 0, 0)

    bus = QComboBox()
    bus.addItem("-",False)
    i = 1
    for b in self.availableBus:
      busLabel = "%s : %s - %s %s"%(SUPPORTED_BUS_TYPE[b['type']], b['name'], b['speed'], SUPPORTED_SPEED_UNIT[b['type']])
      bus.addItem(busLabel, b)
      if msg != None and msg['hash']['hash'] == b['hash']:
        bus.setCurrentIndex(i)
      i += 1

    if msg != None and bus.currentIndex() == 0:
      busLabel = "%s : %s - %s %s"%(SUPPORTED_BUS_TYPE[msg['hash']['type']], msg['hash']['name'], msg['hash']['speed'], SUPPORTED_SPEED_UNIT[msg['hash']['type']])
      bus.addItem(busLabel + " *", msg['hash'])
      bus.setCurrentIndex(i)

    bus.setSizePolicy(sizePolicy)

    titleId = QLabel(QCoreApplication.translate("GENERIC","ID") + " :")
    fldId = QLineEdit()
    fldId.setPlaceholderText(QCoreApplication.translate("GENERIC","ID"))
    fldId.setValidator(self.idValidator)

    if model == "activ":
      fldId.setMaximumWidth(90)
      itemLayout.addWidget(bus, 0, 1, 1, 4)
      itemLayout.addWidget(titleId, 0, 5, 1, 1)
      itemLayout.addWidget(fldId, 0, 6, 1, 2)
      self.body.activeMsg.setItemWidget(item, itemWidget)
    else:
      fldId.setMaximumWidth(60)
      itemLayout.addWidget(bus, 0, 1, 1, 3)
      itemLayout.addWidget(titleId, 0, 4, 1, 1)
      itemLayout.addWidget(fldId, 0, 5, 1, 1)

      titleInterval = QLabel(QCoreApplication.translate("COMMAND","INTERVAL") + " :")
      itemLayout.addWidget(titleInterval, 0, 6, 1, 1)
      fldInterval = QLineEdit()
      fldInterval.setPlaceholderText("ms")
      fldInterval.setValidator(QIntValidator(0, REPLAY.MAX_WAIT_TIME * 1000, self))
      if msg != None:
        fldInterval.setText(msg['interval'])
      fldInterval.setMaximumWidth(60)
      itemLayout.addWidget(fldInterval, 0, 7, 1, 1)

    if msg != None:
      fldId.setText(msg['id'])

    for i in range(1, 9):
      byte = QLineEdit()
      byte.setMaximumWidth(60)
      byte.setMaxLength(7)
      byte.setPlaceholderText(QCoreApplication.translate("GENERIC","BYTE") + " %s"%i)
      byte.setSizePolicy(sizePolicy)
      byte.setValidator(self.byteValidator)
      if msg != None:
        if len(msg['bytes']) >= i:
          byte.setText(msg['bytes'][i-1])
      itemLayout.addWidget(byte, 1, i -1)

    self.body.constantMsg.setItemWidget(item, itemWidget)
    self.updateSaveBtn()


  def gatherCommands(self):
    cmdList = {"const":[], "activ":[]}
    fuzzId = 0
    fuzzBytes = 0

    listWidgets = [self.body.activeMsg, self.body.constantMsg]
    for listWiget in listWidgets:
      for r in range(0, listWiget.count()):
        item = listWiget.item(r)
        widget = listWiget.itemWidget(item)
        layout = widget.layout()
        if widget.property('type') == 'pause':
          duration = layout.itemAtPosition(0, 1).widget().text()
          if len(duration) > 0:
            cmdList['activ'].append({"type":"pause", "duration":duration})
        else:
          cmd = {'type':widget.property('type')}
          cmd['hash'] = layout.itemAtPosition(0,1).widget().currentData()
          if widget.property('type') == 'activ':
            cmd['id'] = layout.itemAtPosition(0, 6).widget().text().replace(" ","")
            if "@" in cmd['id']:
              fuzzId += 1
          else:
            cmd['id'] = layout.itemAtPosition(0, 5).widget().text().replace(" ","")
            cmd['interval'] = layout.itemAtPosition(0, 7).widget().text()
          bytes = []
          fuzzed = False
          for i in range(0, 8):
            byte= layout.itemAtPosition(1, i).widget().text().replace(" ","")
            if "@" in byte:
              fuzzed = True
            bytes.append(byte)
          if fuzzed == True:
            fuzzBytes += 1
          cmd['bytes'] = bytes

          if fuzzBytes > 1 or fuzzId > 1:
            return self.showCmdError("CANNOT_FUZZ_MULTIPLE_MSG", cmd['id'])

          if cmd['hash'] != False and len(cmd['id']) > 0:
            if self.checkCmdValidity(cmd) == True:
              cmdList[widget.property('type')].append(cmd)
            else:
              return False
    return cmdList


  def checkCmdValidity(self, cmd):
    if cmd['hash'] == False:
      return self.showCmdError("BUS_NOTE_SET", cmd['id'])
    # ID
    if '[' in cmd['id'] or '@' in cmd['id'] or ']' in cmd['id']:
      if cmd['type'] == 'const':
        return self.showCmdError("FUZZING_NOT_ALLOWED_IN_CONSTANTS", cmd['id'])
      if re.search("^\[([0-9A-F]{1,8})@([0-9A-F]{1,8})\]$", cmd['id']):
        ids = cmd['id'][1:-1].split("@")
        if int(ids[0],16) >= int(ids[1],16):
          return self.showCmdError("FUZZING_ORDER_ERROR", cmd['id'])
      else:
        return self.showCmdError("INVALID_ID_FUZZING", cmd['id'])
    elif re.search(self.regexpFormula, cmd['id']): # Check arithmetic
        try:
          cmd_ = self.formatFormula(cmd['id'])
          x = eval(cmd_)
        except:
          return self.showCmdError("INVALID_FORMULA", cmd['id'])
    else:
      try:
        decimalValue = int(cmd['id'], 16)
        if decimalValue < 0 or decimalValue > ID_MAX_VALUE:
          return self.showCmdError("ID_OUT_OF_RANGE", cmd['id'])
      except:
        return self.showCmdError("INVALID_ID_VALUE", cmd['id'])

    # BYTES
    for i in range(0, 8):
      if len(cmd['bytes'][i]) > 0:
        if '[' in cmd['bytes'][i] or '@' in cmd['bytes'][i] or ']' in cmd['bytes'][i]:
          if re.search("^\[([0-9A-F]{1,2})@([0-9A-F]{1,2})\]$", cmd['bytes'][i]):
            bytes = cmd['bytes'][i][1:-1].split("@")
            if int(bytes[0],16) >= int(bytes[1],16):
              return self.sbyteshowCmdError("FUZZING_ORDER_ERROR", cmd['bytes'][i])
          else:
            return self.showCmdError("INVALID_BYTE_FUZZING", cmd['bytes'][i])
        elif re.search(self.regexpFormula, cmd['bytes'][i]):
          try:
            cmd_ = self.formatFormula(cmd['bytes'][i])
            x = eval(cmd_)
          except:
            return self.showCmdError("INVALID_FORMULA", cmd['bytes'][i])
        else:
          try:
            decimalValue = int(cmd['bytes'][i], 16)
            if decimalValue < 0 or decimalValue > BYTE_MAX_VALUE:
              return self.showCmdError("BYTE_OUT_OF_RANGE", cmd['bytes'][i])
          except:
            return self.showCmdError("INVALID_BYTE_VALUE", cmd['bytes'][i])
    self.hideCmdError()
    return True


  def formatFormula(self, cmd):
    formula = cmd.lower().replace("$","self.")
    formula = formula.replace(" ","")
    formula = re.split(self.regexpOperands, formula)
    for i in range(0,len(formula)):
      if len(formula[i])> 0 and not re.search(self.regexNonBytes, formula[i]):
        formula[i] = str(int(formula[i],16))
    return "".join(formula)


  def showCmdError(self, errMsg, data=None):
    self.body.errorMsg.show()
    if data != None:
      logging.debug("ERROR %s ON %s"%(errMsg, data))
      self.body.errorMsg.setText(QCoreApplication.translate("CMD",errMsg + " : " + data))
    else:
      logging.debug("ERROR %s"%(errMsg))
      self.body.errorMsg.setText(QCoreApplication.translate("CMD",errMsg))
    return False


  def hideCmdError(self):
    self.body.errorMsg.hide()


  def playCmd(self):
    self.initFuzzBytes()
    self.hideCmdError()
    cmdList = self.gatherCommands()
    if cmdList != False:

      self.frameSrc = []
      self.initMsg = []
      self.startPause = 0
      self.endPause = 0

      timeModulo = 0
      for cmd in cmdList['const']:
        self.frameSrc.append(self.craftFrameSrc(cmd, 'const'))

      counter = 0
      for cmd in cmdList['activ']:
        counter += 1
        if cmd['type'] == "pause":
          timeModulo += int(cmd['duration'])
          if counter == 1:
            self.startPause = int(cmd['duration'])
          if counter == len(cmdList['activ']):
            self.endPause = int(cmd['duration'])
        else:
          self.frameSrc.append(self.craftFrameSrc(cmd, 'activ', timeModulo))

      self.generateAndTransmitFrames()


  def craftFrameSrc(self, cmd, cmdType, timeModulo=None):
    craftedFrameSrc = {'cmdType':cmdType,'type':cmd['type'], 'hash':cmd['hash'], 'count':0}
    if '@' in cmd['id']:
      self.fuzzBytes[0]['isFuzzed'] = True
      ids = cmd['id'][1:-1].split("@")
      self.fuzzBytes[0]['min'] = int(ids[0],16)
      self.fuzzBytes[0]['max'] = int(ids[1], 16)
      craftedFrameSrc['id'] = "self.bi"
    elif re.search(self.regexpFormula, cmd['id']):
      craftedFrameSrc['id'] = self.formatFormula(cmd['id'])
    else:
      craftedFrameSrc['id'] = int(cmd['id'], 16)
    craftedFrameSrc['bytes'] = []
    for i in range(0, 8):
      if '@' in cmd['bytes'][i]:
        self.fuzzBytes[i+1]['isFuzzed'] = True
        bytes = cmd['bytes'][i][1:-1].split("@")
        self.fuzzBytes[i+1]['min'] = int(bytes[0],16)
        self.fuzzBytes[i+1]['max'] = int(bytes[1],16)
        craftedFrameSrc['bytes'].append("self.b%s"%(i+1))
      elif re.search(self.regexpFormula, cmd['bytes'][i]):
        craftedFrameSrc['bytes'].append(self.formatFormula(cmd['bytes'][i]))
      else:
        if len(cmd['bytes'][i]) > 0:
          craftedFrameSrc['bytes'].append(int(cmd['bytes'][i], 16))
        else:
          break
    craftedFrameSrc['len'] = len(craftedFrameSrc['bytes'])
    if timeModulo != None:
      craftedFrameSrc['ts'] = timeModulo
    else:
      craftedFrameSrc['ts'] = int(cmd['interval'])

    return craftedFrameSrc


  def setFuzzByteValue(self, idx, value):
    if idx == 0:
      self.bi = value
    elif idx == 1:
      self.b1 = value
    elif idx == 2:
      self.b2 = value
    elif idx == 3:
      self.b3 = value
    elif idx == 4:
      self.b4 = value
    elif idx == 5:
      self.b5 = value
    elif idx == 6:
      self.b6 = value
    elif idx == 7:
      self.b7 = value
    elif idx == 8:
      self.b8 = value


  def generateAndTransmitFrames(self):
    fuzzMaster = None
    fuzzEnded = False
    fuzzValues = []
    fuzzQty = 1

    for i in range(0, 9):
      if self.fuzzBytes[i]['isFuzzed'] == True:
        if fuzzMaster == None:
          fuzzMaster = i
        fuzzValues.append({"pos":i, "value":self.fuzzBytes[i]['min'], "min":self.fuzzBytes[i]['min'], "max":self.fuzzBytes[i]['max']})
        fuzzQty *= (self.fuzzBytes[i]['max']-self.fuzzBytes[i]['min'])
        self.setFuzzByteValue(i, self.fuzzBytes[i]['min'])
    bytesToFuzz = len(fuzzValues)
    repeat = self.body.fldRepeat.text()
    if len(repeat) == 0:
      repeat = 0
    else:
      repeat = int(repeat)
      fuzzQty *= repeat+1

    fuzzQty *= len(self.frameSrc)
    if fuzzQty >= CMD.FUZZ_QTY_LIMIT:
      return self.showCmdError("FUZZING_TOO_LARGE", CMD.FUZZ_QTY_LIMIT)

    if fuzzQty >= CMD.FUZZ_QTY_WARN:
      msgBox = QMessageBox()
      msgBox.setText(QCoreApplication.translate("COMMAND","WARNING_HUGE_COMMAND"))
      msgBox.setInformativeText(QCoreApplication.translate("COMMAND","WARNING_HUGE_COMMAND_DETAILS"))
      msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
      msgBox.setDefaultButton(QMessageBox.Ok)
      self.centerMsg(msgBox)
      choice = msgBox.exec()

      if choice == QMessageBox.Cancel:
        return False

    self.generateFrames(repeat, fuzzMaster, fuzzEnded, fuzzValues, bytesToFuzz, fuzzQty)


  def generateFrames(self, repeat, fuzzMaster, fuzzEnded, fuzzValues, bytesToFuzz, fuzzQty):
    frames = []
    ts = 0
    maxTs = self.frameSrc[len(self.frameSrc) - 1]['ts']

    if (maxTs == 0):
      maxTs = 0.1

    counter = 1

    if fuzzQty > CMD.FUZZ_QTY_WARN:
      progress = QProgressDialog("", "", 0, 0, self)
      progress.setCancelButton(None)
      progress.setWindowModality(Qt.WindowModal)
      progress.setWindowTitle(QCoreApplication.translate("COMMAND","COMPUTING_FRAMES"))
      progress.setLabelText(QCoreApplication.translate("COMMAND","COMPUTING_FRAMES_DETAILS"))
      progress.setMinimum(0)
      progress.setMaximum(fuzzQty)
      progress.setAutoClose(True)
      progress.canceled.connect(lambda: self.threadStopManager['generateCmd'].set())
      progress.show()

    else:
      progress = None

    self.threadStopManager['generateCmd'].clear()

    while not self.threadStopManager['generateCmd'].is_set():
      for rpt in range(-1, repeat):
        sequenceEnded = False
        isEndPause = False
        while sequenceEnded == False:

          for i in range(0, len(self.frameSrc)):
            if ((self.frameSrc[i]['cmdType'] == 'activ' and isEndPause == False and
                  (maxTs < 1 or (self.frameSrc[i]['ts'] != 0 and ts > 0 and ts%self.frameSrc[i]['ts']==0)) ) or
                (self.frameSrc[i]['cmdType'] == 'const') and
                  ((ts == 0 and self.frameSrc[i]['ts'] == 0) or (self.frameSrc[i]['ts'] != 0 and ts != 0 and ts%self.frameSrc[i]['ts'] == 0))):
              try:
                data = {}
                if type(self.frameSrc[i]['id']) == int:
                  data['id'] = self.frameSrc[i]['id']
                else:
                  data['id'] = eval(self.frameSrc[i]['id'])
                if data['id'] > 0x7FF:
                  data['extendedId'] = True
                else:
                  data['extendedId'] = False
                data['len'] = self.frameSrc[i]['len']
                bytes = []
                bytesStr = []
                for y in range(0, len(self.frameSrc[i]['bytes'])):
                  if type(self.frameSrc[i]['bytes'][y]) == int:
                    b = self.frameSrc[i]['bytes'][y]
                  else:
                    b = eval(self.frameSrc[i]['bytes'][y])
                  bytes.append(b)
                  bytesStr.append(str(b))
                data['msg'] = bytes
                data['type'] = self.frameSrc[i]['hash']['type']
                data['ts'] = ts / 1000
                data['preset'] =  self.frameSrc[i]['hash']['hash']
                data['presetLabel'] =  "%s - %s %s"%(self.frameSrc[i]['hash']['name'],self.frameSrc[i]['hash']['speed'],SUPPORTED_SPEED_UNIT[self.frameSrc[i]['hash']['type']])
                data['busName'] =  self.frameSrc[i]['hash']['name']
                frames.append(data)

                if self.frameSrc[i]['cmdType'] == 'const' and self.frameSrc[i]['ts'] == 0:
                  self.initMsg.append(data)

                if progress != None:
                  counter += 1
                  progress.setValue(counter)
                  QApplication.processEvents()
              except:
                logging.warn("ERROR COMPUTING FRAMES %s"%sys.exc_info()[0])
          if (maxTs < 1 or (ts > 0 and ts%(maxTs)  == 0)) and self.endPause == 0:
            sequenceEnded = True
            isEndPause = False
          elif self.endPause > 0 and (ts > 0 and ts%(round(maxTs) + self.endPause)  == 0):
            sequenceEnded = True
            isEndPause = False
          else:
            if self.endPause > 0 and (maxTs < 1 or (ts > 0 and ts%(maxTs)  == 0)):
              isEndPause = True
          ts += 1

      if bytesToFuzz == 0:
        self.threadStopManager['generateCmd'].set()
      else:
        for i in range(0, bytesToFuzz):
          idx = bytesToFuzz - i -1
          fuzzValues[idx]["value"] += 1
          self.setFuzzByteValue(fuzzValues[idx]["pos"], fuzzValues[idx]["value"])
          if fuzzValues[idx]["value"] > fuzzValues[idx]["max"]:
            if fuzzValues[idx]["pos"] == fuzzMaster:
              self.threadStopManager['generateCmd'].set()
              break
            fuzzValues[idx]["value"] = 0
            self.setFuzzByteValue(fuzzValues[idx]["pos"], fuzzValues[idx]["value"])
          else:
            break
    if progress != None:
      progress.setLabelText(QCoreApplication.translate("COMMAND","LOADING_REPLAY_MODULE"))

    self.appSignals.replayCommand.emit({"frames":frames,"initMsg":self.initMsg,"startPause":self.startPause,"endPause":self.endPause})

    if progress != None:
        progress.close()


  def changeSrc(self):
    self.cmdSrc = self.body.comboCmdSrc.currentData()
    self.loadComboSelector()


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


  def drawDialogBody(self):
    for elt in CMD.SRC:
      self.body.comboCmdSrc.addItem(QCoreApplication.translate("GENERIC",elt),CMD.SRC[elt])

    self.body.errorMsg.hide()
    self.body.btnDelete.hide()
    self.body.btnShare.hide()
    self.body.btnImport.hide()
    self.body.btnSave.setDisabled(True)
    self.body.btnPlay.setDisabled(True)
    self.loadComboSelector()
