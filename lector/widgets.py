# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017-2018 BasioMeusPuga

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
# Especially for comics

import os
import uuid

from PyQt5 import QtWidgets, QtGui, QtCore

from lector.models import BookmarkProxyModel
from lector.sorter import resize_image
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

        # Create the annotations dock
        self.annotationDock = PliantDockWidget(self.main_window, 'annotations', self.contentView)
        self.annotationDock.setWindowTitle(self._translate('Tab', 'Annotations'))
        self.annotationDock.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)
        self.annotationDock.hide()

        self.annotationListView = QtWidgets.QListView(self.annotationDock)
        self.annotationListView.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.annotationListView.setMaximumWidth(350)
        self.annotationListView.doubleClicked.connect(self.contentView.toggle_annotation_mode)
        self.annotationListView.setEditTriggers(QtWidgets.QListView.NoEditTriggers)
        self.annotationDock.setWidget(self.annotationListView)

        self.annotationModel = QtGui.QStandardItemModel(self)
        self.generate_annotation_model()

        # Create the annotation notes dock
        self.annotationNoteDock = PliantDockWidget(self.main_window, 'notes', self.contentView)
        self.annotationNoteDock.setWindowTitle(self._translate('Tab', 'Note'))
        self.annotationNoteDock.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)
        self.annotationNoteDock.hide()

        self.annotationNoteEdit = QtWidgets.QTextEdit(self.annotationDock)
        self.annotationNoteEdit.setMaximumSize(QtCore.QSize(250, 250))
        self.annotationNoteEdit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.annotationNoteDock.setWidget(self.annotationNoteEdit)

        # Create the dock widget for context specific display
        self.bookmarkDock = PliantDockWidget(self.main_window, 'bookmarks', self.contentView)
        self.bookmarkDock.setWindowTitle(self._translate('Tab', 'Bookmarks'))
        self.bookmarkDock.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)
        self.bookmarkDock.hide()

        self.bookmarkTreeView = QtWidgets.QTreeView(self.bookmarkDock)
        self.bookmarkTreeView.setHeaderHidden(True)
        self.bookmarkTreeView.setMaximumWidth(350)
        self.bookmarkTreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.bookmarkTreeView.customContextMenuRequested.connect(
            self.generate_bookmark_context_menu)
        self.bookmarkTreeView.clicked.connect(self.navigate_to_bookmark)
        self.bookmarkDock.setWidget(self.bookmarkTreeView)

        self.bookmarkModel = QtGui.QStandardItemModel(self)
        self.bookmarkProxyModel = BookmarkProxyModel(self)
        self.generate_bookmark_model()

        self.generate_keyboard_shortcuts()

        self.masterLayout.addWidget(self.contentView)
        self.masterLayout.addWidget(self.annotationDock)
        self.masterLayout.addWidget(self.annotationNoteDock)
        self.masterLayout.addWidget(self.bookmarkDock)

        # The following has to be after the docks are added to the layout
        self.annotationDock.setFloating(True)
        self.annotationDock.setWindowOpacity(.95)
        self.annotationNoteDock.setFloating(True)
        self.annotationNoteDock.setWindowOpacity(.95)
        self.bookmarkDock.setFloating(True)
        self.bookmarkDock.setWindowOpacity(.95)

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

    def set_cursor_position(self, cursor_position=None):
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
            required_position, QtGui.QTextCursor.MoveAnchor)
        self.contentView.setTextCursor(cursor)
        self.contentView.ensureCursorVisible()

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
        self.ksNextChapter = QtWidgets.QShortcut(
            QtGui.QKeySequence('Right'), self.contentView)
        self.ksNextChapter.setObjectName('nextChapter')
        self.ksNextChapter.activated.connect(self.sneaky_change)

        self.ksPrevChapter = QtWidgets.QShortcut(
            QtGui.QKeySequence('Left'), self.contentView)
        self.ksPrevChapter.setObjectName('prevChapter')
        self.ksPrevChapter.activated.connect(self.sneaky_change)

        self.ksGoFullscreen = QtWidgets.QShortcut(
            QtGui.QKeySequence('F11'), self.contentView)
        self.ksGoFullscreen.activated.connect(self.go_fullscreen)

        self.ksExitFullscreen = QtWidgets.QShortcut(
            QtGui.QKeySequence('Escape'), self.contentView)
        self.ksExitFullscreen.setContext(QtCore.Qt.ApplicationShortcut)
        self.ksExitFullscreen.activated.connect(self.exit_fullscreen)

        self.ksToggleBookMarks = QtWidgets.QShortcut(
            QtGui.QKeySequence('Ctrl+B'), self.contentView)
        self.ksToggleBookMarks.activated.connect(self.toggle_bookmarks)

    def go_fullscreen(self):
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

        self.is_fullscreen = True

    def exit_fullscreen(self):
        for i in (self.bookmarkDock, self.annotationDock, self.annotationNoteDock):
            if i.isVisible():
                i.setVisible(False)
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

    def toggle_annotations(self):
        if self.annotationDock.isVisible():
            self.annotationDock.hide()
        else:
            self.annotationDock.show()

    def generate_annotation_model(self):
        saved_annotations = self.main_window.settings['annotations']

        if not saved_annotations:
            return

        def add_to_model(annotation):
            item = QtGui.QStandardItem()
            item.setText(annotation['name'])
            item.setData(annotation, QtCore.Qt.UserRole)
            self.annotationModel.appendRow(item)

        # Prevent annotation mixup
        for i in saved_annotations:
            if self.are_we_doing_images_only and i['applicable_to'] == 'images':
                add_to_model(i)
            elif not self.are_we_doing_images_only and i['applicable_to'] == 'text':
                add_to_model(i)

        self.annotationListView.setModel(self.annotationModel)

    def toggle_bookmarks(self):
        if self.bookmarkDock.isVisible():
            self.bookmarkDock.hide()
        else:
            self.bookmarkDock.show()

    def add_bookmark(self):
        identifier = uuid.uuid4().hex[:10]
        description = self._translate('Tab', 'New bookmark')

        if self.are_we_doing_images_only:
            chapter = self.metadata['position']['current_chapter']
            cursor_position = 0
        else:
            chapter, cursor_position = self.contentView.record_position(True)

        self.metadata['bookmarks'][identifier] = {
            'chapter': chapter,
            'cursor_position': cursor_position,
            'description': description}

        self.bookmarkDock.setVisible(True)
        self.add_bookmark_to_model(
            description, chapter, cursor_position, identifier, True)

    def add_bookmark_to_model(
            self, description, chapter, cursor_position,
            identifier, new_bookmark=False):

        # TODO
        # Start treeview.edit(index) when a new bookmark is added
        # Expand parent item of newly added bookmark

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
                parentItem = self.bookmarkModel.itemFromIndex(parentIndex)
                parentItem.appendRow(bookmark)
                return

        # In case no parent item exists
        bookmarkParent = QtGui.QStandardItem()
        bookmarkParent.setData(True, QtCore.Qt.UserRole + 10) # Is Parent
        bookmarkParent.setFlags(bookmarkParent.flags() & ~QtCore.Qt.ItemIsEditable)
        chapter_name = self.metadata['content'][chapter - 1][0]
        bookmarkParent.setData(chapter_name, QtCore.Qt.DisplayRole)
        bookmarkParent.setData(chapter, QtCore.Qt.UserRole)

        bookmarkParent.appendRow(bookmark)
        self.bookmarkModel.appendRow(bookmarkParent)
        # self.update_bookmark_proxy_model()

    def navigate_to_bookmark(self, index):
        if not index.isValid():
            return

        is_parent = self.bookmarkProxyModel.data(
            index, QtCore.Qt.UserRole + 10)
        if is_parent:
            return

        chapter = self.bookmarkProxyModel.data(index, QtCore.Qt.UserRole)
        cursor_position = self.bookmarkProxyModel.data(index, QtCore.Qt.UserRole + 1)

        self.main_window.bookToolBar.tocBox.setCurrentIndex(chapter - 1)
        if not self.are_we_doing_images_only:
            self.set_cursor_position(cursor_position)

    def generate_bookmark_model(self):
        self.bookmarkModel = QtGui.QStandardItemModel(self)
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

    def update_bookmark_proxy_model(self):
        # TODO
        # This isn't being called currently
        # See if there's any rationale for keeping it / removing it

        self.bookmarkProxyModel.invalidateFilter()
        self.bookmarkProxyModel.setFilterParams(
            self.main_window.bookToolBar.searchBar.text())
        self.bookmarkProxyModel.setFilterFixedString(
            self.main_window.bookToolBar.searchBar.text())

    def generate_bookmark_context_menu(self, position):
        index = self.bookmarkTreeView.indexAt(position)
        if not index.isValid():
            return

        is_parent = self.bookmarkProxyModel.data(
            index, QtCore.Qt.UserRole + 10)
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
            # TODO
            # Deletion that doesn't need to generate the whole model again

            source_index = self.bookmarkProxyModel.mapToSource(index)
            delete_uuid = self.bookmarkModel.data(
                source_index, QtCore.Qt.UserRole + 2)

            self.metadata['bookmarks'].pop(delete_uuid)
            self.generate_bookmark_model()

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


class PliantDockWidget(QtWidgets.QDockWidget):
    def __init__(self, main_window, intended_for, contentView, parent=None):
        super(PliantDockWidget, self).__init__()
        self.main_window = main_window
        self.intended_for = intended_for
        self.contentView = contentView
        self.current_annotation = None

    def showEvent(self, event):
        viewport_height = self.contentView.viewport().size().height()
        viewport_topRight = self.contentView.mapToGlobal(
            self.contentView.viewport().rect().topRight())
        viewport_topLeft = self.contentView.mapToGlobal(
            self.contentView.viewport().rect().topLeft())

        desktop_size = QtWidgets.QDesktopWidget().screenGeometry()
        dock_y = viewport_topRight.y() + (viewport_height * .10)
        dock_height = viewport_height * .80

        if self.intended_for == 'bookmarks':
            dock_width = desktop_size.width() // 5.5
            dock_x = viewport_topRight.x() - dock_width + 1
            self.main_window.bookToolBar.bookmarkButton.setChecked(True)

        elif self.intended_for == 'annotations':
            dock_width = desktop_size.width() // 5.5
            dock_x = viewport_topLeft.x()
            self.main_window.bookToolBar.annotationButton.setChecked(True)

        elif self.intended_for == 'notes':
            dock_width = dock_height = desktop_size.width() // 5.5
            dock_x = QtGui.QCursor.pos().x()
            dock_y = QtGui.QCursor.pos().y()

        self.main_window.active_bookmark_docks.append(self)
        self.setGeometry(dock_x, dock_y, dock_width, dock_height)
        self.setFocus()  # TODO This doesn't work

    def hideEvent(self, event=None):
        if self.intended_for == 'bookmarks':
            self.main_window.bookToolBar.bookmarkButton.setChecked(False)
        elif self.intended_for == 'annotations':
            self.main_window.bookToolBar.annotationButton.setChecked(False)
        elif self.intended_for == 'notes':
            annotationNoteEdit = self.findChild(QtWidgets.QTextEdit)
            if self.current_annotation:
                self.current_annotation['note'] = annotationNoteEdit.toPlainText()

        try:
            self.main_window.active_bookmark_docks.remove(self)
        except ValueError:
            pass

    def set_annotation(self, annotation):
        self.current_annotation = annotation

    def closeEvent(self, event):
        self.main_window.bookToolBar.annotationButton.setChecked(False)
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
