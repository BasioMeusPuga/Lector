# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017-2018 BasioMeusPuga

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
import base64
import zipfile

from bs4 import BeautifulSoup


class FB2:
    def __init__(self, filename):
        self.filename = filename
        self.zip_file = None
        self.book = {}
        self.xml = None

    def read_fb2(self):
        try:
            if self.filename.endswith('.fb2.zip'):
                this_book = zipfile.ZipFile(self.filename, mode='r', allowZip64=True)
                for i in this_book.filelist:
                    if os.path.splitext(i.filename)[1] == '.fb2':
                        book_text = this_book.read(i.filename)
                        break
            else:
                with open(self.filename, 'r') as book_file:
                    book_text = book_file.read()

            self.xml = BeautifulSoup(book_text, 'lxml')
            self.generate_book_metadata()
        except:  # Not specifying an exception type here may be justified
            return False

        return True

    def generate_book_metadata(self):
        self.book['title'] = os.path.splitext(
            os.path.basename(self.filename))[0]
        self.book['author'] = 'Unknown'
        self.book['isbn'] = None
        self.book['tags'] = None
        self.book['cover'] = None
        self.book['year'] = 9999
        self.book['book_list'] = []

        # TODO
        # Look for other components of book metadata here
        for i in self.xml.find_all():

            if i.name == 'section':
                for j in i:
                    if j.name == 'title':
                        this_title = j.text
                self.book['book_list'].append(
                    (this_title, str(i)))

        # Cover Image
        cover_image_xml = self.xml.find('coverpage')
        for i in cover_image_xml:
            cover_image_name = i.get('l:href')

        cover_image_data = self.xml.find_all('binary')
        for i in cover_image_data:

            # TODO
            # Account for other images as well
            if cover_image_name.endswith(i.get('id')):
                self.book['cover'] = base64.decodebytes(i.text.encode())
