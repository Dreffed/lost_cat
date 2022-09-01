""""""
import os
import logging
import PIL.Image, PIL.ExifTags
from lost_cat.utils.tag_anon import TagAnon

logger = logging.getLogger(__name__)

class EXIFParser:
    """

    ---
    Attributes
    ----------
    Methods
    -------

    """
    name = "Image"
    version = "0.0.1"

    def __init__(self, uri: str) -> None:
        self._anon = None
        self._uri = uri
        self._img = PIL.Image.open(self._uri)
        self._grp_tags = {}
        self._export_tags = {}
        self._alias_tags = {}

    def __str__(self):
        return f"{self.name} {self.version} <{self._uri}>"

    def close(self) -> None:
        """"""
        if self._img:
            self._img = None

    def set_anonimizer(self, anonimizer: TagAnon) -> None:
        """Allows for the metadata tags to be anonymized"""
        self._anon = anonimizer

    def set_group_tags(self, tags: dict) -> None:
        """Sets the metadata tags to be used for grouping
        The grouping is used to organize the structure"""
        self._grp_tags = tags

    def set_export_tags(self, tags):
        """Sets the tags to use for general metadata"""
        self._export_tags = tags

    def get_extensions(self):
        """

        Parameters
        ----------
        Returns
        -------
        None
        """
        return [".bmp",".dds",".dib",".eps",".gif",".icns",".ico",".im",".jpeg",".msp",".pcx",".png",".ppm",
        ".sgi",".tga",".tiff",".webp",".xbm",".blp",".cur",".dcx",".fli",".flc",".fpx",".ftex",".gbr",".gd",
        ".imt",",iptc",".naa",".mcidas",".mic",".mpo",".pcd",".pixar",".psd",".wal",".wmf",",xpm"]

    def get_functions(self):
        """

        Parameters
        ----------
        Returns
        -------
        None
        """
        return {
            "metadata": self.get_metadata,
            "analyze": self.analyze,
            #"contents": self.get_contents
        }

    def get_metadata(self) -> dict:
        """This will return the doc info infomation from the
        Named file.

        Parameters
        ----------
        Returns
        -------
        None
        """
        width, height = self._img.size
        tags = {PIL.ExifTags.TAGS[k]: v for k, v in self._img._getexif().items() if k in PIL.ExifTags.TAGS}
        data = {
            "width": width,
            "height": height,
            "tags": tags,
            "mode": self._img.mode,
            "info": self._img.info,
            "bands": list(self._img.getbands())
        }
        return data

    def analyze(self) -> dict:
        """

        Parameters
        ----------
        Returns
        -------
        None
        """
        data = dict

        return data

    def get_contents(self) -> list:
        """This will return the paragroah objects in a word document

        Parameters
        ----------
        Returns
        -------
        None
        """
        data = []

        return data