"""A test case for the path utils module"""
import logging
import os
import sys
import unittest
from lost_cat.lost_cat import ClassFailedToLoad, LostCat
from lost_cat.processors.base_processor import BaseProcessor

logger = logging.getLogger(__name__)

class TestLostCat(unittest.TestCase):
    """A container class for the build path modeule test cases"""

    @classmethod
    def setUpClass(self):
        """ Set up for Trie Unit Tests..."""
        _db_path = os.path.abspath("tests/data/base.db")
        if os.path.exists(_db_path):
            # delete the file
            logger.info("Removing file %s", _db_path)
            os.remove(_db_path)

        _paths = {
            "database": f"sqlite:///{_db_path}" #
        }
        self.obj = LostCat(paths=_paths)

    @classmethod
    def tearDownClass(self):
        """ Tear down for Trie Unit Tests"""
        self.obj.close()
        self.obj = None

    def test_addprocessor_obj(self):
        """ Test the adding of a processor to lost cat"""
        self.obj.add_processor(
            label="blank label",
            base_class= BaseProcessor,
            overwrite=True,
        )

        # check the processor got added..
        for _pk, _pv in self.obj._processors.items():
            print(f"{_pk}\t{_pv}")

        assert "baseprocessor 0.0.1" in self.obj._processors
        _proc = self.obj._processors.get("baseprocessor 0.0.1", {})
        assert "uri" in _proc
        assert _proc.get("uri","") == "lost_cat.processors.base_processor.BaseProcessor"

    def test_addprocessor_path(self):
        """Will add a processor by its class path"""
        #from lost_cat.processors.filesystem_scanner.FileScanner

        self.obj.add_processor(
            module_path="lost_cat.processors.filesystem_scanner.FileScanner"
        )

        # check the processor got added..
        for _pk, _pv in self.obj._processors.items():
            print(f"{_pk}\t{_pv}")

        assert "filescanner 0.0.2" in self.obj._processors
        _proc = self.obj._processors.get("filescanner 0.0.2", {})
        assert "uri" in _proc
        assert _proc.get("uri","") == "lost_cat.processors.filesystem_scanner.FileScanner"


    def test_addsource(self):
        """ Test the addition of a source to the db"""
        _params = {
            "processor":    "baseprocessor 0.0.1",
            "uri":          os.path.abspath("logs"),
            "isroot":       True,
            "overwrite":    True,
        }

        _src = self.obj.add_source(**_params)
        print("Source:", _src)

        assert _src.get("type") == "CLASS:BaseProcessor"
        assert _src.get("processorname","").startswith("baseprocessor ")

        # check that we get the same params for a readd
        _params["overwrite"] = False
        _src_new = self.obj.add_source(**_params)

        print("check same values...")
        for _sk, _sv in _src.items():
            print("\t{}: {} => {}".format(_sk, _sv, _src_new.get(_sk)))
            assert _sv == _src_new.get(_sk)

    def test_addinvalidproc(self):
        """ Test for missing processor"""
        _params = {
            "processor":    "dummyprocessor 0.0.1",
            "uri":          os.path.abspath("tests/dummy"),
            "isroot":       True,
            "overwrite":    False,
        }

        self.assertRaises(ClassFailedToLoad, self.obj.add_source, **_params)

    def test_loadsource(self):
        """ Will test the db sources can be loaded"""
        self.obj._sources = None
        self.obj.load_db_sources()

        for _sk, _sv in self.obj._sources.items():
            print(f"Sources [{_sk}]")
            for _uk, _uv in _sv.get("uris", {}).items():
                print(f"\t{_uk} => {_uv}")

            for _pp in _sv.get("processors", []):
                print(f"Proc: {_pp}")

        assert "CLASS:BaseProcessor" in self.obj._sources

    def test_simplescan(self):
        """run a simple test of the system"""
        # add a source for FileScanner
        self.obj.add_processor(
            module_path="lost_cat.processors.filesystem_scanner.FileScanner"
        )
        _uri = os.path.abspath(r"tests\data")

        self.obj.add_source(processor = "filescanner 0.0.2", uri = _uri, isroot = True, overwrite = True)

        self.obj.load_db_sources()

        _resp = self.obj.catalog_artifacts()
        print(f"Catalog: {_resp}")


