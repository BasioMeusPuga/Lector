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

import numpy
import djvu.decode
from PyQt5 import QtGui

djvu_pixel_format = djvu.decode.PixelFormatRgbMask(0xFF0000, 0xFF00, 0xFF, bpp=32)
djvu_pixel_format.rows_top_to_bottom = 1
djvu_pixel_format.y_top_to_bottom = 0


class ParseDJVU:
    def __init__(self, filename, temp_dir, file_md5):
        self.book = None
        self.filename = filename

        # Create the temporary directory where
        # rendered pngs will be stored
        # This may be skipped in case QImage to QPixmap conversion
        # stops segfaulting
        self.extract_dir = os.path.join(temp_dir, file_md5)
        os.makedirs(self.extract_dir, exist_ok=True)

    def read_book(self):
        self.book = djvu.decode.Context().new_document(
            djvu.decode.FileURI(self.filename))
        self.book.decoding_job.wait()

    def generate_metadata(self):
        title = os.path.basename(self.filename)
        author = 'Unknown'
        year = 9999
        isbn = None
        tags = []

        cover_page = self.book.pages[0]
        cover = render_djvu_page(cover_page, self.extract_dir, True)

        Metadata = collections.namedtuple(
            'Metadata', ['title', 'author', 'year', 'isbn', 'tags', 'cover'])
        return Metadata(title, author, year, isbn, tags, cover)

    def generate_content(self):
        # TODO
        # See if it's possible to generate a more involved ToC

        content = list(range(len(self.book.pages)))
        toc = [(1, f'Page {i + 1}', i + 1) for i in content]

        # Return toc, content, images_only
        return toc, content, True

def render_djvu_page(page, extract_dir, for_cover=False):

    # TODO
    # Figure out how to calculate image stride
    bytes_per_line = 13200

    # Yes, but why?
    mode = 0

    page_job = page.decode(wait=True)
    width, height = page_job.size
    rect = (0, 0, width, height)
    color_buffer = numpy.zeros((height, bytes_per_line), dtype=numpy.uint32)
    page_job.render(
        mode, rect, rect, djvu_pixel_format,
        row_alignment=bytes_per_line,
        buffer=color_buffer)
    color_buffer ^= 0xFF000000

    imageFormat = QtGui.QImage.Format_RGB32
    pageQImage = QtGui.QImage(color_buffer, width, height, imageFormat)

    if for_cover:
        return pageQImage

    # TODO
    # Converting from the QImage to the QPixmap directly
    # outright segfaults sometimes.
    # This damages caching, speed and my ego

    outfile = os.path.join(extract_dir, 'temporaryPNG.png')
    pageQImage.save(outfile)
    pixmap = QtGui.QPixmap()
    pixmap.load(outfile)

    return pixmap
