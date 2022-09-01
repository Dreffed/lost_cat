"""This module provides a set of functions for handle paths,
file scanning and zip file handling.
@author: Dreffed
copyright adscens.io 2022 / thoughtswin systems 2022
"""
import hashlib
import io
import logging
import re
import os
import tarfile
import time
import zipfile

from urllib.parse import urlparse
from validators import url as val_url

from lost_cat.utils.name_utils import PhraseTool

logger = logging.getLogger(__name__)

class SourceDoesNotExist(Exception):
    """A class to raise the missing file"""

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

def func_switch_zip(ext: str, op_label: str) -> object:
    """A sweithc dict to enable the selection of the
    function for the zip file handlers, hard coded :("""
    func = {
        ".zip": {
            "open": open_zip,
            "scan": scan_zip,
            "fetch": fetch_zip
        },
        ".tar.gz": {
            "open": open_tar,
            "read": scan_tar,
            "fetch": fetch_tar
        }
    }
    return func.get(ext,{}).get(op_label)


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
        drv, path = os.path.splitdrive(uri)

        if os.path.isdir(uri):
            src["type"] = "folder"

        elif os.path.isfile(uri):
            src["type"] = "file"
            path, filename = os.path.split(path)
            name, ext = os.path.splitext(filename)
            src["name"] = name
            src["ext"] = ext.lower()

        else:
            # not
            raise SourceNotValid(uri=uri, message="path failed file and folder test!")

        folders = []
        while len(path) > 1:
            path, fld = os.path.split(path)
            if len(fld) > 0:
                folders.append(fld)

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

def get_filename(file_dict: dict) -> str:
    """Will accept a json object of file details and return the
    full filename
        {
            "root":     str
            "folder":   str     (optional)
            "folders":  []      (optional)
            "name":     str     (optional)
            "ext":              expects a "."
        }
        <TODO: Add handler for type = http etc.>
    """

    logger.debug("F: %s", file_dict)
    if file_dict.get("root") == ".":
        file_dict["root"] = os.getcwd()
        logger.debug("using current drive %s", file_dict.get("root"))

    if "folders" in file_dict:
        path = os.path.join(file_dict.get("root"), *file_dict.get("folders",[]))
    else:
        path = os.path.join(file_dict.get("root"), file_dict.get("folder",""))

    # expand the path for user and env vars
    path = os.path.expandvars(os.path.expanduser(path))

    if "name" in file_dict:
        path = os.path.join(path, "{}{}".format(file_dict.get("name"), file_dict.get("ext","")))

    return path

def get_file_metadata(uri: str, options: dict = None) -> dict:
    """return dict of file meats data based on the options passed
        "file": the file name of the file, if "splitextension" specified it is
                just the filename not extension
        "ext": the dotted extension of the file
        "folder"L the folder path of the file

        optional output:
            "folders": an array of the folder names, option "split"
            date and size details: option "stats"
                "modified"
                "accessed"
                "size"
                "bytes": szie in mb, gb, etc.

    """
    if not os.path.exists(uri):
        raise SourceDoesNotExist()

    drv, path = os.path.splitdrive(uri)
    dirpath = os.path.dirname(path)
    filename = os.path.basename(path)
    fname, ext = os.path.splitext(filename)
    f_type = os.path.isfile(uri)
    file_dict =  {
            "type":f_type,
            "root": f"{drv}{os.sep}",
            "folder" : dirpath,
            "file" : filename,
            "ext": ext.lower()
    }

    if options and options.get("profile"):
        p_obj = PhraseTool(in_phrase=filename)
        file_dict["profile"] = p_obj.get_metadata()

    if options and options.get("splitextention"):
        file_dict["file"] = fname

    if options and options.get("splitfolders"):
        #file_dict["folders"] = splitall(dirpath)
        pass

    if options and options.get("stats"):
        time_format = "%Y-%m-%d %H:%M:%S"
        file_stats = os.stat(uri)
        file_dict["accessed"] = time.strftime(time_format,time.localtime(file_stats.st_atime))
        file_dict["modified"] = time.strftime(time_format,time.localtime(file_stats.st_mtime))
        file_dict["created"] = time.strftime(time_format,time.localtime(file_stats.st_ctime))
        file_dict["size"] = file_stats.st_size
        file_dict["mode"] = file_stats.st_mode

    return file_dict

def make_hash(uri: str, buff_size: int = 65536) -> dict:
    """ Will hash the files for both MD5 and SHA1 and return a dict of the hashes"""
    hashes = {}
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    try:
        if os.path.exists(uri):
            logger.debug('%s', uri)
            with open(uri, 'rb') as f_io:
                while True:
                    d_bytes = f_io.read(buff_size)
                    if not d_bytes:
                        break
                    md5.update(d_bytes)
                    sha1.update(d_bytes)

            hashes['MD5'] = md5.hexdigest()
            hashes['SHA1'] = sha1.hexdigest()
        else:
            hashes['MD5'] = 'Missing file'
            hashes['SHA1'] = 'Missing file'

    except OSError as ex:
        logger.error('ERROR: [%s]\n%s', uri, ex)

        hashes['MD5'] = 'ERROR'
        hashes['SHA1'] = 'ERROR'

    return hashes

def scan_files(uri: str, options: dict = None) -> dict:
    """Will scan the folder and walk the files and folders below
    yields the found file"""
    for dirpath, _, filenames in os.walk(uri):
        for fullname in filenames:
            filepath = os.path.join(dirpath,fullname)
            file_dict = get_file_metadata(uri=filepath, options=options)
            ext = file_dict.get("ext","")

            # filter the files...
            if not is_include(file_dict=file_dict, options=options):
                continue

            # handel the options for hash
            if options and options.get("generatehash"):
                maxsize = options.get("maxhashsize", 0)
                if maxsize == 0 or maxsize >= file_dict.get("size",0):
                    file_dict["hash"] = make_hash(uri=filepath)

            op_func = func_switch_zip(ext, "scan")
            if op_func:
                zfiles = op_func(uri=filepath)

                file_dict["files"] = zfiles
                yield file_dict

            else:
                yield file_dict

def is_include(file_dict: dict, options: dict = None) -> bool:
    """will use the filter conditions and if all filters are matched
    will return true"""
    if not options:
        return True

    filter_config = options.get("filter")
    output = {}
    if filter_config:
        if "exts" in filter_config:
            output["ext"] = 0
            if file_dict.get("ext","") in filter_config.get("exts", []):
                output["ext"] = 1

        if "regex" in filter_config:
            output["regex"] = 0
            filter_reg = re.compile(filter_config.get("regex", ""))
            m_re = filter_reg.match(file_dict.get("name",""))
            if m_re:
                output["regex"] = 1

    return len(output) == sum(output.values)

def open_zip(uri: str) -> zipfile.ZipFile:
    """Will open a zip file and return the file handle"""
    return zipfile.ZipFile(uri)

def open_tar(uri: str) -> tarfile.TarFile:
    """Will open a tar file and return the handle"""
    return tarfile.open(uri, mode="r")

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

def scan_tar(uri: str) -> dict:
    """Will handle the targz file"""
    tar_file = tarfile.open(uri, mode="r")
    files = []
    for szf in tar_file.getmembers():
        # process only files...
        if not szf.isfile():
            continue

        filepath = szf.name
        dirpath, fullname = os.path.split(filepath)
        filename, ext = os.path.splitext(fullname)
        sub_file = {
            "zipfile": uri,
            "path": filepath,
            "folder": dirpath,
            "name": filename,
            "size": szf.size,
            "ext": ext.lower(),
        }
        files.append(sub_file)

    return files

def fetch_zip(file_obj: zipfile.ZipFile, item_path: str) -> object:
    """for a given zip file, return the item"""
    _data = file_obj.read(item_path)
    return io.BytesIO(_data)

def fetch_tar(file_obj: tarfile.TarFile, item_path: str) -> object:
    """For a given tarfile return the item"""
    _data = file_obj.read(item_path)
    return io.BytesIO(_data)
