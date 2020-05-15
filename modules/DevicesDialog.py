from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import qtawesome as qta
import time
import logging

from ui.ModelDialog import ModelDialog
from ui.DevicesForm import Ui_DEVICES


class DevicesList(QWidget, Ui_DEVICES):
  def __init__(self):
   super().__init__()
   self.setupUi(self)


class DevicesDialog(ModelDialog):
  def __init__(self, interfaces):
    super().__init__()

    self.interfaces = interfaces
    self.interfaces.listDevices()

    # Close btn
    self.closeBtn = QPushButton()
    self.closeBtn.setIcon(qta.icon('fa.close',color='white'))
    self.closeBtn.setText(QCoreApplication.translate("DIALOG", "CLOSE"))
    self.closeBtn.setProperty("cssClass","btn-danger")
    self.closeBtn.setCursor(Qt.PointingHandCursor)
    self.closeBtn.clicked.connect(self.reject)

    self.setBottomButtons(self.closeBtn)

    # Loading body template
    self.dialogTitle.setText(QCoreApplication.translate("DEVICES","IFACE_MANAGEMENT"))
    self.body = DevicesList()
    self.dialogBody.addWidget(self.body)

    # Editing grid
    self.drawDialogBody()


  def addDevice(self, device, id):
    _translate = QCoreApplication.translate
    rowIndex = self.body.deviceGridLayout.rowCount()

    sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)

    deviceName = QLabel(device['name'], self.body.deviceGridWidget)
    deviceName.setObjectName("deviceName_" + id)
    deviceName.setSizePolicy(sizePolicy)
    self.body.deviceGridLayout.addWidget(deviceName, rowIndex, 0, 1, 1)

    portLabel = QLabel(device['port'], self.body.deviceGridWidget)
    portLabel.setObjectName("portName_" + id)
    portLabel.setSizePolicy(sizePolicy)
    self.body.deviceGridLayout.addWidget(portLabel, rowIndex, 1, 1, 1)

    deviceInput = QLineEdit(self.body.deviceGridWidget)
    deviceInput.setObjectName("deviceInput_" + id)
    deviceInput.setSizePolicy(sizePolicy)
    deviceInput.setMaxLength(16)
    deviceInput.setText(device['label'])
    self.body.deviceGridLayout.addWidget(deviceInput, rowIndex, 2, 1, 1)

    devicePermanent = QCheckBox(self.body.deviceGridWidget)
    devicePermanent.setObjectName("devicePermanent_" + id)
    devicePermanent.setCursor(QCursor(Qt.PointingHandCursor))
    self.body.deviceGridLayout.addWidget(devicePermanent, rowIndex, 3, 1, 1, Qt.AlignCenter)

    deviceAdd = QPushButton(self.body.deviceGridWidget)
    deviceAdd.setObjectName("deviceAdd_" + id)
    deviceAdd.setCursor(QCursor(Qt.PointingHandCursor))
    deviceAdd.setIcon(qta.icon('ei.plus',color='white'))
    deviceAdd.setProperty("cssClass","btn-success")
    deviceAdd.released.connect(lambda: self.activateDevice(id, deviceInput.text(), devicePermanent.isChecked() ))
    self.body.deviceGridLayout.addWidget(deviceAdd, rowIndex, 4, 1, 1, Qt.AlignCenter)


  def addInterface(self, bus, isNewDevice = True):
    _translate = QCoreApplication.translate
    rowIndex = self.body.ifaceGridLayout.rowCount()

    sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)

    deviceLabel = QLabel("", self.body.ifaceGridWidget)
    deviceLabel.setObjectName("deviceLabel_" + bus['id'])
    deviceLabel.setSizePolicy(sizePolicy)
    self.body.ifaceGridLayout.addWidget(deviceLabel, rowIndex, 0, 1, 1)
    if isNewDevice == True:
      deviceLabel.setText(bus['deviceLabel'])

    portLabel = QLabel("", self.body.ifaceGridWidget)
    portLabel.setObjectName("portLabel_" + bus['id'])
    portLabel.setSizePolicy(sizePolicy)
    self.body.ifaceGridLayout.addWidget(portLabel, rowIndex, 1, 1, 1)
    if isNewDevice == True:
      portLabel.setText(bus['port'])

    ifaceWidget = QWidget(self.body.ifaceGridWidget)
    ifaceWidget.setObjectName("ifaceWidget_" + bus['id'])
    ifaceWidget.setSizePolicy(sizePolicy)
    ifaceWidgetLayout = QHBoxLayout(ifaceWidget)
    ifaceWidgetLayout.setObjectName("ifaceWidgetLayout_" + bus['id'])
    ifaceWidgetLayout.setContentsMargins(0, 0, 0, 0)

    ifaceLabel = QLabel(bus['name'], ifaceWidget)
    ifaceLabel.setObjectName("ifaceLabel_" +  bus['id'])
    ifaceLabel.setSizePolicy(sizePolicy)

    ifaceInput = QLineEdit(ifaceWidget)
    ifaceInput.setObjectName("ifaceInput_" + bus['id'])
    ifaceInput.setSizePolicy(sizePolicy)
    ifaceInput.setMaxLength(8)
    ifaceInput.setText(bus['name'])
    ifaceInput.textEdited.connect(lambda x: self.updateBusName(bus['id'], x, ifaceInput))
    ifaceWidgetLayout.addWidget(ifaceLabel)
    ifaceWidgetLayout.addWidget(ifaceInput)
    self.body.ifaceGridLayout.addWidget(ifaceWidget, rowIndex, 2, 1, 1)

    if isNewDevice == True:
      ifaceRemove = QPushButton(self.body.ifaceGridWidget)
      if self.interfaces.devices[bus['device']]['builtin'] == True:
          ifaceRemove.setDisabled(True)
          ifaceRemove.setIcon(qta.icon('fa.microchip', color='black'))
          ifaceRemove.setProperty("cssClass","btn-disabled")
      else:
        ifaceRemove.setCursor(QCursor(Qt.PointingHandCursor))
        ifaceRemove.released.connect(lambda: self.disconnectDevice(bus['device']))
        ifaceRemove.setIcon(qta.icon('ei.remove',color='white'))
        ifaceRemove.setProperty("cssClass","btn-danger")
        ifaceRemove.setToolTip("OK") # Translate
    else:
      ifaceRemove = QLabel("", self.body.ifaceGridWidget)
    ifaceRemove.setObjectName("ifaceRemove_" + bus['id'])
    self.body.ifaceGridLayout.addWidget(ifaceRemove, rowIndex, 3, 1, 1, Qt.AlignCenter)


  def updateBusName(self, busId, newName, widget):
    prevValue = self.interfaces.bus[busId]['name']
    if len(newName) == 0:
      widget.setPlaceholderText(prevValue)
    else:
      self.interfaces.bus[busId]['name'] = newName
      if self.interfaces.bus[busId]['label'] == prevValue:
        self.interfaces.bus[busId]['label'] = newName

  def disconnectDevice(self, id):
    self.interfaces.deactivateDevice(id)
    self.drawDialogBody()

  def activateDevice(self, id, label = None, setPermanent = False):
    print("Activating device %s with id %s (Permanent : %s) "%(label, id, setPermanent))
    if label != None and len(label) > 0:
      self.interfaces.devices[id]['label'] = label
    self.interfaces.activateDevice(id, setPermanent)
    self.drawDialogBody()

  def drawDialogBody(self):
    self.removeLines(self.body.ifaceGridLayout)
    self.removeLines(self.body.deviceGridLayout)

    if len(self.interfaces.bus) > 0:
      busOrder = sorted(self.interfaces.bus, key=lambda x: (self.interfaces.bus[x]['deviceLabel'], self.interfaces.bus[x]['name']))
      prevBusId = None
      isNewDevice = False

      for id in busOrder:
        if prevBusId != self.interfaces.bus[id]['device']:
          isNewDevice = True
        else:
          isNewDevice = False
        prevBusId = self.interfaces.bus[id]['device']
        self.addInterface(self.interfaces.bus[id], isNewDevice)
    else:
      noIfaces = QLabel(QCoreApplication.translate("DEVICES","NO_AVAILABLE_DEVICES"),self.body.ifaceGridWidget)
      noIfaces.setObjectName("noIfaces")
      self.body.ifaceGridLayout.addWidget(noIfaces, 1, 0, 1, 4, Qt.AlignCenter)

    stdByDevices = 0
    if len(self.interfaces.devices) > 0:
      logging.debug(self.interfaces.devices)
      deviceOrder = sorted(self.interfaces.devices, key=lambda x: (self.interfaces.devices[x]['name']))
      for id in deviceOrder:
        if self.interfaces.devices[id]['active'] == False:
          self.addDevice(self.interfaces.devices[id], id)
          stdByDevices += 1
    if stdByDevices == 0:
      noDevices = QLabel(QCoreApplication.translate("DEVICES","NO_AVAILABLE_DEVICES"),self.body.deviceGridWidget)
      noDevices.setObjectName("noDevice")
      self.body.deviceGridLayout.addWidget(noDevices, 1, 0, 1, 5, Qt.AlignCenter)
