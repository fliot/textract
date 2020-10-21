"""
Process an image file using tesseract.
"""
import os

from .utils import ShellParser


class Parser(ShellParser):
    """Extract text from various image file formats using tesseract-ocr"""

    def extract(self, filename, **kwargs):

        # if language given as argument, specify language for tesseract to use
        if 'language' in kwargs:
            args = ['tesseract', filename, 'stdout', '-l', kwargs['language']]
        else:
            args = ['tesseract', filename, 'stdout']

        stdout, _ = self.run(args)
        return stdout


    def extract_hocr(self, filename, **kwargs):

        # if language given as argument, specify language for tesseract to use
        if 'language' in kwargs:
            args = ['tesseract', filename, "%s-out" % filename, '-l', kwargs['language'], '-c', 'tessedit_create_hocr=1', '-c', 'tessedit_create_txt=1']
        else:
            args = ['tesseract', filename, "%s-out" % filename, '-c', 'tessedit_create_hocr=1', '-c', 'tessedit_create_txt=1']

        stdout, _ = self.run(args)
        return "%s-out.txt" % filename, "%s-out.hocr" % filename
