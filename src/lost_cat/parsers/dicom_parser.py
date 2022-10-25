import numpy as np
import logging
import pydicom
import os
import sys

from PIL import Image

from lost_cat.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class DICOMParser(BaseParser):
    """A DICOM file parser and converter"""
    def __init__(self, uri: str = None, bytes_io: bytes = None, settings: dict = None) -> None:
        super().__init__(uri=uri, bytes_io=bytes_io, settings=settings)
        self._version = "0.0.1"
        self._name = f"{self.__class__.__name__.lower()} {self._version}"

        if not settings:
            logger.debug("Loading default settings")
            self.settings = DICOMParser.avail_config()

        logger.debug("Name: %s", self._name)
        logger.debug("Settings: %s", self.settings)

        # file
        self._uri = None
        self._file = None
        if uri:
            self._uri = uri
            self._file = pydicom.dcmread(self._uri)
        elif bytes_io:
            self._file = pydicom.dcmread(bytes_io)

    def avail_functions(self) -> dict:
        """Returns a dict prointing to the available functions"""
        return {
            "parser": self.parser,
            "array": self.get_array,
            "tags_alias": self.set_alias_tags,
            "tags_metadata": self.set_metadata_tags,
            "tags_groups": self.set_groups_tags,
            "image": self.get_image,
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
                    "values": [".dcm"]
                }
            ]
        }

    def close(self, force: bool = False, block: bool = False, timeout: int = -1):
        """will close the """
        if self._file:
            self._file = None

    def _prep_tags(self) -> dict:
        """generates an obj of the anonimized exp and grp tags...

        Returns
        -------
        dict:   the tag data extracted from the underlying file and grouped
                by group tag lsit, and export

        """
        data = {
            "grouping": {},
            "metadata": {}
        }

        for tag in self._groups_tags:
            # chjeck for PI data...
            tag = self._alias_tags.get(tag,tag)

            if self._anon and self._anon.is_pii(tag):
                data["grouping"][tag] = self._anon.get_anon(tag=tag, value=self._file.get(tag))
            else:
                data["grouping"][tag] = self._file.get(tag)

        for tag in self._metadata_tags:
            tag = self._alias_tags.get(tag,tag)
            # chjeck for PI data...
            if self._anon and self._anon.is_pii(tag):
                data["metadata"][tag] = self._anon.get_anon(tag=tag, value=self._file.get(tag))
            else:
                data["metadata"][tag] = self._file.get(tag)

        return data

    def parser(self) -> dict:
        """will parser the open file and retrn the result"""
        _data = self._prep_tags()
        return _data

    def get_array(self) -> dict:
        """This will return the dcm as pixel array
        """
        if not hasattr(self._file, "SliceLocation"):
            # missing a slice location...
            return None

        _data = self._prep_tags()
        _data["pixel_array"] = self._file.pixel_array
        return _data

    def get_image(self, ext: str = ".bmp", x: int = 255, y: int = 255) -> object:
        """ """
        _imarr = self._file.pixel_array.astype(float)
        rescaled_image = (np.maximum(_imarr,0)/_imarr.max())*255 # float pixels
        final_image = np.uint8(rescaled_image)
        return Image.fromarray(final_image)

    def get_hounsfield(self):
        """ """
        _imarr = self._file.pixel_array.astype(np.int16) * self._file.RescaleSlope + self._file.RescaleIntercept

        return np.array(_imarr, dtype=np.int16)
