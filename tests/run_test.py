import glob
import unittest
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, 'lost_cat')

testSuite = unittest.TestSuite()
test_file_strings = glob.glob('test_*.py')
module_strings = [str[0:len(str)-3] for str in test_file_strings]

if __name__ == "__main__":
     unittest.main()