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

# INSTRUCTIONS
# Every parser is supposed to have the following methods, even if they return None:
# read_book()
# get_title()
# get_author()
# get_year()
# get_cover_image()
# get_isbn()
# get_tags()
# get_contents() - Should return a tuple with 0: TOC 1: special_settings (dict)
# Parsers for files containing only images need to return only images_only = True

# TODO
# Maybe shift to insert or replace instead of hash checking
# See if you want to include a hash of the book's name and author
# Change thread niceness

import io
import os
import time
import pickle
import hashlib
import threading
from multiprocessing import Pool, Manager
from PyQt5 import QtCore, QtGui

from lector import database

from parsers.cbz import ParseCBZ
from parsers.cbr import ParseCBR
from parsers.epub import ParseEPUB
from parsers.mobi import ParseMOBI

sorter = {
    'epub': ParseEPUB,
    'mobi': ParseMOBI,
    'azw': ParseMOBI,
    'azw3': ParseMOBI,
    'azw4': ParseMOBI,
    'prc': ParseMOBI,
    'cbz': ParseCBZ,
    'cbr': ParseCBR,}

available_parsers = [i for i in sorter]
progressbar = None  # This is populated by __main__
progress_emitter = None  # This is to be made into a global variable


class UpdateProgress(QtCore.QObject):
    # This is for thread safety
    update_signal = QtCore.pyqtSignal(int)

    def connect_to_progressbar(self):
        self.update_signal.connect(progressbar.setValue)

    def update_progress(self, progress_percent):
        self.update_signal.emit(progress_percent)


class BookSorter:
    def __init__(self, file_list, mode, database_path, auto_tags=True, temp_dir=None):
        # Have the GUI pass a list of files straight to here
        # Then, on the basis of what is needed, pass the
        # filenames to the requisite functions
        # This includes getting file info for the database
        # Parsing for the reader proper
        # Caching upon closing
        self.file_list = [i for i in file_list if os.path.exists(i)]
        self.statistics = [0, (len(file_list))]
        self.hashes_and_paths = {}
        self.mode = mode
        self.database_path = database_path
        self.auto_tags = auto_tags
        self.temp_dir = temp_dir
        if database_path:
            self.database_hashes()

        self.threading_completed = []
        self.queue = Manager().Queue()
        self.processed_books = []

        if self.mode == 'addition':
            progress_object_generator()

    def database_hashes(self):
        all_hashes_and_paths = database.DatabaseFunctions(
            self.database_path).fetch_data(
                ('Hash', 'Path'),
                'books',
                {'Hash': ''},
                'LIKE')

        if all_hashes_and_paths:
            # self.hashes = [i[0] for i in all_hashes]
            self.hashes_and_paths = {
                i[0]: i[1] for i in all_hashes_and_paths}

    def database_entry_for_book(self, file_hash):
        database_return = database.DatabaseFunctions(
            self.database_path).fetch_data(
                ('Position', 'Bookmarks'),
                'books',
                {'Hash': file_hash},
                'EQUALS')[0]

        book_data = []
        for i in database_return:
            # All of these values are pickled and stored
            if i:
                book_data.append(pickle.loads(i))
            else:
                book_data.append(None)
        return book_data

    def read_book(self, filename):
        # filename is expected as a string containg the
        # full path of the ebook file

        with open(filename, 'rb') as current_book:
            # This should speed up addition for larger files
            # without compromising the integrity of the process
            first_bytes = current_book.read(1024 * 32)  # First 32KB of the file
            file_md5 = hashlib.md5(first_bytes).hexdigest()

        # Update the progress queue
        self.queue.put(filename)

        # This should not get triggered in reading mode
        # IF the file is NOT being loaded into the reader,

        # Do not allow addition in case the file
        # is already in the database and it remains at its original path
        if self.mode == 'addition' and file_md5 in self.hashes_and_paths:
            if self.hashes_and_paths[file_md5] == filename:
                return

        file_extension = os.path.splitext(filename)[1][1:]
        try:
            # Get the requisite parser from the sorter dict
            book_ref = sorter[file_extension](filename, self.temp_dir, file_md5)
        except KeyError:
            print(filename + ' has an unsupported extension')
            return

        # Everything following this is standard
        # None values are accounted for here
        book_ref.read_book()
        if book_ref.book:

            title = book_ref.get_title()

            author = book_ref.get_author()
            if not author:
                author = 'Unknown'

            try:
                year = int(book_ref.get_year())
            except (TypeError, ValueError):
                year = 9999

            isbn = book_ref.get_isbn()

            tags = None
            if self.auto_tags:
                tags = book_ref.get_tags()

            this_book = {}
            this_book[file_md5] = {
                'title': title,
                'author': author,
                'year': year,
                'isbn': isbn,
                'hash': file_md5,
                'path': filename,
                'tags': tags}

            # Different modes require different values
            if self.mode == 'addition':
                # Reduce the size of the incoming image
                # if one is found

                cover_image_raw = book_ref.get_cover_image()
                if cover_image_raw:
                    cover_image = resize_image(cover_image_raw)
                else:
                    cover_image = None

                this_book[file_md5]['cover_image'] = cover_image

            if self.mode == 'reading':
                all_content = book_ref.get_contents()

                # get_contents() returns a tuple. Index 1 is a collection of
                # special settings that depend on the kind of data being parsed.
                # Currently, this includes:
                # Only images included      images_only     BOOL    Specify only paths to images
                #                                                   File will not be cached on exit

                content = all_content[0]
                images_only = all_content[1]['images_only']

                if not content:
                    content = [('Invalid', 'Something went horribly wrong')]

                book_data = self.database_entry_for_book(file_md5)
                position = book_data[0]
                bookmarks = book_data[1]

                this_book[file_md5]['position'] = position
                this_book[file_md5]['bookmarks'] = bookmarks
                this_book[file_md5]['content'] = content
                this_book[file_md5]['images_only'] = images_only

            return this_book

    def read_progress(self):
        while True:
            processed_file = self.queue.get()
            self.threading_completed.append(processed_file)

            total_number = len(self.file_list)
            completed_number = len(self.threading_completed)

            if progress_emitter:  # Skip update in reading mode
                progress_emitter.update_progress(
                    completed_number * 100 // total_number)

            if total_number == completed_number:
                break

    def initiate_threads(self):
        def pool_creator():
            _pool = Pool(5)
            self.processed_books = _pool.map(
                self.read_book, self.file_list)

            _pool.close()
            _pool.join()

        start_time = time.time()

        worker_thread = threading.Thread(target=pool_creator)
        progress_thread = threading.Thread(target=self.read_progress)
        worker_thread.start()
        progress_thread.start()

        worker_thread.join()
        progress_thread.join(timeout=.5)

        return_books = {}
        # Exclude None returns generated in case of duplication / parse errors
        self.processed_books = [i for i in self.processed_books if i]
        for i in self.processed_books:
            for j in i:
                return_books[j] = i[j]

        del self.processed_books
        print('Finished processing in', time.time() - start_time)
        return return_books


def progress_object_generator():
    # This has to be kept separate from the BookSorter class because
    # the QtObject inheritance disallows pickling
    global progress_emitter
    progress_emitter = UpdateProgress()
    progress_emitter.connect_to_progressbar()


def resize_image(cover_image_raw):
    cover_image = QtGui.QImage()
    cover_image.loadFromData(cover_image_raw)
    cover_image = cover_image.scaled(
        420, 600, QtCore.Qt.IgnoreAspectRatio)

    byte_array = QtCore.QByteArray()
    buffer = QtCore.QBuffer(byte_array)
    buffer.open(QtCore.QIODevice.WriteOnly)
    cover_image.save(buffer, 'jpg', 75)

    cover_image_final = io.BytesIO(byte_array)
    cover_image_final.seek(0)
    return cover_image_final.getvalue()
