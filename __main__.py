#!/usr/bin/env python3

""" TODO
    Options:
        Check files (hashes) upon restart
        Recursive file addition
        Show what on startup
        If cache large files
    Library:
        ✓ sqlite3 for cover images cache
        ✓ sqlite3 for storing metadata
        ✓ Drop down for SortBy
        ✓ Image delegates
        ✓ Image reflow
        ✓ Search bar in toolbar
        ✓ Shift focus to the tab that has the book open
        ✓ Tie file deletion and tab closing to model updates
        ? Create emblem per filetype
        Look into how you might group icons
        Ignore a / the / numbers for sorting purposes
        Put the path in the scope of the search
            maybe as a type: switch
        Mass tagging
        Information dialog widget
        Context menu: Cache, Read, Edit database, delete, Mark read/unread
        Create separate thread for parser - Show progress in main window
    Reading:
        ✓ Drop down for TOC
        ✓ Override the keypress event of the textedit
        ✓ Use format* icons for toolbar buttons
        ✓ Implement book view settings with a(nother) toolbar
        ✓ Substitute textedit for another widget
        ✓ Theming
        ✓ Keep fontsize and margins consistent - Let page increase in length
        ✓ Fullscreening
        ✓ Remember open tabs
        Special Keyboard shortcuts and view modes for QGraphicsView
        Selectable background color for QGraphicsView
        Record progress
        Pagination
        Set context menu for definitions and the like
    Filetypes:
        ? Plugin system for parsers
        ? pdf support
        epub support
        mobi, azw support
        txt, doc, djvu support
        cbz, cbr support
            Keep font settings enabled but only for background color
    Internet:
        Goodreads API: Ratings, Read, Recommendations
        Get ISBN using python-isbnlib
    Other:
        ✓ Define every widget in code
        ✓ Include icons for emblems
"""

import sys

from PyQt5 import QtWidgets, QtGui, QtCore

import mainwindow
import database
import sorter

from widgets import LibraryToolBar, BookToolBar, Tab
from widgets import LibraryDelegate, BackGroundTabUpdate, BackGroundBookAddition
from library import Library
from settings import Settings


class MainUI(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        self.setupUi(self)

        # Empty variables that will be infested soon
        self.last_open_books = None
        self.last_open_tab = None
        self.last_open_path = None
        self.thread = None  # Background Thread
        self.viewModel = None
        self.current_contentView = None  # For fullscreening purposes

        # Initialize application
        Settings(self).read_settings()  # This should populate all variables that need
                                        # to be remembered across sessions

        # Create the database in case it doesn't exist
        database.DatabaseInit(self.database_path)

        # Create and right align the statusbar label widget
        self.statusMessage = QtWidgets.QLabel()
        self.statusMessage.setObjectName('statusMessage')
        self.statusBar.addPermanentWidget(self.statusMessage)

        # Init the QListView
        self.lib_ref = Library(self)

        # Application wide temporary directory
        self.temp_dir = QtCore.QTemporaryDir()

        # Library toolbar
        self.libraryToolBar = LibraryToolBar(self)
        self.libraryToolBar.addButton.triggered.connect(self.add_books)
        self.libraryToolBar.deleteButton.triggered.connect(self.delete_books)
        self.libraryToolBar.searchBar.textChanged.connect(self.lib_ref.update_proxymodel)
        self.libraryToolBar.sortingBox.activated.connect(self.lib_ref.update_proxymodel)
        self.addToolBar(self.libraryToolBar)

        # Book toolbar
        self.bookToolBar = BookToolBar(self)
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

        self.bookToolBar.colorBoxFG.clicked.connect(self.get_color)
        self.bookToolBar.colorBoxBG.clicked.connect(self.get_color)
        self.bookToolBar.tocBox.currentIndexChanged.connect(self.set_toc_position)
        self.addToolBar(self.bookToolBar)

        # Make the correct toolbar visible
        self.tab_switch()
        self.tabWidget.currentChanged.connect(self.tab_switch)

        # Tab closing
        self.tabWidget.setTabsClosable(True)
        # TODO
        # It's possible to add a widget to the Library tab here
        self.tabWidget.tabBar().setTabButton(0, QtWidgets.QTabBar.RightSide, None)
        self.tabWidget.tabCloseRequested.connect(self.tab_close)

        # ListView
        self.listView.setGridSize(QtCore.QSize(175, 240))
        self.listView.setMouseTracking(True)
        self.listView.verticalScrollBar().setSingleStep(7)
        self.listView.doubleClicked.connect(self.list_doubleclick)
        self.listView.setItemDelegate(LibraryDelegate(self.temp_dir.path()))
        self.lib_ref.generate_model('build')
        self.lib_ref.create_proxymodel()

        # Keyboard shortcuts
        self.ks_close_tab = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+W'), self)
        self.ks_close_tab.setContext(QtCore.Qt.ApplicationShortcut)
        self.ks_close_tab.activated.connect(self.tab_close)

        self.ks_exit_all = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.ks_exit_all.setContext(QtCore.Qt.ApplicationShortcut)
        self.ks_exit_all.activated.connect(self.closeEvent)

        # Open last... open books.
        self.open_files(self.last_open_books)
        self.last_open_books = None

    def resizeEvent(self, event=None):
        if event:
            # This implies a vertical resize event only
            # We ain't about that lifestyle
            if event.oldSize().width() == event.size().width():
                return

        # The hackiness of this hack is just...
        default_size = 175  # This is size of the QIcon (160 by default) +
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
                QtCore.QSize(default_size + layout_extra_space_per_image, 240))
        except ZeroDivisionError:  # Initial resize is ignored
            return

    def add_books(self):
        # TODO
        # Maybe expand this to traverse directories recursively
        # Generate list of available parsers

        my_file = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open file', self.last_open_path,
            "eBooks (*.epub *.mobi *.aws *.txt *.pdf *.fb2 *.djvu *.cbz)")

        if my_file[0]:
            self.thread = BackGroundBookAddition(self, my_file[0], self.database_path)
            self.thread.finished.connect(self.lib_ref.create_proxymodel)
            self.thread.start()

    def delete_books(self):
        selected_books = self.listView.selectedIndexes()
        if selected_books:
            def ifcontinue(box_button):
                if box_button.text() == '&Yes':
                    selected_hashes = []
                    for i in selected_books:
                        data = i.data(QtCore.Qt.UserRole + 3)
                        selected_hashes.append(data['hash'])

                    database.DatabaseFunctions(
                        self.database_path).delete_from_database(selected_hashes)

                    self.lib_ref.generate_model('build')
                    self.lib_ref.create_proxymodel()

            selected_number = len(selected_books)
            msg_box = QtWidgets.QMessageBox()
            msg_box.setText('Delete %d book(s)?' % selected_number)
            msg_box.setIcon(QtWidgets.QMessageBox.Question)
            msg_box.setWindowTitle('Confirm deletion')
            msg_box.setStandardButtons(
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg_box.buttonClicked.connect(ifcontinue)
            msg_box.show()
            msg_box.exec_()

    def tab_switch(self):
        if self.tabWidget.currentIndex() == 0:

            self.bookToolBar.hide()
            self.libraryToolBar.show()

            if self.lib_ref.proxy_model:
                # Making the proxy model available doesn't affect
                # memory utilization at all. Bleh.
                self.statusMessage.setText(
                    str(self.lib_ref.proxy_model.rowCount()) + ' Books')
        else:
            self.bookToolBar.show()
            self.libraryToolBar.hide()

            current_metadata = self.tabWidget.widget(
                self.tabWidget.currentIndex()).metadata

            current_title = current_metadata['title']
            current_author = current_metadata['author']
            current_position = current_metadata['position']
            current_toc = current_metadata['content'].keys()

            self.bookToolBar.tocBox.blockSignals(True)
            self.bookToolBar.tocBox.clear()
            self.bookToolBar.tocBox.addItems(current_toc)
            if current_position:
                self.bookToolBar.tocBox.setCurrentIndex(current_position['current_chapter'] - 1)
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

        # We're updating the underlying model to have real-time
        # updates on the read status

        # Set a baseline model index in case the item gets deleted
        # E.g It's open in a tab and deleted from the library
        model_index = None
        start_index = self.viewModel.index(0, 0)
        # Find index of the model item that corresponds to the tab
        matching_item = self.viewModel.match(
            start_index,
            QtCore.Qt.UserRole + 6,
            current_tab.metadata['hash'],
            1, QtCore.Qt.MatchExactly)
        if matching_item:
            model_row = matching_item[0].row()
            model_index = self.viewModel.index(model_row, 0)

        current_tab.metadata[
            'position']['current_chapter'] = event + 1

        if model_index:
            self.viewModel.setData(
                model_index, current_tab.metadata['position'], QtCore.Qt.UserRole + 7)

        current_tab.chapter_change()

    def set_fullscreen(self):
        current_tab = self.tabWidget.currentIndex()
        current_tab_widget = self.tabWidget.widget(current_tab)
        self.current_contentView = current_tab_widget.findChildren(
            (QtWidgets.QTextBrowser, QtWidgets.QGraphicsView))[0]

        self.current_contentView.setWindowFlags(QtCore.Qt.Window)
        self.current_contentView.setWindowState(QtCore.Qt.WindowFullScreen)
        self.current_contentView.show()
        self.hide()

    def list_doubleclick(self, myindex):
        index = self.listView.model().index(myindex.row(), 0)
        metadata = self.listView.model().data(index, QtCore.Qt.UserRole + 3)

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

        contents = sorter.BookSorter(
            file_paths, 'reading', self.database_path, self.temp_dir.path()).initiate_threads()

        found_a_focusable_tab = False

        for i in contents:
            file_data = contents[i]
            Tab(file_data, self.tabWidget)  # New tabs are created here
                                            # Initial position adjustment
                                            # is carried out by the tab itself
            if file_data['path'] == self.last_open_tab:
                found_a_focusable_tab = True
                self.tabWidget.setCurrentIndex(self.tabWidget.count() - 1)

        if not found_a_focusable_tab:
            self.tabWidget.setCurrentIndex(self.tabWidget.count() - 1)

    def get_color(self):
        signal_sender = self.sender().objectName()
        profile_index = self.bookToolBar.profileBox.currentIndex()
        current_profile = self.bookToolBar.profileBox.itemData(
            profile_index, QtCore.Qt.UserRole)

        colorDialog = QtWidgets.QColorDialog()
        new_color = colorDialog.getColor()
        if not new_color:
            return

        color_name = new_color.name()

        if signal_sender == 'fgColor':
            self.bookToolBar.colorBoxFG.setStyleSheet(
                'background-color: %s' % color_name)
            current_profile['foreground'] = color_name

        elif signal_sender == 'bgColor':
            self.bookToolBar.colorBoxBG.setStyleSheet(
                'background-color: %s' % color_name)
            current_profile['background'] = color_name

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

    def format_contentView(self):
        # TODO
        # Implement line spacing
        # See what happens if a font isn't installed

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
            'background-color: %s' % foreground)
        self.bookToolBar.colorBoxBG.setStyleSheet(
            'background-color: %s' % background)

        # Do not run when only the library tab is open
        if self.tabWidget.count() == 1:
            return

        # Change contentView to match new settings
        current_tab = self.tabWidget.widget(self.tabWidget.currentIndex())
        current_tab.format_view(font, font_size, foreground, background, padding)

    def reset_profile(self):
        current_profile_index = self.bookToolBar.profileBox.currentIndex()
        current_profile_default = Settings(self).default_profiles[current_profile_index]
        self.bookToolBar.profileBox.setItemData(
            current_profile_index, current_profile_default, QtCore.Qt.UserRole)
        self.format_contentView()

    def closeEvent(self, event=None):
        # All tabs must be iterated upon here
        self.temp_dir.remove()
        self.hide()

        self.last_open_books = []
        if self.tabWidget.count() > 1:

            all_metadata = []
            for i in range(1, self.tabWidget.count()):
                tab_metadata = self.tabWidget.widget(i).metadata
                self.last_open_books.append(tab_metadata['path'])
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
