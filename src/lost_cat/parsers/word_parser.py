import docx2txt
from docx import Document
import logging
import os
import sys

from lost_cat.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class WordParser(BaseParser):
    """Process a word document"""
    def __init__(self, uri: str = None, bytes_io: bytes = None, settings: dict = None) -> None:
        super().__init__(uri=uri, bytes_io=bytes_io, settings=settings)
        self._version = "0.0.1"
        self._name = f"{self.__class__.__name__.lower()} {self._version}"

        if not settings:
            logger.debug("Loading default settings")
            self.settings = WordParser.avail_config()

        logger.debug("Name: %s", self._name)
        logger.debug("Settings: %s", self.settings)

        # file
        self._uri = None
        self._file = None
        if uri:
            self._uri = uri
            self._file = Document(self._uri)
        elif bytes_io:
            self._bytes_io = bytes_io
            self._file = Document(bytes_io)

    def avail_functions(self) -> dict:
        """Returns a dict prointing to the available functions"""
        return {
            #"anonimizer": self.set_anonimizer,
            #"tags_alias": self.set_alias_tags,
            #"tags_metadata": self.set_metadata_tags,
            #"tags_groups": self.set_groups_tags,
            "parser": self.parser,
            "content": self.get_content,
        }

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
                    "values": [".docx"]
                }
            ]
        }

    def close(self, force: bool = False, block: bool = False, timeout: int = -1):
        """will close the """
        if self._file:
            self._file = None

    def parser(self) -> dict:
        """will parser the open file and retrn the result"""
        return self.get_metadata()

    def get_metadata(self):
        """ """
        cp = self._file.core_properties
        return {
            "author": 	        cp.author,
            "category": 	    cp.category,
            "comments": 	    cp.comments,
            "content_status": 	cp.content_status,
            "created": 	        cp.created,
            "identifier": 	    cp.identifier,
            "keywords": 	    cp.keywords,
            "language": 	    cp.language,
            "last_modified_by": cp.last_modified_by,
            "last_printed": 	cp.last_printed,
            "modified": 	    cp.modified,
            "revision": 	    cp.revision,
            "subject": 	        cp.subject,
            "title": 	        cp.title,
            "version": 	        cp.version,
        }

    def get_content(self):
        """ """
        _text = docx2txt.process(self._uri)
        _lines = [x.strip() for x in _text.split("\n") if x.strip()]

        return {
            "type": "lines",
            "lines": _lines
        }
