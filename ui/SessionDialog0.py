from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import qtawesome as qta

import time
import logging

from ui.ModelDialog import ModelDialog
from ui.SessionsForm import Ui_SESSIONS

class SessionList(QWidget, Ui_SESSIONS):
  def __init__(self):
   super().__init__()
   self.setupUi(self)


class SessionDialog(ModelDialog):
  def __init__(self, refWindow, loadSession = False, saveSession = False, replaySession= False):
    super().__init__()

    self.getMainVariables(refWindow)

    self.loadSession = loadSession
    self.saveSession = saveSession
    self.replaySession = replaySession

    self.comboNameLock = False

    # Bottom buttons
    self.closeBtn = QPushButton()
    self.closeBtn.setIcon(qta.icon('fa.close',color='white'))
    self.closeBtn.setText(QCoreApplication.translate("DIALOG", "CLOSE"))
    self.closeBtn.setProperty("cssClass","btn-danger")
    self.closeBtn.setCursor(Qt.PointingHandCursor)
    self.closeBtn.clicked.connect(self.reject)

    if self.saveSession == True:
      self.dialogTitle.setText(QCoreApplication.translate("SESSION","SAVE_SESSION"))
      self.saveBtn = QPushButton()
      self.saveBtn.setIcon(qta.icon('fa.save',options=[{'color':'white', 'color_disabled':'black'}]))
      self.saveBtn.setText(QCoreApplication.translate("DIALOG", "SAVE"))
      self.saveBtn.setProperty("cssClass","btn-disabled")
      self.saveBtn.setDisabled(True)
      self.saveBtn.setCursor(Qt.ArrowCursor)
      self.saveBtn.clicked.connect(lambda: self.setSessionName())
      self.setBottomButtons([self.closeBtn, self.saveBtn])
    elif self.loadSession == True:
      self.dialogTitle.setText(QCoreApplication.translate("SESSION","LOAD_SESSION"))
      self.setBottomButtons(self.closeBtn)


    # Loading body template
    self.body = SessionList()
    self.dialogBody.addWidget(self.body)

    # Editing grid
    self.drawDialogBody()

  #
  # Session save
  #
  def freeSaveBtn(self, txt):
    if len(txt) > 0:
      self.saveBtn.setCursor(Qt.PointingHandCursor)
      self.saveBtn.setDisabled(False)
      self.saveBtn.setProperty("cssClass","btn-success")
      self.saveBtn.setStyle(self.saveBtn.style())
    else:
      self.saveBtn.setCursor(Qt.ArrowCursor)
      self.saveBtn.setDisabled(True)
      self.saveBtn.setProperty("cssClass","btn-disabled")
      self.saveBtn.setStyle(self.saveBtn.style())

  def setSessionName(self):
    self.session['comment'] = self.body.fldSessionComment.toPlainText()
    self.session['name'] = self.body.fldSessionName.displayText()
    self.done(1)

  #
  # Session load
  #
  def switchSessionRange(self):
    self.comboNameLock = True
    self.body.btnDelete.hide()
    self.body.btnShare.hide()
    self.body.btnLoad.hide()
    self.body.fldAuthor.setText("")
    self.body.fldComment.setPlainText("")

    if self.body.comboRange.currentIndex() == 0:
      self.body.fldAuthor.hide()
      self.body.lblAuthor.hide()
      critera = {"owner":self.user['uid'], "analysis": self.analysis['id']}
    else:
      self.body.fldAuthor.show()
      self.body.lblAuthor.show()
      analysisCursor = self.db.analysis.find({"model": self.analysis['model'],
                                              "manufacturer":self.analysis['manufacturer']},{"id":1})
      analysis = []
      if analysisCursor.count() > 0:
        for elt in analysisCursor:
          analysis.append(elt['id'])
      critera = {"owner":{"$ne":self.user['uid']}, "analysis":{"$in":analysis}}
    sessionCursor = self.db.sessions.find(critera, {"id":1, "name":1, "share":1, "owner":1,"comment":1})

    itemQty = self.body.comboName.count()
    for i in range(0, itemQty):
      self.body.comboName.removeItem(0)

    self.body.comboName.addItem("-", None)
    if sessionCursor.count() > 0:
      sessionCursor.sort([("name",1)])
      for session in sessionCursor:
        self.body.comboName.addItem(session['name'], session)
    self.comboNameLock = False

  def deleteSession(self):
    if self.body.comboName.currentIndex() > 0:
      s = self.body.comboName.currentData()
      if s['owner'] == self.user['uid']:
        msgBox = QMessageBox()
        msgBox.setText(QCoreApplication.translate("SESSION","SESSION_DELETE_CONFIRM"))
        msgBox.setWindowTitle(QCoreApplication.translate("SESSION","SESSION_DELETE_CONFIRM"))
        msgBox.setInformativeText(QCoreApplication.translate("SESSION","SESSION_DELETE_CONFIRM_DETAILS"))
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Ok)
        self.centerMsg(msgBox)
        choice = msgBox.exec()

        if choice == QMessageBox.Ok:
          self.db.sessions.remove({"id":s['id']})
          self.db.frames.remove({"session":s['id']})
          self.body.comboName.removeItem(self.body.comboName.currentIndex())
          self.body.comboName.setCurrentIndex(0)
          if self.session['id'] == s['id']:
            pass

  def loadSessionMetaData(self):
    if self.comboNameLock == False:
      if self.body.comboName.currentIndex() > 0:
        s = self.body.comboName.currentData()
        if 'comment' in s:
          self.body.fldComment.setPlainText(s['comment'])
        else:
          self.body.fldComment.setPlainText("")

        self.body.btnLoad.show()

        if s['owner'] != self.user['uid']:
          userCursor = self.db.users.find({"uid":s['owner']}, {"name":1})
          if userCursor.count() == 1:
            self.body.fldAuthor.setText(userCursor[0]['name'])
          else:
            self.body.fldAuthor.setText(QCoreApplication.translate("SESSION","UNKNOWN_USER"))
          self.body.btnShare.hide()
          self.body.btnDelete.hide()
        else:
          self.body.btnShare.show()
          if s['share'] == True:
            self.body.btnShare.setProperty("cssClass","btn-primary")
            self.body.btnShare.setText(QCoreApplication.translate("SESSION","SHARED"))
          else:
            self.body.btnShare.setProperty("cssClass","btn-secondary")
            self.body.btnShare.setText(QCoreApplication.translate("SESSION","NOT_SHARED"))
          self.body.btnShare.setStyle(self.body.btnShare.style())
          if s['id'] == self.session['id']:
            self.body.btnDelete.setProperty("cssClass","btn-disabled")
            self.body.btnDelete.setDisabled(True)
            self.body.btnDelete.setStyle(self.body.btnShare.style())
          else:
            self.body.btnDelete.setProperty("cssClass","btn-danger")
            self.body.btnDelete.setDisabled(False)
            self.body.btnDelete.setStyle(self.body.btnShare.style())
          self.body.btnDelete.show()
      else:
        self.body.fldComment.setPlainText("")
        self.body.btnShare.hide()
        self.body.btnDelete.hide()
        self.body.btnLoad.hide()

  def returnSessionData(self):
    if self.body.comboName.currentIndex() > 0:
      s = self.body.comboName.currentData()
      self.session['id'] = s['id']
      self.done(1)

  def switchShareStatus(self):
    if self.body.comboName.currentIndex() > 0:
      s = self.body.comboName.currentData()
      if s['owner'] == self.user['uid']:
        s['share'] = not s['share']
        self.body.comboName.setItemData(self.body.comboName.currentIndex(),s)
        if s['share'] == True:
          self.body.btnShare.setProperty("cssClass","btn-primary")
          self.body.btnShare.setText(QCoreApplication.translate("SESSION","SHARED"))
        else:
          self.body.btnShare.setProperty("cssClass","btn-secondary")
          self.body.btnShare.setText(QCoreApplication.translate("SESSION","NOT_SHARED"))
        self.body.btnShare.setStyle(self.body.btnShare.style())
        self.db.sessions.update({"id":s['id']},{"$set":{"share":s['share']}})

  def drawDialogBody(self):
    if self.saveSession == True:
      self.body.sessionGridLoad.hide()
      self.body.fldSessionName.textChanged.connect(lambda x: self.freeSaveBtn(x))
      if self.session['id'] != None:
        self.body.fldSessionComment.setPlainText(self.session['comment'])
        self.body.fldSessionName.setText(self.session['name'])
    elif self.loadSession == True:
      self.body.sessionGridSave.hide()
      self.body.comboRange.addItem(QCoreApplication.translate("SESSION","USER_SESSION"))
      self.body.comboRange.addItem(QCoreApplication.translate("SESSION","SHARED_SESSION"))
      self.body.comboRange.currentIndexChanged.connect(lambda: self.switchSessionRange())
      self.body.comboName.currentIndexChanged.connect(lambda: self.loadSessionMetaData())
      self.body.btnShare.setIcon(qta.icon("fa.share-alt", options=[{"color":"white", "color_disabled":"black"}]))
      self.body.btnDelete.setIcon(qta.icon("mdi.delete", options=[{"color":"white", "color_disabled":"black"}]))
      self.body.btnLoad.setIcon(qta.icon("fa.folder-open", options=[{"color":"white", "color_disabled":"black"}]))
      self.body.btnShare.clicked.connect(lambda: self.switchShareStatus())
      self.body.btnDelete.clicked.connect(lambda: self.deleteSession())
      self.body.btnLoad.clicked.connect(lambda: self.returnSessionData())
      self.switchSessionRange()
