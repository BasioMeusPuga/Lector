#!/usr/bin/env python3

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

import os
import sys
import hashlib
from PyQt5 import QtWidgets, QtGui, QtCore

from lector import database
from lector import sorter
from lector.toolbars import LibraryToolBar, BookToolBar
from lector.widgets import Tab
from lector.delegates import LibraryDelegate
from lector.threaded import BackGroundTabUpdate, BackGroundBookAddition, BackGroundBookDeletion
from lector.library import Library
from lector.settings import Settings
from lector.settingsdialog import SettingsUI
from lector.metadatadialog import MetadataUI
from lector.definitionsdialog import DefinitionsUI

from resources import mainwindow


class MainUI(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        self.setupUi(self)

        # Empty variables that will be infested soon
        self.settings = {}
        self.thread = None  # Background Thread
        self.current_contentView = None  # For fullscreening purposes
        self.display_profiles = None
        self.current_profile_index = None
        self.comic_profile = {}
        self.database_path = None
        self.active_library_filters = []

        # Initialize toolbars
        self.libraryToolBar = LibraryToolBar(self)
        self.bookToolBar = BookToolBar(self)

        # Widget declarations
        self.libraryFilterMenu = QtWidgets.QMenu()
        self.statusMessage = QtWidgets.QLabel()
        self.toolbarToggle = QtWidgets.QToolButton()
        self.reloadLibrary = QtWidgets.QToolButton()

        # Initialize application
        Settings(self).read_settings()  # This should populate all variables that need
                                        # to be remembered across sessions

        # Create the database in case it doesn't exist
        database.DatabaseInit(self.database_path)

        # Initialize settings dialog
        self.settingsDialog = SettingsUI(self)

        # Initialize metadata dialog
        self.metadataDialog = MetadataUI(self)

        # Initialize definition view dialog
        self.definitionDialog = DefinitionsUI(self)

        # Statusbar widgets
        self.statusMessage.setObjectName('statusMessage')
        self.statusBar.addPermanentWidget(self.statusMessage)
        self.sorterProgress = QtWidgets.QProgressBar()
        self.sorterProgress.setMaximumWidth(300)
        self.sorterProgress.setObjectName('sorterProgress')
        sorter.progressbar = self.sorterProgress  # This is so that updates can be
                                                  # connected to setValue
        self.statusBar.addWidget(self.sorterProgress)
        self.sorterProgress.setVisible(False)

        # Statusbar - Toolbar Visibility
        self.toolbarToggle.setIcon(QtGui.QIcon.fromTheme('visibility'))
        self.toolbarToggle.setObjectName('toolbarToggle')
        self.toolbarToggle.setToolTip('Toggle toolbar')
        self.toolbarToggle.setAutoRaise(True)
        self.toolbarToggle.clicked.connect(self.toggle_toolbars)
        self.statusBar.addPermanentWidget(self.toolbarToggle)

        # THIS IS TEMPORARY
        self.guiTest = QtWidgets.QToolButton()
        self.guiTest.setIcon(QtGui.QIcon.fromTheme('mail-thread-watch'))
        self.guiTest.setObjectName('guiTest')
        self.guiTest.setToolTip('Test Function')
        self.guiTest.setAutoRaise(True)
        self.guiTest.clicked.connect(self.test_function)
        self.statusBar.addPermanentWidget(self.guiTest)

        # Application wide temporary directory
        self.temp_dir = QtCore.QTemporaryDir()

        # Init the culling timer
        self.culling_timer = QtCore.QTimer()
        self.culling_timer.setSingleShot(True)
        self.culling_timer.timeout.connect(self.cull_covers)

        # Init the Library
        self.lib_ref = Library(self)

        # Toolbar display
        # Maybe make this a persistent option
        self.settings['show_toolbars'] = True

        # Library toolbar
        self.libraryToolBar.addButton.triggered.connect(self.add_books)
        self.libraryToolBar.deleteButton.triggered.connect(self.delete_books)
        self.libraryToolBar.coverViewButton.triggered.connect(self.switch_library_view)
        self.libraryToolBar.tableViewButton.triggered.connect(self.switch_library_view)
        self.libraryToolBar.colorButton.triggered.connect(self.get_color)
        self.libraryToolBar.settingsButton.triggered.connect(self.show_settings)
        self.libraryToolBar.searchBar.textChanged.connect(self.lib_ref.update_proxymodels)
        self.libraryToolBar.sortingBox.activated.connect(self.lib_ref.update_proxymodels)
        self.libraryToolBar.libraryFilterButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.addToolBar(self.libraryToolBar)

        if self.settings['current_view'] == 0:
            self.libraryToolBar.coverViewButton.trigger()
        else:
            self.libraryToolBar.tableViewButton.trigger()

        # Book toolbar
        self.bookToolBar.addBookmarkButton.triggered.connect(self.add_bookmark)
        self.bookToolBar.bookmarkButton.triggered.connect(self.toggle_dock_widget)
        self.bookToolBar.fullscreenButton.triggered.connect(self.set_fullscreen)

        for count, i in enumerate(self.display_profiles):
            self.bookToolBar.profileBox.setItemData(count, i, QtCore.Qt.UserRole)
        self.bookToolBar.profileBox.currentIndexChanged.connect(self.format_contentView)
        self.bookToolBar.profileBox.setCurrentIndex(self.current_profile_index)

        self.bookToolBar.fontBox.currentFontChanged.connect(self.modify_font)
        self.bookToolBar.fontSizeBox.currentIndexChanged.connect(self.modify_font)
        self.bookToolBar.lineSpacingUp.triggered.connect(self.modify_font)
        self.bookToolBar.lineSpacingDown.triggered.connect(self.modify_font)
        self.bookToolBar.paddingUp.triggered.connect(self.modify_font)
        self.bookToolBar.paddingDown.triggered.connect(self.modify_font)
        self.bookToolBar.resetProfile.triggered.connect(self.reset_profile)

        self.alignment_dict = {
            'left': self.bookToolBar.alignLeft,
            'right': self.bookToolBar.alignRight,
            'center': self.bookToolBar.alignCenter,
            'justify': self.bookToolBar.alignJustify}

        profile_index = self.bookToolBar.profileBox.currentIndex()
        current_profile = self.bookToolBar.profileBox.itemData(
            profile_index, QtCore.Qt.UserRole)
        for i in self.alignment_dict.items():
            i[1].triggered.connect(self.modify_font)
        self.alignment_dict[current_profile['text_alignment']].setChecked(True)

        self.bookToolBar.zoomIn.triggered.connect(self.modify_comic_view)
        self.bookToolBar.zoomOut.triggered.connect(self.modify_comic_view)
        self.bookToolBar.fitWidth.triggered.connect(self.modify_comic_view)
        self.bookToolBar.bestFit.triggered.connect(self.modify_comic_view)
        self.bookToolBar.originalSize.triggered.connect(self.modify_comic_view)
        self.bookToolBar.comicBGColor.clicked.connect(self.get_color)

        self.bookToolBar.colorBoxFG.clicked.connect(self.get_color)
        self.bookToolBar.colorBoxBG.clicked.connect(self.get_color)
        self.bookToolBar.tocBox.currentIndexChanged.connect(self.set_toc_position)
        self.addToolBar(self.bookToolBar)

        # Make the correct toolbar visible
        self.current_tab = self.tabWidget.currentIndex()
        self.tab_switch()
        self.tabWidget.currentChanged.connect(self.tab_switch)

        # Tab closing
        self.tabWidget.setTabsClosable(True)

        # Get list of available parsers
        self.available_parsers = '*.' + ' *.'.join(sorter.available_parsers)
        print('Available parsers: ' + self.available_parsers)

        # The library refresh button on the Library tab
        self.reloadLibrary.setIcon(QtGui.QIcon.fromTheme('reload'))
        self.reloadLibrary.setObjectName('reloadLibrary')
        self.reloadLibrary.setAutoRaise(True)
        self.reloadLibrary.clicked.connect(self.settingsDialog.start_library_scan)

        self.tabWidget.tabBar().setTabButton(
            0, QtWidgets.QTabBar.RightSide, self.reloadLibrary)
        self.tabWidget.tabCloseRequested.connect(self.tab_close)

        # Init display models
        self.lib_ref.generate_model('build')
        self.lib_ref.generate_proxymodels()
        self.lib_ref.generate_library_tags()
        self.set_library_filter()
        self.start_culling_timer()

        # ListView
        self.listView.setGridSize(QtCore.QSize(175, 240))
        self.listView.setMouseTracking(True)
        self.listView.verticalScrollBar().setSingleStep(9)
        self.listView.doubleClicked.connect(self.library_doubleclick)
        self.listView.setItemDelegate(LibraryDelegate(self.temp_dir.path(), self))
        self.listView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listView.customContextMenuRequested.connect(self.generate_library_context_menu)
        self.listView.verticalScrollBar().valueChanged.connect(self.start_culling_timer)

        self.listView.setStyleSheet(
            "QListView {{background-color: {0}}}".format(
                self.settings['listview_background'].name()))

        # TODO
        # Maybe use this for readjusting the border of the focus rectangle
        # in the listView. Maybe this is a job for QML?

        # self.listView.setStyleSheet(
        #     "QListView::item:selected { border-color:blue; border-style:outset;"
        #     "border-width:2px; color:black; }")

        # TableView
        self.tableView.doubleClicked.connect(self.library_doubleclick)
        self.tableView.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        self.tableView.horizontalHeader().setSortIndicator(
            2, QtCore.Qt.AscendingOrder)
        self.tableView.setColumnHidden(0, True)
        self.tableView.horizontalHeader().setHighlightSections(False)
        if self.settings['main_window_headers']:
            for count, i in enumerate(self.settings['main_window_headers']):
                self.tableView.horizontalHeader().resizeSection(count, int(i))
        self.tableView.horizontalHeader().resizeSection(4, 1)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.horizontalHeader().sectionClicked.connect(
            self.lib_ref.table_proxy_model.sort_table_columns)
        self.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.generate_library_context_menu)

        # Keyboard shortcuts
        self.ksCloseTab = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+W'), self)
        self.ksCloseTab.setContext(QtCore.Qt.ApplicationShortcut)
        self.ksCloseTab.activated.connect(self.tab_close)

        self.ksExitAll = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.ksExitAll.setContext(QtCore.Qt.ApplicationShortcut)
        self.ksExitAll.activated.connect(self.closeEvent)

        self.listView.setFocus()
        self.open_books_at_startup()

        # Scan the library @ startup
        if self.settings['scan_library']:
            self.settingsDialog.start_library_scan()

    def open_books_at_startup(self):
        # Last open books and command line books aren't being opened together
        # so that command line books are processed last and therefore retain focus

        # Open last... open books.
        # Then set the value to None for the next run
        if self.settings['last_open_books']:
            files_to_open = {i: None for i in self.settings['last_open_books']}
            self.open_files(files_to_open)
        else:
            self.settings['last_open_tab'] = None

        # Open input files if specified
        cl_parser = QtCore.QCommandLineParser()
        cl_parser.process(QtWidgets.qApp)
        my_args = cl_parser.positionalArguments()
        if my_args:
            file_list = [QtCore.QFileInfo(i).absoluteFilePath() for i in my_args]
            books = sorter.BookSorter(
                file_list,
                'addition',
                self.database_path,
                self.settings['auto_tags'],
                self.temp_dir.path())

            parsed_books = books.initiate_threads()
            database.DatabaseFunctions(self.database_path).add_to_database(parsed_books)
            self.lib_ref.generate_model('addition', parsed_books, True)

            file_dict = {QtCore.QFileInfo(i).absoluteFilePath(): None for i in my_args}
            self.open_files(file_dict)

            self.move_on()

    def cull_covers(self, event=None):
        blank_pixmap = QtGui.QPixmap()
        blank_pixmap.load(':/images/blank.png')  # Keep this. Removing it causes the
                                                 # listView to go blank on a resize

        all_indexes = set()
        for i in range(self.lib_ref.item_proxy_model.rowCount()):
            all_indexes.add(self.lib_ref.item_proxy_model.index(i, 0))

        y_range = list(range(0, self.listView.viewport().height(), 100))
        y_range.extend((-20, self.listView.viewport().height() + 20))
        x_range = range(0, self.listView.viewport().width(), 80)

        visible_indexes = set()
        for i in y_range:
            for j in x_range:
                this_index = self.listView.indexAt(QtCore.QPoint(j, i))
                visible_indexes.add(this_index)

        invisible_indexes = all_indexes - visible_indexes
        for i in invisible_indexes:
            model_index = self.lib_ref.item_proxy_model.mapToSource(i)
            this_item = self.lib_ref.view_model.item(model_index.row())

            if this_item:
                this_item.setIcon(QtGui.QIcon(blank_pixmap))
                this_item.setData(False, QtCore.Qt.UserRole + 8)

        hash_index_dict = {}
        hash_list = []
        for i in visible_indexes:
            model_index = self.lib_ref.item_proxy_model.mapToSource(i)

            book_hash = self.lib_ref.view_model.data(
                model_index, QtCore.Qt.UserRole + 6)
            cover_displayed = self.lib_ref.view_model.data(
                model_index, QtCore.Qt.UserRole + 8)

            if book_hash and not cover_displayed:
                hash_list.append(book_hash)
                hash_index_dict[book_hash] = model_index

        all_covers = database.DatabaseFunctions(
            self.database_path).fetch_covers_only(hash_list)

        for i in all_covers:
            book_hash = i[0]
            cover = i[1]
            model_index = hash_index_dict[book_hash]

            book_item = self.lib_ref.view_model.item(model_index.row())
            self.cover_loader(book_item, cover)

    def start_culling_timer(self):
        if self.settings['perform_culling']:
            self.culling_timer.start(30)

    def load_all_covers(self):
        all_covers_db = database.DatabaseFunctions(
            self.database_path).fetch_data(
                ('Hash', 'CoverImage',),
                'books',
                {'Hash': ''},
                'LIKE')

        all_covers = {
            i[0]: i[1] for i in all_covers_db}

        for i in range(self.lib_ref.view_model.rowCount()):
            this_item = self.lib_ref.view_model.item(i, 0)

            is_cover_already_displayed = this_item.data(QtCore.Qt.UserRole + 8)
            if is_cover_already_displayed:
                continue

            book_hash = this_item.data(QtCore.Qt.UserRole + 6)
            cover = all_covers[book_hash]
            self.cover_loader(this_item, cover)

    def cover_loader(self, item, cover):
        img_pixmap = QtGui.QPixmap()
        if cover:
            img_pixmap.loadFromData(cover)
        else:
            img_pixmap.load(':/images/NotFound.png')
        img_pixmap = img_pixmap.scaled(420, 600, QtCore.Qt.IgnoreAspectRatio)
        item.setIcon(QtGui.QIcon(img_pixmap))
        item.setData(True, QtCore.Qt.UserRole + 8)

    def add_bookmark(self):
        if self.tabWidget.currentIndex() != 0:
            self.tabWidget.widget(self.tabWidget.currentIndex()).add_bookmark()

    def test_function(self):
        print('Caesar si viveret, ad remum dareris')

    def resizeEvent(self, event=None):
        if event:
            # This implies a vertical resize event only
            # We ain't about that lifestyle
            if event.oldSize().width() == event.size().width():
                return

        # The hackiness of this hack is just...
        default_size = 170  # This is size of the QIcon (160 by default) +
                            # minimum margin is needed between thumbnails

        # for n icons, the n + 1th icon will appear at > n +1.11875
        # First, calculate the number of images per row
        i = self.listView.viewport().width() / default_size
        rem = i - int(i)
        if rem >= .11875 and rem <= .9999:
            num_images = int(i)
        else:
            num_images = int(i) - 1

        # The rest is illustrated using informative variable names
        space_occupied = num_images * default_size
        # 12 is the scrollbar width
        # Larger numbers keep reduce flickering but also increase
        # the distance from the scrollbar
        space_left = (
            self.listView.viewport().width() - space_occupied - 19)
        try:
            layout_extra_space_per_image = space_left // num_images
            self.listView.setGridSize(
                QtCore.QSize(default_size + layout_extra_space_per_image, 250))
            self.start_culling_timer()
        except ZeroDivisionError:  # Initial resize is ignored
            return

    def add_books(self):
        # TODO
        # Remember file addition modality
        # If a file is added from here, it should not be removed
        # from the libary in case of a database refresh

        opened_files = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open file', self.settings['last_open_path'],
            f'eBooks ({self.available_parsers})')

        if not opened_files[0]:
            return

        self.settingsDialog.okButton.setEnabled(False)
        self.reloadLibrary.setEnabled(False)

        self.settings['last_open_path'] = os.path.dirname(opened_files[0][0])
        self.sorterProgress.setVisible(True)
        self.statusMessage.setText('Adding books...')
        self.thread = BackGroundBookAddition(
            opened_files[0], self.database_path, False, self)
        self.thread.finished.connect(self.move_on)
        self.thread.start()

    def get_selection(self, library_widget):
        selected_indexes = None

        if library_widget == self.listView:
            selected_books = self.lib_ref.item_proxy_model.mapSelectionToSource(
                self.listView.selectionModel().selection())
            selected_indexes = [i.indexes()[0] for i in selected_books]

        elif library_widget == self.tableView:
            selected_books = self.tableView.selectionModel().selectedRows()
            selected_indexes = [
                self.lib_ref.table_proxy_model.mapToSource(i) for i in selected_books]

        return selected_indexes

    def delete_books(self, selected_indexes=None):
        # TODO
        # ? Mirror selection
        # Ask if library files are to be excluded from further scans
        # Make a checkbox for this

        if not selected_indexes:
            # Get a list of QItemSelection objects
            # What we're interested in is the indexes()[0] in each of them
            # That gives a list of indexes from the view model
            if self.listView.isVisible():
                selected_indexes = self.get_selection(self.listView)

            elif self.tableView.isVisible():
                selected_indexes = self.get_selection(self.tableView)

        if not selected_indexes:
            return

        # Deal with message box selection
        def ifcontinue(box_button):
            if box_button.text() != '&Yes':
                return

            # Persistent model indexes are required beause deletion mutates the model
            # Generate and delete by persistent index
            delete_hashes = [
                self.lib_ref.view_model.data(
                    i, QtCore.Qt.UserRole + 6) for i in selected_indexes]
            persistent_indexes = [QtCore.QPersistentModelIndex(i) for i in selected_indexes]

            for i in persistent_indexes:
                self.lib_ref.view_model.removeRow(i.row())

            # Update the database in the background
            self.thread = BackGroundBookDeletion(
                delete_hashes, self.database_path, self)
            self.thread.finished.connect(self.move_on)
            self.thread.start()

        # Generate a message box to confirm deletion
        selected_number = len(selected_indexes)
        confirm_deletion = QtWidgets.QMessageBox()
        confirm_deletion.setText('Delete %d book(s)?' % selected_number)
        confirm_deletion.setIcon(QtWidgets.QMessageBox.Question)
        confirm_deletion.setWindowTitle('Confirm deletion')
        confirm_deletion.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        confirm_deletion.buttonClicked.connect(ifcontinue)
        confirm_deletion.show()
        confirm_deletion.exec_()

    def move_on(self):
        self.settingsDialog.okButton.setEnabled(True)
        self.settingsDialog.okButton.setToolTip(
            'Save changes and start library scan')
        self.reloadLibrary.setEnabled(True)

        self.sorterProgress.setVisible(False)
        self.sorterProgress.setValue(0)

        self.lib_ref.update_proxymodels()
        self.lib_ref.generate_library_tags()

        if not self.settings['perform_culling']:
            self.load_all_covers()

    def switch_library_view(self):
        if self.libraryToolBar.coverViewButton.isChecked():
            self.stackedWidget.setCurrentIndex(0)
            self.libraryToolBar.sortingBoxAction.setVisible(True)
        else:
            self.stackedWidget.setCurrentIndex(1)
            self.libraryToolBar.sortingBoxAction.setVisible(False)

        self.resizeEvent()

    def tab_switch(self):
        try:
            if self.current_tab != 0:
                self.tabWidget.widget(
                    self.current_tab).update_last_accessed_time()
        except AttributeError:
            pass

        self.current_tab = self.tabWidget.currentIndex()

        if self.tabWidget.currentIndex() == 0:

            self.resizeEvent()
            self.start_culling_timer()
            if self.settings['show_toolbars']:
                self.bookToolBar.hide()
                self.libraryToolBar.show()

            if self.lib_ref.item_proxy_model:
                # Making the proxy model available doesn't affect
                # memory utilization at all. Bleh.
                self.statusMessage.setText(
                    str(self.lib_ref.item_proxy_model.rowCount()) + ' Books')
        else:

            if self.settings['show_toolbars']:
                self.bookToolBar.show()
                self.libraryToolBar.hide()

            current_tab = self.tabWidget.widget(
                self.tabWidget.currentIndex())
            current_metadata = current_tab.metadata

            if self.bookToolBar.fontButton.isChecked():
                self.bookToolBar.customize_view_on()

            current_title = current_metadata['title']
            current_author = current_metadata['author']
            current_position = current_metadata['position']
            current_toc = [i[0] for i in current_metadata['content']]

            self.bookToolBar.tocBox.blockSignals(True)
            self.bookToolBar.tocBox.clear()
            self.bookToolBar.tocBox.addItems(current_toc)
            if current_position:
                self.bookToolBar.tocBox.setCurrentIndex(
                    current_position['current_chapter'] - 1)
                if not current_metadata['images_only']:
                    current_tab.set_scroll_value(False)
            self.bookToolBar.tocBox.blockSignals(False)

            self.format_contentView()

            self.statusMessage.setText(
                current_author + ' - ' + current_title)

    def tab_close(self, tab_index=None):
        if not tab_index:
            tab_index = self.tabWidget.currentIndex()
            if tab_index == 0:
                return

        tab_metadata = self.tabWidget.widget(tab_index).metadata

        self.thread = BackGroundTabUpdate(
            self.database_path, [tab_metadata])
        self.thread.start()

        self.tabWidget.widget(tab_index).update_last_accessed_time()
        self.tabWidget.removeTab(tab_index)

    def set_toc_position(self, event=None):
        current_tab = self.tabWidget.widget(self.tabWidget.currentIndex())

        # We're updating the underlying model to have real-time
        # updates on the read status

        # Set a baseline model index in case the item gets deleted
        # E.g It's open in a tab and deleted from the library
        model_index = None
        start_index = self.lib_ref.view_model.index(0, 0)
        # Find index of the model item that corresponds to the tab
        matching_item = self.lib_ref.view_model.match(
            start_index,
            QtCore.Qt.UserRole + 6,
            current_tab.metadata['hash'],
            1, QtCore.Qt.MatchExactly)
        if matching_item:
            model_row = matching_item[0].row()
            model_index = self.lib_ref.view_model.index(model_row, 0)

        current_tab.metadata[
            'position']['current_chapter'] = event + 1
        current_tab.metadata[
            'position']['is_read'] = False

        # TODO
        # This doesn't update correctly
        # try:
        #     position_perc = (
        #         current_tab.metadata[
        #             'current_chapter'] * 100 / current_tab.metadata['total_chapters'])
        # except KeyError:
        #     position_perc = None

        if model_index:
            self.lib_ref.view_model.setData(
                model_index, current_tab.metadata, QtCore.Qt.UserRole + 3)
            # self.lib_ref.view_model.setData(
            #     model_index, position_perc, QtCore.Qt.UserRole + 7)

        # Go on to change the value of the Table of Contents box
        current_tab.change_chapter_tocBox()
        self.format_contentView()

    def set_fullscreen(self):
        current_tab = self.tabWidget.currentIndex()
        current_tab_widget = self.tabWidget.widget(current_tab)
        current_tab_widget.go_fullscreen()

    def toggle_dock_widget(self):
        sender = self.sender().objectName()
        current_tab = self.tabWidget.currentIndex()
        current_tab_widget = self.tabWidget.widget(current_tab)

        # TODO
        # Extend this to other context related functions
        # Make this fullscreenable

        if sender == 'bookmarkButton':
            current_tab_widget.toggle_bookmarks()

    def library_doubleclick(self, index):
        sender = self.sender().objectName()

        if sender == 'listView':
            source_index = self.lib_ref.item_proxy_model.mapToSource(index)
        elif sender == 'tableView':
            source_index = self.lib_ref.table_proxy_model.mapToSource(index)

        item = self.lib_ref.view_model.item(source_index.row(), 0)
        metadata = item.data(QtCore.Qt.UserRole + 3)
        path = {metadata['path']: metadata['hash']}

        self.open_files(path)

    def open_files(self, path_hash_dictionary):
        # file_paths is expected to be a dictionary
        # This allows for threading file opening
        # Which should speed up multiple file opening
        # especially @ application start

        file_paths = [i for i in path_hash_dictionary]

        for filename in path_hash_dictionary.items():

            file_md5 = filename[1]
            if not file_md5:
                try:
                    with open(filename[0], 'rb') as current_book:
                        first_bytes = current_book.read(1024 * 32)  # First 32KB of the file
                        file_md5 = hashlib.md5(first_bytes).hexdigest()
                except FileNotFoundError:
                    return

            # Remove any already open files
            # Set focus to last file in case only one is open
            for i in range(1, self.tabWidget.count()):
                tab_metadata = self.tabWidget.widget(i).metadata
                if tab_metadata['hash'] == file_md5:
                    file_paths.remove(filename[0])
                    if not file_paths:
                        self.tabWidget.setCurrentIndex(i)
                        return

        if not file_paths:
            return

        def finishing_touches():
            self.format_contentView()
            self.start_culling_timer()

        print('Attempting to open: ' + ', '.join(file_paths))

        contents = sorter.BookSorter(
            file_paths,
            'reading',
            self.database_path,
            True,
            self.temp_dir.path()).initiate_threads()

        for i in contents:
            # New tabs are created here
            # Initial position adjustment is carried out by the tab itself
            file_data = contents[i]
            Tab(file_data, self.tabWidget)

        if self.settings['last_open_tab'] == 'library':
            self.tabWidget.setCurrentIndex(0)
            self.listView.setFocus()
            self.settings['last_open_tab'] = None
            return

        for i in range(1, self.tabWidget.count()):
            this_path = self.tabWidget.widget(i).metadata['path']
            if self.settings['last_open_tab'] == this_path:
                self.tabWidget.setCurrentIndex(i)
                self.settings['last_open_tab'] = None
                finishing_touches()
                return

        self.tabWidget.setCurrentIndex(self.tabWidget.count() - 1)
        finishing_touches()

    # TODO
    # def dropEvent

    def get_color(self):
        def open_color_dialog(current_color):
            color_dialog = QtWidgets.QColorDialog()
            new_color = color_dialog.getColor(current_color)
            if new_color.isValid():  # Returned in case cancel is pressed
                return new_color
            else:
                return current_color

        signal_sender = self.sender().objectName()

        # Special cases that don't affect (comic)book display
        if signal_sender == 'libraryBackground':
            current_color = self.settings['listview_background']
            new_color = open_color_dialog(current_color)
            self.listView.setStyleSheet("QListView {{background-color: {0}}}".format(
                new_color.name()))
            self.settings['listview_background'] = new_color
            return

        if signal_sender == 'dialogBackground':
            current_color = self.settings['dialog_background']
            new_color = open_color_dialog(current_color)
            self.settings['dialog_background'] = new_color
            return new_color

        profile_index = self.bookToolBar.profileBox.currentIndex()
        current_profile = self.bookToolBar.profileBox.itemData(
            profile_index, QtCore.Qt.UserRole)

        # Retain current values on opening a new dialog
        if signal_sender == 'fgColor':
            current_color = current_profile['foreground']
            new_color = open_color_dialog(current_color)
            self.bookToolBar.colorBoxFG.setStyleSheet(
                'background-color: %s' % new_color.name())
            current_profile['foreground'] = new_color

        elif signal_sender == 'bgColor':
            current_color = current_profile['background']
            new_color = open_color_dialog(current_color)
            self.bookToolBar.colorBoxBG.setStyleSheet(
                'background-color: %s' % new_color.name())
            current_profile['background'] = new_color

        elif signal_sender == 'comicBGColor':
            current_color = self.comic_profile['background']
            new_color = open_color_dialog(current_color)
            self.bookToolBar.comicBGColor.setStyleSheet(
                'background-color: %s' % new_color.name())
            self.comic_profile['background'] = new_color

        self.bookToolBar.profileBox.setItemData(
            profile_index, current_profile, QtCore.Qt.UserRole)
        self.format_contentView()

    def modify_font(self):
        signal_sender = self.sender().objectName()
        profile_index = self.bookToolBar.profileBox.currentIndex()
        current_profile = self.bookToolBar.profileBox.itemData(
            profile_index, QtCore.Qt.UserRole)

        if signal_sender == 'fontBox':
            current_profile['font'] = self.bookToolBar.fontBox.currentFont().family()

        if signal_sender == 'fontSizeBox':
            old_size = current_profile['font_size']
            new_size = self.bookToolBar.fontSizeBox.itemText(
                self.bookToolBar.fontSizeBox.currentIndex())
            if new_size.isdigit():
                current_profile['font_size'] = new_size
            else:
                current_profile['font_size'] = old_size

        if signal_sender == 'lineSpacingUp' and current_profile['line_spacing'] < 200:
            current_profile['line_spacing'] += 5
        if signal_sender == 'lineSpacingDown' and current_profile['line_spacing'] > 90:
            current_profile['line_spacing'] -= 5

        if signal_sender == 'paddingUp':
            current_profile['padding'] += 5
        if signal_sender == 'paddingDown':
            current_profile['padding'] -= 5

        alignment_dict = {
            'alignLeft': 'left',
            'alignRight': 'right',
            'alignCenter': 'center',
            'alignJustify': 'justify'}
        if signal_sender in alignment_dict:
            current_profile['text_alignment'] = alignment_dict[signal_sender]

        self.bookToolBar.profileBox.setItemData(
            profile_index, current_profile, QtCore.Qt.UserRole)
        self.format_contentView()

    def modify_comic_view(self):
        signal_sender = self.sender().objectName()
        current_tab = self.tabWidget.widget(self.tabWidget.currentIndex())

        self.bookToolBar.fitWidth.setChecked(False)
        self.bookToolBar.bestFit.setChecked(False)
        self.bookToolBar.originalSize.setChecked(False)

        if signal_sender == 'zoomOut':
            self.comic_profile['zoom_mode'] = 'manualZoom'
            self.comic_profile['padding'] += 50

            # This prevents infinite zoom out
            if self.comic_profile['padding'] * 2 > current_tab.contentView.viewport().width():
                self.comic_profile['padding'] -= 50

        if signal_sender == 'zoomIn':
            self.comic_profile['zoom_mode'] = 'manualZoom'
            self.comic_profile['padding'] -= 50

            # This prevents infinite zoom in
            if self.comic_profile['padding'] < 0:
                self.comic_profile['padding'] = 0

        if signal_sender == 'fitWidth':
            self.comic_profile['zoom_mode'] = 'fitWidth'
            self.comic_profile['padding'] = 0
            self.bookToolBar.fitWidth.setChecked(True)

        # Padding in the following cases is decided by
        # the image pixmap loaded by the widget
        if signal_sender == 'bestFit':
            self.comic_profile['zoom_mode'] = 'bestFit'
            self.bookToolBar.bestFit.setChecked(True)

        if signal_sender == 'originalSize':
            self.comic_profile['zoom_mode'] = 'originalSize'
            self.bookToolBar.originalSize.setChecked(True)

        self.format_contentView()

    def format_contentView(self):
        # TODO
        # See what happens if a font isn't installed

        current_tab = self.tabWidget.widget(self.tabWidget.currentIndex())

        try:
            current_metadata = current_tab.metadata
        except AttributeError:
            return

        if current_metadata['images_only']:
            background = self.comic_profile['background']
            padding = self.comic_profile['padding']
            zoom_mode = self.comic_profile['zoom_mode']

            if zoom_mode == 'fitWidth':
                self.bookToolBar.fitWidth.setChecked(True)
            if zoom_mode == 'bestFit':
                self.bookToolBar.bestFit.setChecked(True)
            if zoom_mode == 'originalSize':
                self.bookToolBar.originalSize.setChecked(True)

            self.bookToolBar.comicBGColor.setStyleSheet(
                'background-color: %s' % background.name())

            current_tab.format_view(
                None, None, None, background, padding, None, None)

        else:
            profile_index = self.bookToolBar.profileBox.currentIndex()
            current_profile = self.bookToolBar.profileBox.itemData(
                profile_index, QtCore.Qt.UserRole)

            font = current_profile['font']
            foreground = current_profile['foreground']
            background = current_profile['background']
            padding = current_profile['padding']
            font_size = current_profile['font_size']
            line_spacing = current_profile['line_spacing']
            text_alignment = current_profile['text_alignment']

            # Change toolbar widgets to match new settings
            self.bookToolBar.fontBox.blockSignals(True)
            self.bookToolBar.fontSizeBox.blockSignals(True)
            self.bookToolBar.fontBox.setCurrentText(font)
            current_index = self.bookToolBar.fontSizeBox.findText(
                str(font_size), QtCore.Qt.MatchExactly)
            self.bookToolBar.fontSizeBox.setCurrentIndex(current_index)
            self.bookToolBar.fontBox.blockSignals(False)
            self.bookToolBar.fontSizeBox.blockSignals(False)

            self.alignment_dict[current_profile['text_alignment']].setChecked(True)

            self.bookToolBar.colorBoxFG.setStyleSheet(
                'background-color: %s' % foreground.name())
            self.bookToolBar.colorBoxBG.setStyleSheet(
                'background-color: %s' % background.name())

            current_tab.format_view(
                font, font_size, foreground,
                background, padding, line_spacing,
                text_alignment)

    def reset_profile(self):
        current_profile_index = self.bookToolBar.profileBox.currentIndex()
        current_profile_default = Settings(self).default_profiles[current_profile_index]
        self.bookToolBar.profileBox.setItemData(
            current_profile_index, current_profile_default, QtCore.Qt.UserRole)
        self.format_contentView()

    def show_settings(self):
        if not self.settingsDialog.isVisible():
            self.settingsDialog.show()
        else:
            self.settingsDialog.hide()

    def generate_library_context_menu(self, position):
        index = self.sender().indexAt(position)
        if not index.isValid():
            return

        # It's worth remembering that these are indexes of the view_model
        # and NOT of the proxy models
        selected_indexes = self.get_selection(self.sender())

        context_menu = QtWidgets.QMenu()

        openAction = context_menu.addAction(
            QtGui.QIcon.fromTheme('view-readermode'), 'Start reading')

        editAction = None
        if len(selected_indexes) == 1:
            editAction = context_menu.addAction(
                QtGui.QIcon.fromTheme('edit-rename'), 'Edit')

        deleteAction = context_menu.addAction(
            QtGui.QIcon.fromTheme('trash-empty'), 'Delete')
        readAction = context_menu.addAction(
            QtGui.QIcon.fromTheme('vcs-normal'), 'Mark read')
        unreadAction = context_menu.addAction(
            QtGui.QIcon.fromTheme('emblem-unavailable'), 'Mark unread')

        action = context_menu.exec_(self.sender().mapToGlobal(position))

        if action == openAction:
            books_to_open = {}
            for i in selected_indexes:
                metadata = self.lib_ref.view_model.data(i, QtCore.Qt.UserRole + 3)
                books_to_open[metadata['path']] = metadata['hash']

            self.open_files(books_to_open)

        if action == editAction:
            edit_book = selected_indexes[0]
            metadata = self.lib_ref.view_model.data(
                edit_book, QtCore.Qt.UserRole + 3)
            is_cover_loaded = self.lib_ref.view_model.data(
                edit_book, QtCore.Qt.UserRole + 8)

            # Loads a cover in case culling is enabled and the table view is visible
            if not is_cover_loaded:
                book_hash = self.lib_ref.view_model.data(
                    edit_book, QtCore.Qt.UserRole + 6)
                book_item = self.lib_ref.view_model.item(edit_book.row())
                book_cover = database.DatabaseFunctions(
                    self.database_path).fetch_covers_only([book_hash])[0][1]
                self.cover_loader(book_item, book_cover)

            cover = self.lib_ref.view_model.item(edit_book.row()).icon()
            title = metadata['title']
            author = metadata['author']
            year = str(metadata['year'])
            tags = metadata['tags']

            self.metadataDialog.load_book(
                cover, title, author, year, tags, edit_book)

            self.metadataDialog.show()

        if action == deleteAction:
            self.delete_books(selected_indexes)

        if action == readAction or action == unreadAction:
            for i in selected_indexes:
                metadata = self.lib_ref.view_model.data(i, QtCore.Qt.UserRole + 3)
                book_hash = self.lib_ref.view_model.data(i, QtCore.Qt.UserRole + 6)
                position = metadata['position']

                if position:
                    if action == readAction:
                        position['is_read'] = True
                        position['scroll_value'] = 1
                    elif action == unreadAction:
                        position['is_read'] = False
                        position['current_chapter'] = 1
                        position['scroll_value'] = 0
                else:
                    position = {}
                    if action == readAction:
                        position['is_read'] = True

                metadata['position'] = position

                position_perc = None
                last_accessed_time = None
                if action == readAction:
                    last_accessed_time = QtCore.QDateTime().currentDateTime()
                    position_perc = 100

                self.lib_ref.view_model.setData(i, metadata, QtCore.Qt.UserRole + 3)
                self.lib_ref.view_model.setData(i, position_perc, QtCore.Qt.UserRole + 7)
                self.lib_ref.view_model.setData(i, last_accessed_time, QtCore.Qt.UserRole + 12)
                self.lib_ref.update_proxymodels()

                database_dict = {
                    'Position': position,
                    'LastAccessed': last_accessed_time}

                database.DatabaseFunctions(
                    self.database_path).modify_metadata(database_dict, book_hash)

    def generate_library_filter_menu(self, directory_list=None):
        self.libraryFilterMenu.clear()

        def generate_name(path_data):
            this_filter = path_data[1]
            if not this_filter:
                this_filter = os.path.basename(
                    path_data[0]).title()
            return this_filter

        filter_actions = []
        filter_list = []
        if directory_list:
            checked = [i for i in directory_list if i[3] == QtCore.Qt.Checked]
            filter_list = list(map(generate_name, checked))
            filter_list.sort()
            filter_list.append('Manually Added')
            filter_actions = [QtWidgets.QAction(i, self.libraryFilterMenu) for i in filter_list]

        filter_all = QtWidgets.QAction('All', self.libraryFilterMenu)
        filter_actions.append(filter_all)
        for i in filter_actions:
            i.setCheckable(True)
            i.setChecked(True)
            i.triggered.connect(self.set_library_filter)

        self.libraryFilterMenu.addActions(filter_actions)
        self.libraryFilterMenu.insertSeparator(filter_all)
        self.libraryToolBar.libraryFilterButton.setMenu(self.libraryFilterMenu)

    def set_library_filter(self, event=None):
        self.active_library_filters = []
        something_was_unchecked = False

        if self.sender():  # Program startup sends a None here
            if self.sender().text() == 'All':
                for i in self.libraryFilterMenu.actions():
                    i.setChecked(self.sender().isChecked())

        for i in self.libraryFilterMenu.actions()[:-2]:
            if i.isChecked():
                self.active_library_filters.append(i.text())
            else:
                something_was_unchecked = True

        if something_was_unchecked:
            self.libraryFilterMenu.actions()[-1].setChecked(False)
        else:
            self.libraryFilterMenu.actions()[-1].setChecked(True)

        self.lib_ref.update_proxymodels()

    def toggle_toolbars(self):
        self.settings['show_toolbars'] = not self.settings['show_toolbars']

        current_tab = self.tabWidget.currentIndex()
        if current_tab == 0:
            self.libraryToolBar.setVisible(
                not self.libraryToolBar.isVisible())
        else:
            self.bookToolBar.setVisible(
                not self.bookToolBar.isVisible())

    def closeEvent(self, event=None):
        if event:
            event.ignore()

        self.hide()
        self.metadataDialog.hide()
        self.settingsDialog.hide()
        self.definitionDialog.hide()
        self.temp_dir.remove()

        self.settings['last_open_books'] = []
        if self.tabWidget.count() > 1:

            # All tabs must be iterated upon here
            all_metadata = []
            for i in range(1, self.tabWidget.count()):
                tab_metadata = self.tabWidget.widget(i).metadata
                all_metadata.append(tab_metadata)

                if self.settings['remember_files']:
                    self.settings['last_open_books'].append(tab_metadata['path'])

            Settings(self).save_settings()
            self.thread = BackGroundTabUpdate(
                self.database_path, all_metadata)
            self.thread.finished.connect(self.database_care)
            self.thread.start()

        else:
            Settings(self).save_settings()
            self.database_care()

    def database_care(self):
        database.DatabaseFunctions(self.database_path).vacuum_database()
        QtWidgets.qApp.exit()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('Lector')  # This is needed for QStandardPaths
                                      # and my own hubris
    form = MainUI()
    form.show()
    form.resizeEvent()
    app.exec_()


if __name__ == '__main__':
    main()
