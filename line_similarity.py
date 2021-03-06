# -*- coding: utf-8 -*-

"""
/***************************************************************************
 LineSimilarity
                                 A QGIS plugin
 Calculate similarity between 2 lines
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-12-10
        copyright            : (C) 2020 by Julie Pierson, UMR 6554 LET, CNRS
        email                : julie.pierson@univ-brest.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Julie Pierson, UMR 6554 LET, CNRS'
__date__ = '2020-12-10'
__copyright__ = '(C) 2020 by Julie Pierson, UMR 6554 LET, CNRS'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect

from qgis.core import QgsProcessingAlgorithm, QgsApplication
from .line_similarity_provider import LineSimilarityProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class LineSimilarityPlugin(object):

    def __init__(self):
        self.provider = None

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = LineSimilarityProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
