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
import pickle
import pathlib
from PyQt5 import QtGui, QtCore

import database
from models import TableProxyModel, ItemProxyModel


class Library:
    def __init__(self, parent):
        self.parent = parent
        self.view_model = None
        self.item_proxy_model = None
        self.table_proxy_model = None

    def generate_model(self, mode, parsed_books=None, is_database_ready=True):
        if mode == 'build':
            self.view_model = QtGui.QStandardItemModel()
            self.view_model.setColumnCount(10)

            books = database.DatabaseFunctions(
                self.parent.database_path).fetch_data(
                    ('Title', 'Author', 'Year', 'DateAdded', 'Path',
                     'Position', 'ISBN', 'Tags', 'Hash', 'LastAccessed'),
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
            current_qdatetime = QtCore.QDateTime().currentDateTime()
            for i in parsed_books.items():
                _tags = i[1]['tags']
                if _tags:
                    _tags = ', '.join([j for j in _tags if j])

                books.append([
                    i[1]['title'], i[1]['author'], i[1]['year'], current_qdatetime,
                    i[1]['path'], None, i[1]['isbn'], _tags, i[0], None])

        else:
            return

        for i in books:
            # The database query returns (or the extension data is)
            # an iterable with the following indices:
            title = i[0]
            author = i[1]
            year = i[2]
            path = i[4]
            last_accessed = i[9]

            tags = i[7]
            if isinstance(tags, list):  # When files are added for the first time
                if tags:
                    tags = ', '.join(str(this_tag) for this_tag in tags)
                else:
                    tags = None

            try:
                date_added = pickle.loads(i[3])
            except TypeError:  # Because of datetime.datetime.now() above
                date_added = i[3]

            position_perc = None
            position = i[5]
            if position:
                position = pickle.loads(position)
                if position['is_read']:
                    position_perc = 100
                else:
                    try:
                        position_perc = (
                            position['current_chapter'] * 100 / position['total_chapters'])
                    except KeyError:
                        position_perc = None

            file_exists = os.path.exists(path)

            all_metadata = {
                'title': title,
                'author': author,
                'year': year,
                'date_added': date_added,
                'path': path,
                'position': position,
                'isbn': i[6],
                'tags': tags,
                'hash': i[8],
                'last_accessed': last_accessed,
                'file_exists': file_exists}

            tooltip_string = title + '\nAuthor: ' + author + '\nYear: ' + str(year)

            # Additional data can be set using an incrementing
            # QtCore.Qt.UserRole
            # QtCore.Qt.DisplayRole is the same as item.setText()
            # The model is a single row and has no columns

            # No covers are set at this time
            # That is to be achieved by way of the culling function
            img_pixmap = QtGui.QPixmap()
            img_pixmap.load(':/images/blank.png')
            img_pixmap = img_pixmap.scaled(
                420, 600, QtCore.Qt.IgnoreAspectRatio)
            item = QtGui.QStandardItem()
            item.setToolTip(tooltip_string)

            # Just keep the following order. It's way too much trouble otherwise
            item.setData(title, QtCore.Qt.UserRole)
            item.setData(author, QtCore.Qt.UserRole + 1)
            item.setData(year, QtCore.Qt.UserRole + 2)
            item.setData(all_metadata, QtCore.Qt.UserRole + 3)
            item.setData(tags, QtCore.Qt.UserRole + 4)
            item.setData(file_exists, QtCore.Qt.UserRole + 5)
            item.setData(i[8], QtCore.Qt.UserRole + 6)  # File hash
            item.setData(position_perc, QtCore.Qt.UserRole + 7)
            item.setData(False, QtCore.Qt.UserRole + 8) # Is the cover being displayed?
            item.setData(date_added, QtCore.Qt.UserRole + 9)
            item.setData(last_accessed, QtCore.Qt.UserRole + 12)
            item.setIcon(QtGui.QIcon(img_pixmap))

            self.view_model.appendRow(item)

        # The is_database_ready boolean is required when a new thread sends
        # books here for model generation.
        if not self.parent.settings['perform_culling'] and is_database_ready:
            self.parent.load_all_covers()

    def generate_proxymodels(self):
        self.item_proxy_model = ItemProxyModel()
        self.item_proxy_model.setSourceModel(self.view_model)
        self.item_proxy_model.setSortCaseSensitivity(False)
        s = QtCore.QSize(160, 250)  # Set icon sizing here
        self.parent.listView.setIconSize(s)
        self.parent.listView.setModel(self.item_proxy_model)

        self.table_proxy_model = TableProxyModel(self.parent.temp_dir.path())
        self.table_proxy_model.setSourceModel(self.view_model)
        self.table_proxy_model.setSortCaseSensitivity(False)
        self.parent.tableView.setModel(self.table_proxy_model)

        self.update_proxymodels()

    def update_proxymodels(self):
        # Table proxy model
        self.table_proxy_model.invalidateFilter()
        self.table_proxy_model.setFilterParams(
            self.parent.libraryToolBar.searchBar.text(),
            self.parent.active_library_filters,
            0) # This doesn't need to know the sorting box position
        self.table_proxy_model.setFilterFixedString(
            self.parent.libraryToolBar.searchBar.text())
        # ^^^ This isn't needed, but it forces a model update every time the
        # text in the line edit changes. So I guess it is needed.

        # Item proxy model
        self.item_proxy_model.invalidateFilter()
        self.item_proxy_model.setFilterParams(
            self.parent.libraryToolBar.searchBar.text(),
            self.parent.active_library_filters,
            self.parent.libraryToolBar.sortingBox.currentIndex())
        self.item_proxy_model.setFilterFixedString(
            self.parent.libraryToolBar.searchBar.text())

        self.parent.statusMessage.setText(
            str(self.item_proxy_model.rowCount()) + ' books')

        # TODO
        # Allow sorting by type

        # Index of the sorting drop down corresponding to the
        # UserRole of the item model
        # This keeps from having to rearrange all the UserRoles in the
        # existing model
        sort_roles = {
            0: 0,
            1: 1,
            2: 2,
            3: 9,
            4: 12}

        # Sorting according to roles and the drop down in the library toolbar
        self.item_proxy_model.setSortRole(
            QtCore.Qt.UserRole + sort_roles[self.parent.libraryToolBar.sortingBox.currentIndex()])

        # This can be expanded to other fields by appending to the list
        sort_order = QtCore.Qt.AscendingOrder
        if self.parent.libraryToolBar.sortingBox.currentIndex() in [3, 4]:
            sort_order = QtCore.Qt.DescendingOrder

        self.item_proxy_model.sort(0, sort_order)
        self.parent.start_culling_timer()

    def generate_library_tags(self):
        db_library_directories = database.DatabaseFunctions(
            self.parent.database_path).fetch_data(
                ('Path', 'Name', 'Tags'),
                'directories',  # This checks the directories table NOT the book one
                {'Path': ''},
                'LIKE')

        if not db_library_directories:  # Empty database / table
            return

        library_directories = {
            i[0]: (i[1], i[2]) for i in db_library_directories}

        def get_tags(all_metadata):
            path = os.path.dirname(all_metadata['path'])
            path_ref = pathlib.Path(path)

            for i in library_directories:
                if i == path or pathlib.Path(i) in path_ref.parents:
                    directory_name = library_directories[i][0]
                    if directory_name:
                        directory_name = directory_name.lower()
                    else:
                        directory_name = path.rsplit('/')[-1].lower()

                    directory_tags = library_directories[i][1]
                    if directory_tags:
                        directory_tags = directory_tags.lower()

                    return directory_name, directory_tags

            return 'manually added', None

        # Generate tags for the QStandardItemModel
        for i in range(self.view_model.rowCount()):
            this_item = self.view_model.item(i, 0)
            all_metadata = this_item.data(QtCore.Qt.UserRole + 3)
            directory_name, directory_tags = get_tags(all_metadata)

            this_item.setData(directory_name, QtCore.Qt.UserRole + 10)
            this_item.setData(directory_tags, QtCore.Qt.UserRole + 11)

    def prune_models(self, valid_paths):
        # To be executed when the library is updated by folder
        # All files in unselected directories will have to be removed
        # from both of the models
        # They will also have to be deleted from the library
        valid_paths = set(valid_paths)

        # Get all paths
        all_paths = set()
        for i in range(self.view_model.rowCount()):
            item = self.view_model.item(i, 0)
            item_metadata = item.data(QtCore.Qt.UserRole + 3)
            book_path = item_metadata['path']
            all_paths.add(book_path)

        invalid_paths = all_paths - valid_paths

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
