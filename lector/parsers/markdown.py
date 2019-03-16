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

import os
import logging
import collections

import markdown

logger = logging.getLogger(__name__)


class ParseMD:
    def __init__(self, filename, *args):
        self.book = None
        self.filename = filename

    def read_book(self):
        self.book = None

    def generate_metadata(self):
        title = os.path.basename(self.filename)
        author = 'Unknown'
        year = 9999
        isbn = None
        tags = []
        cover = None

        Metadata = collections.namedtuple(
            'Metadata', ['title', 'author', 'year', 'isbn', 'tags', 'cover'])
        return Metadata(title, author, year, isbn, tags, cover)

    def generate_content(self):
        with open(self.filename, 'r') as book:
            text = book.read()
            content = [markdown.markdown(text)]

        toc = [(1, 'Markdown', 1)]

        # Return toc, content, images_only
        return toc, content, False
