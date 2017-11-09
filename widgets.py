#!usr/bin/env python3

from PyQt5 import QtWidgets, QtGui, QtCore

class BookToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(BookToolBar, self).__init__(parent)

        self.setMovable(False)
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFloatable(False)
        self.setObjectName("LibraryToolBar")

        # Buttons
        self.fullscreenButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('view-fullscreen'), 'Fullscreen', self)
        self.fontButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('gtk-select-font'), 'Format view', self)
        self.settingsButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('settings'), 'Settings', self)

        # Add buttons
        self.addAction(self.fontButton)
        self.addAction(self.fullscreenButton)
        self.addSeparator()
        self.addAction(self.settingsButton)

        # Widget arrangement
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.searchBar = QtWidgets.QLineEdit()
        self.searchBar.setPlaceholderText('Search...')
        self.searchBar.setSizePolicy(sizePolicy)
        self.searchBar.setContentsMargins(10, 0, 0, 0)
        self.searchBar.setMinimumWidth(150)
        self.searchBar.setObjectName('searchBar')

        # Sorter
        sorting_choices = ['Chapter ' + str(i) for i in range(1, 11)]
        self.tocBox = QtWidgets.QComboBox()
        self.tocBox.addItems(sorting_choices)
        self.tocBox.setObjectName('sortingBox')
        self.tocBox.setSizePolicy(sizePolicy)
        self.tocBox.setMinimumContentsLength(10)
        self.tocBox.setToolTip('Table of Contents')

        # Add widgets
        self.addWidget(spacer)
        self.addWidget(self.tocBox)
        self.addWidget(self.searchBar)


class LibraryToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(LibraryToolBar, self).__init__(parent)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.setMovable(False)
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFloatable(False)
        self.setObjectName("LibraryToolBar")

        # Buttons
        self.addButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('add'), 'Add book', self)
        self.deleteButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('remove'), 'Delete book', self)
        self.settingsButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('settings'), 'Settings', self)

        # Add buttons
        self.addAction(self.addButton)
        self.addAction(self.deleteButton)
        self.addSeparator()
        self.addAction(self.settingsButton)

        # Filter
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.filterEdit = QtWidgets.QLineEdit()
        self.filterEdit.setPlaceholderText(
            'Search for Title, Author, Tags...')
        self.filterEdit.setSizePolicy(sizePolicy)
        self.filterEdit.setContentsMargins(10, 0, 0, 0)
        self.filterEdit.setMinimumWidth(150)
        self.filterEdit.setObjectName('filterEdit')

        # Sorter
        sorting_choices = ['Title', 'Author', 'Year']
        self.sortingBox = QtWidgets.QComboBox()
        self.sortingBox.addItems(sorting_choices)
        self.sortingBox.setObjectName('sortingBox')
        self.sortingBox.setSizePolicy(sizePolicy)
        # self.sortingBox.setContentsMargins(30, 0, 0, 0)
        self.sortingBox.setMinimumContentsLength(10)
        self.sortingBox.setToolTip('Sort by')

        # Add widgets
        self.addWidget(spacer)
        self.addWidget(self.sortingBox)
        self.addWidget(self.filterEdit)


class Tab(QtWidgets.QWidget):
    def __init__(self, book_metadata, parent=None):
        # TODO
        # The display widget will probably have to be shifted to something else
        # A horizontal slider to control flow
        # Keyboard shortcuts

        super(Tab, self).__init__(parent)
        self.parent = parent
        self.book_metadata = book_metadata  # Save progress data into this dictionary

        book_title = self.book_metadata['book_title']
        book_path = self.book_metadata['book_path']

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)
        self.parent.addTab(self, book_title)
        self.textEdit.setText(book_path)
