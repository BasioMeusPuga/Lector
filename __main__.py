#!/usr/bin/env python3

""" TODO
    ✓ sqlite3 for cover images cache
    ✓ sqlite3 for storing metadata
    ✓ Drop down for SortBy (library view)
    ✓ Define every widget in code because you're going to need to create separate tabs
    ✓ Override the keypress event of the textedit
    ✓ Search bar in toolbar
    
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

import mainwindow
import database
import book_parser


class MainUI(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    #pylint: disable-msg=E1101
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        # Initialize application
        Settings(self).read_settings()  # This should populate all variables that need
                                        # to be remembered across sessions
        Toolbars(self)
        # This is an ugly hack?
        # I can't seem to access the Qcombobox the usual way
        self.librarySortingBox = self.LibraryToolBar.findChild(QtWidgets.QComboBox)
        self.libraryFilterEdit = self.LibraryToolBar.findChild(QtWidgets.QLineEdit)

        database.DatabaseInit(self.database_path)

        self.lib_ref = Library(self)
        self.viewModel = None

        # Right align everything in the statusbar
        self.statusMessage = QtWidgets.QLabel()
        self.statusMessage.setObjectName('statusMessage')
        self.statusBar.addPermanentWidget(self.statusMessage)

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

    def add_books(self):
        # TODO
        # Maybe expand this to traverse directories recursively
        self.statusMessage.setText('Adding books...')
        my_file = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open file', self.last_open_path, "eBooks (*.epub *.mobi *.txt)")
        if my_file[0]:
            self.listView.setEnabled(False)
            self.last_open_path = os.path.dirname(my_file[0][0])
            books = book_parser.BookSorter(my_file[0])
            parsed_books = books.initiate_threads()
            database.DatabaseFunctions(self.database_path).add_to_database(parsed_books)
            self.listView.setEnabled(True)
            self.viewModel = None
        self.reload_listview()

    def delete_books(self):
        selected_books = self.listView.selectedIndexes()
        if selected_books:
            def ifcontinue(box_button):
                if box_button.text() == '&Yes':
                    selected_hashes = []
                    for i in selected_books:
                        book_data = i.data(QtCore.Qt.UserRole + 3)
                        selected_hashes.append(book_data['book_hash'])
                    database.DatabaseFunctions(
                        self.database_path).delete_from_database(selected_hashes)
                    self.viewModel = None
                    self.reload_listview()

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
        if not self.viewModel:
            self.lib_ref.generate_model()
        self.lib_ref.update_listView()

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

    def generate_model(self):
        # TODO
        # Use QItemdelegates to show book read progress
        # The QlistView widget needs to be populated
        # with a model that inherits from QStandardItemModel

        self.parent_window.viewModel = QtGui.QStandardItemModel()
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
        # sortingbox_index = self.parent_window.librarySortingBox.currentIndex()
        # books = sorted(books, key=lambda x: x[sortingbox_index + 1])

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

            # This remarkably ugly hack is because the QSortFilterProxyModel
            # doesn't easily allow searching through multiple item roles
            search_workaround = book_title + ' ' + book_author
            if book_tags:
                search_workaround += book_tags

            # Generate image pixmap and then pass it to the widget
            # as a QIcon
            # Additional data can be set using an incrementing
            # QtCore.Qt.UserRole
            # QtCore.Qt.DisplayRole is the same as item.setText()
            # The model is a single row and has no columns
            img_pixmap = QtGui.QPixmap()
            img_pixmap.loadFromData(book_cover)
            img_pixmap = img_pixmap.scaled(410, 600, QtCore.Qt.IgnoreAspectRatio)
            item = QtGui.QStandardItem()
            item.setToolTip(tooltip_string)
            item.setData(book_title, QtCore.Qt.UserRole)
            item.setData(book_author, QtCore.Qt.UserRole + 1)
            item.setData(book_year, QtCore.Qt.UserRole + 2)
            item.setData(additional_data, QtCore.Qt.UserRole + 3)
            item.setData(search_workaround, QtCore.Qt.UserRole + 4)
            item.setIcon(QtGui.QIcon(img_pixmap))
            self.parent_window.viewModel.appendRow(item)

    def update_listView(self):
        proxy_model = QtCore.QSortFilterProxyModel()
        proxy_model.setSourceModel(self.parent_window.viewModel)
        proxy_model.setFilterRole(QtCore.Qt.UserRole + 4)
        proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        proxy_model.setFilterWildcard(self.parent_window.libraryFilterEdit.text())

        self.parent_window.statusMessage.setText(
            str(proxy_model.rowCount()) + ' books')

        # Sorting according to roles and the drop down in the library
        proxy_model.setSortRole(
            QtCore.Qt.UserRole + self.parent_window.librarySortingBox.currentIndex())
        proxy_model.sort(0)

        s = QtCore.QSize(250, 250)  # Set icon sizing here
        self.parent_window.listView.setIconSize(s)
        self.parent_window.listView.setModel(proxy_model)


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

        addButton.triggered.connect(self.parent_window.add_books)
        settingsButton.triggered.connect(self.parent_window.create_tab_class)
        deleteButton.triggered.connect(self.parent_window.delete_books)

        # Filter
        filterEdit = QtWidgets.QLineEdit()
        filterEdit.setPlaceholderText('Search for Title, Author, Tags...')
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        filterEdit.setSizePolicy(sizePolicy)
        filterEdit.setContentsMargins(200, 0, 200, 0)
        filterEdit.setMinimumWidth(150)
        filterEdit.textChanged.connect(self.parent_window.reload_listview)

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

        # Add widgets to toolbar
        self.parent_window.LibraryToolBar.addAction(addButton)
        self.parent_window.LibraryToolBar.addAction(deleteButton)
        self.parent_window.LibraryToolBar.addSeparator()
        self.parent_window.LibraryToolBar.addAction(settingsButton)
        self.parent_window.LibraryToolBar.addWidget(spacer)
        self.parent_window.LibraryToolBar.addWidget(filterEdit)
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
