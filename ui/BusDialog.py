from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import qtawesome as qta

import time
import hashlib

from modules.Constants import *
from ui.ModelDialog import ModelDialog, UCValidator
from ui.BusForm import Ui_BUS

class BusList(QWidget, Ui_BUS):
  def __init__(self):
   super().__init__()
   self.setupUi(self)


class BusDialog(ModelDialog):
  def __init__(self, refWindow, busType):
    super().__init__()

    self.getMainVariables(refWindow)

    self.gwLock = False
    self.presetLock = False

    self.busType = busType
    self.busLabel = SUPPORTED_BUS_TYPE[busType]

    # Need update
    self.widgets = {"preset":{}, "label":{}, "speed":{},"gw":{},"btn":{}} # Store some widgets ref for R/W operations

    # Close btn
    self.closeBtn = QPushButton()
    self.closeBtn.setIcon(qta.icon('fa.close',color='white'))
    self.closeBtn.setText(QCoreApplication.translate("DIALOG", "CLOSE"))
    self.closeBtn.setProperty("cssClass","btn-danger")
    self.closeBtn.setCursor(Qt.PointingHandCursor)
    self.closeBtn.clicked.connect(self.reject)
    self.setBottomButtons(self.closeBtn)

    # Loading body template
    self.dialogTitle.setText(QCoreApplication.translate("BUS", "%s_BUS_MANAGEMENT"%self.busLabel))
    self.body = BusList()
    self.dialogBody.addWidget(self.body)

    # Editing grid
    self.drawDialogBody()


  def drawDialogBody(self):
    self.body.fldManufacturer.hide()
    self.body.busEditor.hide()

    # Interface tab
    self.listInterfaces()

    # Bus tab
    self.listDefinedBus()

    self.populateComboBox(self.body.fldSpeed, SUPPORTED_SPEED[self.busType], SUPPORTED_SPEED_UNIT[self.busType])
    self.populateComboBox(self.body.fldWire10, WIRE_COLOR)
    self.populateComboBox(self.body.fldWire11, WIRE_COLOR)
    self.populateComboBox(self.body.fldWire20, WIRE_COLOR)
    self.populateComboBox(self.body.fldWire21, WIRE_COLOR)
    self.populateComboBox(self.body.fldOBD1, OBD_PORTS)
    self.populateComboBox(self.body.fldOBD2, OBD_PORTS)

    # Icons
    self.body.btnAddBus.setIcon(qta.icon("fa5s.plus-square", color="white"))
    self.body.editorCancel.setIcon(qta.icon('fa.close',color='white'))
    self.body.editorSave.setIcon(qta.icon('fa.save',options=[{'color':'white','color_active':'white', 'color_disabled':'black'}]))

    # Signals
    self.body.btnDelete.clicked.connect(lambda: self.delBus())
    self.body.btnAddBus.clicked.connect(lambda:self.showEditor())
    self.body.editorCancel.clicked.connect(lambda:self.hideEditor())
    self.body.editorSave.clicked.connect(lambda:self.saveBusPreset())
    self.body.fldName.textChanged.connect(lambda:self.unlockSaveBtn())
    self.body.fldSpeed.currentIndexChanged.connect(lambda:self.unlockSaveBtn())
    self.body.fldPreset.currentIndexChanged.connect(lambda x: self.applyPreset(x))

    upperCaseValidator = UCValidator(self)
    self.body.fldName.setValidator(upperCaseValidator)

  #
  # GENERIC METHODS
  #
  def populateComboBox(self, comboBox, values, unit="", hasData = False):
    comboBox.addItem("-")
    for elt in values:
      if hasData != False:
        data = elt[hasData]
        label = elt['label']
      else:
        data = elt
        label = str(elt)
      comboBox.addItem(QCoreApplication.translate("BUS",label + " " + unit), data)


  def autoSelectComboBox(self, comboBox, values, value):
      if value == None:
        comboBox.setCurrentIndex(0)
      else:
        for i in range(0, len(values)):
          if values[i] == value:
            comboBox.setCurrentIndex(i + 1)
            break


  #
  # INTERFACES MANAGEMENT
  #
  def listInterfaces(self):
    self.removeLines(self.body.ifaceGridLayout)

    self.busPresets = []
    busCursor = self.db.analysis.find({"id": self.analysis['id']}, {"bus": 1})
    if busCursor.count() == 1:
      for bus in busCursor[0]['bus']:
        if bus['type'] == self.busType:
          preset = {"label": bus['name'], "speed": bus['speed'], "init": bus['init'], "hash":bus['hash'],
                    "version": bus['version'], "strSpeed" :  str(bus['speed']) + ' ' +  SUPPORTED_SPEED_UNIT[self.busType],
                    "altLabel": bus['name'] + ' - ' + str(bus['speed']) + ' ' +  SUPPORTED_SPEED_UNIT[self.busType]}

          self.busPresets.append(preset)
    self.busPresets = sorted(self.busPresets, key=lambda x: (x['label']))

    # Interfaces tab
    busQty = 0
    if len(self.interfaces.bus) > 0:
      busOrder = sorted(self.interfaces.bus, key=lambda x: (self.interfaces.bus[x]['deviceLabel'], self.interfaces.bus[x]['name']))
      for id in busOrder:
        if self.interfaces.bus[id]['type'] == self.busType:
          self.addInterface(id)
          busQty += 1
    if busQty == 0:
      noIfaces = QLabel(QCoreApplication.translate("BUS","NO_AVAILABLE_BUS"),self.body.busGridWidget)
      noIfaces.setObjectName("noBus")
      self.body.ifaceGridLayout.addWidget(noIfaces, 1, 0, 1, 4, Qt.AlignCenter)


  def addInterface(self, id):
    _translate = QCoreApplication.translate
    rowIndex = self.body.ifaceGridLayout.rowCount()

    sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)

    ifaceWidget = QWidget(self.body.gridIface)
    ifaceWidget.setSizePolicy(sizePolicy)
    ifaceWidgetLayout = QHBoxLayout(ifaceWidget)
    ifaceWidgetLayout.setContentsMargins(0, 0, 0, 0)
    ifaceDeviceName = QLabel(self.interfaces.bus[id]['deviceLabel'], ifaceWidget)
    ifaceDeviceName.setSizePolicy(sizePolicy)
    ifaceName = QLabel(self.interfaces.bus[id]['name'], ifaceWidget)
    ifaceName.setSizePolicy(sizePolicy)
    ifaceWidgetLayout.addWidget(ifaceDeviceName)
    ifaceWidgetLayout.addWidget(ifaceName)
    self.body.ifaceGridLayout.addWidget(ifaceWidget, rowIndex, 0, 1, 1)

    busPreset = QComboBox(self.body.gridIface)
    busPreset.setSizePolicy(sizePolicy)
    self.widgets['preset'][id] = busPreset
    self.updatePresetItems(id)
    busPreset.currentIndexChanged.connect(lambda: self.updatePreset(id))
    self.body.ifaceGridLayout.addWidget(busPreset, rowIndex, 1, 1, 1)


    busLabel = QLineEdit(self.body.gridIface)
    busLabel.setSizePolicy(sizePolicy)
    busLabel.setText(self.interfaces.bus[id]['label'])
    busLabel.setPlaceholderText(self.interfaces.bus[id]['name'])
    self.body.ifaceGridLayout.addWidget(busLabel, rowIndex, 2, 1, 1)
    self.widgets['label'][id] = busLabel

    busSpeed = QLineEdit(self.body.gridIface)
    busSpeed.setSizePolicy(sizePolicy)
    busSpeed.setDisabled(True)
    if self.interfaces.bus[id]['preset']!= None:
      for preset in self.busPresets:
        if preset['hash'] == self.interfaces.bus[id]['preset']:
          busSpeed.setText(preset['strSpeed'])
          break

    self.body.ifaceGridLayout.addWidget(busSpeed, rowIndex, 3, 1, 1)
    self.widgets['speed'][id] = busSpeed

    busGw = QComboBox(self.body.gridIface)
    busGw.setSizePolicy(sizePolicy)
    self.widgets['gw'][id] = busGw
    self.updateGwItems(id)
    busGw.currentIndexChanged.connect(lambda x:self.updateGw(id, x))
    self.body.ifaceGridLayout.addWidget(busGw, rowIndex, 4, 1, 1)

    busSwitch = QPushButton(self.body.gridIface)
    if busPreset.currentIndex() < 1:
      busSwitch.setDisabled(True)
      busSwitch.setCursor(Qt.ArrowCursor)
    else:
      busSwitch.setCursor(Qt.PointingHandCursor)
    busSwitch.setObjectName("busSwitch_" + id)
    busSwitch.clicked.connect(lambda :self.switchBusState(id))
    self.body.ifaceGridLayout.addWidget(busSwitch, rowIndex, 5, 1, 1, Qt.AlignCenter)
    self.widgets['btn'][id] = busSwitch

    if self.interfaces.bus[id]['active'] == True:
      self.lockBusParams(id, busState = 1)
    elif self.interfaces.bus[id]['preset'] != None:
      self.lockBusParams(id, busState = 0)
    else:
      self.lockBusParams(id, busState = -1)


  def lockBusParams(self, id, busState = -1):
    if busState == -1:
      self.widgets['btn'][id].setIcon(qta.icon('fa.play-circle', color='white', color_disabled='grey'))
      self.widgets['btn'][id].setProperty("cssClass","btn-disabled")
      self.widgets['btn'][id].setStyle(self.widgets['btn'][id].style())
      self.widgets['btn'][id].setDisabled(True)
      self.widgets['btn'][id].setCursor(Qt.ArrowCursor)
      self.widgets['gw'][id].setDisabled(True)
      self.widgets['gw'][id].setCursor(Qt.ArrowCursor)
      self.widgets['preset'][id].setDisabled(False)
      self.widgets['preset'][id].setCursor(Qt.PointingHandCursor)
      self.widgets['label'][id].setDisabled(True)
    elif busState == 0:
      self.widgets['btn'][id].setIcon(qta.icon('fa.play-circle', color='white', color_disabled='grey'))
      self.widgets['btn'][id].setProperty("cssClass","btn-success")
      self.widgets['btn'][id].setStyle(self.widgets['btn'][id].style())
      self.widgets['btn'][id].setDisabled(False)
      self.widgets['btn'][id].setCursor(Qt.PointingHandCursor)
      self.widgets['gw'][id].setDisabled(False)
      self.widgets['gw'][id].setCursor(Qt.PointingHandCursor)
      self.widgets['preset'][id].setDisabled(False)
      self.widgets['preset'][id].setCursor(Qt.PointingHandCursor)
      self.widgets['label'][id].setDisabled(False)
    else:
      self.widgets['btn'][id].setIcon(qta.icon('fa.stop-circle', color='white', color_disabled='grey'))
      self.widgets['btn'][id].setProperty("cssClass","btn-danger")
      self.widgets['btn'][id].setStyle(self.widgets['btn'][id].style())
      self.widgets['btn'][id].setDisabled(False)
      self.widgets['btn'][id].setCursor(Qt.PointingHandCursor)
      self.widgets['gw'][id].setDisabled(True)
      self.widgets['gw'][id].setCursor(Qt.ArrowCursor)
      self.widgets['preset'][id].setDisabled(True)
      self.widgets['preset'][id].setCursor(Qt.ArrowCursor)
      self.widgets['label'][id].setDisabled(True)


  def switchBusState(self, id):
    if self.interfaces.bus[id]['active'] == True:
      self.appSignals.switchBus.emit({"id":id,"dialog":self})
      # If GW, we also shut the related bus
      if self.interfaces.bus[id]['gw'] != None:
        self.appSignals.switchBus.emit({"id":self.interfaces.bus[id]['gw'],"dialog":self})
    else:
      self.appSignals.switchBus.emit({"id":id,"dialog":self})
      if len(self.widgets['label'][id].text()) > 0:
        self.interfaces.bus[id]['label'] = self.widgets['label'][id].text()
      else:
        self.interfaces.bus[id]['label'] = self.interfaces.bus[id]['name']
      if self.interfaces.bus[id]['gw'] != None and self.gwLock == False:
        self.gwLock = True
        self.switchBusState(self.interfaces.bus[id]['gw'])
        self.gwLock = False

    if self.gwLock == False:
      for busId in self.widgets['gw']:
        self.updateGwItems(busId)


  def updatePresetItems(self, busId):
    presetWidget = self.widgets['preset'][busId]
    presetWidget.addItem("-")
    for i in range(0, len(self.busPresets)):
      presetWidget.addItem(self.busPresets[i]['altLabel'], self.busPresets[i]['hash'])
      if self.interfaces.bus[busId]['preset'] == self.busPresets[i]['hash']:
        presetWidget.setCurrentIndex(i+1)


  def updatePreset(self, busId):
    if self.widgets['preset'][busId].currentIndex() > 0:
      hash = self.widgets['preset'][busId].currentData()
      for preset in self.busPresets:
        if preset['hash'] == hash:
          self.interfaces.bus[busId]['preset'] = hash
          self.interfaces.bus[busId]['presetLabel'] = preset['altLabel']
          self.interfaces.bus[busId]['speed'] = preset['speed']
          self.interfaces.bus[busId]['label'] = preset['label']
          self.interfaces.bus[busId]['init'] = preset['init']
          self.interfaces.bus[busId]['version'] = preset['version']
          self.widgets['speed'][busId].setText(preset['strSpeed'])
          self.widgets['label'][busId].setText(preset['label'])
          self.lockBusParams(busId, 0)
          break
    else:
      self.lockBusParams(busId, -1)
      self.interfaces.bus[busId]['preset'] = None
      self.interfaces.bus[busId]['speed'] = None
      self.interfaces.bus[busId]['label'] = None
      self.widgets['speed'][busId].setText("")
      self.widgets['label'][busId].setText("")


  def updateGw(self, busId, idx):
    if self.gwLock == False:
      self.gwLock = True
      # Revert any previous assigned GW
      if self.interfaces.bus[busId]['gw'] != None:
        self.widgets['gw'][self.interfaces.bus[busId]['gw']].setCurrentIndex(0)
        self.interfaces.bus[self.interfaces.bus[busId]['gw']]['gw'] = None

      if idx > 0:
        dstGwId = self.widgets['gw'][busId].currentData()
        if self.interfaces.bus[dstGwId]['gw'] != None:
          self.widgets['gw'][self.interfaces.bus[dstGwId]['gw']].setCurrentIndex(0)
          self.interfaces.bus[self.interfaces.bus[dstGwId]['gw']]['gw'] = None
        self.widgets['preset'][dstGwId].setCurrentIndex(self.widgets['preset'][busId].currentIndex())
        self.interfaces.bus[busId]['gw'] = dstGwId

        for i in range(0, self.widgets['gw'][dstGwId].count()):
          if self.widgets['gw'][dstGwId].itemData(i) == busId:
            self.widgets['gw'][dstGwId].setCurrentIndex(i)
            self.interfaces.bus[dstGwId]['gw'] = busId
            break
      else:
        self.interfaces.bus[busId]['gw'] = None
      self.gwLock = False


  def listAvailableGw(self, busId):
    gwList = []
    busOrder = sorted(self.interfaces.bus, key=lambda x: (self.interfaces.bus[x]['name']))
    for id in busOrder:
      if self.interfaces.bus[id]['type'] == self.busType and id != busId:
        if self.interfaces.bus[id]['active'] == False or (self.interfaces.bus[busId]['gw'] == id and self.interfaces.bus[busId]['active'] == True ):
          gwList.append(id)
    return gwList


  def updateGwItems(self, busId):
    gwWidget = self.widgets['gw'][busId]
    self.gwLock = True
    itemQty = gwWidget.count()
    for i in range(0, itemQty):
      gwWidget.removeItem(0)

    gwList = self.listAvailableGw(busId)
    gwWidget.addItem("-")
    for i in range(0, len(gwList)):
      gwWidget.addItem(self.interfaces.bus[gwList[i]]['name'], self.interfaces.bus[gwList[i]]['id'])
      if self.interfaces.bus[busId]['gw'] and self.interfaces.bus[busId]['gw'] == gwList[i]:
        gwWidget.setCurrentIndex(i+1)
    self.gwLock = False


  #
  # BUS MANAGEMENT
  #

  # Bus list
  def listDefinedBus(self):
    self.removeLines(self.body.busListLayout)
    analysisCursor = self.db.analysis.find({"id": self.analysis['id'], "owner":self.user['uid'],"bus.type":self.busType},{"_id":0})
    if analysisCursor.count() > 0:
      for analysis in analysisCursor:
        for bus in analysis['bus']:
          self.addBus(bus)
    else:
      noBus = QLabel(QCoreApplication.translate("BUS","NO_AVAILABLE_BUS"),self.body.busList)
      self.body.busListLayout.addWidget(noBus, 1, 0, 1, 4, Qt.AlignCenter)


  def addBus(self, bus):
    _translate = QCoreApplication.translate
    rowIndex = self.body.busListLayout.rowCount()

    sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)

    sizePolicyAlt = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    busLabel = QLabel(bus['name'], self.body.busList)
    busLabel.setSizePolicy(sizePolicy)
    self.body.busListLayout.addWidget(busLabel, rowIndex, 0, 1, 1)

    speedLabel = QLabel(str(bus['speed']) + " " +SUPPORTED_SPEED_UNIT[self.busType], self.body.busList)
    speedLabel.setSizePolicy(sizePolicy)
    self.body.busListLayout.addWidget(speedLabel, rowIndex, 1, 1, 1)

    if len(bus['wire']) > 0:
      wireLabel = QLabel(self.parseWireInfo(bus['wire'],"<br />"), self.body.busList)
      wireLabel.setSizePolicy(sizePolicy)
      self.body.busListLayout.addWidget(wireLabel, rowIndex, 2, 1, 1)

    editBtn = QPushButton(_translate("MAIN","EDIT"), self.body.busList)
    editBtn.setProperty("cssClass","btn-primary")
    editBtn.setIcon(qta.icon("fa5.edit", color="white"))
    editBtn.setCursor(Qt.PointingHandCursor)
    editBtn.setSizePolicy(sizePolicyAlt)
    editBtn.clicked.connect(lambda: self.showEditor(bus['hash']))
    self.body.busListLayout.addWidget(editBtn, rowIndex, 3, 1, 1, Qt.AlignRight)


  # Bus editor
  def unlockSaveBtn(self):
    if len(self.body.fldName.text()) > 0 and self.body.fldSpeed.currentIndex() > 0:
      self.body.editorSave.setDisabled(False)
      self.body.editorSave.setProperty("cssClass","btn-success")
      self.body.editorSave.setStyle(self.body.editorSave.style())
    else:
      self.body.editorSave.setDisabled(True)
      self.body.editorSave.setProperty("cssClass","btn-disabled")
      self.body.editorSave.setStyle(self.body.editorSave.style())


  def getBusHash(self, name, speed, manufacturer):
    name = hashlib.md5(name.encode('utf8')).hexdigest()
    manufacturer = hashlib.md5(manufacturer.encode('utf8')).hexdigest()
    strToHash = self.busType + name + str(speed) + manufacturer
    strToHash = strToHash.encode('utf8')
    return hashlib.sha224(strToHash).hexdigest()


  def getWireInfo(self, wireId=1):
    wire = None
    color = None
    obd = None
    if wireId == 1:
      if self.body.fldWire10.currentIndex() > 0:
        color = [self.body.fldWire10.currentData()]
        if self.body.fldWire11.currentIndex() > 0:
          color.append(self.body.fldWire11.currentData())
      if self.body.fldOBD1.currentIndex() > 0:
        obd = self.body.fldOBD1.currentData()
    else:
      if self.body.fldWire20.currentIndex() > 0:
        color = [self.body.fldWire20.currentData()]
        if self.body.fldWire21.currentIndex() > 0:
          color.append(self.body.fldWire21.currentData())
      if self.body.fldOBD2.currentIndex() > 0:
        obd = self.body.fldOBD2.currentData()
    if obd != None or color != None:
      wire = {"color":color,"obd":obd}
    return wire


  def saveBusPreset(self):
    bus = {}
    wire = []
    bus['type'] = self.busType
    bus['name'] = self.body.fldName.text()
    bus['speed'] = self.body.fldSpeed.currentData()
    if self.body.fldLinVersion.currentIndex() > 0:
      bus['version'] = self.body.fldLinVersion.currentData()
    else:
      bus['version'] = None
    if self.body.fldKlnInit.currentIndex() > 0:
      bus['init'] = self.body.fldKlnInit.currentData()
    else:
      bus['init'] = None

    bus['comment'] = self.body.fldComment.toPlainText()
    wire.append(self.getWireInfo(1))
    wire.append(self.getWireInfo(2))
    bus['wire'] = []
    for i in range(0,len(wire)):
      if wire[i] != None:
        bus['wire'].append(wire[i])
    bus['hash'] = self.getBusHash(bus['name'], bus['speed'], self.analysis['manufacturer'])

    saveData = True

    if self.editBus == False:
      busCursor = self.db.bus.find({"hash": bus['hash'], "type":self.busType}, {"_id":1})
      if busCursor.count() == 0:
        self.db.bus.insert({"name": bus['name'], "type": bus['type'], "speed": bus['speed'],
                              "manufacturer": self.analysis["manufacturer"], "hash": bus['hash']})

    # If hash altered, we remove the previous entry
    if self.editBus != False and bus['hash'] !=  self.editBus:

      msgBox = QMessageBox()
      msgBox.setText(QCoreApplication.translate("BUS","HASH_CHANGED"))
      msgBox.setInformativeText(QCoreApplication.translate("BUS","HASH_CHANGED_DETAILS"))
      msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
      msgBox.setDefaultButton(QMessageBox.Ok)
      self.centerMsg(msgBox)
      choice = msgBox.exec()

      if choice == QMessageBox.Ok:

        self.db.bus.update({"hash": self.editBus}, {"name": bus['name'], "type": bus['type'], "speed": bus['speed'],
                              "manufacturer": self.analysis["manufacturer"], "hash": bus['hash']})
        self.db.analysis.update({"id": self.analysis['id']},
                                  {"$pull":{"bus":{"hash": self.editBus}}})
        #self.db.analysis.update({"id": self.analysis['id'], "bus.hash": self.editBus},
        #                        {"$set":{"bus.$.hash": bus['hash']}})
        """
        self.db.sessions.update({"bus.hash": self.editBus, "analysis": self.analysis['id']},
                                {"$set":{"bus.$.hash": bus['hash']}})
        self.db.signals.update({"bus.hash": self.editBus, "analysis": self.analysis['id']},
                                {"$set":{"bus.$.hash": bus['hash']}})
        """
      else:
        saveData = False

    if saveData == True:
      self.db.analysis.update({"id": self.analysis['id'], "bus.hash":bus['hash']},
                              {"$set":{"bus.$.wire": bus['wire'], "bus.$.comment":bus['comment'],
                                        "bus.$.init":bus['init'], "bus.$.version": bus['version']}})
      self.db.analysis.update({"id": self.analysis['id']},{"$addToSet":{"bus":bus}, "$set":{"lastUpdate":time.time()}})

    self.hideEditor()


  def delBus(self):
    if self.editBus != False:
      msgBox = QMessageBox()
      msgBox.setText(QCoreApplication.translate("BUS","CONFIRM_BUS_DELETION"))
      msgBox.setInformativeText(QCoreApplication.translate("BUS","CONFIRM_BUS_DELETION_DETAILS"))
      msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
      msgBox.setDefaultButton(QMessageBox.Ok)
      self.centerMsg(msgBox)
      choice = msgBox.exec()

      if choice == QMessageBox.Ok:
        self.db.analysis.update({"id": self.analysis['id']},
                                {"$pull":{"bus":{"hash": self.editBus}}})
        """
        self.db.sessions.update({"bus.hash": self.editBus, "analysis": self.analysis['id']},
                                {"$set":{"bus.$.hash": bus['hash']}})
        self.db.signals.update({"bus.hash": self.editBus, "analysis": self.analysis['id']},
                                {"$set":{"bus.$.hash": bus['hash']}})
        """
        self.listDefinedBus()

        self.hideEditor()



  def hideEditor(self):
    self.listDefinedBus()
    self.listInterfaces()
    self.body.busEditor.hide()
    self.body.busList.show()


  def showEditor(self, editBus = False):
    self.body.busEditor.show()
    self.body.busList.hide()

    self.editBus = editBus
    self.initEditor()

    self.setBusNameAutocomplete()
    self.loadPresetValues()

    if self.editBus != False:
      busCursor = self.db.analysis.find({"bus.hash": editBus, "id":self.analysis['id']})
      if busCursor.count() == 1:
        for bus in busCursor[0]['bus']:
          if bus['hash'] == self.editBus:
            bus['manufacturer'] = busCursor[0]['manufacturer']
            self.fillEditor(bus)
            break
      self.body.editorSave.setDisabled(False)
      self.body.editorSave.setProperty("cssClass","btn-success")
      self.body.editorSave.setStyle(self.body.editorSave.style())
      self.body.btnDelete.show()
    else:
      self.body.editorSave.setDisabled(True)
      self.body.editorSave.setProperty("cssClass","btn-disabled")
      self.body.editorSave.setStyle(self.body.editorSave.style())
      self.body.btnDelete.hide()


  def initEditor(self):
    self.body.fldName.setText("")
    self.body.fldSpeed.setCurrentIndex(0)
    self.body.fldLinVersion.setCurrentIndex(0)
    if self.busType != "lin":
      self.body.labelLinVersion.hide()
      self.body.fldLinVersion.hide()
    self.body.fldKlnInit.setCurrentIndex(0)
    if self.busType != "kln":
      self.body.labelKlnInit.hide()
      self.body.fldKlnInit.hide()
    self.body.fldComment.setPlainText("")
    self.body.fldWire10.setCurrentIndex(0)
    self.body.fldWire11.setCurrentIndex(0)
    self.body.fldWire20.setCurrentIndex(0)
    self.body.fldWire21.setCurrentIndex(0)
    self.body.fldOBD1.setCurrentIndex(0)
    self.body.fldOBD2.setCurrentIndex(0)


  def fillEditor(self, busInfo):
    self.body.fldName.setText(busInfo['name'])
    self.body.fldManufacturer.setText(busInfo['manufacturer'])
    self.body.fldComment.setPlainText(busInfo['comment'])

    self.autoSelectComboBox(self.body.fldSpeed, SUPPORTED_SPEED[self.busType], busInfo['speed'])
    if len(busInfo['wire']) > 0:
      if busInfo['wire'][0]['color'] != None:
        self.autoSelectComboBox(self.body.fldWire10, WIRE_COLOR, busInfo['wire'][0]['color'][0])
        if len( busInfo['wire'][0]['color'] ) > 1:
          self.autoSelectComboBox(self.body.fldWire11, WIRE_COLOR, busInfo['wire'][0]['color'][1])
        else:
          self.autoSelectComboBox(self.body.fldWire11, WIRE_COLOR, None)
      self.autoSelectComboBox(self.body.fldOBD1, OBD_PORTS,  busInfo['wire'][0]['obd'])
    if len(busInfo['wire']) > 1:
      if busInfo['wire'][1]['color'] != None:
        self.autoSelectComboBox(self.body.fldWire20, WIRE_COLOR, busInfo['wire'][1]['color'][0])
        if len(busInfo['wire'][1]['color']) > 1:
          self.autoSelectComboBox(self.body.fldWire21, WIRE_COLOR, busInfo['wire'][1]['color'][1])
        else:
          self.autoSelectComboBox(self.body.fldWire21, WIRE_COLOR, None)
      self.autoSelectComboBox(self.body.fldOBD2, OBD_PORTS,  busInfo['wire'][1]['obd'])


  def setBusNameAutocomplete(self):
    busNameList = []
    busNameCursor = self.db.bus.find({"manufacturer":self.analysis['manufacturer'], "type":self.busType},
                                      {"_id":0, "name":1})
    if busNameCursor.count() > 0:
      for busName in busNameCursor:
        busNameList.append(busName['name'])
    busNameCompleter = QCompleter(busNameList, self.body.fldName)
    busNameCompleter.setCaseSensitivity(Qt.CaseInsensitive)
    self.body.fldName.setCompleter(busNameCompleter)

  # PRESETS
  def loadPresetValues(self):
    self.presetLock = True
    itemQty = self.body.fldPreset.count()
    for i in range(0, itemQty):
      self.body.fldPreset.removeItem(0)
    self.body.fldPreset.addItem("-")

    busCursor = self.db.bus.find({"manufacturer": self.analysis['manufacturer'], "type":self.busType},
                                    {"_id":0}).sort([("name",1),("speed",1)])
    presets = []
    if busCursor.count() > 0:
      variants = []
      for bus in busCursor:
        variantCursor = self.db.analysis.find({"bus.hash": bus['hash']},{"bus.$":1})
        variantCursor.sort([("model",1), ("year",-1)])
        for variant in variantCursor:
          if not variant['bus'][0]['wire'] in variants:
            variants.append(variant['bus'][0]['wire'])
          presets.append({"manufacturer":bus['manufacturer'], "name":bus['name'], "speed":bus['speed'],
                          "comment":variant['bus'][0]['comment'], "init":variant['bus'][0]['init'],
                          "version":variant['bus'][0]['version'],"hash":bus['hash'], "wire":variant['bus'][0]['wire']})
    # ADD GENERIC ?
    parsedBus = []
    for preset in presets:
      label = self.parsePresetLabel(preset)
      if not label in parsedBus:
        self.body.fldPreset.addItem(label, preset)
        parsedBus.append(label)

    self.presetLock = False


  def parsePresetLabel(self, bus):
    label = bus['name'] + " : "
    label += str(bus['speed']) + " " + SUPPORTED_SPEED_UNIT[self.busType]
    if len(bus['wire']) > 0:
      label += " ("
      label += self.parseWireInfo(bus['wire'])
      label += ")"
    return label

  def parseWireInfo(self, wire, splitter=" - "):
    label = ""
    if wire[0]['color'] != None:
      label += QCoreApplication.translate("BUS", wire[0]['color'][0])
      if len(wire[0]['color']) > 1:
        label += "/" + QCoreApplication.translate("BUS", wire[0]['color'][1])
    if wire[0]['obd'] != None:
        label += " OBD : " + str(wire[0]['obd'])
    if len(wire) > 1:
      label += splitter
      if wire[1]['color'] != None:
        label += QCoreApplication.translate("BUS", wire[1]['color'][0])
        if len(wire[1]['color']) > 1:
          label += "/" + QCoreApplication.translate("BUS", wire[1]['color'][1])
      if wire[1]['obd'] != None:
          label += " OBD : " + str(wire[1]['obd'])
    return label


  def applyPreset(self, presetId):
    if presetId > 0:
      bus = self.body.fldPreset.currentData()
      self.fillEditor(bus)
