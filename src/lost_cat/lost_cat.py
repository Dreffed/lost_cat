"""
Lost cat will scan and process a range of files
"""
import os
import logging
import shelve
import time
from .database.db_utils import DBEngine
from .database.schema import SourceMaps, SourceUris, SubPaths, SourceValues, LCItems ,LCItemVersions, NameProfiles, NameProfileParts, mapper_registry
from .utils.path_utils import build_path, get_filename, scan_files, func_switch_zip

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, session

logger = logging.getLogger(__name__)

# <TODO: move this out exception library>
class FeatureNotImplemented(Exception):
    """used for the feature not implemented"""
    def __init__(self, label: str, feature: str, message: str) -> None:
        self.label = label
        self.feature = feature
        self.message = message
        super().__init__()

class SourceAlreadyExists(Exception):
    """A simple exception to raise already exist error"""

class ParserAlreadyExists(Exception):
    """A simple exception to raise already exist error"""

class ScannerAlreadyExists(Exception):
    """A simple exception to raise already exist error"""

class ParserFailedToLoad(Exception):
    """A simple exception to raise already exist error"""
    def __init__(self, label: str, base_class: str, message: str) -> None:
        self.label = label
        self.base_class = base_class
        self.message = message
        super().__init__()

class LostCat():
    """
    The Lost Cat Main class

    - Lost cat will accept a range of sources (OS Paths)
    - Scan the folders and files
    - Create an artifact list
    - Create a catalog:
        - Grouped by key tags
        - metadata extracted from files as needed
        - file / folder path metadata included
        - it will also scan and index archive files (zip only atm)
    - provide a set of tools to move, relabel, and so on to help organize
    """
    name = "LostCat"
    version = "0.0.3"

    def __init__(self, options: dict = None,
            shelve_paths: dict = None,
            db_connection: dict = None) -> None:
        """Initialize the core elements

        Parameters
        ----------
        opttion : dict      A dict that sets the search options for the syste,
            {
                "profile":          will profile the filename of the artifact
                "splitextension":   will split of the extension from the name
                "splitfolders":     will break the folders in an list of folders
                "stats":            will collect the system stats for the file
                "generatehash":     will generate a MD5 and SHA1 hash of the file
                "maxhashsize"       will limt the hash size scanned
                "filter":           if set will apply a filter check during the scan
                    "ext":          a list of extensions to include in the scan .<ext>
                    "regex":        a regex to apply to the file to select
            }

        shelve_paths: dict  A dict of paths to use for the components
            {
                "artifcats":        path to artifacts shelve file
            }

        """
        # a labelled dic of sources,
        # sources are parsed to an object
        self._sources = dict()
        self._parsers = dict()
        self._parse_ext = dict()
        self._scanners = dict()
        self._features = ["parser"]
        self._anonimizer = dict()
        self._tags_exp = dict()
        self._group_tags = dict()
        self._set_alias_tags = dict()

        # set the objects
        if options:
            self._options = options
        else:
            # default to create a phrase profile for the filename
            self._options = {
                "splitfolders": True,
                "splitextension": True,
                "stats": True
            }

        # shelve root is the base oath for the shelve file
        # this program will create a shelve for each function run...
        # artifacts - augmented with meatadata and file information
        if shelve_paths:
            self._paths = shelve_paths

            # a local store for the disovered artifacts
            logger.info("Shelve file: %s", self._paths.get("artifacts", "<missing>"))
            self._artifacts = shelve.open(self._paths.get("artifacts", "<missing>"))
        elif db_connection:
            self._paths = db_connection
            logger.info("Database: %s", self._paths.get("database", "<missing>"))
            self._db = DBEngine(connString=self._paths.get("database", "lost-cat.db"))

        # a place to store the processed artifacts, organized
        # by the grouping, and with metadata...
        self._catalog = dict()

    def close(self) -> None:
        """Will save the shelve to the OS"""
        logger.debug("Closing shelve %s", len(self._artifacts))
        self._artifacts.close()

    def load_db_sources(self):
        """will read the sources from the db"""
        if not self._db:
            return

        # load in the tables from the source system...
        db_sess = self._db.session()

        rows = list(db_sess.execute(select(SourceUris).order_by(SourceUris.s_type)))
        for r in rows:
            logger.info(r)

        rows = list(db_sess.execute(select(SourceValues).order_by(SourceValues.sv_label)))
        for r in rows:
            logger.info(r)

        

    def add_source(self, label: str, uri: str, overwrite: bool = False) -> dict:
        """It parse the provided source path and
        add to the source list."""
        if label in self._sources and not overwrite:
            raise SourceAlreadyExists

        self._sources[label] = build_path(uri=uri)

    def add_scanner(self, label: str, base_class: object, overwrite: bool = False) -> None:
        """Add a scnner tool to the system, the added scanner will """
        # this disabled, add an app option
        if "scanner" not in self._features:
            raise FeatureNotImplemented(label="Feature", feature="Scanners",
                    message="Scanner feature not implemented!")

        if label in self._scanners and not overwrite:
            raise ScannerAlreadyExists

        # the scanner will process the source uri and determine if it can handle the
        # scanning action and prodution of items
        self._scanners[label] = {"class": base_class}

    def add_parser(self, label: str, base_class: object, overwrite: bool = False) -> None:
        """Adds a parser to the file handling process
        {
            <name> : {
                    "class": <class>
                },
            ....
        }
        """
        # this disabled, add an app option
        if "parser" not in self._features:
            raise FeatureNotImplemented(label="Feature", feature="parser",
                    message="parser feature not implemented!")

        if label in self._parsers and not overwrite:
            raise ParserAlreadyExists

        self._parsers[label] = {"class": base_class}

        # scan the parser for the file types supported...
        try:
            obj = base_class()
            for ext in obj.get_extensions():
                if ext not in self._parse_ext:
                    self._parse_ext[ext] = []
                self._parse_ext[ext].append(label)

        except Exception as ex:
            raise ParserFailedToLoad(label=label,
                    message="Class provided could not be loaded for extensions.",
                    base_class=base_class) from ex

    def load_catalog(self, catalog: dict) -> None:
        """Will load a dictionary as the catalog"""
        self._artifacts = catalog

    def fetch_catalog(self) -> dict:
        """Will load a dictionary as the catalog"""
        return self._artifacts

    def catalog_artifacts(self) -> dict:
        """Will scan the sources and load a dictionary with the found files,
        it'll use the template list for extensions to use.
        <<for web addresses, it'll need a scraper built>>"""
        file_added = 0
        zip_added = 0
        start = time.time()

        for uri_obj in self._sources.items():
            if uri_obj.get("type") not in ["folder"]:
                continue

            uri = os.path.join(uri_obj.get("root"), *uri_obj.get("folders",[]))
            if not os.path.exists(uri):
                logging.error("URI doesn't exisit %s", uri)

            start_location = time.time()

            for idx, fnd_file in enumerate(scan_files(uri, options=self._options)):
                file_path = get_filename(fnd_file)
                #

                # process the returned files...
                if not file_path in self._artifacts:
                    file_added +=1
                    self._artifacts[file_path] = fnd_file

                # check it is a zip file items...
                for zip_file in fnd_file.get("files",{}) :
                    if not zip_file.get("path") in self._artifacts:
                        zip_added +=1
                        self._artifacts[zip_file.get("path")] = zip_file

                # print out the srtatus
                if idx % self._options.get("status_count", 10000) == 0:
                    logger.debug("Example: %s", fnd_file)
                    logger.info("Status: %s Time: %s Added: %s Total: %s",
                            idx, time.time() - start_location,
                            file_added, len(self._artifacts))

        cat_cnt = len(self._artifacts)
        return {
            "files": file_added,
            "zipped": zip_added,
            "cataloged": cat_cnt,
            "duration": time.time() - start
        }

    def process_parsers(self) -> dict:
        """Will scan the loaded files into the catalog and apply the PARSER"""
        if "parser" not in self._features:
            raise FeatureNotImplemented(label="Feature", feature="parser",
                    message="parser feature not implemented!")

        z_path = None
        z_ext = None
        zip_obj = None

        data = {}

        # scan the files and zips...
        for _, file_obj in self._artifacts.items():
            f_ext = file_obj.get("ext","<>")
            if f_ext not in data:
                data[f_ext] = 0
            data[f_ext] += 1

            # scan using the template function
            for p_label in self._parse_ext.get(f_ext, []):
                cls = self._parsers.get(p_label,{}).get("class")
                if not cls:
                    continue

                if "zipfile" in file_obj:
                    if file_obj.get("zipfile") != z_path:
                        z_path = file_obj.get("zipfile")
                        _, z_ext = os.path.splitext(z_path)
                        z_ext = z_ext.lower()
                        z_func = func_switch_zip(ext=z_ext, op_label="open")

                        #logger.debug(z_path)
                        #logger.debug(z_func)
                        zip_obj = z_func(uri=z_path)

                    if zip_obj:
                        bytes_io = func_switch_zip(ext=z_ext, op_label="fetch")(
                                file_obj=zip_obj, item_path=file_obj.get("path"))
                        obj = cls(bytes_io=bytes_io)
                else:
                    obj = cls(uri=file_obj.get("path"))

                #logger.debug("Running Class %s -> %s", p_label, cls)

                # load the anonimizer
                obj.set_anonimizer(anonimizer=self._anonimizer)
                obj.set_export_tags(tags=self._tags_exp)
                obj.set_group_tags(tags=self._group_tags)
                obj.set_alias_tags(tags=self._set_alias_tags)

                md_obj = obj.get_metadata()

                # fetch the metadata...
                if "metadata" not in file_obj:
                    file_obj["metadata"] = {}

                for mt, mv in md_obj.get("metadata", {}).items():
                    file_obj["metadata"][mt] = mv

                if "grouping" not in file_obj:
                    file_obj["grouping"] = {}

                for gt, gv in md_obj.get("grouping", {}).items():
                    file_obj["grouping"][gt] = gv

                # close th file
                obj.close()

                # save the items to the catalog by walking the group tree
                cur_node = self._catalog
                #logger.debug(file_obj)

                # pivot into the grouping structure...
                for gt, gv in md_obj.get("grouping", {}).items():
                    if not gv:
                        gv = "<missing>"
                    if gv not in cur_node:
                        cur_node[gv] = {}
                    cur_node = cur_node.get(gv)

                # save the file item at the botto,
                cur_node["files"]  = []
                cur_node["files"].append(file_obj)

        return data
