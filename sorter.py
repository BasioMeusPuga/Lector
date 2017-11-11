#!/usr/bin/env python3

# TODO
# Methods that return None must be quantified here if needed

import hashlib
from multiprocessing.dummy import Pool

import database
from parsers.epub import ParseEPUB

class BookSorter:
    def __init__(self, file_list, database_path):
        # Have the GUI pass a list of files straight to here
        # Then, on the basis of what is needed, pass the
        # filenames to the requisite functions
        # This includes getting file info for the database
        # Parsing for the reader proper
        # Caching upon closing
        self.file_list = file_list
        self.all_books = {}
        self.database_path = database_path
        self.hashes = []
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

    def read_book(self, filename):
        # filename is expected as a string containg the
        # full path of the ebook file

        with open(filename, 'rb') as current_book:
            file_md5 = hashlib.md5(current_book.read()).hexdigest()

        # Do not allow addition in case the file is dupicated in the directory
        # OR is already in the database
        # TODO
        # See if you want to include a hash of the book's name and author
        if file_md5 in self.all_books.items() or file_md5 in self.hashes:
            return

        # TODO
        # See if tags can be generated from book content
        # Sort according to to file extension here
        book_ref = ParseEPUB(filename)

        # Everything following this is standard
        # Some of the None returns will have to have
        # values associated with them, though
        book_ref.read_book()
        if book_ref.book:
            title = book_ref.get_title()
            author = book_ref.get_author()
            year = book_ref.get_year()
            cover_image = book_ref.get_cover_image()
            isbn = book_ref.get_isbn()

            self.all_books[file_md5] = {
                'title': title,
                'author': author,
                'year': year,
                'isbn': isbn,
                'path': filename,
                'cover_image': cover_image}

    def initiate_threads(self):
        _pool = Pool(5)
        _pool.map(self.read_book, self.file_list)
        _pool.close()
        _pool.join()

        return self.all_books
