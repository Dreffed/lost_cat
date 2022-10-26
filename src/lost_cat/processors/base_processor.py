"""the base class for the scanners"""
import logging
import multiprocessing as mp
from time import sleep, time

from lost_cat.utils.tag_anon import TagAnon

logger = logging.getLogger(__name__)

class UnableToLoadProcessor(Exception):
    """Exception to handle the class load failed! """

class InvalidURIGiven(Exception):
    """Exception to raise the URL is incorrect """

class BaseProcessor():
    """This will create the core functions
    """
    def __init__(self, settings: dict = None):
        """sets up the class and attaches the queues"""
        self.settings = settings
        self.input = None
        self.output = None
        self.processorid = -1
        self._version = "0.0.1"
        self._name = f"{self.__class__.__name__.lower()} {self._version}"
        self._semiphore = f"DONE: {self._name}"

        # init the tags lists
        self._anonobj = None
        self._groups_tags = []
        self._metadata_tags = []
        self._alias_tags = {}

    @property
    def name(self):
        """the freindly name of the class """
        return self._name

    @property
    def version(self):
        """the version of the class """
        return self._version

    @property
    def semiphore(self):
        """the semiphore to check for end the queue reads """
        return self._semiphore

    def set_anonimizer(self, anonimizer: TagAnon) -> None:
        """Allows for the metadata tags to be anonymized"""
        self._anonobj = anonimizer

    def set_alias_tags(self, tags: dict) -> None:
        """Allows for the metadata tags to be anonymized
            <tag to rename>: <tag new name>
        '"""
        self._alias_tags = tags

    def set_groups_tags(self, tags: list) -> None:
        """Sets the metadata tags to be used for grouping
        The grouping is used to organize the structure"""
        self._groups_tags = tags

    def set_metadata_tags(self, tags: list):
        """Sets the tags to use for general metadata"""
        self._metadata_tags = tags

    def in_queue(self, in_queue: mp.Queue):
        """the queue to use for input """
        self.input = in_queue

    def out_queue(self, out_queue: mp.Queue):
        """the queue to use for output """
        self.output = out_queue

    def metadata(self) -> dict:
        """Returns the metadata about the current root
        device """
        return {"error": "not implemented"}

    def scan(self):
        """starts the scanner operation"""

    def fetch(self, uri: str) -> object:
        """will return a file, stream, or binary"""

    def upload(self, data: object, uri:str = None) -> bool:
        """will upload the data to the provided uri, if not uri
        provided will write into the current location"""
        return False

    def close(self, force: bool = False, block: bool = False, timeout: int = -1):
        """will close the objects """
        logger.debug("%s %s %s", force, block, timeout)
        if self.input:
            # check for force and / or block
            if force:
                self.input = None
            else:
                start_time = time()
                self.input.put(self.semiphore)
                while True:
                    sleep(10)
                    if time() - start_time > timeout:
                        logger.debug("Timeout hit %s %s", timeout, time() - start_time)
                        break

            self.input = None

    def build_path(self, uri: str, hint: str = "n/a") -> dict:
        """will accept a uri and will turn it to a dictionary
        for later use.
        and return a dictionary
            "type": str
            "uri": uri
        """

        src = {
            "uri": uri,
            "type": f"CLASS:{self.__class__.__name__}",
            "domain": "<base class>"
        }

        return src

    def avail_functions(self) -> dict:
        """Returns a dict prointing to the available functions"""
        return {
            "sources": self.in_queue,
            "uris": self.out_queue,
            #"scan": self.scan,

            #"fetch": self.fetch,
            #"upload": self.upload,

            "anonimizer": self.set_anonimizer,
            "tags_alias": self.set_alias_tags,
            "tags_metadata": self.set_metadata_tags,
            "tags_groups": self.set_groups_tags,
        }

    @staticmethod
    def avail_config() -> dict:
        """returns configuration details about the class
            "options":          dict    specific to the called class
            "uritypes":         array   uri_types to filter sources
            "<functionname>":   array   dict
                                        provide a simplified query for the
                                        generation of the funcname that
                                        is being called

                    "table"             str     the table to search
                                        must relate to a URI table
                    "field"             str     the fields to check
                    "select"            str     the value to match as the field
                    "filter"            list    values to filter the value field
            "uri_metadata":     list    a list of fields to send
                                        in the processor class queue

            "version_metadata": list    a list of fields to send
                                        in the processor class queue
            "threads":
                "count":        int     how many threads to create
                "stop":         bool    force stop on close
                "timeout":      int     timeout in seconds
        """
        return {}
