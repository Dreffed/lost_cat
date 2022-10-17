"""A test case for the path utils module"""
import os
import unittest
import logging
from lost_cat.utils.path_utils import build_path

logger = logging.getLogger(__name__)

# def build_path(uri: str) -> dict:
# def get_filename(file_dict: dict) -> str:
# def get_file_metadata(uri: str, options: dict = None) -> dict:
# def make_hash(uri: str, buff_size: int = 65536) -> dict:
# def scan_files(uri: str, options: dict = None) -> dict:
# def is_include(file_dict: dict, options: dict = None) -> bool:
# def scan_zip(uri: str) -> dict:
# def scan_tar(uri: str) -> dict:
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


if __name__ == '__main__':
    unittest.main()
