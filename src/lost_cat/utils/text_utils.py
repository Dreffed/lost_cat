"""A module to mange the parseing of sets of lines
    into a table, based in field detection """
import logging
import nltk
import re

logger = logging.getLogger(__name__)

nltk.download([
        "names",
        "stopwords",
        "averaged_perceptron_tagger",
        "vader_lexicon",
        "punkt",
    ])

def clean_text(text: str, operations: dict = None) -> list:
    """This will clean a text block and return
    a list of phrases"""
    _data = []

    if operations:
        for _opk, _opv in operations.items():
            if _opv.get("stage","") == "pre":
                if _reg := _opv.get("regex"):
                    text = re.sub(pattern=_reg, repl=_opv.get("replace",""), string=text, flags=re.IGNORECASE)
                else:
                    _fnd = _opv.get("find", "")
                    text = text.replace(_fnd, _opv.get("replace",""))

    for _tt in nltk.sent_tokenize(text):
        if operations:
            for _opk, _opv in operations.items():
                if _opv.get("stage","") == "sentence":
                    if _reg := _opv.get("regex"):
                        _tt = re.sub(pattern=_reg, repl=_opv.get("replace",""), string=_tt, flags=re.IGNORECASE)
                    else:
                        _fnd = _opv.get("find", "")
                        _tt = _tt.replace(_fnd, _opv.get("replace",""))

        _data.append(_tt.strip())
    return _data

def tablify(lines: list, fields: dict) -> dict:
    """ will take the collection of key words / phrases
    and return the text as a key value doctionary
        fields:
            "fieldname" :{
                match:      [<array of string to match>]
                regex:      [<array of regex to get groups]
                groups:     [list of group name in regex]
                fstring:    format string to match on,
                            use "<fstring>".format(**<groups>)
                extract:    add this line as a field, but keep the current
                            field in play
            }
    """
    _data = {}
    _compiled = {}

    _fld_name = None
    _fld_lines = []

    for _l in lines:
        _continue = False
        for _fn, _fd in fields.items():
            for _mt in _fd.get("match", []):
                if _mt == _l.lower():
                    if _fld_name:
                        _data[_fld_name] = "\n".join(_fld_lines)
                    _fld_name = _fn
                    _fld_lines = []
                    _continue = True
                    break

            if _continue:
                logger.debug("String Match: %s", _l)
                break

            for _idx, _restr in enumerate(_fd.get("regex", [])):
                if f"{_fn}:{_idx:3}" in _compiled:
                    _rg = _compiled.get(f"{_fn}:{_idx:3}")
                else:
                    _rg = re.compile(_restr, re.IGNORECASE)
                    _compiled[f"{_fn}:{_idx:3}"] = _rg

                if _m := _rg.match(_l):
                    if _fd.get("extract"):
                        _grps = {}
                        for _g in _fd.get("groups",[]):
                            _grps[_g] = _m.group(_g)
                        if _grps:
                            _data[_fn] = _fd.get("fstring","").format(**_grps)
                        else:
                            _data[_fn] = _l
                        _continue = True
                        break

                    if _fld_name:
                        _data[_fld_name] = "\n".join(_fld_lines)
                    _continue = True
                    _fld_name = _fn
                    _fld_lines = []

                    _grps = {}
                    for _g in _fd.get("groups",[]):
                        _grps[_g] = _m.group(_g)
                    if _grps:
                        _fld_lines.append(_fd.get("fstring","").format(**_grps))

            if _continue:
                logger.debug("Regex Match: %s", _l)
                break

        if _fld_name and not _continue:
            logger.debug("field: %s\tline: %s", _fld_name, _l)
            _fld_lines.append(_l)

    if _fld_name:
        logger.debug("closing: %s", _fld_name)
        _data[_fld_name] = "\n".join(_fld_lines)

    return _data
