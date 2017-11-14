#!/usr/bin/env python3

import os
import pickle
import database

from PyQt5 import QtWidgets, QtGui, QtCore
from widgets import MyAbsModel


class Library:
    def __init__(self, parent):
        self.parent_window = parent
        self.proxy_model = None

    def generate_model(self):
        # The QlistView widget needs to be populated
        # with a model that inherits from QStandardItemModel
        # self.parent_window.viewModel = QtGui.QStandardItemModel()
        self.parent_window.viewModel = MyAbsModel()

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

            position = i[5]
            if position:
                position = pickle.loads(position)

            all_metadata = {
                'title': title,
                'author': author,
                'year': year,
                'path': path,
                'position': position,
                'isbn': i[6],
                'tags': tags,
                'hash': i[8]}

            tooltip_string = title + '\nAuthor: ' + author + '\nYear: ' + str(year)
            if tags:
                tooltip_string += ('\nTags: ' + tags)

            # This remarkably ugly hack is because the QSortFilterProxyModel
            # doesn't easily allow searching through multiple item roles
            search_workaround = title + ' ' + author
            if tags:
                search_workaround += tags

            file_exists = os.path.exists(path)

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
            item.setData(file_exists, QtCore.Qt.UserRole + 5)
            item.setData(i[8], QtCore.Qt.UserRole + 6)  # File hash
            item.setData(position, QtCore.Qt.UserRole + 7)
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
