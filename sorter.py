#!/usr/bin/env python3

# TODO
# See if you want to include a hash of the book's name and author

import io
import os
import pickle
import hashlib
from multiprocessing.dummy import Pool
from PyQt5 import QtCore, QtGui

import database

# Every parser is supposed to have the following methods, even if they return None:
# read_book()
# get_title()
# get_author()
# get_year()
# get_cover_image()
# get_isbn()
# get_contents() - Should return a tuple with 0: TOC 1: special_settings (dict)
# Parsers for files containing only images need to return only images_only = True

from parsers.epub import ParseEPUB
from parsers.cbz import ParseCBZ
from parsers.cbr import ParseCBR

available_parsers = ['epub', 'cbz', 'cbr']
progressbar = None  # This is populated by __main__


# This is for thread safety
class UpdateProgress(QtCore.QObject):
    update_signal = QtCore.pyqtSignal(int)

    def connect_to_progressbar(self):
        self.update_signal.connect(progressbar.setValue)

    def update_progress(self, progress_percent):
        self.update_signal.emit(progress_percent)


class BookSorter:
    def __init__(self, file_list, mode, database_path, temp_dir=None):
        # Have the GUI pass a list of files straight to here
        # Then, on the basis of what is needed, pass the
        # filenames to the requisite functions
        # This includes getting file info for the database
        # Parsing for the reader proper
        # Caching upon closing
        self.file_list = [i for i in file_list if os.path.exists(i)]
        self.statistics = [0, (len(file_list))]
        self.all_books = {}
        self.hashes = []
        self.mode = mode
        self.database_path = database_path
        self.temp_dir = temp_dir
        if database_path:
            self.database_hashes()

        if self.mode == 'addition':
            self.progress_emitter = UpdateProgress()
            self.progress_emitter.connect_to_progressbar()

    def database_hashes(self):
        # TODO
        # Overwrite book if deleted and then re-added
        # Also fetch the path of the file here

        all_hashes = database.DatabaseFunctions(
            self.database_path).fetch_data(
                ('Hash',),
                'books',
                {'Hash': ''},
                'LIKE')

        if all_hashes:
            self.hashes = [i[0] for i in all_hashes]

    def database_position(self, file_hash):
        position = database.DatabaseFunctions(
            self.database_path).fetch_data(
                ('Position',),
                'books',
                {'Hash': file_hash},
                'EQUALS',
                True)

        if position:
            position_dict = pickle.loads(position)
            return position_dict
        else:
            return None

    def read_book(self, filename):
        # filename is expected as a string containg the
        # full path of the ebook file

        with open(filename, 'rb') as current_book:
            # This should speed up addition for larger files
            # without compromising the integrity of the process
            first_bytes = current_book.read(1024 * 32)  # First 32KB of the file
            salt = 'Caesar si viveret, ad remum dareris'.encode()
            first_bytes += salt
            file_md5 = hashlib.md5(first_bytes).hexdigest()

        if self.mode == 'addition':
            self.statistics[0] += 1
            self.progress_emitter.update_progress(
                self.statistics[0] * 100 // self.statistics[1])

        # IF the file is NOT being loaded into the reader,
        # Do not allow addition in case the file is dupicated in the directory
        # OR is already in the database
        # This should not get triggered in reading mode
        if (self.mode == 'addition'
                and (file_md5 in self.all_books.items() or file_md5 in self.hashes)):
            return

        # ___________SORTING TAKES PLACE HERE___________
        sorter = {
            'epub': ParseEPUB,
            'cbz': ParseCBZ,
            'cbr': ParseCBR
        }

        file_extension = os.path.splitext(filename)[1][1:]
        try:
            book_ref = sorter[file_extension](filename, self.temp_dir, file_md5)
        except KeyError:
            print(filename + ' has an unsupported extension')
            return

        # Everything following this is standard
        # None values are accounted for here
        book_ref.read_book()
        if book_ref.book:

            title = book_ref.get_title().title()

            author = book_ref.get_author()
            if not author:
                author = 'Unknown'

            try:
                year = int(book_ref.get_year())
            except (TypeError, ValueError):
                year = 9999

            isbn = book_ref.get_isbn()

            # Different modes require different values
            if self.mode == 'addition':
                cover_image_raw = book_ref.get_cover_image()
                if cover_image_raw:
                    # Reduce the size of the incoming image
                    cover_image = resize_image(cover_image_raw)
                else:
                    cover_image = None

                self.all_books[file_md5] = {
                    'title': title,
                    'author': author,
                    'year': year,
                    'isbn': isbn,
                    'path': filename,
                    'cover_image': cover_image}

            if self.mode == 'reading':
                all_content = book_ref.get_contents()

                # get_contents() returns a tuple. Index 1 is a collection of
                # special settings that depend on the kind of data being parsed.
                # Currently, this includes:
                # Only images included      images_only     BOOL    Specify only paths to images
                #                                                   File will not be cached on exit

                content = all_content[0]
                images_only = all_content[1]['images_only']

                if not content.keys():
                    content['Invalid'] = 'Possible Parse Error'

                position = self.database_position(file_md5)
                self.all_books[file_md5] = {
                    'title': title,
                    'author': author,
                    'year': year,
                    'isbn': isbn,
                    'hash': file_md5,
                    'path': filename,
                    'position': position,
                    'content': content,
                    'images_only': images_only}


    def initiate_threads(self):
        _pool = Pool(5)
        _pool.map(self.read_book, self.file_list)
        _pool.close()
        _pool.join()

        return self.all_books


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
