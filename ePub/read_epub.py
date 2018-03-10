#!/usr/bin/env python3

# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017 BasioMeusPuga

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
import sys
import zipfile

import pprint
import inspect

import bs4
from bs4 import BeautifulSoup


class EPUB:
    def __init__(self, filename):
        self.filename = filename
        self.zip_file = None
        self.book = {}

    def read_book(self):
        # This is the function that should error out in
        # case the module cannot process the file
        self.load_zip()
        contents_path = self.get_file_path('content.opf')
        self.generate_book_metadata(contents_path)
        self.parse_toc()

    def load_zip(self):
        try:
            self.zip_file = zipfile.ZipFile(
                self.filename, mode='r', allowZip64=True)
        except (KeyError, AttributeError, zipfile.BadZipFile):
            print('Cannot parse ' + self.filename)
            return

    def parse_xml(self, filename, parser):
        try:
            this_xml = self.zip_file.read(filename).decode()
        except KeyError:
            print('File not found in zip')
            return

        root = BeautifulSoup(this_xml, parser)
        return root

    def get_file_path(self, filename):
        # Use this to get the location of the content.opf file
        # And maybe some other file that has a more well formatted
        # idea of the TOC
        for i in self.zip_file.filelist:
            if os.path.basename(i.filename) == filename:
                return i.filename


    def generate_book_metadata(self, contents_path):
        item_dict = {
            'title': 'dc:title',
            'author': 'dc:creator',
            'date': 'dc:date'}

        # Parse metadata
        xml = self.parse_xml(contents_path, 'lxml')

        for i in item_dict.items():
            item = xml.find(i[1])
            if item:
                self.book[i[0]] = item.text

        # Get identifier
        xml = self.parse_xml(contents_path, 'xml')

        metadata_items = xml.find('metadata')
        for i in metadata_items.children:
            if isinstance(i, bs4.element.Tag):
                try:
                    if i.get('opf:scheme').lower() == 'isbn':
                        self.book['isbn'] = i.text
                        break
                except AttributeError:
                    self.book['isbn'] = None

        # Get items
        book_items = {}
        all_items = xml.find_all('item')
        for i in all_items:
            media_type = i.get('media-type')

            if media_type == 'application/xhtml+xml':
                book_items[i.get('id')] = i.get('href')
            if media_type == 'application/x-dtbncx+xml':
                self.book['toc_file'] = i.get('href')
            if i.get('id') == 'cover':
                self.book['cover'] = self.zip_file.read(i.get('href'))

        # Parse spine
        spine_items = xml.find_all('itemref')
        spine_order = []
        for i in spine_items:
            spine_order.append(i.get('idref'))

        # book_order = []
        # for i in spine_order:
        #     try:
        #         book_order.append(book_items[i])
        #     except KeyError:
        #         pass

        # self.book['book_order'] = book_order

    def parse_toc(self):
        # Try to get chapter names from the toc
        try:
            toc_file = self.book['toc_file']
        except KeyError:
            toc_file = self.get_file_path('toc.ncx')

        xml = self.parse_xml(toc_file, 'xml')
        navpoints = xml.find_all('navPoint')

        self.book['navpoint_dict'] = {}
        for i in navpoints:
            chapter_title = i.find('text').text
            chapter_source = i.find('content').get('src')
            chapter_source = chapter_source.split('#')[0]
            self.book['navpoint_dict'][chapter_title] = chapter_source

        # self.book['navpoint_dict'] = {}
        # for i in self.book['book_order']:
        #     try:
        #         self.book['navpoint_dict'][i] = navpoint_dict[i]
        #     except:
        #         # TODO
        #         # Create title
        #         self.book['navpoint_dict'][i] = 'Unspecified'

        # # Reverse the dict
        # reverse_dict = {i[1]: i[0] for i in self.book['navpoint_dict'].items()}
        # self.book['navpoint_dict'] = reverse_dict

    def parse_chapters(self):
        for i in self.book['navpoint_dict'].items():
            try:
                self.book['navpoint_dict'][i[0]] = self.zip_file.read(i[1]).decode()
            except KeyError:
                print(i[1] + ' skipped')


def main():
    book = EPUB(sys.argv[1])
    book.read_book()
    book.parse_chapters()

if __name__ == '__main__':
    main()
