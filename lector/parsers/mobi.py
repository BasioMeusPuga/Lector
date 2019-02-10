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

# TODO
# See if it's possible to just feed the
# unzipped mobi7 file into the EPUB parser module

import os
import sys
import shutil
import zipfile
import logging

from lector.readers.read_epub import EPUB
import lector.KindleUnpack.kindleunpack as KindleUnpack

logger = logging.getLogger(__name__)


class ParseMOBI:
    # This module parses Amazon ebooks using KindleUnpack to first create an
    # epub and then read the usual way

    def __init__(self, filename, temp_dir, file_md5):
        self.book = None
        self.filename = filename
        self.epub_filepath = None
        self.temp_dir = temp_dir
        self.extract_path = os.path.join(temp_dir, file_md5)

    def read_book(self):
        with HidePrinting():
            KindleUnpack.unpackBook(self.filename, self.extract_path)

        epub_filename = os.path.splitext(
            os.path.basename(self.filename))[0] + '.epub'
        self.epub_filepath = os.path.join(
            self.extract_path, 'mobi8', epub_filename)

        if not os.path.exists(self.epub_filepath):
            zip_dir = os.path.join(self.extract_path, 'mobi7')
            zip_file = os.path.join(
                self.extract_path, epub_filename)
            self.epub_filepath = shutil.make_archive(zip_file, 'zip', zip_dir)

        self.book = EPUB(self.epub_filepath, self.temp_dir)

    def generate_metadata(self):
        self.book.generate_metadata()
        return self.book.metadata

    def generate_content(self):
        zipfile.ZipFile(self.epub_filepath).extractall(self.extract_path)

        self.book.generate_toc()
        self.book.generate_content()

        toc = []
        content = []
        for count, i in enumerate(self.book.content):
            toc.append((1, i[1], count + 1))
            content.append(i[2])

        # Return toc, content, images_only
        return toc, content, False


class HidePrinting:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout
