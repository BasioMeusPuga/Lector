#!/usr/bin/env python3

import os
import re
import collections
import ebooklib.epub


def get_book_essentials(filename):
    book = ebooklib.epub.read_epub(filename)

    # Get book title
    title = book.title.strip()

    # Get cover image
    # This seems hack-ish, but that's never stopped me before
    image_path = None
    try:
        cover = book.metadata['http://www.idpf.org/2007/opf']['cover'][0][1]['content']
        cover_item = book.get_item_with_id(cover)

        # In case no cover_item is returned, we search the items
        # in the book and get the first referenced image
        if not cover_item:
            for j in book.guide:
                try:
                    if (j['title'].lower in ['cover', 'cover-image', 'coverimage'] or j['type'] == 'coverimagestandard'):
                        image_path = j['href']
                    break
                except KeyError:
                    pass

            if not image_path:
                for j in book.items:
                    if j.media_type == 'application/xhtml+xml':
                        _regex = re.search(r"src=\"(.*)\"\/", j.content.decode('utf-8'))
                        if _regex:
                            image_path = _regex[1]
                        break

            for k in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                if os.path.basename(k.file_name) == os.path.basename(image_path):
                    image_content = k.get_content()

        else:
            image_content = cover_item.get_content()

    except KeyError:
        print('Cannot parse ' + filename)

    # Get ISBN ID
    isbn_id = None
    try:
        identifier = book.metadata['http://purl.org/dc/elements/1.1/']['identifier']
        for i in identifier:
            identifier_provider = i[1]['{http://www.idpf.org/2007/opf}scheme']
            if identifier_provider.lower() == 'isbn':
                isbn_id = i[0]
                break
    except KeyError:
        pass

    with open('/home/akhil/aa.jpg', 'bw') as myimg:
        myimg.write(image_content)
