#!/usr/bin/env python3

import os
import re
import collections
import ebooklib.epub


class ParseEPUB:
    def __init__(self, filename):
        self.filename = filename
        self.book_title = None
        try:
            self.book = ebooklib.epub.read_epub(filename)
        except (KeyError, AttributeError):
            print('Cannot parse ' + self.filename)
            return

    def get_title(self):
        return self.book.title.strip()

    def get_cover_image(self):
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
            print('Cannot parse ' + self.filename)
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

    def add_to_database(self):
        # Consider multithreading this
        for i in self.file_list:
            book_ref = ParseEPUB(i)
            title = book_ref.get_title()
            cover_image = book_ref.get_cover_image()
            isbn = book_ref.get_isbn()

            print(title, isbn)
