"""
Lost cat will scan and process a range of files
"""
import os

from .utils.path_utils import build_path, scan_files

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
        self._sources = {}
        self._parsers = {}
        self._parse_ext = {}
        self._scanners = {}
        self._features = ["parser"]

        # a local store for the disovered artifacts
        self._artifacts = {
            "files": {}
        }

        # a place to store the processed artifacts, organized
        # by the grouping, and with metadata...
        self._catalog = {}

    def add_source(self, label: str, uri: str, overwrite: bool = False) -> dict:
        """It parse the provided source path and
        add to the source list."""
        if label in self._sources and not overwrite:
            raise SourceAlreadyExists

        uri_obj = build_path(uri=uri)
        self._sources[label] = uri_obj

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
        for uri_obj in self._sources:
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
