#!/usr/bin/env python3

""" TODO
    Define every widget in code because you're going to need to create separate tabs
    Override the keypress event of the textedit
    Goodreads API: Ratings, Read, Recommendations
    Get ISBN using python-isbnlib
    All ebooks should be returned as HTML
    Theming
    Search bar in toolbar
    Pagination
    sqlite3 for storing metadata
    sqlite3 for caching files open @ time of exit
    sqlite3 for cover images cache
    Information dialog widget
    Check file hashes upon restart
    Drop down for TOC
    Recursive file addition
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

        # Book Toolbar
        self.BookToolBar.hide()
        fullscreenButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('view-fullscreen'), 'Fullscreen', self)
        self.BookToolBar.addAction(fullscreenButton)
        fullscreenButton.triggered.connect(self.set_fullscreen)

        # Library Toolbar
        addButton = QtWidgets.QAction(QtGui.QIcon.fromTheme('add'), 'Add book', self)
        deleteButton = QtWidgets.QAction(QtGui.QIcon.fromTheme('remove'), 'Delete book', self)
        settingsButton = QtWidgets.QAction(QtGui.QIcon.fromTheme('settings'), 'Settings', self)
        addButton.triggered.connect(self.open_file)
        settingsButton.triggered.connect(self.create_tab_class)
        deleteButton.triggered.connect(self.populatelist)

        self.LibraryToolBar.addAction(addButton)
        self.LibraryToolBar.addAction(deleteButton)
        self.LibraryToolBar.addSeparator()
        self.LibraryToolBar.addAction(settingsButton)

        # Toolbar switching
        self.tabWidget.currentChanged.connect(self.toolbar_switch)

        # Tab closing
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabBar().setTabButton(0, QtWidgets.QTabBar.RightSide, None)
        self.tabWidget.tabCloseRequested.connect(self.close_tab_class)

        self.listView.doubleClicked.connect(self.listclick)

    def create_tab_class(self):
        # TODO
        # Shift focus to tab if it's already open instead of creating
        # a new one
        self.tabs['TitleText'] = {
            'information about': 'This tab'}
        this_tab = Tabs(self, 'TitleText')
        this_tab.create_tab()

    def open_file(self):
        # TODO
        # Maybe expand this to traverse directories recursively
        home_dir = os.path.expanduser('~')
        my_file = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open file', home_dir, "eBooks (*.epub *.mobi *.txt)")
        print(my_file[0])

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

        self.exit_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence('Escape'), self.current_textEdit)
        self.exit_shortcut.activated.connect(self.set_normalsize)

        self.current_textEdit.setWindowFlags(QtCore.Qt.Window)
        self.current_textEdit.setWindowState(QtCore.Qt.WindowFullScreen)
        self.hide()
        self.current_textEdit.show()

    def set_normalsize(self):
        self.current_textEdit.setWindowState(QtCore.Qt.WindowNoState)
        self.current_textEdit.setWindowFlags(QtCore.Qt.Widget)
        self.show()
        self.current_textEdit.show()

    def populatelist(self):
        self.listView.setWindowTitle('huh')

        # The QlistView widget needs to be populated with a model that
        # inherits from QStandardItemModel
        model = QtGui.QStandardItemModel()

        # Get the list of images from here
        # Temp dir this out after getting the images from the
        # database
        my_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'thumbnails')
        image_list = [os.path.join(my_dir, i) for i in os.listdir('./thumbnails')]

        # Generate image pixmap and then pass it to the widget
        # as a QIcon
        # Additional data can be set using an incrementing
        # QtCore.Qt.UserRole
        # QtCore.Qt.DisplayRole is the same as item.setText()
        # The model is a single row and has no columns
        for i in image_list:
            img_pixmap = QtGui.QPixmap(i)
            item = QtGui.QStandardItem(i.split('/')[-1:][0])
            item.setData('Additional data for ' + i.split('/')[-1:][0], QtCore.Qt.UserRole)
            item.setIcon(QtGui.QIcon(img_pixmap))
            model.appendRow(item)
        s = QtCore.QSize(200, 200)  # Set icon sizing here
        self.listView.setIconSize(s)
        self.listView.setModel(model)

    def listclick(self, myindex):
        # print('selected item index found at %s with data: %s' % (myindex.row(), myindex.data()))
        index = self.listView.model().index(myindex.row(), 0)
        print(self.listView.model().data(index, QtCore.Qt.UserRole))


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
        self.parent_window.tabWidget.addTab(self.tab, self.book_title)
        self.textEdit.setText(','.join(dir(self.parent_window)))

    def close_tab(self, tab_index):
        tab_title = self.parent_window.tabWidget.tabText(tab_index).replace('&', '')
        print(self.parent_window.tabs[tab_title])
        self.parent_window.tabWidget.removeTab(tab_index)


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = MainUI()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
