#!/usr/bin/env python

'''
This module defines site transformations which transforms a structure into 
another structure. Site transformations differ from standard transformations 
in that they operate in a site-specific manner.
All transformations should inherit the AbstractTransformation ABC.
'''

from __future__ import division

__author__ = "Shyue Ping Ong, Will Richards"
__copyright__ = "Copyright 2011, The Materials Project"
__version__ = "1.2"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyue@mit.edu"
__date__ = "Sep 23, 2011"

import math
import itertools
import logging
import time

from pymatgen.transformations.transformation_abc import AbstractTransformation
from pymatgen.core.structure_modifier import StructureEditor
from pymatgen.analysis.ewald import EwaldSummation, EwaldMinimizer

class ReplaceSiteSpeciesTransformation(AbstractTransformation):
    """
    This transformation substitutes certain sites with certain species.
    """
    def __init__(self, indices_species_map):
        """
        Args:
            indices_species_map:
                A dict containing the species mapping in int-string pairs. 
                E.g., { 1:"Na"} or {2:"Mn2+"}. Multiple substitutions can 
                be done. Overloaded to accept sp_and_occu dictionary
                E.g. {'Si: {'Ge':0.75, 'C':0.25} }, which substitutes a single
                species with multiple species to generate a disordered structure.
        """
        self._indices_species_map = indices_species_map

    def apply_transformation(self, structure):
        editor = StructureEditor(structure)
        for i, sp in self._indices_species_map.items():
            editor.replace_site(int(i), sp)
        return editor.modified_structure

    def __str__(self):
        return "ReplaceSiteSpeciesTransformationTransformation :" + ", ".join([k + "->" + v for k, v in self._species_map.items()])

    def __repr__(self):
        return self.__str__()

    @property
    def inverse(self):
        return None

    @property
    def is_one_to_many(self):
        return False

    @property
    def to_dict(self):
        output = {'name' : self.__class__.__name__, 'version': __version__}
        output['init_args'] = {'indices_species_map': self._indices_species_map}
        return output


class RemoveSitesTransformation(AbstractTransformation):
    """
    Remove certain sites in a structure.
    """
    def __init__(self, indices_to_remove):
        """
        Args:
            indices_to_remove:
                List of indices to remove. E.g., [0, 1, 2] 
        """
        self._indices = indices_to_remove

    def apply_transformation(self, structure):
        editor = StructureEditor(structure)
        editor.delete_sites(self._indices)
        return editor.modified_structure

    def __str__(self):
        return "RemoveSitesTransformation :" + ", ".join(self._indices)

    def __repr__(self):
        return self.__str__()

    @property
    def inverse(self):
        return None

    @property
    def is_one_to_many(self):
        return False

    @property
    def to_dict(self):
        output = {'name' : self.__class__.__name__, 'version': __version__}
        output['init_args'] = {'indices_to_remove': self._indices}
        return output


class TranslateSitesTransformation(AbstractTransformation):
    """
    This class translates a set of sites by a certain vector.
    """
    def __init__(self, indices_to_move, translation_vector, vector_in_frac_coords=True):
        self._indices = indices_to_move
        self._vector = translation_vector
        self._frac = vector_in_frac_coords

    def apply_transformation(self, structure):
        editor = StructureEditor(structure)
        editor.translate_sites(self._indices, self._vector, self._frac)
        return editor.modified_structure

    def __str__(self):
        return "TranslateSitesTransformation for indices {}, vector {} and vector_in_frac_coords = {}".format(self._indices, self._translation_vector, self._frac)

    def __repr__(self):
        return self.__str__()

    @property
    def inverse(self):
        return TranslateSitesTransformation(self._indices, [-c for c in self._vector], self._frac)

    @property
    def is_one_to_many(self):
        return False

    @property
    def to_dict(self):
        output = {'name' : self.__class__.__name__, 'version': __version__}
        output['init_args'] = {'indices_to_move': self._indices,
                               'translation_vector': self._vector,
                               'vector_in_frac_coords': self._frac}
        return output


class PartialRemoveSitesTransformation(AbstractTransformation):
    """
    Remove fraction of specie from a structure. 
    Requires an oxidation state decorated structure for ewald sum to be 
    computed.
    
    Given that the solution to selecting the right removals is NP-hard, there
    are several algorithms provided with varying degrees of accuracy and speed.
    The options are as follows:
    
    ALGO_FAST:
        This is a highly optimized algorithm to quickly go through the search 
        tree. It is guaranteed to find the optimal solution, but will return
        only a single lowest energy structure. Typically, you will want to use
        this.
    
    ALGO_COMPLETE:
        The complete algo ensures that you get all symmetrically distinct 
        orderings, ranked by the estimated Ewald energy. But this can be an
        extremely time-consuming process if the number of possible orderings is
        very large. Use this if you really want all possible orderings. If you
        want just the lowest energy ordering, ALGO_FAST is accurate and faster.
        
    ALGO_BEST_FIRST:
        This algorithm is for ordering the really large cells that defeats even 
        ALGO_FAST.  For example, if you have 48 sites of which you want to
        remove 16 of them, the number of possible orderings is around 2 x 10^12.
        ALGO_BEST_FIRST shortcircuits the entire search tree by removing the 
        highest energy site first, then followed by the next highest energy
        site, and so on.  It is guaranteed to find a solution in a reasonable
        time, but it is also likely to be highly inaccurate. 
    """

    ALGO_FAST = 0
    ALGO_COMPLETE = 1
    ALGO_BEST_FIRST = 2

    def __init__(self, indices, fractions, algo=ALGO_COMPLETE):
        """
        Args:
            indices:
                A list of list of indices.
                e.g. [[0, 1], [2, 3, 4, 5]]
            fractions:
                The corresponding fractions to remove. Must be same length as indices.
                e.g. [0.5, 0.25]
            algo:
                This parameter allows you to choose the algorithm to perform
                ordering. Use one of PartialRemoveSpecieTransformation.ALGO_*
                variables to set the algo.
        """
        self._indices = indices
        self._fractions = fractions
        self._algo = algo
        self.logger = logging.getLogger(self.__class__.__name__)

    def best_first_ordering(self, structure, num_remove_dict):
        self.logger.debug('Performing best first ordering')
        starttime = time.time()
        self.logger.debug('Performing initial ewald sum...')
        ewaldsum = EwaldSummation(structure)
        self.logger.debug('Ewald sum took {} seconds.'.format(time.time() - starttime))
        starttime = time.time()

        ematrix = ewaldsum.total_energy_matrix
        to_delete = []

        totalremovals = sum(num_remove_dict.values())
        removed = {k : 0 for k in num_remove_dict.keys()}
        for i in xrange(totalremovals):
            maxindex = None
            maxe = float('-inf')
            maxindices = None
            for indices in num_remove_dict.keys():
                if removed[indices] < num_remove_dict[indices]:
                    for ind in indices:
                        if ind not in to_delete:
                            energy = sum(ematrix[:, ind]) + sum(ematrix[:, ind]) - ematrix[ind, ind]
                            if energy > maxe:
                                maxindex = ind
                                maxe = energy
                                maxindices = indices
            removed[maxindices] += 1
            to_delete.append(maxindex)
            ematrix[:, maxindex] = 0
            ematrix[maxindex, :] = 0
        mod = StructureEditor(structure)
        mod.delete_sites(to_delete)
        self.logger.debug('Minimizing Ewald took {} seconds.'.format(time.time() - starttime))
        return [{'energy':sum(sum(ematrix)),
                 'structure': mod.modified_structure.get_sorted_structure()}]

    def complete_ordering(self, structure, num_remove_dict):
        self.logger.debug('Performing complete ordering...')
        all_structures = []
        from pymatgen.symmetry.spglib_adaptor import SymmetryFinder
        symprec = 0.1
        s = SymmetryFinder(structure, symprec=symprec)
        self.logger.debug('Symmetry of structure is determined to be {}.'.format(s.get_spacegroup_symbol()))
        sg = s.get_spacegroup()
        tested_sites = []
        starttime = time.time()
        self.logger.debug('Performing initial ewald sum...')
        ewaldsum = EwaldSummation(structure)
        self.logger.debug('Ewald sum took {} seconds.'.format(time.time() - starttime))
        starttime = time.time()

        allcombis = []
        for ind, num in num_remove_dict.items():
            allcombis.append(itertools.combinations(ind, num))

        count = 0
        for allindices in itertools.product(*allcombis):
            sites_to_remove = []
            indices_list = []
            for indices in allindices:
                sites_to_remove.extend([structure[i] for i in indices])
                indices_list.extend(indices)

            mod = StructureEditor(structure)
            mod.delete_sites(indices_list)
            s_new = mod.modified_structure
            energy = ewaldsum.compute_partial_energy(indices_list)
            already_tested = False
            for i, tsites in enumerate(tested_sites):
                tenergy = all_structures[i]['energy']
                if abs((energy - tenergy) / len(s_new)) < 1e-5 and sg.are_symmetrically_equivalent(sites_to_remove, tsites, symprec=symprec):
                    already_tested = True

            if not already_tested:
                tested_sites.append(sites_to_remove)
                all_structures.append({'structure':s_new, 'energy':energy})

            count += 1
            if count % 10 == 0:
                timenow = time.time()
                self.logger.debug('{} structures, {:.2f} seconds.'.format(count, timenow - starttime))
                self.logger.debug('Average time per combi = {} seconds'.format((timenow - starttime) / count))
                self.logger.debug('{} symmetrically distinct structures found.'.format(len(all_structures)))

        all_structures = sorted(all_structures, key=lambda s: s['energy'])
        return all_structures

    def fast_ordering(self, structure, num_remove_dict, num_to_return=1):
        """
        This method uses the matrix form of ewaldsum to calculate the ewald sums 
        of the potential structures. This is on the order of 4 orders of magnitude 
        faster when there are large numbers of permutations to consider.
        There are further optimizations possible (doing a smarter search of 
        permutations for example), but this wont make a difference
        until the number of permutations is on the order of 30,000.
        """
        self.logger.debug('Performing fast ordering')
        starttime = time.time()
        self.logger.debug('Performing initial ewald sum...')

        ewaldmatrix = EwaldSummation(structure).total_energy_matrix
        self.logger.debug('Ewald sum took {} seconds.'.format(time.time() - starttime))
        starttime = time.time()
        m_list = []
        for indices, num in num_remove_dict.items():
            m_list.append([0, num, list(indices), None])

        self.logger.debug('Calling EwaldMinimizer...')
        minimizer = EwaldMinimizer(ewaldmatrix, m_list, num_to_return, PartialRemoveSitesTransformation.ALGO_FAST)
        self.logger.debug('Minimizing Ewald took {} seconds.'.format(time.time() - starttime))

        all_structures = []

        lowest_energy = minimizer.output_lists[0][0]
        num_atoms = sum(structure.composition.values())

        for output in minimizer.output_lists:
            se = StructureEditor(structure)
            del_indices = [] #do deletions afterwards because they screw up the indices of the structure

            for manipulation in output[1]:
                if manipulation[1] is None:
                    del_indices.append(manipulation[0])
                else:
                    se.replace_site(manipulation[0], manipulation[1])
            se.delete_sites(del_indices)
            all_structures.append({'energy':output[0], 'energy_above_minimum':(output[0] - lowest_energy) / num_atoms, 'structure': se.modified_structure.get_sorted_structure()})

        return all_structures

    def apply_transformation(self, structure, return_ranked_list=False):
        """
        Apply the transformation.
        
        Args:
            structure:
                input structure
            return_ranked_list:
                Boolean stating whether or not multiple structures are
                returned. If return_ranked_list is a number, that number of
                structures is returned.
                
        Returns:
            Depending on returned_ranked list, either a transformed structure 
            or
            a list of dictionaries, where each dictionary is of the form 
            {'structure' = .... , 'other_arguments'}
            the key 'transformation' is reserved for the transformation that
            was actually applied to the structure. 
            This transformation is parsed by the alchemy classes for generating
            a more specific transformation history. Any other information will
            be stored in the transformation_parameters dictionary in the 
            transmuted structure class.
        """
        num_remove_dict = {}
        total_combis = 0
        for indices, frac in zip(self._indices, self._fractions):
            num_to_remove = len(indices) * frac
            if abs(num_to_remove - int(round(num_to_remove))) > 1e-3:
                raise ValueError("Fraction to remove must be consistent with integer amounts in structure.")
            else:
                num_to_remove = int(round(num_to_remove))
            num_remove_dict[tuple(indices)] = num_to_remove
            n = len(indices)
            total_combis += int(round(math.factorial(n) / math.factorial(num_to_remove) / math.factorial(n - num_to_remove)))

        self.logger.debug('Total combinations = {}'.format(total_combis))

        try:
            num_to_return = int(return_ranked_list)
        except:
            num_to_return = 1

        num_to_return = max(1, num_to_return)
        self.logger.debug('Will return {} best structures.'.format(num_to_return))

        if self._algo == PartialRemoveSitesTransformation.ALGO_FAST:
            all_structures = self.fast_ordering(structure, num_remove_dict, num_to_return)
        elif self._algo == PartialRemoveSitesTransformation.ALGO_COMPLETE:
            all_structures = self.complete_ordering(structure, num_remove_dict)
        elif self._algo == PartialRemoveSitesTransformation.ALGO_BEST_FIRST:
            all_structures = self.best_first_ordering(structure, num_remove_dict)
        opt_s = all_structures[0]['structure']
        return opt_s if not return_ranked_list else all_structures[0:num_to_return]

    def __str__(self):
        return "PartialRemoveSitesTransformation : Indices and fraction to remove = {}, ALGO = {}".format(self._specie, self._indices_fraction_dict, self._algo)

    def __repr__(self):
        return self.__str__()

    @property
    def inverse(self):
        return None

    @property
    def is_one_to_many(self):
        return True

    @property
    def to_dict(self):
        output = {'name' : self.__class__.__name__, 'version': __version__}
        output['init_args'] = {'indices': self._indices, 'fractions': self._fractions, 'algo':self._algo}
        return output

