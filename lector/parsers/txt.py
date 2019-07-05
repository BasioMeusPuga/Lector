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

import collections
import os

import textile


class ParseTXT:
    """Parser for TXT files."""

    def __init__(self, filename, *args):
        """Initialize new instance of the TXT parser."""
        self.filename = filename

    def read_book(self):
        """Prepare the parser to read book."""
        pass

    def generate_metadata(self):
        """Generate metadata for the book."""
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
        """Generate content of the book."""
        with open(self.filename, 'rt') as txt:
            text = txt.read()
            content = [textile.textile(text)]

        toc = [(1, 'Text', 1)]

        return toc, content, False
