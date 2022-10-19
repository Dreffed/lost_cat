"""this will scan a word set and return the details"""
import io
import logging
import multiprocessing as mp
import os
import threading as td
import zipfile
from queue import Empty

from lost_cat.parsers.dicom_parser import DICOMParser
from lost_cat.processors.base_processor import BaseProcessor
from lost_cat.utils.path_utils import SourceNotHandled, scan_files
from lost_cat.utils.tag_anon import TagAnon

logger = logging.getLogger(__name__)

class WordProcessor(BaseProcessor):
    """"""
