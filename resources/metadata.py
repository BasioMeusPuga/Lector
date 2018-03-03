# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'raw/metadata.ui'
#
# Created by: PyQt5 UI code generator 5.10
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(700, 230)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMaximumSize(QtCore.QSize(700, 230))
        Dialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.coverView = QtWidgets.QGraphicsView(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.coverView.sizePolicy().hasHeightForWidth())
        self.coverView.setSizePolicy(sizePolicy)
        self.coverView.setMinimumSize(QtCore.QSize(140, 218))
        self.coverView.setMaximumSize(QtCore.QSize(140, 218))
        self.coverView.setBaseSize(QtCore.QSize(140, 200))
        self.coverView.setObjectName("coverView")
        self.horizontalLayout.addWidget(self.coverView)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.titleLine = QtWidgets.QLineEdit(Dialog)
        self.titleLine.setObjectName("titleLine")
        self.verticalLayout.addWidget(self.titleLine)
        self.authorLine = QtWidgets.QLineEdit(Dialog)
        self.authorLine.setObjectName("authorLine")
        self.verticalLayout.addWidget(self.authorLine)
        self.yearLine = QtWidgets.QLineEdit(Dialog)
        self.yearLine.setObjectName("yearLine")
        self.verticalLayout.addWidget(self.yearLine)
        self.tagsLine = QtWidgets.QLineEdit(Dialog)
        self.tagsLine.setMinimumSize(QtCore.QSize(0, 0))
        self.tagsLine.setObjectName("tagsLine")
        self.verticalLayout.addWidget(self.tagsLine)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Edit metadata"))
        self.titleLine.setPlaceholderText(_translate("Dialog", "Title"))
        self.authorLine.setPlaceholderText(_translate("Dialog", "Author"))
        self.yearLine.setPlaceholderText(_translate("Dialog", "Year"))
        self.tagsLine.setPlaceholderText(_translate("Dialog", "Tags"))

