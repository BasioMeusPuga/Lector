#!usr/bin/env python3

# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2018 BasioMeusPuga

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from PyQt5 import QtWidgets, QtGui, QtCore


class BookToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(BookToolBar, self).__init__(parent)

        # Spacer
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setMovable(False)
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFloatable(False)
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setObjectName("LibraryToolBar")

        # Buttons
        self.fontButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('gtk-select-font'),
            'View settings', self)
        self.fullscreenButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('view-fullscreen'),
            'Fullscreen', self)
        self.addBookmarkButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('bookmark-new'),
            'Add bookmark', self)
        self.bookmarkButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('bookmarks'),
            'Bookmarks', self)
        self.bookmarkButton.setObjectName('bookmarkButton')
        self.resetProfile = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('view-refresh'),
            'Reset profile', self)

        # Add buttons
        self.addAction(self.fontButton)
        self.fontButton.setCheckable(True)
        self.fontButton.triggered.connect(self.toggle_font_settings)
        self.addSeparator()
        self.addAction(self.addBookmarkButton)
        self.addAction(self.bookmarkButton)
        self.bookmarkButton.setCheckable(True)
        self.addSeparator()
        self.addAction(self.fullscreenButton)

        # Font modification
        font_sizes = [str(i) for i in range(8, 48, 2)]
        font_sizes.extend(['56', '64', '72'])
        self.fontSizeBox = QtWidgets.QComboBox(self)
        self.fontSizeBox.setObjectName('fontSizeBox')
        self.fontSizeBox.setToolTip('Font size')
        self.fontSizeBox.addItems(font_sizes)
        self.fontSizeBox.setEditable(True)

        self.paddingUp = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-indent-less'),
            'Increase padding', self)
        self.paddingUp.setObjectName('paddingUp')
        self.paddingDown = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-indent-more'),
            'Decrease padding', self)
        self.paddingDown.setObjectName('paddingDown')

        self.lineSpacingUp = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-line-spacing-triple'),
            'Increase line spacing', self)
        self.lineSpacingUp.setObjectName('lineSpacingUp')
        self.lineSpacingDown = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-line-spacing-double'),
            'Decrease line spacing', self)
        self.lineSpacingDown.setObjectName('lineSpacingDown')

        self.alignLeft = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-justify-left'),
            'Left align text', self)
        self.alignLeft.setObjectName('alignLeft')
        self.alignLeft.setCheckable(True)

        self.alignRight = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-justify-right'),
            'Right align text', self)
        self.alignRight.setObjectName('alignRight')
        self.alignRight.setCheckable(True)

        self.alignCenter = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-justify-center'),
            'Center align text', self)
        self.alignCenter.setObjectName('alignCenter')
        self.alignCenter.setCheckable(True)

        self.alignJustify = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-justify-fill'),
            'Justify text', self)
        self.alignJustify.setObjectName('alignJustify')
        self.alignJustify.setCheckable(True)

        self.alignButtons = QtWidgets.QActionGroup(self)
        self.alignButtons.setExclusive(True)
        self.alignButtons.addAction(self.alignLeft)
        self.alignButtons.addAction(self.alignRight)
        self.alignButtons.addAction(self.alignCenter)
        self.alignButtons.addAction(self.alignJustify)

        self.fontBox = QtWidgets.QFontComboBox()
        self.fontBox.setFontFilters(QtWidgets.QFontComboBox.ScalableFonts)
        self.fontBox.setObjectName('fontBox')

        self.colorBoxFG = FixedPushButton(self)
        self.colorBoxFG.setObjectName('fgColor')
        self.colorBoxFG.setToolTip('Text color')
        self.colorBoxBG = FixedPushButton(self)
        self.colorBoxBG.setToolTip('Background color')
        self.colorBoxBG.setObjectName('bgColor')

        profiles = ['Profile 1', 'Profile 2', 'Profile 3']
        self.profileBox = QtWidgets.QComboBox(self)
        self.profileBox.addItems(profiles)

        self.profileAction = self.addWidget(self.profileBox)
        self.fontSeparator1 = self.addSeparator()
        self.fontBoxAction = self.addWidget(self.fontBox)
        self.fontSizeBoxAction = self.addWidget(self.fontSizeBox)
        self.fontSeparator2 = self.addSeparator()
        self.fgColorAction = self.addWidget(self.colorBoxFG)
        self.bgColorAction = self.addWidget(self.colorBoxBG)
        self.fontSeparator3 = self.addSeparator()
        self.addAction(self.lineSpacingUp)
        self.addAction(self.lineSpacingDown)
        self.fontSeparator4 = self.addSeparator()
        self.addAction(self.paddingUp)
        self.addAction(self.paddingDown)
        self.fontSeparator4 = self.addSeparator()
        self.addAction(self.alignLeft)
        self.addAction(self.alignRight)
        self.addAction(self.alignCenter)
        self.addAction(self.alignJustify)

        self.fontActions = [
            self.fontBoxAction,
            self.fontSizeBoxAction,
            self.fgColorAction,
            self.bgColorAction,
            self.lineSpacingUp,
            self.lineSpacingDown,
            self.paddingUp,
            self.paddingDown,
            self.alignLeft,
            self.alignRight,
            self.alignCenter,
            self.alignJustify,
            self.profileAction,
            self.fontSeparator1,
            self.fontSeparator2,
            self.fontSeparator3,
            self.fontSeparator4,
            self.resetProfile]

        for i in self.fontActions:
            i.setVisible(False)

        # Comic view modification
        self.zoomIn = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('zoom-in'),
            'Zoom in', self)
        self.zoomIn.setObjectName('zoomIn')
        self.zoomOut = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('zoom-out'),
            'Zoom Out', self)
        self.zoomOut.setObjectName('zoomOut')

        self.fitWidth = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('zoom-fit-width'),
            'Fit Width', self)
        self.fitWidth.setObjectName('fitWidth')
        self.fitWidth.setCheckable(True)
        self.bestFit = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('zoom-fit-best'),
            'Best Fit', self)
        self.bestFit.setObjectName('bestFit')
        self.bestFit.setCheckable(True)
        self.originalSize = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('zoom-original'),
            'Original size', self)
        self.originalSize.setObjectName('originalSize')
        self.originalSize.setCheckable(True)

        self.comicBGColor = FixedPushButton(self)
        self.comicBGColor.setToolTip('Background color')
        self.comicBGColor.setObjectName('comicBGColor')

        self.comicSeparator1 = self.addSeparator()
        self.addAction(self.zoomIn)
        self.addAction(self.zoomOut)
        self.addAction(self.fitWidth)
        self.addAction(self.bestFit)
        self.addAction(self.originalSize)
        self.comicSeparator2 = self.addSeparator()
        self.comicBGColorAction = self.addWidget(self.comicBGColor)

        self.comicActions = [
            self.comicBGColorAction,
            self.zoomIn,
            self.zoomOut,
            self.fitWidth,
            self.bestFit,
            self.originalSize,
            self.comicSeparator1,
            self.comicSeparator2]

        for i in self.comicActions:
            i.setVisible(False)

        # Other booktoolbar widgets
        self.searchBar = FixedLineEdit(self)
        self.searchBar.setPlaceholderText(
            'Search...')
        self.searchBar.setSizePolicy(sizePolicy)
        self.searchBar.setContentsMargins(10, 0, 0, 0)
        self.searchBar.setObjectName('searchBar')

        # Sorter
        self.tocBox = FixedComboBox(self)
        self.tocBox.setObjectName('sortingBox')
        self.tocBox.setToolTip('Table of Contents')

        # All of these will be put after the spacer
        # This means that the buttons in the left side of
        # the toolbar have to split up and added here
        self.boxSpacer = self.addWidget(spacer)

        self.tocBoxAction = self.addWidget(self.tocBox)
        self.searchBarAction = self.addWidget(self.searchBar)

        self.bookActions = [
            self.addBookmarkButton,
            self.bookmarkButton,
            self.fullscreenButton,
            self.tocBoxAction,
            self.searchBarAction]

        for i in self.bookActions:
            i.setVisible(True)

        self.addAction(self.resetProfile)

    def toggle_font_settings(self):
        if self.fontButton.isChecked():
            self.customize_view_on()
        else:
            self.customize_view_off()

    def customize_view_on(self):
        if self.parent().tabWidget.widget(
                self.parent().tabWidget.currentIndex()).metadata['images_only']:

            # The following might seem redundant,
            # but it's necessary for tab switching

            for i in self.comicActions:
                i.setVisible(True)

            for i in self.fontActions:
                i.setVisible(False)
        else:
            for i in self.fontActions:
                i.setVisible(True)

            for i in self.comicActions:
                i.setVisible(False)

        for i in self.bookActions:
            i.setVisible(False)

    def customize_view_off(self):
        for i in self.fontActions:
            i.setVisible(False)

        for i in self.comicActions:
            i.setVisible(False)

        for i in self.bookActions:
            i.setVisible(True)


class LibraryToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(LibraryToolBar, self).__init__(parent)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.setMovable(False)
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFloatable(False)
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setObjectName("LibraryToolBar")

        # Buttons
        self.addButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('add'), 'Add book', self)
        self.deleteButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('remove'), 'Delete book', self)
        self.colorButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('color-picker'), 'Library background color', self)
        self.colorButton.setObjectName('libraryBackground')
        self.settingsButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('settings'), 'Settings', self)
        self.settingsButton.setCheckable(True)

        self.coverViewButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('view-grid'), 'View as covers', self)
        self.coverViewButton.setCheckable(True)
        self.tableViewButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('table'), 'View as table', self)
        self.tableViewButton.setCheckable(True)

        self.libraryFilterButton = QtWidgets.QToolButton(self)
        self.libraryFilterButton.setIcon(QtGui.QIcon.fromTheme('view-readermode'))
        self.libraryFilterButton.setText('Filter library')
        self.libraryFilterButton.setToolTip('Filter library')

        # Auto unchecks the other QToolButton in case of clicking
        self.viewButtons = QtWidgets.QActionGroup(self)
        self.viewButtons.setExclusive(True)
        self.viewButtons.addAction(self.coverViewButton)
        self.viewButtons.addAction(self.tableViewButton)

        # Add buttons
        self.addAction(self.addButton)
        self.addAction(self.deleteButton)
        self.addSeparator()
        self.addAction(self.coverViewButton)
        self.addAction(self.tableViewButton)
        self.addSeparator()
        self.addWidget(self.libraryFilterButton)
        self.addSeparator()
        self.addAction(self.colorButton)
        self.addAction(self.settingsButton)

        # Filter
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.searchBar = FixedLineEdit(self)
        self.searchBar.setClearButtonEnabled(True)
        self.searchBar.setPlaceholderText(
            'Search for Title, Author, Tags...')
        self.searchBar.setSizePolicy(sizePolicy)
        self.searchBar.setContentsMargins(10, 0, 0, 0)
        self.searchBar.setObjectName('searchBar')

        # Sorter
        sorting_choices = ['Title', 'Author', 'Year', 'Newest', 'Last read']
        self.sortingBox = FixedComboBox(self)
        self.sortingBox.addItems(sorting_choices)
        self.sortingBox.setObjectName('sortingBox')
        self.sortingBox.setSizePolicy(sizePolicy)
        self.sortingBox.setMinimumContentsLength(10)
        self.sortingBox.setToolTip('Sort by')

        # Add widgets
        self.addWidget(spacer)
        self.sortingBoxAction = self.addWidget(self.sortingBox)
        self.addWidget(self.searchBar)


# Sublassing these widgets out prevents them from resizing
class FixedComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(FixedComboBox, self).__init__(parent)

    def sizeHint(self):
        return QtCore.QSize(400, 22)


class FixedLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(FixedLineEdit, self).__init__(parent)

    def sizeHint(self):
        return QtCore.QSize(400, 22)


class FixedPushButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(FixedPushButton, self).__init__(parent)

    def sizeHint(self):
        return QtCore.QSize(36, 30)
