import os
import shutil
import six
from lxml import etree, html
from pathlib import Path
from tempfile import mkdtemp

from ..exceptions import UnknownMethod, ShellError

from .utils import ShellParser
from .image import Parser as TesseractParser


class Parser(ShellParser):
    """Extract text from pdf files using either the ``pdftotext`` method
    (default) or the ``pdfminer`` method.
    """

    def extract(self, filename, method='', **kwargs):
        if method == '' or method == 'pdftotext':
            try:
                return self.extract_pdftotext(filename, **kwargs)
            except ShellError as ex:
                # If pdftotext isn't installed and the pdftotext method
                # wasn't specified, then gracefully fallback to using
                # pdfminer instead.
                if method == '' and ex.is_not_installed():
                    return self.extract_pdfminer(filename, **kwargs)
                else:
                    raise ex

        elif method == 'pdfminer':
            return self.extract_pdfminer(filename, **kwargs)
        elif method == 'tesseract':
            return self.extract_tesseract(filename, **kwargs)
        elif method == 'tesseract-hocr':
            return self.extract_tesseract_hocr(filename, **kwargs)
        else:
            raise UnknownMethod(method)

    def extract_pdftotext(self, filename, **kwargs):
        """Extract text from pdfs using the pdftotext command line utility."""
        if 'layout' in kwargs:
            args = ['pdftotext', '-layout', filename, '-']
        else:
            args = ['pdftotext', filename, '-']
        stdout, _ = self.run(args)
        return stdout

    def extract_pdfminer(self, filename, **kwargs):
        """Extract text from pdfs using pdfminer."""
        stdout, _ = self.run(['pdf2txt.py', filename])
        return stdout

    def extract_tesseract(self, filename, **kwargs):
        """Extract text from pdfs using tesseract (per-page OCR)."""
        temp_dir = mkdtemp()
        base = os.path.join(temp_dir, 'conv')
        contents = []
        try:
            stdout, _ = self.run(['pdftoppm', filename, base])

            for page in sorted(os.listdir(temp_dir)):
                page_path = os.path.join(temp_dir, page)
                page_content = TesseractParser().extract(page_path, **kwargs)
                contents.append(page_content)
            return six.b('').join(contents)
        finally:
            shutil.rmtree(temp_dir)

    def extract_tesseract_hocr(self, filename, **kwargs):
        """Extract text from pdfs using tesseract (per-page OCR)."""
        temp_dir = mkdtemp()
        base = os.path.join(temp_dir, 'conv')
        contents = []
        try:
            n = 1
            stdout, _ = self.run(['pdftoppm', filename, base])

            for page in sorted(os.listdir(temp_dir)):
                page_path = os.path.join(temp_dir, page)
                file_text, file_hocr = TesseractParser().extract_hocr(page_path, **kwargs)

                # txt
                in_file = open(file_text, "rb")
                page_content = in_file.read()
                in_file.close()
                contents.append(page_content)

                # hocr
                if n == 1:
                    doc = html.parse(file_hocr)
                    pages = doc.xpath("//*[@class='ocr_page']")
                    container = pages[-1].getparent()
                else:
                    doc2 = html.parse(file_hocr)
                    pages = doc2.xpath("//*[@class='ocr_page']")
                    for pagen in pages:
                        container.append(pagen)
                n += 1

            return [ six.b('').join(contents), str(etree.tostring(doc, pretty_print=True).decode('UTF-8')) ]
        finally:
            shutil.rmtree(temp_dir)
