#!/usr/bin/env python3
# Every parser is supposed to have the following methods, even if they return None:
# read_book()
# get_title()
# get_author()
# get_year()
# get_cover_image()
# get_isbn
# TODO More for get contents, get TOC

import os
import re

import ebooklib.epub


class ParseEPUB:
    def __init__(self, filename):
        # TODO
        # Maybe also include book description
        self.filename = filename
        self.book = None

    def read_book(self):
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
