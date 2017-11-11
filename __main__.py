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
        ? Substitute textedit for another widget
        All ebooks should first be added to the database and then returned as HTML
        Pagination
        Theming
        Set context menu for definitions and the like
        Keep fontsize and margins consistent - Let page increase in length
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
        ? Include icons for emblems
"""

import os
import sys

from PyQt5 import QtWidgets, QtGui, QtCore

import mainwindow
import database
import sorter

from widgets import LibraryToolBar, BookToolBar, Tab, LibraryDelegate
from subclasses import Settings, Library


class MainUI(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

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
        self.viewModel = None
        self.lib_ref = Library(self)

        # Create toolbars
        self.libraryToolBar = LibraryToolBar(self)
        self.libraryToolBar.addButton.triggered.connect(self.add_books)
        self.libraryToolBar.deleteButton.triggered.connect(self.delete_books)
        self.libraryToolBar.filterEdit.textChanged.connect(self.only_update_listview)
        self.libraryToolBar.sortingBox.activated.connect(self.only_update_listview)
        self.addToolBar(self.libraryToolBar)

        self.bookToolBar = BookToolBar(self)
        self.bookToolBar.fullscreenButton.triggered.connect(self.set_fullscreen)
        self.bookToolBar.tocBox.activated.connect(self.set_toc_position)
        self.addToolBar(self.bookToolBar)

        # Make the correct toolbar visible
        self.tab_switch()
        self.tabWidget.currentChanged.connect(self.tab_switch)

        # New tabs and their contents
        self.current_tab = None
        self.current_contentView = None

        # Tab closing
        self.tabWidget.setTabsClosable(True)
        # TODO
        # It's possible to add a widget to the Library tab here
        self.tabWidget.tabBar().setTabButton(0, QtWidgets.QTabBar.RightSide, None)
        self.tabWidget.tabCloseRequested.connect(self.close_tab)

        # ListView
        # self.listView.setSpacing(0)
        self.listView.setGridSize(QtCore.QSize(175, 240))
        self.listView.verticalScrollBar().setSingleStep(7)
        self.listView.doubleClicked.connect(self.list_doubleclick)
        self.listView.setItemDelegate(LibraryDelegate())
        self.reload_listview()

        # Keyboard shortcuts
        self.exit_all = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.exit_all.activated.connect(self.closeEvent)

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
        self.statusMessage.setText('Adding books...')
        my_file = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open file', self.last_open_path,
            "eBooks (*.epub *.mobi *.aws *.txt *.pdf *.fb2 *.djvu)")
        if my_file[0]:
            self.listView.setEnabled(False)
            self.last_open_path = os.path.dirname(my_file[0][0])
            books = sorter.BookSorter(my_file[0], 'addition', self.database_path)
            parsed_books = books.initiate_threads()
            database.DatabaseFunctions(self.database_path).add_to_database(parsed_books)
            self.listView.setEnabled(True)
            self.viewModel = None
        self.reload_listview()

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
                    self.viewModel = None  # TODO
                                           # Delete the item from the model instead
                                           # of reconstructing it
                                           # The same goes for addition
                    self.reload_listview()

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

    def only_update_listview(self):
        self.lib_ref.update_proxymodel()

    def reload_listview(self):
        if not self.viewModel:
            self.lib_ref.generate_model()
        self.lib_ref.create_proxymodel()
        self.lib_ref.update_proxymodel()

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
                self.bookToolBar.tocBox.setCurrentIndex(current_position)
            self.bookToolBar.tocBox.blockSignals(False)

            self.statusMessage.setText(
                current_author + ' - ' + current_title)

    def set_toc_position(self, event=None):
        self.tabWidget.widget(
            self.tabWidget.currentIndex()).metadata[
                'position'] = event

        chapter_name = self.bookToolBar.tocBox.currentText()

        current_tab = self.tabWidget.widget(self.tabWidget.currentIndex())
        required_content = current_tab.metadata['content'][chapter_name]
        current_tab.contentView.setHtml(required_content)

    def set_fullscreen(self):
        self.current_tab = self.tabWidget.currentIndex()
        self.current_contentView = self.tabWidget.widget(self.current_tab)

        self.exit_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence('Escape'), self.current_contentView)
        self.exit_shortcut.activated.connect(self.set_normalsize)

        self.current_contentView.setWindowFlags(QtCore.Qt.Window)
        self.current_contentView.setWindowState(QtCore.Qt.WindowFullScreen)
        self.hide()
        self.current_contentView.show()

    def set_normalsize(self):
        self.current_contentView.setWindowState(QtCore.Qt.WindowNoState)
        self.current_contentView.setWindowFlags(QtCore.Qt.Widget)
        self.show()
        self.current_contentView.show()

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
        contents = sorter.BookSorter(
            [path], 'reading', self.database_path).initiate_threads()

        tab_ref = Tab(contents, self.tabWidget)
        self.tabWidget.setCurrentWidget(tab_ref)
        # print(tab_ref.book_metadata)  # Metadata upon tab creation

    def close_tab(self, tab_index):
        # print(self.tabWidget.widget(tab_index).metadata)  # Metadata upon tab deletion
        self.tabWidget.removeTab(tab_index)

    def closeEvent(self, event=None):
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
