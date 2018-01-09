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
# Implement filterAcceptsRow for the view_model


import os
import pickle
import database

from PyQt5 import QtGui, QtCore
from models import MostExcellentTableModel, TableProxyModel


class Library:
    def __init__(self, parent):
        self.parent = parent
        self.view_model = None
        self.proxy_model = None
        self.table_model = None
        self.table_proxy_model = None
        self.table_rows = []

    def generate_model(self, mode, parsed_books=None):
        if mode == 'build':
            self.table_rows = []
            self.view_model = QtGui.QStandardItemModel()

            books = database.DatabaseFunctions(
                self.parent.database_path).fetch_data(
                    ('Title', 'Author', 'Year', 'Path', 'Position', 'ISBN', 'Tags', 'Hash',),
                    'books',
                    {'Title': ''},
                    'LIKE')

            if not books:
                print('Database returned nothing')
                return

        elif mode == 'addition':
            # Assumes self.view_model already exists and may be extended
            # Because any additional books have already been added to the
            # database using background threads

            books = []
            for i in parsed_books.items():
                _tags = i[1]['tags']
                if _tags:
                    _tags = ', '.join([j for j in _tags if j])

                books.append([
                    i[1]['title'], i[1]['author'], i[1]['year'], i[1]['path'],
                    None, i[1]['isbn'], _tags, i[0]])

        else:
            return

        for i in books:
            # The database query returns (or the extension data is)
            # an iterable with the following indices:
            # Index 0 is the key ID is ignored
            title = i[0]
            author = i[1]
            year = i[2]
            path = i[3]
            tags = i[6]
            # cover = i[9]

            position = i[4]
            if position:
                position = pickle.loads(position)

            file_exists = os.path.exists(path)

            all_metadata = {
                'title': title,
                'author': author,
                'year': year,
                'path': path,
                'position': position,
                'isbn': i[5],
                'tags': tags,
                'hash': i[7],
                'file_exists': file_exists}

            tooltip_string = title + '\nAuthor: ' + author + '\nYear: ' + str(year)
            if tags:
                tooltip_string += ('\nTags: ' + tags)

            # This remarkably ugly hack is because the QSortFilterProxyModel
            # doesn't easily allow searching through multiple item roles
            search_workaround = title + ' ' + author
            if tags:
                search_workaround += tags

            # Additional data can be set using an incrementing
            # QtCore.Qt.UserRole
            # QtCore.Qt.DisplayRole is the same as item.setText()
            # The model is a single row and has no columns

            # No covers are set at this time
            # That is to be achieved by way of the culling function
            img_pixmap = QtGui.QPixmap()
            img_pixmap.load(':/images/blank.png')
            img_pixmap = img_pixmap.scaled(420, 600, QtCore.Qt.IgnoreAspectRatio)
            item = QtGui.QStandardItem()
            item.setToolTip(tooltip_string)

            # The following order is needed to keep sorting working
            item.setData(title, QtCore.Qt.UserRole)
            item.setData(author, QtCore.Qt.UserRole + 1)
            item.setData(year, QtCore.Qt.UserRole + 2)
            item.setData(all_metadata, QtCore.Qt.UserRole + 3)
            item.setData(search_workaround, QtCore.Qt.UserRole + 4)
            item.setData(file_exists, QtCore.Qt.UserRole + 5)
            item.setData(i[7], QtCore.Qt.UserRole + 6)  # File hash
            item.setData(position, QtCore.Qt.UserRole + 7)
            item.setData(False, QtCore.Qt.UserRole + 8) # Is the cover being displayed?
            item.setIcon(QtGui.QIcon(img_pixmap))
            self.view_model.appendRow(item)

            # all_metadata is just being sent. It is not being displayed
            # It will be correlated to the current row as its first userrole
            self.table_rows.append(
                [title, author, None, year, tags, all_metadata, i[7]])

    def create_table_model(self):
        table_header = ['Title', 'Author', 'Status', 'Year', 'Tags']
        self.table_model = MostExcellentTableModel(
            table_header, self.table_rows, self.parent.temp_dir.path())
        self.create_table_proxy_model()

    def create_table_proxy_model(self):
        self.table_proxy_model = TableProxyModel()
        self.table_proxy_model.setSourceModel(self.table_model)
        self.table_proxy_model.setSortCaseSensitivity(False)
        self.table_proxy_model.sort(0, QtCore.Qt.AscendingOrder)
        self.parent.tableView.setModel(self.table_proxy_model)
        self.parent.tableView.horizontalHeader().setSortIndicator(
            0, QtCore.Qt.AscendingOrder)
        self.update_table_proxy_model()

    def update_table_proxy_model(self):
        self.table_proxy_model.invalidateFilter()
        self.table_proxy_model.setFilterParams(
            self.parent.libraryToolBar.searchBar.text(), [0, 1, 4])
        # This isn't needed, but it forces a model update every time the
        # text in the line edit changes. So I guess it is needed.
        self.table_proxy_model.setFilterFixedString(
            self.parent.libraryToolBar.searchBar.text())

    def create_proxymodel(self):
        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.view_model)
        self.proxy_model.setSortCaseSensitivity(False)
        s = QtCore.QSize(160, 250)  # Set icon sizing here
        self.parent.listView.setIconSize(s)
        self.parent.listView.setModel(self.proxy_model)
        self.update_proxymodel()

    def update_proxymodel(self):
        self.proxy_model.setFilterRole(QtCore.Qt.UserRole + 4)
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy_model.setFilterWildcard(
            self.parent.libraryToolBar.searchBar.text())

        self.parent.statusMessage.setText(
            str(self.proxy_model.rowCount()) + ' books')

        # Sorting according to roles and the drop down in the library
        self.proxy_model.setSortRole(
            QtCore.Qt.UserRole + self.parent.libraryToolBar.sortingBox.currentIndex())
        self.proxy_model.sort(0)
        self.parent.culling_timer.start(100)

    def prune_models(self, valid_paths):
        # To be executed when the library is updated by folder
        # All files in unselected directories will have to be removed
        # from both of the models
        # They will also have to be deleted from the library
        valid_paths = set(valid_paths)

        # Get all paths in the dictionary from either of the models
        # self.table_rows has all file metadata in position 5
        all_paths = [i[5]['path'] for i in self.table_rows]
        all_paths = set(all_paths)

        invalid_paths = all_paths - valid_paths

        # Remove invalid paths from both of the models
        self.table_rows = [
            i for i in self.table_rows if i[5]['path'] not in invalid_paths]

        deletable_persistent_indexes = []
        for i in range(self.view_model.rowCount()):
            item = self.view_model.item(i)
            path = item.data(QtCore.Qt.UserRole + 3)['path']
            if path in invalid_paths:
                deletable_persistent_indexes.append(
                    QtCore.QPersistentModelIndex(item.index()))

        if deletable_persistent_indexes:
            for i in deletable_persistent_indexes:
                self.view_model.removeRow(i.row())

        # Remove invalid paths from the database as well
        database.DatabaseFunctions(
            self.parent.database_path).delete_from_database('Path', invalid_paths)
