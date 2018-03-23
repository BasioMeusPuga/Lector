#!usr/bin/env python3

# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2018 BasioMeusPuga

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

from PyQt5 import QtCore, QtGui
from lector import database
from lector.resources import resources


class QImageFactory:
    def __init__(self, parent):
        self.parent = parent

    def get_image(self, image_name):
        icon_theme = self.parent.settings['icon_theme']
        icon_path = f':/images/{icon_theme}/{image_name}.svg'

        this_qicon = QtGui.QIcon(icon_path)
        return this_qicon


class CoverLoadingAndCulling:
    def __init__(self, main_window):
        self.main_window = main_window
        self.lib_ref = self.main_window.lib_ref
        self.listView = self.main_window.listView

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
            self.main_window.database_path).fetch_covers_only(hash_list)

        for i in all_covers:
            book_hash = i[0]
            cover = i[1]
            model_index = hash_index_dict[book_hash]

            book_item = self.lib_ref.view_model.item(model_index.row())
            self.cover_loader(book_item, cover)

    def load_all_covers(self):
        all_covers_db = database.DatabaseFunctions(
            self.main_window.database_path).fetch_data(
                ('Hash', 'CoverImage',),
                'books',
                {'Hash': ''},
                'LIKE')

        if not all_covers_db:
            return

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
