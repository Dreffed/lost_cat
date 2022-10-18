"""A test case for the phrase tool module"""
import logging
import sys
import unittest

from lost_cat.utils.phrase_utils import PhraseTool

logger = logging.getLogger(__name__)

# class PhraseTool:
#   __init__
#   get_metadata
class TestPhraseTool(unittest.TestCase):
    """A container class for the phrase tool modeule test cases"""
    """        self._phrases = [
            '1.4ProtectionOfPrivacy-InformationIncidents(PrivacyBreaches)',
            'DS1 12345',
            'DS9 98765',
            'AN12 1234567',
            'Accept Form 20220415',
            '564218 - Undertaking - Anytown Road',
            'Smalltoen Cleft - X5623771',
            "C:\\users\\user\\files\\BLUE_CARD_VISA_CARD_1504_Oct_25-2021.pdf"
        ]
    """

    def test_pt_text_blob(self):
        """This will do a simple test of the tool"""
        phrase = 'ProtectionOfPrivacyInformationIncidents(PrivacyBreaches)1234567'
        pr_obj = PhraseTool(in_phrase=phrase)

        result = pr_obj.get_metadata()

        self.assertIsInstance(result.get("parts"), list, "parts is not a list")

        self.assertIsInstance(result.get("short"), str, "short is not a string")
        self.assertIsInstance(result.get("profile"), str, "profile is not a string")
        self.assertIsInstance(result.get("expand"), str, "expand is not a string")

        pr_len = len(result.get("parts",[]))

        # there shouldbe 10 parth to this phrase
        self.assertEqual(pr_len, 10)
        self.assertEqual(result.get("parts",[])[0].get("value"), "Protection", "First Word is not discovered")


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    unittest.main()
