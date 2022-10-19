"""this will scan a file system and return the file details"""
import logging
import multiprocessing as mp
import os
import re
import threading as td
from queue import Empty
from socket import gethostname
from urllib.parse import urljoin, urlparse

from azure.storage.blob import (BlobClient, BlobServiceClient, ContainerClient,
                                __version__)
from lost_cat.processors.base_processor import (BaseProcessor, InvalidURIGiven,
                                                UnableToLoadProcessor)
from lost_cat.utils.path_utils import (SourceDoesNotExist, SourceNotHandled,
                                       build_path, get_file_metadata,
                                       get_filename, scan_files)

logger = logging.getLogger(__name__)

class AzureStorageProcessor(BaseProcessor):
    """This class will perform serveral operations:
            process an acceptable uri
            scan a uri and catalog found items there
            fetch an item from a uri
            upload an item to a uri
    """

    def __init__(self, settings: dict = None):
        """"""
        super().__init__(settings=settings)
        self._version = "0.0.2"
        self._name = f"{self.__class__.__name__.lower()} {self._version}"
        self._semiphore = f"DONE: {self._name}"

        if not settings:
            logger.debug("Loading default settings")
            self.settings = AzureStorageProcessor.avail_config()

        logger.debug("Name: %s", self._name)
        logger.debug("Semiphore: %s", self._semiphore)
        logger.debug("Settings: %s", self.settings)

        logger.info("Azure Blob Storage v%s", __version__)
        connect_str = os.environ.get(self.settings.get("connvar"))
        if not connect_str:
            logger.error("Unable to fetch connection string! Missing Connvar and envar")
            UnableToLoadProcessor()

        self._bsclient = BlobServiceClient.from_connection_string(connect_str)
        self._bsurl = self._bsclient.url
        self._bsacctname = self._bsclient.account_name

    def avail_functions(self) -> dict:
        """Returns a dict prointing to the available functions"""
        return {
            #"build": self.build_path,
            "scanner": self.scan,
            #"fetch": self.fetch,
            "upload": self.upload,
        }

    @staticmethod
    def avail_config() -> dict:
        """returns default configuration details about the class"""
        return {
            "connvar": "AZURE_STORAGE_CONNSTTR",
            "options":{
                "splitfolders": True,
                "splitextension": True,
                "stats": True,
            },
            "uritypes": [
                "AzureStorage", "AzureStorage.node", "AzureStorage.blob"
            ],
            "filters":[],
            "threads": {
                "count": 1,
                "stop": True, # tells the system to stop when the in queue is empty
                "timeout": 2
            }
        }

    def metadata(self) -> dict:
        """ Returne the properties of the root object"""
        _data = {
            "uri" :     self._bsurl,
            "account":  self._bsacctname,
            "settings": self.settings,
        }

        return _data

    def scan(self):
        """scan the file system use multprocess to
        scan each item in the queue"""
        use_threads = self.settings.get("threads",{}).get("count",5)

        for t_idx in range(use_threads):
            logger.info("Thread: %s",t_idx)
            scan_q = td.Thread(target=self.scan_fs)
            scan_q.start()
            scan_q.join()

    def scan_fs(self):
        """A file scanner function, quick and dirty"""
        t_settings = self.settings.get("threads",{})

        while self.input:
            try:
                q_item = self.input.get(timeout=t_settings.get("timeout")) if self.input else None
                if q_item == self.semiphore:
                    break

                # if the user wants to kill the queue if there are not entries...
                # requires timeout set, otherwise the queue get blocks...
                if not q_item and self.settings.get("threads",{}).get("stop"):
                    break

                uri = q_item
                uriid = -1

                if isinstance(q_item, dict):
                    uri = q_item.get("uri")
                    uriid = q_item.get("uriid")

                _urlparts = urlparse(uri)

                # run the scan of the URL
                _con_client = self._bsclient.get_container_client(uri)

                # see what is in the container...
                _blob_list = _con_client.list_blobs()
                for _blob in _blob_list:
                    _hostname = "{}::{}".format(self.settings.get("connvar"), _blob.container)
                    _uri = "{}{}/{}".format(self._bsurl, _blob.container, _blob.name)
                    if _blob.size > 0:
                        _, _ext = os.path.splitext(_blob.name)
                        _type = ".blob"
                    else:
                        _ext = ''
                        _type = ".node"

                    _data =  {
                        "domain": self._bsurl,

                        "processorid": self.processorid,
                        "uriid": uriid,
                        "uri_type": f"AzureStorage{_type}",
                        "uri": _uri,
                        "deleted": _blob.deleted_time,
                        "metadata": {
                            "ext": _ext,
                            "created": _blob.creation_time,
                            "name": _blob.name,
                            "container": _blob.container,
                            "host": self._bsurl,
                        },
                        "versions": {
                            "modified": _blob.last_modified,
                            "size": _blob.size,
                            "tags": _blob.tags,
                            "etag":	_blob.etag,
                            "metadata":	_blob.metadata,
                        }
                    }

                    self.output.put(_data)

            except Empty:
                break

    def upload(self, destination:str, source: str = None, data:bytes = None):
        """Will upload the data to the given url
        uri will include the account, container, and path"""
        (scheme, netloc, urlpath, params, query, fragment) = urlparse(destination)
        (bsscheme, bsnetloc, bspath, bsparams, bsquery, bsfragment) = urlparse(self._bsurl)

        if netloc != bsnetloc:
            # wrong acct given
            logger.error("Incorrect Account: Given: %s, expected: %s", bsnetloc, netloc)
            raise InvalidURIGiven()

        _ppaths = urlpath.split("/")
        logger.info("Paths:     %s",_ppaths)
        _container = _ppaths[1]
        logger.info("Container: %s", _container)

        _path = "/".join(_ppaths[2:]) if len(_ppaths) > 2 else None
        logger.info("Path:      %s", _path)

        _bclient = self._bsclient.get_blob_client(container=_container, blob=_path)
        if data:
            _bclient.upload_blob(data)
        elif source and os.path.exists(source):
            with open(source, "rb") as data:
                _bclient.upload_blob(data)
