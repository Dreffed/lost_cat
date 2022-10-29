
"""A test case for the path utils module"""
import logging
import os
import unittest
from lost_cat.parsers.dicom_parser import DICOMParser

logger = logging.getLogger(__name__)

class TestLostCat(unittest.TestCase):
    """A container class for the build path modeule test cases"""

    @classmethod
    def setUpClass(self):
        """ Set up for Trie Unit Tests..."""
        self.tags = {
            "alias":    {"creationDate": "created", "modDate": "modified"},
            "groups":   ['Modality', 'BodyPartExamined', 'PhotometricInterpretation', 'PatientID',
                            'StudyInstanceUID', 'SeriesInstanceUID'],
            "metadata":   ['PatientAge', 'PatientComments', 'PatientID', 'PatientName', 'PatientOrientation',
                        'PatientPosition', 'PatientSex', 'PatientWeight', 'ProtocolName', 'ApprovalStatus',
                        'ProtocolName', 'ImageType', 'ImageOrientationPatient', 'ImagePositionPatient',
                        'InstanceNumber', 'SeriesInstanceUID', 'PixelSpacing', 'SliceThickness',
                        'SliceLocation', 'Columns', 'Rows', 'RescaleIntercept', 'RescaleSlope'] ,
        }


    @classmethod
    def tearDownClass(self):
        """ Tear down for Trie Unit Tests"""

    def test_fileobj(self):
        """Test the loading of a file object"""
        _tag_labels = ["alias", "groups", "metadata"]

        _uri = os.path.abspath(r"tests\data\test.dcm")
        assert os.path.exists(_uri)

        obj = DICOMParser(uri=_uri)
        print("Obj: ", obj)
        assert obj

        avail_config = obj.avail_config()
        for _source in avail_config.get("source",{}):
            print("\tsource: ", _source)
            assert ".dcm" in _source.get("values",[])

        avail_func = obj.avail_functions()
        assert "parser" in avail_func

        for _tn in _tag_labels:
            print("\ttags: ", _tn)
            assert f"tags_{_tn}" in avail_func
            print("\t==> ", _tn)
            if _fn := avail_func.get(f"tags_{_tn}"):
                _fn(tags=self.tags.get(_tn))
            else:
                print("\t ERROR: missing ", _tn)

        assert len(self.tags.get("alias",[])) == len(obj._alias_tags)
        assert len(self.tags.get("groups",[])) == len(obj._groups_tags)
        assert len(self.tags.get("metadata",[])) == len(obj._metadata_tags)

        data = avail_func.get("parser")()
        print("\tParser: ", data)

        obj.close()



