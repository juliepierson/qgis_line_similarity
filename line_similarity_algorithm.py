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

__author__ = 'Julie Pierson, UMR 6554 LETG, CNRS'
__date__ = '2020-12-10'
__copyright__ = '(C) 2020 by Julie Pierson, UMR 6554 LETG, CNRS'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import math
import pandas as pd
import plotly.express as px
from scipy import stats
from functools import reduce
from os import path, mkdir
import processing
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFolderDestination,
                       QgsProperty,
                       QgsVectorLayer,
                       QgsProcessingOutputMultipleLayers,
                       QgsProcessingContext,
                       QgsProcessingParameterDistance)

        
class LineSimilarityAlgorithm(QgsProcessingAlgorithm):
    """
    This script measures shape similarity between line geometries 2-by-2, 
    independently of translation, scale or rotation.
    See https://github.com/juliepierson/qgis_line_similarity for more details
    """
    # Save reference to the QGIS interface
#    self.iface = iface

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT1 = 'INPUT1'
    INPUT2 = 'INPUT2'
    ID_INPUT1 = 'ID_INPUT1'
    ID_INPUT2 = 'ID_INPUT2'
    INTERVAL = 'INTERVAL'
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'
    OUTPUT_LAYERS = 'OUTPUT_LAYERS'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # input line layer 1
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT1,
                self.tr('First line layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        # input id field for line layer1
        self.addParameter(
            QgsProcessingParameterField(
                self.ID_INPUT1,
                self.tr('ID field for first line layer'),
                '',
                self.INPUT1
            )
        )
        # input line layer 2
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT2,
                self.tr('Second line layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        # input id field for line layer 2
        self.addParameter(
            QgsProcessingParameterField(
                self.ID_INPUT2,
                self.tr('ID field for second line layer'),
                '',
                self.INPUT2
            )
        )
        # input interval measure
        self.addParameter(
            QgsProcessingParameterDistance(
                self.INTERVAL,
                self.tr('Interval used to densify vertexes (based on layer 1'),
                '',
                self.INPUT1
            )
        )
        # output folder for CSV
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER, 
                self.tr('Output folder for statistic results (CSV)'),
                None, True))
        
        # output layers
        self.addOutput(
            QgsProcessingOutputMultipleLayers(
                self.OUTPUT_LAYERS,
                self.tr('Output layers')
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        
        # Retrieve inputs and output
        layer1 = self.parameterAsVectorLayer(parameters, self.INPUT1, context)
        field1 = self.parameterAsString(parameters, self.ID_INPUT1, context)
        layer2 = self.parameterAsVectorLayer(parameters, self.INPUT2, context)
        field2 = self.parameterAsString(parameters, self.ID_INPUT2, context)
        interval = self.parameterAsInt(parameters, self.INTERVAL, context)
        output_folder = self.parameterAsFile(parameters, self.OUTPUT_FOLDER, context)

        # LET'S GO !
        
        # calculate total length of lines in each layer, one dictionary per layer with one item for each line
        # lineLength = {"line1" : 21.2, "line2" : 14.3, ...}
        lineLength1 = self.getLength(layer1, field1)
        lineLength2 = self.getLength(layer2, field2)
        #QgsMessageLog.logMessage(('lineLength1 : ' + str(lineLength1)), 'LineSimilarity')
        #QgsMessageLog.logMessage(('lineLength2 : ' + str(lineLength2)), 'LineSimilarity')
        
        # retrieves list of line ids from lineLength dictionaries
        lineIds1 = lineLength1.keys()
        lineIds2 = lineLength2.keys()
        # check that lineIds1 and lineIds2 are the same
        if set(lineIds1) != set(lineIds2):
            message = 'Lines from input layers do not have the same ids : for each line in layer 1 there should be a line in layer 2 with same id (and vice versa)'
#            iface.messageBar().pushMessage('Line Similarity', message, level=Qgis.Critical) # does not work ??
            feedback.reportError(QCoreApplication.translate('Line Similarity', message))
            return {}
        
        # densify line vertexes so that each line in layer 1 gets one vertex every chosen interval
        # and each line in layer 2 get as many vertex as line with same id in layer 1
        layer1DensifyPt, layer2DensifyPt = self.densifyLines(layer1, layer2, field2, lineLength1, lineLength2, interval, context, feedback)
        
        # create line layer from point layers layer1densify and layer2densify
        layer1densifyLn = self.lineFromPoint(layer1DensifyPt, field1, "layer 1 densify line", context, feedback)
        layer2densifyLn = self.lineFromPoint(layer2DensifyPt, field2, "layer 2 densify line", context, feedback)
        
        # get all vertex coordinates of lines in each layer, one dictionary per layer with one list for each line
        # pointsCoord = {"line1" : [[xA, yA], [xB, yB], ...], "line2" : [[xA, yA], [xB, yB], ...], ...}
        pointsCoord1 = self.getPointsCoord(layer1densifyLn, field1)
        pointsCoord2 = self.getPointsCoord(layer2densifyLn, field2)
        #QgsMessageLog.logMessage(('pointsCoord1 : ' + str(pointsCoord1)), 'LineSimilarity')
        #QgsMessageLog.logMessage(('pointsCoord2 : ' + str(pointsCoord2)), 'LineSimilarity')
        
        # get for each vertex except 1st and last its distance between 0 and 1 and its angle
        # lineLength = {"line1" : [[0.12, 94], [0.25, 178], ..., [0.93, 134]], "line2" : [[0.09, 88], [0.28, 192], ..., [0.95, 129]], ...}
        pointInfos1 = self.getPointInfo(lineIds1, pointsCoord1, lineLength1)
        pointInfos2 = self.getPointInfo(lineIds2, pointsCoord2, lineLength2)
        #QgsMessageLog.logMessage(('pointInfos1 : ' + str(pointInfos1)), 'LineSimilarity')
        #QgsMessageLog.logMessage(('pointInfos2 : ' + str(pointInfos2)), 'LineSimilarity')
        
        # create dataframe with 4 columns from these infos : distance, angle, line id and layer name
        df, df1, df2 = self.createDataframe(pointInfos1, pointInfos2, layer1.name(), layer2.name())
        
        # create plots for each line, distance as x and angle as y, 
        # this step is optional, only for visualising results
        self.plotLine(df, df1, df2, layer1.name(), layer2.name())
        
        # create one result dataframe : 1st column for line id, next columns for stat results
        dfResults = self.getStatResults(df1, df2, lineIds1, feedback)
        
        # reurn results
        if output_folder:
            # create csv for layer 1 and 2, used to compute statistics
            self.createCSV(output_folder, "layer1", df1)
            self.createCSV(output_folder, "layer2", df2)
            # create csv for statistical results, in output folder
            self.createCSV(output_folder, "similarity", dfResults)
            message = f'CSV results were created in folder {output_folder}'
            feedback.pushInfo(QCoreApplication.translate('Line Similarity', message))

        return {}
    
    # get total length of all lines in a line layer
    # lineLength = {"line1" : 21.2, "line2" : 14.3, ...}
    def getLength(self, lineLayer, idField):
        lineLength = {}
        features = lineLayer.getFeatures()
        for f in features:
            idValue = f[idField]
            geom = f.geometry()
            lineLength[idValue] = geom.length()
        return lineLength
    
    # create point layers for each input layer by adding vertex at given interval in layer 1
    def densifyLines(self, layer1, layer2, field2, lineLength1, lineLength2, distance, context, feedback):
        # add vertex at given interval (distance parameter) for layer 1 with pointsalonglines processing algorithm
        param1 = {'INPUT':layer1,
                  'DISTANCE':distance,
                  'START_OFFSET':0,
                  'END_OFFSET':0,
                  'OUTPUT':'layer 1 densify'}
        res = processing.run("native:pointsalonglines", param1, context=context, feedback=feedback)
        layer1densify = res['OUTPUT']
        # get intervals at which points must be created in layer 2 
        # so that each line gets as many vertex as line with same id in layer1
        intervalLayer2 = {}
        for lineid in lineLength1.keys():
            intervalLayer2[lineid] = lineLength2[lineid] * distance / lineLength1[lineid]
        # add vertex for layer 2 with pointsalongline processing algorithm
        # this is a complicated expression so that for each line entity the distance is equal to to the value of the intervalLayer2 item that has the line id as key
        # https://gis.stackexchange.com/questions/383435/accessing-python-dictionary-by-field-value-in-qgsexpression/383469#383469
        qgis_expr = f'map_get(map{reduce(lambda x, y: x + y, intervalLayer2.items())}, {field2})'
        param2 = {'INPUT':layer2,
                  'DISTANCE': QgsProperty.fromExpression(qgis_expr),
                  'START_OFFSET':0,
                  'END_OFFSET':0,
                  'OUTPUT':'layer 2 densify'}
        res = processing.run("native:pointsalonglines", param2, context=context, feedback=feedback)
        layer2densify = res['OUTPUT']
        # return resulting point layers
        layer1densify = QgsVectorLayer(layer1densify, "layer 1 densify", "ogr")
        layer2densify = QgsVectorLayer(layer2densify, "layer 2 densify", "ogr")
        # these layers do not get loaded in QGIS unless code below is uncommented
#        output_layers = []
#        output_layers.append(layer1densify)
#        context.temporaryLayerStore().addMapLayer(layer1densify)
#        context.addLayerToLoadOnCompletion(
#            layer1densify.id(),
#            QgsProcessingContext.LayerDetails(
#                'layer name',
#                context.project(),
#                self.OUTPUT_LAYERS
#            )
#        )
#        output_layers.append(layer2densify)
#        context.temporaryLayerStore().addMapLayer(layer2densify)
#        context.addLayerToLoadOnCompletion(
#            layer2densify.id(),
#            QgsProcessingContext.LayerDetails(
#                'layer name',
#                context.project(),
#                self.OUTPUT_LAYERS
#            )
#        )    
        return layer1densify, layer2densify
    
    def lineFromPoint(self, layerDensifyPt, idfield, layername, context, feedback):
        # run pointstopath algorithm
        param = {'INPUT': layerDensifyPt,
                  'CLOSE_PATH': False,
                  'ORDER_FIELD': 'distance',
                  'GROUP_FIELD': idfield,
                  'DATE_FORMAT': '',
                  'OUTPUT': layername}
        res = processing.run("qgis:pointstopath", param, context=context, feedback=feedback)
        layerDensifyLn = res['OUTPUT']
        # load resulting layer
        # https://gis.stackexchange.com/a/343404
        layerDensifyLn = QgsVectorLayer(layerDensifyLn, layername, "ogr")
        output_layers = []
        output_layers.append(layerDensifyLn)
        context.temporaryLayerStore().addMapLayer(layerDensifyLn)
        context.addLayerToLoadOnCompletion(
            layerDensifyLn.id(),
            QgsProcessingContext.LayerDetails(
                'layer name',
                context.project(),
                self.OUTPUT_LAYERS
            )
        )
        return layerDensifyLn
    
    # get vertex coordinates from all lines in a line layer
    # {"line1" : [[xA, yA], [xB, yB], ...], "line2" : [[xA, yA], [xB, yB], ...], ...}
    def getPointsCoord(self, lineLayer, idField):
        pointsCoords = {}
        features = lineLayer.getFeatures()
        for f in features:
            idValue = f[idField]
            geom = f.geometry()
            pl = geom.asPolyline()
            pointsCoords[idValue] = [[point.x(), point.y()] for point in pl]
        return pointsCoords
    
    # calculate angle at b from 3 points coordinates a, b and c where each point = [x, y]
    # angle is measured anti-clockwise
    # https://manivannan-ai.medium.com/find-the-angle-between-three-points-from-2d-using-python-348c513e2cd
    def getAngle(self, a, b, c):
        ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
        return ang + 360 if ang < 0 else ang
    
    # calculate the distance between 2 points a, b where each point = [x, y]
    def getDistance(self, a, b):
        distance = math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)
        return distance
    
    # get for each vertex except first and last its position and its angle
    # position is between 0 and 1, with 0 = 1st vertex and 1 = last vertex
    # angle gets calculated with getAngle function
    # result is a dictionary, each item a list where each element = [position, angle]
    # {"line1" : [[0.12, 94], [0.25, 178], ..., [0.93, 134]], "line2" : [[0.09, 88], [0.28, 192], ..., [0.95, 129]], ...}
    def getPointInfo(self, lineIds, pointsCoord, lineLength):
        pointInfos = {k:[] for k in lineIds}
        # for each line
        for key, value in pointsCoord.items():
            distance = 0
            # for each point except 1st and last
            for i, point in enumerate(value[1:-1]):
                # calculates distance to previous vertex
                distToPreviousPoint = self.getDistance(point, value[i])
                # adds it to previous calculated distance
                distance = distance + distToPreviousPoint
                # standardise distance between 0 and 1
                distanceStandardised = distance / lineLength[key]
                # calculate angle between previous vertex, vertex and next vertex
                angle = self.getAngle(value[i], point, value[i+2])
                # stores the distance and angle for each vertex
                pointInfos[key].append([distanceStandardised, angle])
        return pointInfos
    
    # create dataframe from the infos of the 2 line layers
    # 4 columns : distance, angle, line id and layer name
    def createDataframe(self, pointInfos1, pointInfos2, layerName1, layerName2):
        # data frame for 1st layer
        lrows1 = []
        for key in pointInfos1.keys():
            for point in pointInfos1[key]:
                currentDict = {"layer": layerName1, "line id": key, "distance": point[0], "angle": point[1]}
                lrows1.append(currentDict)
        df1 = pd.DataFrame(lrows1)
        # dataframe for 2nd layer
        lrows2 = []
        for key in pointInfos2.keys():
            for point in pointInfos2[key]:
                currentDict = {"layer": layerName2, "line id": key, "distance": point[0], "angle": point[1]}
                lrows2.append(currentDict)
        df2 = pd.DataFrame(lrows2)
        df = pd.concat([df1, df2])
        return df, df1, df2
    
    # create line plot with distance as x and angle as y, for the 2 layers
    # this step is optional, only for visualising results
    def plotLine(self, df, df1, df2, layer1name, layer2name):
        # add dash column to dataframe so that layer 1 = full line and layer 2 = dashed line
        df['dash_line'] = df['layer']
        df.loc[df['dash_line']  == layer1name, 'dash_line'] = ''
        df.loc[df['dash_line']  == layer2name, 'dash_line'] = 'dash'
        # create plot
        fig = px.line(df, x = "distance", y = "angle", color = "line id", line_dash = 'dash_line', line_group = "line id", hover_name = "layer")
        # sets min, max and step for the axes
        fig.update_layout(xaxis_range=[0, 1])
        fig.update_layout(yaxis_range=[0, 360])
        fig.update_yaxes(tick0=0, dtick=45)
        # show plot in web browser
        fig.show()
     
    # from dataframes df1 and df2, create dataframe with statistical results
    # one row per line id, one column per statistical test
    def getStatResults(self, df1, df2, lineIds1, feedback):
        # empty list for lines to add to dfResults
        rows_list = []
        # for each couple of lines with same id 
        for lineId in lineIds1:
            # create empty dic for current line id results
            lineResults = {}
            # add line id in lineResults
            lineResults['line id'] = lineId
            # get line with current id for layer 1
            line1 = df1.loc[df1['line id'] == lineId]
            line1 = list(line1['angle'])
            # get line with current id for layer 2
            line2 = df2.loc[df2['line id'] == lineId]
            line2 = list(line2['angle'])
            # Spearman test
            self.tryTest(lineResults, lineId, line1, line2, 'Spearman', stats.spearmanr, [line1, line2], 'Spearman', 'Spearman p-value', feedback)
            # Shapiro test
            self.tryTest(lineResults, lineId, line1, line2, 'Shapiro for layer 1', stats.shapiro, [line1], 'Shapiro line 1', 'Shapiro p-value line 1', feedback)
            self.tryTest(lineResults, lineId, line1, line2, 'Shapiro for layer 2', stats.shapiro, [line2], 'Shapiro line 2', 'Shapiro p-value line 2', feedback)
            # Student Test
            self.tryTest(lineResults, lineId, line1, line2, 'Student', stats.ttest_rel, [line1, line2], 'Student', 'Student p-value', feedback)
            # perform Wilocoxon test
            self.tryTest(lineResults, lineId, line1, line2, 'Wilcoxon', stats.wilcoxon, [line1, line2], 'Wilcoxon', 'Wilcoxon p-value', feedback)
            # add current line results to dfResults
            rows_list.append(lineResults)
        # add all line to final df
        dfResults = pd.DataFrame(rows_list)
        return dfResults
    
    # try a given statistic test, write results in results dictionary
    def tryTest(self, lineResults, lineId, line1, line2, testName, testFunction, inputList, resultName, pvalueName, feedback):
        # try to compute statistical test
        try:
            stat, pvalue = testFunction(*inputList)
            if math.isnan(stat) or math.isnan(pvalue):
                raise
            # if everything is ok, stores results in result dictionary lineResults
            else:
                lineResults[resultName] = round(stat, 6)
                lineResults[pvalueName] = round(pvalue, 6)
        # if test could not be computed or returned no value
        except:
            message = f'Could not compute {testName} test for line {lineId}, perhaps not enough vertices : try with a lower interval'
            feedback.pushInfo(QCoreApplication.translate('Line Similarity', message))
            lineResults[resultName] = 'nan'
            lineResults[pvalueName] = 'nan'
    
    # create CSV file form result array
    def createCSV(self, output_folder, csv_name, csv_content):
        # if output folder do not exist, create it (save to temporary folder)
        if not path.exists(output_folder):
            mkdir(output_folder)
        csv_file = output_folder + '/' + csv_name + ".csv"
        pd.DataFrame(csv_content).to_csv(csv_file, index=False)
            
    def shortHelpString(self):
        return self.tr('''This algorithm takes 2 line layers as input, with their id field.
                       Lines from each layer with same id get compared 2 by 2, and statistical results for each line pair computed in output csv file.
                       To compare lines, each line in same pair gets same number of vertex, according to interval specified (used for layer 1).''')
    
    def helpUrl(self):
        return "https://github.com/juliepierson/qgis_line_similarity"

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Line similarity'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return LineSimilarityAlgorithm()
