"""A test case for the path utils module"""
import logging
import os
import random
import sys
import unittest
from lost_cat.utils.tag_anon import TagAnon

logger = logging.getLogger(__name__)

class TestUtilsTagAnon(unittest.TestCase):
    """A container class for the build path modeule test cases"""

    def test_coretags(self):
        """ tests for  core annoymizer"""
        tags_anon = {
                    "PatientID":        "seq",          # (0010,0020)
                    "PatientName":      "name",
                    "ReviewerName":     "name",         # (300E,0008)
                    "PatientBirthDate": "date",         # (0010,0030)
                }

        test_tags = {
            "PatientID": [999, 888, 777, 666, 555, 444],
            "PatientName": ['alice', 'bob', 'chris', 'david', 'eric', 'fred'],
            "ReviewerName": ['zeebeedee', 'yazoo','xavier','william',' una'],
            "PatientBirthDate": ['19050512', '20221231', '20000101', '14000505']
        }

        obj =TagAnon(tags=tags_anon)

        for idx in range(1, 50):
            tag = random.choice(list(tags_anon.keys()))
            value = random.choice(test_tags.get(tag,[]))
            res = obj.get_anon(tag=tag, value=value)
            print("{:20}|\t{:>15}\t{:>15}".format(tag, value, res))

        obj = None

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    unittest.main()
