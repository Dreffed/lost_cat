"""A module to mange the parseing of sets of lines
    into a table, based in field detection """
import logging
import re

logger = logging.getLogger(__name__)

def get_dicomreportfields():
    """ Returns the template for the DICOM Reports"""
    return {
            "age" :{
                "match": ["age"],
            },
            "reportdate" :{
                "match": ["date", "report date"],
            },
            "studydate" :{
                "match": ["study date"],
            },
            "patientsex" :{
                "match": ["sex", "gender"],
            },
            "patientid" :{
                "match": ["patient id"],
            },
            "patientname" :{
                "match": ["patient name"],
            },
            "referral" :{
                "match": ["ref doctor", "ref. by"],
            },
            "notice" :{
                "regex": ["^(?P<phrase>this report is not valid.*$)"],
                "groups": {"phrase"},
                "fstring": "{phrase}",
            },
            "scan" :{
                "regex": ["(?P<phrase>^.*scan of brain.*$)"],
                "groups": {"phrase"},
                "fstring": "{phrase}",
            },
            "impression" :{
                "regex": ["^impression:(?P<phrase>.*)$"],
                "groups": {"phrase"},
                "fstring": "{phrase}",
            },
            "observations" :{
                "regex": ["^observations:(?P<phrase>.*)$"],
                "groups": {"phrase"},
                "fstring": "{phrase}",
            },
            "protocol" :{
                "regex": ["^protocol:(?P<phrase>.*)$"],
                "groups": {"phrase"},
                "fstring": "{phrase}",
            },
            "disclaimer" :{
                "regex": ["^disclaimer:(?P<phrase>.*)$"],
                "groups": {"phrase"},
                "fstring": "{phrase}",
            },
            "advice" :{
                "regex": ["^[advice|adv][: ]+(?P<phrase>.*)$"],
                "groups": {"phrase"},
                "fstring": "{phrase}",
            },
            "findings" :{
                "regex": ["^(?P<phrase>.* findings are .*)$"],
                "groups": {"phrase"},
                "fstring": "{phrase}",
            },
    }

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
                break

            for _idx, _restr in enumerate(_fd.get("regex", [])):
                if f"{_fn}:{_idx:3}" in _compiled:
                    _rg = _compiled.get(f"{_fn}:{_idx:3}")
                else:
                    _rg = re.compile(_restr, re.IGNORECASE)
                    _compiled[f"{_fn}:{_idx:3}"] = _rg

                if _m := _rg.match(_l):
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
                break

        if _fld_name and not _continue:
            _fld_lines.append(_l)

    if _fld_name:
        _data[_fld_name] = "\n".join(_fld_lines)

    return _data

if __name__ == "__main__":
    _lines =  ['Patient Name', 'NEERAJ',
        'Patient ID', '22100320',
        'Age', '034Y',
        'Sex', 'F',
        'Ref. By', 'DR PUSHPENDER SINGH',
        'Study date', '3/10/2022 9:36:29 PM',
        'Report Date', '3/10/2022 10:55:46 PM',
        'CT SCAN OF BRAIN (Plain study)',
        'Above study was performed on MDCT unit and appropriate hard copy documentation done',
        'OBSERVATIONS:', 'Cerebral parenchyma appears normal. No evidence of focal lesion seen.',
        'Ventricular system and cisterns are within normal limit.',
        'There is no shift of midline structures.',
        'Cerebellum and brainstem appear normal.',
        'No evidence of any intra axial or extra axial hemorrhage is seen.',
        'Bony skull vault appears normal.',
        'Visualized orbits are normal.',
        'Visualized para nasal sinuses show no gross lesion / soft tissue mucosal thickening.',
        'Visualized mastoid appears normal and no soft tissue mucosal thickening is seen.',
        'IMPRESSION: CT findings are suggestive of:',
        'No significant abnormality seen in brain parenchyma.', '•',
        'This Report is not valid for any medico legal purpose. This report is prepared on the basis of digital',
        'DICOM images transmitted via internet without identification of patient, not on the films or plates',
        'provided to the patient.',
        'Disclaimer: - It is an online interpretation of medical imaging based on clinical data. All modern',
        'machines/procedures have their own limitation. If there is any clinical discrepancy, this investigation may be',
        'repeated or reassessed by other tests. Patient’s identification in online reporting is not established, so in no',
        'way can this report be utilized for any medico legal purpose. In case of any discrepancy due to typing error',
        'or machinery error please get it rectified immediately*.',
        'For Any Query please call us at +91-9269101212, +91-9261001212']

    _table = tablify(lines=_lines, fields=get_dicomreportfields())

    for _k, _v in _table.items():
        print(f"\t{_k}\t=> {_v}")
