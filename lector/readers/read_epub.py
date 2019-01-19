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
import zipfile
from urllib.parse import unquote

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EPUB:
    def __init__(self, filename):
        self.filename = filename
        self.zip_file = None
        self.book = {}
        self.book['split_chapters'] = {}

    def read_epub(self):
        # This is the function that should error out in
        # case the module cannot process the file
        try:
            self.load_zip()
            contents_path = self.get_file_path(
                None, True)

            if not contents_path:
                return False  # No (valid) opf was found so processing cannot continue

            self.generate_book_metadata(contents_path)
        except:  # Not specifying an exception type here may be justified
            return False

        return True

    def load_zip(self):
        try:
            self.zip_file = zipfile.ZipFile(
                self.filename, mode='r', allowZip64=True)
        except (KeyError, AttributeError, zipfile.BadZipFile):
            logger.error('Malformed zip file ' + self.filename)
            return

    def parse_xml(self, filename, parser):
        try:
            this_xml = self.zip_file.read(filename).decode()
        except KeyError:
            short_filename = os.path.basename(self.filename)
            warning_string = f'{str(filename)} not found in {short_filename}'
            logger.warning(warning_string)
            return

        root = BeautifulSoup(this_xml, parser)
        return root

    def get_file_path(self, filename, is_content_file=False):
        # Use this to get the location of the content.opf file
        # And maybe some other file that has a more well formatted
        # idea of the TOC
        # We're going to all this trouble because there really is
        # no going forward without a toc
        if is_content_file:
            container_location = self.get_file_path('container.xml')
            xml = self.parse_xml(container_location, 'xml')

            if xml:
                root_item = xml.find('rootfile')
                try:
                    return root_item.get('full-path')
                except AttributeError:
                    error_string = f'ePub module: {self.filename} has a malformed container.xml'
                    logger.error(error_string)
                    return None

            possible_filenames = ('content.opf', 'package.opf')
            for i in possible_filenames:
                presumptive_location = self.get_file_path(i)
                if presumptive_location:
                    return presumptive_location

        for i in self.zip_file.filelist:
            if os.path.basename(i.filename) == os.path.basename(filename):
                return i.filename

        return None

    def read_from_zip(self, filename):
        filename = unquote(filename)
        try:
            file_data = self.zip_file.read(filename)
            return file_data
        except KeyError:
            file_path_actual = self.get_file_path(filename)
            if file_path_actual:
                return self.zip_file.read(file_path_actual)
            else:
                logger.error('ePub module can\'t find ' + filename)

    #______________________________________________________

    def generate_book_metadata(self, contents_path):
        self.book['title'] = os.path.splitext(
            os.path.basename(self.filename))[0]
        self.book['author'] = 'Unknown'
        self.book['isbn'] = None
        self.book['tags'] = None
        self.book['cover'] = None
        self.book['toc_file'] = 'toc.ncx'  # Overwritten if another one exists

        # Parse XML
        xml = self.parse_xml(contents_path, 'xml')

        # Parse metadata
        item_dict = {
            'title': 'title',
            'author': 'creator',
            'year': 'date'}

        for i in item_dict.items():
            item = xml.find(i[1])
            if item:
                self.book[i[0]] = item.text

        try:
            self.book['year'] = int(self.book['year'][:4])
        except (TypeError, KeyError, IndexError, ValueError):
            self.book['year'] = 9999

        # Get identifier
        identifier_items = xml.find_all('identifier')
        for i in identifier_items:
            scheme = i.get('scheme')
            try:
                if scheme.lower() == 'isbn':
                    self.book['isbn'] = i.text
            except AttributeError:
                self.book['isbn'] = None

        # Tags
        tag_items = xml.find_all('subject')
        tag_list = [i.text for i in tag_items]
        self.book['tags'] = tag_list

        # Get items
        self.book['content_dict'] = {}
        all_items = xml.find_all('item')
        for i in all_items:
            media_type = i.get('media-type')
            this_id = i.get('id')

            if media_type == 'application/xhtml+xml' or media_type == 'text/html':
                self.book['content_dict'][this_id] = i.get('href')

            if media_type == 'application/x-dtbncx+xml':
                self.book['toc_file'] = i.get('href')

            # Cover image
            if 'cover' in this_id and media_type.split('/')[0] == 'image':
                cover_href = i.get('href')
                try:
                    self.book['cover'] = self.zip_file.read(cover_href)
                except KeyError:
                    # The cover cannot be found according to the
                    # path specified in the content reference
                    self.book['cover'] = self.zip_file.read(
                        self.get_file_path(cover_href))

        if not self.book['cover']:
            # If no cover is located the conventional way,
            # we go looking for the largest image in the book
            biggest_image_size = 0
            biggest_image = None
            for j in self.zip_file.filelist:
                if os.path.splitext(j.filename)[1] in ['.jpg', '.jpeg', '.png', '.gif']:
                    if j.file_size > biggest_image_size:
                        biggest_image = j.filename
                        biggest_image_size = j.file_size

            if biggest_image:
                self.book['cover'] = self.read_from_zip(biggest_image)
            else:
                logger.error('No cover found for: ' + self.filename)

        # Parse spine and arrange chapter paths acquired from the opf
        # according to the order IN THE SPINE
        spine_items = xml.find_all('itemref')
        spine_order = []
        for i in spine_items:
            spine_order.append(i.get('idref'))

        self.book['chapters_in_order'] = []
        for i in spine_order:
            chapter_path = self.book['content_dict'][i]
            self.book['chapters_in_order'].append(chapter_path)

    def parse_toc(self):
        # This has no bearing on the actual order
        # We're just using this to get chapter names
        self.book['navpoint_dict'] = {}

        toc_file = self.book['toc_file']
        if toc_file:
            toc_file = self.get_file_path(toc_file)

        xml = self.parse_xml(toc_file, 'xml')
        if not xml:
            return

        navpoints = xml.find_all('navPoint')

        for i in navpoints:
            chapter_title = i.find('text').text
            chapter_source = i.find('content').get('src')
            chapter_source_file = unquote(chapter_source.split('#')[0])

            if '#' in chapter_source:
                try:
                    self.book['split_chapters'][chapter_source_file].append(
                        (chapter_source.split('#')[1], chapter_title))
                except KeyError:
                    self.book['split_chapters'][chapter_source_file] = []
                    self.book['split_chapters'][chapter_source_file].append(
                        (chapter_source.split('#')[1], chapter_title))

            self.book['navpoint_dict'][chapter_source_file] = chapter_title

    def parse_chapters(self, temp_dir=None, split_large_xml=False):
        no_title_chapter = 0
        self.book['book_list'] = []

        for i in self.book['chapters_in_order']:
            chapter_data = self.read_from_zip(i).decode()

            if i in self.book['split_chapters'] and not split_large_xml:
                split_chapters = get_split_content(
                    chapter_data, self.book['split_chapters'][i])
                self.book['book_list'].extend(split_chapters)

            elif split_large_xml:
                # https://stackoverflow.com/questions/14444732/how-to-split-a-html-page-to-multiple-pages-using-python-and-beautiful-soup
                markup = BeautifulSoup(chapter_data, 'xml')
                chapters = []
                pagebreaks = markup.find_all('pagebreak')

                def next_element(elem):
                    while elem is not None:
                        elem = elem.next_sibling
                        if hasattr(elem, 'name'):
                            return elem

                for pbreak in pagebreaks:
                    chapter = [str(pbreak)]
                    elem = next_element(pbreak)
                    while elem and elem.name != 'pagebreak':
                        chapter.append(str(elem))
                        elem = next_element(elem)
                    chapters.append('\n'.join(chapter))

                for this_chapter in chapters:
                    fallback_title = str(no_title_chapter)
                    self.book['book_list'].append(
                        (fallback_title, this_chapter + ('<br/>' * 8)))
                    no_title_chapter += 1
            else:
                try:
                    self.book['book_list'].append(
                        (self.book['navpoint_dict'][i], chapter_data + ('<br/>' * 8)))
                except KeyError:
                    fallback_title = str(no_title_chapter)
                    self.book['book_list'].append(
                        (fallback_title, chapter_data))
                no_title_chapter += 1

        cover_path = os.path.join(temp_dir, os.path.basename(self.filename)) + '- cover'
        if self.book['cover']:
            with open(cover_path, 'wb') as cover_temp:
                cover_temp.write(self.book['cover'])

            try:
                self.book['book_list'][0] = (
                    'Cover', f'<center><img src="{cover_path}" alt="Cover"></center>')
            except IndexError:
                pass

def get_split_content(chapter_data, split_by):
    split_anchors = [i[0] for i in split_by]
    chapter_titles = [i[1] for i in split_by]
    return_list = []

    xml = BeautifulSoup(chapter_data, 'lxml')
    xml_string = xml.body.prettify()

    for count, i in enumerate(split_anchors):
        this_split = xml_string.split(i)
        current_chapter = this_split[0]

        bs_obj = BeautifulSoup(current_chapter, 'lxml')
        # Since tags correspond to data following them, the first
        # chunk will be ignored
        # As will all empty chapters
        if bs_obj.text == '\n' or bs_obj.text == '' or count == 0:
            continue
        bs_obj_string = str(bs_obj).replace('"&gt;', '', 1) + ('<br/>' * 8)

        return_list.append(
            (chapter_titles[count - 1], bs_obj_string))

        xml_string = ''.join(this_split[1:])

    bs_obj = BeautifulSoup(xml_string, 'lxml')
    bs_obj_string = str(bs_obj).replace('"&gt;', '', 1) + ('<br/>' * 8)
    return_list.append(
        (chapter_titles[-1], bs_obj_string))

    return return_list
