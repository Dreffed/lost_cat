"""this will scan a file system and return the file details"""
import logging
import os
import sys

from lost_cat.utils.tag_anon import TagAnon

logger = logging.getLogger(__name__)

class BaseParser():
    """A base class for a single file parser or converter"""
    def __init__(self, uri : str = None, bytes_io: bytes = None, settings: dict = None) -> None:
        self._version = "0.0.1"
        self._name = f"{self.__class__.__name__.lower()} {self._version}"

        if not settings:
            logger.debug("Loading default settings")
            self.settings = BaseParser.avail_config()

        logger.debug("Name: %s", self._name)
        logger.debug("Settings: %s", self.settings)

        # init the tags lists
        self._anon = None
        self._anon_tags = {}
        self._alias_tags = {}
        self._grp_tags = {}
        self._md_tags = {}

    @property
    def name(self):
        """Returns the class name"""
        return self._name

    @property
    def version(self):
        """Returns the version"""
        return self._version

    def avail_functions(self) -> dict:
        """Returns a dict prointing to the available functions"""
        return {
            "parser": self.parser
        }

    @staticmethod
    def avail_config() -> dict:
        """returns default configuration details about the class"""
        return {
            "options":{},
            "uritypes": ["file"],
            "filter":[
                {
                    "table": "URIMD",
                    "key": "ext",
                    "values": []
                }
            ]
        }

    def set_anonimizer(self, anonimizer: TagAnon) -> None:
        """Allows for the metadata tags to be anonymized"""
        self._anon = anonimizer

    def set_alias_tags(self, tags: list) -> None:
        """Allows for the metadata tags to be anonymized"""
        self._alias_tags = tags

    def set_group_tags(self, tags: list) -> None:
        """Sets the metadata tags to be used for grouping
        The grouping is used to organize the structure"""
        self._grp_tags = tags

    def set_metadata_tags(self, tags: list):
        """Sets the tags to use for general metadata"""
        self._md_tags = tags

    def close(self, force: bool = False, block: bool = False, timeout: int = -1):
        """will close the current file and connectors"""
        pass

    def parser(self) -> dict:
        """will parser the open file and retrn the result"""
        _data = {}
        return _data
