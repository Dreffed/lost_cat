"""this will scan a word set and return the details"""
from email.errors import ObsoleteHeaderDefect
import io
import logging
import multiprocessing as mp
import os
import threading as td
import zipfile
from queue import Empty

from lost_cat.processors.base_processor import BaseProcessor
from lost_cat.parsers.word_parser import WordParser
from lost_cat.utils.path_utils import SourceNotHandled, scan_files
from lost_cat.utils.tag_anon import TagAnon

logger = logging.getLogger(__name__)

class WordProcessor(BaseProcessor):
    """Will process the queue and provide a """

    def __init__(self, settings: dict = None):
        """"""
        super().__init__(settings=settings)
        self._version = "0.0.1"
        self._name = f"{self.__class__.__name__.lower()} {self._version}"
        self._semiphore = f"DONE: {self._name}"

        if not settings:
            logger.debug("Loading default settings")
            self.settings = WordParser.avail_config()

        logger.debug("Name: %s", self._name)
        logger.debug("Semiphore: %s", self._semiphore)
        logger.debug("Settings: %s", self.settings)

        # init the tags lists
        self._anon = None
        self._grp_tags = {}
        self._md_tags = {}
        self._alias_tags = {}

    def avail_functions(self) -> dict:
        """Returns a dict prointing to the available functions"""
        return {
            "parser": self.parser,
            "anonimizer": self.anonimizer,
            "tags_alias": self.alias_tags,
            "tags_groups": self.groups_tags,
            "tags_metadata": self.metadata_tags,
            #"metadata": self.metadata,
            #"contents": self.get_image,
            "export": {
                "numpy": {
                    "ext": ".pickle",
                    #"func": self.get_numpy},
                },
                "hounsfield": {
                    "ext": ".bmp",
                    #"func": self.get_hounsfield,
                }
            }
        }

    @staticmethod
    def avail_config() -> dict:
        """returns default configuration details about the class"""
        return {
            "options":{
            },
            "uritypes": [
                "file", "zipfiles"
            ],
            "source":[
                {
                    "table": "URIMD",
                    "field": "key",
                    "select": "ext",
                    "filter": [".docx"],

                }
            ],
            "uri_metadata": ["zipfile"],
            "threads": {
                "count": 1,
                "stop": True, # tells the system to stop when the in queue is empty
                "timeout": 2
            }
        }

    def add_action(self, obj: object = None
            ):
        """ Will add an action to run against the file in the queue
        abd add the return to the metadata if needed."""
        pass

    def anonimizer(self, anonimizer: TagAnon) -> None:
        """Allows for the metadata tags to be anonymized"""
        self._anon = anonimizer

    def alias_tags(self, tags: list) -> None:
        """Allows for the metadata tags to be anonymized"""
        self._alias_tags = tags

    def groups_tags(self, tags: list) -> None:
        """Sets the metadata tags to be used for grouping
        The grouping is used to organize the structure"""
        self._grp_tags = tags

    def metadata_tags(self, tags: list):
        """Sets the tags to use for general metadata"""
        self._md_tags = tags