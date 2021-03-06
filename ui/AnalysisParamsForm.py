# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'form-analysis_params.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AnalysisParams(object):
    def setupUi(self, AnalysisParams):
        AnalysisParams.setObjectName("AnalysisParams")
        AnalysisParams.resize(600, 305)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AnalysisParams.sizePolicy().hasHeightForWidth())
        AnalysisParams.setSizePolicy(sizePolicy)
        AnalysisParams.setWindowTitle("")
        self.formLayout = QtWidgets.QFormLayout(AnalysisParams)
        self.formLayout.setObjectName("formLayout")
        self.labelVehicleType = QtWidgets.QLabel(AnalysisParams)
        self.labelVehicleType.setObjectName("labelVehicleType")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.labelVehicleType)
        self.fldVehicleType = QtWidgets.QComboBox(AnalysisParams)
        self.fldVehicleType.setObjectName("fldVehicleType")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.fldVehicleType)
        self.labelManufacturer = QtWidgets.QLabel(AnalysisParams)
        self.labelManufacturer.setObjectName("labelManufacturer")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.labelManufacturer)
        self.fldManufacturer = QtWidgets.QLineEdit(AnalysisParams)
        self.fldManufacturer.setObjectName("fldManufacturer")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.fldManufacturer)
        self.labelModel = QtWidgets.QLabel(AnalysisParams)
        self.labelModel.setObjectName("labelModel")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.labelModel)
        self.fldModel = QtWidgets.QLineEdit(AnalysisParams)
        self.fldModel.setObjectName("fldModel")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.fldModel)
        self.labelYear = QtWidgets.QLabel(AnalysisParams)
        self.labelYear.setObjectName("labelYear")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.labelYear)
        self.fldYear = QtWidgets.QLineEdit(AnalysisParams)
        self.fldYear.setMaximumSize(QtCore.QSize(80, 16777215))
        self.fldYear.setMaxLength(4)
        self.fldYear.setObjectName("fldYear")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.fldYear)
        self.labelEngine = QtWidgets.QLabel(AnalysisParams)
        self.labelEngine.setObjectName("labelEngine")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.labelEngine)
        self.fldEngine = QtWidgets.QComboBox(AnalysisParams)
        self.fldEngine.setObjectName("fldEngine")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.fldEngine)
        self.labelVIN = QtWidgets.QLabel(AnalysisParams)
        self.labelVIN.setObjectName("labelVIN")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.labelVIN)
        self.fldVIN = QtWidgets.QLineEdit(AnalysisParams)
        self.fldVIN.setMaximumSize(QtCore.QSize(300, 16777215))
        self.fldVIN.setMaxLength(24)
        self.fldVIN.setObjectName("fldVIN")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.fldVIN)
        self.line1 = QtWidgets.QFrame(AnalysisParams)
        self.line1.setFrameShape(QtWidgets.QFrame.HLine)
        self.line1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line1.setObjectName("line1")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.SpanningRole, self.line1)
        self.labelMode = QtWidgets.QLabel(AnalysisParams)
        self.labelMode.setObjectName("labelMode")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.LabelRole, self.labelMode)
        self.fldPrivacyMode = QtWidgets.QComboBox(AnalysisParams)
        self.fldPrivacyMode.setObjectName("fldPrivacyMode")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.FieldRole, self.fldPrivacyMode)
        self.labelModeCommnt = QtWidgets.QLabel(AnalysisParams)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setItalic(True)
        self.labelModeCommnt.setFont(font)
        self.labelModeCommnt.setWordWrap(True)
        self.labelModeCommnt.setObjectName("labelModeCommnt")
        self.formLayout.setWidget(8, QtWidgets.QFormLayout.FieldRole, self.labelModeCommnt)

        self.retranslateUi(AnalysisParams)
        QtCore.QMetaObject.connectSlotsByName(AnalysisParams)

    def retranslateUi(self, AnalysisParams):
        _translate = QtCore.QCoreApplication.translate
        self.labelVehicleType.setText(_translate("AnalysisParams", "VEHICLE_TYPE"))
        self.labelManufacturer.setText(_translate("AnalysisParams", "MANUFACTURER"))
        self.labelModel.setText(_translate("AnalysisParams", "MODEL"))
        self.labelYear.setText(_translate("AnalysisParams", "YEAR"))
        self.labelEngine.setText(_translate("AnalysisParams", "ENGINE"))
        self.labelVIN.setText(_translate("AnalysisParams", "VIN"))
        self.labelMode.setText(_translate("AnalysisParams", "PRIVACY_MODE"))
        self.labelModeCommnt.setText(_translate("AnalysisParams", "PRIVACY_MODE_COMMENT"))

