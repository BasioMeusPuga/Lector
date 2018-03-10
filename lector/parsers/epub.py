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
import zipfile

from ePub.read_epub import EPUB


class ParseEPUB:
    def __init__(self, filename, temp_dir, file_md5):
        # TODO
        # Maybe also include book description
        self.book_ref = None
        self.book = None
        self.temp_dir = temp_dir
        self.filename = filename
        self.file_md5 = file_md5

    def read_book(self):
        self.book_ref = EPUB(self.filename)
        contents_found = self.book_ref.read_epub()
        if not contents_found:
            print('Cannot process: ' + self.filename)
            return
        self.book = self.book_ref.book

    def get_title(self):
        return self.book['title']

    def get_author(self):
        return self.book['author']

    def get_year(self):
        return self.book['year']

    def get_cover_image(self):
        return self.book['cover']

    def get_isbn(self):
        return self.book['isbn']

    def get_tags(self):
        return self.book['tags']

    def get_contents(self):
        extract_path = os.path.join(self.temp_dir, self.file_md5)
        zipfile.ZipFile(self.filename).extractall(extract_path)

        self.book_ref.parse_chapters(temp_dir=self.temp_dir)
        file_settings = {
            'images_only': False}
        return self.book['book_list'], file_settings
