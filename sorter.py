#!/usr/bin/env python3

# TODO
# See if tags can be generated from book content
# See if you want to include a hash of the book's name and author

import os
import pickle
import hashlib
from multiprocessing.dummy import Pool

import database

# Every parser is supposed to have the following methods, even if they return None:
# read_book()
# get_title()
# get_author()
# get_year()
# get_cover_image()
# get_isbn()
# get_contents() - Should return a tuple with 0: TOC 1: Deletable temp_directory
# Parsers for files containing only images need to return only
# the image path, and images_only = True

from parsers.epub import ParseEPUB
from parsers.cbz import ParseCBZ
from parsers.cbr import ParseCBR


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
        if database_path and self.mode == 'reading':
            self.database_hashes()

    def database_hashes(self):
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
            file_md5 = hashlib.md5(current_book.read()).hexdigest()

        # TODO
        # Make use of this
        # self.statistics[0] += 1
        # print(self.statistics)

        # IF the file is NOT being loaded into the reader,
        # Do not allow addition in case the file is dupicated in the directory
        # OR is already in the database
        # This should not get triggered in reading mode
        if (self.mode == 'addition'
                and (file_md5 in self.all_books.items() or file_md5 in self.hashes)):
            return

        # ___________SORTING TAKES PLACE HERE___________
        try:
            file_extension = os.path.splitext(filename)[1][1:]
            if file_extension == 'epub':
                book_ref = ParseEPUB(filename, self.temp_dir, file_md5)
            if file_extension == 'cbz':
                book_ref = ParseCBZ(filename, self.temp_dir, file_md5)
            if file_extension == 'cbr':
                book_ref = ParseCBR(filename, self.temp_dir, file_md5)
        except IndexError:
            return

        # Everything following this is standard
        # None values are accounted for here
        book_ref.read_book()
        if book_ref.book:
            title = book_ref.get_title().title()
            author = book_ref.get_author()
            if not author:
                author = 'Unknown'
            year = book_ref.get_year()
            if not year:
                year = 9999
            isbn = book_ref.get_isbn()

            # Different modes require different values
            if self.mode == 'addition':
                cover_image = book_ref.get_cover_image()
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
