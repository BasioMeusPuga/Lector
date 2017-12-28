# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'raw/settings.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(929, 638)
        self.gridLayout_3 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.treeView = QtWidgets.QTreeView(self.groupBox_2)
        self.treeView.setObjectName("treeView")
        self.gridLayout_2.addWidget(self.treeView, 0, 0, 1, 1)
        self.aboutBox = QtWidgets.QTextBrowser(self.groupBox_2)
        self.aboutBox.setOpenExternalLinks(True)
        self.aboutBox.setOpenLinks(False)
        self.aboutBox.setObjectName("aboutBox")
        self.gridLayout_2.addWidget(self.aboutBox, 1, 0, 1, 1)
        self.verticalLayout_2.addWidget(self.groupBox_2)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.refreshLibrary = QtWidgets.QCheckBox(self.groupBox)
        self.refreshLibrary.setObjectName("refreshLibrary")
        self.horizontalLayout_4.addWidget(self.refreshLibrary)
        self.fileRemember = QtWidgets.QCheckBox(self.groupBox)
        self.fileRemember.setObjectName("fileRemember")
        self.horizontalLayout_4.addWidget(self.fileRemember)
        self.coverShadows = QtWidgets.QCheckBox(self.groupBox)
        self.coverShadows.setObjectName("coverShadows")
        self.horizontalLayout_4.addWidget(self.coverShadows)
        self.autoTags = QtWidgets.QCheckBox(self.groupBox)
        self.autoTags.setObjectName("autoTags")
        self.horizontalLayout_4.addWidget(self.autoTags)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.gridLayout_3.addLayout(self.verticalLayout_2, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout_2.addWidget(self.okButton)
        self.cancelButton = QtWidgets.QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout_2.addWidget(self.cancelButton)
        self.aboutButton = QtWidgets.QPushButton(Dialog)
        self.aboutButton.setObjectName("aboutButton")
        self.horizontalLayout_2.addWidget(self.aboutButton)
        self.gridLayout_3.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Settings"))
        self.groupBox_2.setTitle(_translate("Dialog", "Library"))
        self.groupBox.setTitle(_translate("Dialog", "Switches"))
        self.refreshLibrary.setText(_translate("Dialog", "Startup: Refresh library"))
        self.fileRemember.setText(_translate("Dialog", "Remember open files"))
        self.coverShadows.setText(_translate("Dialog", "Cover shadows"))
        self.autoTags.setText(_translate("Dialog", "Generate tags from files"))
        self.okButton.setText(_translate("Dialog", "OK"))
        self.cancelButton.setText(_translate("Dialog", "Cancel"))
        self.aboutButton.setText(_translate("Dialog", "About"))

