#!/usr/bin/env python3

""" TODO
    ✓ sqlite3 for cover images cache
    ✓ sqlite3 for storing metadata
    ✓ Drop down for SortBy (library view)
    ✓ Define every widget in code because you're going to need to create separate tabs
    ✓ Override the keypress event of the textedit

    Goodreads API: Ratings, Read, Recommendations
    Get ISBN using python-isbnlib
    All ebooks should be returned as HTML
    Theming
    Search bar in toolbar
    Drop down for TOC (book view)
    Pagination
    sqlite3 for caching files open @ time of exit
    Use format* icons for toolbar buttons
    Information dialog widget
    Check file hashes upon restart
    Recursive file addition
    Set context menu for definitions and the like
"""

import os
import sys

from PyQt5 import QtWidgets, QtGui, QtCore

import book_parser
import mainwindow
import database


class MainUI(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        # Initialize application
        Settings(self).read_settings()  # This should populate all variables that need
                                        # to be remembered across sessions
        Toolbars(self)
        # This is an ugly ugly hack
        # I can't seem to access the Qcombobox the usual way
        self.librarySortingBox = self.LibraryToolBar.children()[-1:][0]

        database.DatabaseInit(self.database_path)

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

        # ListView
        self.listView.setSpacing(15)
        self.reload_listview()
        self.listView.doubleClicked.connect(self.listclick)

        # Keyboard shortcuts
        self.exit_all = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.exit_all.activated.connect(QtWidgets.qApp.exit)

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
            books = book_parser.BookSorter(my_file[0])
            parsed_books = books.initiate_threads()
            database.DatabaseFunctions(self.database_path).add_to_database(parsed_books)
            self.reload_listview()

    def delete_books(self):
        selected_books = self.listView.selectedIndexes()
        if selected_books:
            def ifcontinue(box_button):
                if box_button.text() == '&Yes':
                    selected_hashes = []
                    for i in selected_books:
                        book_row = i.row()
                        book_data = i.data(QtCore.Qt.UserRole)
                        selected_hashes.append(book_data['book_hash'])
                        self.listView.model().removeRow(book_row)
                    database.DatabaseFunctions(
                        self.database_path).delete_from_database(selected_hashes)

            selected_number = len(selected_books)
            msg_box = QtWidgets.QMessageBox()
            msg_box.setText(f'Delete {selected_number} book(s)?')
            msg_box.setIcon(QtWidgets.QMessageBox.Question)
            msg_box.setWindowTitle('Confirm deletion')
            msg_box.setStandardButtons(
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg_box.buttonClicked.connect(ifcontinue)
            msg_box.show()
            msg_box.exec_()

    def reload_listview(self):
        lib_ref = Library(self)
        lib_ref.load_listView()

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

    def listclick(self, myindex):
        index = self.listView.model().index(myindex.row(), 0)
        print(self.listView.model().data(index, QtCore.Qt.UserRole))

    def closeEvent(self, event):
        Settings(self).save_settings()


class Library:
    def __init__(self, parent):
        self.parent_window = parent

    def load_listView(self):
        # TODO
        # The rest of it is just refreshing the listview

        # The QlistView widget needs to be populated
        # with a model that inherits from QStandardItemModel
        model = QtGui.QStandardItemModel()

        books = database.DatabaseFunctions(
            self.parent_window.database_path).fetch_data(
                ('*',),
                'books',
                {'Title': ''},
                'LIKE')

        if not books:
            print('Database returned nothing')
            return

        # The sorting indices are related to the indices of what the library returns
        # by -1. Consider making this something more foolproof. Maybe.
        sortingbox_index = self.parent_window.librarySortingBox.currentIndex()
        books = sorted(books, key=lambda x: x[sortingbox_index + 1])

        for i in books:

            # The database query returns a tuple with the following indices
            # Index 0 is the key ID is ignored
            book_title = i[1]
            book_author = i[2]
            book_year = i[3]
            book_cover = i[8]
            book_tags = i[6]
            additional_data = {
                'book_title': i[1],
                'book_path': i[4],
                'book_isbn': i[5],
                'book_hash': i[7]}

            tooltip_string = book_title + '\nAuthor: ' + book_author + '\nYear: ' + str(book_year)
            if book_tags:
                tooltip_string += ('\nTags: ' + book_tags)
            # Generate image pixmap and then pass it to the widget
            # as a QIcon
            # Additional data can be set using an incrementing
            # QtCore.Qt.UserRole
            # QtCore.Qt.DisplayRole is the same as item.setText()
            # The model is a single row and has no columns
            img_pixmap = QtGui.QPixmap()
            img_pixmap.loadFromData(book_cover)
            item = QtGui.QStandardItem()
            item.setToolTip(tooltip_string)
            item.setData(additional_data, QtCore.Qt.UserRole)
            item.setIcon(QtGui.QIcon(img_pixmap))
            model.appendRow(item)

        s = QtCore.QSize(200, 200)  # Set icon sizing here
        self.parent_window.listView.setIconSize(s)
        self.parent_window.listView.setModel(model)


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

        self.settings.beginGroup('runtimeVariables')
        self.parent_window.last_open_path = self.settings.value(
            'lastOpenPath', os.path.expanduser('~'))
        self.parent_window.database_path = self.settings.value(
            'databasePath',
            QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppDataLocation))
        self.settings.endGroup()

    def save_settings(self):
        self.settings.beginGroup('mainWindow')
        self.settings.setValue('windowSize', self.parent_window.size())
        self.settings.setValue('windowPosition', self.parent_window.pos())
        self.settings.endGroup()

        self.settings.beginGroup('runtimeVariables')
        self.settings.setValue('lastOpenPath', self.parent_window.last_open_path)
        self.settings.setValue('databasePath', self.parent_window.database_path)
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
        deleteButton.triggered.connect(self.parent_window.delete_books)

        # Sorter
        sorting_choices = ['Title', 'Author', 'Year']
        sortingBox = QtWidgets.QComboBox()
        sortingBox.addItems(sorting_choices)
        sortingBox.setObjectName('sortingBox')
        sortingBox.setToolTip('Sort by')
        sortingBox.activated.connect(self.parent_window.reload_listview)

        # Spacer
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.parent_window.LibraryToolBar.addAction(addButton)
        self.parent_window.LibraryToolBar.addAction(deleteButton)
        self.parent_window.LibraryToolBar.addSeparator()
        self.parent_window.LibraryToolBar.addAction(settingsButton)
        self.parent_window.LibraryToolBar.addWidget(spacer)
        self.parent_window.LibraryToolBar.addWidget(sortingBox)


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


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('Lector')  # This is needed for QStandardPaths
                                      # and my own hubris
    form = MainUI()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
