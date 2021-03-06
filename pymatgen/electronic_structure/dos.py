#!/usr/bin/env python

"""
This module defines classes to represent the density of states, etc.
"""

from __future__ import division

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "2.0"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyue@mit.edu"
__date__ = "Mar 20, 2012"

from collections import OrderedDict

import numpy as np

from pymatgen.electronic_structure.core import Spin, Orbital
from pymatgen.core.structure import Structure
from pymatgen.util.plotting_utils import get_publication_quality_plot
from pymatgen.util.io_utils import clean_json
from pymatgen.util.coord_utils import get_linear_interpolated_value


class Dos(object):
    """
    Basic DOS object. All other DOS objects are extended versions of this object.
    """

    def __init__(self, efermi, energies, densities):
        """
        Args:
            efermi:
                Fermi level energy
            energies:
                A sequences of energies
            densities:
                A dict of {Spin: np.array} representing the density of states 
                for each Spin.
        """
        self._efermi = efermi
        self._energies = np.array(energies)
        self._dos = {k:np.array(d) for k, d in densities.items()}

    def get_densities(self, spin=None):
        """
        Returns the density of states for a particular spin. If Spin is None,
        the sum of both Spin.up and Spin.down (if they exist) is returned.
        
        Args:
            spin:
                Spin
        """
        if self._dos == None:
            result = None
        elif spin == None:
            if Spin.down in self._dos:
                result = self._dos[Spin.up] + self._dos[Spin.down]
            else:
                result = self._dos[Spin.up]
        else:
            result = self._dos[spin]
        return result

    @property
    def densities(self):
        """
        Dict representation of the densities, {Spin: densities}
        """
        return self._dos

    def get_smeared_densities(self, sigma):
        """
        Returns the Dict representation of the densities, {Spin: densities}, 
        but with a Gaussian smearing of std dev sigma applied about the fermi
        level.
        
        Args:
            sigma:
                Std dev of Gaussian smearing function.
        """
        from scipy.ndimage.filters import gaussian_filter1d
        smeared_dens = {}
        diff = [self._energies[i + 1] - self._energies[i] for i in xrange(len(self.energies) - 1)]
        avgdiff = sum(diff) / len(diff)
        for spin, dens in self._dos.items():
            smeared_dens[spin] = gaussian_filter1d(dens, sigma / avgdiff)
        return smeared_dens

    @property
    def efermi(self):
        """
        Fermi energy
        """
        return self._efermi

    @property
    def energies(self):
        """
        Energy levels of the DOS.
        """
        return self._energies

    def __add__(self, other):
        """
        Adds two DOS together. Checks that energy scales are the same. 
        Otherwise, a ValueError is thrown.
        
        Args:
            other:
                Another DOS object.
                
        Returns:
            Sum of the two DOSs.
        """
        if not (self.energies == other.energies).all():
            raise ValueError("Energies of both DOS are not compatible!")
        densities = {spin: self._dos[spin] + other._dos[spin] for spin in self._dos.keys()}
        return Dos(self.efermi, self.energies, densities)

    def get_interpolated_value(self, energy):
        """
        Returns interpolated density for a particular energy.
        
        Args:
            energy:
                Energy to return the density for.
        """
        f = {}
        for spin in self._dos.keys():
            f[spin] = get_linear_interpolated_value(self._energies, self._dos[spin], energy)
        return f

    def get_interpolated_gap(self, tol=0.001, abs_tol=False, spin=None):
        """
        Expects a DOS object and finds the gap
        
        Args:
            tol:
                tolerance in occupations for determining the gap
            abs_tol:
                tolerance an absolute tolerance (True) and a relative one (False)
            spin:
                Possible values are:
                    None - finds the ap in the summed densities
                    Up - finds the gap in the up spin channel
                    Down - finds the gap in teh down spin channel
        
        Returns:
            (gap, cbm, vbm) :  tuple of floats in eV corresponding to the gap, cbm and vbm
        """

        tdos = self.get_densities(spin)
        if abs_tol == False:
            tol = tol * tdos.sum() / tdos.shape[0]
        energies = self._energies
        below_fermi = [i for i in xrange(len(energies)) if energies[i] < self._efermi and tdos[i] > tol]
        above_fermi = [i for i in xrange(len(energies)) if energies[i] > self._efermi and tdos[i] > tol]
        vbm_start = max(below_fermi)
        cbm_start = min(above_fermi)
        if vbm_start == cbm_start:
            return 0.0, self._efermi, self._efermi
        else:
            # Interpolate between adjacent values
            start = get_linear_interpolated_value(tdos[vbm_start:vbm_start + 2][::-1], energies[vbm_start:vbm_start + 2][::-1], tol)
            end = get_linear_interpolated_value(tdos[cbm_start - 1:cbm_start + 1], energies[cbm_start - 1:cbm_start + 1], tol)
            return end - start, end, start

    def get_cbm_vbm(self, tol=0.001, abs_tol=False, spin=None):
        """
        Expects a DOS object and finds the cbm and vbm.
        
        Args:
            tol: 
                tolerance in occupations for determining the gap
            abs_tol: 
                an absolute tolerance (True) and a relative one (False)
            spin:
                Possible values are:
                    None - finds the gap in the summed densities
                    Up - finds the gap in the up spin channel
                    Down - finds the gap in teh down spin channel
        
        Returns:
            (cbm, vbm): float in eV corresponding to the gap
        """
        #determine tolerance
        tdos = self.get_densities(spin)
        if abs_tol == False:
            tol = tol * tdos.sum() / tdos.shape[0]

        # find index of fermi energy
        i_fermi = 0
        while (self._energies[i_fermi] <= self._efermi):
            i_fermi += 1

        # work backwards until tolerance is reached
        i_gap_start = i_fermi
        while i_gap_start - 1 >= 0 and tdos[i_gap_start - 1] <= tol :
            i_gap_start -= 1

        # work forwards until tolerance is reached
        i_gap_end = i_gap_start
        while i_gap_end < tdos.shape[0] and tdos[i_gap_end] <= tol :
            i_gap_end += 1
        i_gap_end -= 1
        return (self._energies[i_gap_end], self._energies[i_gap_start])

    def get_gap(self, tol=0.001, abs_tol=False, spin=None):
        """
        Expects a DOS object and finds the gap.
        
        Args:
            tol: 
                tolerance in occupations for determining the gap
            abs_tol: 
                an absolute tolerance (True) and a relative one (False)
            spin:
                Possible values are:
                    None - finds the gap in the summed densities
                    Up - finds the gap in the up spin channel
                    Down - finds the gap in teh down spin channel
        
        Returns:
            gap in eV
        """
        (cbm, vbm) = self.get_cbm_vbm(tol, abs_tol, spin)
        return max(cbm - vbm, 0.0)

    def __str__(self):
        """
        Returns a string which can be easily plotted (using gnuplot).
        """
        if Spin.down in self._dos:
            stringarray = ["#%30s %30s %30s" % ('Energy', 'DensityUp', 'DensityDown')]
            stringarray.extend(["%.5f %.5f %.5f" % (self._energies[i], self._dos[Spin.up][i], self._dos[Spin.down][i]) for i in range(len(self._energies))])
        else:
            stringarray = ["#%30s %30s" % ('Energy', 'DensityUp')]
            stringarray.extend(["%.5f %.5f" % (self._energies[i], self._dos[Spin.up][i]) for i in range(len(self._energies))])
        return "\n".join(stringarray)

    @staticmethod
    def from_dict(d):
        """
        Returns Dos object from dict representation of Dos.
        """
        return Dos(d['efermi'], d['energies'], { Spin.from_int(int(k)):v for k, v in d['densities'].items()})

    @property
    def to_dict(self):
        """
        Json-serializable dict representation of Dos.
        """
        d = {}
        d['efermi'] = self._efermi
        d['energies'] = list(self._energies)
        d['densities'] = { str(int(spin)) : list(dens) for spin , dens in self._dos.items() }
        return d


class PDos(Dos):
    """
    Projected DOS for a specific orbital. Extends the Dos object.
    """
    def __init__(self, efermi, energies, densities, orbital):
        """
        Args:
            efermi:
                Fermi level energy
            energies:
                A sequences of energies
            densities:
                A dict of {Spin: np.array} representing the density of states 
                for each Spin.
            site:
                Site associated with the projected DOS.
            orbital:
                The orbital associated with the projected DOS.
        """
        Dos.__init__(self, efermi, energies, densities)
        self.orbital = orbital

    def __str__(self):
        return "#" + str(self.orbital) + "\n" + super(PDos, self).__str__()

    @staticmethod
    def from_dict(d):
        """
        Returns PDos object from dict representation.
        """
        return PDos(d['efermi'], d['energies'], { Spin.from_int(int(k)):v for k, v in d['densities'].items()}, Orbital.from_string(d['orbital']))

    @property
    def to_dict(self):
        """
        Json-serializable dict representation of PDos.
        """
        d = {}
        d['efermi'] = self._efermi
        d['energies'] = list(self._energies)
        d['densities'] = { str(int(spin)) : list(dens) for spin , dens in self._dos.items() }
        d['orbital'] = str(self.orbital)
        return d

class CompleteDos(Dos):
    """
    This wrapper class defines a total dos, and also provides a list of PDos.
    Mainly used by pymatgen.io.vaspio.Vasprun to create a complete Dos from
    a vasprun.xml file. You are unlikely to try to generate this object manually.
    """

    def __init__(self, structure, total_dos, pdoss):
        """
        Args:
            structure:
                Structure associated with this particular DOS.
            total_dos:
                total Dos for structure
            pdoss:
                The pdoss are supplied as an { Site : {Orbital : Dos.. }}
        """
        self._efermi = total_dos.efermi
        self._energies = total_dos.energies
        self._dos = total_dos.densities
        self._pdos = pdoss
        self._structure = structure

    @property
    def structure(self):
        """
        Structure associated with the CompleteDos.
        """
        return self._structure

    def get_site_orbital_dos(self, site, orbital):
        """
        Get the Dos for a particular orbital of a particular site.
        
        Args:
            site:
                Site in Structure associated with CompleteDos.
            orbital:
                Orbital in the site.
                
        Returns:
            Dos containing densities for orbital of site.
        """
        return self._pdos[site][orbital]

    def get_site_dos(self, site):
        """
        Get the total Dos for a site (all orbitals).
        
        Args:
            site:
                Site in Structure associated with CompleteDos.
                
        Returns:
            Dos containing summed orbital densities for site.
        """
        site_dos = None
        for pdos in self._pdos[site].values():
            if site_dos == None:
                site_dos = Dos(pdos.efermi, pdos.energies, pdos.densities)
            else:
                site_dos += pdos
        return site_dos

    def get_spd_dos(self):
        """
        Get orbital projected Dos.
        
        Returns:
            dict of {orbital: Dos}, e.g. {'s': Dos object, ...}
        """
        spd_dos = dict()
        for atom_dos in self._pdos.values():
            for pdos in atom_dos.values():
                orbital_type = pdos.orbital.orbital_type
                if orbital_type not in spd_dos:
                    spd_dos[orbital_type] = Dos(pdos.efermi, pdos.energies, pdos.densities)
                else:
                    spd_dos[orbital_type] += pdos
        return spd_dos

    def get_element_dos(self):
        """
        Get element projected Dos.
        
        Returns:
            dict of {Element: Dos}
        """

        el_dos = dict()
        for site, atom_dos in self._pdos.items():
            el = site.specie
            for pdos in atom_dos.values():
                if el not in el_dos:
                    el_dos[el] = Dos(pdos.efermi, pdos.energies, pdos.densities)
                else:
                    el_dos[el] += pdos
        return el_dos

    @staticmethod
    def from_dict(d):
        """
        Returns CompleteDos object from dict representation.
        """
        tdos = Dos.from_dict(d)
        struct = Structure.from_dict(d['structure'])
        pdoss = {}
        for i in xrange(len(d['pdos'])):
            at = struct[i]
            orb_dos = {}
            for orb_str, odos in d['pdos'][i].items():
                orb = Orbital.from_string(orb_str)
                orb_dos[orb] = PDos(odos['efermi'], odos['energies'], { Spin.from_int(int(k)):v for k, v in odos['densities'].items()}, orb)
            pdoss[at] = orb_dos
        return CompleteDos(struct, tdos, pdoss)

    @property
    def to_dict(self):
        """
        Json-serializable dict representation of CompleteDos.
        """
        d = {}
        d['efermi'] = self._efermi
        d['structure'] = self._structure.to_dict
        d['energies'] = list(self._energies)
        d['densities'] = { str(int(spin)) : list(dens) for spin , dens in self._dos.items() }
        d['pdos'] = []
        if len(self._pdos) > 0:
            for at in self._structure:
                dd = dict()
                for pdos in self._pdos[at].values():
                    dd[str(pdos.orbital)] = {'efermi' : pdos.efermi, 'energies': list(pdos.energies), 'densities' : { str(int(spin)) : list(dens) for spin , dens in pdos.densities.items() }}
                d['pdos'].append(dd)
            d['atom_dos'] = {str(at) : dos.to_dict for at, dos in self.get_element_dos().items()}
            d['spd_dos'] = {str(orb) : dos.to_dict for orb, dos in self.get_spd_dos().items()}
        return d

    def __str__(self):
        return "Complete DOS for " + str(self._structure)


class DosPlotter(object):
    """
    Class for plotting DOSes.
    """

    def __init__(self, zero_at_efermi=True, stack=False,
                 sigma=None):
        """
        Args:
            zero_at_efermi:
                Whether to shift all Dos to have zero energy at the fermi energy.
                Defaults to True.
            stack:
                Whether to plot the DOS as a stacked area graph
            key_sort_func:
                function used to sort the dos_dict keys.
            sigma:
                A float specifying a standard deviation for Gaussian smearing the 
                DOS for nicer looking plots. Defaults to None for no smearing.
        """
        self.zero_at_efermi = zero_at_efermi
        self.stack = stack
        self.sigma = sigma
        self._doses = OrderedDict()

    def add_dos(self, label, dos):
        """
        Adds a dos for plotting.
        
        Args:
            label:
                label for the DOS. Must be unique.
            dos:
                Dos object
        """
        energies = dos.energies - dos.efermi if self.zero_at_efermi else dos.energies
        densities = dos.get_smeared_densities(self.sigma) if self.sigma else dos.densities
        efermi = dos.efermi
        self._doses[label] = {'energies':energies, 'densities': densities, 'efermi':efermi}

    def add_dos_dict(self, dos_dict, key_sort_func=None):
        """
        Add a dictionary of doses, with an optional sorting function for the 
        keys.
        
        Args:
            dos_dict:
                dict of {label: Dos}
            key_sort_func:
                function used to sort the dos_dict keys.
        """
        if key_sort_func:
            keys = sorted(dos_dict.keys(), key=key_sort_func)
        else:
            keys = dos_dict.keys()
        for label in keys:
            self.add_dos(label, dos_dict[label])

    def get_dos_dict(self):
        """
        Returns the added doses as a json-serializable dict. Note that if you
        have specified smearing for the DOS plot, the densities returned will
        be the smeared densities, not the original densities.
        
        Returns:
            Dict of dos data. Generally of the form, {label: {'energies':..,
            'densities': {'up':...}, 'efermi':efermi}}
        """
        return clean_json(self._doses)

    def show(self, xlim=None, ylim=None):
        """
        Show the plot using matplotlib.
        
        Args:
            xlim:
                Specifies the x-axis limits. Set to None for automatic 
                determination.
            ylim:
                Specifies the y-axis limits. 
        """
        plt = get_publication_quality_plot(12, 8)
        color_order = ['r', 'b', 'g', 'c']

        y = None
        alldensities = []
        allenergies = []
        """
        Note that this complicated processing of energies is to allow for
        stacked plots in matplotlib.
        """
        for key, dos in self._doses.items():
            energies = dos['energies']
            densities = dos['densities']
            if not y:
                y = {Spin.up: np.zeros(energies.shape), Spin.down: np.zeros(energies.shape)}
            newdens = {}
            for spin in [Spin.up, Spin.down]:
                if spin in densities:
                    if self.stack:
                        y[spin] += densities[spin]
                        newdens[spin] = y[spin].copy()
                    else:
                        newdens[spin] = densities[spin]
            allenergies.append(energies)
            alldensities.append(newdens)

        keys = list(self._doses.keys())
        keys.reverse()
        alldensities.reverse()
        allenergies.reverse()
        allpts = []
        for i, key in enumerate(keys):
            x = []
            y = []
            for spin in [Spin.up, Spin.down]:
                if spin in alldensities[i]:
                    densities = list(int(spin) * alldensities[i][spin])
                    energies = list(allenergies[i])
                    if spin == Spin.down:
                        energies.reverse()
                        densities.reverse()
                    x.extend(energies)
                    y.extend(densities)
            allpts.extend(zip(x, y))
            if self.stack:
                plt.fill(x, y, color=color_order[i % 4], label=str(key))
            else:
                plt.plot(x, y, color=color_order[i % 4], label=str(key))
            if not self.zero_at_efermi:
                ylim = plt.ylim()
                plt.plot([self._doses[key]['efermi'], self._doses[key]['efermi']], ylim, color_order[i % 4] + '--', linewidth=2)

        plt.xlabel('Energies (eV)')
        plt.ylabel('Density of states')
        if xlim:
            plt.xlim(xlim)
        if ylim:
            plt.ylim(ylim)
        else:
            xlim = plt.xlim()
            relevanty = [p[1] for p in allpts if p[0] > xlim[0] and p[0] < xlim[1]]
            plt.ylim((min(relevanty), max(relevanty)))

        if self.zero_at_efermi:
            ylim = plt.ylim()
            plt.plot([0, 0], ylim, 'k--', linewidth=2)

        plt.legend()
        leg = plt.gca().get_legend()
        ltext = leg.get_texts()  # all the text.Text instance in the legend
        plt.setp(ltext, fontsize=30)
        plt.tight_layout()
        plt.show()

