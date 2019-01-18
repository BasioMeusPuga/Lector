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
import base64
import zipfile
import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FB2:
    def __init__(self, filename):
        self.filename = filename
        self.zip_file = None
        self.book = {}
        self.xml = None

    def read_fb2(self):
        try:
            if self.filename.endswith('.fb2.zip'):
                this_book = zipfile.ZipFile(
                    self.filename, mode='r', allowZip64=True)
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
        self.book['isbn'] = None
        self.book['tags'] = None
        self.book['book_list'] = []

        # All metadata can be parsed in one pass
        all_tags = self.xml.find('description')

        self.book['title'] = all_tags.find('book-title').text
        if self.book['title'] == '' or self.book['title'] is None:
            self.book['title'] = os.path.splitext(
                os.path.basename(self.filename))[0]

        self.book['author'] = all_tags.find(
            'author').getText(separator=' ').replace('\n', ' ')
        if self.book['author'] == '' or self.book['author'] is None:
            self.book['author'] = 'Unknown'

        # TODO
        # Account for other date formats
        try:
            self.book['year'] = int(all_tags.find('date').text)
        except ValueError:
            self.book['year'] = 9999

        # Cover Image
        try:
            cover_image_xml = self.xml.find('coverpage')
            for i in cover_image_xml:
                cover_image_name = i.get('l:href')

            cover_image_data = self.xml.find_all('binary')
            for i in cover_image_data:
                if cover_image_name.endswith(i.get('id')):
                    self.book['cover'] = base64.decodebytes(i.text.encode())
        except (AttributeError, TypeError):
            # Catch TypeError in case no images exist in the book
            logger.error('No cover found for: ' + self.filename)
            self.book['cover'] = None

    def parse_chapters(self, temp_dir):
        # There's no need to parse the TOC separately because
        # everything is linear
        for i in self.xml.find_all('section'):
            this_title = '<No title>'
            for j in i:
                if j.name == 'title':
                    this_title = j.getText(separator=' ')

            self.book['book_list'].append(
                [this_title, str(i)])

        # Extract all images to the temp_dir
        for i in self.xml.find_all('binary'):
            image_name = i.get('id')
            image_path = os.path.join(temp_dir, image_name)
            image_string = f'<image l:href="#{image_name}"'
            replacement_string = f'<img src=\"{image_path}\"'

            for j in self.book['book_list']:
                j[1] = j[1].replace(
                    image_string, replacement_string)
            try:
                image_data = base64.decodebytes(i.text.encode())
                with open(image_path, 'wb') as outimage:
                    outimage.write(image_data)
            except AttributeError:
                pass

        # Insert the book cover at the beginning
        if self.book['cover']:
            cover_path = os.path.join(temp_dir, 'cover')
            with open(cover_path, 'wb') as outimage:
                outimage.write(self.book['cover'])
            self.book['book_list'].insert(
                0, ('Cover', f'<center><img src="{cover_path}" alt="Cover"></center>'))
