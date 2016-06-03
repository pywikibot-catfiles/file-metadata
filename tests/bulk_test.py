# -*- coding: utf-8 -*-
"""
This file contains large scale bulk tests to check whether the code is
running find or not. This is tested using a large number of files from
commons.wikimedia.org.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import pytest

from file_metadata.generic_file import GenericFile
from file_metadata.utilities import download
from tests import dump_log, unittest, CACHE_DIR

try:
    import pywikibot
except ImportError as err:
    raise unittest.SkipTest("Module pywikibot not found. Please install it "
                            "to run bulk tests.")
except RuntimeError as err:
    pywikibot = err
    raise unittest.SkipTest('pywikibot requires a user-config.py, which was '
                            'not found. Please create one and then run '
                            'bulk tests.')

from pywikibot import pagegenerators


@pytest.mark.timeout(60 * 60)
class PyWikiBotTestHelper(unittest.TestCase):

    def setUp(self):
        self.site = pywikibot.Site()
        self.site.login()

        if not os.path.isdir(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    @staticmethod
    def download_page(page, fname=None):
        url = page.fileUrl()
        if fname is None:
            _, fname = os.path.split(url)
        fpath = os.path.join(CACHE_DIR, fname)
        download(url, fpath)
        return fpath

    def factory(self, args, fname=None):
        """
        Use pywikibot to fetch pages based on the given arguments.

        :param args:  The args to give to pywikibot
        :param fname: If this is given, the file is stored in this filename.
        :return:      A generator with the pages asked
        """
        gen_factory = pagegenerators.GeneratorFactory(self.site)
        for arg in args:
            gen_factory.handleArg(arg)

        generator = gen_factory.getCombinedGenerator()
        if not generator:
            self.fail('No generator was asked from the factory.')
        else:
            pregen = pagegenerators.PreloadingGenerator(generator)
            for page in pregen:
                if page.exists() and not page.isRedirectPage():
                    page_path = self.download_page(page, fname=fname)
                    yield page, page_path


class BulkCategoryTest(PyWikiBotTestHelper):

    def _test_mimetype_category(self, cat):
        log = []
        for page, path in self.factory(['-catr:' + cat,
                                        '-limit:1000',
                                        '-ns:File']):
            data = GenericFile(path).analyze_mimetype()
            log.append('=== [[:' + page.title() + ']] ===')
            log.append("* '''URL''': " + page.fileUrl())
            log.append("* '''Mime Type''': " +
                       data.get('File:MIMEType', "ERROR: KEY NOT FOUND"))
        dump_log(log, logname='Category_' + cat,
                 header="This page holds all the analysis done on the "
                        "files of the category " + cat + ".\n")

    def test_mimetype_images(self):
        for cat in ['PNG_files', 'SVG_files', 'JPEG_files', 'GIF_files',
                    'TIFF_files']:
            self._test_mimetype_category(cat)

    def test_mimetype_videos(self):
        for cat in ['Ogv_videos', 'Animated_GIF_files',
                    'Animated_PNG', 'Animated_SVG']:
            self._test_mimetype_category(cat)

    def test_mimetype_audio(self):
        for cat in ['WAV_files', 'Ogg_sound_files', 'MIDI_files',
                    'FLAC_files']:
            self._test_mimetype_category(cat)

    def test_mimetype_other(self):
        for cat in ['PDF_files', 'DjVu_files', 'XCF_files']:
            self._test_mimetype_category(cat)