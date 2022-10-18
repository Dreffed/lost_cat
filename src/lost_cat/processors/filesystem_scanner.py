"""this will scan a file system and return the file details"""
import logging
import multiprocessing as mp
import os
import re
import threading as td

from lost_cat.utils.path_utils import SourceDoesNotExist, get_filename, get_file_metadata
from lost_cat.processors.base_processor import BaseProcessor
from lost_cat.utils.path_utils import scan_files, SourceNotHandled
from queue import Empty
from socket import gethostname

logger = logging.getLogger(__name__)

class FileScanner(BaseProcessor):
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
            self.settings = FileScanner.avail_config()

        logger.debug("Name: %s", self._name)
        logger.debug("Semiphore: %s", self._semiphore)
        logger.debug("Settings: %s", self.settings)

    def avail_functions(self) -> dict:
        """Returns a dict prointing to the available functions"""
        return {
            "build": self.build_path,
            "scanner": self.scan,
            #"fetch": self.fetch,
            #"upload": self.upload,
        }

    @staticmethod
    def avail_config() -> dict:
        """returns default configuration details about the class"""
        return {
            "options":{
                "splitfolders": True,
                "splitextension": True,
                "stats": True,
            },
            "uritypes": [
                "folder",
            ],
            "filters":[
                {
                    "table": "URIs",
                    "field": "root",
                    "select": True
                }
            ],
            "threads": {
                "count": 1,
                "stop": True, # tells the system to stop when the in queue is empty
                "timeout": 2
            }
        }

    def build_path(self, uri: str, hint: str = "folder") -> dict:
        """will accept a uri and will turn it to a dictionary
        for later use.
        and return a dictionary
            "type": str
            "uri": uri

            "root": str
            "folders": list
            "filename": str
            "ext": str
        """

        src = {
            "uri": uri,
            "type": None
        }

        logger.debug("Check: %s\t:%s\t:%s ", r"[\\\/\.]+", uri, re.search(r"[\\\/\.]+", uri))
        try:
            _fmd = get_file_metadata(uri=uri, options={"stats": True})
            logger.debug("File Stats %s\n\t\t%s", uri, _fmd)

        except SourceDoesNotExist:
            logger.debug("Provide uri does not exist %s", uri)
            return

        if re.search(r"[\\\/]+", uri):
            _uri = os.path.expandvars(os.path.expanduser(uri))
            _drv, _path = os.path.splitdrive(uri)

            if os.path.exists(_uri):
                if os.path.isdir(_uri):
                    src["type"] = "folder"

                elif os.path.isfile(_uri):
                    src["type"] = "file"
            else:
                src["type"] = hint

            if src["type"] == "file":
                _path, _filename = os.path.split(_path)
                _name, _ext = os.path.splitext(_filename)
                src["name"] = _name
                src["ext"] = _ext.lower()

            _folders = []
            while len(_path) > 1:
                _path, _fld = os.path.split(_path)
                if len(_fld) > 0:
                    _folders.append(_fld)

            _folders.reverse()
            src["folders"] = _folders
            src["root"] = f"{_drv}{os.sep}"
            src["domain"] = _fmd.get("domain")

        else:
            raise SourceNotHandled(uri=uri, message="provided uri could not be understood by parser!")

        return src

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
        _hostname = gethostname()

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
                if isinstance(q_item, dict):
                    uri = q_item.get("uri")

                for fs_obj in scan_files(uri=uri, options=self.settings.get("options",{})):
                    # convert to the
                    # URIs
                    #   -> Metadata
                    #   -> Versions
                    #       -> metadata
                    # {
                    #   'type': | 'root': | 'folder': | 'name': | 'ext': |
                    #   'folders': | 'accessed': | 'modified': | 'created': | 'size': | 'mode':
                    _uri = get_filename(fs_obj)
                    _data = {
                        "domain": _hostname,

                        "processorid": self.processorid,
                        "uriid": q_item.get("uriid"),
                        "uri_type": fs_obj.get("type"),
                        "uri": _uri, #fs_obj.get("uri"),
                        "metadata": {
                            "ext": fs_obj.get("ext"),
                            "created": fs_obj.get("created"),
                            "name": fs_obj.get("name"),
                        },
                        "versions": {
                            "modified": fs_obj.get("modified"),
                            "size": fs_obj.get("size"),
                            "checksum": fs_obj.get("hash", {}).get("SHA1"),
                        }
                    }
                    self.output.put(_data)

                    for zs_obj in fs_obj.get("files", []):
                        # dict :    zipfile
                        #           path
                        #           folder
                        #           name
                        #           size
                        #           ext

                        logger.debug(zs_obj)
                        _data = {
                            "domain": _hostname,
                            "processorid": self.processorid,
                            "uri_type": "zipfile",
                            "uri": zs_obj.get("path"),
                            "metadata": {
                                "ext": zs_obj.get("ext"),
                                # <TODO: get the create / modified dates from the zipfile itself>
                                "created": fs_obj.get("created"),
                                "name": zs_obj.get("name"),
                                "zipfile": _uri,
                            },
                            "versions": {
                                # <TODO: get the create / modified dates from the zipfile itself>
                                "modified": fs_obj.get("modified"),
                                "size": zs_obj.get("size")
                            }
                        }
                        self.output.put(_data)

            except Empty:
                break

if __name__ == "__main__":
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    out_queue = mp.Queue()
    _settings = {
        "threads": {
            "count": 3,
            "stop": True, # tells the system to stop when the in queue is empty
            "timeout": 2
        }
    }

    in_queue = mp.Queue()

    # quick function to add the detault drives and user drives...
    _settings["filescanner"] = FileScanner.avail_config()
    _settings["filescanner"]["builder"] = {
                "drives": ["C", "D", "E"],
                "base": ["users", os.getlogin()],
                "folders": ["Downloads"],
                #['Documents', 'Downloads', 'Dropbox', 'OneDrive', 'Pictures', 'Music', 'Videos'],
            }

    builder = _settings.get("filescanner", {}).get("builder", {})
    base_path = builder.get("base", [])

    logger.debug("Builder: %s", builder)
    logger.debug("Drives: %s", builder.get("drives", ["C"]))
    logger.debug("Base: %s", base_path)
    logger.debug("Folders: %s", builder.get("folders", ["Downloads"]))

    for fs_drive in builder.get("drives", ["C"]):
        for folder_name in builder.get("folders", ["Downloads"]):
            folder_path = base_path + [folder_name]

            fs_path = os.path.join(f"{fs_drive}:\\", *folder_path)
            logger.debug("Try: %s", fs_path)
            if os.path.exists(fs_path):
                logger.info("Adding: %s", fs_path)
                in_queue.put(fs_path)


    logger.debug("Settings: %s", _settings)
    obj = FileScanner(settings=_settings)

    obj.in_queue(in_queue=in_queue)
    obj.out_queue(out_queue=out_queue)

    # add the semiphore to the queue, can also use a timeout option...
    for i in range(_settings.get("threads",{}).get("count",5)):
        in_queue.put(obj.semiphore)

    obj.scan()
    cls_name = obj.semiphore

    obj.close()
    out_queue.put("DONE")

    exts = {}
    in_zip = []

    while out_queue:
        try:
            # set a timeout, and handle the semiphore case too
            o_item = out_queue.get(timeout=_settings.get("threads",{}).get("timeout")) if out_queue else None
            if o_item == "DONE":
                break

            # if the user wants to kill the queue if there are not entries...
            # requires timeout set, otherwise the queue get blocks...
            if not o_item and _settings.get("threads",{}).get("stop"):
                break

            ext = o_item.get("ext", "<missing>")
            if ext not in exts:
                exts[ext] = {
                    "size": 0,
                    "count": 0,
                    "files": []
                }
            exts[ext]["size"] += o_item.get("size",0)
            exts[ext]["count"] += 1
            exts[ext]["files"].append(o_item)

            if "zipfile" in o_item:
                in_zip.append(o_item)

            #logger.info(o_item)
        except Empty:
            break

    for ext, values in exts.items():
        logger.info("\t%s:\t%s,\t%s", ext, values.get("count", 0), values.get("size", 0))

    for fs_item in exts.get(".zip", {}).get("files", []):
        descr_str = "\n\tFile:\t{name}{ext}\n\t\t{folder}\n\t\t{modified}:{size}".format(**fs_item)
        logger.info(descr_str)
        for zf in fs_item.get("files",[]):
            descr_str = "ZIPFILES:\n\tFile:\t{name}{ext}\n\t\t{folder}\n\t\t{size}".format(**zf)

    logger.info("Zipped: %s", len(in_zip))
