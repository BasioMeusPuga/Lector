# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017-2019 BasioMeusPuga

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

import logging

from PyQt5 import QtWidgets, QtCore

logger = logging.getLogger(__name__)


class BookToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(BookToolBar, self).__init__(parent)
        self._translate = QtCore.QCoreApplication.translate

        # Spacer
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.setMovable(False)
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFloatable(False)
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setObjectName('LibraryToolBar')

        image_factory = self.window().QImageFactory

        # Buttons
        self.fontButton = QtWidgets.QAction(
            image_factory.get_image('gtk-select-font'),
            self._translate('BookToolBar', 'View settings'),
            self)
        self.annotationButton = QtWidgets.QAction(
            image_factory.get_image('annotate'),
            self._translate('BookToolBar', 'Annotations (Ctrl + N)'),
            self)
        self.addBookmarkButton = QtWidgets.QAction(
            image_factory.get_image('bookmark-new'),
            self._translate('BookToolBar', 'Add bookmark'),
            self)
        self.bookmarkButton = QtWidgets.QAction(
            image_factory.get_image('bookmarks'),
            self._translate('BookToolBar', 'Bookmarks (Ctrl + B)'),
            self)
        self.searchButton = QtWidgets.QAction(
            image_factory.get_image('search'),
            self._translate('BookToolBar', 'Search (Ctrl + F)'),
            self)
        self.distractionFreeButton = QtWidgets.QAction(
            image_factory.get_image('visibility'),
            self._translate('Main_BookToolBarUI', 'Toggle distraction free mode (Ctrl + D)'),
            self)
        self.fullscreenButton = QtWidgets.QAction(
            image_factory.get_image('view-fullscreen'),
            self._translate('BookToolBar', 'Fullscreen (F)'),
            self)
        self.resetProfile = QtWidgets.QAction(
            image_factory.get_image('reload'),
            self._translate('BookToolBar', 'Reset profile'),
            self)

        # Add buttons
        self.addAction(self.fontButton)
        self.fontButton.setCheckable(True)
        self.fontButton.triggered.connect(self.toggle_font_settings)
        self.bookSeparator1 = self.addSeparator()
        self.addAction(self.addBookmarkButton)
        self.addAction(self.bookmarkButton)
        self.bookSeparator2 = self.addSeparator()
        self.addAction(self.annotationButton)
        self.bookSeparator3 = self.addSeparator()
        self.addAction(self.searchButton)
        self.bookSeparator4 = self.addSeparator()
        self.addAction(self.distractionFreeButton)
        self.addAction(self.fullscreenButton)

        # Font modification
        font_sizes = [str(i) for i in range(8, 48, 2)]
        font_sizes.extend(['56', '64', '72'])
        self.fontSizeBox = QtWidgets.QComboBox(self)
        self.fontSizeBox.setObjectName('fontSizeBox')
        self.fontSizeBox.setToolTip(self._translate('BookToolBar', 'Font size'))
        self.fontSizeBox.addItems(font_sizes)
        self.fontSizeBox.setEditable(True)

        self.paddingUp = QtWidgets.QAction(
            image_factory.get_image('format-indent-less'),
            self._translate('BookToolBar', 'Increase padding'),
            self)
        self.paddingUp.setObjectName('paddingUp')
        self.paddingDown = QtWidgets.QAction(
            image_factory.get_image('format-indent-more'),
            self._translate('BookToolBar', 'Decrease padding'),
            self)
        self.paddingDown.setObjectName('paddingDown')

        self.lineSpacingUp = QtWidgets.QAction(
            image_factory.get_image('format-line-spacing-triple'),
            self._translate('BookToolBar', 'Increase line spacing'),
            self)
        self.lineSpacingUp.setObjectName('lineSpacingUp')
        self.lineSpacingDown = QtWidgets.QAction(
            image_factory.get_image('format-line-spacing-double'),
            self._translate('BookToolBar', 'Decrease line spacing'),
            self)
        self.lineSpacingDown.setObjectName('lineSpacingDown')

        self.alignLeft = QtWidgets.QAction(
            image_factory.get_image('format-justify-left'),
            self._translate('BookToolBar', 'Left align text'),
            self)
        self.alignLeft.setObjectName('alignLeft')
        self.alignLeft.setCheckable(True)

        self.alignRight = QtWidgets.QAction(
            image_factory.get_image('format-justify-right'),
            self._translate('BookToolBar', 'Right align text'),
            self)
        self.alignRight.setObjectName('alignRight')
        self.alignRight.setCheckable(True)

        self.alignCenter = QtWidgets.QAction(
            image_factory.get_image('format-justify-center'),
            self._translate('BookToolBar', 'Center align text'),
            self)
        self.alignCenter.setObjectName('alignCenter')
        self.alignCenter.setCheckable(True)

        self.alignJustify = QtWidgets.QAction(
            image_factory.get_image('format-justify-fill'),
            self._translate('BookToolBar', 'Justify text'),
            self)
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
        self.colorBoxBG.setToolTip(self._translate('BookToolBar', 'Background color'))
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
        self.fontSeparator5 = self.addSeparator()
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
            self.fontSeparator5,
            self.resetProfile]

        for i in self.fontActions:
            i.setVisible(False)

        # Comic view modification
        self.doublePageButton = QtWidgets.QAction(
            image_factory.get_image('page-double'),
            self._translate('BookToolBar', 'Double page mode (D)'),
            self)
        self.doublePageButton.setObjectName('doublePageButton')            
        self.doublePageButton.setCheckable(True)

        self.mangaModeButton = QtWidgets.QAction(
            image_factory.get_image('manga-mode'),
            self._translate('BookToolBar', 'Manga mode (M)'),
            self)
        self.mangaModeButton.setObjectName('mangaModeButton')
        self.mangaModeButton.setCheckable(True)

        self.zoomIn = QtWidgets.QAction(
            image_factory.get_image('zoom-in'),
            self._translate('BookToolBar', 'Zoom in (+)'),
            self)
        self.zoomIn.setObjectName('zoomIn')
        self.zoomOut = QtWidgets.QAction(
            image_factory.get_image('zoom-out'),
            self._translate('BookToolBar', 'Zoom Out (-)'),
            self)
        self.zoomOut.setObjectName('zoomOut')

        self.fitWidth = QtWidgets.QAction(
            image_factory.get_image('zoom-fit-width'),
            self._translate('BookToolBar', 'Fit Width (W)'),
            self)
        self.fitWidth.setObjectName('fitWidth')
        self.fitWidth.setCheckable(True)
        self.bestFit = QtWidgets.QAction(
            image_factory.get_image('zoom-fit-best'),
            self._translate('BookToolBar', 'Best Fit (B)'),
            self)
        self.bestFit.setObjectName('bestFit')
        self.bestFit.setCheckable(True)
        self.originalSize = QtWidgets.QAction(
            image_factory.get_image('zoom-original'),
            self._translate('BookToolBar', 'Original size (O)'),
            self)
        self.originalSize.setObjectName('originalSize')
        self.originalSize.setCheckable(True)

        self.comicBGColor = FixedPushButton(self)
        self.comicBGColor.setToolTip(self._translate('BookToolBar', 'Background color'))
        self.comicBGColor.setObjectName('comicBGColor')

        self.comicSeparator1 = self.addSeparator()
        self.addAction(self.doublePageButton)
        self.addAction(self.mangaModeButton)
        self.comicSeparator2 = self.addSeparator()
        self.addAction(self.zoomIn)
        self.addAction(self.zoomOut)
        self.addAction(self.fitWidth)
        self.addAction(self.bestFit)
        self.addAction(self.originalSize)
        self.comicSeparator3 = self.addSeparator()
        self.comicBGColorAction = self.addWidget(self.comicBGColor)

        self.comicActions = [
            self.doublePageButton,
            self.mangaModeButton,
            self.comicBGColorAction,
            self.zoomIn,
            self.zoomOut,
            self.fitWidth,
            self.bestFit,
            self.originalSize,
            self.comicSeparator1,
            self.comicSeparator2,
            self.comicSeparator3]

        for i in self.comicActions:
            i.setVisible(False)

        # Table of contents Combo Box
        # Has to have a QTreeview associated with it
        self.tocBox = FixedComboBox(self)
        self.tocBox.setToolTip(
            self._translate('BookToolBar', 'Table of Contents'))
        self.tocTreeView = QtWidgets.QTreeView(self.tocBox)
        self.tocBox.setView(self.tocTreeView)
        self.tocTreeView.setItemsExpandable(False)
        self.tocTreeView.setRootIsDecorated(False)

        # All of these will be put after the spacer
        # This means that the buttons in the left side of
        # the toolbar have to split up and added here
        self.addWidget(spacer)
        self.tocBoxAction = self.addWidget(self.tocBox)

        self.bookActions = [
            self.annotationButton,
            self.addBookmarkButton,
            self.bookmarkButton,
            self.searchButton,
            self.distractionFreeButton,
            self.fullscreenButton,
            self.tocBoxAction,
            self.bookSeparator1,
            self.bookSeparator2,
            self.bookSeparator3,
            self.bookSeparator4]

        for i in self.bookActions:
            i.setVisible(True)

        self.addAction(self.resetProfile)

    def toggle_font_settings(self):
        if self.fontButton.isChecked():
            self.customize_view_on()
        else:
            self.customize_view_off()

    def customize_view_on(self):
        images_only = self.parent().tabWidget.currentWidget().are_we_doing_images_only
        # The following might seem redundant,
        # but it's necessary for tab switching
        if images_only:
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
        self.fontButton.setChecked(False)
        for i in self.fontActions:
            i.setVisible(False)

        for i in self.comicActions:
            i.setVisible(False)

        for i in self.bookActions:
            i.setVisible(True)


class LibraryToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(LibraryToolBar, self).__init__(parent)
        self._translate = QtCore.QCoreApplication.translate

        self.setMovable(False)
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFloatable(False)
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)

        image_factory = self.window().QImageFactory

        # Buttons
        self.addButton = QtWidgets.QAction(
            image_factory.get_image('add'),
            self._translate('LibraryToolBar', 'Add book'),
            self)
        self.deleteButton = QtWidgets.QAction(
            image_factory.get_image('remove'),
            self._translate('LibraryToolBar', 'Delete book'),
            self)
        self.colorButton = QtWidgets.QAction(
            image_factory.get_image('color-picker'),
            self._translate('LibraryToolBar', 'Library background color'),
            self)
        self.colorButton.setObjectName('libraryBackground')
        self.settingsButton = QtWidgets.QAction(
            image_factory.get_image('settings'),
            self._translate('LibraryToolBar', 'Settings'),
            self)
        self.settingsButton.setCheckable(True)

        self.coverViewButton = QtWidgets.QAction(
            image_factory.get_image('view-grid'),
            self._translate('LibraryToolBar', 'View as covers'),
            self)
        self.coverViewButton.setCheckable(True)
        self.tableViewButton = QtWidgets.QAction(
            image_factory.get_image('table'),
            self._translate('LibraryToolBar', 'View as table'),
            self)
        self.tableViewButton.setCheckable(True)

        self.reloadLibraryButton = QtWidgets.QAction(
            image_factory.get_image('reload'),
            self._translate('LibraryToolBar', 'Scan Library'),
            self)
        self.reloadLibraryButton.setObjectName('reloadLibrary')

        self.libraryFilterButton = QtWidgets.QToolButton(self)
        self.libraryFilterButton.setIcon(image_factory.get_image('view-readermode'))
        self.libraryFilterButton.setToolTip(
            self._translate('LibraryToolBar', 'Filter library'))

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
        self.addAction(self.reloadLibraryButton)
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
            self._translate('LibraryToolBar', 'Search for Title, Author, Tags...'))
        self.searchBar.setSizePolicy(sizePolicy)
        self.searchBar.setContentsMargins(0, 0, 10, 0)

        # Sorter
        title_string = self._translate('LibraryToolBar', 'Title')
        author_string = self._translate('LibraryToolBar', 'Author')
        year_string = self._translate('LibraryToolBar', 'Year')
        newest_string = self._translate('LibraryToolBar', 'Newest')
        lastread_string = self._translate('LibraryToolBar', 'Last Read')
        progress_string = self._translate('LibraryToolBar', 'Progress')
        sorting_choices = [
            title_string, author_string, year_string,
            newest_string, lastread_string, progress_string]

        self.sortingBox = FixedComboBox(self)
        self.sortingBox.addItems(sorting_choices)
        self.sortingBox.setMinimumContentsLength(10)
        self.sortingBox.setToolTip(self._translate('LibraryToolBar', 'Sort by'))

        # Spacer
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Add widgets
        self.addWidget(spacer)
        self.addWidget(self.searchBar)
        self.sortingBoxAction = self.addWidget(self.sortingBox)


# Sublassing these widgets out prevents them from resizing
class FixedComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(FixedComboBox, self).__init__(parent)
        screen_width = QtWidgets.QDesktopWidget().screenGeometry().width()
        self.adjusted_size = screen_width // 4.5

    def sizeHint(self):
        # This and the one below should adjust to screen size
        return QtCore.QSize(self.adjusted_size, 22)


class FixedLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(FixedLineEdit, self).__init__(parent)
        screen_width = QtWidgets.QDesktopWidget().screenGeometry().width()
        self.adjusted_size = screen_width // 4.5

    def sizeHint(self):
        return QtCore.QSize(self.adjusted_size, 22)

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.clear()


class FixedPushButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(FixedPushButton, self).__init__(parent)

    def sizeHint(self):
        return QtCore.QSize(36, 30)
