""" A module for fucntions and classes to help manage run time
    loaded modules.
    Returns a set of dictionaries with values as the class or functions """

import importlib
import inspect
import logging
import os
import sys

logger = logging.getLogger(__name__)

class ModuleFailedToLoad(Exception):
    """A simple exception to raise module load error"""
    def __init__(self, label: str, message: str) -> None:
        super.__init__()
        self.label = label
        self.message = message

def load_modules(folderpath: str):
    _data = {}
    for _folder, _, _files in os.walk(os.path.abspath(folderpath)):
        for _file in _files:
            if not _file.lower().endswith(".py"):
                continue
            if _file == "__init__.py":
                continue

            _mod_data = load_modulefile(_folder, _file)
            for _fk, _fv in _mod_data.items():
                _data[_fk] = _fv
    return _data

def load_modulefile(folder: str, file: str, funcs: list = None):
    """Loads a module from a relative or abs path"""
    _data = {}
    _pfile = os.path.abspath(os.path.join(folder, file))
    _m_name = file.replace(".py", "")
    _spec = importlib.util.spec_from_file_location(_m_name, _pfile)
    logger.debug("Spec:   %s", _spec)

    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    logger.debug("Module: %s", _module)
    logger.debug("Dir:    %s", dir(_module))
    _members = dict(inspect.getmembers(_module))

    if funcs:
        for _fn in funcs:
            logger.debug("Func: %s", _fn)
            _data[_fn] = _members.get(_fn)
    else:
        logger.debug("Inspect: %s", _members)
        sys.modules[_spec.name] = _module
        for _fn, _fv in _members.items():
            if _fn.startswith("__"):
                continue

            _data[_fn] = _fv

    return _data

def load_module(module: str, funcs: list = None) -> dict:
    """Loads a module based on the module path rather than
    file path, if a func list is provided ti will only
    return the object pointers
    """
    _data = {}
    try:
        components = module.split('.')
        logger.debug("Path: %s Funcs: %s", components, funcs)

        if funcs:
            # assum full path
            mod = __import__(".".join(components), fromlist=funcs)
            logger.debug("Module: %s", dir(mod))

            for _fn in funcs:
                _data[_fn] = getattr(mod, _fn)
                logger.debug(_data[_fn])

        else:
            # assume the last element is the function or class
            mod = __import__(".".join(components[:-1]), fromlist=components[-1])
            _data[components[-1]] = getattr(mod, components[-1])

            # finds the classes in the module..
            # check each class and add to processor list...
            logger.debug(_data[components[-1]])

    except ImportError as ex:
        raise ModuleFailedToLoad(label=module,
                message="module could not be loaded") from ex

    return _data
