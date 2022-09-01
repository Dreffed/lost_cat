"""A mnodule for the Phrase Tool code and class"""

import re
import logging

logger = logging.getLogger(__name__)

class PhraseTool:
    """
    ---
    Attributes
    ----------

    Methods
    -------

    """

    # instatitate as a class variable
    _regexes = {
        "tcase": re.compile("[A-Z][a-z]+"),
        "abbrv": re.compile("[A-Z]{2,}"),
        "ucase": re.compile("[A-Z]+"),
        "lcase": re.compile("[a-z]+"),
        "code": re.compile(r"[\u4e00-\u9fff]+"),
        "decimal": re.compile(r"\d+\.\d+"),
        "int": re.compile(r"\d+"),
        "group": re.compile(r"[()\[\]{}']+"),
        "formula": re.compile(r"[,!@#$%&+=?]+"),
        "space": re.compile(r"[\. _\-\t]+")
    }
    name = "names"
    version = "0.0.1"

    def __init__(self, in_phrase: str) -> None:
        self._phrase = in_phrase

    def __str__(self):
        return f"{self.name} {self.version} <{self._phrase}>"

    def get_metadata(self) -> dict:
        """This will return a profile of the file path and name

        Parameters
        ----------

        Returns
        -------
        None
        """
        in_phrase = self._phrase
        positions = {}
        p = {}
        for k,v in self._regexes.items():
            for m in v.finditer(in_phrase):
                l = len(m.group())
                s = m.start()
                e = m.end()
                if s not in p:
                    p[s] = {
                        "start": s,
                        "end": e,
                        "type": k,
                        "value": m.group()
                    }

                    # remove the found groups with place holders
                    in_phrase = "{}{}{}".format(in_phrase[:s], k[0]*l, in_phrase[e:])
                    if l == 1:
                        positions[s] = k[0]
                    else:
                        positions[s] = "{}{}".format(k[0],l)

        out_phrase = []
        parts = []
        for k, v in sorted(positions.items()):
            out_phrase.append(v.upper())
            parts.append(p.get(k))
        pro_phrase = "".join(out_phrase)

        return {
            "parts": parts,
            "short": re.sub('\\d','', pro_phrase),
            "profile": pro_phrase,
            "expand": in_phrase
        }

