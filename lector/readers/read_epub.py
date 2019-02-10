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
# See if inserting chapters not in the toc.ncx can be avoided
# Account for stylesheets... eventually
# Everything needs logging
# Mobipocket files

import os
import zipfile
import logging
import collections
from urllib.parse import unquote

import xmltodict
from PyQt5 import QtGui
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EPUB:
    def __init__(self, book_filename, temp_dir):
        self.book_filename = book_filename
        self.temp_dir = temp_dir
        self.zip_file = None
        self.file_list = None
        self.opf_dict = None
        self.book = {}

        self.generate_references()

    def find_file(self, filename):
        # Get rid of special characters
        filename = unquote(filename)

        # First, look for the file in the root of the book
        if filename in self.file_list:
            return filename

        # Then search for it elsewhere
        else:
            file_basename = os.path.basename(filename)
            for i in self.file_list:
                if os.path.basename(i) == file_basename:
                    return i

        # If the file isn't found
        logging.error(filename + ' not found in ' + self.book_filename)
        return False

    def generate_references(self):
        self.zip_file = zipfile.ZipFile(
            self.book_filename, mode='r', allowZip64=True)
        self.file_list = self.zip_file.namelist()

        # Book structure relies on parsing the .opf file
        # in the book. Now that might be the usual content.opf
        # or package.opf or it might be named after your favorite
        # eldritch abomination. The point is we have to check
        # the container.xml
        container = self.find_file('container.xml')
        if container:
            container_xml = self.zip_file.read(container)
            container_dict = xmltodict.parse(container_xml)
            packagefile = container_dict['container']['rootfiles']['rootfile']['@full-path']
        else:
            presumptive_names = ('content.opf', 'package.opf', 'volume.opf')
            for i in presumptive_names:
                packagefile = self.find_file(i)
                if packagefile:
                    break

        packagefile_data = self.zip_file.read(packagefile)
        self.opf_dict = xmltodict.parse(packagefile_data)

    def generate_toc(self):
        self.book['content'] = []

        def find_alternative_toc():
            toc_filename = None
            toc_filename_alternative = None
            manifest = self.opf_dict['package']['manifest']['item']

            for i in manifest:
                # Behold the burning hoops we're jumping through
                if i['@id'] == 'ncx':
                    toc_filename = i['@href']
                if ('ncx' in i['@id']) or ('toc' in i['@id']):
                    toc_filename_alternative = i['@href']
                if toc_filename and toc_filename_alternative:
                    break

            if not toc_filename:
                if not toc_filename_alternative:
                    logger.error('No ToC found for: ' + self.book_filename)
                else:
                    toc_filename = toc_filename_alternative

            logger.info('Using alternate ToC for: ' + self.book_filename)
            return toc_filename

        # Find the toc.ncx file from the manifest
        # EPUBs will name literally anything, anything so try
        # a less stringent approach if the first one doesn't work
        # The idea is to prioritize 'toc.ncx' since this should work
        # for the vast majority of books
        toc_filename = 'toc.ncx'
        does_toc_exist = self.find_file(toc_filename)
        if not does_toc_exist:
            toc_filename = find_alternative_toc()

        tocfile = self.find_file(toc_filename)
        tocfile_data = self.zip_file.read(tocfile)
        toc_dict = xmltodict.parse(tocfile_data)

        def recursor(level, nav_node):
            if isinstance(nav_node, list):
                these_contents = [[
                    level + 1,
                    i['navLabel']['text'],
                    i['content']['@src']] for i in nav_node]
                self.book['content'].extend(these_contents)
                return

            if 'navPoint' in nav_node.keys():
                recursor(level, nav_node['navPoint'])

            else:
                self.book['content'].append([
                    level + 1,
                    nav_node['navLabel']['text'],
                    nav_node['content']['@src']])

        navpoints = toc_dict['ncx']['navMap']['navPoint']
        for top_level_nav in navpoints:
            # Just one chapter
            if isinstance(top_level_nav, str):
                self.book['content'].append([
                    1,
                    navpoints['navLabel']['text'],
                    navpoints['content']['@src']])
                break

            # Multiple chapters
            self.book['content'].append([
                1,
                top_level_nav['navLabel']['text'],
                top_level_nav['content']['@src']])

            if 'navPoint' in top_level_nav.keys():
                recursor(1, top_level_nav)

    def get_chapter_content(self, chapter_file):
        this_file = self.find_file(chapter_file)
        if this_file:
            chapter_content = self.zip_file.read(this_file).decode()

            # Generate a None return for a blank chapter
            # These will be removed from the contents later
            contentDocument = QtGui.QTextDocument(None)
            contentDocument.setHtml(chapter_content)
            contentText = contentDocument.toPlainText().replace('\n', '')
            if contentText == '':
                chapter_content = None

            return chapter_content
        else:
            return 'Possible parse error: ' + chapter_file

    def parse_split_chapters(self, chapters_with_split_content):
        self.book['split_chapters'] = {}

        # For split chapters, get the whole chapter first, then split
        # between ids using their anchors, then "heal" the resultant text
        # by creating a BeautifulSoup object. Write its str to the content
        for i in chapters_with_split_content.items():
            chapter_file = i[0]
            self.book['split_chapters'][chapter_file] = {}

            chapter_content = self.get_chapter_content(chapter_file)
            soup = BeautifulSoup(chapter_content, 'lxml')

            split_anchors = i[1]
            for this_anchor in reversed(split_anchors):
                this_tag = soup.find(
                    attrs={"id":lambda x: x == this_anchor})

                markup_split = str(soup).split(str(this_tag))
                soup = BeautifulSoup(markup_split[0], 'lxml')

                # If the tag is None, it probably means the content is overlapping
                # Skipping the insert is the way forward
                if this_tag:
                    this_markup = BeautifulSoup(
                        str(this_tag).strip() + markup_split[1], 'lxml')
                    self.book['split_chapters'][chapter_file][this_anchor] = str(this_markup)

            # Remaining markup is assigned here
            self.book['split_chapters'][chapter_file]['top_level'] = str(soup)

    def generate_content(self):
        # Find all the chapters mentioned in the opf spine
        # These are simply ids that correspond to the actual item
        # as mentioned in the manifest - which is a comprehensive
        # list of files
        chapters_in_spine = [
            i['@idref']
            for i in self.opf_dict['package']['spine']['itemref']]

        # Next, find items and ids from the manifest
        chapters_from_manifest = {
            i['@id']: i['@href']
            for i in self.opf_dict['package']['manifest']['item']}

        # Finally, check which items are supposed to be in the spine
        # on the basis of the id and change the toc accordingly
        spine_final = []
        for i in chapters_in_spine:
            try:
                spine_final.append(chapters_from_manifest.pop(i))
            except KeyError:
                pass

        chapter_title = 1
        toc_chapters = [
            unquote(i[2].split('#')[0]) for i in self.book['content']]

        last_valid_index = -2  # Yes, but why?
        for i in spine_final:
            if not i in toc_chapters:
                previous_chapter = spine_final[spine_final.index(i) - 1]
                try:
                    previous_chapter_toc_index = toc_chapters.index(previous_chapter)
                    # In case of 2+ consecutive missing chapters
                    last_valid_index = previous_chapter_toc_index
                except ValueError:
                    last_valid_index += 1

                self.book['content'].insert(
                    last_valid_index + 1,
                    [1, str(chapter_title), i])
                chapter_title += 1

        # Parse split chapters as below
        # They can be picked up during the iteration through the toc
        chapters_with_split_content = {}
        for i in self.book['content']:
            if '#' in i[2]:
                this_split = i[2].split('#')
                chapter = this_split[0]
                anchor = this_split[1]

                try:
                    chapters_with_split_content[chapter].append(anchor)
                except KeyError:
                    chapters_with_split_content[chapter] = []
                    chapters_with_split_content[chapter].append(anchor)

        self.parse_split_chapters(chapters_with_split_content)

        # Now we iterate over the ToC as presented in the toc.ncx
        # and add chapters to the content list
        # In case a split chapter is encountered, get its content
        # from the split_chapters dictionary
        # What could possibly go wrong?
        split_chapters = self.book['split_chapters']
        toc_copy = self.book['content'][:]

        # Put the book into the book
        for count, i in enumerate(toc_copy):
            chapter_file = i[2]

            # Get split content according to its corresponding id attribute
            if '#' in chapter_file:
                this_split = chapter_file.split('#')
                chapter_file_proper = this_split[0]
                this_anchor = this_split[1]

                try:
                    chapter_content = (
                        split_chapters[chapter_file_proper][this_anchor])
                except KeyError:
                    chapter_content = 'Parse Error'
                    error_string = (
                        f'Error parsing {self.book_filename}: {chapter_file_proper}')
                    logger.error(error_string)

            # Get content that remained at the end of the pillaging above
            elif chapter_file in split_chapters.keys():
                try:
                    chapter_content = split_chapters[chapter_file]['top_level']
                except KeyError:
                    chapter_content = 'Parse Error'
                    error_string = (
                        f'Error parsing {self.book_filename}: {chapter_file}')
                    logger.error(error_string)

            # Vanilla non split chapters
            else:
                chapter_content = self.get_chapter_content(chapter_file)

            self.book['content'][count][2] = chapter_content

        # Cleanup content by removing null chapters
        self.book['content'] = [
            i for i in self.book['content'] if i[2]]

        self.generate_book_cover()
        if self.book['cover']:
            cover_path = os.path.join(
                self.temp_dir, os.path.basename(self.book_filename)) + '- cover'
            with open(cover_path, 'wb') as cover_temp:
                cover_temp.write(self.book['cover'])

            # There's probably some rationale to doing an insert here
            # But a replacement seems... neater
            self.book['content'].insert(
                0, (1, 'Cover', f'<center><img src="{cover_path}" alt="Cover"></center>'))

    def generate_metadata(self):
        metadata = self.opf_dict['package']['metadata']

        def flattener(this_object):
            if isinstance(this_object, collections.OrderedDict):
                return this_object['#text']

            if isinstance(this_object, list):
                if isinstance(this_object[0], collections.OrderedDict):
                    return this_object[0]['#text']
                else:
                    return this_object[0]

            if isinstance(this_object, str):
                return this_object

        # There are no exception types specified below
        # This is on purpose and makes me long for the days
        # of simpler, happier things.

        # Book title
        try:
            self.book['title'] = flattener(metadata['dc:title'])
        except:
            self.book['title'] = os.path.splitext(
                os.path.basename(self.book_filename))[0]

        # Book author
        try:
            self.book['author'] = flattener(metadata['dc:creator'])
        except:
            self.book['author'] = 'Unknown'

        # Book year
        try:
            self.book['year'] = int(flattener(metadata['dc:date'])[:4])
        except:
            self.book['year'] = 9999

        # Book isbn
        # Both one and multiple schema
        self.book['isbn'] = None
        try:
            scheme = metadata['dc:identifier']['@opf:scheme'].lower()
            if scheme.lower() == 'isbn':
                self.book['isbn'] = metadata['dc:identifier']['#text']

        except (TypeError, KeyError):
            try:
                for i in metadata['dc:identifier']:
                    if i['@opf:scheme'].lower() == 'isbn':
                        self.book['isbn'] = i['#text']
                    break
            except:
                pass

        # Book tags
        try:
            self.book['tags'] = metadata['dc:subject']
            if isinstance(self.book['tags'], str):
                self.book['tags'] = [self.book['tags']]
        except:
            self.book['tags'] = []

        # Book cover
        self.generate_book_cover()

    def generate_book_cover(self):
        # This is separate because the book cover needs to
        # be found and extracted both during addition / reading
        self.book['cover'] = None
        try:
            cover_image = [
                i['@href'] for i in self.opf_dict['package']['manifest']['item']
                if i['@media-type'].split('/')[0] == 'image' and
                'cover' in i['@id']][0]
            self.book['cover'] = self.zip_file.read(
                self.find_file(cover_image))
        except:
            pass

        # Find book cover the hard way
        if not self.book['cover']:
            biggest_image_size = 0
            biggest_image = None
            for j in self.zip_file.filelist:
                if os.path.splitext(j.filename)[1] in ['.jpg', '.jpeg', '.png', '.gif']:
                    if j.file_size > biggest_image_size:
                        biggest_image = j.filename
                        biggest_image_size = j.file_size

            if biggest_image:
                self.book['cover'] = self.zip_file.read(
                    self.find_file(biggest_image))
