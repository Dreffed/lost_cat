import fitz
import logging
import os
import sys
try:
    from parsers.base_parser import BaseParser
except:
    currentdir = os.path.dirname(os.path.abspath(os.getcwd()))
    if not currentdir in sys.path:
        sys.path.insert(0, currentdir)
    from ..parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class PDFParser(BaseParser):
    """Process a word document"""
    def __init__(self, uri: str = None, bytes_io: bytes = None, settings: dict = None) -> None:
        super().__init__(uri=uri, bytes_io=bytes_io, settings=settings)
        self._version = "0.0.1"
        self._name = f"{self.__class__.__name__.lower()} {self._version}"

        if not settings:
            logger.debug("Loading default settings")
            self.settings = PDFParser.avail_config()

        logger.debug("Name: %s", self._name)
        logger.debug("Settings: %s", self.settings)

        # file
        self._uri = None
        self._file = None
        if uri:
            self._uri = uri
            self._file = fitz.open(self._uri)
        elif bytes_io:
            self._file = fitz.open(stream=bytes_io, filetype="pdf")

    @staticmethod
    def avail_config() -> dict:
        """returns default configuration details about the class"""
        return {
            "options":{},
            "uritypes": ["file"],
            "source":[
                {
                    "table": "URIMD",
                    "key": "ext",
                    "values": [".pdf"]
                }
            ]
        }

    def parser(self) -> dict:
        """will parser the open file and retrn the result"""
        return self.get_metadata()

    def get_toc(self) -> dict:
        """ """
        _data = []
        _data = self._file.get_toc(simple=True)

        return {
            "type": "toc",
            "toc": _data
        }

    def get_content(self) -> dict:
        """ """
        _pages = {}
        _lines = []
        for _idx, _page in enumerate(self._file):
            _text = _page.get_text('text', sort=True, flags=2)
            if _text:
                _pages[_idx] = _text
                # the text is split on lines
                _lines.extend([x.strip() for x in _text.split("\n") if x.strip()])

        return {
            "type": "lines",
            "pages": _pages,
            "lines": _lines
        }

    def get_metadata(self) -> dict:
        """ """
        return self._file.metadata

    def avail_functions(self) -> dict:
        """Returns a dict prointing to the available functions"""
        return {
            "toc": self.get_toc,
            "content": self.get_content,
            "metadata": self.get_metadata,
            "parser": self.parser,
        }

    def close(self, force: bool = False, block: bool = False, timeout: int = -1):
        """will close the """
        if self._file:
            self._file = None