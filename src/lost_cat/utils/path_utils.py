"""This model provides a set of functions for handle paths,
file scanning and zip file handling."""
import os
import zipfile

from urllib.parse import urlparse
from validators import url as val_url

class SourceNotValid(Exception):
    """A simple exception class to catch edge casses"""
    def __init__(self, uri:str, message:str, *args: object) -> None:
        self.uri = uri
        self.message = message
        super().__init__(*args)

class SourceNotHandled(Exception):
    """A simple exception class to catch edge casses"""
    def __init__(self, uri:str, message:str, *args: object) -> None:
        self.uri = uri
        self.message = message
        super().__init__(*args)

def build_path(uri: str) -> dict:
    """Will take a path, and split into components
    and return a dictionary
    {
        "root": str
        "type": str
        "folders": list
        "filename": str
        "ext": str
    }"""

    src = {
        "root": None,
        "type": None,
        "folders": []
    }

    if os.path.exists(uri):
        #print(uri)
        drv, path = os.path.splitdrive(uri)
        #print(f"DRV: {drv} \n\t{path}")

        if os.path.isdir(uri):
            src["type"] = "folder"

        elif os.path.isfile(uri):
            src["type"] = "file"
            path, filename = os.path.split(path)
            #print(f"PFN:\t{path}\n\t{filename}")
            name, ext = os.path.splitext(filename)
            #print(f"EXT:\t{name}\n\t{ext}")
            src["name"] = name
            src["ext"] = ext.lower()

        else:
            # not
            raise SourceNotValid(uri=uri, message="path failed file and folder test!")

        folders = []
        while len(path) > 1:
            path, fld = os.path.split(path)
            #print(f"FLD:\t{path}\n\t{fld}")
            if len(fld) > 0:
                folders.append(fld)
            #print(f"F:\t{folders}")

        folders.reverse()
        src["folders"] = folders
        src["root"] = f"{drv}{os.sep}"

    elif val_url(uri):
        src["type"] = "http"

        url_obj = urlparse(uri)
        src["scheme"] = url_obj.scheme
        src["netloc"] = url_obj.netloc
        src["path"] = url_obj.path
        src["params"] = url_obj.params
        src["query"] = url_obj.query
        src["fragment"] = url_obj.fragment

    else:
        raise SourceNotHandled(uri=uri, message="provided uri could not be understood by parser!")

    return src

def scan_files(uri: str) -> dict:
    """Will scan the folder and walk the files and folders below
    yields the found file"""
    for dirpath, _, filenames in os.walk(uri):
        for fullname in filenames:
            filepath = os.path.join(dirpath,fullname)
            filename, ext = os.path.splitext(fullname)
            ext = ext.lower()
            if ext in [".zip"]:
                zfiles = scan_zip(filepath)

                yield {
                    "path": filepath,
                    "folder": dirpath,
                    "name": filename,
                    "ext": ext,
                    "files": zfiles
                }

            else:
                yield {
                    "path": filepath,
                    "folder": dirpath,
                    "name": filename,
                    "ext": ext,
                }

def scan_zip(uri: str) -> dict:
    """Will scan the zip file and return the file details"""
    zip_file = zipfile.ZipFile(uri)
    files = []

    for szf in zip_file.infolist():
        if not szf.is_dir():
            filepath = szf.filename
            dirpath, fullname = os.path.split(filepath)
            filename, ext = os.path.splitext(fullname)
            sub_file = {
                "zipfile": uri,
                "path": filepath,
                "folder": dirpath,
                "name": filename,
                "size": szf.file_size,
                "ext": ext.lower(),
            }
            files.append(sub_file)

    return files
