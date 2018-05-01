# Lector
Qt based ebook reader

Currently supports:
* pdf
* epub
* mobi
* azw / azw3 / azw4
* cbr / cbz

Support for a bunch of other formats is coming. Please see the TODO for additional information.

## Requirements
| Package | Version tested |
| --- | --- |
| Qt5 | 5.10.1 |
| Python | 3.6 |
| PyQt5 | 5.10.1 |
| python-beautifulsoup4 | 4.6.0 |
| poppler-qt5 | 0.61.1 |
| python-poppler-qt5 | 0.24.2 |

poppler-qt5 and python-poppler-qt5 are optional.

## Installation
### Manual
0. Install dependencies - I recommend using your package manager for this.
1. Clone repository
2. Type the following in the root directory:

        $ python setup.py build
        # python setup.py install
3. OR launch with `lector/__main__.py`

### Available packages
* [AUR](https://aur.archlinux.org/packages/lector-git/)
* [Gentoo (unofficial)](https://bitbucket.org/szymonsz/gen2-overlay/src/master/app-text/lector/)

## Translations
1. There is a `SAMPLE.ts` file [here](https://github.com/BasioMeusPuga/Lector/tree/master/lector/resources/translations). Open it in `Qt Linguist`.
2. Pick the language you wish to translate to.
3. Translate relevant strings.
4. Try to resist the urge to include profanity.
5. Save the file as `Lector_<language>` and send it to me, preferably as a pull request.

Please keep the translations short. There's only so much space for UI elements.

## Screenshots

### Main window
![alt tag](https://i.imgur.com/yrv2c0a.png)

### Table view
![alt tag](https://i.imgur.com/b1XdXqP.png)

### Book reading view
![alt tag](https://i.imgur.com/Tei6TqF.png)

### Comic reading view
![alt tag](https://i.imgur.com/U5JR35g.png)

### Bookmark support
![alt tag](https://i.imgur.com/RZkmCzG.png)

### View profiles
![alt tag](https://i.imgur.com/gkJ88pi.png)

### Metadata editor
![alt tag](https://i.imgur.com/AqQREBf.png)

### In program dictionary
![alt tag](https://i.imgur.com/Vh9xQUC.png)

## Reporting issues
When reporting issues:

* If you're having trouble with a book while the rest of the application / other books work, please link to a copy of the book itself.
* If nothing is working, please make sure the requirements mentioned above are all installed, and are at least at the version mentioned.

## Attributions
* [KindleUnpack](https://github.com/kevinhendricks/KindleUnpack)
* [rarfile](https://github.com/markokr/rarfile)
* [Papirus icon theme](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme)
