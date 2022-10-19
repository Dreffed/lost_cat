""" Utilities to build and manage TRIEs """

import logging
import string

logger = logging.getLogger(__name__)

class WordNode():
    """ A node to store aword in the system"""
    def __init__(self, word:str, depth:int = 0) -> None:
        self.word = word
        self.counter = 0
        self.depth = depth
        self.is_end = False
        self.children = {}

    def __repr__(self) -> str:
        return f"<WordNode [{self.word}]>"

    def fetchchild(self, word: str) -> object:
        """ Will return the child object that
        matches the word"""
        return self.children.get(word)

class TrieWord():
    """ a word Trie root"""

    def __init__(self) -> None:
        """Initializes and create a root node"""
        self.root = WordNode("")

    def insert(self, phrase: str):
        """Insert a phrase, a collection of word
        and will build out the tree accordingly"""
        node = self.root
        phrase = phrase.replace("_", " ").replace("-", " ").translate(str.maketrans('', '', string.punctuation))
        words = [x for x in phrase.split()]

        for idx, word in enumerate(words):
            if not word:
                continue

            if not node:
                break

            word = word.lower().strip()

            if word in node.children:
                node = node.children.get(word)
            else:
                add_node = WordNode(word=word, depth=idx+1)
                node.children[word] = add_node
                node = add_node

        node.is_end = True
        node.counter += 1

    def export(self, node: WordNode = None, depth: int = 0, maxdepth: int = 10):
        """ Returns an indented json object"""
        if depth >= maxdepth:
            return None

        if not node:
            node = self.root

        _data = {}
        for word, childnode in node.children.items():
            _data[word] = self.export(node=childnode, depth=depth+1)

        return _data

def process_sentence(sentence: str, roottrie: TrieWord) -> dict:
    """ Will process the sentene and provide a dict of
    {
        "sentence": <imput sentence>
        "terms": list of phrases found
        "pos": list of elements in the sentence
    }
    """
    tagged = []
    phrases = []
    curr_phrase = []
    node = roottrie
    sentence = sentence.replace("_", " ").replace("-", " ").translate(str.maketrans('', '', string.punctuation))
    logger.debug("Sentence: %s", sentence)

    for idx, word in enumerate([x for x in sentence.split()]):
        tags = {}

        logger.debug("\tW:\t%s", word)
        if cnode := node.fetchchild(word.lower()):
            if len(curr_phrase) == 0:
                logger.debug("\t\t\tS =>")

            curr_phrase.append(word)
            node = cnode

        else:
            # only add the phrase if end wordm reset phrase
            if curr_phrase:
                if node.is_end:
                    logger.debug("\t\t\t<= E")
                    phrases.append(" ".join(curr_phrase))

                    tagged.append({
                        "phrase": (" ".join(curr_phrase)),
                        "start":  idx - len(curr_phrase) + 1,
                        "length": len(curr_phrase),
                    })
                else:
                    if len(curr_phrase) == 1:
                        tagged.append({
                            "word": curr_phrase[0],
                            "start":  idx,
                            "length": len(curr_phrase),
                        })

                curr_phrase = []

            logger.debug("\t\t\t<> C")
            node = roottrie

            # check that the current word
            if cnode := node.fetchchild(word.lower()):
                logger.debug("\t\t\tS =>")
                curr_phrase.append(word)
                node = cnode
            else:
                tags = {
                    "word": word,
                    "start": idx+1,
                    "length": 1,
                }

        if len(curr_phrase) == 0:
            tagged.append(tags)
        #markup = [w for d["word"] in ]

    # catch end...
    if curr_phrase:
        if node.is_end:
            phrases.append(" ".join(curr_phrase))
            tagged.append({
                "phrase": (" ".join(curr_phrase)),
                "start":  idx - len(curr_phrase) + 1 ,
                "length": len(curr_phrase),
            })
        elif len(curr_phrase) == 1:
            tagged.append({
                "word": curr_phrase[0],
                "start":  idx,
                "length": len(curr_phrase),
            })
        else:
            logger.error("Curre phrase %s in sentence %s is mislabeled!", curr_phrase, sentence)

    return {
        "sentence": sentence,
        "tagged": tagged,
        "phrases": phrases,
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    phrases = [
            "one", "one two", "one two three", "one two three four",
            "two four", "two five", "six", "seven eight",
        ]

    sentences = [
            "one two seven eight",
            "one one two eight seven nine",
            "one one two seven",
            "two six seven eight",
            "four three two one",
            "one two three four five",
            "seven five three four",
        ]

    obj = TrieWord()
    for p in phrases:
        obj.insert(phrase=p)

    for s in sentences:
        logger.info(" ")
        tags = process_sentence(sentence=s, roottrie=obj.root)
        for t in tags.get("tagged"):
            logger.info("\tT: %s", t)