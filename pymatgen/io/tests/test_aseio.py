#!/usr/bin/env python

'''
Created on Mar 8, 2012
'''

from __future__ import division

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyue@mit.edu"
__date__ = "Mar 8, 2012"

import unittest
import os

from nose.exc import SkipTest

from pymatgen.core.structure import Composition
from pymatgen.io.vaspio import Poscar
import pymatgen.io.aseio as aio

import pymatgen

test_dir = os.path.join(os.path.dirname(os.path.abspath(pymatgen.__file__)), '..', 'test_files')

class AseAtomsAdaptorTest(unittest.TestCase):

    def test_get_atoms(self):
        if not aio.ase_loaded:
            raise SkipTest("ASE not present. Skipping...")
        p = Poscar.from_file(os.path.join(test_dir, 'POSCAR'))
        structure = p.struct
        atoms = aio.AseAtomsAdaptor.get_atoms(structure)
        ase_composition = Composition.from_formula(atoms.get_name())
        self.assertEqual(ase_composition, structure.composition)

    def test_get_structure(self):
        if not aio.ase_loaded:
            raise SkipTest("ASE not present. Skipping...")
        p = Poscar.from_file(os.path.join(test_dir, 'POSCAR'))
        atoms = aio.AseAtomsAdaptor.get_atoms(p.struct)
        self.assertEqual(aio.AseAtomsAdaptor.get_structure(atoms).formula, "Fe4 P4 O16")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    if aio.ase_loaded:
        unittest.main()
    else:
        print "ASE not loaded. Skipping tests"
