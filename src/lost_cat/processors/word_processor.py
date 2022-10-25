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
        self._anonobj = None
        self._groups_tags = {}
        self._metadata_tags = {}
        self._alias_tags = {}

    def avail_functions(self) -> dict:
        """Returns a dict prointing to the available functions"""
        return {
            "parser": self.parser,
            #"anonimizer": self.anonimizer,
            #"tags_alias": self.alias_tags,
            #"tags_groups": self.groups_tags,
            #"tags_metadata": self.metadata_tags,
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
        self._anonobj = anonimizer

    def alias_tags(self, tags: list) -> None:
        """Allows for the metadata tags to be anonymized"""
        self._alias_tags = tags

    def groups_tags(self, tags: list) -> None:
        """Sets the metadata tags to be used for grouping
        The grouping is used to organize the structure"""
        self._groups_tags = tags

    def metadata_tags(self, tags: list):
        """Sets the tags to use for general metadata"""
        self._metadata_tags = tags

    def parser(self) -> None:
        """ load the for each match to a parser, load the
        an in_queue with values, then call the *_processer
        to process the queue.
        The parser enabled processer will use a helper file to handle the files"""
        use_threads = self.settings.get("threads",{}).get("count",5)

        for t_idx in range(use_threads):
            logger.info("Thread: %s",t_idx)
            scan_q = td.Thread(target=self.parser_file)
            scan_q.start()
            scan_q.join()

    def parser_file(self):
        """A parser scanner function, quick and dirty"""
        t_settings = self.settings.get("threads",{})
        self.input.put(self.semiphore)

        while self.input:
            try:
                q_item = self.input.get(timeout=t_settings.get("timeout")) if self.input else None
                if q_item == self.semiphore:
                    break

                # if the user wants to kill the queue if there are not entries...
                # requires timeout set, otherwise the queue get blocks...
                if not q_item and self.settings.get("threads",{}).get("stop"):
                    break

                _uri=q_item.get("uri")
                if not os.path.exists(_uri):
                    # most likely a zipfile...
                    zf = zipfile.ZipFile(q_item.get("zipfile"))
                    file_data = zf.read(q_item.get("uri"))
                    bytes_io = io.BytesIO(file_data)
                    _fileobj = WordParser(bytes_io=bytes_io)

                else:
                    _fileobj = WordParser(uri=_uri)

                # return the file metadata and information...
                # load the
                _fileobj.set_anon(anon=self._anonobj)
                _fileobj.set_groups_tags(tags=self._groups_tags)
                _fileobj.set_metadata_tags(tags=self._metadata_tags)
                _filemd = _fileobj.parser()
                _fileobj.close()

                # create the returning object
                _data = {
                    "processorid": self.processorid,
                    "uri id": q_item.get("uriid"),
                    "uri_type": q_item.get("uri_type"),
                    "uri": q_item.get("uri"),
                    "metadata": {},
                    "versions": {
                        "__latest__": True,
                        "versionmd" : _filemd
                    }
                }

                logger.debug("O Data: %s", _data)
                self.output.put(_data)

            except Empty:
                break