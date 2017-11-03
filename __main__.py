#!/usr/bin/env python3

""" TODO
    Define every widget in code because you're going to need to create separate tabs
    Override the keypress event of the textedit
    Goodreads API: Ratings, Read, Recommendations
    Get ISBN using python-isbnlib
    Theming
    Pagination
    sqlite3 for storing metadata
    Drop down for TOC
    Recursive file addition
    Get cover images
    Set context menu for definitions and the like
"""

import os
import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import mainwindow


class MainUI(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        # Set up a dictionary to keep track of new tabs
        self.tabs = {}

        # Toolbar setup
        self.BookToolBar.hide()
        fullscreenButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('view-fullscreen'), 'Fullscreen', self)
        self.BookToolBar.addAction(fullscreenButton)
        fullscreenButton.triggered.connect(self.set_fullscreen)

        # LibraryToolBar buttons
        addButton = QtWidgets.QAction(QtGui.QIcon.fromTheme('add'), 'Add book', self)
        deleteButton = QtWidgets.QAction(QtGui.QIcon.fromTheme('remove'), 'Delete book', self)
        settingsButton = QtWidgets.QAction(QtGui.QIcon.fromTheme('settings'), 'Settings', self)
        addButton.triggered.connect(self.create_tab)

        self.LibraryToolBar.addAction(addButton)
        self.LibraryToolBar.addAction(deleteButton)
        self.LibraryToolBar.addSeparator()
        self.LibraryToolBar.addAction(settingsButton)

        self.exit_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Escape'), self)
        self.exit_shortcut.activated.connect(self.set_normalsize)

        # Toolbar switching
        self.tabWidget.currentChanged.connect(self.toolbar_switch)


    def create_tab(self):
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.tab_3)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.textEdit1 = QtWidgets.QTextEdit(self.tab_3)
        self.textEdit1.setObjectName("textEdit1")
        self.gridLayout_4.addWidget(self.textEdit1, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_3, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), 'self.book_title')
        self.textEdit1.setText(', '.join(dir(self))) 

    
    def toolbar_switch(self):
        if self.tabWidget.currentIndex() == 0:
            self.BookToolBar.hide()
            self.LibraryToolBar.show()
        else:
            self.BookToolBar.show()
            self.LibraryToolBar.hide()

    
    def set_fullscreen(self):
        scr = QtGui.QGuiApplication.primaryScreen()
        agm = QtGui.QScreen.availableGeometry(scr)
        self.textEdit.setParent(self)
        self.textEdit.setGeometry(agm)
        self.textEdit.showFullScreen()
        self.showFullScreen()

    def set_normalsize(self):
        self.textEdit.setParent(self.tab_2)
        self.textEdit.showNormal()
        self.showNormal()





def wutface():
    print('huh?')


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = MainUI()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
