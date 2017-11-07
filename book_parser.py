#!/usr/bin/env python3

import os
import re
import hashlib
from multiprocessing.dummy import Pool

import ebooklib.epub


class ParseEPUB:
    def __init__(self, filename):
        # TODO
        # Maybe also include book description
        self.filename = filename
        self.book = None

    def read_epub(self):
        try:
            self.book = ebooklib.epub.read_epub(self.filename)
        except (KeyError, AttributeError):
            print('Cannot parse ' + self.filename)
            return

    def get_title(self):
        return self.book.title.strip()

    def get_author(self):
        try:
            return self.book.metadata['http://purl.org/dc/elements/1.1/']['creator'][0][0]
        except KeyError:
            return None

    def get_year(self):
        try:
            return self.book.metadata['http://purl.org/dc/elements/1.1/']['date'][0][0][:4]
        except KeyError:
            return None

    def get_cover_image(self):
        # TODO
        # Generate a cover image in case one isn't found
        # This has to be done or the database module will
        # error out

        # Get cover image
        # This seems hack-ish, but that's never stopped me before
        image_path = None
        try:
            cover = self.book.metadata['http://www.idpf.org/2007/opf']['cover'][0][1]['content']
            cover_item = self.book.get_item_with_id(cover)
            if cover_item:
                return cover_item.get_content()

            # In case no cover_item is returned,
            # we look for a cover in the guide
            for j in self.book.guide:
                try:
                    if (j['title'].lower in ['cover', 'cover-image', 'coverimage'] or
                            j['type'] == 'coverimagestandard'):
                        image_path = j['href']
                    break
                except KeyError:
                    pass

            # And if all else fails, we find
            # the first image referenced in the book
            # Fuck everything
            if not image_path:
                for j in self.book.items:
                    if j.media_type == 'application/xhtml+xml':
                        _regex = re.search(r"src=\"(.*)\"\/", j.content.decode('utf-8'))
                        if _regex:
                            image_path = _regex[1]
                        break

            for k in self.book.get_items_of_type(ebooklib.ITEM_IMAGE):
                if os.path.basename(k.file_name) == os.path.basename(image_path):
                    image_content = k.get_content()
                    break

            return image_content

        except KeyError:
            return

    def get_isbn(self):
        try:
            identifier = self.book.metadata['http://purl.org/dc/elements/1.1/']['identifier']
            for i in identifier:
                identifier_provider = i[1]['{http://www.idpf.org/2007/opf}scheme']
                if identifier_provider.lower() == 'isbn':
                    isbn = i[0]
                    return isbn
        except KeyError:
            return


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
        book_ref = ParseEPUB(filename)
        book_ref.read_epub()
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
