import codecs
from os import path
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESC = f.read()

INSTALL_DEPS = ['PyQt5==5.10.1',
                'requests==2.18.4',
                'beautifulsoup4==4.6.0']
TEST_DEPS = ['pytest',
             'unittest2']
DEV_DEPS = []

setup(
    name='lector',

    # https://pypi.python.org/pypi/setuptools_scm
    use_scm_version=True,

    description='Qt-based ebook reader',
    long_description=LONG_DESC,

    url='https://github.com/BasioMeusPuga/Lector',

    author='BasioMeusPuga',
    author_email='disgruntled.mob@gmail.com',

    license='GPL v3.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Intended Audience :: End Users/Desktop',

        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    # What does your project relate to?
    keywords='qt ebook epub kindle',

    packages=find_packages(),

    entry_points={
          'console_scripts': [
              'lector = lector.__main__:main'
          ]
      },
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=INSTALL_DEPS,

    setup_requires=['setuptools_scm'],

    python_requires='>=3.4, <4.0',

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': DEV_DEPS,
        'test': TEST_DEPS
    },
)
