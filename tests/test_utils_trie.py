"""A test case for the path utils module"""
import logging
import os
import sys
import unittest
from lost_cat.utils.trie_utils import WordNode, TrieWord, process_sentence

logger = logging.getLogger(__name__)

class TestUtilsModule(unittest.TestCase):
    """A container class for the build path modeule test cases"""

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        self.phrases = [
            "one", "one two", "one two three", "one two three four",
            "two four", "two five", "six", "seven eight",
        ]

        self.sentences = [
            "one two seven eight",
            "one one two seven",
            "two six seven eight",
            "four three two one",
            "one two three four five",
            "seven five three four",
        ]

        self.markedup = [
            "<b>one two<b> <b>seven eight<b>",
            "<b>one<b> <b>one two<b> seven",
            "two <b>six<b> <b>seven eight<b>",
            "four three two <b>one<b>",
            "<b>one two three four<b> five",
            "seven five three four",
        ]

    @classmethod
    def setUpClass(self):
        """ Set up for Trie Unit Tests..."""
        self.obj = TrieWord()

    @classmethod
    def tearDownClass(self):
        """ Tear down for Trie Unit Tests"""
        self.obj = None

    def test_trieslf(self):
        """ Test the loader and phrases"""
        for p in self.phrases:
            self.obj.insert(phrase = p)

        data = self.obj.export()
        logger.debug(data)

    def test_sentence(self):
        """ Test the sentence parser and replacement"""
        for p in self.phrases:
            self.obj.insert(phrase = p)

        for idx, sentence in enumerate(self.sentences):
            tags = process_sentence(sentence=sentence, roottrie=self.obj.root)
            sentence = tags.get("sentence")

            logger.debug(f"IN:\t%s", sentence)
            markup = []
            for t in tags.get("tagged",[]):
                if word := t.get("word"):
                    markup.append(word)
                elif phrase := t.get("phrase"):
                    markup.append(f"<b>{phrase}<b>")

            logger.debug(f"=>\t%s", " ".join(markup))
            markedup = " ".join(markup)

            assert markedup.replace("<b>","") == sentence
            assert markedup == self.markedup[idx]

    def test_structure(self):
        """ unit test the trie sturcture and nest"""
        for p in self.phrases:
            self.obj.insert(phrase = p)

        node = self.obj.root
        for w in ["one", "two"]:
            logger.debug(w)
            assert w in node.children
            node = node.children[w]
        logger.debug("Word: %s [%s]", node.word, node.is_end)
        assert node.is_end is True

        logger.debug("Test solos...")

        for w in ["one", "six"]:
            logger.debug(w)
            node = self.obj.root
            assert w in node.children
            node = node.children[w]
            logger.debug("Word: %s [%s]", node.word, node.is_end)
            assert node.is_end is True

        logger.debug("Test single in phrase...")
        node = self.obj.root
        for w in ["two", "seven"]:
            logger.debug(w)
            node = self.obj.root
            assert w in node.children
            node = node.children[w]
            logger.debug("Word: %s [%s]", node.word, node.is_end)
            assert node.is_end is False


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    unittest.main()
