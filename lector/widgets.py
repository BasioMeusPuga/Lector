#!usr/bin/env python3

# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017 BasioMeusPuga

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
import zipfile

try:
    import popplerqt5
except ImportError:
    pass

from PyQt5 import QtWidgets, QtGui, QtCore

from lector.rarfile import rarfile
from lector.models import BookmarkProxyModel
from lector.delegates import BookmarkDelegate
from lector.threaded import BackGroundCacheRefill
from lector.sorter import resize_image


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

        # See bookmark availability
        if not self.metadata['bookmarks']:
            self.metadata['bookmarks'] = {}

        # Create the dock widget for context specific display
        self.dockWidget = PliantDockWidget(self.main_window, self.contentView)
        self.dockWidget.setWindowTitle(self._translate('Tab', 'Bookmarks'))
        self.dockWidget.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)
        self.dockWidget.hide()

        self.dockListView = QtWidgets.QListView(self.dockWidget)
        self.dockListView.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.dockListView.setMaximumWidth(350)
        self.dockListView.setItemDelegate(
            BookmarkDelegate(self.main_window, self.dockListView))
        self.dockListView.setUniformItemSizes(True)
        self.dockListView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.dockListView.customContextMenuRequested.connect(
            self.generate_bookmark_context_menu)
        self.dockListView.clicked.connect(self.navigate_to_bookmark)
        self.dockWidget.setWidget(self.dockListView)

        self.bookmark_model = QtGui.QStandardItemModel(self)
        self.proxy_model = BookmarkProxyModel(self)
        self.generate_bookmark_model()

        self.generate_keyboard_shortcuts()

        self.masterLayout.addWidget(self.contentView)
        self.masterLayout.addWidget(self.dockWidget)
        self.dockWidget.setFloating(True)
        self.dockWidget.setWindowOpacity(.95)

        title = self.metadata['title']
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

        start_index = self.main_window.lib_ref.view_model.index(0, 0)
        matching_item = self.main_window.lib_ref.view_model.match(
            start_index,
            QtCore.Qt.UserRole + 6,
            self.metadata['hash'],
            1, QtCore.Qt.MatchExactly)

        try:
            self.main_window.lib_ref.view_model.setData(
                matching_item[0], self.metadata['last_accessed'], QtCore.Qt.UserRole + 12)
        except IndexError:  # The file has been deleted
            pass

    def set_cursor_position(self, cursor_position=None):
        try:
            required_position = self.metadata['position']['cursor_position']
        except KeyError:
            print(f'Database: Cursor position error. Recommend retry.')
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
        if self.dockWidget.isVisible():
            self.dockWidget.setVisible(False)
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

    def toggle_bookmarks(self):
        if self.dockWidget.isVisible():
            self.dockWidget.hide()
        else:
            self.dockWidget.show()

    def add_bookmark(self):
        # TODO
        # Start dockListView.edit(index) when something new is added

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

        self.add_bookmark_to_model(
            description, chapter, cursor_position, identifier)
        self.dockWidget.setVisible(True)

    def add_bookmark_to_model(self, description, chapter, cursor_position, identifier):
        bookmark = QtGui.QStandardItem()
        bookmark.setData(description, QtCore.Qt.DisplayRole)

        bookmark.setData(chapter, QtCore.Qt.UserRole)
        bookmark.setData(cursor_position, QtCore.Qt.UserRole + 1)
        bookmark.setData(identifier, QtCore.Qt.UserRole + 2)

        self.bookmark_model.appendRow(bookmark)
        self.update_bookmark_proxy_model()

    def navigate_to_bookmark(self, index):
        if not index.isValid():
            return

        chapter = self.proxy_model.data(index, QtCore.Qt.UserRole)
        cursor_position = self.proxy_model.data(index, QtCore.Qt.UserRole + 1)

        self.main_window.bookToolBar.tocBox.setCurrentIndex(chapter - 1)
        if not self.are_we_doing_images_only:
            self.set_cursor_position(cursor_position)

    def generate_bookmark_model(self):
        # TODO
        # Sorting is not working correctly

        try:
            for i in self.metadata['bookmarks'].items():
                self.add_bookmark_to_model(
                    i[1]['description'],
                    i[1]['chapter'],
                    i[1]['cursor_position'],
                    i[0])
        except KeyError:
            title = self.metadata['title']

            # TODO
            # Delete the bookmarks entry for this file
            print(f'Database: Bookmark error for {title}. Recommend delete entry.')
            return

        self.generate_bookmark_proxy_model()

    def generate_bookmark_proxy_model(self):
        self.proxy_model.setSourceModel(self.bookmark_model)
        self.proxy_model.setSortCaseSensitivity(False)
        self.proxy_model.setSortRole(QtCore.Qt.UserRole)
        self.dockListView.setModel(self.proxy_model)

    def update_bookmark_proxy_model(self):
        self.proxy_model.invalidateFilter()
        self.proxy_model.setFilterParams(
            self.main_window.bookToolBar.searchBar.text())
        self.proxy_model.setFilterFixedString(
            self.main_window.bookToolBar.searchBar.text())

    def generate_bookmark_context_menu(self, position):
        index = self.dockListView.indexAt(position)
        if not index.isValid():
            return

        bookmark_menu = QtWidgets.QMenu()
        editAction = bookmark_menu.addAction(
            self.main_window.QImageFactory.get_image('edit-rename'),
            self._translate('Tab', 'Edit'))
        deleteAction = bookmark_menu.addAction(
            self.main_window.QImageFactory.get_image('trash-empty'),
            self._translate('Tab', 'Delete'))

        action = bookmark_menu.exec_(
            self.dockListView.mapToGlobal(position))

        if action == editAction:
            self.dockListView.edit(index)

        if action == deleteAction:
            row = index.row()
            delete_uuid = self.bookmark_model.item(row).data(QtCore.Qt.UserRole + 2)

            self.metadata['bookmarks'].pop(delete_uuid)
            self.bookmark_model.removeRow(index.row())

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


class PliantQGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, filepath, main_window, parent=None):
        super(PliantQGraphicsView, self).__init__(parent)
        self._translate = QtCore.QCoreApplication.translate
        self.parent = parent
        self.main_window = main_window

        self.qimage = None  # Will be needed to resize pdf
        self.image_pixmap = None
        self.image_cache = [None for _ in range(4)]

        self.thread = None

        self.filepath = filepath
        self.filetype = os.path.splitext(self.filepath)[1][1:]

        if self.filetype == 'cbz':
            self.book = zipfile.ZipFile(self.filepath)

        elif self.filetype == 'cbr':
            self.book = rarfile.RarFile(self.filepath)

        elif self.filetype == 'pdf':
            self.book = popplerqt5.Poppler.Document.load(self.filepath)
            self.book.setRenderHint(
                popplerqt5.Poppler.Document.Antialiasing
                and popplerqt5.Poppler.Document.TextAntialiasing)

        self.common_functions = PliantWidgetsCommonFunctions(
            self, self.main_window)

        # TODO
        # Image panning with mouse
        self.ignore_wheel_event = False
        self.ignore_wheel_event_number = 0
        self.setMouseTracking(True)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.viewport().setCursor(QtCore.Qt.ArrowCursor)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            self.generate_graphicsview_context_menu)

    def loadImage(self, current_page):
        # TODO
        # For double page view: 1 before, 1 after
        all_pages = [i[1] for i in self.parent.metadata['content']]

        def load_page(current_page):
            image_pixmap = QtGui.QPixmap()

            if self.filetype in ('cbz', 'cbr'):
                page_data = self.book.read(current_page)
                image_pixmap.loadFromData(page_data)
            elif self.filetype == 'pdf':
                page_data = self.book.page(current_page)
                page_qimage = page_data.renderToImage(400, 400)  # TODO Maybe this needs a setting?
                image_pixmap.convertFromImage(page_qimage)
            return image_pixmap

        def generate_image_cache(current_page):
            print('Building image cache')
            current_page_index = all_pages.index(current_page)

            for i in (-1, 0, 1, 2):
                try:
                    this_page = all_pages[current_page_index + i]
                    this_pixmap = load_page(this_page)
                    self.image_cache[i + 1] = (this_page, this_pixmap)
                except IndexError:
                    self.image_cache[i + 1] = None

        def refill_cache(remove_value):
            # Do NOT put a parent in here or the mother of all
            # memory leaks will result
            self.thread = BackGroundCacheRefill(
                self.image_cache, remove_value,
                self.filetype, self.book, all_pages)
            self.thread.finished.connect(overwrite_cache)
            self.thread.start()

        def overwrite_cache():
            self.image_cache = self.thread.image_cache

        def check_cache(current_page):
            for i in self.image_cache:
                if i:
                    if i[0] == current_page:
                        return_pixmap = i[1]
                        refill_cache(i)
                        return return_pixmap

            # No return happened so the image isn't in the cache
            generate_image_cache(current_page)

        if self.main_window.settings['caching_enabled']:
            return_pixmap = None
            while not return_pixmap:
                return_pixmap = check_cache(current_page)
        else:
            return_pixmap = load_page(current_page)

        self.image_pixmap = return_pixmap
        self.resizeEvent()

    def resizeEvent(self, *args):
        if not self.image_pixmap:
            return

        zoom_mode = self.main_window.comic_profile['zoom_mode']
        padding = self.main_window.comic_profile['padding']

        if zoom_mode == 'fitWidth':
            available_width = self.viewport().width()
            image_pixmap = self.image_pixmap.scaledToWidth(
                available_width, QtCore.Qt.SmoothTransformation)

        elif zoom_mode == 'originalSize':
            image_pixmap = self.image_pixmap

            new_padding = (self.viewport().width() - image_pixmap.width()) // 2
            if new_padding < 0:  # The image is larger than the viewport
                self.main_window.comic_profile['padding'] = 0
            else:
                self.main_window.comic_profile['padding'] = new_padding

        elif zoom_mode == 'bestFit':
            available_width = self.viewport().width()
            available_height = self.viewport().height()

            image_pixmap = self.image_pixmap.scaled(
                available_width, available_height,
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

            self.main_window.comic_profile['padding'] = (
                self.viewport().width() - image_pixmap.width()) // 2

        elif zoom_mode == 'manualZoom':
            available_width = self.viewport().width() - 2 * padding
            image_pixmap = self.image_pixmap.scaledToWidth(
                available_width, QtCore.Qt.SmoothTransformation)

        graphics_scene = QtWidgets.QGraphicsScene()
        graphics_scene.addPixmap(image_pixmap)

        self.setScene(graphics_scene)
        self.show()

    def wheelEvent(self, event):
        self.common_functions.wheelEvent(event)

    def keyPressEvent(self, event):
        vertical = self.verticalScrollBar().value()
        maximum = self.verticalScrollBar().maximum()

        def scroller(increment, move_forward=True):
            if move_forward:
                if vertical == maximum:
                    self.common_functions.change_chapter(1, True)
                else:
                    next_val = vertical + increment
                    if next_val >= .95 * maximum:
                        next_val = maximum
                    self.verticalScrollBar().setValue(next_val)
            else:
                if vertical == 0:
                    self.common_functions.change_chapter(-1, False)
                else:
                    next_val = vertical - increment
                    if next_val <= .05 * maximum:
                        next_val = 0
                    self.verticalScrollBar().setValue(next_val)

        small_increment = maximum // 4
        big_increment = maximum // 2

        if event.key() == QtCore.Qt.Key_Up:
            scroller(small_increment, False)
        if event.key() == QtCore.Qt.Key_Down:
            scroller(small_increment)
        if event.key() == QtCore.Qt.Key_Space:
            scroller(big_increment)

        view_modification_keys = (
            QtCore.Qt.Key_Plus, QtCore.Qt.Key_Minus, QtCore.Qt.Key_Equal,
            QtCore.Qt.Key_B, QtCore.Qt.Key_W, QtCore.Qt.Key_O)
        if event.key() in view_modification_keys:
            self.main_window.modify_comic_view(event.key())

    def record_position(self):
        self.parent.metadata['position']['is_read'] = False
        self.common_functions.update_model()

    def mouseMoveEvent(self, *args):
        self.viewport().setCursor(QtCore.Qt.ArrowCursor)
        self.parent.mouse_hide_timer.start(3000)

    def generate_graphicsview_context_menu(self, position):
        contextMenu = QtWidgets.QMenu()

        saveAction = contextMenu.addAction(
            self.main_window.QImageFactory.get_image('filesaveas'),
            self._translate('PliantQGraphicsView', 'Save page as...'))

        fsToggleAction = dfToggleAction = 'Caesar si viveret, ad remum dareris'

        if self.parent.is_fullscreen:
            fsToggleAction = contextMenu.addAction(
                self.main_window.QImageFactory.get_image('view-fullscreen'),
                self._translate('PliantQGraphicsView', 'Exit fullscreen'))
        else:
            if self.main_window.settings['show_bars']:
                distraction_free_prompt = self._translate(
                    'PliantQGraphicsView', 'Distraction Free mode')
            else:
                distraction_free_prompt = self._translate(
                    'PliantQGraphicsView', 'Exit Distraction Free mode')

            dfToggleAction = contextMenu.addAction(
                self.main_window.QImageFactory.get_image('visibility'),
                distraction_free_prompt)

        viewSubMenu = contextMenu.addMenu('View')
        viewSubMenu.setIcon(
            self.main_window.QImageFactory.get_image('mail-thread-watch'))

        zoominAction = viewSubMenu.addAction(
            self.main_window.QImageFactory.get_image('zoom-in'),
            self._translate('PliantQGraphicsView', 'Zoom in (+)'))

        zoomoutAction = viewSubMenu.addAction(
            self.main_window.QImageFactory.get_image('zoom-out'),
            self._translate('PliantQGraphicsView', 'Zoom out (-)'))

        fitWidthAction = viewSubMenu.addAction(
            self.main_window.QImageFactory.get_image('zoom-fit-width'),
            self._translate('PliantQGraphicsView', 'Fit width (W)'))

        bestFitAction = viewSubMenu.addAction(
            self.main_window.QImageFactory.get_image('zoom-fit-best'),
            self._translate('PliantQGraphicsView', 'Best fit (B)'))

        originalSizeAction = viewSubMenu.addAction(
            self.main_window.QImageFactory.get_image('zoom-original'),
            self._translate('PliantQGraphicsView', 'Original size (O)'))

        bookmarksToggleAction = 'Latin quote 2. Electric Boogaloo.'
        if not self.main_window.settings['show_bars'] or self.parent.is_fullscreen:
            bookmarksToggleAction = contextMenu.addAction(
                self.main_window.QImageFactory.get_image('bookmarks'),
                self._translate('PliantQGraphicsView', 'Bookmarks'))

            self.common_functions.generate_combo_box_action(contextMenu)

        action = contextMenu.exec_(self.sender().mapToGlobal(position))

        if action == saveAction:
            dialog_prompt = self._translate('Main_UI', 'Save page as...')
            extension_string = self._translate('Main_UI', 'Images')
            save_file = QtWidgets.QFileDialog.getSaveFileName(
                self, dialog_prompt, self.main_window.settings['last_open_path'],
                f'{extension_string} (*.png *.jpg *.bmp)')

            if save_file:
                self.image_pixmap.save(save_file[0])

        if action == bookmarksToggleAction:
            self.parent.toggle_bookmarks()
        if action == dfToggleAction:
            self.main_window.toggle_distraction_free()
        if action == fsToggleAction:
            self.parent.exit_fullscreen()

        view_action_dict = {
            zoominAction: QtCore.Qt.Key_Plus,
            zoomoutAction: QtCore.Qt.Key_Minus,
            fitWidthAction: QtCore.Qt.Key_W,
            bestFitAction: QtCore.Qt.Key_B,
            originalSizeAction: QtCore.Qt.Key_O}

        if action in view_action_dict:
            self.main_window.modify_comic_view(view_action_dict[action])

    def closeEvent(self, *args):
        # In case the program is closed when a contentView is fullscreened
        self.main_window.closeEvent()


class PliantQTextBrowser(QtWidgets.QTextBrowser):
    def __init__(self, main_window, parent=None):
        super(PliantQTextBrowser, self).__init__(parent)
        self._translate = QtCore.QCoreApplication.translate

        self.parent = parent
        self.main_window = main_window

        self.common_functions = PliantWidgetsCommonFunctions(
            self, self.main_window)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            self.generate_textbrowser_context_menu)

        self.setMouseTracking(True)
        self.viewport().setCursor(QtCore.Qt.IBeamCursor)
        self.verticalScrollBar().sliderMoved.connect(
            self.record_position)
        self.ignore_wheel_event = False
        self.ignore_wheel_event_number = 0

    def wheelEvent(self, event):
        self.record_position()
        self.common_functions.wheelEvent(event)

    def keyPressEvent(self, event):
        QtWidgets.QTextEdit.keyPressEvent(self, event)
        if event.key() == QtCore.Qt.Key_Space:
            if self.verticalScrollBar().value() == self.verticalScrollBar().maximum():
                self.common_functions.change_chapter(1, True)
            else:
                self.set_top_line_cleanly()
        self.record_position()

    def set_top_line_cleanly(self):
        # Find the cursor position of the top line and move to it
        find_cursor = self.cursorForPosition(QtCore.QPoint(0, 0))
        find_cursor.movePosition(
            find_cursor.position(), QtGui.QTextCursor.KeepAnchor)
        self.setTextCursor(find_cursor)
        self.ensureCursorVisible()

    def record_position(self, return_as_bookmark=False):
        self.parent.metadata['position']['is_read'] = False

        cursor = self.cursorForPosition(QtCore.QPoint(0, 0))
        cursor_position = cursor.position()

        # Current block for progress measurement
        current_block = cursor.block().blockNumber()
        current_chapter = self.parent.metadata['position']['current_chapter']

        blocks_per_chapter = self.parent.metadata['position']['blocks_per_chapter']
        block_sum = sum(blocks_per_chapter[:(current_chapter - 1)])
        block_sum += current_block

        # This 'current_block' refers to the number of
        # blocks in the book upto this one
        self.parent.metadata['position']['current_block'] = block_sum
        self.common_functions.update_model()

        if return_as_bookmark:
            return (self.parent.metadata['position']['current_chapter'],
                    cursor_position)
        else:
            self.parent.metadata['position']['cursor_position'] = cursor_position

    def generate_textbrowser_context_menu(self, position):
        selected_word = self.textCursor().selection()
        selected_word = selected_word.toPlainText()

        contextMenu = QtWidgets.QMenu()

        # The following cannot be None because a click
        # outside the menu means that the action variable is None.
        defineAction = fsToggleAction = dfToggleAction = 'Caesar si viveret, ad remum dareris'

        if selected_word and selected_word != '':
            selected_word = selected_word.split()[0]
            define_string = self._translate('PliantQTextBrowser', 'Define')
            defineAction = contextMenu.addAction(
                self.main_window.QImageFactory.get_image('view-readermode'),
                f'{define_string} "{selected_word}"')

        searchAction = contextMenu.addAction(
            self.main_window.QImageFactory.get_image('search'),
            self._translate('PliantQTextBrowser', 'Search'))

        if self.parent.is_fullscreen:
            fsToggleAction = contextMenu.addAction(
                self.main_window.QImageFactory.get_image('view-fullscreen'),
                self._translate('PliantQTextBrowser', 'Exit fullscreen'))
        else:
            if self.main_window.settings['show_bars']:
                distraction_free_prompt = self._translate(
                    'PliantQTextBrowser', 'Distraction Free mode')
            else:
                distraction_free_prompt = self._translate(
                    'PliantQTextBrowser', 'Exit Distraction Free mode')

            dfToggleAction = contextMenu.addAction(
                self.main_window.QImageFactory.get_image('visibility'),
                distraction_free_prompt)

        bookmarksToggleAction = 'Latin quote 2. Electric Boogaloo.'
        if not self.main_window.settings['show_bars'] or self.parent.is_fullscreen:
            bookmarksToggleAction = contextMenu.addAction(
                self.main_window.QImageFactory.get_image('bookmarks'),
                self._translate('PliantQTextBrowser', 'Bookmarks'))

            self.common_functions.generate_combo_box_action(contextMenu)

        action = contextMenu.exec_(self.sender().mapToGlobal(position))

        if action == defineAction:
            self.main_window.definitionDialog.find_definition(selected_word)
        if action == searchAction:
            self.main_window.bookToolBar.searchBar.setFocus()
        if action == bookmarksToggleAction:
            self.parent.toggle_bookmarks()
        if action == fsToggleAction:
            self.parent.exit_fullscreen()
        if action == dfToggleAction:
            self.main_window.toggle_distraction_free()

    def closeEvent(self, *args):
        self.main_window.closeEvent()

    def mouseMoveEvent(self, event):
        self.viewport().setCursor(QtCore.Qt.IBeamCursor)
        self.parent.mouse_hide_timer.start(3000)
        QtWidgets.QTextBrowser.mouseMoveEvent(self, event)


class PliantWidgetsCommonFunctions:
    def __init__(self, parent_widget, main_window):
        self.pw = parent_widget
        self.main_window = main_window
        self.are_we_doing_images_only = self.pw.parent.are_we_doing_images_only

    def wheelEvent(self, event):
        ignore_events = 20
        if self.are_we_doing_images_only:
            ignore_events = 10

        if self.pw.ignore_wheel_event:
            self.pw.ignore_wheel_event_number += 1
            if self.pw.ignore_wheel_event_number > ignore_events:
                self.pw.ignore_wheel_event = False
                self.pw.ignore_wheel_event_number = 0
            return

        if self.are_we_doing_images_only:
            QtWidgets.QGraphicsView.wheelEvent(self.pw, event)
        else:
            QtWidgets.QTextBrowser.wheelEvent(self.pw, event)

        # Since this is a delta on a mouse move event, it cannot ever be 0
        vertical_pdelta = event.pixelDelta().y()
        if vertical_pdelta > 0:
            moving_up = True
        elif vertical_pdelta < 0:
            moving_up = False

        if abs(vertical_pdelta) > 80:  # Adjust sensitivity here
            # Implies that no scrollbar movement is possible
            if self.pw.verticalScrollBar().value() == self.pw.verticalScrollBar().maximum() == 0:
                if moving_up:
                    self.change_chapter(-1)
                else:
                    self.change_chapter(1)

            # Implies that the scrollbar is at the bottom
            elif self.pw.verticalScrollBar().value() == self.pw.verticalScrollBar().maximum():
                if not moving_up:
                    self.change_chapter(1)

            # Implies scrollbar is at the top
            elif self.pw.verticalScrollBar().value() == 0:
                if moving_up:
                    self.change_chapter(-1)

    def change_chapter(self, direction, was_button_pressed=None):
        current_toc_index = self.main_window.bookToolBar.tocBox.currentIndex()
        max_toc_index = self.main_window.bookToolBar.tocBox.count() - 1

        if (current_toc_index < max_toc_index and direction == 1) or (
                current_toc_index > 0 and direction == -1):
            self.main_window.bookToolBar.tocBox.setCurrentIndex(
                current_toc_index + direction)

            # Set page position depending on if the chapter number is increasing or decreasing
            if direction == 1 or was_button_pressed:
                self.pw.verticalScrollBar().setValue(0)
            else:
                self.pw.verticalScrollBar().setValue(
                    self.pw.verticalScrollBar().maximum())

            if not was_button_pressed:
                self.pw.ignore_wheel_event = True

            if not self.are_we_doing_images_only:
                self.pw.record_position()

    def update_model(self):
        # We're updating the underlying model to have real-time
        # updates on the read status

        # Set a baseline model index in case the item gets deleted
        # E.g It's open in a tab and deleted from the library
        model_index = None
        start_index = self.main_window.lib_ref.view_model.index(0, 0)

        # Find index of the model item that corresponds to the tab
        model_index = self.main_window.lib_ref.view_model.match(
            start_index,
            QtCore.Qt.UserRole + 6,
            self.pw.parent.metadata['hash'],
            1, QtCore.Qt.MatchExactly)

        if self.are_we_doing_images_only:
            position_percentage = (self.pw.parent.metadata['position']['current_chapter'] /
                                   self.pw.parent.metadata['position']['total_chapters'])
        else:
            position_percentage = (self.pw.parent.metadata['position']['current_block'] /
                                   self.pw.parent.metadata['position']['total_blocks'])

        # Update book metadata and position percentage
        if model_index:
            self.main_window.lib_ref.view_model.setData(
                model_index[0], self.pw.parent.metadata, QtCore.Qt.UserRole + 3)

            self.main_window.lib_ref.view_model.setData(
                model_index[0], position_percentage, QtCore.Qt.UserRole + 7)

    def generate_combo_box_action(self, contextMenu):
        contextMenu.addSeparator()

        toc_combobox = QtWidgets.QComboBox()
        toc_data = [i[0] for i in self.pw.parent.metadata['content']]
        toc_combobox.addItems(toc_data)
        toc_combobox.setCurrentIndex(
            self.pw.main_window.bookToolBar.tocBox.currentIndex())
        toc_combobox.currentIndexChanged.connect(
            self.pw.main_window.bookToolBar.tocBox.setCurrentIndex)

        comboboxAction = QtWidgets.QWidgetAction(self.pw)
        comboboxAction.setDefaultWidget(toc_combobox)
        contextMenu.addAction(comboboxAction)


class PliantDockWidget(QtWidgets.QDockWidget):
    def __init__(self, main_window, contentView, parent=None):
        super(PliantDockWidget, self).__init__()
        self.main_window = main_window
        self.contentView = contentView

    def showEvent(self, event):
        viewport_height = self.contentView.viewport().size().height()
        viewport_topRight = self.contentView.mapToGlobal(
            self.contentView.viewport().rect().topRight())

        desktop_size = QtWidgets.QDesktopWidget().screenGeometry()
        dock_width = desktop_size.width() // 5.5

        dock_x = viewport_topRight.x() - dock_width + 1
        dock_y = viewport_topRight.y() + (viewport_height * .10)
        dock_height = viewport_height * .80

        self.setGeometry(dock_x, dock_y, dock_width, dock_height)
        self.main_window.bookToolBar.bookmarkButton.setChecked(True)
        self.main_window.active_bookmark_docks.append(self)

    def hideEvent(self, event):
        self.main_window.bookToolBar.bookmarkButton.setChecked(False)
        self.main_window.active_bookmark_docks.remove(self)


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
