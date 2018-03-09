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
import re
import sys
import shutil
import zipfile
import collections
from urllib.parse import unquote

import ebooklib.epub
import KindleUnpack.kindleunpack as KindleUnpack


class ParseEBook:
    def __init__(self, filename, temp_dir, file_md5):
        # TODO
        # Maybe also include book description
        self.filename = filename
        self.filename_copy = filename
        self.book = None
        self.temp_dir = temp_dir
        self.temp_dir_copy = temp_dir
        self.file_md5 = file_md5

        # This is a crazy lazy thing
        # But it works for now

        self.use_KindleUnpack = False
        kindle_extensions = ['.mobi', '.azw', '.azw3', '.azw4', '.prc']
        if os.path.splitext(self.filename)[1].lower() in kindle_extensions:
            self.use_KindleUnpack = True
            self.temp_dir = os.path.join(
                self.temp_dir, os.path.basename(self.filename))

    def read_book(self):
        if self.use_KindleUnpack:
            with HidePrinting():
                KindleUnpack.unpackBook(self.filename, self.temp_dir)

            new_filename_with_ext = os.path.splitext(
                os.path.basename(self.filename))[0] + '.epub'

            self.filename = os.path.join(
                self.temp_dir, 'mobi8', new_filename_with_ext)
            if not os.path.exists(self.filename):
                zip_dir = os.path.join(self.temp_dir, 'mobi7')
                zip_file = os.path.join(
                    self.temp_dir_copy, new_filename_with_ext)
                self.filename = shutil.make_archive(zip_file, 'zip', zip_dir)

            self.temp_dir = self.temp_dir_copy

        try:
            self.book = ebooklib.epub.read_epub(self.filename)
        except (KeyError, AttributeError):
            print('Cannot parse ' + self.filename)
            return
        except FileNotFoundError:
            print('Intermediate FNF: ' + self.filename_copy)
            return

    def get_title(self):
        return self.book.title.strip()

    def get_author(self):
        try:
            return self.book.metadata['http://purl.org/dc/elements/1.1/']['creator'][0][0]
        except KeyError:
            return

    def get_year(self):
        try:
            return self.book.metadata['http://purl.org/dc/elements/1.1/']['date'][0][0][:4]
        except KeyError:
            return

    def get_cover_image(self):
        # Get cover image
        # This seems hack-ish, but that's never stopped me before
        image_path = None
        try:
            cover = self.book.metadata['http://www.idpf.org/2007/opf']['cover'][0][1]['content']
            cover_item = self.book.get_item_with_id(cover)
            if cover_item:
                return cover_item.get_content()
        except KeyError:
            pass

        # In case no cover_item is returned, we look for a cover in the guide
        for i in self.book.guide:
            try:
                if (i['title'].lower in ['cover', 'cover-image', 'coverimage'] or
                        i['type'] == 'coverimagestandard'):
                    image_path = i['href']
                break
            except KeyError:
                pass

        # If that fails, we find the first image referenced in the book
        if not image_path:
            for i in self.book.items:
                if i.media_type == 'application/xhtml+xml':
                    _regex = re.search(r"src=\"(.*)\"\/", i.content.decode('utf-8'))
                    if _regex:
                        image_path = _regex[1]
                    break

        if image_path:
            for i in self.book.get_items_of_type(ebooklib.ITEM_IMAGE):
                if os.path.basename(i.file_name) == os.path.basename(image_path):
                    return i.get_content()

        # And if that too fails, we get the first image referenced in the file
        for i in self.book.items:
            if i.media_type == 'image/jpeg' or i.media_type == 'image/png':
                return i.get_content()

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

    def get_tags(self):
        try:
            subject = self.book.metadata['http://purl.org/dc/elements/1.1/']['subject']
            tags = [i[0] for i in subject]
            return tags
        except KeyError:
            return

    def get_contents(self):
        extract_path = os.path.join(self.temp_dir, self.file_md5)
        zipfile.ZipFile(self.filename).extractall(extract_path)

        contents = collections.OrderedDict()

        def flatten_section(toc_element):
            output_list = []
            for i in toc_element:
                if isinstance(i, (tuple, list)):
                    output_list.extend(flatten_section(i))
                else:
                    output_list.append(i)
            return output_list

        for i in self.book.toc:
            if isinstance(i, (tuple, list)):
                flattened = flatten_section(i)

                for j in flattened:
                    title = j.title
                    href = unquote(j.href)
                    try:
                        content = self.book.get_item_with_href(href).get_content()
                        contents[title] = content.decode()
                    except AttributeError:
                        pass

            else:
                title = i.title
                href = unquote(i.href)
                try:
                    content = self.book.get_item_with_href(href).get_content()
                    if content:
                        contents[title] = content.decode()
                    else:
                        raise AttributeError
                except AttributeError:
                    contents[title] = 'Parse Error'

        # Special settings that have to be returned with the file
        # Referenced in sorter.py
        file_settings = {
            'images_only': False}

        return contents, file_settings


class HidePrinting:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout
