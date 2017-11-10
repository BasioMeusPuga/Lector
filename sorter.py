#!/usr/bin/env python3

# TODO
# Methods that return None must be quantified here if needed

import hashlib
from multiprocessing.dummy import Pool

from parsers.epub import ParseEPUB


class BookSorter:
    def __init__(self, file_list):
        # Have the GUI pass a list of files straight to here
        # Then, on the basis of what is needed, pass the
        # filenames to the requisite functions
        # This includes getting file info for the database
        # Parsing for the reader proper
        # Caching upon closing
        self.file_list = file_list
        self.all_books = {}

    def read_book(self, filename):
        # filename is expected as a string containg the
        # full path of the ebook file

        # TODO
        # See if you want to include a hash of the book's name and author
        with open(filename, 'rb') as current_book:
            file_md5 = hashlib.md5(current_book.read()).hexdigest()

        if file_md5 in self.all_books.items():
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
