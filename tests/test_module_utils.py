"""A test case for the path utils module"""
import logging
import os
import sys
import unittest
from lost_cat.utils.module_utils import load_module, load_modules, load_modulefile, ModuleFailedToLoad

logger = logging.getLogger(__name__)

class TestUtilsModule(unittest.TestCase):
    """A container class for the build path modeule test cases"""

    def test_loadmodule(self):
        """ Unit test for the loadmodule function"""
        _uri ="tests.code.simple_module.FirstClass"
        _objs = load_module(module=_uri)
        for _k, _v in _objs.items():
            logger.debug("Objs: %s => %s", _k, _v)

        assert "FirstClass" in _objs

        _objs  = load_module(module="tests.code.simple_module", funcs=["second_function"])
        for _k, _v in _objs.items():
            logger.debug("Objs: %s => %s", _k, _v)

        assert "second_function" in _objs

    def test_loadmodulefile(self):
        """ UNit test for the load_modulefile function"""
        _uri = r"tests\code"
        _file = r"simple_module.py"

        _objs = load_modulefile(folder=_uri, file=_file)
        for _k, _v in _objs.items():
            logger.debug("Objs: %s => %s", _k, _v)
        assert "FirstClass" in _objs
        assert "SecondClass" in _objs
        assert "first_function" in _objs
        assert "second_function" in _objs

        _uri = r"tests\code"
        _file = r"simple_module.py"
        _funcs = ["first_function"]
        _objs = load_modulefile(folder=_uri, file=_file, funcs=_funcs)
        for _k, _v in _objs.items():
            logger.debug("Objs: %s => %s", _k, _v)

        assert "first_function" in _objs

    def test_loadmodules(self):
        """ Unit test for the load modules"""


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    unittest.main()
