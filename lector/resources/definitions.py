# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'raw/definition.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(729, 318)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.definitionView = QtWidgets.QTextBrowser(Dialog)
        self.definitionView.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.definitionView.setFrameShadow(QtWidgets.QFrame.Plain)
        self.definitionView.setObjectName("definitionView")
        self.verticalLayout.addWidget(self.definitionView)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/checkmark.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.okButton.setIcon(icon)
        self.okButton.setIconSize(QtCore.QSize(24, 24))
        self.okButton.setFlat(True)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.pronounceButton = QtWidgets.QPushButton(Dialog)
        self.pronounceButton.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/images/QMPlay2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pronounceButton.setIcon(icon1)
        self.pronounceButton.setIconSize(QtCore.QSize(24, 24))
        self.pronounceButton.setFlat(True)
        self.pronounceButton.setObjectName("pronounceButton")
        self.horizontalLayout.addWidget(self.pronounceButton)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.dialogBackground = QtWidgets.QPushButton(Dialog)
        self.dialogBackground.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/images/color.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.dialogBackground.setIcon(icon2)
        self.dialogBackground.setIconSize(QtCore.QSize(27, 27))
        self.dialogBackground.setFlat(True)
        self.dialogBackground.setObjectName("dialogBackground")
        self.horizontalLayout.addWidget(self.dialogBackground)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.okButton.setToolTip(_translate("Dialog", "WERDS"))
        self.pronounceButton.setToolTip(_translate("Dialog", "Play pronunciation of root word"))
