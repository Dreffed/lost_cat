"""A mnodule for the Phrase Tool code and class"""
import logging
import re

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

    def __init__(self, phrase: str) -> None:
        self._phrase = phrase

    def __str__(self):
        return f"{self.name} {self.version} <{self._phrase}>"

    def get_metadata(self, phrase: str = None) -> dict:
        """This will return a profile of the file path and name

        Parameters
        ----------

        Returns
        -------
        None
        """
        if not phrase:
            phrase = self._phrase

        positions = {}
        p = {}
        for k,v in self._regexes.items():
            for m in v.finditer(phrase):
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
                    phrase = "{}{}{}".format(phrase[:s], k[0]*l, phrase[e:])
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
            "expand": phrase
        }

    def get_parts(self, phrase: str = None) -> dict:
        """Uses the hard code parser to break down the phrase"""
        if not phrase:
            phrase = self._phrase

        _rows = []
        _transtr = []
        _shrtstr = []

        block = []
        state = None
        start = 0
        count = 0

        for idx, c in enumerate(phrase):
            if c.isupper():
                _newstate = "u"
            elif c.isalpha():
                _newstate = "l"
            elif c.isdigit():
                _newstate = "d"
            elif c.isspace():
                _newstate = "s"

            elif c in "(){}[]<>":
                _newstate = "b"
            elif c.isprintable():
                _newstate = "p"
            else:
                _newstate = "?"

            # process and update data...
            if _newstate == state or (_newstate =="l" and state=="t"):
                count += 1
                block.append(c)

            elif state == "u" and _newstate == "l":
                # deteect uppercased phrases...
                if len(block) > 1:
                    _transtr.append(f"{state}{count}")
                    _shrtstr.append(state)
                    _rows.append({
                        "type": state,
                        "start": start,
                        "end": idx-2,
                        "block": "".join(block[:-1])
                    })
                    count = 1
                    block = [block[-1]]

                state = "t"
                count += 1
                block.append(c)

            else:
                if state:
                    _transtr.append(f"{state}{count}")
                    _shrtstr.append(state)
                if block:
                    _rows.append({
                        "type": state,
                        "start": start,
                        "end": idx-1,
                        "block": "".join(block)
                    })

                count = 1
                state = _newstate
                start = idx
                block = [c]

        _transtr.append(f"{state}{count}")
        _shrtstr.append(state)

        # handle final state:
        _rows.append({
            "type": state,
            "start": start,
            "end": idx,
            "block": "".join(block)
        })

        return {
            "profile": "".join(_transtr),
            "short": "".join(_shrtstr).replace("s","").replace("p","").replace("?",""),
            "blocks": _rows
            }
