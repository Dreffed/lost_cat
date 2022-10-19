"""This is a class module for the anonimizer"""
import logging
import random
import string
import uuid
from datetime import date, datetime

logger = logging.getLogger(__name__)

# create unique id
class TagAnon():
    """A class to handle the anonimizing and past tags and values."""
    def __init__(self, tags: dict) -> None:
        """Code with 4 base functions:
            name - returns a ([a-z0-9]{3})-([A-Z0-9]{9}) string
            UUID - returns a GUID
            Date - Will return the <YYYY>-01-01
            Seq  - Will return an incremental number
        """
        self.func_map = {
            "name": self._get_uname,
            "uuid": self._get_uuid,
            "date": self._get_udate,
            "seq": self._get_useq,
        }

        self.tag_map = {}
        self.tag_lookup = {
            "__names": []
        }

        for k_tag, v_tag in tags.items():
            func = self.func_map.get(v_tag,"seq")

            # initialize the function map
            if k_tag not in self.tag_map:
                self.tag_map[k_tag] = func

            # initiialize the lookups
            if k_tag not in self.tag_lookup:
                self.tag_lookup[k_tag] = {}

    def load_cache(self, tag_lookup: dict) -> None:
        """Allows for previsously remembered lookup to be loaded,
        *********************************************************
        this cache will potentially have PII data in it and
        should only be used for a batch of imports
        *********************************************************
        """
        self.tag_lookup = tag_lookup

    def fetch_cache(self) -> dict:
        """
        return the dict of the lookups
        *********************************************************
        this cache will potentially have PII data in it and
        should only be used for a batch of imports
        *********************************************************
        The cache is a pickle file of a dict
        """
        return self.tag_lookup

    def is_pii(self, tag: str) -> bool:
        """Will check if the tag is on the PI (Anon) list"""
        return tag in self.tag_lookup

    def get_anon(self, tag: str, value: str) -> str:
        """For the past tag and value, it will add the value to a lookup
        and return the new value.
        If the same tag|value combo is past in, it'll return the prior value
        for the lifetime of the class instance.
        The cache can be saved and loaded"""
        #self._fix_missing(tag=tag)
        if tag not in self.tag_lookup:
            return value

        new_value = self.tag_lookup.get(tag, {}).get(value)
        if not new_value:
            new_value = self.tag_map.get(tag, self._get_useq)(tag=tag, value=value)
            self.tag_lookup[tag][value] = new_value

        return new_value

    def add_tag(self, tag: str, func: str) -> None:
        """Will add a tag and the associated function to the lookup tables"""
        #  handle the missing value cases
        if tag not in self.tag_map:
            self.tag_map[tag] = self.func_map.get(func, "def")

        if tag not in self.tag_lookup:
            self.tag_lookup[tag] = {}

    def _get_uuid(self, tag: str, value:str) -> str:
        """Returns a UUID"""
        return str(uuid.uuid4())

    def _get_uname(self, tag: str, value: str) -> str:
        """Build a random string of 3-9"""
        new_value = self.get_random_string(prefix_len=3, body_len=9)
        while True:
            if new_value in self.tag_lookup.get("__names"):
                new_value = self.get_random_string(prefix_len=3, body_len=9)
                continue

            self.tag_lookup["__names"].append(new_value)
            break

        return new_value

    def _get_udate(self, tag: str, value: str) -> date:
        """Zeros the month and day to 01-01"""
        # default to 1900-01-01
        new_dob = date(1900,1,1)
        try:
            dob = datetime.strptime(value, "%Y%m%d")
            new_dob = date(dob.year, 1, 1)

        except ValueError:
            logger.error("bad date, %s -> %s, using default", tag, value)

        return new_dob.strftime("%Y%m%d")

    def _get_useq(self, tag: str, value: str) -> date:
        """Return a simple incremental ID"""
        # index as seen
        return len(self.tag_lookup.get(tag, {})) + 1
        pass

    def get_random_string(self, prefix_len: int, body_len: int) -> str:
        """Function to build a random string [prefex]-[body]"""
        # choose from all lowercase letter
        letters = string.ascii_uppercase
        numb = string.hexdigits
        str_02 = ''.join(random.choice(numb + letters + numb) for i in range(body_len))

        return "{}-{}".format(''.join(random.choice(numb) for i in range(prefix_len)), str_02)


if __name__ == "__main__":
    tags_anon = {
        #"PatientID":        "seq",          # (0010,0020)
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

    anon_obj = TagAnon(tags=tags_anon)

    for idx in range(1, 50):
        tag = random.choice(list(tags_anon.keys()))
        value = random.choice(test_tags.get(tag,[]))
        res = anon_obj.get_anon(tag=tag, value=value)
        print("{:20}|\t{:>15}\t{:>15}".format(tag, value, res))

    anon_obj = None
