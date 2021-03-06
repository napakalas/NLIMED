# Natural Language Interface for Model Entities Discovery (NLIMED)
#
# Copyright (C) 2019 NLIMED Project
# Authors: Yuda Munarko <ymun794@aucklanduni.ac.nz>
#          Dewan M. Sarwar
#          Koray Atalag
#          David P. Nickerson
# URL: https://github.com/napakalas/NLIMED
# For license information, see LICENSE.TXT

"""
Natural Language Interface for Model Entity Discovery (NLIMED) is an interface
to search model entities (i.e. flux of sodium across the basolateral plasma
membrane, the concentration of potassium in the portion of tissue fluid) in
the biosimulation models in repositories. The interface utilises the RDF inside
biosimulation models and metadata from BioPortal

Yuda Munarko, Dewan M. Sarwar, Koray Atalag, and David P. Nickerson (2019).
NLIMED: Natural Language Interface for ModelEntity Discovery in Biosimulation ModelRepositories.
https://doi.org/10.1101/756304
"""

# Copyright notice
__copyright__ = """\
Copyright (C) 2019 NLIMED.

Distributed and Licensed under the GNU GENERAL PUBLIC LICENSE, Version 3,
which is included by reference.
"""

__license__ = "License :: OSI Approved :: GNU General Public License (GPL)"

from NLIMED.NLIMED import NLIMED
from NLIMED.NLIMED import getConfig, config
import os
import nltk

# check nltk_data availability, download if not available
__required_nltk_group__ = ['taggers', 'corpora']
__required_nltk_data__ = ['stopwords', 'averaged_perceptron_tagger']
__available_nltk_data__ = []
for __group__ in __required_nltk_group__:
    try:
        __available_nltk_data__ += os.listdir(nltk.data.find(__group__))
    except:
        pass
for __required__ in __required_nltk_data__:
    if __required__ not in __available_nltk_data__:
        nltk.download(__required__)

# standard arguments for NLIMED setup
def __pl_type__(x):
    x = int(x)
    if x >= 1:
        return x
    raise ValueError("Minimum precision level is 1")

def __multiply_type__(x):
    x = float(x)
    if x >= 0:
        return x
    raise ValueError("Minimum multiplier is 0")

__dictArgsMandatory__ = {'repo': ['pmr', 'bm', 'all'], 'parser': ['stanford', 'nltk', 'ncbo']}
__dictArgsOptional__ = {'show': ['models', 'sparql', 'annotation', 'verbose'], 'pl': __pl_type__,
                        'alpha': __multiply_type__, 'beta': __multiply_type__, 'gamma': __multiply_type__,
                        'delta': __multiply_type__, 'quite': False}
__dictDefArgsVal__ = {'repo': __dictArgsMandatory__['repo'][0], 'parser': __dictArgsMandatory__['parser'][0],
                      'show': __dictArgsOptional__['show'], 'pl': 1,
                      'alpha': 0.4, 'beta': 0.1, 'gamma': 1.0, 'delta': 1.0, 'quite': False}
