"""A test case for the path utils module"""
import logging
import os
import sys
import unittest
from lost_cat.utils.path_utils import get_machine, build_path, split_folder

logger = logging.getLogger(__name__)

class TestUtilsBuildPath(unittest.TestCase):
    """A container class for the build path modeule test cases"""

    def test_build_path(self):
        """test the build path function and see it returns"""
        uri = os.path.join(os.getcwd(), *['tests', 'data'])
        logger.debug("URI: %s", uri)

        result = build_path(uri=uri)

        # check the result
        self.assertEqual(result.get("type"), "folder")

        self.assertGreater(len(result.get("folders",[])), 2, "Folders incorrect length")

    def test_get_machine(self):
        """ unit test for get machine"""
        machine = get_machine()
        logger.debug("MC: %s", machine)
        assert "platform" in machine
        assert "platform-release" in machine
        assert "platform-version" in machine

        assert "architecture" in machine

        assert "hostname" in machine
        assert "ip-address" in machine
        assert "mac-address" in machine

        assert "processor" in machine
        assert "ram" in machine

    def text_split_folder(self):
        """ unit test for split_folder"""
        uri = r"one\two\three\four\five"
        splt = split_folder(path=uri)
        logger.debug("URI: %s\n\tFldrs: %s", uri, splt)
        assert len(splt) == 5

        uri = r"\\bob\fred\sue"
        splt = split_folder(path=uri)
        logger.debug("URI: %s\n\tFldrs: %s", uri, splt)

        uri = r"d:\bob\fred\sue"
        splt = split_folder(path=uri)
        logger.debug("URI: %s\n\tFldrs: %s", uri, splt)


    def text_get_filename(self):
        """ unit test for get_filename"""

    def text_get_file_metadata(self):
        """ unit test for """

    def text_make_hash(self):
        """ unit test for """

    def text_fast_scan(self):
        """ unit test for """

    def text_scan_files(self):
        """ unit test for """


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    unittest.main()
