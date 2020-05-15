# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'form-replay.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_REPLAY(object):
    def setupUi(self, REPLAY):
        REPLAY.setObjectName("REPLAY")
        REPLAY.resize(600, 426)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(REPLAY.sizePolicy().hasHeightForWidth())
        REPLAY.setSizePolicy(sizePolicy)
        REPLAY.setWindowTitle("")
        self.verticalLayout = QtWidgets.QVBoxLayout(REPLAY)
        self.verticalLayout.setObjectName("verticalLayout")
        self.replayMainGrid = QtWidgets.QWidget(REPLAY)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.replayMainGrid.sizePolicy().hasHeightForWidth())
        self.replayMainGrid.setSizePolicy(sizePolicy)
        self.replayMainGrid.setObjectName("replayMainGrid")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.replayMainGrid)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 6)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.checkLoop = QtWidgets.QCheckBox(self.replayMainGrid)
        self.checkLoop.setText("")
        self.checkLoop.setObjectName("checkLoop")
        self.gridLayout_2.addWidget(self.checkLoop, 3, 1, 1, 1)
        self.titleFeedback = QtWidgets.QLabel(self.replayMainGrid)
        self.titleFeedback.setObjectName("titleFeedback")
        self.gridLayout_2.addWidget(self.titleFeedback, 3, 2, 1, 1)
        self.lblFrames = QtWidgets.QLabel(self.replayMainGrid)
        self.lblFrames.setText("")
        self.lblFrames.setObjectName("lblFrames")
        self.gridLayout_2.addWidget(self.lblFrames, 2, 1, 1, 1)
        self.titleReplayInfo = QtWidgets.QLabel(self.replayMainGrid)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.titleReplayInfo.setFont(font)
        self.titleReplayInfo.setObjectName("titleReplayInfo")
        self.gridLayout_2.addWidget(self.titleReplayInfo, 0, 0, 1, 1)
        self.lblMode = QtWidgets.QLabel(self.replayMainGrid)
        self.lblMode.setText("")
        self.lblMode.setObjectName("lblMode")
        self.gridLayout_2.addWidget(self.lblMode, 1, 1, 1, 1)
        self.titleLoop = QtWidgets.QLabel(self.replayMainGrid)
        self.titleLoop.setObjectName("titleLoop")
        self.gridLayout_2.addWidget(self.titleLoop, 3, 0, 1, 1)
        self.titleMode = QtWidgets.QLabel(self.replayMainGrid)
        self.titleMode.setObjectName("titleMode")
        self.gridLayout_2.addWidget(self.titleMode, 1, 0, 1, 1)
        self.titleFrames = QtWidgets.QLabel(self.replayMainGrid)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.titleFrames.setFont(font)
        self.titleFrames.setObjectName("titleFrames")
        self.gridLayout_2.addWidget(self.titleFrames, 2, 0, 1, 1)
        self.titleId = QtWidgets.QLabel(self.replayMainGrid)
        self.titleId.setObjectName("titleId")
        self.gridLayout_2.addWidget(self.titleId, 1, 2, 1, 1)
        self.titleMsg = QtWidgets.QLabel(self.replayMainGrid)
        self.titleMsg.setObjectName("titleMsg")
        self.gridLayout_2.addWidget(self.titleMsg, 2, 2, 1, 1)
        self.lblMsg = QtWidgets.QLabel(self.replayMainGrid)
        self.lblMsg.setText("")
        self.lblMsg.setObjectName("lblMsg")
        self.gridLayout_2.addWidget(self.lblMsg, 2, 3, 1, 1)
        self.lblId = QtWidgets.QLabel(self.replayMainGrid)
        self.lblId.setText("")
        self.lblId.setObjectName("lblId")
        self.gridLayout_2.addWidget(self.lblId, 1, 3, 1, 1)
        self.comboFeedback = QtWidgets.QComboBox(self.replayMainGrid)
        self.comboFeedback.setObjectName("comboFeedback")
        self.comboFeedback.addItem("")
        self.comboFeedback.addItem("")
        self.comboFeedback.addItem("")
        self.comboFeedback.addItem("")
        self.gridLayout_2.addWidget(self.comboFeedback, 3, 3, 1, 1)
        self.verticalLayout.addWidget(self.replayMainGrid)
        self.splitRequired = QtWidgets.QFrame(REPLAY)
        self.splitRequired.setFrameShape(QtWidgets.QFrame.HLine)
        self.splitRequired.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.splitRequired.setObjectName("splitRequired")
        self.verticalLayout.addWidget(self.splitRequired)
        self.deviceTitle = QtWidgets.QLabel(REPLAY)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.deviceTitle.sizePolicy().hasHeightForWidth())
        self.deviceTitle.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.deviceTitle.setFont(font)
        self.deviceTitle.setObjectName("deviceTitle")
        self.verticalLayout.addWidget(self.deviceTitle)
        self.replayBusGridWidget = QtWidgets.QWidget(REPLAY)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.replayBusGridWidget.sizePolicy().hasHeightForWidth())
        self.replayBusGridWidget.setSizePolicy(sizePolicy)
        self.replayBusGridWidget.setObjectName("replayBusGridWidget")
        self.replayBusGridLayout = QtWidgets.QGridLayout(self.replayBusGridWidget)
        self.replayBusGridLayout.setObjectName("replayBusGridLayout")
        self.titleIface = QtWidgets.QLabel(self.replayBusGridWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.titleIface.setFont(font)
        self.titleIface.setObjectName("titleIface")
        self.replayBusGridLayout.addWidget(self.titleIface, 0, 3, 1, 1)
        self.titleType = QtWidgets.QLabel(self.replayBusGridWidget)
        self.titleType.setMaximumSize(QtCore.QSize(80, 16777215))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.titleType.setFont(font)
        self.titleType.setObjectName("titleType")
        self.replayBusGridLayout.addWidget(self.titleType, 0, 0, 1, 1)
        self.titleBus = QtWidgets.QLabel(self.replayBusGridWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.titleBus.sizePolicy().hasHeightForWidth())
        self.titleBus.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.titleBus.setFont(font)
        self.titleBus.setObjectName("titleBus")
        self.replayBusGridLayout.addWidget(self.titleBus, 0, 2, 1, 1)
        self.titleName = QtWidgets.QLabel(self.replayBusGridWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.titleName.setFont(font)
        self.titleName.setObjectName("titleName")
        self.replayBusGridLayout.addWidget(self.titleName, 0, 1, 1, 1)
        self.verticalLayout.addWidget(self.replayBusGridWidget)
        self.split = QtWidgets.QFrame(REPLAY)
        self.split.setFrameShape(QtWidgets.QFrame.HLine)
        self.split.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.split.setObjectName("split")
        self.verticalLayout.addWidget(self.split)
        self.replayBtnGrid = QtWidgets.QWidget(REPLAY)
        self.replayBtnGrid.setObjectName("replayBtnGrid")
        self.gridLayout = QtWidgets.QGridLayout(self.replayBtnGrid)
        self.gridLayout.setContentsMargins(0, -1, 0, -1)
        self.gridLayout.setObjectName("gridLayout")
        self.btnPrevious = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnPrevious.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnPrevious.setObjectName("btnPrevious")
        self.gridLayout.addWidget(self.btnPrevious, 3, 0, 1, 1)
        self.btnReplayAll = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnReplayAll.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnReplayAll.setObjectName("btnReplayAll")
        self.gridLayout.addWidget(self.btnReplayAll, 6, 0, 1, 1)
        self.btnRevert = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnRevert.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnRevert.setObjectName("btnRevert")
        self.gridLayout.addWidget(self.btnRevert, 3, 1, 1, 1)
        self.btnReplay = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnReplay.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnReplay.setObjectName("btnReplay")
        self.gridLayout.addWidget(self.btnReplay, 4, 1, 1, 1)
        self.btnCancelAll = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnCancelAll.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnCancelAll.setObjectName("btnCancelAll")
        self.gridLayout.addWidget(self.btnCancelAll, 5, 3, 1, 1)
        self.btnCancel = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnCancel.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnCancel.setObjectName("btnCancel")
        self.gridLayout.addWidget(self.btnCancel, 4, 3, 1, 1)
        self.btnSlice = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnSlice.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnSlice.setObjectName("btnSlice")
        self.gridLayout.addWidget(self.btnSlice, 3, 2, 1, 1)
        self.btnUpdate = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnUpdate.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnUpdate.setObjectName("btnUpdate")
        self.gridLayout.addWidget(self.btnUpdate, 4, 0, 1, 1)
        self.btnStop = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnStop.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnStop.setObjectName("btnStop")
        self.gridLayout.addWidget(self.btnStop, 4, 2, 1, 1)
        self.btnSliceAll = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnSliceAll.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnSliceAll.setObjectName("btnSliceAll")
        self.gridLayout.addWidget(self.btnSliceAll, 5, 1, 1, 1)
        self.btnAddCommand = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnAddCommand.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnAddCommand.setObjectName("btnAddCommand")
        self.gridLayout.addWidget(self.btnAddCommand, 6, 2, 1, 1)
        self.btnSmartReplay = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnSmartReplay.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnSmartReplay.setObjectName("btnSmartReplay")
        self.gridLayout.addWidget(self.btnSmartReplay, 6, 1, 1, 1)
        self.titlePlaying = QtWidgets.QLabel(self.replayBtnGrid)
        self.titlePlaying.setObjectName("titlePlaying")
        self.gridLayout.addWidget(self.titlePlaying, 2, 0, 1, 1)
        self.btnNext = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnNext.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnNext.setObjectName("btnNext")
        self.gridLayout.addWidget(self.btnNext, 3, 3, 1, 1)
        self.progress = QtWidgets.QProgressBar(self.replayBtnGrid)
        self.progress.setProperty("value", 0)
        self.progress.setObjectName("progress")
        self.gridLayout.addWidget(self.progress, 0, 0, 1, 4)
        self.btnUpdateSession = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnUpdateSession.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnUpdateSession.setObjectName("btnUpdateSession")
        self.gridLayout.addWidget(self.btnUpdateSession, 6, 3, 1, 1)
        self.btnBack = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnBack.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnBack.setObjectName("btnBack")
        self.gridLayout.addWidget(self.btnBack, 5, 0, 1, 1)
        self.btnPause = QtWidgets.QPushButton(self.replayBtnGrid)
        self.btnPause.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btnPause.setObjectName("btnPause")
        self.gridLayout.addWidget(self.btnPause, 5, 2, 1, 1)
        self.lblFrameCount = QtWidgets.QLabel(self.replayBtnGrid)
        self.lblFrameCount.setText("")
        self.lblFrameCount.setObjectName("lblFrameCount")
        self.gridLayout.addWidget(self.lblFrameCount, 2, 1, 1, 2)
        self.lblFrameId = QtWidgets.QLabel(self.replayBtnGrid)
        self.lblFrameId.setText("")
        self.lblFrameId.setAlignment(QtCore.Qt.AlignCenter)
        self.lblFrameId.setObjectName("lblFrameId")
        self.gridLayout.addWidget(self.lblFrameId, 1, 0, 1, 4)
        self.verticalLayout.addWidget(self.replayBtnGrid)
        spacerItem = QtWidgets.QSpacerItem(20, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(REPLAY)
        QtCore.QMetaObject.connectSlotsByName(REPLAY)

    def retranslateUi(self, REPLAY):
        _translate = QtCore.QCoreApplication.translate
        self.titleFeedback.setText(_translate("REPLAY", "LIVE_REPLAY"))
        self.titleReplayInfo.setText(_translate("REPLAY", "REPLAY_INFO"))
        self.titleLoop.setText(_translate("REPLAY", "LOOP_REPLAY"))
        self.titleMode.setText(_translate("REPLAY", "MODE"))
        self.titleFrames.setText(_translate("REPLAY", "FRAMES"))
        self.titleId.setText(_translate("REPLAY", "CURRENT_ID"))
        self.titleMsg.setText(_translate("REPLAY", "CURRENT_MSG"))
        self.comboFeedback.setItemText(0, _translate("REPLAY", "NONE"))
        self.comboFeedback.setItemText(1, _translate("REPLAY", "FEEDBACK_LIVE"))
        self.comboFeedback.setItemText(2, _translate("REPLAY", "FEEDBACK_RECORD"))
        self.comboFeedback.setItemText(3, _translate("REPLAY", "FEEDBACK_RECORD_NEW"))
        self.deviceTitle.setText(_translate("REPLAY", "REPLAY_REQUIRED_BUS"))
        self.titleIface.setText(_translate("REPLAY", "INTERFACES"))
        self.titleType.setText(_translate("REPLAY", "TYPE"))
        self.titleBus.setText(_translate("REPLAY", "BUS"))
        self.titleName.setText(_translate("REPLAY", "NAME"))
        self.btnPrevious.setText(_translate("REPLAY", "PREVIOUS"))
        self.btnPrevious.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.btnReplayAll.setText(_translate("REPLAY", "REPLAY_ALL"))
        self.btnReplayAll.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.btnRevert.setText(_translate("REPLAY", "REVERT"))
        self.btnRevert.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.btnReplay.setText(_translate("REPLAY", "REPLAY"))
        self.btnReplay.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.btnCancelAll.setText(_translate("REPLAY", "CANCEL"))
        self.btnCancelAll.setProperty("cssClass", _translate("REPLAY", "btn-danger"))
        self.btnCancel.setText(_translate("REPLAY", "CANCEL"))
        self.btnCancel.setProperty("cssClass", _translate("REPLAY", "btn-danger"))
        self.btnSlice.setText(_translate("REPLAY", "SLICE"))
        self.btnSlice.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.btnUpdate.setText(_translate("REPLAY", "UPDATE"))
        self.btnUpdate.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.btnStop.setText(_translate("REPLAY", "STOP"))
        self.btnStop.setProperty("cssClass", _translate("REPLAY", "btn-danger"))
        self.btnSliceAll.setText(_translate("REPLAY", "SLICE"))
        self.btnSliceAll.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.btnAddCommand.setText(_translate("REPLAY", "ADD_COMMAND"))
        self.btnSmartReplay.setText(_translate("REPLAY", "SMART_REPLAY"))
        self.btnSmartReplay.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.titlePlaying.setText(_translate("REPLAY", "PLAYING"))
        self.btnNext.setText(_translate("REPLAY", "NEXT"))
        self.btnNext.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.btnUpdateSession.setText(_translate("REPLAY", "UPDATE_SESSION"))
        self.btnUpdateSession.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.btnBack.setText(_translate("REPLAY", "BACK_3_SEC"))
        self.btnBack.setProperty("cssClass", _translate("REPLAY", "btn-primary"))
        self.btnPause.setText(_translate("REPLAY", "PAUSE"))
        self.btnPause.setProperty("cssClass", _translate("REPLAY", "btn-danger"))

