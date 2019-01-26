#!/usr/bin/env python3

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

import os
import gc
import sys
import hashlib
import pathlib

# This allows for the program to be launched from the
# dir where it's been copied instead of needing to be
# installed
install_dir = os.path.realpath(__file__)
install_dir = pathlib.Path(install_dir).parents[1]
sys.path.append(str(install_dir))

# Init logging
# Must be done first and at the module level
# or it won't work properly in case of the imports below
from lector.logger import init_logging
logger = init_logging(sys.argv)
logger.log(60, 'Application started')

from PyQt5 import QtWidgets, QtGui, QtCore

from lector import database
from lector import sorter
from lector.toolbars import LibraryToolBar, BookToolBar
from lector.widgets import Tab, DragDropListView, DragDropTableView
from lector.delegates import LibraryDelegate
from lector.threaded import BackGroundTabUpdate, BackGroundBookAddition, BackGroundBookDeletion
from lector.library import Library
from lector.guifunctions import QImageFactory, CoverLoadingAndCulling, ViewProfileModification
from lector.settings import Settings
from lector.settingsdialog import SettingsUI
from lector.metadatadialog import MetadataUI
from lector.definitionsdialog import DefinitionsUI
from lector.resources import mainwindow, resources


class MainUI(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        self.setupUi(self)

        # Set window icon
        self.setWindowIcon(
            QtGui.QIcon(':/images/Lector.png'))

        # Central Widget - Make borders disappear
        self.centralWidget().layout().setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)

        # Initialize translation function
        self._translate = QtCore.QCoreApplication.translate

        # Create library widgets
        self.listView = DragDropListView(self, self.listPage)
        self.gridLayout_4.addWidget(self.listView, 0, 0, 1, 1)

        self.tableView = DragDropTableView(self, self.tablePage)
        self.gridLayout_3.addWidget(self.tableView, 0, 0, 1, 1)

        # Empty variables that will be infested soon
        self.settings = {}
        self.thread = None  # Background Thread
        self.current_contentView = None  # For fullscreening purposes
        self.display_profiles = None
        self.current_profile_index = None
        self.comic_profile = {}
        self.database_path = None
        self.active_library_filters = []
        self.active_docks = []

        # Initialize application
        Settings(self).read_settings()  # This should populate all variables that need
                                        # to be remembered across sessions

        # Initialize icon factory
        self.QImageFactory = QImageFactory(self)

        # Initialize toolbars
        self.libraryToolBar = LibraryToolBar(self)
        self.bookToolBar = BookToolBar(self)

        # Widget declarations
        self.libraryFilterMenu = QtWidgets.QMenu()
        self.statusMessage = QtWidgets.QLabel()

        # Reference variables
        self.alignment_dict = {
            'left': self.bookToolBar.alignLeft,
            'right': self.bookToolBar.alignRight,
            'center': self.bookToolBar.alignCenter,
            'justify': self.bookToolBar.alignJustify}

        # Create the database in case it doesn't exist
        database.DatabaseInit(self.database_path)

        # Initialize settings dialog
        self.settingsDialog = SettingsUI(self)

        # Initialize metadata dialog
        self.metadataDialog = MetadataUI(self)

        # Initialize definition view dialog
        self.definitionDialog = DefinitionsUI(self)

        # Make the statusbar invisible by default
        self.statusBar.setVisible(False)

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

        # Application wide temporary directory
        self.temp_dir = QtCore.QTemporaryDir()

        # Init the Library
        self.lib_ref = Library(self)

        # Initialize Cover loading functions
        # Must be after the Library init
        self.cover_functions = CoverLoadingAndCulling(self)

        # Init the culling timer
        self.culling_timer = QtCore.QTimer()
        self.culling_timer.setSingleShot(True)
        self.culling_timer.timeout.connect(self.cover_functions.cull_covers)

        # Initialize profile modification functions
        self.profile_functions = ViewProfileModification(self)

        # Toolbar display
        # Maybe make this a persistent option
        self.settings['show_bars'] = True

        # Library toolbar
        self.libraryToolBar.addButton.triggered.connect(self.add_books)
        self.libraryToolBar.deleteButton.triggered.connect(self.delete_books)
        self.libraryToolBar.coverViewButton.triggered.connect(self.switch_library_view)
        self.libraryToolBar.tableViewButton.triggered.connect(self.switch_library_view)
        self.libraryToolBar.reloadLibraryButton.triggered.connect(
            self.settingsDialog.start_library_scan)
        self.libraryToolBar.colorButton.triggered.connect(self.get_color)
        self.libraryToolBar.settingsButton.triggered.connect(self.show_settings)
        self.libraryToolBar.searchBar.textChanged.connect(self.lib_ref.update_proxymodels)
        self.libraryToolBar.sortingBox.activated.connect(self.lib_ref.update_proxymodels)
        self.libraryToolBar.libraryFilterButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.libraryToolBar.searchBar.textChanged.connect(self.statusbar_visibility)
        self.addToolBar(self.libraryToolBar)

        if self.settings['current_view'] == 0:
            self.libraryToolBar.coverViewButton.trigger()
        else:
            self.libraryToolBar.tableViewButton.trigger()

        # Book toolbar
        self.bookToolBar.addBookmarkButton.triggered.connect(self.add_bookmark)
        self.bookToolBar.bookmarkButton.triggered.connect(
            lambda: self.tabWidget.currentWidget().toggle_side_dock(0))
        self.bookToolBar.annotationButton.triggered.connect(
            lambda: self.tabWidget.currentWidget().toggle_side_dock(1))
        self.bookToolBar.searchButton.triggered.connect(
            lambda: self.tabWidget.currentWidget().toggle_side_dock(2))
        self.bookToolBar.distractionFreeButton.triggered.connect(self.toggle_distraction_free)
        self.bookToolBar.fullscreenButton.triggered.connect(self.set_fullscreen)

        self.bookToolBar.doublePageButton.triggered.connect(self.change_page_view)
        self.bookToolBar.mangaModeButton.triggered.connect(self.change_page_view)
        if self.settings['double_page_mode']:
            self.bookToolBar.doublePageButton.setChecked(True)
        if self.settings['manga_mode']:
            self.bookToolBar.mangaModeButton.setChecked(True)

        for count, i in enumerate(self.display_profiles):
            self.bookToolBar.profileBox.setItemData(count, i, QtCore.Qt.UserRole)
        self.bookToolBar.profileBox.currentIndexChanged.connect(
            self.profile_functions.format_contentView)
        self.bookToolBar.profileBox.setCurrentIndex(self.current_profile_index)

        self.bookToolBar.fontBox.currentFontChanged.connect(self.modify_font)
        self.bookToolBar.fontSizeBox.currentIndexChanged.connect(self.modify_font)
        self.bookToolBar.lineSpacingUp.triggered.connect(self.modify_font)
        self.bookToolBar.lineSpacingDown.triggered.connect(self.modify_font)
        self.bookToolBar.paddingUp.triggered.connect(self.modify_font)
        self.bookToolBar.paddingDown.triggered.connect(self.modify_font)
        self.bookToolBar.resetProfile.triggered.connect(
            self.profile_functions.reset_profile)

        profile_index = self.bookToolBar.profileBox.currentIndex()
        current_profile = self.bookToolBar.profileBox.itemData(
            profile_index, QtCore.Qt.UserRole)
        for i in self.alignment_dict.items():
            i[1].triggered.connect(self.modify_font)
        self.alignment_dict[current_profile['text_alignment']].setChecked(True)

        self.bookToolBar.zoomIn.triggered.connect(
            self.modify_comic_view)
        self.bookToolBar.zoomOut.triggered.connect(
            self.modify_comic_view)
        self.bookToolBar.fitWidth.triggered.connect(
            lambda: self.modify_comic_view(False))
        self.bookToolBar.bestFit.triggered.connect(
            lambda: self.modify_comic_view(False))
        self.bookToolBar.originalSize.triggered.connect(
            lambda: self.modify_comic_view(False))
        self.bookToolBar.comicBGColor.clicked.connect(
            self.get_color)

        self.bookToolBar.colorBoxFG.clicked.connect(self.get_color)
        self.bookToolBar.colorBoxBG.clicked.connect(self.get_color)
        self.bookToolBar.tocBox.currentIndexChanged.connect(self.set_toc_position)
        self.addToolBar(self.bookToolBar)

        # Make the correct toolbar visible
        self.current_tab = self.tabWidget.currentIndex()
        self.tab_switch()
        self.tabWidget.currentChanged.connect(self.tab_switch)

        # Tab Widget formatting
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.tabBarClicked.connect(self.tab_disallow_library_movement)

        # Get list of available parsers
        self.available_parsers = '*.' + ' *.'.join(sorter.available_parsers)
        logger.info('Available parsers: ' + self.available_parsers)

        # The Library tab gets no button
        self.tabWidget.tabBar().setTabButton(
            0, QtWidgets.QTabBar.RightSide, None)
        self.tabWidget.widget(0).is_library = True
        self.tabWidget.tabCloseRequested.connect(self.tab_close)
        self.tabWidget.setTabBarAutoHide(True)

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
        self.listView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.listView.setAcceptDrops(True)

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
        self.tableView.horizontalHeader().resizeSection(5, 30)
        self.tableView.horizontalHeader().setStretchLastSection(False)
        self.tableView.horizontalHeader().sectionClicked.connect(
            self.lib_ref.tableProxyModel.sort_table_columns)
        self.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(
            self.generate_library_context_menu)

        # Keyboard shortcuts
        self.ksDistractionFree = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+D'), self)
        self.ksDistractionFree.setContext(QtCore.Qt.ApplicationShortcut)
        self.ksDistractionFree.activated.connect(self.toggle_distraction_free)

        self.ksOpenFile = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+O'), self)
        self.ksOpenFile.setContext(QtCore.Qt.ApplicationShortcut)
        self.ksOpenFile.activated.connect(self.add_books)

        self.ksExitAll = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.ksExitAll.setContext(QtCore.Qt.ApplicationShortcut)
        self.ksExitAll.activated.connect(self.closeEvent)

        self.ksCloseTab = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+W'), self)
        self.ksCloseTab.setContext(QtCore.Qt.ApplicationShortcut)
        self.ksCloseTab.activated.connect(self.tab_close)

        self.ksDeletePressed = QtWidgets.QShortcut(QtGui.QKeySequence('Delete'), self)
        self.ksDeletePressed.setContext(QtCore.Qt.ApplicationShortcut)
        self.ksDeletePressed.activated.connect(self.delete_pressed)

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
            self.process_post_hoc_files(file_list, True)

    def process_post_hoc_files(self, file_list, open_files_after_processing):
        # Takes care of both dragged and dropped files
        # As well as files sent as command line arguments

        file_list = [i for i in file_list if os.path.exists(i)]
        if not file_list:
            return

        books = sorter.BookSorter(
            file_list,
            ('addition', 'manual'),
            self.database_path,
            self.settings['auto_tags'],
            self.temp_dir.path())

        parsed_books = books.initiate_threads()
        if not parsed_books and not open_files_after_processing:
            return

        database.DatabaseFunctions(self.database_path).add_to_database(parsed_books)
        self.lib_ref.generate_model('addition', parsed_books, True)

        file_dict = {i: None for i in file_list}
        if open_files_after_processing:
            self.open_files(file_dict)

        self.move_on()

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

        logger.info(
            'Attempting to open: ' + ', '.join(file_paths))

        contents = sorter.BookSorter(
            file_paths,
            ('reading', None),
            self.database_path,
            True,
            self.temp_dir.path()).initiate_threads()

        # TODO
        # Notification feedback in case all books return nothing

        if not contents:
            logger.error('No parseable files found')
            return

        successfully_opened = []
        for i in contents:
            # New tabs are created here
            # Initial position adjustment is carried out by the tab itself
            file_data = contents[i]
            Tab(file_data, self)
            successfully_opened.append(file_data['path'])
        logger.info(
            'Successfully opened: ' + ', '.join(file_paths))

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
                return

        self.tabWidget.setCurrentIndex(self.tabWidget.count() - 1)

    def start_culling_timer(self):
        if self.settings['perform_culling']:
            self.culling_timer.start(30)

    def add_bookmark(self):
        if self.tabWidget.currentIndex() != 0:
            self.tabWidget.widget(self.tabWidget.currentIndex()).add_bookmark()

    def resizeEvent(self, event=None):
        if event:
            # This implies a vertical resize event only
            # We ain't about that lifestyle
            if event.oldSize().width() == event.size().width():
                return

        # The hackiness of this hack is just...
        default_size = 170  # This is size of the QIcon (160 by default) +
                            # minimum margin needed between thumbnails

        # for n icons, the n + 1th icon will appear at > n +1.11875
        # First, calculate the number of images per row
        i = self.listView.viewport().width() / default_size
        rem = i - int(i)
        if rem >= .21875 and rem <= .9999:
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
        dialog_prompt = self._translate('Main_UI', 'Add books to database')
        ebooks_string = self._translate('Main_UI', 'eBooks')
        opened_files = QtWidgets.QFileDialog.getOpenFileNames(
            self, dialog_prompt, self.settings['last_open_path'],
            f'{ebooks_string} ({self.available_parsers})')

        if not opened_files[0]:
            return

        self.settingsDialog.okButton.setEnabled(False)
        self.libraryToolBar.reloadLibraryButton.setEnabled(False)

        self.settings['last_open_path'] = os.path.dirname(opened_files[0][0])
        self.statusBar.setVisible(True)
        self.sorterProgress.setVisible(True)
        self.statusMessage.setText(self._translate('Main_UI', 'Adding books...'))
        self.thread = BackGroundBookAddition(
            opened_files[0], self.database_path, 'manual', self)
        self.thread.finished.connect(self.move_on)
        self.thread.start()

    def get_selection(self, library_widget):
        selected_indexes = None

        if library_widget == self.listView:
            selected_books = self.lib_ref.itemProxyModel.mapSelectionToSource(
                self.listView.selectionModel().selection())
            selected_indexes = [i.indexes()[0] for i in selected_books]

        elif library_widget == self.tableView:
            selected_books = self.tableView.selectionModel().selectedRows()
            selected_indexes = [
                self.lib_ref.tableProxyModel.mapToSource(i) for i in selected_books]

        return selected_indexes

    def delete_books(self, selected_indexes=None):
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
                self.lib_ref.libraryModel.data(
                    i, QtCore.Qt.UserRole + 6) for i in selected_indexes]
            persistent_indexes = [QtCore.QPersistentModelIndex(i) for i in selected_indexes]

            for i in persistent_indexes:
                self.lib_ref.libraryModel.removeRow(i.row())

            # Update the database in the background
            self.thread = BackGroundBookDeletion(
                delete_hashes, self.database_path)
            self.thread.finished.connect(self.move_on)
            self.thread.start()

        # Generate a message box to confirm deletion
        selected_number = len(selected_indexes)
        confirm_deletion = QtWidgets.QMessageBox()
        deletion_prompt = self._translate(
            'Main_UI', f'Delete {selected_number} book(s)?')
        confirm_deletion.setText(deletion_prompt)
        confirm_deletion.setIcon(QtWidgets.QMessageBox.Question)
        confirm_deletion.setWindowTitle(self._translate('Main_UI', 'Confirm deletion'))
        confirm_deletion.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        confirm_deletion.buttonClicked.connect(ifcontinue)
        confirm_deletion.show()
        confirm_deletion.exec_()

    def delete_pressed(self):
        if self.tabWidget.currentIndex() == 0:
            self.delete_books()

    def move_on(self):
        self.settingsDialog.okButton.setEnabled(True)
        self.settingsDialog.okButton.setToolTip(
            self._translate('Main_UI', 'Save changes and start library scan'))
        self.libraryToolBar.reloadLibraryButton.setEnabled(True)

        self.sorterProgress.setVisible(False)
        self.sorterProgress.setValue(0)

        if self.libraryToolBar.searchBar.text() == '':
            self.statusBar.setVisible(False)

        self.lib_ref.update_proxymodels()
        self.lib_ref.generate_library_tags()

        self.statusMessage.setText(
            str(self.lib_ref.itemProxyModel.rowCount()) +
            self._translate('Main_UI', ' books'))

        if not self.settings['perform_culling']:
            self.cover_functions.load_all_covers()

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
            # Disallow library tab movement
            # Does not need to be looped since the library
            # tab can only ever go to position 1
            if not self.tabWidget.widget(0).is_library:
                self.tabWidget.tabBar().moveTab(1, 0)

            if self.current_tab != 0:
                self.tabWidget.widget(
                    self.current_tab).update_last_accessed_time()
        except AttributeError:
            pass

        self.current_tab = self.tabWidget.currentIndex()

        # Hide all side docks whenever a tab is switched
        for i in range(1, self.tabWidget.count()):
            self.tabWidget.widget(i).sideDock.setVisible(False)

        # If library
        if self.tabWidget.currentIndex() == 0:
            self.resizeEvent()
            self.start_culling_timer()

            if self.settings['show_bars']:
                self.bookToolBar.hide()
                self.libraryToolBar.show()

            if self.lib_ref.itemProxyModel:
                # Making the proxy model available doesn't affect
                # memory utilization at all. Bleh.
                self.statusMessage.setText(
                    str(self.lib_ref.itemProxyModel.rowCount()) +
                    self._translate('Main_UI', ' Books'))

            if self.libraryToolBar.searchBar.text() != '':
                self.statusBar.setVisible(True)

        else:
            if self.settings['show_bars']:
                self.bookToolBar.show()
                self.libraryToolBar.hide()

            current_tab = self.tabWidget.currentWidget()
            self.bookToolBar.tocBox.setModel(current_tab.tocModel)
            self.bookToolBar.tocTreeView.expandAll()
            current_tab.set_tocBox_index(None, None)

            # Needed to set the contentView widget background
            # on first run. Subsequent runs might be redundant,
            # but it doesn't seem to visibly affect performance
            self.profile_functions.format_contentView()
            self.statusBar.setVisible(False)

            if self.bookToolBar.fontButton.isChecked():
                self.bookToolBar.customize_view_on()
            else:
                if current_tab.are_we_doing_images_only:
                    self.bookToolBar.searchButton.setVisible(False)
                    self.bookToolBar.annotationButton.setVisible(False)
                    self.bookToolBar.bookSeparator2.setVisible(False)
                    self.bookToolBar.bookSeparator3.setVisible(False)
                else:
                    self.bookToolBar.searchButton.setVisible(True)
                    self.bookToolBar.annotationButton.setVisible(True)
                    self.bookToolBar.bookSeparator2.setVisible(True)
                    self.bookToolBar.bookSeparator3.setVisible(True)

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

        self.tabWidget.widget(tab_index).deleteLater()
        self.tabWidget.widget(tab_index).setParent(None)
        gc.collect()

    def tab_disallow_library_movement(self, tab_index):
        # Makes the library tab immovable
        if tab_index == 0:
            self.tabWidget.setMovable(False)
        else:
            self.tabWidget.setMovable(True)

    def set_toc_position(self, event=None):
        currentIndex = self.bookToolBar.tocTreeView.currentIndex()
        required_position = currentIndex.data(QtCore.Qt.UserRole)
        if not required_position:
            return  # Initial startup might return a None

        # The set_content method is universal
        # It's going to do position tracking
        current_tab = self.tabWidget.currentWidget()
        current_tab.set_content(required_position)

    def set_fullscreen(self):
        self.tabWidget.currentWidget().go_fullscreen()

    def library_doubleclick(self, index):
        sender = self.sender().objectName()

        if sender == 'listView':
            source_index = self.lib_ref.itemProxyModel.mapToSource(index)
        elif sender == 'tableView':
            source_index = self.lib_ref.tableProxyModel.mapToSource(index)

        item = self.lib_ref.libraryModel.item(source_index.row(), 0)
        metadata = item.data(QtCore.Qt.UserRole + 3)
        path = {metadata['path']: metadata['hash']}

        self.open_files(path)

    def statusbar_visibility(self):
        if self.sender() == self.libraryToolBar.searchBar:
            if self.libraryToolBar.searchBar.text() == '':
                self.statusBar.setVisible(False)
            else:
                self.statusBar.setVisible(True)

    def show_settings(self):
        if not self.settingsDialog.isVisible():
            self.settingsDialog.show()
        else:
            self.settingsDialog.hide()

    #____________________________________________
    # The contentView modification functions are in the guifunctions
    # module. self.profile_functions is the reference here.

    def get_color(self):
        self.profile_functions.get_color(
            self.sender().objectName())

    def modify_font(self):
        self.profile_functions.modify_font(
            self.sender().objectName())

    def modify_comic_view(self, key_pressed=None):
        if key_pressed:
            signal_sender = None
        else:
            signal_sender = self.sender().objectName()
        self.profile_functions.modify_comic_view(
            signal_sender, key_pressed)

    #____________________________________________

    def change_page_view(self, key_pressed=False):
        # Set zoom mode to best fit to
        # make the transition less jarring
        self.comic_profile['zoom_mode'] = 'bestFit'

        # Toggle Double page mode / manga mode on keypress
        if key_pressed == QtCore.Qt.Key_D:
            self.bookToolBar.doublePageButton.setChecked(
                not self.bookToolBar.doublePageButton.isChecked())
        if key_pressed == QtCore.Qt.Key_M:
            self.bookToolBar.mangaModeButton.setChecked(
                not self.bookToolBar.mangaModeButton.isChecked())

        # Change settings according to the
        # current state of each of the toolbar buttons
        self.settings['double_page_mode'] = self.bookToolBar.doublePageButton.isChecked()
        self.settings['manga_mode'] = self.bookToolBar.mangaModeButton.isChecked()

        # Switch page to whatever index is selected in the tocBox
        current_tab = self.tabWidget.currentWidget()
        chapter_number = current_tab.metadata['position']['current_chapter']
        current_tab.set_content(chapter_number, False)

    def generate_library_context_menu(self, position):
        index = self.sender().indexAt(position)
        if not index.isValid():
            return

        # It's worth remembering that these are indexes of the libraryModel
        # and NOT of the proxy models
        selected_indexes = self.get_selection(self.sender())

        context_menu = QtWidgets.QMenu()

        openAction = context_menu.addAction(
            self.QImageFactory.get_image('view-readermode'),
            self._translate('Main_UI', 'Start reading'))

        editAction = None
        if len(selected_indexes) == 1:
            editAction = context_menu.addAction(
                self.QImageFactory.get_image('edit-rename'),
                self._translate('Main_UI', 'Edit'))

        deleteAction = context_menu.addAction(
            self.QImageFactory.get_image('trash-empty'),
            self._translate('Main_UI', 'Delete'))
        readAction = context_menu.addAction(
            QtGui.QIcon(':/images/checkmark.svg'),
            self._translate('Main_UI', 'Mark read'))
        unreadAction = context_menu.addAction(
            QtGui.QIcon(':/images/xmark.svg'),
            self._translate('Main_UI', 'Mark unread'))

        action = context_menu.exec_(self.sender().mapToGlobal(position))

        if action == openAction:
            books_to_open = {}
            for i in selected_indexes:
                metadata = self.lib_ref.libraryModel.data(i, QtCore.Qt.UserRole + 3)
                books_to_open[metadata['path']] = metadata['hash']

            self.open_files(books_to_open)

        if action == editAction:
            edit_book = selected_indexes[0]
            is_cover_loaded = self.lib_ref.libraryModel.data(
                edit_book, QtCore.Qt.UserRole + 8)

            # Loads a cover in case culling is enabled and the table view is visible
            if not is_cover_loaded:
                book_hash = self.lib_ref.libraryModel.data(
                    edit_book, QtCore.Qt.UserRole + 6)
                book_item = self.lib_ref.libraryModel.item(edit_book.row())
                book_cover = database.DatabaseFunctions(
                    self.database_path).fetch_covers_only([book_hash])[0][1]
                self.cover_functions.cover_loader(book_item, book_cover)

            cover = self.lib_ref.libraryModel.item(
                edit_book.row()).icon()
            title = self.lib_ref.libraryModel.data(
                edit_book, QtCore.Qt.UserRole)
            author = self.lib_ref.libraryModel.data(
                edit_book, QtCore.Qt.UserRole + 1)
            year = str(self.lib_ref.libraryModel.data(
                edit_book, QtCore.Qt.UserRole + 2))  # Text cannot be int
            tags = self.lib_ref.libraryModel.data(
                edit_book, QtCore.Qt.UserRole + 4)

            self.metadataDialog.load_book(
                cover, title, author, year, tags, edit_book)
            self.metadataDialog.show()

        if action == deleteAction:
            self.delete_books(selected_indexes)

        if action == readAction or action == unreadAction:
            for i in selected_indexes:
                metadata = self.lib_ref.libraryModel.data(i, QtCore.Qt.UserRole + 3)
                book_hash = self.lib_ref.libraryModel.data(i, QtCore.Qt.UserRole + 6)
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
                    position_perc = 1

                self.lib_ref.libraryModel.setData(i, metadata, QtCore.Qt.UserRole + 3)
                self.lib_ref.libraryModel.setData(i, position_perc, QtCore.Qt.UserRole + 7)
                self.lib_ref.libraryModel.setData(i, last_accessed_time, QtCore.Qt.UserRole + 12)
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

        filter_list.append(self._translate('Main_UI', 'Manually Added'))
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

    def toggle_distraction_free(self):
        self.settings['show_bars'] = not self.settings['show_bars']

        if self.tabWidget.count() > 1:
            self.tabWidget.tabBar().setVisible(
                self.settings['show_bars'])

        current_tab = self.tabWidget.currentIndex()
        if current_tab == 0:
            self.libraryToolBar.setVisible(
                not self.libraryToolBar.isVisible())
        else:
            self.bookToolBar.setVisible(
                not self.bookToolBar.isVisible())

        self.start_culling_timer()

    def closeEvent(self, event=None):
        if event:
            event.ignore()

        self.hide()
        self.metadataDialog.hide()
        self.settingsDialog.hide()
        self.definitionDialog.hide()
        self.temp_dir.remove()
        for this_dock in self.active_docks:
            try:
                this_dock.setVisible(False)
            except RuntimeError:
                pass

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

    # Internationalization support
    translator = QtCore.QTranslator()
    translations_found = translator.load(
        QtCore.QLocale.system(), ':/translations/translations_bin/Lector_')
    app.installTranslator(translator)

    translations_out_string = ' (Translations found)'
    if not translations_found:
        translations_out_string = ' (No translations found)'
    print(f'Locale: {QtCore.QLocale.system().name()}' + translations_out_string)

    form = MainUI()
    form.show()
    form.resizeEvent()
    app.exec_()


if __name__ == '__main__':
    main()
