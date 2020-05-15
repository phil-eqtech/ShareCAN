from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from modules.Constants import *

import qtawesome as qta
import time
import logging
import uuid

from ui.ModelDialog import ModelDialog, UCValidator
from ui.SignalsForm import Ui_SIGNAL

#
# Tableview classes
#
class TableView(QTableView):
  def __init__(self, *args, **kwargs):
    super(TableView, self).__init__(*args, **kwargs)


class CustomDelegate(QStyledItemDelegate):
  def anchorAt(self, html, point):
    doc = QTextDocument()
    doc.setHtml(html)
    textLayout = doc.documentLayout()
    return textLayout.anchorAt(point)

  def paint(self, painter, option, index):
    options = QStyleOptionViewItem(option)
    self.initStyleOption(options, index)

    if options.widget:
      style = options.widget.style()
    else:
      style = QtWidgets.QApplication.style()

    doc = QTextDocument()
    doc.setHtml(options.text)
    options.text = ''

    style.drawControl(QStyle.CE_ItemViewItem, options, painter)
    ctx = QAbstractTextDocumentLayout.PaintContext()

    textRect = style.subElementRect(QStyle.SE_ItemViewItemText, options)

    painter.save()
    painter.translate(textRect.topLeft())
    painter.setClipRect(textRect.translated(-textRect.topLeft()))
    painter.translate(0, 0.5*(options.rect.height() - doc.size().height()))
    doc.documentLayout().draw(painter, ctx)

    painter.restore()

  def sizeHint(self, option, index):
    options = QStyleOptionViewItem(option)
    self.initStyleOption(options, index)

    doc = QTextDocument()
    doc.setHtml(options.text)
    doc.setTextWidth(options.rect.width())
    return QSize(doc.idealWidth(), doc.size().height())


class bitsTableModel(QAbstractTableModel):
    def __init__(self, columnsDef, frame=None, parent=None):
        super().__init__()
        self.parent = parent

        self.frame = frame
        self.signalStart = None
        self.signalLen = None

        self.columnLabel = columnsDef

    def __getitem__(self, key):
      return getattr(self, key)

    def __setitem__(self, key, value):
      return setattr(self, key, value)

    def rowCount(self, parent):
      return len(self.frame)

    def columnCount(self, parent):
      return len(self.columnLabel)

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return QCoreApplication.translate("FRAME",self.columnLabel[section]['label'])
            if orientation == Qt.Vertical:
                return str(section +1)

    def data(self, index, role):
        r = index.row()
        f = self.frame[r]
        c = index.column()

        if role == Qt.DisplayRole:
          if self.columnLabel[c]['field'] == 'byte':
           return f['byte']
          else:
            return f['b' + str(8-c)]['value']
        elif role == Qt.BackgroundColorRole:
          if self.signalStart != None:
            bitNumber = c + 8 * r
            if bitNumber >= self.signalStart and bitNumber < self.signalStart + self.signalLen and c < 8:
              return QVariant(QColor(204, 229,255))


    def updateFrame(self, frame):
      self.frame = frame
      self.layoutChanged.emit()

    def updateSignal(self, start, length):
      self.signalStart = start
      self.signalLen = length
      self.layoutChanged.emit()

#
# Dialog classes
#
class SignalForm(QWidget, Ui_SIGNAL):
  def __init__(self):
   super().__init__()
   self.setupUi(self)


class SignalDialog(ModelDialog):
  def __init__(self, refWindow, frameSrc=None):
    super().__init__()

    self.getMainVariables(refWindow)

    self.frameSrc = frameSrc
    logging.debug("SIGNAL : %s"%frameSrc)
    self.lastRefresh = 0

    self.signalStart = None
    self.signalLen = None
    self.signalActiveClick = False

    self.signalId = None

    self.comboSignalsLock = False

    # Bottom buttons
    self.closeBtn = QPushButton()
    self.closeBtn.setIcon(qta.icon('fa.close',color='white'))
    self.closeBtn.setText(QCoreApplication.translate("DIALOG", "CLOSE"))
    self.closeBtn.setProperty("cssClass","btn-danger")
    self.closeBtn.setCursor(Qt.PointingHandCursor)
    self.closeBtn.clicked.connect(self.reject)
    self.setBottomButtons(self.closeBtn)

    # Loading body template
    self.body = SignalForm()
    self.dialogBody.addWidget(self.body)

    self.body.bitsTable.clicked.connect(lambda x: self.selectBits(x))

    # Signals
    self.appSignals.signalEditorRefresh.connect(lambda x: self.updateGrid(x))
    self.body.fldStart.textChanged.connect(lambda: self.updateSaveBtn())
    self.body.fldLen.textChanged.connect(lambda: self.updateSaveBtn())
    self.body.fldName.textChanged.connect(lambda: self.updateSaveBtn())
    self.body.btnSave.clicked.connect(lambda: self.saveSignal())
    self.body.btnAddValue.clicked.connect(lambda: self.addValueFields())
    self.body.btnImport.clicked.connect(lambda: self.importSignal())
    self.body.comboSignalSelector.currentIndexChanged.connect(lambda x: self.loadSignal(x))
    self.body.btnNewSignal.clicked.connect(lambda: self.resetSignal())
    self.body.btnDelete.clicked.connect(lambda: self.deleteSignal())

    # Btn
    options=[{'color_disabled': 'black', 'color':'white'}]
    self.body.btnSave.setIcon(qta.icon('fa5.save',options=options))
    self.body.btnDelete.setIcon(qta.icon('mdi.delete',options=options))
    self.body.btnNewSignal.setIcon(qta.icon('ei.file-new',options=options))
    self.body.btnAddValue.setIcon(qta.icon('mdi.playlist-plus',options=options))
    self.body.btnImport.setIcon(qta.icon('mdi.content-duplicate',options=options))

    # Validators
    QLocale.setDefault(QLocale(QLocale.C))
    self.body.fldMin.setValidator(QDoubleValidator(-2147483647, 2147483647, 5, self))
    self.body.fldMax.setValidator(QDoubleValidator(-2147483647, 2147483647, 5,self))
    self.body.fldOffset.setValidator(QDoubleValidator(-2147483647, 2147483647, 5,self))
    self.body.fldFactor.setValidator(QDoubleValidator(-2147483647, 2147483647, 5,self))
    self.body.fldStart.setValidator(QIntValidator(0, 511, self))
    self.body.fldLen.setValidator(QIntValidator(0, 511, self))
    upperCaseValidator = UCValidator(self)
    self.body.fldECU.setValidator(upperCaseValidator)

    # Btn initial staets
    self.body.btnSave.setDisabled(True)
    self.body.btnDelete.setDisabled(True)
    self.body.btnImport.hide()

    self.body.comboEndian.addItem(QCoreApplication.translate("SIGNALS","LITTLE_ENDIAN"), 1)
    self.body.comboEndian.addItem(QCoreApplication.translate("SIGNALS","BIG_ENDIAN"), 0)

    # Editing grid
    self.frameModel = bitsTableModel(BIT_WINDOW_MODEL, self.extractBits(), self.body.bitsTable)
    self.body.bitsTable.setModel(self.frameModel)
    self.body.bitsTable.setItemDelegate(CustomDelegate(self))

    self.drawDialogBody()


  def selectBits(self, cell = None):
    if cell != None:
      if cell.column() < 8:
        if self.signalActiveClick == False:
          self.signalActiveClick = True
          self.signalStart = self.defineBitNumber(cell)
          self.signalLen = 1
          self.body.fldStart.setText(str(self.signalStart))
          self.body.fldLen.setText(str(self.signalLen))
        else:
          nextBit = self.defineBitNumber(cell)
          if nextBit < self.signalStart:
            self.signalLen = self.signalStart - nextBit
            self.signalStart = nextBit
          else:
            self.signalLen = nextBit - self.signalStart
          self.signalLen += 1
          self.body.fldStart.setText(str(self.signalStart))
          self.body.fldLen.setText(str(self.signalLen))
          self.signalActiveClick = False
        self.frameModel.updateSignal(self.signalStart, self.signalLen)


  def defineBitNumber(self, cell):
    return cell.column() + 8 * cell.row()


  def updateSaveBtn(self):
    b = self.body
    if len(b.fldStart.text()) > 0 and  len(b.fldLen.text()) > 0 and  len(b.fldName.text()) > 0:
      b.btnSave.setDisabled(False)
      b.btnSave.setProperty('cssClass','btn-success')
    else:
      b.btnSave.setDisabled(True)
      b.btnSave.setProperty('cssClass','btn-disabled')
    b.btnSave.setStyle(b.btnSave.style())


  def loadSignal(self, id):
    if self.comboSignalsLock == False and id > 0:
      self.resetSignal(resetComboIndex=False)
      s = self.body.comboSignalSelector.currentData()

      self.signalId = s['sid']
      self.body.fldName.setText(s['name'])
      self.body.fldECU.setText(s['ecu'])
      self.body.fldStart.setText(s['start'])
      self.body.fldLen.setText(s['len'])
      self.body.fldFactor.setText(s['factor'])
      self.body.fldOffset.setText(s['offset'])
      self.body.fldMin.setText(s['min'])
      self.body.fldMax.setText(s['max'])
      self.body.fldUnit.setText(s['unit'])
      self.body.fldComment.setPlainText(s['comment'])
      self.body.checkSigned.setCheckState(s['signed'])
      self.body.comboEndian.setCurrentIndex(1-s['endian'])
      # Values
      for i in range(0, len(s['values'])):
        self.addValueFields(s['values'][i])

      if s['owner'] != self.user['uid']:
        self.body.btnSave.hide()
        self.body.btnImport.show()
        self.body.btnDelete.setDisabled(True)
        self.body.btnDelete.setProperty("cssClass","btn-disabled")
        self.body.btnDelete.setStyle(self.body.btnDelete.style())
      else:
        self.body.btnSave.show()
        self.body.btnImport.hide()
        self.body.btnDelete.setDisabled(False)
        self.body.btnDelete.setProperty("cssClass","btn-danger")
        self.body.btnDelete.setStyle(self.body.btnDelete.style())
      self.frameModel.updateSignal(int(s['start']), int(s['len']))

  def importSignal(self):
    self.signalId = None
    self.saveSignal()
    self.body.btnSave.show()
    self.body.btnImport.hide()

  def deleteSignal(self):
    if self.signalId != None:
      msgBox = QMessageBox()
      msgBox.setText(QCoreApplication.translate("SIGNALS","DELETE_SIGNAL"))
      msgBox.setInformativeText(QCoreApplication.translate("SIGNALS","DELETE_SIGNAL_DETAILS"))
      msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
      msgBox.setDefaultButton(QMessageBox.Ok)
      self.centerMsg(msgBox)
      choice = msgBox.exec()

      if choice == QMessageBox.Ok:
        self.db.signals.remove({"sid":self.signalId})

        f = self.frameSrc
        if f['type'] in self.signals and f['preset'] in self.signals[f['type']] and f['id'] in self.signals[f['type']][f['preset']]:
          for i in range(0, len(self.signals[f['type']][f['preset']][f['id']])):
            if self.signals[f['type']][f['preset']][f['id']][i]['sid'] == self.signalId:
              self.signals[f['type']][f['preset']][f['id']].pop(i)
              break

        self.loadComboSelector()
        self.resetSignal()
        self.appSignals.signalReload.emit(True)


  def resetSignal(self, resetComboIndex=True):
    self.signalId = None
    self.body.fldName.setText("")
    self.body.fldECU.setText("")
    self.body.fldStart.setText("")
    self.body.fldLen.setText("")
    self.body.fldFactor.setText("")
    self.body.fldOffset.setText("")
    self.body.fldMin.setText("")
    self.body.fldMax.setText("")
    self.body.fldUnit.setText("")
    self.body.fldComment.setPlainText("")
    self.body.checkSigned.setCheckState(False)
    self.body.comboEndian.setCurrentIndex(0)
    for i in range(1, self.body.gridValuesLayout.rowCount()):
      self.deleteValue(i)
    self.frameModel.updateSignal(None, None)
    self.body.btnSave.show()
    self.body.btnImport.hide()
    self.body.btnDelete.setDisabled(True)
    self.body.btnDelete.setProperty("cssClass","btn-disabled")
    self.body.btnDelete.setStyle(self.body.btnDelete.style())
    if resetComboIndex == True:
      self.body.comboSignalSelector.setCurrentIndex(0)

  def saveSignal(self):
    newSignal = False
    if self.signalId == None:
      self.signalId = str(uuid.uuid4())
      newSignal = True
    signal = {"sid":self.signalId}
    signal['id'] = self.frameSrc['id']
    signal['preset'] = self.frameSrc['preset']
    signal['type'] = self.frameSrc['type']
    signal['analysis'] = self.analysis['id']
    signal['manufacturer'] = self.analysis['manufacturer']
    signal['model'] = self.analysis['model']
    signal['engineCode'] = self.analysis['engineCode']
    signal['owner'] = self.user['uid']
    signal['lastUpdate'] = time.time()
    signal['name'] = self.body.fldName.text()
    signal['ecu'] = self.body.fldECU.text()
    signal['start'] = self.body.fldStart.text()
    signal['len'] = self.body.fldLen.text()
    signal['signed'] = self.body.checkSigned.isChecked()
    signal['endian'] = self.body.comboEndian.currentData()
    signal['factor'] = self.body.fldFactor.text()
    signal['offset'] = self.body.fldOffset.text()
    signal['min'] = self.body.fldMin.text()
    signal['max'] = self.body.fldMax.text()
    signal['unit'] = self.body.fldUnit.text()
    signal['comment'] = self.body.fldComment.toPlainText()
    signal['values'] = self.getValues()
    self.db.signals.update({"sid":signal['sid']},signal, True)
    if newSignal == True:
      f = self.frameSrc
      if not f['type'] in self.signals:
        self.signals[f['type']] = {}
      if not f['preset'] in self.signals[f['type']]:
        self.signals[f['type']][f['preset']] = {}
      if not f['id'] in self.signals[f['type']][f['preset']]:
        self.signals[f['type']][f['preset']][f['id']] = []
      self.signals[f['type']][f['preset']][f['id']].append(signal)
      self.loadComboSelector()
      self.body.btnDelete.setDisabled(False)
      self.body.btnDelete.setProperty("cssClass","btn-danger")
      self.body.btnDelete.setStyle(self.body.btnDelete.style())
    self.appSignals.signalReload.emit(True)

  def getValues(self):
    rowIndex = self.body.gridValuesLayout.rowCount()
    values = []
    if rowIndex > 0:
      for r in range(1, rowIndex):
        if self.body.gridValuesLayout.itemAtPosition(r, 0) != None:
          value = self.body.gridValuesLayout.itemAtPosition(r, 0).widget().displayText()
          label = self.body.gridValuesLayout.itemAtPosition(r, 1).widget().displayText()
          if len(value) > 0 and len(label) > 0:
            values.append({"value":value,"label":label})
    return values


  def addValueFields(self, value=None):
    rowIndex = self.body.gridValuesLayout.rowCount()
    sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)


    valueWidget = QLineEdit(self.body.tabValues)
    valueWidget.setSizePolicy(sizePolicy)
    valueWidget.setMaximumSize(QSize(60, 16777215))
    valueWidget.setPlaceholderText(QCoreApplication.translate("SIGNALS","VALUE"))
    valueWidget.setValidator(QIntValidator(0, 2147483647, self) )
    if value != None:
      valueWidget.setText(value['value'])
    self.body.gridValuesLayout.addWidget(valueWidget, rowIndex, 0, 1, 1)

    labelWidget = QLineEdit(self.body.tabValues)
    labelWidget.setSizePolicy(sizePolicy)
    labelWidget.setMaximumSize(QSize(120, 16777215))
    labelWidget.setPlaceholderText(QCoreApplication.translate("SIGNALS","LABEL"))
    if value != None:
      labelWidget.setText(value['label'])
    self.body.gridValuesLayout.addWidget(labelWidget, rowIndex, 1, 1, 1)

    deleteWidget = QPushButton(self.body.tabValues)
    deleteWidget.setSizePolicy(sizePolicy)
    deleteWidget.setIcon(qta.icon("mdi.delete", options=[{"color":"white"}]))
    deleteWidget.setProperty("cssClass","btn-danger")
    deleteWidget.setCursor(Qt.PointingHandCursor)
    deleteWidget.clicked.connect(lambda: self.deleteValue(rowIndex))
    self.body.gridValuesLayout.addWidget(deleteWidget, rowIndex, 2, 1, 1)


  def deleteValue(self, rowIndex):
    if rowIndex < self.body.gridValuesLayout.rowCount():
      for c in range(0,self.body.gridValuesLayout.columnCount()):
        w = self.body.gridValuesLayout.itemAtPosition(rowIndex, c)
        if w != None:
          w = w.widget()
          self.body.gridValuesLayout.removeWidget(w)
          w.deleteLater()


  def extractBits(self):
    byteList = []
    timer = time.time()
    for byte in self.frameSrc['bytes']:
      byteDetails = {}
      for i in range(0,8):
        factor = 2 ** i
        byteDetails['b' + str(i+1)] = {"value":0, "isChanged":False}
        if byte['value'] & factor == factor:
          byteDetails['b' + str(i+1)]['value'] = str(1)
        else:
          byteDetails['b' + str(i+1)]['value'] = str(0)

        if byte['prevByte'] != None and (byte['isChanged'] == True or (byte['prevByte'] != byte['value'] and  byte['lastChange'] + FRAME_CHANGE_TIME > timer)):
          if byte['value'] & factor != byte['prevByte'] & factor:
            byteDetails['b' + str(i+1)]['isChanged'] = True
            byteDetails['b' + str(i+1)]['value'] = '<span style="color:#FF0000">' + byteDetails['b' + str(i+1)]['value'] + '<span>'

      byteDetails['byte'] = str("{0:#0{1}x}".format(byte['value'],4))
      if byte['isChanged'] == True or (byte['prevByte'] != byte['value'] and  byte['lastChange'] + FRAME_CHANGE_TIME > timer):
        byteDetails['byte']  = '<span style="color:#FF0000">' + byteDetails['byte'] + '<span>'

      byteList.append(byteDetails.copy())
    return byteList


  def updateGrid(self, msg):
    if self.lastRefresh + TABLE_REFRESH_RATE < time.time():
      self.frameSrc = msg
      self.frameModel.updateFrame(self.extractBits())
      self.lastRefresh = time.time()

  def loadComboSelector(self):
    self.comboSignalsLock = True
    idx = self.body.comboSignalSelector.count()
    for i in range(0, idx):
      self.body.comboSignalSelector.removeItem(0)
    self.body.comboSignalSelector.addItem("---", None)

    f = self.frameSrc
    if f['type'] in self.signals and f['preset'] in self.signals[f['type']] and f['id'] in self.signals[f['type']][f['preset']]:
      s = self.signals[f['type']][f['preset']][f['id']]
      signalOrder = sorted(s, key=lambda x: x['name'])
      for elt in signalOrder:
        lbl = "%s [%s|%s]"%(elt['name'],elt['start'],elt['len'])
        if elt['owner'] != self.user['uid']:
          if elt['engineCode'] == self.analysis['engineCode']:
            lbl += " (%s)" % QCoreApplication.translate("SIGNALS","ENGINE_CODE")
          elif elt['model'] == self.analysis['model']:
            lbl += " (%s)" % QCoreApplication.translate("SIGNALS","MODEL")
          else:
            lbl += " (%s)" % QCoreApplication.translate("SIGNALS","MANUFACTURER")
        self.body.comboSignalSelector.addItem(lbl, elt)
    self.comboSignalsLock = False

  def drawDialogBody(self):
    if self.frameSrc['extendedId']==True:
      id = "{0:#0{1}x}".format(self.frameSrc['id'],10)
    else:
      id = "{0:#0{1}x}".format(self.frameSrc['id'],5)
    self.body.fldId.setText(id)

    for i in range(0, len(BIT_WINDOW_MODEL)):
      if hasattr(BIT_WINDOW_MODEL[i],'w'):
        self.body.bitsTable.setColumnWidth(i,BIT_WINDOW_MODEL[i]['w'])

    self.body.bitsTable.resizeColumnsToContents()
    h = self.body.bitsTable.horizontalHeader()
    h.setStretchLastSection(True)

    self.loadComboSelector()
