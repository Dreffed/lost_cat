"""
Lost cat will scan and process a range of files
"""
import os
from .utils.path_utils import build_path, scan_files

class SourceAlreadyExists(Exception):
    """A simple exception to raise already exist error"""

class LostCat(object):
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