"""this will scan a word set and return the details"""
import io
import logging
import multiprocessing as mp
import os
import threading as td
import zipfile
from parsers.DICOM_parser import DICOMParser

from utils.tag_anon import TagAnon
try:
    from processors.base_processor import BaseProcessor
except ImportError:
    import sys
    from os import path
    sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
    from base_processor import BaseProcessor

try:
    from utils.path_utils import scan_files, SourceNotHandled
except ImportError:
    import sys
    from os import path
    sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
    from utils.path_utils import scan_files, SourceNotHandled

from queue import Empty

logger = logging.getLogger(__name__)

class WordProcessor(BaseProcessor):
    """"""