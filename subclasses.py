#!/usr/bin/env python3

import os
import database
from PyQt5 import QtWidgets, QtGui, QtCore


class Library:
    def __init__(self, parent):
        self.parent_window = parent
        self.proxy_model = None

    def generate_model(self):
        # TODO
        # Use QItemdelegates to show book read progress

        # The QlistView widget needs to be populated
        # with a model that inherits from QStandardItemModel
        self.parent_window.viewModel = QtGui.QStandardItemModel()
        books = database.DatabaseFunctions(
            self.parent_window.database_path).fetch_data(
                ('*',),
                'books',
                {'Title': ''},
                'LIKE')

        if not books:
            print('Database returned nothing')
            return

        for i in books:
            # The database query returns a tuple with the following indices
            # Index 0 is the key ID is ignored
            title = i[1]
            author = i[2]
            year = i[3]
            path = i[4]
            tags = i[6]
            cover = i[9]
            progress = None  # TODO
                             # Leave at None for an untouched book
                             # 'completed' for a completed book
                             # whatever else is here can be used
                             # to remember position
                             # Maybe get from the position param

            all_metadata = {
                'title': i[1],
                'author': i[2],
                'year': i[3],
                'path': i[4],
                'position': i[5],
                'isbn': i[6],
                'tags': i[7],
                'hash': i[8]}

            tooltip_string = title + '\nAuthor: ' + author + '\nYear: ' + str(year)
            if tags:
                tooltip_string += ('\nTags: ' + tags)

            # This remarkably ugly hack is because the QSortFilterProxyModel
            # doesn't easily allow searching through multiple item roles
            search_workaround = title + ' ' + author
            if tags:
                search_workaround += tags

            # Generate book state for passing onto the QStyledItemDelegate
            def generate_book_state(path, progress):
                if not os.path.exists(path):
                    return 'deleted'

                if progress:
                    if progress == 'completed':
                        return 'completed'
                    else:
                        return 'inprogress'
                else:
                    return None
            state = generate_book_state(path, progress)

            # Generate image pixmap and then pass it to the widget
            # as a QIcon
            # Additional data can be set using an incrementing
            # QtCore.Qt.UserRole
            # QtCore.Qt.DisplayRole is the same as item.setText()
            # The model is a single row and has no columns
            img_pixmap = QtGui.QPixmap()
            img_pixmap.loadFromData(cover)
            img_pixmap = img_pixmap.scaled(420, 600, QtCore.Qt.IgnoreAspectRatio)
            item = QtGui.QStandardItem()
            item.setToolTip(tooltip_string)
            # The following order is needed to keep sorting working
            item.setData(title, QtCore.Qt.UserRole)
            item.setData(author, QtCore.Qt.UserRole + 1)
            item.setData(year, QtCore.Qt.UserRole + 2)
            item.setData(all_metadata, QtCore.Qt.UserRole + 3)
            item.setData(search_workaround, QtCore.Qt.UserRole + 4)
            item.setData(state, QtCore.Qt.UserRole + 5)
            item.setIcon(QtGui.QIcon(img_pixmap))
            self.parent_window.viewModel.appendRow(item)

    def create_proxymodel(self):
        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.parent_window.viewModel)
        s = QtCore.QSize(160, 250)  # Set icon sizing here
        self.parent_window.listView.setIconSize(s)
        self.parent_window.listView.setModel(self.proxy_model)

    def update_proxymodel(self):
        self.proxy_model.setFilterRole(QtCore.Qt.UserRole + 4)
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy_model.setFilterWildcard(
            self.parent_window.libraryToolBar.searchBar.text())

        self.parent_window.statusMessage.setText(
            str(self.proxy_model.rowCount()) + ' books')

        # Sorting according to roles and the drop down in the library
        self.proxy_model.setSortRole(
            QtCore.Qt.UserRole + self.parent_window.libraryToolBar.sortingBox.currentIndex())
        self.proxy_model.sort(0)


class Settings:
    def __init__(self, parent):
        self.parent_window = parent
        self.settings = QtCore.QSettings('Lector', 'Lector')

        self.default_profile1 = {
            'font': 'Noto Sans',
            'foreground': '#000000',
            'background': '#d8d8d8',
            'padding': 140,
            'font_size': 20,
            'line_spacing': 1.5}

        self.default_profile2 = {
            'font': 'Roboto',
            'foreground': '#c2c2c2',
            'background': '#161616',
            'padding': 140,
            'font_size': 20,
            'line_spacing': 1.5}

        self.default_profile3 = {
            'font': 'Roboto',
            'foreground': '#657b83',
            'background': '#002b36',
            'padding': 140,
            'font_size': 20,
            'line_spacing': 1.5}

    def read_settings(self):
        self.settings.beginGroup('mainWindow')
        self.parent_window.resize(self.settings.value(
            'windowSize',
            QtCore.QSize(1299, 748)))
        self.parent_window.move(self.settings.value(
            'windowPosition',
            QtCore.QPoint(286, 141)))
        self.settings.endGroup()

        self.settings.beginGroup('runtimeVariables')
        self.parent_window.last_open_path = self.settings.value(
            'lastOpenPath', os.path.expanduser('~'))
        self.parent_window.database_path = self.settings.value(
            'databasePath',
            QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppDataLocation))
        self.parent_window.display_profiles = self.settings.value(
            'displayProfiles', [
                self.default_profile1,
                self.default_profile2,
                self.default_profile3])
        self.parent_window.current_profile_index = int(self.settings.value(
            'currentProfileIndex', 0))
        self.settings.endGroup()

    def save_settings(self):
        self.settings.beginGroup('mainWindow')
        self.settings.setValue('windowSize', self.parent_window.size())
        self.settings.setValue('windowPosition', self.parent_window.pos())
        self.settings.endGroup()

        self.settings.beginGroup('runtimeVariables')
        self.settings.setValue('lastOpenPath', self.parent_window.last_open_path)
        self.settings.setValue('databasePath', self.parent_window.database_path)

        current_profile1 = self.parent_window.bookToolBar.profileBox.itemData(
            0, QtCore.Qt.UserRole)
        current_profile2 = self.parent_window.bookToolBar.profileBox.itemData(
            1, QtCore.Qt.UserRole)
        current_profile3 = self.parent_window.bookToolBar.profileBox.itemData(
            2, QtCore.Qt.UserRole)
        current_profile_index = self.parent_window.bookToolBar.profileBox.currentIndex()
        self.settings.setValue('displayProfiles', [
            current_profile1,
            current_profile2,
            current_profile3])
        self.settings.setValue('currentProfileIndex', current_profile_index)
        self.settings.endGroup()
