from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class UCValidator(QValidator):
  def validate(self, string, pos):
    return QValidator.Acceptable, string.upper(), pos

class ModelDialog(QDialog):
  def __init__(self, *args, **kwargs):
    super(ModelDialog, self).__init__(*args, **kwargs)

    self.setProperty("cssClass","modalWindow")

    # Title
    titleWidget = QWidget()
    titleWidget.setProperty("cssClass","modalTitle")
    layoutTitle = QHBoxLayout()
    titleWidget.setLayout(layoutTitle)
    self.dialogTitle = QLabel("TITLE")
    font = QFont()
    font.setPointSize(14)
    font.setBold(False)
    font.setWeight(50)
    self.dialogTitle.setFont(font)
    layoutTitle.addWidget(self.dialogTitle)
    sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(titleWidget.sizePolicy().hasHeightForWidth())
    titleWidget.setSizePolicy(sizePolicy)

    # Body
    bodyWidget = QWidget()
    sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(bodyWidget.sizePolicy().hasHeightForWidth())
    bodyWidget.setSizePolicy(sizePolicy)
    bodyWidget.setProperty("cssClass","modalBody")
    self.dialogBody = QVBoxLayout()
    bodyWidget.setLayout(self.dialogBody)

    # Dialog
    self.layout = QVBoxLayout()
    self.layout.addWidget(titleWidget)
    self.layout.addWidget(bodyWidget)
    self.setLayout(self.layout)

  # Footer
  def setBottomButtons(self, bottomButtons):
    self.bottomButtons = QWidget()
    sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.bottomButtons.sizePolicy().hasHeightForWidth())
    self.bottomButtons.setSizePolicy(sizePolicy)
    self.bottomButtons.setObjectName("bottomButtons")
    self.layout.addWidget(self.bottomButtons)
    self.bottomLayout = QHBoxLayout(self.bottomButtons)
    self.bottomLayout.setObjectName("bottomLayout")
    spacerItem = QSpacerItem(5, 5, QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.bottomLayout.addItem(spacerItem)
    self.bottomButtons.setProperty("cssClass","modalFooter")

    if type(bottomButtons) == list:
      for btn in bottomButtons:
        self.bottomLayout.addWidget(btn)
    else:
      self.bottomLayout.addWidget(bottomButtons)

  def getMainVariables(self, mainWindowRef):
    self.db = mainWindowRef.db
    self.config = mainWindowRef.config
    self.user = mainWindowRef.user
    self.appSignals = mainWindowRef.appSignals
    self.analysis = mainWindowRef.analysis
    self.interfaces = mainWindowRef.interfaces
    self.session = mainWindowRef.session
    self.activeBus = mainWindowRef.activeBus
    self.threads = mainWindowRef.threads
    self.threadStopManager = mainWindowRef.threadStopManager
    self.signals =  mainWindowRef.signals
    print(self.analysis)

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

  def centerMsg(self, msgWidget):
    msgWidget.setGeometry(self.x(), self.y(), 300, 180)
    msgWidget.move(self.x() + (self.width() - msgWidget.width()) / 2,
                   self.y() + (self.height() - msgWidget.height()) / 2)
