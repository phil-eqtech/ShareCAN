from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import qtawesome as qta

import time
import uuid

from modules.Constants import *
from ui.ModelDialog import ModelDialog, UCValidator
from ui.NotepadForm import Ui_Notepad

class Notepad(QWidget, Ui_Notepad):
  def __init__(self):
   super().__init__()
   self.setupUi(self)

class NotepadDialog(ModelDialog):
  def __init__(self, refWindow):
    super().__init__()

    self.getMainVariables(refWindow)

    self.notes = ""

    noteCursor = self.db.analysis.find({"id": self.analysis['id']},{"_id":0, "notes":1})
    if noteCursor.count() == 1:
      if 'notes' in noteCursor[0]:
        self.notes = noteCursor[0]['notes']

    self.closeBtn = QPushButton()
    self.closeBtn.setIcon(qta.icon('fa.close',color='white'))
    self.dialogTitle.setText(QCoreApplication.translate("GENERIC","NOTEPAD"))
    self.closeBtn.setText(QCoreApplication.translate("DIALOG", "CLOSE"))
    self.closeBtn.setProperty("cssClass","btn-danger")
    self.closeBtn.setCursor(Qt.PointingHandCursor)
    self.closeBtn.clicked.connect(self.reject)
    self.setBottomButtons([self.closeBtn])

    # Loading body template
    self.body = Notepad()
    self.dialogBody.addWidget(self.body)

    self.body.notes.textChanged.connect(lambda: self.saveNotes())
    # Editing grid
    self.drawDialogBody()


  def drawDialogBody(self):
    self.body.notes.setPlainText(self.notes)

  def saveNotes(self):
    self.db.analysis.update({"id":self.analysis['id']}, {"$set":{"notes": self.body.notes.toPlainText()}})
