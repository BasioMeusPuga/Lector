#!usr/bin/env python3

from PyQt5 import QtWidgets, QtGui, QtCore

class BookToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(BookToolBar, self).__init__(parent)

        # Spacer
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Size policy
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.setMovable(False)
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFloatable(False)
        self.setObjectName("LibraryToolBar")

        # Buttons
        self.fullscreenButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('view-fullscreen'), 'Fullscreen', self)
        self.fontButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('gtk-select-font'), 'Font settings', self)
        self.settingsButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('settings'), 'Settings', self)

        # Add buttons
        self.addAction(self.fontButton)
        self.fontButton.setCheckable(True)
        self.fontButton.triggered.connect(self.toggle_font_settings)
        self.addSeparator()
        self.addAction(self.fullscreenButton)
        self.addAction(self.settingsButton)

        # Font modification buttons
        # All hidden by default
        self.fontSizeUp = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-font-size-more'),
            'Increase font size', self)
        self.fontSizeDown = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-font-size-less'),
            'Decrease font size', self)

        self.marginsUp = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-justify-fill'),
            'Increase margins', self)
        self.marginsDown = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-indent-less'),
            'Decrease margins', self)

        self.lineSpacingUp = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-line-spacing-triple'),
            'Increase line spacing', self)
        self.lineSpacingDown = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-line-spacing-double'),
            'Decrease line spacing', self)

        self.fontBox = QtWidgets.QFontComboBox()
        self.colorBoxFG = QtWidgets.QPushButton()
        self.colorBoxBG = QtWidgets.QPushButton()

        self.fontBoxAction = self.addWidget(self.fontBox)
        self.addAction(self.fontSizeUp)
        self.addAction(self.fontSizeDown)
        self.fontSeparator1 = self.addSeparator()
        self.fgColorAction = self.addWidget(self.colorBoxFG)
        self.bgColorAction = self.addWidget(self.colorBoxBG)
        self.fontSeparator2 = self.addSeparator()
        self.addAction(self.lineSpacingUp)
        self.addAction(self.lineSpacingDown)
        self.fontSeparator3 = self.addSeparator()
        self.addAction(self.marginsUp)
        self.addAction(self.marginsDown)

        self.fontBoxAction.setVisible(False)
        self.fontSizeUp.setVisible(False)
        self.fontSizeDown.setVisible(False)
        self.fgColorAction.setVisible(False)
        self.bgColorAction.setVisible(False)
        self.lineSpacingUp.setVisible(False)
        self.lineSpacingDown.setVisible(False)
        self.marginsUp.setVisible(False)
        self.marginsDown.setVisible(False)
        self.fontSeparator1.setVisible(False)
        self.fontSeparator2.setVisible(False)
        self.fontSeparator3.setVisible(False)

        self.searchBar = QtWidgets.QLineEdit()
        self.searchBar.setPlaceholderText('Search...')
        self.searchBar.setSizePolicy(sizePolicy)
        self.searchBar.setContentsMargins(10, 0, 0, 0)
        self.searchBar.setMinimumWidth(150)
        self.searchBar.setObjectName('searchBar')

        # Sorter
        self.tocBox = QtWidgets.QComboBox()
        self.tocBox.setObjectName('sortingBox')
        self.tocBox.setSizePolicy(sizePolicy)
        self.tocBox.setMinimumContentsLength(10)
        self.tocBox.setToolTip('Table of Contents')

        # All of these will be put after the spacer
        # This means that the buttons in the left side of
        # the toolbar have to split up and added here
        self.boxSpacer = self.addWidget(spacer)

        self.tocBoxAction = self.addWidget(self.tocBox)
        self.searchBarAction = self.addWidget(self.searchBar)

    def toggle_font_settings(self):
        if self.fontButton.isChecked():
            self.font_settings_on()
        else:
            self.font_settings_off()

    def font_settings_on(self):
        self.fullscreenButton.setVisible(False)
        self.settingsButton.setVisible(False)

        self.fontBoxAction.setVisible(True)
        self.fontSizeUp.setVisible(True)
        self.fontSizeDown.setVisible(True)
        self.fgColorAction.setVisible(True)
        self.bgColorAction.setVisible(True)
        self.lineSpacingUp.setVisible(True)
        self.lineSpacingDown.setVisible(True)
        self.marginsUp.setVisible(True)
        self.marginsDown.setVisible(True)
        self.fontSeparator1.setVisible(True)
        self.fontSeparator2.setVisible(True)
        self.fontSeparator3.setVisible(True)

        self.tocBoxAction.setVisible(False)
        self.searchBarAction.setVisible(False)

    def font_settings_off(self):
        self.fullscreenButton.setVisible(True)
        self.settingsButton.setVisible(True)

        self.fontBoxAction.setVisible(False)
        self.fontSizeUp.setVisible(False)
        self.fontSizeDown.setVisible(False)
        self.fgColorAction.setVisible(False)
        self.bgColorAction.setVisible(False)
        self.lineSpacingUp.setVisible(False)
        self.lineSpacingDown.setVisible(False)
        self.marginsUp.setVisible(False)
        self.marginsDown.setVisible(False)
        self.fontSeparator1.setVisible(False)
        self.fontSeparator2.setVisible(False)
        self.fontSeparator3.setVisible(False)

        self.tocBoxAction.setVisible(True)
        self.searchBarAction.setVisible(True)


class LibraryToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(LibraryToolBar, self).__init__(parent)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

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
    def __init__(self, metadata, parent=None):
        # TODO
        # A horizontal slider to control flow
        # Keyboard shortcuts

        # The content display widget is currently a QTextBrowser
        super(Tab, self).__init__(parent)
        self.parent = parent
        self.metadata = metadata  # Save progress data into this dictionary
        self.setStyleSheet("background-color: black")

        title = self.metadata['title']
        path = self.metadata['path']

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.contentView = QtWidgets.QTextBrowser(self)
        self.contentView.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.contentView.setObjectName("contentView")
        self.contentView.verticalScrollBar().setSingleStep(7)
        self.contentView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.gridLayout.addWidget(self.contentView, 0, 0, 1, 1)
        self.parent.addTab(self, title)
        self.contentView.setStyleSheet(
            "QTextEdit {font-size:20px; padding-left:100; padding-right:100; background-color:black}")


class LibraryDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(LibraryDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
        option = option.__class__(option)
        state = index.data(QtCore.Qt.UserRole + 5)
        if state:
            if state == 'deleted':
                read_icon = QtGui.QIcon.fromTheme('vcs-conflicting').pixmap(36)
            if state == 'completed':
                read_icon = QtGui.QIcon.fromTheme('vcs-normal').pixmap(36)
            if state == 'inprogress':
                read_icon = QtGui.QIcon.fromTheme('vcs-locally-modified').pixmap(36)
        else:
            return

        x_draw = option.rect.bottomRight().x() - 30
        y_draw = option.rect.bottomRight().y() - 35
        painter.drawPixmap(x_draw, y_draw, read_icon)
