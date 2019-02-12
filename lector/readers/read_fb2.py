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
import collections

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FB2:
    def __init__(self, filename):
        self.filename = filename
        self.zip_file = None
        self.xml = None

        self.metadata = None
        self.content = []

        self.generate_references()

    def generate_references(self):
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

    def generate_metadata(self):
        # All metadata can be parsed in one pass
        all_tags = self.xml.find('description')

        title = all_tags.find('book-title').text
        if title == '' or title is None:
            title = os.path.splitext(
                os.path.basename(self.filename))[0]

        author = all_tags.find(
            'author').getText(separator=' ').replace('\n', ' ')
        if author == '' or author is None:
            author = '<Unknown>'
        else:
            author = author.strip()

        # TODO
        # Account for other date formats
        try:
            year = int(all_tags.find('date').text)
        except ValueError:
            year = 9999

        isbn = None
        tags = None

        cover = self.generate_book_cover()

        Metadata = collections.namedtuple(
            'Metadata', ['title', 'author', 'year', 'isbn', 'tags', 'cover'])
        self.metadata = Metadata(title, author, year, isbn, tags, cover)

    def generate_content(self, temp_dir):
        # TODO
        # Check what's up with recursion levels
        # Why is the TypeError happening in get_title

        def get_title(element):
            this_title = '<No title>'
            title_xml = '<No title xml>'
            try:
                for i in element:
                    if i.name == 'title':
                        this_title = i.getText(separator=' ')
                        this_title = this_title.replace('\n', '').strip()
                        title_xml = str(i.unwrap())
                        break
            except TypeError:
                return None, None
            return this_title, title_xml

        def recursor(level, element):
            children = element.findChildren('section', recursive=False)
            if not children and level != 1:
                this_title, title_xml = get_title(element)
                self.content.append(
                    [level, this_title, title_xml + str(element)])
            else:
                for i in children:
                    recursor(level + 1, i)

        first_element = self.xml.find('section')  # Recursive find
        siblings = list(first_element.findNextSiblings('section', recursive=False))
        siblings.insert(0, first_element)

        for this_element in siblings:
            this_title, title_xml = get_title(this_element)
            # Do not add chapter content in case it has sections
            # inside it. This prevents having large Book sections that
            # have duplicated content
            section_children = this_element.findChildren('section')
            chapter_text = str(this_element)
            if section_children:
                chapter_text = this_title

            self.content.append([1, this_title, chapter_text])
            recursor(1, this_element)

        # Extract all images to the temp_dir
        for i in self.xml.find_all('binary'):
            image_name = i.get('id')
            image_path = os.path.join(temp_dir, image_name)
            image_string = f'<image l:href="#{image_name}"'
            replacement_string = f'<p></p><img src=\"{image_path}\"'

            for j in self.content:
                j[2] = j[2].replace(
                    image_string, replacement_string)
            try:
                image_data = base64.decodebytes(i.text.encode())
                with open(image_path, 'wb') as outimage:
                    outimage.write(image_data)
            except AttributeError:
                pass

        # Insert the book cover at the beginning
        cover_image = self.generate_book_cover()
        if cover_image:
            cover_path = os.path.join(
                temp_dir, os.path.basename(self.filename)) + ' - cover'
            with open(cover_path, 'wb') as cover_temp:
                cover_temp.write(cover_image)

            self.content.insert(
                0, (1, 'Cover', f'<center><img src="{cover_path}" alt="Cover"></center>'))

    def generate_book_cover(self):
        cover = None

        try:
            cover_image_xml = self.xml.find('coverpage')
            for i in cover_image_xml:
                cover_image_name = i.get('l:href')

            cover_image_data = self.xml.find_all('binary')
            for i in cover_image_data:
                if cover_image_name.endswith(i.get('id')):
                    cover = base64.decodebytes(i.text.encode())
        except (AttributeError, TypeError):
            # Catch TypeError in case no images exist in the book
            logger.warning('Cover not found: ' + self.filename)

        return cover
