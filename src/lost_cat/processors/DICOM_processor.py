"""this will scan a file system and return the file details"""
import io
import logging
import multiprocessing as mp
import os
import threading as td
import zipfile
from parsers.DICOM_parser import DICOMParser

from utils.tag_anon import TagAnon
try:
    from processors.base_processor import BaseProcessor
except ImportError:
    import sys
    from os import path
    sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
    from base_processor import BaseProcessor

try:
    from utils.path_utils import scan_files, SourceNotHandled
except ImportError:
    import sys
    from os import path
    sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
    from utils.path_utils import scan_files, SourceNotHandled

from queue import Empty

logger = logging.getLogger(__name__)

class DICOMProcessor(BaseProcessor):
    """This class will perform serveral operations:
            process an acceptable uri
            scan a uri and catalog found items there
            fetch an item from a uri
            upload an item to a uri
    """

    def __init__(self, settings: dict = None):
        """"""
        super().__init__(settings=settings)
        self._version = "0.0.1"
        self._name = f"{self.__class__.__name__.lower()} {self._version}"
        self._semiphore = f"DONE: {self._name}"

        if not settings:
            logger.debug("Loading default settings")
            self.settings = DICOMParser.avail_config()

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
                    "filter": [".dcm"],

                }
            ],
            "uri_metadata": ["zipfile"],
            "threads": {
                "count": 1,
                "stop": True, # tells the system to stop when the in queue is empty
                "timeout": 2
            }
        }

    @staticmethod
    def default_anon() -> dict:
        """return defaults"""
        return {
            "PatientID":        "seq",          # (0010,0020)
            "PatientName":      "name",
            "ReviewerName":     "name",         # (300E,0008)
            "PatientBirthDate": "date",         # (0010,0030)
        }

    @staticmethod
    def default_alias() -> dict:
        """return defaults"""
        return {
            "*PatientID": "*PatientName"
        }

    @staticmethod
    def default_groups() -> list:
        """return defaults"""
        return ['PatientID',
            'Modality',
            'BodyPartExamined',
            'PhotometricInterpretation',
            'StudyInstanceUID',
            'SeriesInstanceUID']

    @staticmethod
    def default_metadata() -> list:
        """return defaults"""
        return ['PatientAge',
            'PatientComments',
            'PatientID',
            'PatientName',
            'PatientOrientation',
            'PatientPosition',
            'PatientSex',
            'PatientWeight',
            'ProtocolName',
            'ApprovalStatus',
            'ProtocolName',
            'ImageType',
            'ImageOrientationPatient',
            'ImagePositionPatient',
            'InstanceNumber',
            'SeriesInstanceUID',
            'SeriesDescription',
            'PixelSpacing',
            'SliceThickness',
            'SliceLocation',
            'Columns', 'Rows',
            'RescaleIntercept',
            'RescaleSlope'
        ]

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
                dcm_data = zf.read(q_item.get("uri"))
                bytes_io = io.BytesIO(dcm_data)

                _dcmobj = DICOMParser(bytes_io=bytes_io)
            else:
                _dcmobj = DICOMParser(uri=_uri)

            # load the
            _dcmobj.set_anonimizer(anonimizer=self._anon)
            _dcmobj.set_group_tags(tags=self._grp_tags)
            _dcmobj.set_metadata_tags(tags=self._md_tags)
            _dcmmd = _dcmobj.parser()
            _dcmobj.close()

            # process the tags and return...
            _md = {}
            for _mdk, _mdv in _dcmmd.get("grouping",{}).items():
                _md[_mdk] = _mdv if _mdv  else "<missing>"

            _vmd = {}
            for _vmdk, _vmdv in _dcmmd.get("metadata",{}).items():
                _vmd[_vmdk] = _vmdv

            _data = {
                "processorid": self.processorid,
                "uri id": q_item.get("uriid"),
                "uri_type": q_item.get("uri_type"),
                "uri": q_item.get("uri"),
                "metadata": _md,
                "versions": {
                    "__latest__": True,
                    "versionmd" : _vmd
                }
            }
            logger.debug("O Data: %s", _data)
            self.output.put(_data)

    def collection(self) -> None:
        """will run the queue and will build out a structure of group items
        uses the group tags
            [group]
                [...group]
                    [uris]
                    [metadata]
        """
        t_settings = self.settings.get("threads",{})
        self.input.put(self.semiphore)

        while self.input:
            q_item = self.input.get(timeout=t_settings.get("timeout")) if self.input else None
            if q_item == self.semiphore:
                break

            # if the user wants to kill the queue if there are not entries...
            # requires timeout set, otherwise the queue get blocks...
            if not q_item and self.settings.get("threads",{}).get("stop"):
                break


    def consolidate(self) -> None:
        """This will process the items in the queue which are grouped items
            [group]
                [...group]
                    [uris]
                    [metadata]
        """
        pass
