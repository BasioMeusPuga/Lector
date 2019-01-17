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

# TODO
# Reading modes
# Double page, Continuous etc

import os
import uuid

from PyQt5 import QtWidgets, QtGui, QtCore

from lector.models import BookmarkProxyModel
from lector.sorter import resize_image
from lector.threaded import BackGroundTextSearch
from lector.contentwidgets import PliantQGraphicsView, PliantQTextBrowser


class Tab(QtWidgets.QWidget):
    def __init__(self, metadata, main_window, parent=None):
        super(Tab, self).__init__(parent)
        self._translate = QtCore.QCoreApplication.translate

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.first_run = True
        self.main_window = main_window
        self.metadata = metadata  # Save progress data into this dictionary
        self.are_we_doing_images_only = self.metadata['images_only']
        self.is_fullscreen = False
        self.is_library = False

        self.masterLayout = QtWidgets.QHBoxLayout(self)
        self.masterLayout.setContentsMargins(0, 0, 0, 0)

        self.metadata['last_accessed'] = QtCore.QDateTime().currentDateTime()

        if self.metadata['position']:
            if self.metadata['position']['is_read']:
                self.generate_position(True)
            current_chapter = self.metadata['position']['current_chapter']
        else:
            self.generate_position()
            current_chapter = 1

        chapter_content = self.metadata['content'][current_chapter - 1][1]

        # Create relevant containers
        if not self.metadata['annotations']:
            self.metadata['annotations'] = {}

        # See bookmark availability
        if not self.metadata['bookmarks']:
            self.metadata['bookmarks'] = {}

        # The content display widget is, by default a QTextBrowser.
        # In case the incoming data is only images
        # such as in the case of comic book files,
        # we want a QGraphicsView widget doing all the heavy lifting
        # instead of a QTextBrowser
        if self.are_we_doing_images_only:  # Boolean
            self.contentView = PliantQGraphicsView(
                self.metadata['path'], self.main_window, self)
            self.contentView.loadImage(chapter_content)
        else:
            self.contentView = PliantQTextBrowser(self.main_window, self)

            relative_path_root = os.path.join(
                self.main_window.temp_dir.path(), self.metadata['hash'])
            relative_paths = []
            for i in os.walk(relative_path_root):

                # TODO
                # Rename the .css files to something else here and keep
                # a record of them
                # Currently, I'm just removing them for the sake of simplicity
                for j in i[2]:
                    file_extension = os.path.splitext(j)[1]
                    if file_extension == '.css':
                        file_path = os.path.join(i[0], j)
                        os.remove(file_path)

                relative_paths.append(os.path.join(relative_path_root, i[0]))
            self.contentView.setSearchPaths(relative_paths)

            self.contentView.setOpenLinks(False)  # TODO Change this when HTML navigation works
            self.contentView.setHtml(chapter_content)
            self.contentView.setReadOnly(True)

            self.hiddenButton = QtWidgets.QToolButton(self)
            self.hiddenButton.setVisible(False)
            self.hiddenButton.clicked.connect(self.set_cursor_position)
            self.hiddenButton.animateClick(50)

        # Load annotations for current content
        self.contentView.common_functions.load_annotations(current_chapter)

        # The following are common to both the text browser and
        # the graphics view
        self.contentView.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.contentView.setObjectName('contentView')
        self.contentView.verticalScrollBar().setSingleStep(
            self.main_window.settings['scroll_speed'])

        if self.main_window.settings['hide_scrollbars']:
            self.contentView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.contentView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        else:
            self.contentView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            self.contentView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        # Create a common dock for annotations and bookmarks
        # And add a vertical layout to it for requisite widgets
        self.sideDock = PliantDockWidget(self.main_window, False, self.contentView)
        self.sideDock.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)
        self.sideDock.setTitleBarWidget(QtWidgets.QWidget())
        self.sideDockTabWidget = QtWidgets.QTabWidget()
        self.sideDock.setWidget(self.sideDockTabWidget)

        # Bookmark tree view and model
        self.bookmarkTreeView = QtWidgets.QTreeView()
        self.bookmarkTreeView.setHeaderHidden(True)
        self.bookmarkTreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.bookmarkTreeView.customContextMenuRequested.connect(
            self.generate_bookmark_context_menu)
        self.bookmarkTreeView.clicked.connect(self.navigate_to_bookmark)
        bookmarks_string = self._translate('Tab', 'Bookmarks')
        self.sideDockTabWidget.addTab(self.bookmarkTreeView, bookmarks_string)

        self.bookmarkModel = QtGui.QStandardItemModel(self)
        self.bookmarkProxyModel = BookmarkProxyModel(self)
        self.generate_bookmark_model()

        # Annotation list view and model
        self.annotationListView = QtWidgets.QListView()
        self.annotationListView.setEditTriggers(QtWidgets.QListView.NoEditTriggers)
        self.annotationListView.doubleClicked.connect(self.contentView.toggle_annotation_mode)
        annotations_string = self._translate('Tab', 'Annotations')
        if not self.are_we_doing_images_only:
            self.sideDockTabWidget.addTab(self.annotationListView, annotations_string)

        self.annotationModel = QtGui.QStandardItemModel(self)
        self.generate_annotation_model()

        # Search view and model
        self.searchLineEdit = QtWidgets.QLineEdit()
        self.searchLineEdit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.searchLineEdit.setClearButtonEnabled(True)
        search_string = self._translate('Tab', 'Search')
        self.searchLineEdit.setPlaceholderText(search_string)

        search_book_string = self._translate('Tab', 'Search entire book')
        self.searchBookButton = QtWidgets.QToolButton()
        self.searchBookButton.setIcon(
            self.main_window.QImageFactory.get_image('view-readermode'))
        self.searchBookButton.setToolTip(search_book_string)
        self.searchBookButton.setCheckable(True)
        self.searchBookButton.setAutoRaise(True)

        case_sensitive_string = self._translate('Tab', 'Match case')
        self.caseSensitiveSearchButton = QtWidgets.QToolButton()
        self.caseSensitiveSearchButton.setIcon(
            self.main_window.QImageFactory.get_image('search-case'))
        self.caseSensitiveSearchButton.setToolTip(case_sensitive_string)
        self.caseSensitiveSearchButton.setCheckable(True)
        self.caseSensitiveSearchButton.setAutoRaise(True)

        match_word_string = self._translate('Tab', 'Match word')
        self.matchWholeWordButton = QtWidgets.QToolButton()
        self.matchWholeWordButton.setIcon(
            self.main_window.QImageFactory.get_image('search-word'))
        self.matchWholeWordButton.setToolTip(match_word_string)
        self.matchWholeWordButton.setCheckable(True)
        self.matchWholeWordButton.setAutoRaise(True)

        self.searchOptionsLayout = QtWidgets.QHBoxLayout()
        self.searchOptionsLayout.setContentsMargins(0, 3, 0, 0)
        self.searchOptionsLayout.addWidget(self.searchLineEdit)
        self.searchOptionsLayout.addWidget(self.searchBookButton)
        self.searchOptionsLayout.addWidget(self.caseSensitiveSearchButton)
        self.searchOptionsLayout.addWidget(self.matchWholeWordButton)

        self.searchResultsTreeView = QtWidgets.QTreeView()
        self.searchResultsTreeView.setHeaderHidden(True)
        self.searchResultsTreeView.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.searchResultsTreeView.clicked.connect(self.navigate_to_search_result)

        self.searchTabLayout = QtWidgets.QVBoxLayout()
        self.searchTabLayout.addLayout(self.searchOptionsLayout)
        self.searchTabLayout.addWidget(self.searchResultsTreeView)
        self.searchTabLayout.setContentsMargins(0, 0, 0, 0)
        self.searchTabWidget = QtWidgets.QWidget()
        self.searchTabWidget.setLayout(self.searchTabLayout)

        if not self.are_we_doing_images_only:
            self.sideDockTabWidget.addTab(self.searchTabWidget, search_string)

        # Create the annotation notes dock
        self.annotationNoteDock = PliantDockWidget(self.main_window, True, self.contentView)
        self.annotationNoteDock.setWindowTitle(self._translate('Tab', 'Note'))
        self.annotationNoteDock.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)
        self.annotationNoteDock.hide()

        self.annotationNoteEdit = QtWidgets.QTextEdit(self.annotationNoteDock)
        self.annotationNoteEdit.setMaximumSize(QtCore.QSize(250, 250))
        self.annotationNoteEdit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.annotationNoteDock.setWidget(self.annotationNoteEdit)

        self.generate_keyboard_shortcuts()

        self.masterLayout.addWidget(self.contentView)
        self.masterLayout.addWidget(self.sideDock)
        self.masterLayout.addWidget(self.annotationNoteDock)

        # The following has to be after the docks are added to the layout
        self.sideDock.setFloating(True)
        self.sideDock.setWindowOpacity(.95)
        self.annotationNoteDock.setFloating(True)
        self.annotationNoteDock.setWindowOpacity(.95)
        self.sideDock.hide()

        # Create search references
        if not self.are_we_doing_images_only:
            self.searchResultsModel = None

            self.searchThread = BackGroundTextSearch()
            self.searchThread.finished.connect(self.generate_search_result_model)

            self.searchTimer = QtCore.QTimer()
            self.searchTimer.setSingleShot(True)
            self.searchTimer.timeout.connect(self.set_search_options)

            self.searchLineEdit.textChanged.connect(
                lambda: self.searchLineEdit.setStyleSheet(
                    QtWidgets.QLineEdit.styleSheet(self)))
            self.searchLineEdit.textChanged.connect(
                lambda: self.searchTimer.start(500))
            self.searchBookButton.clicked.connect(
                lambda: self.searchTimer.start(100))
            self.caseSensitiveSearchButton.clicked.connect(
                lambda: self.searchTimer.start(100))
            self.matchWholeWordButton.clicked.connect(
                lambda: self.searchTimer.start(100))

        # Create tab in the central tab widget
        title = self.metadata['title']
        if self.main_window.settings['attenuate_titles'] and len(title) > 30:
            title = title[:30] + '...'
        self.main_window.tabWidget.addTab(self, title)

        this_tab_index = self.main_window.tabWidget.indexOf(self)
        cover_icon = QtGui.QPixmap()
        cover_icon.loadFromData(self.metadata['cover'])
        self.main_window.tabWidget.setTabIcon(
            this_tab_index, QtGui.QIcon(cover_icon))

        # Hide mouse cursor timer
        self.mouse_hide_timer = QtCore.QTimer()
        self.mouse_hide_timer.setSingleShot(True)
        self.mouse_hide_timer.timeout.connect(self.hide_mouse)

        # Hide the tab bar in case distraction free mode is active
        if not self.main_window.settings['show_bars']:
            self.main_window.tabWidget.tabBar().setVisible(False)

        self.contentView.setFocus()

    def toggle_side_dock(self, tab_required, override_hide=False):
        if (self.sideDock.isVisible()
                and self.sideDockTabWidget.currentIndex() == tab_required
                and not override_hide):
            self.sideDock.hide()
        elif not self.sideDock.isVisible():
            self.sideDock.show()
            if tab_required == 2:
                self.sideDock.activateWindow()
                self.searchLineEdit.setFocus()
                self.searchLineEdit.selectAll()

        self.sideDockTabWidget.setCurrentIndex(tab_required)

    def update_last_accessed_time(self):
        self.metadata['last_accessed'] = QtCore.QDateTime().currentDateTime()

        start_index = self.main_window.lib_ref.libraryModel.index(0, 0)
        matching_item = self.main_window.lib_ref.libraryModel.match(
            start_index,
            QtCore.Qt.UserRole + 6,
            self.metadata['hash'],
            1, QtCore.Qt.MatchExactly)

        try:
            self.main_window.lib_ref.libraryModel.setData(
                matching_item[0], self.metadata['last_accessed'], QtCore.Qt.UserRole + 12)
        except IndexError:  # The file has been deleted
            pass

    def set_cursor_position(self, cursor_position=None, select_chars=0):
        try:
            required_position = self.metadata['position']['cursor_position']
        except KeyError:
            print('Database: Cursor position error. Recommend retry.')
            return

        if cursor_position:
            required_position = cursor_position

        # This is needed so that the line we want is
        # always at the top of the window
        self.contentView.verticalScrollBar().setValue(
            self.contentView.verticalScrollBar().maximum())

        # textCursor() RETURNS a copy of the textcursor
        cursor = self.contentView.textCursor()
        cursor.setPosition(
            required_position - select_chars,
            QtGui.QTextCursor.MoveAnchor)
        if select_chars > 0:  # Select search results
            cursor.movePosition(
                QtGui.QTextCursor.NextCharacter,
                QtGui.QTextCursor.KeepAnchor,
                select_chars)
        self.contentView.setTextCursor(cursor)
        self.contentView.ensureCursorVisible()

        # Finally, to make sure the cover image isn't
        # scrolled halfway through on first open,
        if self.main_window.bookToolBar.tocBox.currentIndex() == 0:
            self.contentView.verticalScrollBar().setValue(0)

    def generate_position(self, is_read=False):
        total_chapters = len(self.metadata['content'])

        current_chapter = 1
        if is_read:
            current_chapter = total_chapters

        # Generate block count @ time of first read
        # Blocks are indexed from 0 up
        blocks_per_chapter = []
        total_blocks = 0

        if not self.are_we_doing_images_only:
            for i in self.metadata['content']:
                chapter_html = i[1]

                textDocument = QtGui.QTextDocument(None)
                textDocument.setHtml(chapter_html)
                block_count = textDocument.blockCount()

                blocks_per_chapter.append(block_count)
                total_blocks += block_count

        self.metadata['position'] = {
            'current_chapter': current_chapter,
            'total_chapters': total_chapters,
            'blocks_per_chapter': blocks_per_chapter,
            'total_blocks': total_blocks,
            'is_read': is_read,
            'current_block': 0,
            'cursor_position': 0}

    def generate_keyboard_shortcuts(self):
        ksNextChapter = QtWidgets.QShortcut(
            QtGui.QKeySequence('Right'), self.contentView)
        ksNextChapter.setObjectName('nextChapter')
        ksNextChapter.activated.connect(self.sneaky_change)

        ksPrevChapter = QtWidgets.QShortcut(
            QtGui.QKeySequence('Left'), self.contentView)
        ksPrevChapter.setObjectName('prevChapter')
        ksPrevChapter.activated.connect(self.sneaky_change)

        ksGoFullscreen = QtWidgets.QShortcut(
            QtGui.QKeySequence('F'), self.contentView)
        ksGoFullscreen.activated.connect(self.go_fullscreen)

        ksExitFullscreen = QtWidgets.QShortcut(
            QtGui.QKeySequence('Escape'), self.contentView)
        ksExitFullscreen.setContext(QtCore.Qt.ApplicationShortcut)
        ksExitFullscreen.activated.connect(self.exit_fullscreen)

        ksToggleBookmarks = QtWidgets.QShortcut(
            QtGui.QKeySequence('Ctrl+B'), self.contentView)
        ksToggleBookmarks.activated.connect(lambda: self.toggle_side_dock(0))

        # Shortcuts not required for comic view functionality
        if not self.are_we_doing_images_only:
            ksToggleAnnotations = QtWidgets.QShortcut(
                QtGui.QKeySequence('Ctrl+N'), self.contentView)
            ksToggleAnnotations.activated.connect(lambda: self.toggle_side_dock(1))

            ksToggleSearch = QtWidgets.QShortcut(
                QtGui.QKeySequence('Ctrl+F'), self.contentView)
            ksToggleSearch.activated.connect(lambda: self.toggle_side_dock(2))

    def go_fullscreen(self):
        # To allow toggles to function
        # properly after the fullscreening

        self.sideDock.hide()
        self.annotationNoteDock.hide()

        if self.contentView.windowState() == QtCore.Qt.WindowFullScreen:
            self.exit_fullscreen()
            return

        if not self.are_we_doing_images_only:
            self.contentView.record_position()

        self.contentView.setWindowFlags(QtCore.Qt.Window)
        self.contentView.setWindowState(QtCore.Qt.WindowFullScreen)
        self.contentView.show()
        self.main_window.hide()

        if not self.are_we_doing_images_only:
            self.hiddenButton.animateClick(100)

        self.mouse_hide_timer.start(2000)
        self.is_fullscreen = True

    def exit_fullscreen(self):
        # Intercept escape presses
        for i in (self.annotationNoteDock, self.sideDock):
            if i.isVisible():
                i.setVisible(False)
                return

        # Prevents cursor position change on escape presses
        if self.main_window.isVisible():
            return

        if not self.are_we_doing_images_only:
            self.contentView.record_position()

        self.main_window.show()
        self.contentView.setWindowFlags(QtCore.Qt.Widget)
        self.contentView.setWindowState(QtCore.Qt.WindowNoState)
        self.contentView.show()
        self.is_fullscreen = False

        if not self.are_we_doing_images_only:
            self.hiddenButton.animateClick(100)

        # Hide the view modification buttons in case they're visible
        self.main_window.bookToolBar.customize_view_off()

        # Exit distraction free mode too
        if not self.main_window.settings['show_bars']:
            self.main_window.toggle_distraction_free()

        self.mouse_hide_timer.start(2000)
        self.contentView.setFocus()

    def change_chapter_tocBox(self):
        chapter_number = self.main_window.bookToolBar.tocBox.currentIndex()
        required_content = self.metadata['content'][chapter_number][1]

        if self.are_we_doing_images_only:
            self.contentView.loadImage(required_content)
        else:
            self.contentView.clear()
            self.contentView.setHtml(required_content)

        self.contentView.common_functions.load_annotations(chapter_number + 1)

    def format_view(self, font, font_size, foreground,
                    background, padding, line_spacing,
                    text_alignment):

        if self.are_we_doing_images_only:
            # Tab color does not need to be set separately in case
            # no padding is set for the viewport of a QGraphicsView
            # and image resizing in done in the pixmap
            my_qbrush = QtGui.QBrush(QtCore.Qt.SolidPattern)
            my_qbrush.setColor(background)
            self.contentView.setBackgroundBrush(my_qbrush)
            self.contentView.resizeEvent()

        else:
            self.contentView.setStyleSheet(
                "QTextEdit {{font-family: {0}; font-size: {1}px; color: {2}; background-color: {3}}}".format(
                    font, font_size, foreground.name(), background.name()))

            # Line spacing
            # Set line spacing per a block format
            # This is proportional line spacing so assume a divisor of 100
            block_format = QtGui.QTextBlockFormat()
            block_format.setLineHeight(
                line_spacing, QtGui.QTextBlockFormat.ProportionalHeight)

            block_format.setTextIndent(50)

            # Give options for alignment
            alignment_dict = {
                'left': QtCore.Qt.AlignLeft,
                'right': QtCore.Qt.AlignRight,
                'center': QtCore.Qt.AlignCenter,
                'justify': QtCore.Qt.AlignJustify}

            current_index = self.main_window.bookToolBar.tocBox.currentIndex()
            if current_index == 0:
                block_format.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
            else:
                block_format.setAlignment(alignment_dict[text_alignment])

            # Also for padding
            # Using setViewPortMargins for this disables scrolling in the margins
            block_format.setLeftMargin(padding)
            block_format.setRightMargin(padding)

            this_cursor = self.contentView.textCursor()
            this_cursor.movePosition(QtGui.QTextCursor.Start, 0, 1)

            # Iterate over the entire document block by block
            # The document ends when the cursor position can no longer be incremented
            while True:
                old_position = this_cursor.position()
                this_cursor.mergeBlockFormat(block_format)
                this_cursor.movePosition(QtGui.QTextCursor.NextBlock, 0, 1)
                new_position = this_cursor.position()
                if old_position == new_position:
                    break

    def generate_annotation_model(self):
        saved_annotations = self.main_window.settings['annotations']
        if not saved_annotations:
            return

        # Create annotation model
        # TODO
        # Annotation previews will require creation of a
        # QStyledItemDelegate
        for i in saved_annotations:
            item = QtGui.QStandardItem()
            item.setText(i['name'])
            item.setData(i, QtCore.Qt.UserRole)
            self.annotationModel.appendRow(item)
        self.annotationListView.setModel(self.annotationModel)

    def add_bookmark(self, position=None):
        identifier = uuid.uuid4().hex[:10]
        description = self._translate('Tab', 'New bookmark')

        if self.are_we_doing_images_only:
            chapter = self.metadata['position']['current_chapter']
            cursor_position = 0
        else:
            chapter, cursor_position = self.contentView.record_position(True)
            if position:  # Should be the case when called from the context menu
                cursor_position = position

        self.metadata['bookmarks'][identifier] = {
            'chapter': chapter,
            'cursor_position': cursor_position,
            'description': description}

        self.sideDock.setVisible(True)
        self.sideDockTabWidget.setCurrentIndex(0)
        self.add_bookmark_to_model(
            description, chapter, cursor_position, identifier, True)

    def add_bookmark_to_model(
            self, description, chapter, cursor_position,
            identifier, new_bookmark=False):

        def edit_new_bookmark(parent_item):
            new_child = parent_item.child(parent_item.rowCount() - 1, 0)
            source_index = self.bookmarkModel.indexFromItem(new_child)
            edit_index = self.bookmarkTreeView.model().mapFromSource(source_index)
            self.sideDock.activateWindow()
            self.bookmarkTreeView.setFocus()
            self.bookmarkTreeView.setCurrentIndex(edit_index)
            self.bookmarkTreeView.edit(edit_index)

        bookmark = QtGui.QStandardItem()

        bookmark.setData(False, QtCore.Qt.UserRole + 10) # Is Parent
        bookmark.setData(chapter, QtCore.Qt.UserRole)  # Chapter name
        bookmark.setData(cursor_position, QtCore.Qt.UserRole + 1)  # Cursor Position
        bookmark.setData(identifier, QtCore.Qt.UserRole + 2)  # Identifier
        bookmark.setData(description, QtCore.Qt.DisplayRole)  # Description

        for i in range(self.bookmarkModel.rowCount()):
            parentIndex = self.bookmarkModel.index(i, 0)
            parent_chapter = parentIndex.data(QtCore.Qt.UserRole)
            if parent_chapter == chapter:
                bookmarkParent = self.bookmarkModel.itemFromIndex(parentIndex)
                bookmarkParent.appendRow(bookmark)
                if new_bookmark:
                    edit_new_bookmark(bookmarkParent)

                return

        # In case no parent item exists
        bookmarkParent = QtGui.QStandardItem()
        bookmarkParent.setData(True, QtCore.Qt.UserRole + 10)  # Is Parent
        bookmarkParent.setFlags(bookmarkParent.flags() & ~QtCore.Qt.ItemIsEditable)  # Is Editable
        chapter_name = self.metadata['content'][chapter - 1][0]  # Chapter Name
        bookmarkParent.setData(chapter_name, QtCore.Qt.DisplayRole)
        bookmarkParent.setData(chapter, QtCore.Qt.UserRole)  # Chapter Number

        bookmarkParent.appendRow(bookmark)
        self.bookmarkModel.appendRow(bookmarkParent)
        if new_bookmark:
            edit_new_bookmark(bookmarkParent)

    def navigate_to_bookmark(self, index):
        if not index.isValid():
            return

        is_parent = self.bookmarkProxyModel.data(index, QtCore.Qt.UserRole + 10)
        if is_parent:
            chapter_number = self.bookmarkProxyModel.data(index, QtCore.Qt.UserRole)
            self.main_window.bookToolBar.tocBox.setCurrentIndex(chapter_number - 1)
            return

        chapter = self.bookmarkProxyModel.data(index, QtCore.Qt.UserRole)
        cursor_position = self.bookmarkProxyModel.data(index, QtCore.Qt.UserRole + 1)

        self.main_window.bookToolBar.tocBox.setCurrentIndex(chapter - 1)
        if not self.are_we_doing_images_only:
            self.set_cursor_position(cursor_position)

    def generate_bookmark_model(self):
        self.bookmarkModel = QtGui.QStandardItemModel(self)

        if self.main_window.settings['toc_with_bookmarks']:
            for chapter_number, i in enumerate(self.metadata['content']):
                chapterItem = QtGui.QStandardItem()
                chapterItem.setData(i[0], QtCore.Qt.DisplayRole)  # Display name
                chapterItem.setData(chapter_number + 1, QtCore.Qt.UserRole)  # Chapter Number
                chapterItem.setData(True, QtCore.Qt.UserRole + 10)  # Is Parent
                chapterItem.setFlags(chapterItem.flags() & ~QtCore.Qt.ItemIsEditable)  # Is Editable
                self.bookmarkModel.appendRow(chapterItem)

        for i in self.metadata['bookmarks'].items():
            description = i[1]['description']
            chapter = i[1]['chapter']
            cursor_position = i[1]['cursor_position']
            identifier = i[0]
            self.add_bookmark_to_model(
                description, chapter, cursor_position, identifier)

        self.generate_bookmark_proxy_model()

    def generate_bookmark_proxy_model(self):
        self.bookmarkProxyModel.setSourceModel(self.bookmarkModel)
        self.bookmarkProxyModel.setSortCaseSensitivity(False)
        self.bookmarkProxyModel.setSortRole(QtCore.Qt.UserRole)
        self.bookmarkProxyModel.sort(0)
        self.bookmarkTreeView.setModel(self.bookmarkProxyModel)

    def generate_bookmark_context_menu(self, position):
        index = self.bookmarkTreeView.indexAt(position)
        if not index.isValid():
            return

        is_parent = self.bookmarkProxyModel.data(index, QtCore.Qt.UserRole + 10)
        if is_parent:
            return

        bookmarkMenu = QtWidgets.QMenu()
        editAction = bookmarkMenu.addAction(
            self.main_window.QImageFactory.get_image('edit-rename'),
            self._translate('Tab', 'Edit'))
        deleteAction = bookmarkMenu.addAction(
            self.main_window.QImageFactory.get_image('trash-empty'),
            self._translate('Tab', 'Delete'))

        action = bookmarkMenu.exec_(
            self.bookmarkTreeView.mapToGlobal(position))

        if action == editAction:
            self.bookmarkTreeView.edit(index)

        if action == deleteAction:
            child_index = self.bookmarkProxyModel.mapToSource(index)
            parent_index = child_index.parent()
            child_rows = self.bookmarkModel.itemFromIndex(parent_index).rowCount()
            delete_uuid = self.bookmarkModel.data(
                child_index, QtCore.Qt.UserRole + 2)

            self.metadata['bookmarks'].pop(delete_uuid)

            self.bookmarkModel.removeRow(child_index.row(), child_index.parent())
            if child_rows == 1:
                self.bookmarkModel.removeRow(parent_index.row())

    def set_search_options(self):
        search_content = (
            self.metadata['content'][self.main_window.bookToolBar.tocBox.currentIndex()],)
        if self.searchBookButton.isChecked():
            search_content = self.metadata['content']

        self.searchThread.set_search_options(
            search_content,
            self.searchLineEdit.text(),
            self.caseSensitiveSearchButton.isChecked(),
            self.matchWholeWordButton.isChecked())
        self.searchThread.start()

    def generate_search_result_model(self):
        self.searchResultsModel = QtGui.QStandardItemModel()
        search_results = self.searchThread.search_results
        for i in search_results:
            parentItem = QtGui.QStandardItem()
            parentItem.setData(True, QtCore.Qt.UserRole)  # Is parent?
            parentItem.setData(i, QtCore.Qt.UserRole + 3)  # Display text for label
            chapter_index = self.main_window.bookToolBar.tocBox.findText(
                i, QtCore.Qt.MatchExactly)

            for j in search_results[i]:
                childItem = QtGui.QStandardItem(parentItem)
                childItem.setData(False, QtCore.Qt.UserRole)  # Is parent?
                childItem.setData(chapter_index, QtCore.Qt.UserRole + 1)  # Chapter index
                childItem.setData(j[0], QtCore.Qt.UserRole + 2)  # Cursor Position
                childItem.setData(j[1], QtCore.Qt.UserRole + 3)  # Display text for label
                childItem.setData(j[2], QtCore.Qt.UserRole + 4)  # Search term
                parentItem.appendRow(childItem)
            self.searchResultsModel.appendRow(parentItem)

        self.searchResultsTreeView.setModel(self.searchResultsModel)
        self.searchResultsTreeView.expandToDepth(1)

        if not search_results and len(self.searchLineEdit.text()) > 2:
            self.searchLineEdit.setStyleSheet("QLineEdit {color: red;}")

        # We'll be putting in labels instead of making a delegate
        # QLabels can understand RTF, and they also have the somewhat
        # distinct advantage of being a lot less work than a delegate

        def generate_label(index):
            label_text = self.searchResultsModel.data(index, QtCore.Qt.UserRole + 3)
            labelWidget = PliantLabelWidget(index, self.navigate_to_search_result)
            labelWidget.setText(label_text)
            self.searchResultsTreeView.setIndexWidget(index, labelWidget)

        for parent_iter in range(self.searchResultsModel.rowCount()):
            parentItem = self.searchResultsModel.item(parent_iter)
            parentIndex = self.searchResultsModel.index(parent_iter, 0)
            generate_label(parentIndex)

            for child_iter in range(parentItem.rowCount()):
                childIndex = self.searchResultsModel.index(child_iter, 0, parentIndex)
                generate_label(childIndex)

    def navigate_to_search_result(self, index):
        if not index.isValid():
            return

        is_parent = self.searchResultsModel.data(index, QtCore.Qt.UserRole)
        if is_parent:
            return

        chapter_index = self.searchResultsModel.data(index, QtCore.Qt.UserRole + 1)
        cursor_position = self.searchResultsModel.data(index, QtCore.Qt.UserRole + 2)
        search_term = self.searchResultsModel.data(index, QtCore.Qt.UserRole + 4)

        self.main_window.bookToolBar.tocBox.setCurrentIndex(chapter_index)
        if not self.are_we_doing_images_only:
            self.set_cursor_position(
                cursor_position, len(search_term))

    def hide_mouse(self):
        self.contentView.viewport().setCursor(QtCore.Qt.BlankCursor)

    def sneaky_change(self):
        direction = -1
        if self.sender().objectName() == 'nextChapter':
            direction = 1

        self.contentView.common_functions.change_chapter(
            direction, True)

    def sneaky_exit(self):
        self.contentView.hide()
        self.main_window.closeEvent()


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


class PliantDockWidget(QtWidgets.QDockWidget):
    def __init__(self, main_window, notes_only, contentView, parent=None):
        super(PliantDockWidget, self).__init__()
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


class PliantQGraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent=None):
        super(PliantQGraphicsScene, self).__init__(parent)
        self.parent = parent
        self._translate = QtCore.QCoreApplication.translate

    def mouseReleaseEvent(self, event):
        self.parent.previous_position = self.parent.pos()

        image_files = '*.jpg *.png'
        dialog_prompt = self._translate('PliantQGraphicsScene', 'Select new cover')
        images_string = self._translate('PliantQGraphicsScene', 'Images')
        new_cover = QtWidgets.QFileDialog.getOpenFileName(
            None, dialog_prompt, self.parent.parent.settings['last_open_path'],
            f'{images_string} ({image_files})')[0]

        if not new_cover:
            self.parent.show()
            return

        with open(new_cover, 'rb') as cover_ref:
            cover_bytes = cover_ref.read()
            resized_cover = resize_image(cover_bytes)
            self.parent.cover_for_database = resized_cover

        cover_pixmap = QtGui.QPixmap()
        cover_pixmap.load(new_cover)
        cover_pixmap = cover_pixmap.scaled(
            140, 205, QtCore.Qt.IgnoreAspectRatio)

        self.parent.load_cover(cover_pixmap, True)
        self.parent.show()


class DragDropListView(QtWidgets.QListView):
    # This is the library listview
    def __init__(self, main_window, parent):
        super(DragDropListView, self).__init__(parent)
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setResizeMode(QtWidgets.QListView.Fixed)
        self.setLayoutMode(QtWidgets.QListView.SinglePass)
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setProperty("showDropIndicator", False)
        self.setProperty("isWrapping", True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setUniformItemSizes(True)
        self.setWordWrap(True)
        self.setObjectName("listView")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(DragDropListView, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        super(DragDropListView, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_list = [url.path() for url in event.mimeData().urls()]
            self.main_window.process_post_hoc_files(file_list, False)
            event.acceptProposedAction()
        else:
            super(DragDropListView, self).dropEvent(event)


class DragDropTableView(QtWidgets.QTableView):
    # This is the library tableview
    def __init__(self, main_window, parent):
        super(DragDropTableView, self).__init__(parent)
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.DoubleClicked |
            QtWidgets.QAbstractItemView.EditKeyPressed |
            QtWidgets.QAbstractItemView.SelectedClicked)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setGridStyle(QtCore.Qt.NoPen)
        self.setSortingEnabled(True)
        self.setWordWrap(False)
        self.setObjectName("tableView")
        self.horizontalHeader().setVisible(True)
        self.verticalHeader().setVisible(False)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(DragDropTableView, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        super(DragDropTableView, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_list = [url.path() for url in event.mimeData().urls()]
            self.main_window.process_post_hoc_files(file_list, False)
            event.acceptProposedAction()
        else:
            super(DragDropTableView, self).dropEvent(event)
