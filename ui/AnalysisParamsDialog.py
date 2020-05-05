from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import qtawesome as qta

import time
import uuid

from modules.Constants import *
from ui.ModelDialog import ModelDialog, UCValidator
from ui.AnalysisParamsForm import Ui_AnalysisParams

class AnalysisParams(QWidget, Ui_AnalysisParams):
  def __init__(self):
   super().__init__()
   self.setupUi(self)

class AnalysisParamsDialog(ModelDialog):
  def __init__(self, refWindow, newAnalysis=False):
    super().__init__()

    self.getMainVariables(refWindow)

    self.isNewAnalysis = newAnalysis

    # Init / Save / Close btn
    if self.isNewAnalysis == True:
      self.saveBtn = QPushButton()
      self.saveBtn.setIcon(qta.icon('mdi.magnify-scan',color='white', color_disabled='grey'))
      self.saveBtn.setText(QCoreApplication.translate("ANALYSIS", "START_ANALYSIS"))
      self.saveBtn.setProperty("cssClass","btn-disabled")
      self.saveBtn.setCursor(Qt.ArrowCursor)
      self.saveBtn.setDisabled(True)
      self.saveBtn.clicked.connect(lambda: self.startNewAnalysis())
    else:
      self.saveBtn = QPushButton()
      self.saveBtn.setIcon(qta.icon('mdi.magnify-scan',color='white', color_disabled='grey'))
      self.saveBtn.setText(QCoreApplication.translate("ANALYSIS", "UPDATE_PARAMS"))
      self.saveBtn.setProperty("cssClass","btn-success")
      self.saveBtn.setCursor(Qt.PointingHandCursor)
      self.saveBtn.clicked.connect(lambda: self.updateAnalysisParams())

    self.closeBtn = QPushButton()
    self.closeBtn.setIcon(qta.icon('fa.close',color='white'))
    self.closeBtn.setText(QCoreApplication.translate("DIALOG", "CLOSE"))
    self.closeBtn.setProperty("cssClass","btn-danger")
    self.closeBtn.setCursor(Qt.PointingHandCursor)
    self.closeBtn.clicked.connect(self.reject)
    self.setBottomButtons([self.saveBtn, self.closeBtn])

    # Loading body template
    self.dialogTitle.setText(QCoreApplication.translate("ANALYSIS", "ANALYSIS_PARAMS"))
    self.body = AnalysisParams()
    self.dialogBody.addWidget(self.body)

    # Editing grid
    self.drawDialogBody()


  def drawDialogBody(self):
    upperCaseValidator = UCValidator(self)

    if self.isNewAnalysis == False:
      self.body.fldYear.setText(self.analysis['year'])
      self.body.fldVIN.setText(self.analysis['VIN'])

    if self.isNewAnalysis == True:
      self.body.fldVehicleType.addItem("-",-1)
      self.body.fldVehicleType.currentIndexChanged.connect(lambda x: self.activateSaveButton(x))
      i = 1
    else:
      i = 0
    for vehicleType in SUPPORTED_VEHICLE:
      self.body.fldVehicleType.addItem(QCoreApplication.translate("CONSTANTS",SUPPORTED_VEHICLE[vehicleType]),vehicleType)
      if self.isNewAnalysis == False:
        if self.analysis['vehicleType'] == vehicleType:
          self.body.fldVehicleType.setCurrentIndex(i)
        #self.body.fldVehicleType.setDisabled(False)
        i += 1

    self.setManufacturerAutoComplete()
    self.body.fldManufacturer.setValidator(upperCaseValidator)
    self.body.fldManufacturer.textChanged.connect(lambda x: self.updateFldModelStatus(x))
    if self.isNewAnalysis == False:
      if self.analysis['manufacturer'] != None:
        self.body.fldManufacturer.setText(self.analysis['manufacturer'])

    if self.isNewAnalysis == True or self.analysis['manufacturer'] == None:
      self.body.fldModel.setDisabled(True)
    else:
      self.setModelAutoComplete(self.analysis['manufacturer'])
    self.body.fldModel.setValidator(upperCaseValidator)
    if self.isNewAnalysis == False:
      if self.analysis['model'] != None:
        self.body.fldModel.setText(self.analysis['model'])

    i = 0
    if self.isNewAnalysis == True:
      self.body.fldEngine.addItem("-",-1)
    for engine in SUPPORTED_ENGINE:
      self.body.fldEngine.addItem(QCoreApplication.translate("CONSTANTS",SUPPORTED_ENGINE[engine]),engine)
      if self.isNewAnalysis == False:
        if self.analysis['engine'] == engine:
          self.body.fldEngine.setCurrentIndex(i)
        i += 1

    i=0
    for privacyMode in PRIVACY_MODE:
      self.body.fldPrivacyMode.addItem(QCoreApplication.translate("CONSTANTS",PRIVACY_MODE[privacyMode]),privacyMode)
      if self.isNewAnalysis == False:
        if self.analysis['privacy'] == privacyMode:
          self.body.fldPrivacyMode.setCurrentIndex(i)
        i += 1


  def startNewAnalysis(self):
    self.analysis = self.setAnalysisParams(isNew = True)
    self.appSignals.startAnalysis.emit(True)
    self.accept()


  def updateAnalysisParams(self):
    self.analysis = self.setAnalysisParams()
    self.appSignals.updateAnalysis.emit(True)
    # Signal : update label, reload frame signals definitions, check privacy
    self.accept()


  def setAnalysisParams(self, isNew = False):
    analysis = {"vehicleType":None, "manufacturer":None, "model":None, "VIN":None, "engineCode":None,
                      "year":None,"engine":None, "privacy":None, "bus":[]}
    analysis['vehicleType'] = self.body.fldVehicleType.currentData()
    if len(self.body.fldManufacturer.text()) > 0:
      analysis['manufacturer'] = self.body.fldManufacturer.text()
    if len(self.body.fldModel.text()) > 0:
      analysis['model'] = self.body.fldModel.text()
    if len(self.body.fldVIN.text()) > 0:
      analysis['VIN'] = self.body.fldVIN.text()
      analysis['engineCode'] = analysis['VIN'][3:8]
    if len(self.body.fldYear.text()) > 0:
      analysis['year'] = self.body.fldYear.text()
    if self.body.fldEngine.currentData() != -1:
      analysis['engine'] = self.body.fldEngine.currentData()
    analysis['privacy'] = self.body.fldPrivacyMode.currentData()

    if isNew == True:
      analysis['id'] = str(uuid.uuid4())
      analysis['createTime'] = time.time()
      analysis['lastUpdate'] = analysis['createTime']
      analysis['owner'] = self.user['uid']
      self.db.analysis.insert(analysis)
    else:
      analysis['bus'] = self.analysis['bus']
      self.db.analysis.update({"id":self.analysis['id']},{"$set":analysis})
      # IF manufacturer / VIN / model are changed, we update the signals DB

    for elt in analysis:
      self.analysis[elt] = analysis[elt]

    # If manufacturer/model is not known, we add them in the DB
    if analysis['manufacturer'] != None:
      manufacturer = self.db.manufacturers.find({"name": analysis['manufacturer']},{"_id":0, "models":1})
      if manufacturer.count() == 0:
        model = {}
        if analysis['model'] != None:
          model = {"name":analysis['model']}
        self.db.manufacturers.insert({"name":analysis['manufacturer'],"models":[model]})
      elif analysis['model'] != None:
        modelExists = False
        for model in manufacturer[0]['models']:
          if model['name'] == analysis['model']:
            modelExists = True
            break
        if modelExists == False:
          self.db.manufacturers.update({"name":analysis['manufacturer']},{"$push":{"models":{"name":analysis['model']}}})


  def setManufacturerAutoComplete(self):
    manufacturerList = []
    manufacturerCursor = self.db.manufacturers.find({},{"_id":0, "name":1})
    if manufacturerCursor.count() > 0:
      for manufacturer in manufacturerCursor:
        manufacturerList.append(manufacturer['name'])
    manufacturerCompleter = QCompleter(manufacturerList, self.body.fldManufacturer)
    manufacturerCompleter.setCaseSensitivity(Qt.CaseInsensitive)
    self.body.fldManufacturer.setCompleter(manufacturerCompleter)


  def setModelAutoComplete(self, manufacturer):
    modelList = []
    modelCursor = self.db.manufacturers.find({"name": manufacturer},{"_id":0, "models":1})
    if modelCursor.count() == 1:
      entry = modelCursor[0]
      if 'models' in entry:
        for model in entry['models']:
          if 'name' in model:
            modelList.append(model['name'])

    modelCompleter = QCompleter(modelList, self.body.fldModel)
    modelCompleter.setCaseSensitivity(Qt.CaseInsensitive)
    self.body.fldModel.setCompleter(modelCompleter)


  def updateFldModelStatus(self, manufacturerName):
    if len(manufacturerName) == 0:
      self.body.fldModel.setDisabled(True)
    else:
      self.body.fldModel.setDisabled(False)
      self.setModelAutoComplete(manufacturerName)


  def activateSaveButton(self, idx):
    if idx ==0:
      self.saveBtn.setDisabled(True)
      self.saveBtn.setProperty("cssClass","btn-disabled")
      self.saveBtn.setCursor(Qt.ArrowCursor)
    else:
      self.saveBtn.setDisabled(False)
      self.saveBtn.setProperty("cssClass","btn-primary")
      self.saveBtn.setCursor(Qt.PointingHandCursor)
    self.saveBtn.setStyle(self.saveBtn.style())
