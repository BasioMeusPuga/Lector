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
import pathlib
from multiprocessing.dummy import Pool
from PyQt5 import QtCore, QtGui

from lector import sorter
from lector import database


class BackGroundTabUpdate(QtCore.QThread):
    def __init__(self, database_path, all_metadata, parent=None):
        super(BackGroundTabUpdate, self).__init__(parent)
        self.database_path = database_path
        self.all_metadata = all_metadata

    def run(self):
        for i in self.all_metadata:
            book_hash = i['hash']
            database_dict = {
                'Position': i['position'],
                'LastAccessed': i['last_accessed'],
                'Bookmarks': i['bookmarks']}

            database.DatabaseFunctions(self.database_path).modify_metadata(
                database_dict, book_hash)


class BackGroundBookAddition(QtCore.QThread):
    def __init__(self, file_list, database_path, prune_required, parent=None):
        super(BackGroundBookAddition, self).__init__(parent)
        self.file_list = file_list
        self.parent = parent
        self.database_path = database_path
        self.prune_required = prune_required

    def run(self):
        books = sorter.BookSorter(
            self.file_list,
            'addition',
            self.database_path,
            self.parent.settings['auto_tags'],
            self.parent.temp_dir.path())

        parsed_books = books.initiate_threads()
        if not parsed_books:
            return

        self.parent.lib_ref.generate_model('addition', parsed_books, False)
        if self.prune_required:
            self.parent.lib_ref.prune_models(self.file_list)
        database.DatabaseFunctions(self.database_path).add_to_database(parsed_books)


class BackGroundBookDeletion(QtCore.QThread):
    def __init__(self, hash_list, database_path, parent=None):
        super(BackGroundBookDeletion, self).__init__(parent)
        self.parent = parent
        self.hash_list = hash_list
        self.database_path = database_path

    def run(self):
        database.DatabaseFunctions(
            self.database_path).delete_from_database('Hash', self.hash_list)


class BackGroundBookSearch(QtCore.QThread):
    def __init__(self, data_list, parent=None):
        super(BackGroundBookSearch, self).__init__(parent)
        self.parent = parent
        self.valid_files = []

        # Filter for checked directories
        self.valid_directories = [
            [i[0], i[1], i[2]] for i in data_list if i[3] == QtCore.Qt.Checked]
        self.unwanted_directories = [
            pathlib.Path(i[0]) for i in data_list if i[3] == QtCore.Qt.Unchecked]

    def run(self):
        def is_wanted(directory):
            directory_parents = pathlib.Path(directory).parents
            for i in self.unwanted_directories:
                if i in directory_parents:
                    return False
            return True

        def traverse_directory(incoming_data):
            root_directory = incoming_data[0]
            for directory, subdirs, files in os.walk(root_directory, topdown=True):
                # Black magic fuckery
                # Skip subdir tree in case it's not wanted
                subdirs[:] = [d for d in subdirs if is_wanted(os.path.join(directory, d))]
                for filename in files:
                    if os.path.splitext(filename)[1][1:] in sorter.available_parsers:
                        self.valid_files.append(os.path.join(directory, filename))

        def initiate_threads():
            _pool = Pool(5)
            _pool.map(traverse_directory, self.valid_directories)
            _pool.close()
            _pool.join()

        initiate_threads()
        print(len(self.valid_files), 'books found')


class BackGroundCacheRefill(QtCore.QThread):
    def __init__(self, image_cache, remove_value, filetype, book, all_pages, parent=None):
        super(BackGroundCacheRefill, self).__init__(parent)

        self.image_cache = image_cache
        self.remove_value = remove_value
        self.filetype = filetype
        self.book = book
        self.all_pages = all_pages

    def run(self):
        def load_page(current_page):
            image_pixmap = QtGui.QPixmap()

            if self.filetype in ('cbz', 'cbr'):
                page_data = self.book.read(current_page)
                image_pixmap.loadFromData(page_data)
            elif self.filetype == 'pdf':
                page_data = self.book.page(current_page)
                page_qimage = page_data.renderToImage(350, 350)
                image_pixmap.convertFromImage(page_qimage)
            return image_pixmap

        remove_index = self.image_cache.index(self.remove_value)

        if remove_index == 1:
            first_path = self.image_cache[0][0]
            self.image_cache.pop(3)
            previous_page = self.all_pages[self.all_pages.index(first_path) - 1]
            refill_pixmap = load_page(previous_page)
            self.image_cache.insert(0, (previous_page, refill_pixmap))

        else:
            self.image_cache[0] = self.image_cache[1]
            self.image_cache.pop(1)
            try:
                last_page = self.image_cache[2][0]
                next_page = self.all_pages[self.all_pages.index(last_page) + 1]
                refill_pixmap = load_page(next_page)
                self.image_cache.append((next_page, refill_pixmap))
            except (IndexError, TypeError):
                self.image_cache.append(None)
