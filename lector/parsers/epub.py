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
# Maybe also include book description

import os
import zipfile
import logging

from lector.readers.read_epub import EPUB

logger = logging.getLogger(__name__)


class ParseEPUB:
    def __init__(self, filename, temp_dir, file_md5):
        self.book = None
        self.filename = filename
        self.temp_dir = temp_dir
        self.extract_path = os.path.join(temp_dir, file_md5)

    def read_book(self):
        self.book = EPUB(self.filename, self.temp_dir)

    def generate_metadata(self):
        self.book.generate_metadata()
        return self.book.metadata

    def generate_content(self):
        zipfile.ZipFile(self.filename).extractall(self.extract_path)

        self.book.generate_toc()
        self.book.generate_content()

        toc = []
        content = []
        for count, i in enumerate(self.book.content):
            toc.append((i[0], i[1], count + 1))
            content.append(i[2])

        # Return toc, content, images_only
        return toc, content, False
