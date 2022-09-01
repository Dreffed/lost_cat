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

    def set_group_tags(self, tags: dict) -> None:
        """Sets the metadata tags to be used for grouping
        The grouping is used to organize the structure"""
        self._grp_tags = tags

    def set_export_tags(self, tags):
        """Sets the tags to use for general metadata"""
        self._export_tags = tags

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
            "contents": self.get_image,
            "export": self.get_convertedimage
        }

    def get_extensions(self):
        """

        Parameters
        ----------

        Returns
        -------
        None
        """
        return [".dcm"]

    def set_alias_tags(self, tags):
        """The alias tag do a simple replacement with another tag"""
        self._alias_tags = tags

    def get_tag(self, tag_id: str) -> dict:
        """will return the tag specified by a number"""
        return self._dcm_file.dir()

    def get_metadata(self) -> dict:
        """This will return the doc info infomation from the
        Named file.

        Parameters
        ----------

        Returns
        -------
        None
        """
        data = self._prep_tags()
        return data

    def get_image(self) -> dict:
        """This will return the paragroah objects in a word document

        Parameters
        ----------

        Returns
        -------
        None
        """
        if not hasattr(self._dcm_file, "SliceLocation"):
            # missing a slice location...
            return None

        data = self._prep_tags()
        data["pixels"] = self._dcm_file.pixel_array

        return data

    def get_convertedimage(self, conversion: str) -> dict:
        """will use the conversion string, and return an array of image data"""
        pass

    def _prep_tags(self) -> dict:
        """generates an obj of the exp and grp tags..."""
        data = {
            "grouping": {},
            "metadata": {}
        }

        for t in self._grp_tags:
            # chjeck for PI data...
            t = self._alias_tags.get(t,t)

            if self._anon.is_pii(t):
                data["grouping"][t] = self._anon.get_anon(tag=t, value=self._dcm_file.get(t))
            else:
                data["grouping"][t] = self._dcm_file.get(t)

        for t in self._export_tags:
            t = self._alias_tags.get(t,t)
            # chjeck for PI data...
            if self._anon.is_pii(t):
                data["metadata"][t] = self._anon.get_anon(tag=t, value=self._dcm_file.get(t))
            else:
                data["metadata"][t] = self._dcm_file.get(t)

        return data
