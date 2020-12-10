# Line similarity processing plugin for QGIS

This script measures similarity between 2 line geometries, independently of translation, scale or rotation.

Lines are standardised, by creating for each line an array with 2 columns and 1 line for each vertex except first and last :
* 1 column for the vertex position between 0 and 1, 0 corresponding to the first vertex and 1 to the last vertex
* 1 column for the angle between the vertex, the previous vertex and the next one

The 2 arrays are then considered as variables and the spearman correlation coefficient is calculated.

* Input : 2 lines layers, with only 1 line entity in each layer
* Output : spearman correlation coefficient and p-value, + plot for the standardized lines

This plugin is added in processing, in a provider called "shape analysis".

Reference :
https://www.researchgate.net/post/How_can_I_compare_the_shape_of_two_curves/57d29951cbd5c229b92a866d/citation/download
