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
import re
import logging
import pathlib
from multiprocessing.dummy import Pool

from PyQt5 import QtCore, QtGui

from lector import sorter
from lector import database
from lector.parsers.pdf import render_pdf_page

logger = logging.getLogger(__name__)


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
                'Bookmarks': i['bookmarks'],
                'Annotations': i['annotations']}

            database.DatabaseFunctions(self.database_path).modify_metadata(
                database_dict, book_hash)


class BackGroundBookAddition(QtCore.QThread):
    def __init__(self, file_list, database_path, addition_mode, main_window, parent=None):
        super(BackGroundBookAddition, self).__init__(parent)
        self.file_list = file_list
        self.database_path = database_path
        self.addition_mode = addition_mode
        self.main_window = main_window

        self.prune_required = True
        if self.addition_mode == 'manual':
            self.prune_required = False

    def run(self):
        books = sorter.BookSorter(
            self.file_list,
            ('addition', self.addition_mode),
            self.database_path,
            self.main_window.settings['auto_tags'],
            self.main_window.temp_dir.path())

        parsed_books = books.initiate_threads()
        self.main_window.lib_ref.generate_model('addition', parsed_books, False)
        database.DatabaseFunctions(self.database_path).add_to_database(parsed_books)

        if self.prune_required:
            self.main_window.lib_ref.prune_models(self.file_list)


class BackGroundBookDeletion(QtCore.QThread):
    def __init__(self, hash_list, database_path, parent=None):
        super(BackGroundBookDeletion, self).__init__(parent)
        self.hash_list = hash_list
        self.database_path = database_path

    def run(self):
        database.DatabaseFunctions(
            self.database_path).delete_from_database('Hash', self.hash_list)


class BackGroundBookSearch(QtCore.QThread):
    def __init__(self, data_list, parent=None):
        super(BackGroundBookSearch, self).__init__(parent)
        self.valid_files = []

        # Filter for checked directories
        self.valid_directories = [
            [i[0], i[1], i[2]] for i in data_list if i[
                3] == QtCore.Qt.Checked and os.path.exists(i[0])]
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

        if self.valid_directories:
            initiate_threads()
            if self.valid_files:
                info_string = str(len(self.valid_files)) + ' books found'
                logger.info(info_string)
            else:
                logger.error('No books found on scan')
        else:
            logger.error('No valid directories')


class BackGroundCacheRefill(QtCore.QThread):
    def __init__(self, image_cache, remove_value, filetype, book, all_pages, parent=None):
        super(BackGroundCacheRefill, self).__init__(parent)

        # TODO
        # Return with only the first image in case of a cache miss
        # Rebuilding the entire n image cache takes considerably longer

        self.image_cache = image_cache
        self.remove_value = remove_value
        self.filetype = filetype
        self.book = book
        self.all_pages = all_pages

    def run(self):
        def load_page(current_page):
            pixmap = QtGui.QPixmap()

            if self.filetype in ('cbz', 'cbr'):
                page_data = self.book.read(current_page)
                pixmap.loadFromData(page_data)

            elif self.filetype == 'pdf':
                page_data = self.book.loadPage(current_page)
                pixmap = render_pdf_page(page_data)

            return pixmap

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


class BackGroundTextSearch(QtCore.QThread):
    def __init__(self):
        super(BackGroundTextSearch, self).__init__(None)
        self.search_content = None
        self.search_text = None
        self.case_sensitive = False
        self.match_words = False
        self.search_results = []

    def set_search_options(
            self, search_content, search_text,
            case_sensitive, match_words):
        self.search_content = search_content
        self.search_text = search_text
        self.case_sensitive = case_sensitive
        self.match_words = match_words

    def run(self):
        if not self.search_text or len(self.search_text) < 3:
            return

        def get_surrounding_text(textCursor, words_before):
            textCursor.movePosition(
                QtGui.QTextCursor.WordLeft,
                QtGui.QTextCursor.MoveAnchor,
                words_before)
            textCursor.movePosition(
                QtGui.QTextCursor.NextWord,
                QtGui.QTextCursor.KeepAnchor,
                words_before * 2)
            cursor_selection = textCursor.selection().toPlainText()
            return cursor_selection.replace('\n', '')

        self.search_results = {}

        # Create a new QTextDocument of each chapter and iterate
        # through it looking for hits

        for i in self.search_content:
            chapter_title = i[0]
            chapterDocument = QtGui.QTextDocument()
            chapterDocument.setHtml(i[1])
            chapter_number = i[2]

            findFlags = QtGui.QTextDocument.FindFlags(0)
            if self.match_words:
                findFlags = findFlags | QtGui.QTextDocument.FindWholeWords
            if self.case_sensitive:
                findFlags = findFlags | QtGui.QTextDocument.FindCaseSensitively

            findResultCursor = chapterDocument.find(self.search_text, 0, findFlags)
            while not findResultCursor.isNull():
                result_position = findResultCursor.position()

                words_before = 3
                while True:
                    surroundingTextCursor = QtGui.QTextCursor(chapterDocument)
                    surroundingTextCursor.setPosition(
                        result_position, QtGui.QTextCursor.MoveAnchor)
                    surrounding_text = get_surrounding_text(
                        surroundingTextCursor, words_before)
                    words_before += 1
                    if surrounding_text[:2] not in ('. ', ', '):
                        break

                # Case insensitive replace for find results
                replace_pattern = re.compile(re.escape(self.search_text), re.IGNORECASE)
                surrounding_text = replace_pattern.sub(
                    f'<b>{self.search_text}</b>', surrounding_text)

                result_tuple = (
                    result_position, surrounding_text, self.search_text, chapter_number)

                try:
                    self.search_results[chapter_title].append(result_tuple)
                except KeyError:
                    self.search_results[chapter_title] = [result_tuple]

                new_position = result_position + len(self.search_text)
                findResultCursor = chapterDocument.find(
                    self.search_text, new_position, findFlags)
