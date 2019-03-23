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

import uuid

from PyQt5 import QtWidgets, QtGui, QtCore

from lector.models import BookmarkProxyModel
from lector.threaded import BackGroundTextSearch


class PliantDockWidget(QtWidgets.QDockWidget):
    def __init__(self, main_window, notes_only, contentView, parent=None):
        super(PliantDockWidget, self).__init__(parent)
        self.main_window = main_window
        self.notes_only = notes_only
        self.contentView = contentView
        self.current_annotation = None
        self.parent = parent

        # Models
        # The following models belong to the sideDock
        # bookmarkModel, bookmarkProxyModel
        # annotationModel
        # searchResultsModel
        self.bookmarkModel = None
        self.bookmarkProxyModel = None
        self.annotationModel = None
        self.searchResultsModel = None

        # References
        # All widgets belong to these
        self.bookmarks = None
        self.annotations = None
        self.search = None

        # Widgets
        # Except this one
        self.sideDockTabWidget = None

        # Animate appearance
        self.animation = QtCore.QPropertyAnimation(self, b'windowOpacity')
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setDuration(200)

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
            self.parent.navBar.hide()

        self.main_window.active_docks.append(self)
        self.setGeometry(dock_x, dock_y, dock_width, dock_height)
        self.animation.start()

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

    def populate(self):
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)
        self.setTitleBarWidget(QtWidgets.QWidget(self))  # Removes titlebar
        self.sideDockTabWidget = QtWidgets.QTabWidget(self)
        self.setWidget(self.sideDockTabWidget)

        # This order is important
        self.bookmarkModel = QtGui.QStandardItemModel(self)
        self.bookmarkProxyModel = BookmarkProxyModel(self)
        self.bookmarks = Bookmarks(self)
        self.bookmarks.generate_bookmark_model()

        if not self.parent.are_we_doing_images_only:
            self.annotationModel = QtGui.QStandardItemModel(self)
            self.annotations = Annotations(self)
            self.annotations.generate_annotation_model()

            self.searchResultsModel = QtGui.QStandardItemModel(self)
            self.search = Search(self)

    def closeEvent(self, event):
        self.hide()
        # Ignoring this event prevents application closure
        # when everything is fullscreened
        event.ignore()


# For the following classes, the parent is the sideDock
# The parentTab is the parent... tab. So self.parent.parent
class Bookmarks:
    def __init__(self, parent):
        self.parent = parent
        self.parentTab = self.parent.parent
        self.bookmarkTreeView = QtWidgets.QTreeView(self.parent)

        self._translate = QtCore.QCoreApplication.translate
        self.bookmarks_string = self._translate('SideDock', 'Bookmarks')
        self.bookmark_default = self._translate('SideDock', 'New bookmark')

        self.create_widgets()

    def create_widgets(self):
        self.bookmarkTreeView.setHeaderHidden(True)
        self.bookmarkTreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.bookmarkTreeView.customContextMenuRequested.connect(
            self.generate_bookmark_context_menu)
        self.bookmarkTreeView.clicked.connect(self.navigate_to_bookmark)

        # Add widget to side dock
        self.parent.sideDockTabWidget.addTab(
            self.bookmarkTreeView, self.bookmarks_string)

    def add_bookmark(self, position=None):
        identifier = uuid.uuid4().hex[:10]

        if self.parentTab.are_we_doing_images_only:
            chapter = self.parentTab.metadata['position']['current_chapter']
            cursor_position = 0
        else:
            chapter, cursor_position = self.parent.contentView.record_position(True)
            if position:  # Should be the case when called from the context menu
                cursor_position = position

        self.parentTab.metadata['bookmarks'][identifier] = {
            'chapter': chapter,
            'cursor_position': cursor_position,
            'description': self.bookmark_default}

        self.parent.setVisible(True)
        self.parent.sideDockTabWidget.setCurrentIndex(0)
        self.add_bookmark_to_model(
            self.bookmark_default, chapter, cursor_position, identifier, True)

    def add_bookmark_to_model(
            self, description, chapter_number, cursor_position,
            identifier, new_bookmark=False):

        def edit_new_bookmark(parent_item):
            new_child = parent_item.child(parent_item.rowCount() - 1, 0)
            source_index = self.parent.bookmarkModel.indexFromItem(new_child)
            edit_index = self.bookmarkTreeView.model().mapFromSource(source_index)
            self.parent.activateWindow()
            self.bookmarkTreeView.setFocus()
            self.bookmarkTreeView.setCurrentIndex(edit_index)
            self.bookmarkTreeView.edit(edit_index)

        def get_chapter_name(chapter_number):
            for i in reversed(self.parentTab.metadata['toc']):
                if i[2] <= chapter_number:
                    return i[1]
            return 'Unknown'

        bookmark = QtGui.QStandardItem()
        bookmark.setData(False, QtCore.Qt.UserRole + 10) # Is Parent
        bookmark.setData(chapter_number, QtCore.Qt.UserRole)  # Chapter number
        bookmark.setData(cursor_position, QtCore.Qt.UserRole + 1)  # Cursor Position
        bookmark.setData(identifier, QtCore.Qt.UserRole + 2)  # Identifier
        bookmark.setData(description, QtCore.Qt.DisplayRole)  # Description
        bookmark_chapter_name = get_chapter_name(chapter_number)

        for i in range(self.parent.bookmarkModel.rowCount()):
            parentIndex = self.parent.bookmarkModel.index(i, 0)
            parent_chapter_number = parentIndex.data(QtCore.Qt.UserRole)
            parent_chapter_name = parentIndex.data(QtCore.Qt.DisplayRole)

            # This prevents duplication of the bookmark in the new
            # navigation model
            if ((parent_chapter_number <= chapter_number) and
                    (parent_chapter_name == bookmark_chapter_name)):
                bookmarkParent = self.parent.bookmarkModel.itemFromIndex(parentIndex)
                bookmarkParent.appendRow(bookmark)
                if new_bookmark:
                    edit_new_bookmark(bookmarkParent)
                return

        # In case no parent item exists
        bookmarkParent = QtGui.QStandardItem()
        bookmarkParent.setData(True, QtCore.Qt.UserRole + 10)  # Is Parent
        bookmarkParent.setFlags(bookmarkParent.flags() & ~QtCore.Qt.ItemIsEditable)  # Is Editable
        bookmarkParent.setData(get_chapter_name(chapter_number), QtCore.Qt.DisplayRole)
        bookmarkParent.setData(chapter_number, QtCore.Qt.UserRole)

        bookmarkParent.appendRow(bookmark)
        self.parent.bookmarkModel.appendRow(bookmarkParent)
        if new_bookmark:
            edit_new_bookmark(bookmarkParent)

    def navigate_to_bookmark(self, index):
        if not index.isValid():
            return

        is_parent = self.parent.bookmarkProxyModel.data(
            index, QtCore.Qt.UserRole + 10)
        if is_parent:
            chapter_number = self.parent.bookmarkProxyModel.data(
                index, QtCore.Qt.UserRole)
            self.parentTab.set_content(chapter_number, True, True)
            return

        chapter = self.parent.bookmarkProxyModel.data(
            index, QtCore.Qt.UserRole)
        cursor_position = self.parent.bookmarkProxyModel.data(
            index, QtCore.Qt.UserRole + 1)

        self.parentTab.set_content(chapter, True, True)
        if not self.parentTab.are_we_doing_images_only:
            self.parentTab.set_cursor_position(cursor_position)

    def generate_bookmark_model(self):
        for i in self.parentTab.metadata['bookmarks'].items():
            description = i[1]['description']
            chapter = i[1]['chapter']
            cursor_position = i[1]['cursor_position']
            identifier = i[0]
            self.add_bookmark_to_model(
                description, chapter, cursor_position, identifier)

        self.generate_bookmark_proxy_model()

    def generate_bookmark_proxy_model(self):
        self.parent.bookmarkProxyModel.setSourceModel(self.parent.bookmarkModel)
        self.parent.bookmarkProxyModel.setSortCaseSensitivity(False)
        self.parent.bookmarkProxyModel.setSortRole(QtCore.Qt.UserRole)
        self.parent.bookmarkProxyModel.sort(0)
        self.bookmarkTreeView.setModel(self.parent.bookmarkProxyModel)

    def generate_bookmark_context_menu(self, position):
        index = self.bookmarkTreeView.indexAt(position)
        if not index.isValid():
            return

        is_parent = self.parent.bookmarkProxyModel.data(
            index, QtCore.Qt.UserRole + 10)
        if is_parent:
            return

        bookmarkMenu = QtWidgets.QMenu()
        editAction = bookmarkMenu.addAction(
            self.parentTab.main_window.QImageFactory.get_image('edit-rename'),
            self._translate('Tab', 'Edit'))
        deleteAction = bookmarkMenu.addAction(
            self.parentTab.main_window.QImageFactory.get_image('trash-empty'),
            self._translate('Tab', 'Delete'))

        action = bookmarkMenu.exec_(
            self.bookmarkTreeView.mapToGlobal(position))

        if action == editAction:
            self.bookmarkTreeView.edit(index)

        if action == deleteAction:
            child_index = self.parent.bookmarkProxyModel.mapToSource(index)
            parent_index = child_index.parent()
            child_rows = self.parent.bookmarkModel.itemFromIndex(
                parent_index).rowCount()
            delete_uuid = self.parent.bookmarkModel.data(
                child_index, QtCore.Qt.UserRole + 2)

            self.parentTab.metadata['bookmarks'].pop(delete_uuid)

            self.parent.bookmarkModel.removeRow(
                child_index.row(), child_index.parent())
            if child_rows == 1:
                self.parent.bookmarkModel.removeRow(parent_index.row())


class Annotations:
    def __init__(self, parent):
        self.parent = parent
        self.parentTab = self.parent.parent
        self.annotationListView = QtWidgets.QListView(self.parent)

        self._translate = QtCore.QCoreApplication.translate
        self.annotations_string = self._translate('SideDock', 'Annotations')

        self.create_widgets()

    def create_widgets(self):
        self.annotationListView.setEditTriggers(QtWidgets.QListView.NoEditTriggers)
        self.annotationListView.doubleClicked.connect(
            self.parent.contentView.toggle_annotation_mode)

        # Add widget to side dock
        self.parent.sideDockTabWidget.addTab(
            self.annotationListView, self.annotations_string)

    def generate_annotation_model(self):
        # TODO
        # Annotation previews will require creation of a
        # QStyledItemDelegate

        saved_annotations = self.parent.main_window.settings['annotations']
        if not saved_annotations:
            return

        # Create annotation model
        for i in saved_annotations:
            item = QtGui.QStandardItem()
            item.setText(i['name'])
            item.setData(i, QtCore.Qt.UserRole)
            self.parent.annotationModel.appendRow(item)
        self.annotationListView.setModel(self.parent.annotationModel)


class Search:
    def __init__(self, parent):
        self.parent = parent
        self.parentTab = self.parent.parent

        self.searchThread = BackGroundTextSearch()
        self.searchOptionsLayout = QtWidgets.QHBoxLayout()
        self.searchTabLayout = QtWidgets.QVBoxLayout()
        self.searchTimer = QtCore.QTimer(self.parent)
        self.searchLineEdit = QtWidgets.QLineEdit(self.parent)
        self.searchBookButton = QtWidgets.QToolButton(self.parent)
        self.caseSensitiveSearchButton = QtWidgets.QToolButton(self.parent)
        self.matchWholeWordButton = QtWidgets.QToolButton(self.parent)
        self.searchResultsTreeView = QtWidgets.QTreeView(self.parent)

        self._translate = QtCore.QCoreApplication.translate
        self.search_string = self._translate('SideDock', 'Search')
        self.search_book_string = self._translate('SideDock', 'Search entire book')
        self.case_sensitive_string = self._translate('SideDock', 'Match case')
        self.match_word_string = self._translate('SideDock', 'Match word')

        self.create_widgets()

    def create_widgets(self):
        self.searchThread.finished.connect(self.generate_search_result_model)

        self.searchTimer.setSingleShot(True)
        self.searchTimer.timeout.connect(self.set_search_options)

        self.searchLineEdit.textChanged.connect(
            lambda: self.searchLineEdit.setStyleSheet(
                QtWidgets.QLineEdit.styleSheet(self.parent)))
        self.searchLineEdit.textChanged.connect(
            lambda: self.searchTimer.start(500))
        self.searchBookButton.clicked.connect(
            lambda: self.searchTimer.start(100))
        self.caseSensitiveSearchButton.clicked.connect(
            lambda: self.searchTimer.start(100))
        self.matchWholeWordButton.clicked.connect(
            lambda: self.searchTimer.start(100))

        self.searchLineEdit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.searchLineEdit.setClearButtonEnabled(True)
        self.searchLineEdit.setPlaceholderText(self.search_string)

        self.searchBookButton.setIcon(
            self.parent.main_window.QImageFactory.get_image('view-readermode'))
        self.searchBookButton.setToolTip(self.search_book_string)
        self.searchBookButton.setCheckable(True)
        self.searchBookButton.setAutoRaise(True)
        self.searchBookButton.setIconSize(QtCore.QSize(20, 20))

        self.caseSensitiveSearchButton.setIcon(
            self.parent.main_window.QImageFactory.get_image('search-case'))
        self.caseSensitiveSearchButton.setToolTip(self.case_sensitive_string)
        self.caseSensitiveSearchButton.setCheckable(True)
        self.caseSensitiveSearchButton.setAutoRaise(True)
        self.caseSensitiveSearchButton.setIconSize(QtCore.QSize(20, 20))

        self.matchWholeWordButton.setIcon(
            self.parent.main_window.QImageFactory.get_image('search-word'))
        self.matchWholeWordButton.setToolTip(self.match_word_string)
        self.matchWholeWordButton.setCheckable(True)
        self.matchWholeWordButton.setAutoRaise(True)
        self.matchWholeWordButton.setIconSize(QtCore.QSize(20, 20))

        self.searchOptionsLayout.setContentsMargins(0, 3, 0, 0)
        self.searchOptionsLayout.addWidget(self.searchLineEdit)
        self.searchOptionsLayout.addWidget(self.searchBookButton)
        self.searchOptionsLayout.addWidget(self.caseSensitiveSearchButton)
        self.searchOptionsLayout.addWidget(self.matchWholeWordButton)

        self.searchResultsTreeView.setHeaderHidden(True)
        self.searchResultsTreeView.setEditTriggers(
            QtWidgets.QTreeView.NoEditTriggers)
        self.searchResultsTreeView.clicked.connect(
            self.navigate_to_search_result)

        self.searchTabLayout.addLayout(self.searchOptionsLayout)
        self.searchTabLayout.addWidget(self.searchResultsTreeView)
        self.searchTabLayout.setContentsMargins(0, 0, 0, 0)
        self.searchTabWidget = QtWidgets.QWidget(self.parent)
        self.searchTabWidget.setLayout(self.searchTabLayout)

        # Add widget to side dock
        self.parent.sideDockTabWidget.addTab(
            self.searchTabWidget, self.search_string)

    def set_search_options(self):
        def generate_title_content_pair(required_chapters):
            title_content_list = []
            for i in self.parentTab.metadata['toc']:
                if i[2] in required_chapters:
                    title_content_list.append(
                        (i[1], self.parentTab.metadata['content'][i[2] - 1], i[2]))
            return title_content_list

        # Select either the current chapter or all chapters
        # Function name is descriptive
        chapter_numbers = (self.parentTab.metadata['position']['current_chapter'],)
        if self.searchBookButton.isChecked():
            chapter_numbers = [i + 1 for i in range(len(self.parentTab.metadata['content']))]
        search_content = generate_title_content_pair(chapter_numbers)

        self.searchThread.set_search_options(
            search_content,
            self.searchLineEdit.text(),
            self.caseSensitiveSearchButton.isChecked(),
            self.matchWholeWordButton.isChecked())
        self.searchThread.start()

    def generate_search_result_model(self):
        self.parent.searchResultsModel.clear()
        search_results = self.searchThread.search_results
        for i in search_results:
            parentItem = QtGui.QStandardItem()
            parentItem.setData(True, QtCore.Qt.UserRole)  # Is parent?
            parentItem.setData(i, QtCore.Qt.UserRole + 3)  # Display text for label

            for j in search_results[i]:
                childItem = QtGui.QStandardItem(parentItem)
                childItem.setData(False, QtCore.Qt.UserRole)  # Is parent?
                childItem.setData(j[3], QtCore.Qt.UserRole + 1)  # Chapter index
                childItem.setData(j[0], QtCore.Qt.UserRole + 2)  # Cursor Position
                childItem.setData(j[1], QtCore.Qt.UserRole + 3)  # Display text for label
                childItem.setData(j[2], QtCore.Qt.UserRole + 4)  # Search term
                parentItem.appendRow(childItem)
            self.parent.searchResultsModel.appendRow(parentItem)

        self.searchResultsTreeView.setModel(self.parent.searchResultsModel)
        self.searchResultsTreeView.expandToDepth(1)

        # Reset stylesheet in case something is found
        if search_results:
            self.searchLineEdit.setStyleSheet(
                QtWidgets.QLineEdit.styleSheet(self.parent))

        # Or set to Red in case nothing is found
        if not search_results and len(self.searchLineEdit.text()) > 2:
            self.searchLineEdit.setStyleSheet("QLineEdit {color: red;}")

        # We'll be putting in labels instead of making a delegate
        # QLabels can understand RTF, and they also have the somewhat
        # distinct advantage of being a lot less work than a delegate

        def generate_label(index):
            label_text = self.parent.searchResultsModel.data(index, QtCore.Qt.UserRole + 3)
            labelWidget = PliantLabelWidget(index, self.navigate_to_search_result)
            labelWidget.setText(label_text)
            self.searchResultsTreeView.setIndexWidget(index, labelWidget)

        for parent_iter in range(self.parent.searchResultsModel.rowCount()):
            parentItem = self.parent.searchResultsModel.item(parent_iter)
            parentIndex = self.parent.searchResultsModel.index(parent_iter, 0)
            generate_label(parentIndex)

            for child_iter in range(parentItem.rowCount()):
                childIndex = self.parent.searchResultsModel.index(child_iter, 0, parentIndex)
                generate_label(childIndex)

    def navigate_to_search_result(self, index):
        if not index.isValid():
            return

        is_parent = self.parent.searchResultsModel.data(index, QtCore.Qt.UserRole)
        if is_parent:
            return

        chapter_number = self.parent.searchResultsModel.data(index, QtCore.Qt.UserRole + 1)
        cursor_position = self.parent.searchResultsModel.data(index, QtCore.Qt.UserRole + 2)
        search_term = self.parent.searchResultsModel.data(index, QtCore.Qt.UserRole + 4)

        self.parentTab.set_content(chapter_number, True, True)
        if not self.parentTab.are_we_doing_images_only:
            self.parentTab.set_cursor_position(
                cursor_position, len(search_term))


class PliantLabelWidget(QtWidgets.QLabel):
    # This is a hack to get clickable / editable appearance
    # search results in the tree view.

    def __init__(self, index, navigate_to_search_result):
        super(PliantLabelWidget, self).__init__()
        self.index = index
        self.navigate_to_search_result = navigate_to_search_result

    def mousePressEvent(self, QMouseEvent):
        self.navigate_to_search_result(self.index)
        QtWidgets.QLabel.mousePressEvent(self, QMouseEvent)


class PliantNavBarWidget(QtWidgets.QDockWidget):
    def __init__(self, main_window, contentView, parent):
        super(PliantNavBarWidget, self).__init__(parent)
        self.main_window = main_window
        self.contentView = contentView
        self.parent = parent

        self.setWindowTitle('Navigation')

        # Animate appearance
        self.animation = QtCore.QPropertyAnimation(self, b'windowOpacity')
        self.animation.setDuration(200)
        self.animation.setStartValue(0)
        self.animation.setEndValue(.8)

        background = self.main_window.settings['dialog_background']
        self.setStyleSheet(
            "QDockWidget {{background-color: {0}}}".format(background.name()))

        self.backButton = QtWidgets.QPushButton()
        self.backButton.setFlat(True)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(":/images/previous.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.backButton.setIcon(icon)
        self.backButton.setIconSize(QtCore.QSize(24, 24))

        self.nextButton = QtWidgets.QPushButton()
        self.nextButton.setFlat(True)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(":/images/next.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.nextButton.setIcon(icon)
        self.nextButton.setIconSize(QtCore.QSize(24, 24))

        self.backButton.clicked.connect(lambda: self.button_click(-1))
        self.nextButton.clicked.connect(lambda: self.button_click(1))

        self.tocComboBox = FixedComboBox(self)
        self.populate_combo_box()

        self.navLayout = QtWidgets.QHBoxLayout()
        self.navLayout.addWidget(self.backButton)
        self.navLayout.addWidget(self.tocComboBox)
        self.navLayout.addWidget(self.nextButton)
        self.navWidget = QtWidgets.QWidget()
        self.navWidget.setLayout(self.navLayout)

        self.setWidget(self.navWidget)

    def showEvent(self, event=None):
        # TODO
        # See what happens when the size of the viewport is smaller
        # than the size of the dock

        viewport_bottomRight = self.contentView.mapToGlobal(
            self.contentView.viewport().rect().bottomRight())

        # Dock dimensions
        desktop_size = QtWidgets.QDesktopWidget().screenGeometry()
        dock_width = desktop_size.width() // 4.5
        dock_height = 30

        dock_x = viewport_bottomRight.x() - dock_width - 30
        dock_y = viewport_bottomRight.y() - 70

        self.main_window.active_docks.append(self)
        self.setGeometry(dock_x, dock_y, dock_width, dock_height)

        # Rounded
        radius = 20
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(self.rect()), radius, radius)
        try:
            mask = QtGui.QRegion(path.toFillPolygon().toPolygon())
            self.setMask(mask)
        except TypeError:  # Required for older versions of Qt
            pass

        self.animation.start()

    def populate_combo_box(self):
        def set_toc_position(tocTree):
            currentIndex = tocTree.currentIndex()
            required_position = currentIndex.data(QtCore.Qt.UserRole)
            self.return_focus()
            self.parent.set_content(required_position, True, True)

        # Create the Combobox / Treeview combination
        tocTree = QtWidgets.QTreeView()
        self.tocComboBox.setView(tocTree)
        self.tocComboBox.setModel(self.parent.tocModel)
        tocTree.setRootIsDecorated(False)
        tocTree.setItemsExpandable(False)
        tocTree.expandAll()

        # Set the position of the QComboBox
        self.parent.set_tocBox_index(None, self.tocComboBox)

        # Make clicking do something
        self.tocComboBox.currentIndexChanged.connect(
            lambda: set_toc_position(tocTree))

    def button_click(self, change):
        self.contentView.common_functions.change_chapter(change)
        self.return_focus()

    def return_focus(self):
        # The NavBar needs to be hidden after clicking
        self.parent.activateWindow()
        self.parent.contentView.setFocus()
        self.parent.mouseHideTimer.start()


class FixedComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(FixedComboBox, self).__init__(parent)
        screen_width = QtWidgets.QDesktopWidget().screenGeometry().width()
        self.adjusted_size = screen_width // 6

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return QtCore.QSize(self.adjusted_size, 32)

    def wheelEvent(self, QWheelEvent):
        # Disable mouse wheel scrolling in the ComboBox
        return
