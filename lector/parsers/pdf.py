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
import collections

import fitz
from PyQt5 import QtGui


class ParsePDF:
    def __init__(self, filename, *args):
        self.filename = filename
        self.book = None

    def read_book(self):
        self.book = fitz.open(self.filename)

    def generate_metadata(self):
        title = self.book.metadata['title']
        if not title:
            title = os.path.splitext(os.path.basename(self.filename))[0]

        author = self.book.metadata['author']
        if not author:
            author = 'Unknown'

        creation_date = self.book.metadata['creationDate']
        try:
            year = creation_date.split(':')[1][:4]
        except (ValueError, AttributeError):
            year = 9999

        isbn = None

        tags = self.book.metadata['keywords']
        if not tags:
            tags = []

        # This is a little roundabout for the cover
        # and I'm sure it's taking a performance hit
        # But it is simple. So there's that.
        cover_page = self.book.loadPage(0)
        # Disabling scaling gets the covers much faster
        cover = render_pdf_page(cover_page, True)

        Metadata = collections.namedtuple(
            'Metadata', ['title', 'author', 'year', 'isbn', 'tags', 'cover'])
        return Metadata(title, author, year, isbn, tags, cover)

    def generate_content(self):
        content = list(range(self.book.pageCount))
        toc = self.book.getToC()
        if not toc:
            toc = [(1, f'Page {i + 1}', i + 1) for i in range(self.book.pageCount)]

        # Return toc, content, images_only
        return toc, content, True


def render_pdf_page(page_data, for_cover=False):
    # Draw page contents on to a pixmap
    # and then return that pixmap

    # Render quality is set by the following
    zoom_matrix = fitz.Matrix(4, 4)
    if for_cover:
        zoom_matrix = fitz.Matrix(1, 1)

    pagePixmap = page_data.getPixmap(
        matrix=zoom_matrix,
        alpha=False)  # Sets background to White
    imageFormat = QtGui.QImage.Format_RGB888  # Set to Format_RGB888 if alpha
    pageQImage = QtGui.QImage(
        pagePixmap.samples,
        pagePixmap.width,
        pagePixmap.height,
        pagePixmap.stride,
        imageFormat)

    # The cover page doesn't require conversion into a Pixmap
    if for_cover:
        return pageQImage

    pixmap = QtGui.QPixmap()
    pixmap.convertFromImage(pageQImage)
    return pixmap
