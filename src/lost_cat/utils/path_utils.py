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

try:
    from os import scandir, DirEntry
except ImportError:
    from scandir import scandir, DirEntry

from urllib.parse import urlparse
from validators import url as val_url

from lost_cat.utils.phrase_utils import PhraseTool

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

def split_folder(path: str) -> list:
    """Will split the folder path in to a list of folders"""
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts

def build_path(uri: str, path_type: str = "file") -> dict:
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

    logger.debug("Check: %s\t:%s\t:%s ", r"[\\\/\.]+", uri, re.search(r"[\\\/\.]+", uri))

    if val_url(uri):
        src["type"] = "http"

        url_obj = urlparse(uri)
        src["scheme"] = url_obj.scheme
        src["netloc"] = url_obj.netloc
        src["path"] = url_obj.path
        src["params"] = url_obj.params
        src["query"] = url_obj.query
        src["fragment"] = url_obj.fragment

    elif re.search(r"[\\\/\.]+", uri):
        uri = os.path.expandvars(os.path.expanduser(uri))
        drv, path = os.path.splitdrive(uri)

        if os.path.exists(uri):
            if os.path.isdir(uri):
                src["type"] = "folder"

            elif os.path.isfile(uri):
                src["type"] = "file"
        else:
            src["type"] = path_type

        if src["type"] == "file":
            path, filename = os.path.split(path)
            name, ext = os.path.splitext(filename)
            src["name"] = name
            src["ext"] = ext.lower()

        folders = []
        while len(path) > 1:
            path, fld = os.path.split(path)
            if len(fld) > 0:
                folders.append(fld)

        folders.reverse()
        src["folders"] = folders
        src["root"] = f"{drv}{os.sep}"

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
            "ext":              (optional) expects "." prefix
        }
        <TODO: Add handler for type = http etc.>
    """

    #logger.debug("F: %s", file_dict)
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

    if options and options.get("splitextension"):
        file_dict["file"] = fname

    if options and options.get("splitfolders"):
        file_dict["folders"] = split_folder(dirpath)

    return file_dict

def make_hash(uri: str, buff_size: int = 65536) -> dict:
    """ Will hash the files for both MD5 and SHA1 and return a dict of the hashes"""
    hashes = {}
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    try:
        if os.path.exists(uri):
            #logger.debug('%s', uri)
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

def fast_scan(uri: str) -> DirEntry:
    """"""
    for os_obj in scandir(path=uri):
        try:
            if os_obj.is_dir(follow_symlinks=False):
                yield from fast_scan(uri=os_obj.path)
            else:
                if os_obj.is_file():
                    #logger.debug(os_obj)
                    yield os_obj

        except PermissionError:
            logger.error("Permission Error: %s", os_obj.path)

def scan_files(uri: str, options: dict = None) -> dict:
    """Will scan the folder and walk the files and folders below
    yields the found file"""
    for os_obj in fast_scan(uri=uri):
        try:
            drv, path = os.path.splitdrive(os_obj.path)
            dirpath = os.path.dirname(path)
            filename = os.path.basename(path)
            fname, ext = os.path.splitext(filename)

            f_type = "file" if os_obj.is_file() else "folder"

            file_dict =  {
                    "type":f_type,
                    "root": f"{drv}{os.sep}",
                    "folder" : dirpath,
                    "file" : filename,
                    "ext": ext.lower()
            }

            if options and options.get("splitextension"):
                file_dict["file"] = fname

            if options and options.get("splitfolders"):
                file_dict["folders"] = dirpath.split(os.sep) #split_folder(dirpath)

            # filter the files...
            if not is_include(file_dict=file_dict, options=options):
                continue

            if options and options.get("stats"):
                time_format = "%Y-%m-%d %H:%M:%S"
                file_stats = os.stat(uri)
                file_dict["accessed"] = time.strftime(time_format,
                        time.localtime(file_stats.st_atime))
                file_dict["modified"] = time.strftime(time_format,
                        time.localtime(file_stats.st_mtime))
                file_dict["created"] = time.strftime(time_format,
                        time.localtime(file_stats.st_ctime))
                file_dict["size"] = file_stats.st_size
                file_dict["mode"] = file_stats.st_mode

            if options and options.get("profile"):
                p_obj = PhraseTool(in_phrase=file_dict.get("file",""))
                file_dict["profile"] = p_obj.get_metadata()

            # handel the options for hash
            if options and options.get("generatehash"):
                maxsize = options.get("maxhashsize", 0)
                if maxsize == 0 or maxsize >= file_dict.get("size",0):
                    file_dict["hash"] = make_hash(uri=os_obj.path)

            op_func = func_switch_zip(ext, "scan")
            if op_func:
                zfiles = op_func(uri=os_obj.path)
                file_dict["files"] = zfiles
                yield file_dict

            else:
                yield file_dict

        except SourceDoesNotExist as ex:
            logger.error('URI: %s %s', os_obj.path, ex)
        except zipfile.BadZipFile as ex:
            logger.error('URI: %s %s', os_obj.path, ex)
        except PermissionError as ex:
            logger.error("Permission Error: %s %s", os_obj.path, ex)


def is_include(file_dict: dict, options: dict = None) -> bool:
    """will use the filter conditions and if all filters are matched
    will return true"""
    if not options:
        return True

    filter_config = options.get("filter")
    if not filter_config:
        return True

    output = {}
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
