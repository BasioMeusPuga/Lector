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

import os
import zipfile
import webbrowser

try:
    import popplerqt5
except ImportError:
    pass

from PyQt5 import QtWidgets, QtGui, QtCore

from lector.rarfile import rarfile
from lector.threaded import BackGroundCacheRefill
from lector.annotations import AnnotationPlacement


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

        self.annotation_dict = self.parent.metadata['annotations']

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

        self.ignore_wheel_event = False
        self.ignore_wheel_event_number = 0
        self.setMouseTracking(True)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            self.generate_graphicsview_context_menu)

    def loadImage(self, current_page):
        all_pages = [i[1] for i in self.parent.metadata['content']]
        current_page_index = all_pages.index(current_page)

        double_page_mode = False
        if (self.main_window.settings['page_view_button'] == 'doublePageButton'
                and (current_page_index != 0 and current_page_index != len(all_pages) - 1)):
            double_page_mode = True

        def load_page(current_page):
            def page_loader(page):
                # TODO Maybe pdf image res needs a setting?
                pixmap = QtGui.QPixmap()
                if self.filetype in ('cbz', 'cbr'):
                    page_data = self.book.read(page)
                    pixmap.loadFromData(page_data)
                elif self.filetype == 'pdf':
                    page_data = self.book.page(current_page)
                    page_qimage = page_data.renderToImage(400, 400)
                    pixmap.convertFromImage(page_qimage)
                return pixmap

            firstPixmap = page_loader(current_page)
            if not double_page_mode:
                return firstPixmap

            next_page = all_pages[current_page_index + 1]
            secondPixmap = page_loader(next_page)

            bigPixmap = QtGui.QPixmap(
                firstPixmap.width() + secondPixmap.width() + 5,
                firstPixmap.height())
            bigPixmap.fill(QtCore.Qt.transparent)
            imagePainter = QtGui.QPainter(bigPixmap)
            imagePainter.drawPixmap(0, 0, firstPixmap)
            imagePainter.drawPixmap(firstPixmap.width() + 5, 0, secondPixmap)
            imagePainter.end()
            return bigPixmap

        def generate_image_cache(current_page):
            print('Building image cache')
            current_page_index = all_pages.index(current_page)

            # Image caching for single and double page views
            page_indices = (-1, 0, 1, 2)

            index_modifier = 0
            if double_page_mode:
                index_modifier = 1

            for i in page_indices:
                try:
                    this_page = all_pages[current_page_index + i + index_modifier]
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

        # TODO
        # Get caching working for double page view
        if not double_page_mode and self.main_window.settings['caching_enabled']:
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

        graphicsScene = QtWidgets.QGraphicsScene()
        graphicsScene.addPixmap(image_pixmap)

        self.setScene(graphicsScene)
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

    def mouseMoveEvent(self, event):
        if QtWidgets.QApplication.mouseButtons() == QtCore.Qt.NoButton:
            self.viewport().setCursor(QtCore.Qt.OpenHandCursor)
        else:
            self.viewport().setCursor(QtCore.Qt.ClosedHandCursor)
        self.parent.mouse_hide_timer.start(3000)
        QtWidgets.QGraphicsView.mouseMoveEvent(self, event)

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

        view_submenu_string = self._translate('PliantQGraphicsView', 'View')
        viewSubMenu = contextMenu.addMenu(view_submenu_string)
        viewSubMenu.setIcon(
            self.main_window.QImageFactory.get_image('mail-thread-watch'))

        singlePageAction = doublePageAction = 'It\'s hammer time'
        if self.main_window.settings['page_view_button'] == 'doublePageButton':
            singlePageAction = viewSubMenu.addAction(
                self.main_window.QImageFactory.get_image('page-single'),
                self._translate('PliantQGraphicsView', 'Single page view'))
        else:
            doublePageAction = viewSubMenu.addAction(
                self.main_window.QImageFactory.get_image('page-double'),
                self._translate('PliantQGraphicsView', 'Double page view'))

        viewSubMenu.addSeparator()

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

        if action == singlePageAction:
            self.main_window.bookToolBar.singlePageButton.trigger()

        if action == doublePageAction:
            self.main_window.bookToolBar.doublePageButton.trigger()

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

    def toggle_annotation_mode(self):
        pass


class PliantQTextBrowser(QtWidgets.QTextBrowser):
    def __init__(self, main_window, parent=None):
        super(PliantQTextBrowser, self).__init__(parent)
        self._translate = QtCore.QCoreApplication.translate

        self.parent = parent
        self.main_window = main_window

        self.annotation_mode = False
        self.annotator = AnnotationPlacement()
        self.current_annotation = None
        self.annotation_dict = self.parent.metadata['annotations']

        self.common_functions = PliantWidgetsCommonFunctions(
            self, self.main_window)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            self.generate_textbrowser_context_menu)

        self.setMouseTracking(True)
        self.verticalScrollBar().sliderMoved.connect(
            self.record_position)
        self.ignore_wheel_event = False
        self.ignore_wheel_event_number = 0

        self.at_end = False

    def wheelEvent(self, event):
        self.record_position()
        self.common_functions.wheelEvent(event)

    def keyPressEvent(self, event):
        QtWidgets.QTextEdit.keyPressEvent(self, event)
        if event.key() == QtCore.Qt.Key_Space:
            if self.verticalScrollBar().value() == self.verticalScrollBar().maximum():
                if self.at_end:  # This makes sure the last lines of the chapter don't get skipped
                    self.common_functions.change_chapter(1, True)
                self.at_end = True
            else:
                self.at_end = False
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

    def toggle_annotation_mode(self):
        if self.annotation_mode:
            self.annotation_mode = False
            self.viewport().setCursor(QtCore.Qt.ArrowCursor)
            self.parent.annotationDock.show()
            self.parent.annotationDock.setWindowOpacity(.95)

            self.current_annotation = None
            self.parent.annotationListView.clearSelection()

        else:
            self.annotation_mode = True
            self.viewport().setCursor(QtCore.Qt.IBeamCursor)
            self.parent.annotationDock.hide()

            selected_index = self.parent.annotationListView.currentIndex()
            self.current_annotation = self.parent.annotationModel.data(
                selected_index, QtCore.Qt.UserRole)
            print('Current annotation: ' + self.current_annotation['name'])

    def mouseReleaseEvent(self, event):
        # This takes care of annotation placement
        # and addition to the list that holds all current annotations
        if not self.current_annotation:
            QtWidgets.QTextBrowser.mouseReleaseEvent(self, event)
            return

        current_chapter = self.parent.metadata['position']['current_chapter']
        cursor = self.textCursor()
        cursor_start = cursor.selectionStart()
        cursor_end = cursor.selectionEnd()
        annotation_type = 'text_markup'
        applicable_to = 'text'
        annotation_components = self.current_annotation['components']

        self.annotator.set_current_annotation(
            annotation_type, annotation_components)

        new_cursor = self.annotator.format_text(
            cursor, cursor_start, cursor_end)
        self.setTextCursor(new_cursor)

        # TODO
        # Maybe use annotation name for a consolidated annotation list

        this_annotation = {
            'name': self.current_annotation['name'],
            'applicable_to': applicable_to,
            'type': annotation_type,
            'cursor': (cursor_start, cursor_end),
            'components': annotation_components,
            'note': None}

        try:
            self.annotation_dict[current_chapter].append(this_annotation)
        except KeyError:
            self.annotation_dict[current_chapter] = []
            self.annotation_dict[current_chapter].append(this_annotation)

        self.toggle_annotation_mode()

    def generate_textbrowser_context_menu(self, position):
        selection = self.textCursor().selection()
        selection = selection.toPlainText()

        current_chapter = self.parent.metadata['position']['current_chapter']
        cursor_at_mouse = self.cursorForPosition(position)
        annotation_is_present = self.common_functions.annotation_specific(
            'check', 'text', current_chapter, cursor_at_mouse.position())

        contextMenu = QtWidgets.QMenu()

        # The following cannot be None because a click
        # outside the menu means that the action variable is None.
        defineAction = fsToggleAction = dfToggleAction = 'Caesar si viveret, ad remum dareris'
        searchWikipediaAction = searchYoutubeAction = 'Does anyone know something funny in Latin?'
        searchAction = searchGoogleAction = bookmarksToggleAction = 'TODO Insert Latin Joke'
        deleteAnnotationAction = editAnnotationNoteAction = 'Latin quote 2. Electric Boogaloo.'

        if selection and selection != '':
            first_selected_word = selection.split()[0]
            define_string = self._translate('PliantQTextBrowser', 'Define')
            defineAction = contextMenu.addAction(
                self.main_window.QImageFactory.get_image('view-readermode'),
                f'{define_string} "{first_selected_word}"')

            search_submenu_string = self._translate('PliantQTextBrowser', 'Search for')
            searchSubMenu = contextMenu.addMenu(search_submenu_string + f' "{selection}"')
            searchSubMenu.setIcon(self.main_window.QImageFactory.get_image('search'))

            searchAction = searchSubMenu.addAction(
                self.main_window.QImageFactory.get_image('search'),
                self._translate('PliantQTextBrowser', 'In this book'))
            searchSubMenu.addSeparator()
            searchGoogleAction = searchSubMenu.addAction(
                QtGui.QIcon(':/images/Google.png'),
                'Google')
            searchWikipediaAction = searchSubMenu.addAction(
                QtGui.QIcon(':/images/Wikipedia.png'),
                'Wikipedia')
            searchYoutubeAction = searchSubMenu.addAction(
                QtGui.QIcon(':/images/Youtube.png'),
                'Youtube')

        if annotation_is_present:
            annotationsubMenu = contextMenu.addMenu('Annotation')
            annotationsubMenu.setIcon(self.main_window.QImageFactory.get_image('annotate'))

            editAnnotationNoteAction = annotationsubMenu.addAction(
                self.main_window.QImageFactory.get_image('edit-rename'),
                self._translate('PliantQTextBrowser', 'Edit note'))
            deleteAnnotationAction = annotationsubMenu.addAction(
                self.main_window.QImageFactory.get_image('remove'),
                self._translate('PliantQTextBrowser', 'Delete annotation'))

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

        if not self.main_window.settings['show_bars'] or self.parent.is_fullscreen:
            bookmarksToggleAction = contextMenu.addAction(
                self.main_window.QImageFactory.get_image('bookmarks'),
                self._translate('PliantQTextBrowser', 'Bookmarks'))

            self.common_functions.generate_combo_box_action(contextMenu)

        action = contextMenu.exec_(self.sender().mapToGlobal(position))

        if action == defineAction:
            self.main_window.definitionDialog.find_definition(selection)

        if action == searchAction:
            self.main_window.bookToolBar.searchBar.setText(selection)
            self.main_window.bookToolBar.searchBar.setFocus()
        if action == searchGoogleAction:
            webbrowser.open_new_tab(
                f'https://www.google.com/search?q={selection}')
        if action == searchWikipediaAction:
            webbrowser.open_new_tab(
                f'https://en.wikipedia.org/wiki/Special:Search?search={selection}')
        if action == searchYoutubeAction:
            webbrowser.open_new_tab(
                f'https://www.youtube.com/results?search_query={selection}')

        if action == editAnnotationNoteAction:
            self.common_functions.annotation_specific(
                'note', 'text', current_chapter, cursor_at_mouse.position())

        if action == deleteAnnotationAction:
            self.common_functions.annotation_specific(
                'delete', 'text', current_chapter, cursor_at_mouse.position())

        if action == bookmarksToggleAction:
            self.parent.toggle_bookmarks()

        if action == fsToggleAction:
            self.parent.exit_fullscreen()
        if action == dfToggleAction:
            self.main_window.toggle_distraction_free()

    def closeEvent(self, *args):
        self.main_window.closeEvent()

    def mouseMoveEvent(self, event):
        if self.annotation_mode:
            self.viewport().setCursor(QtCore.Qt.IBeamCursor)
        else:
            self.viewport().setCursor(QtCore.Qt.ArrowCursor)
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

            # Special cases for double page view
            def get_modifier():
                if (self.main_window.settings['page_view_button'] == 'singlePageButton'
                        or not self.are_we_doing_images_only):
                    return 0

                if (current_toc_index == 0
                        or current_toc_index % 2 == 0
                        or current_toc_index == max_toc_index):
                    return 0
                if current_toc_index % 2 == 1:
                    return direction

            self.main_window.bookToolBar.tocBox.setCurrentIndex(
                current_toc_index + direction + get_modifier())

            # Set page position depending on if the chapter number is increasing or decreasing
            if direction == 1 or was_button_pressed:
                self.pw.verticalScrollBar().setValue(0)
            else:
                self.pw.verticalScrollBar().setValue(
                    self.pw.verticalScrollBar().maximum())

            if not was_button_pressed:
                self.pw.ignore_wheel_event = True

    def load_annotations(self, chapter):
        try:
            chapter_annotations = self.pw.annotation_dict[chapter]
        except KeyError:
            return

        for i in chapter_annotations:
            applicable_to = i['applicable_to']
            annotation_type = i['type']
            annotation_components = i['components']

            if not self.are_we_doing_images_only and applicable_to == 'text':
                cursor = self.pw.textCursor()
                cursor_start = i['cursor'][0]
                cursor_end = i['cursor'][1]

                self.pw.annotator.set_current_annotation(
                    annotation_type, annotation_components)

                new_cursor = self.pw.annotator.format_text(
                    cursor, cursor_start, cursor_end)
                self.pw.setTextCursor(new_cursor)

    def clear_annotations(self):
        if not self.are_we_doing_images_only:
            cursor = self.pw.textCursor()
            cursor.setPosition(0)
            cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)

            previewCharFormat = QtGui.QTextCharFormat()
            previewCharFormat.setFontStyleStrategy(
                QtGui.QFont.PreferAntialias)
            cursor.setCharFormat(previewCharFormat)
            cursor.clearSelection()
            self.pw.setTextCursor(cursor)

    def annotation_specific(self, mode, annotation_type, chapter, cursor_position):
        try:
            chapter_annotations = self.pw.annotation_dict[chapter]
        except KeyError:
            return False

        for i in chapter_annotations:
            if annotation_type == 'text':
                cursor_start = i['cursor'][0]
                cursor_end = i['cursor'][1]

                if cursor_start <= cursor_position <= cursor_end:
                    if mode == 'check':
                        return True
                    if mode == 'delete':
                        self.pw.annotation_dict[chapter].remove(i)
                    if mode == 'note':
                        note = i['note']
                        self.pw.parent.annotationNoteDock.set_annotation(i)
                        self.pw.parent.annotationNoteEdit.setText(note)
                        self.pw.parent.annotationNoteDock.show()

        # Post iteration
        if mode == 'check':
            return False
        if mode == 'delete':
            scroll_position = self.pw.verticalScrollBar().value()
            self.clear_annotations()
            self.load_annotations(chapter)
            self.pw.verticalScrollBar().setValue(scroll_position)

    def update_model(self):
        # We're updating the underlying model to have real-time
        # updates on the read status

        # Set a baseline model index in case the item gets deleted
        # E.g It's open in a tab and deleted from the library
        model_index = None
        start_index = self.main_window.lib_ref.libraryModel.index(0, 0)

        # Find index of the model item that corresponds to the tab
        model_index = self.main_window.lib_ref.libraryModel.match(
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

        # Update position percentage
        if model_index:
            self.main_window.lib_ref.libraryModel.setData(
                model_index[0], position_percentage, QtCore.Qt.UserRole + 7)

    def generate_combo_box_action(self, contextMenu):
        contextMenu.addSeparator()

        tocCombobox = QtWidgets.QComboBox()
        toc_data = [i[0] for i in self.pw.parent.metadata['content']]
        tocCombobox.addItems(toc_data)
        tocCombobox.setCurrentIndex(
            self.pw.main_window.bookToolBar.tocBox.currentIndex())
        tocCombobox.currentIndexChanged.connect(
            self.pw.main_window.bookToolBar.tocBox.setCurrentIndex)

        comboboxAction = QtWidgets.QWidgetAction(self.pw)
        comboboxAction.setDefaultWidget(tocCombobox)
        contextMenu.addAction(comboboxAction)
