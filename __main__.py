#!/usr/bin/env python3

""" TODO
    Define every widget in code because you're going to need to create separate tabs
    Override the keypress event of the textedit
    Goodreads API: Ratings, Read, Recommendations
    Get ISBN using python-isbnlib
    All ebooks should be returned as HTML
    Theming
    Search bar in toolbar
    Drop down for SortBy (library view) / TOC (book view)
    Pagination
    sqlite3 for storing metadata
    sqlite3 for caching files open @ time of exit
    sqlite3 for cover images cache
    Use format* icons for toolbar buttons
    Information dialog widget
    Check file hashes upon restart
    Recursive file addition
    Set context menu for definitions and the like
"""

import os
import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import mainwindow
import database
import parser


class MainUI(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        # Initialize application
        Database(self)
        Settings(self).read_settings()
        Toolbars(self)

        # New tabs and their contents
        self.tabs = {}
        self.current_tab = None
        self.current_textEdit = None

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
        my_file = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open file', self.last_open_path, "eBooks (*.epub *.mobi *.txt)")
        if my_file[0]:
            self.last_open_path = os.path.dirname(my_file[0][0])
            print(self.last_open_path)
            books = parser.BookSorter(my_file[0])
            books.add_to_database()

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

        # The QlistView widget needs to be populated 
        # with a model that inherits from QStandardItemModel
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
            # item = QtGui.QStandardItem(i.split('/')[-1:][0][:-4])
            item = QtGui.QStandardItem()
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
        self.listView.setSpacing(10)

    def closeEvent(self, event):
        Settings(self).save_settings()


class Settings:
    def __init__(self, parent):
        self.parent_window = parent
        self.settings = QtCore.QSettings('Lector', 'Lector')

    def read_settings(self):
        self.settings.beginGroup('mainWindow')
        self.parent_window.resize(self.settings.value(
            'windowSize',
            QtCore.QSize(1299, 748)))
        self.parent_window.move(self.settings.value(
            'windowPosition',
            QtCore.QPoint(286, 141)))
        self.settings.endGroup()

        self.settings.beginGroup('path')
        self.parent_window.last_open_path = self.settings.value(
            'path', os.path.expanduser('~'))
        print(self.parent_window.last_open_path)
        self.settings.endGroup()

    def save_settings(self):
        self.settings.beginGroup('mainWindow')
        self.settings.setValue('windowSize', self.parent_window.size())
        self.settings.setValue('windowPosition', self.parent_window.pos())
        self.settings.endGroup()

        self.settings.beginGroup('lastOpen')
        self.settings.setValue('path', self.parent_window.last_open_path)
        self.settings.endGroup()


class Toolbars:
    # TODO
    # Inheritances so that this self.parent_window.
    # bullshit can be removed
    def __init__(self, parent):
        self.parent_window = parent
        self.parent_window.BookToolBar.hide()
        self.create_toolbars()

    def create_toolbars(self):
         # Book Toolbar
        fullscreenButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('view-fullscreen'), 'Fullscreen', self.parent_window)

        self.parent_window.BookToolBar.addAction(fullscreenButton)
        self.parent_window.BookToolBar.setIconSize(QtCore.QSize(22, 22))

        fullscreenButton.triggered.connect(self.parent_window.set_fullscreen)

        # Library Toolbar
        addButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('add'), 'Add book', self.parent_window)
        deleteButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('remove'), 'Delete book', self.parent_window)
        settingsButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('settings'), 'Settings', self.parent_window)

        addButton.triggered.connect(self.parent_window.open_file)
        settingsButton.triggered.connect(self.parent_window.create_tab_class)
        deleteButton.triggered.connect(self.parent_window.populatelist)

        self.parent_window.LibraryToolBar.addAction(addButton)
        self.parent_window.LibraryToolBar.addAction(deleteButton)
        self.parent_window.LibraryToolBar.addSeparator()
        self.parent_window.LibraryToolBar.addAction(settingsButton)


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
        self.textEdit.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)
        self.parent_window.tabWidget.addTab(self.tab, self.book_title)
        self.textEdit.setText(','.join(dir(self.parent_window)))

    def close_tab(self, tab_index):
        tab_title = self.parent_window.tabWidget.tabText(tab_index).replace('&', '')
        print(self.parent_window.tabs[tab_title])
        self.parent_window.tabWidget.removeTab(tab_index)


class Database:
    # This is maybe, possibly, redundant
    def __init__(self, parent):
        self.parent_window = parent
        self.database_path = QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.AppDataLocation)
        self.db = database.DatabaseFunctions(self.database_path)


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('Lector')  # This is needed for QStandardPaths
                                      # and my own hubris
    form = MainUI()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
