#!/usr/bin/env python3
# Every parser is supposed to have the following methods, even if they return None:
# read_book()
# get_title()
# get_author()
# get_year()
# get_cover_image()
# get_isbn()
# get_contents() - Should return a tuple with 0: TOC 1: Deletable temp_directory

import os
import re
import zipfile
import collections

import ebooklib.epub


class ParseEPUB:
    def __init__(self, filename, temp_dir, file_md5):
        # TODO
        # Maybe also include book description
        self.filename = filename
        self.book = None
        self.temp_dir = temp_dir
        self.file_md5 = file_md5

    def read_book(self):
        try:
            self.book = ebooklib.epub.read_epub(self.filename)
        except (KeyError, AttributeError, FileNotFoundError):
            print('Cannot parse ' + self.filename)
            return

    def get_title(self):
        return self.book.title.strip()

    def get_author(self):
        try:
            return self.book.metadata['http://purl.org/dc/elements/1.1/']['creator'][0][0]
        except KeyError:
            return None

    def get_year(self):
        try:
            return self.book.metadata['http://purl.org/dc/elements/1.1/']['date'][0][0][:4]
        except KeyError:
            return None

    def get_cover_image(self):
        # Get cover image
        # This seems hack-ish, but that's never stopped me before
        image_path = None
        try:
            cover = self.book.metadata['http://www.idpf.org/2007/opf']['cover'][0][1]['content']
            cover_item = self.book.get_item_with_id(cover)
            if cover_item:
                return cover_item.get_content()
        except KeyError:
            pass

        # In case no cover_item is returned, we look for a cover in the guide
        for i in self.book.guide:
            try:
                if (i['title'].lower in ['cover', 'cover-image', 'coverimage'] or
                        i['type'] == 'coverimagestandard'):
                    image_path = i['href']
                break
            except KeyError:
                pass

        # If that fails, we find the first image referenced in the book
        if not image_path:
            for i in self.book.items:
                if i.media_type == 'application/xhtml+xml':
                    _regex = re.search(r"src=\"(.*)\"\/", i.content.decode('utf-8'))
                    if _regex:
                        image_path = _regex[1]
                    break

        if image_path:
            for i in self.book.get_items_of_type(ebooklib.ITEM_IMAGE):
                if os.path.basename(i.file_name) == os.path.basename(image_path):
                    return i.get_content()

        # And if that too fails, we get the first image referenced in the file
        for i in self.book.items:
            if i.media_type == 'image/jpeg' or i.media_type == 'image/png':
                return i.get_content()


    def get_isbn(self):
        try:
            identifier = self.book.metadata['http://purl.org/dc/elements/1.1/']['identifier']
            for i in identifier:
                identifier_provider = i[1]['{http://www.idpf.org/2007/opf}scheme']
                if identifier_provider.lower() == 'isbn':
                    isbn = i[0]
                    return isbn
        except KeyError:
            return None

    def get_contents(self):
        # Extract all contents to a temporary directory
        # for relative path lookup voodoo
        extract_path = os.path.join(self.temp_dir, self.file_md5)
        zipfile.ZipFile(self.filename).extractall(extract_path)

        contents = collections.OrderedDict()

        def flatten_chapter(toc_element):
            output_list = []
            for i in toc_element:
                if isinstance(i, (tuple, list)):
                    output_list.extend(flatten_chapter(i))
                else:
                    output_list.append(i)
            return output_list

        for i in self.book.toc:
            if isinstance(i, (tuple, list)):
                title = i[0].title
                contents[title] = 'Composite Chapter'
                # composite_chapter = flatten_chapter(i)
                # composite_chapter_content = []
                # for j in composite_chapter:
                #     href = j.href
                #     composite_chapter_content.append(
                #         self.book.get_item_with_href(href).get_content())

                # contents[title] = composite_chapter_content
            else:
                title = i.title
                href = i.href
                try:
                    content = self.book.get_item_with_href(href).get_content()
                    if content:
                        contents[title] = content.decode()
                    else:
                        raise AttributeError
                except AttributeError:
                    contents[title] = ''

        # Special settings that have to be returned with the file
        # Referenced in sorter.py
        file_settings = {
            'temp_dir': extract_path,
            'images_only': False}

        return contents, file_settings
