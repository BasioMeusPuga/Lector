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

# TODO
# Consider using sender().text() instead of sender().objectName()

import os
import sys

from PyQt5 import QtWidgets, QtGui, QtCore

import sorter
import database

from resources import mainwindow, resources
from widgets import LibraryToolBar, BookToolBar, Tab, LibraryDelegate
from threaded import BackGroundTabUpdate, BackGroundBookAddition, BackGroundBookDeletion
from library import Library
from settings import Settings

from settingsdialog import SettingsUI


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
        self.library_filter_menu = None

        # Initialize toolbars
        self.libraryToolBar = LibraryToolBar(self)
        self.bookToolBar = BookToolBar(self)

        # Widget declarations
        self.library_filter_menu = QtWidgets.QMenu()
        self.statusMessage = QtWidgets.QLabel()
        self.toolbarToggle = QtWidgets.QToolButton()
        self.reloadLibrary = QtWidgets.QToolButton()

        # Initialize application
        Settings(self).read_settings()  # This should populate all variables that need
                                        # to be remembered across sessions

        # Create the database in case it doesn't exist
        database.DatabaseInit(self.database_path)

        # Initialize settings dialog
        self.settings_dialog = SettingsUI(self)

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
        self.libraryToolBar.settingsButton.triggered.connect(self.show_settings)
        self.libraryToolBar.searchBar.textChanged.connect(self.lib_ref.update_proxymodel)
        self.libraryToolBar.searchBar.textChanged.connect(self.lib_ref.update_table_proxy_model)
        self.libraryToolBar.sortingBox.activated.connect(self.lib_ref.update_proxymodel)
        self.libraryToolBar.libraryFilterButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.addToolBar(self.libraryToolBar)

        if self.settings['current_view'] == 0:
            self.libraryToolBar.coverViewButton.trigger()
        else:
            self.libraryToolBar.tableViewButton.trigger()

        # Book toolbar
        self.bookToolBar.bookmarkButton.triggered.connect(self.toggle_dock_widget)
        self.bookToolBar.fullscreenButton.triggered.connect(self.set_fullscreen)

        for count, i in enumerate(self.display_profiles):
            self.bookToolBar.profileBox.setItemData(count, i, QtCore.Qt.UserRole)
        self.bookToolBar.profileBox.currentIndexChanged.connect(self.format_contentView)
        self.bookToolBar.profileBox.setCurrentIndex(self.current_profile_index)

        self.bookToolBar.fontBox.currentFontChanged.connect(self.modify_font)
        self.bookToolBar.fontSizeBox.currentTextChanged.connect(self.modify_font)
        self.bookToolBar.lineSpacingUp.triggered.connect(self.modify_font)
        self.bookToolBar.lineSpacingDown.triggered.connect(self.modify_font)
        self.bookToolBar.paddingUp.triggered.connect(self.modify_font)
        self.bookToolBar.paddingDown.triggered.connect(self.modify_font)
        self.bookToolBar.resetProfile.triggered.connect(self.reset_profile)

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
        self.reloadLibrary.clicked.connect(self.settings_dialog.start_library_scan)

        self.tabWidget.tabBar().setTabButton(
            0, QtWidgets.QTabBar.RightSide, self.reloadLibrary)
        self.tabWidget.tabCloseRequested.connect(self.tab_close)

        # Init display models
        self.lib_ref.generate_model('build')
        self.lib_ref.create_table_model()
        self.lib_ref.create_proxymodel()
        self.lib_ref.generate_library_tags()

        # ListView
        self.listView.setGridSize(QtCore.QSize(175, 240))
        self.listView.setMouseTracking(True)
        self.listView.verticalScrollBar().setSingleStep(9)
        self.listView.doubleClicked.connect(self.library_doubleclick)
        self.listView.setItemDelegate(LibraryDelegate(self.temp_dir.path(), self))
        self.listView.verticalScrollBar().valueChanged.connect(self.start_culling_timer)

        # TableView
        self.tableView.doubleClicked.connect(self.library_doubleclick)
        self.tableView.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        self.tableView.horizontalHeader().setSortIndicator(0, QtCore.Qt.AscendingOrder)
        self.tableView.horizontalHeader().setHighlightSections(False)
        if self.settings['main_window_headers']:
            for count, i in enumerate(self.settings['main_window_headers']):
                self.tableView.horizontalHeader().resizeSection(count, int(i))
        self.tableView.horizontalHeader().setStretchLastSection(True)

        # Keyboard shortcuts
        self.ks_close_tab = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+W'), self)
        self.ks_close_tab.setContext(QtCore.Qt.ApplicationShortcut)
        self.ks_close_tab.activated.connect(self.tab_close)

        self.ks_exit_all = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.ks_exit_all.setContext(QtCore.Qt.ApplicationShortcut)
        self.ks_exit_all.activated.connect(self.closeEvent)

        self.listView.setFocus()

        # Open last... open books.
        # Then set the value to None for the next run
        if self.settings['last_open_books']:
            self.open_files(self.settings['last_open_books'])
        else:
            self.settings['last_open_tab'] = None

        # Scan the library @ startup
        if self.settings['scan_library']:
            self.settings_dialog.start_library_scan()

    def cull_covers(self, event=None):
        blank_pixmap = QtGui.QPixmap()
        blank_pixmap.load(':/images/blank.png')

        all_indexes = set()
        for i in range(self.lib_ref.proxy_model.rowCount()):
            all_indexes.add(self.lib_ref.proxy_model.index(i, 0))

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
            model_index = self.lib_ref.proxy_model.mapToSource(i)
            this_item = self.lib_ref.view_model.item(model_index.row())

            if this_item:
                this_item.setIcon(QtGui.QIcon(blank_pixmap))
                this_item.setData(False, QtCore.Qt.UserRole + 8)

        for i in visible_indexes:
            model_index = self.lib_ref.proxy_model.mapToSource(i)
            this_item = self.lib_ref.view_model.item(model_index.row())

            if this_item:
                is_cover_already_displayed = this_item.data(QtCore.Qt.UserRole + 8)
                if is_cover_already_displayed:
                    continue

                book_hash = this_item.data(QtCore.Qt.UserRole + 6)
                cover = database.DatabaseFunctions(
                    self.database_path).fetch_data(
                        ('CoverImage',),
                        'books',
                        {'Hash': book_hash},
                        'EQUALS',
                        True)

                img_pixmap = QtGui.QPixmap()
                if cover:
                    img_pixmap.loadFromData(cover)
                else:
                    img_pixmap.load(':/images/NotFound.png')
                img_pixmap = img_pixmap.scaled(420, 600, QtCore.Qt.IgnoreAspectRatio)
                this_item.setIcon(QtGui.QIcon(img_pixmap))
                this_item.setData(True, QtCore.Qt.UserRole + 8)

    def start_culling_timer(self):
        self.culling_timer.start(30)

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

        self.settings_dialog.okButton.setEnabled(False)
        self.reloadLibrary.setEnabled(False)

        self.settings['last_open_path'] = os.path.dirname(opened_files[0][0])
        self.sorterProgress.setVisible(True)
        self.statusMessage.setText('Adding books...')
        self.thread = BackGroundBookAddition(
            opened_files[0], self.database_path, False, self)
        self.thread.finished.connect(self.move_on)
        self.thread.start()

    def delete_books(self):
        # TODO
        # Implement this for the tableview
        # The same process can be used to mirror selection
        # Ask if library files are to be excluded from further scans
        # Make a checkbox for this

        # Get a list of QItemSelection objects
        # What we're interested in is the indexes()[0] in each of them
        # That gives a list of indexes from the view model
        selected_books = self.lib_ref.proxy_model.mapSelectionToSource(
            self.listView.selectionModel().selection())

        if not selected_books:
            return

        # Deal with message box selection
        def ifcontinue(box_button):
            if box_button.text() != '&Yes':
                return

            # Generate list of selected indexes and deletable hashes
            selected_indexes = [i.indexes() for i in selected_books]
            delete_hashes = [
                self.lib_ref.view_model.data(
                    i[0], QtCore.Qt.UserRole + 6) for i in selected_indexes]

            # Delete the entries from the table model by way of filtering by hash
            self.lib_ref.table_rows = [
                i for i in self.lib_ref.table_rows if i[6] not in delete_hashes]

            # Persistent model indexes are required beause deletion mutates the model
            # Gnerate and delete by persistent index
            persistent_indexes = [
                QtCore.QPersistentModelIndex(i[0]) for i in selected_indexes]
            for i in persistent_indexes:
                self.lib_ref.view_model.removeRow(i.row())

            # Update the database in the background
            self.thread = BackGroundBookDeletion(
                delete_hashes, self.database_path, self)
            self.thread.finished.connect(self.move_on)
            self.thread.start()

        # Generate a message box to confirm deletion
        selected_number = len(selected_books)
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
        self.settings_dialog.okButton.setEnabled(True)
        self.settings_dialog.okButton.setToolTip(
            'Save changes and start library scan')
        self.reloadLibrary.setEnabled(True)

        self.sorterProgress.setVisible(False)
        self.sorterProgress.setValue(0)

        self.lib_ref.create_table_model()
        self.lib_ref.create_proxymodel()
        self.lib_ref.generate_library_tags()

    def switch_library_view(self):
        if self.libraryToolBar.coverViewButton.isChecked():
            self.stackedWidget.setCurrentIndex(0)
            self.libraryToolBar.sortingBoxAction.setVisible(True)
        else:
            self.stackedWidget.setCurrentIndex(1)
            self.libraryToolBar.sortingBoxAction.setVisible(False)

        self.resizeEvent()

    def tab_switch(self):
        if self.tabWidget.currentIndex() == 0:

            self.resizeEvent()
            self.start_culling_timer()
            if self.settings['show_toolbars']:
                self.bookToolBar.hide()
                self.libraryToolBar.show()

            if self.lib_ref.proxy_model:
                # Making the proxy model available doesn't affect
                # memory utilization at all. Bleh.
                self.statusMessage.setText(
                    str(self.lib_ref.proxy_model.rowCount()) + ' Books')
        else:

            if self.settings['show_toolbars']:
                self.bookToolBar.show()
                self.libraryToolBar.hide()

            current_metadata = self.tabWidget.widget(
                self.tabWidget.currentIndex()).metadata

            if self.bookToolBar.fontButton.isChecked():
                self.bookToolBar.customize_view_on()

            current_title = current_metadata['title']
            current_author = current_metadata['author']
            current_position = current_metadata['position']
            current_toc = current_metadata['content'].keys()

            self.bookToolBar.tocBox.blockSignals(True)
            self.bookToolBar.tocBox.clear()
            self.bookToolBar.tocBox.addItems(current_toc)
            if current_position:
                self.bookToolBar.tocBox.setCurrentIndex(
                    current_position['current_chapter'] - 1)
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

        self.tabWidget.removeTab(tab_index)

    def set_toc_position(self, event=None):
        current_tab = self.tabWidget.widget(self.tabWidget.currentIndex())

        # We're updating the underlying models to have real-time
        # updates on the read status
        # Since there are 2 separate models, they will each have to
        # be updated individually

        # The listView model
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

        if model_index:
            self.lib_ref.view_model.setData(
                model_index, current_tab.metadata['position'], QtCore.Qt.UserRole + 7)

        # The tableView model
        model_index = None
        start_index = self.lib_ref.table_model.index(0, 0)
        matching_item = self.lib_ref.table_model.match(
            start_index,
            QtCore.Qt.UserRole + 1,
            current_tab.metadata['hash'],
            1, QtCore.Qt.MatchExactly)

        if matching_item:
            model_row = matching_item[0].row()
            self.lib_ref.table_model.display_data[model_row][5][
                'position'] = current_tab.metadata['position']

        # Go on to change the value of the Table of Contents box
        current_tab.change_chapter_tocBox()

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
            metadata = self.lib_ref.proxy_model.data(index, QtCore.Qt.UserRole + 3)
        elif sender == 'tableView':
            metadata = self.lib_ref.table_proxy_model.data(index, QtCore.Qt.UserRole)

        # Shift focus to the tab that has the book open (if there is one)
        for i in range(1, self.tabWidget.count()):
            tab_metadata = self.tabWidget.widget(i).metadata
            if tab_metadata['hash'] == metadata['hash']:
                self.tabWidget.setCurrentIndex(i)
                return

        path = metadata['path']
        self.open_files([path])

    def open_files(self, file_paths):
        # file_paths is expected to be a list
        # This allows for threading file opening
        # Which should speed up multiple file opening
        # especially @ application start
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

    def get_color(self):
        signal_sender = self.sender().objectName()
        profile_index = self.bookToolBar.profileBox.currentIndex()
        current_profile = self.bookToolBar.profileBox.itemData(
            profile_index, QtCore.Qt.UserRole)

        # Retain current values on opening a new dialog
        def open_color_dialog(current_color):
            color_dialog = QtWidgets.QColorDialog()
            new_color = color_dialog.getColor(current_color)
            if new_color.isValid():  # Returned in case cancel is pressed
                return new_color
            else:
                return current_color

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
            new_size = self.bookToolBar.fontSizeBox.currentText()
            if new_size.isdigit():
                current_profile['font_size'] = int(new_size)
            else:
                current_profile['font_size'] = old_size

        if signal_sender == 'lineSpacingUp':
            current_profile['line_spacing'] += .5
        if signal_sender == 'lineSpacingDown':
            current_profile['line_spacing'] -= .5

        if signal_sender == 'paddingUp':
            current_profile['padding'] += 5
        if signal_sender == 'paddingDown':
            current_profile['padding'] -= 5

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
        # Implement line spacing
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
                None, None, None, background, padding)

        else:
            profile_index = self.bookToolBar.profileBox.currentIndex()
            current_profile = self.bookToolBar.profileBox.itemData(
                profile_index, QtCore.Qt.UserRole)

            font = current_profile['font']
            foreground = current_profile['foreground']
            background = current_profile['background']
            padding = current_profile['padding']
            font_size = current_profile['font_size']

            # Change toolbar widgets to match new settings
            self.bookToolBar.fontBox.blockSignals(True)
            self.bookToolBar.fontSizeBox.blockSignals(True)
            self.bookToolBar.fontBox.setCurrentText(font)
            self.bookToolBar.fontSizeBox.setCurrentText(str(font_size))
            self.bookToolBar.fontBox.blockSignals(False)
            self.bookToolBar.fontSizeBox.blockSignals(False)

            self.bookToolBar.colorBoxFG.setStyleSheet(
                'background-color: %s' % foreground.name())
            self.bookToolBar.colorBoxBG.setStyleSheet(
                'background-color: %s' % background.name())

            current_tab.format_view(
                font, font_size, foreground, background, padding)

    def reset_profile(self):
        current_profile_index = self.bookToolBar.profileBox.currentIndex()
        current_profile_default = Settings(self).default_profiles[current_profile_index]
        self.bookToolBar.profileBox.setItemData(
            current_profile_index, current_profile_default, QtCore.Qt.UserRole)
        self.format_contentView()

    def show_settings(self):
        if not self.settings_dialog.isVisible():
            self.settings_dialog.show()
        else:
            self.settings_dialog.hide()

    def generate_library_filter_menu(self, directory_list=None):
        # TODO
        # Connect this to filtering @ the level of the library
        # Remember state of the checkboxes on library update and application restart
        # Behavior for clicking on All
        # Don't show anything for less than 2 library folders

        self.library_filter_menu.clear()

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
            filter_actions = [QtWidgets.QAction(i, self.library_filter_menu) for i in filter_list]

        filter_all = QtWidgets.QAction('All', self.library_filter_menu)
        filter_actions.append(filter_all)
        for i in filter_actions:
            i.setCheckable(True)
            i.setChecked(True)
            i.triggered.connect(self.set_library_filter)

        self.library_filter_menu.addActions(filter_actions)
        self.library_filter_menu.insertSeparator(filter_all)
        self.libraryToolBar.libraryFilterButton.setMenu(self.library_filter_menu)

    def set_library_filter(self, event=None):
        print(event)
        print(self.sender().text())

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
        # All tabs must be iterated upon here
        self.hide()
        self.settings_dialog.hide()
        self.temp_dir.remove()

        self.settings['last_open_books'] = []
        if self.tabWidget.count() > 1 and self.settings['remember_files']:

            all_metadata = []
            for i in range(1, self.tabWidget.count()):
                tab_metadata = self.tabWidget.widget(i).metadata
                self.settings['last_open_books'].append(tab_metadata['path'])
                all_metadata.append(tab_metadata)

            Settings(self).save_settings()
            self.thread = BackGroundTabUpdate(self.database_path, all_metadata)
            self.thread.finished.connect(QtWidgets.qApp.exit)
            self.thread.start()

        else:
            Settings(self).save_settings()
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
