# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017-2019 BasioMeusPuga

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

# This module parses Amazon ebooks using KindleUnpack to first create an
# epub that is then read the usual way

import os
import sys
import shutil
import zipfile
import logging

from lector.readers.read_epub import EPUB
import lector.KindleUnpack.kindleunpack as KindleUnpack

logger = logging.getLogger(__name__)


class ParseMOBI:
    def __init__(self, filename, temp_dir, file_md5):
        self.book_ref = None
        self.book = None
        self.filename = filename
        self.epub_filepath = None
        self.split_large_xml = False
        self.temp_dir = temp_dir
        self.extract_dir = os.path.join(temp_dir, file_md5)

    def read_book(self):
        with HidePrinting():
            KindleUnpack.unpackBook(self.filename, self.extract_dir)

        epub_filename = os.path.splitext(
            os.path.basename(self.filename))[0] + '.epub'

        self.epub_filepath = os.path.join(
            self.extract_dir, 'mobi8', epub_filename)
        if not os.path.exists(self.epub_filepath):
            zip_dir = os.path.join(self.extract_dir, 'mobi7')
            zip_file = os.path.join(
                self.extract_dir, epub_filename)
            self.epub_filepath = shutil.make_archive(zip_file, 'zip', zip_dir)
            self.split_large_xml = True

        self.book_ref = EPUB(self.epub_filepath)
        contents_found = self.book_ref.read_epub()
        if not contents_found:
            return False
        self.book = self.book_ref.book
        return True

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
        extract_path = os.path.join(self.extract_dir)
        zipfile.ZipFile(self.epub_filepath).extractall(extract_path)

        self.book_ref.parse_chapters(
            temp_dir=self.temp_dir, split_large_xml=self.split_large_xml)
        file_settings = {
            'images_only': False}
        return self.book['book_list'], file_settings

class HidePrinting:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout
