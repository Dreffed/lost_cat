"""This module contains DICOM file parser class and helper functions"""
import logging
import pydicom
from lost_cat.utils.tag_anon import TagAnon

logger = logging.getLogger(__name__)

class DICOM_Parser():
    """This will process the DICOM file"""

    name = "DICOM"
    version = "0.0.1"

    def __init__(self, uri: str = None, bytes_io: bytes = None) -> None:
        self._anon = None
        if uri:
            self._uri = uri
            self._dcm_file = pydicom.dcmread(self._uri)
        elif bytes_io:
            self._uri - "ZIP File"
            self._dcm_file = pydicom.dcmread(bytes_io)

        # init the tags lists
        self._grp_tags = {}
        self._export_tags = {}
        self._alias_tags = {}

    def __str__(self):
        return f"{self.name} {self.version} <{self._uri}>"

    def close(self) -> None:
        """"""
        if self._dcm_file:
            self._dcm_file = None

    def set_anonimizer(self, anonimizer: TagAnon) -> None:
        """Allows for the metadata tags to be anonymized"""
        self._anon = anonimizer

    def set_group_tags(self, tags: list) -> None:
        """Sets the metadata tags to be used for grouping
        The grouping is used to organize the structure"""
        self._grp_tags = tags

    def set_export_tags(self, tags: list):
        """Sets the tags to use for general metadata"""
        self._export_tags = tags

    def get_functions(self) -> dict:
        """

        Returns
        -------
        dict
        """
        return {
            "metadata": self.get_metadata,
            "contents": self.get_image,
            "export": self.get_convertedimage
        }

    def get_extensions(self) -> list:
        """ lists what extensions this parser applies to

        Returns
        -------
        list:
        """
        return [".dcm"]

    def set_alias_tags(self, tags: list) -> None:
        """The alias tag do a simple replacement with another tag

        Parameters
        ----------

        """
        self._alias_tags = tags

    def get_tag(self, tag_id: str) -> dict:
        """will return the tag specified by a number"""
        return self._dcm_file.dir()

    def get_metadata(self) -> dict:
        """This will return the doc info infomation from the
        Named file.

        Returns
        -------
        None
        """
        data = self._prep_tags()
        return data

    def get_image(self) -> dict:
        """This will return the paragroah objects in a word document

        Returns
        -------
        dict
        """
        if not hasattr(self._dcm_file, "SliceLocation"):
            # missing a slice location...
            return None

        data = self._prep_tags()
        data["pixels"] = self._dcm_file.pixel_array

        return data

    def get_convertedimage(self, conversion: str) -> dict:
        """will use the conversion string, and return an array of image data
        Returns
        -------
        dict: the
        """

        pass

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

        for tag in self._grp_tags:
            # chjeck for PI data...
            tag = self._alias_tags.get(tag,tag)

            if self._anon.is_pii(tag):
                data["grouping"][tag] = self._anon.get_anon(tag=tag, value=self._dcm_file.get(tag))
            else:
                data["grouping"][tag] = self._dcm_file.get(tag)

        for tag in self._export_tags:
            tag = self._alias_tags.get(tag,tag)
            # chjeck for PI data...
            if self._anon.is_pii(tag):
                data["metadata"][tag] = self._anon.get_anon(tag=tag, value=self._dcm_file.get(tag))
            else:
                data["metadata"][tag] = self._dcm_file.get(tag)

        return data
