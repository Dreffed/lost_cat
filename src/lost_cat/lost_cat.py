"""
Lost cat will scan and process a range of files
"""
import os
import logging
from .utils.path_utils import build_path, scan_files, func_switch_zip

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
    def __init__(self) -> None:
        """Initialize the core elements"""
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

        # a local store for the disovered artifacts
        self._artifacts = {
            "files": dict()
        }

        # a place to store the processed artifacts, organized
        # by the grouping, and with metadata...
        self._catalog = dict()

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
        for _, uri_obj in self._sources.items():
            if uri_obj.get("type") not in ["folder"]:
                continue

            uri = os.path.join(uri_obj.get("root"), *uri_obj.get("folders",[]))

            for fnd_file in scan_files(uri):
                # process the returned files...
                if not fnd_file.get("path","") in self._artifacts.get("files", {}):
                    file_added +=1
                    self._artifacts["files"][fnd_file.get("path")] = fnd_file

                for zip_file in fnd_file.get("files",{}) :
                    if not zip_file.get("path","") in self._artifacts.get("files", {}):
                        zip_added +=1
                        self._artifacts["files"][zip_file.get("path")] = zip_file

        cat_cnt = len(self._artifacts.get("files"))
        return {
            "files": file_added,
            "zipped": zip_added,
            "cataloged": cat_cnt
        }

    def process_artifacts(self) -> dict:
        """Will scan the loaded files into the catalog and apply the PARSER"""
        z_path = None
        z_ext = None
        zip_obj = None

        data = {}

        # scan the files and zips...
        for _, file_obj in self._artifacts.get("files", {}).items():
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

                        logger.debug(z_path)
                        logger.debug(z_func)
                        zip_obj = z_func(uri=z_path)

                    if zip_obj:
                        bytes_io = func_switch_zip(ext=z_ext, op_label="fetch")(
                                file_obj=zip_obj, item_path=file_obj.get("path"))
                        obj = cls(bytes_io=bytes_io)
                else:
                    obj = cls(uri=file_obj.get("path"))

                logger.debug("Running Class %s -> %s", p_label, cls)

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
                logger.debug(file_obj)

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
