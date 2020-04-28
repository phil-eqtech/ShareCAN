# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'form-notepad.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Notepad(object):
    def setupUi(self, Notepad):
        Notepad.setObjectName("Notepad")
        Notepad.resize(600, 305)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Notepad.sizePolicy().hasHeightForWidth())
        Notepad.setSizePolicy(sizePolicy)
        Notepad.setWindowTitle("")
        self.verticalLayout = QtWidgets.QVBoxLayout(Notepad)
        self.verticalLayout.setObjectName("verticalLayout")
        self.notes = QtWidgets.QPlainTextEdit(Notepad)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.notes.sizePolicy().hasHeightForWidth())
        self.notes.setSizePolicy(sizePolicy)
        self.notes.setObjectName("notes")
        self.verticalLayout.addWidget(self.notes)

        self.retranslateUi(Notepad)
        QtCore.QMetaObject.connectSlotsByName(Notepad)

    def retranslateUi(self, Notepad):
        pass

