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

        # New tabs and their contents
        self.tabs = {}
        self.current_tab = None
        self.current_textEdit = None
        self.current_textEdit_parent = None

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
        addButton.triggered.connect(self.create_tab_class)

        self.LibraryToolBar.addAction(addButton)
        self.LibraryToolBar.addAction(deleteButton)
        self.LibraryToolBar.addSeparator()
        self.LibraryToolBar.addAction(settingsButton)

        self.exit_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Escape'), self.textEdit)
        self.exit_shortcut.activated.connect(self.testfsoff)

        # Toolbar switching
        self.tabWidget.currentChanged.connect(self.toolbar_switch)

        # Tab closing
        self.tabWidget.tabCloseRequested.connect(self.close_tab_class)

        self.pushButton.clicked.connect(self.testfs)

    def create_tab_class(self):
        # TODO
        # Shift focus to tab if it's already open instead of creating
        # a new one
        self.tabs['TitleText'] = {
            'information about': 'This tab'}
        this_tab = Tabs(self, 'TitleText')
        this_tab.create_tab()

    def close_tab_class(self, tab_index):
        this_tab = Tabs(self, None)
        this_tab.close_tab(tab_index)

    def toolbar_switch(self):
        if self.tabWidget.currentIndex() == 0:
            self.BookToolBar.hide()
            self.LibraryToolBar.show()
        else:
            self.BookToolBar.show()
            self.LibraryToolBar.hide()

    def set_fullscreen(self):
        self.current_tab = self.tabWidget.currentIndex()
        self.current_textEdit = self.tabWidget.widget(self.current_tab)
        self.current_textEdit_parent = self.current_textEdit.parent()
        print(self.current_textEdit_parent)

        scr = QtGui.QGuiApplication.primaryScreen()
        agm = QtGui.QScreen.availableGeometry(scr)

        self.current_textEdit.setParent(self)
        self.current_textEdit.setGeometry(agm)
        self.current_textEdit.showFullScreen()
        self.showFullScreen()

    def set_normalsize(self):
        # TODO
        # Figure out how to restore the textEdit to its original parent
        # self.current_textEdit.setParent(self.current_textEdit_parent)
        # self.current_textEdit_parent.show()
        print(self.current_textEdit_parent)
        self.current_textEdit.setParent(self.current_textEdit_parent)
        self.current_textEdit.showNormal()
        self.showNormal()


    def testfs(self):
        self.textEdit.setWindowFlags(QtCore.Qt.Window)
        self.textEdit.setWindowState(QtCore.Qt.WindowFullScreen)
        self.textEdit.show()
    
    def testfsoff(self):
        self.textEdit.setWindowState(QtCore.Qt.WindowNoState)
        self.textEdit.setWindowFlags(QtCore.Qt.Widget)
        self.textEdit.show()


    # def set_fullscreen_te(self):







class Tabs:
    def __init__(self, parent, book_title):
        self.parent_window = parent
        self.book_title = book_title

    def create_tab(self):
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("newtab")
        self.gridLayout = QtWidgets.QGridLayout(self.tab)
        self.gridLayout.setObjectName("gridLayout")
        self.textEdit = QtWidgets.QTextEdit(self.tab)
        self.textEdit.setObjectName("textEdit")
        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)
        self.parent_window.tabWidget.addTab(self.tab, "")
        self.parent_window.tabWidget.setTabText(
            self.parent_window.tabWidget.indexOf(self.tab), self.book_title)
        self.textEdit.setText(','.join(dir(self.parent_window)))

    def close_tab(self, tab_index):
        tab_title = self.parent_window.tabWidget.tabText(tab_index).replace('&', '')
        print(self.parent_window.tabs[tab_title])
        # self.parent_window.tabWidget.removeTab(tab_index)


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = MainUI()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
