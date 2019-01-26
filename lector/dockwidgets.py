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

from PyQt5 import QtWidgets, QtGui, QtCore

from lector.models import BookmarkProxyModel


class PliantDockWidget(QtWidgets.QDockWidget):
    def __init__(self, main_window, notes_only, contentView, parent=None):
        super(PliantDockWidget, self).__init__(parent)
        self.main_window = main_window
        self.notes_only = notes_only
        self.contentView = contentView
        self.current_annotation = None

    def showEvent(self, event=None):
        viewport_topRight = self.contentView.mapToGlobal(
            self.contentView.viewport().rect().topRight())

        desktop_size = QtWidgets.QDesktopWidget().screenGeometry()
        dock_y = viewport_topRight.y()
        dock_height = self.contentView.viewport().size().height()

        if self.notes_only:
            dock_width = dock_height = desktop_size.width() // 5.5
            dock_x = QtGui.QCursor.pos().x()
            dock_y = QtGui.QCursor.pos().y()
        else:
            dock_width = desktop_size.width() // 5
            dock_x = viewport_topRight.x() - dock_width + 1

        self.main_window.active_docks.append(self)
        self.setGeometry(dock_x, dock_y, dock_width, dock_height)

    def hideEvent(self, event=None):
        if self.notes_only:
            annotationNoteEdit = self.findChild(QtWidgets.QTextEdit)
            if self.current_annotation:
                self.current_annotation['note'] = annotationNoteEdit.toPlainText()

        try:
            self.main_window.active_docks.remove(self)
        except ValueError:
            pass

    def set_annotation(self, annotation):
        self.current_annotation = annotation

    def closeEvent(self, event):
        self.hide()

        # Ignoring this event prevents application closure when everything is fullscreened
        event.ignore()


def populate_sideDock(tabWidget):
    tabWidget.sideDock.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)
    tabWidget.sideDock.setTitleBarWidget(QtWidgets.QWidget())
    tabWidget.sideDockTabWidget = QtWidgets.QTabWidget()
    tabWidget.sideDock.setWidget(tabWidget.sideDockTabWidget)

    # Bookmark tree view and model
    tabWidget.bookmarkTreeView = QtWidgets.QTreeView(tabWidget)
    tabWidget.bookmarkTreeView.setHeaderHidden(True)
    tabWidget.bookmarkTreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    tabWidget.bookmarkTreeView.customContextMenuRequested.connect(
        tabWidget.generate_bookmark_context_menu)
    tabWidget.bookmarkTreeView.clicked.connect(tabWidget.navigate_to_bookmark)
    bookmarks_string = tabWidget._translate('Tab', 'Bookmarks')
    tabWidget.sideDockTabWidget.addTab(tabWidget.bookmarkTreeView, bookmarks_string)

    tabWidget.bookmarkModel = QtGui.QStandardItemModel(tabWidget)
    tabWidget.bookmarkProxyModel = BookmarkProxyModel(tabWidget)
    tabWidget.generate_bookmark_model()

    # Annotation list view and model
    tabWidget.annotationListView = QtWidgets.QListView(tabWidget)
    tabWidget.annotationListView.setEditTriggers(QtWidgets.QListView.NoEditTriggers)
    tabWidget.annotationListView.doubleClicked.connect(tabWidget.contentView.toggle_annotation_mode)
    annotations_string = tabWidget._translate('Tab', 'Annotations')
    if not tabWidget.are_we_doing_images_only:
        tabWidget.sideDockTabWidget.addTab(tabWidget.annotationListView, annotations_string)

    tabWidget.annotationModel = QtGui.QStandardItemModel(tabWidget)
    tabWidget.generate_annotation_model()

    # Search view and model
    tabWidget.searchLineEdit = QtWidgets.QLineEdit(tabWidget)
    tabWidget.searchLineEdit.setFocusPolicy(QtCore.Qt.StrongFocus)
    tabWidget.searchLineEdit.setClearButtonEnabled(True)
    search_string = tabWidget._translate('Tab', 'Search')
    tabWidget.searchLineEdit.setPlaceholderText(search_string)

    search_book_string = tabWidget._translate('Tab', 'Search entire book')
    tabWidget.searchBookButton = QtWidgets.QToolButton()
    tabWidget.searchBookButton.setIcon(
        tabWidget.main_window.QImageFactory.get_image('view-readermode'))
    tabWidget.searchBookButton.setToolTip(search_book_string)
    tabWidget.searchBookButton.setCheckable(True)
    tabWidget.searchBookButton.setAutoRaise(True)

    case_sensitive_string = tabWidget._translate('Tab', 'Match case')
    tabWidget.caseSensitiveSearchButton = QtWidgets.QToolButton(tabWidget)
    tabWidget.caseSensitiveSearchButton.setIcon(
        tabWidget.main_window.QImageFactory.get_image('search-case'))
    tabWidget.caseSensitiveSearchButton.setToolTip(case_sensitive_string)
    tabWidget.caseSensitiveSearchButton.setCheckable(True)
    tabWidget.caseSensitiveSearchButton.setAutoRaise(True)

    match_word_string = tabWidget._translate('Tab', 'Match word')
    tabWidget.matchWholeWordButton = QtWidgets.QToolButton()
    tabWidget.matchWholeWordButton.setIcon(
        tabWidget.main_window.QImageFactory.get_image('search-word'))
    tabWidget.matchWholeWordButton.setToolTip(match_word_string)
    tabWidget.matchWholeWordButton.setCheckable(True)
    tabWidget.matchWholeWordButton.setAutoRaise(True)

    tabWidget.searchOptionsLayout = QtWidgets.QHBoxLayout()
    tabWidget.searchOptionsLayout.setContentsMargins(0, 3, 0, 0)
    tabWidget.searchOptionsLayout.addWidget(tabWidget.searchLineEdit)
    tabWidget.searchOptionsLayout.addWidget(tabWidget.searchBookButton)
    tabWidget.searchOptionsLayout.addWidget(tabWidget.caseSensitiveSearchButton)
    tabWidget.searchOptionsLayout.addWidget(tabWidget.matchWholeWordButton)

    tabWidget.searchResultsTreeView = QtWidgets.QTreeView()
    tabWidget.searchResultsTreeView.setHeaderHidden(True)
    tabWidget.searchResultsTreeView.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
    tabWidget.searchResultsTreeView.clicked.connect(tabWidget.navigate_to_search_result)

    tabWidget.searchTabLayout = QtWidgets.QVBoxLayout()
    tabWidget.searchTabLayout.addLayout(tabWidget.searchOptionsLayout)
    tabWidget.searchTabLayout.addWidget(tabWidget.searchResultsTreeView)
    tabWidget.searchTabLayout.setContentsMargins(0, 0, 0, 0)
    tabWidget.searchTabWidget = QtWidgets.QWidget()
    tabWidget.searchTabWidget.setLayout(tabWidget.searchTabLayout)

    if not tabWidget.are_we_doing_images_only:
        tabWidget.sideDockTabWidget.addTab(tabWidget.searchTabWidget, search_string)
