#!/usr/bin/env python

'''
Created on Mar 18, 2012
'''

from __future__ import division

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyue@mit.edu"
__date__ = "Mar 18, 2012"

import unittest
import os
import pymatgen

from pymatgen.borg.hive import VaspToComputedEntryDrone
from pymatgen.borg.queen import BorgQueen

test_dir = os.path.join(os.path.dirname(os.path.abspath(pymatgen.__file__)), '..', 'test_files')


class BorgQueenTest(unittest.TestCase):

    def setUp(self):
        drone = VaspToComputedEntryDrone()
        self.queen = BorgQueen(drone, test_dir, 1)

    def test_get_assimilated_data(self):
        data = self.queen.get_assimilated_data()
        self.assertEqual(len(data), 1)

    def test_load_data(self):
        drone = VaspToComputedEntryDrone()
        queen = BorgQueen(drone)
        queen.load_data(os.path.join(test_dir, "assimilated.json"))
        self.assertEqual(len(queen.get_assimilated_data()), 1)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
