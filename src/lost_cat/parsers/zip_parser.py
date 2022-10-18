import tarfile
import zipfile
import fitz
import logging
import os
import sys

from lost_cat.base_parser import BaseParser
    from utils.path_utils import func_switch_zip, get_file_metadata


logger = logging.getLogger(__name__)

class ZipParser(BaseParser):
    """Process a ZIP document"""
    def __init__(self, uri: str = None, bytes_io: bytes = None, settings: dict = None) -> None:
        super().__init__(uri=uri, bytes_io=bytes_io, settings=settings)
        self._version = "0.0.1"
        self._name = f"{self.__class__.__name__.lower()} {self._version}"

        if not settings:
            logger.debug("Loading default settings")
            self.settings = ZipParser.avail_config()

        logger.debug("Name: %s", self._name)
        logger.debug("Settings: %s", self.settings)

        # file
        self._uri = None
        self._file = None
        if uri:
            self._uri = uri
            logger.info("File: %s", self._uri)
            self._filemd = get_file_metadata(uri=self._uri, options=self.settings.get("options",{}))
            logger.info("MD: %s", self._filemd)
            self._file = func_switch_zip(self._filemd.get("ext"), "open")(uri = self._uri)
            op_func = func_switch_zip(self._filemd.get("ext"), "scan")
            if op_func:
                self._files = op_func(uri=self._uri)
            else:
                raise NotImplementedError()
        elif bytes_io:
            raise NotImplementedError()

    def avail_functions(self) -> dict:
        """Returns a dict prointing to the available functions"""
        return {
            "toc": self.get_toc,
            "metadata": self.get_metadata,
            "parser": self.parser,
            "content": self.get_content,
            "get_item": self.get_item,
        }

    @staticmethod
    def avail_config() -> dict:
        """returns default configuration details about the class"""
        return {
            "options":{
                "splitfolders": True,
                "splitextension": True,
                "stats": True,
            },
            "uritypes": ["file"],
            "source":[
                {
                    "table": "URIMD",
                    "key": "ext",
                    "values": [".zip"]
                }
            ]
        }

    def get_toc(self):
        """ """
        return [d["path"] for d in self._files]

    def get_metadata(self):
        """ """
        _data = {}
        for _kv, _vv in self._filemd.items():
            _data[_kv] = _vv

    def get_content(self):
        """ """
        _data = {}
        for _f in self._files:
            _data[_f.get("path")] = _f
        return _data

    def get_item(self, path:str) -> bytes:
        """ """

        return func_switch_zip(self._filemd.get("ext"), "fetch")(file_obj=self._file, item_path=path)

    def close(self, force: bool = False, block: bool = False, timeout: int = -1):
        """will close the """
        if self._file:
            self._file = None

    def parser(self) -> dict:
        """will parser the open file and retrn the result"""
        _data = {
            "files": self._files
        }
        for _kv, _vv in self._filemd.items():
            _data[_kv] = _vv

        return _data