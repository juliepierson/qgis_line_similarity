# Line similarity processing plugin for QGIS

## Brief summary

This script measures shape similarity between line geometries 2-by-2, independently of translation, scale or rotation.

It takes 2 line layers as input, and their id field. Lines from each layer with same id get compared, and similarity measures using different statistical tests are computed.

Output is a CSV with the statistical results and p-values.

Statistical tests used are Spearman, Student and Wilcoxon. Thanks to Grégoire Le Campion (UMR Passages, CNRS) for his input on statistics !

This plugin is added in processing, in a provider called "shape analysis".

## Dependencies

This plugin uses the following Python modules :  pandas, numpy, scipy and plotly.

## More details

There are 3 steps for this plugin :

- lines from each layer with same id gets same number of vertexes. Number of vertexes is set so that they are spaced according to a given interval in layer 1
- lines are standardized, by getting for each vertex except first and last : 1/vertex position between 0 and 1, 0 corresponding to the first vertex and 1 to the last vertex, and 2/ angle between the vertex, the previous vertex and the next one

These 2 steps allows for the similarity results to be independent of scale, rotation and translation. Beware though that if 2 lines do not have same direction, they may not be considered similar even though they are (symmetry is not taken into account).

* 3rd step is then calculating statistical tests for each line pair : Spearman, Student and Wilcoxon. Shapiro test is also performed  to know if it's ok to use Student results.

Output is a CSV with one row per line id, and one column for each statistical result.

The plugin also output the lines created in step 1 as temporary layers, and a HTML plot of the standardized lines create in step 2 (using plotly).

Do not hesitate to message me if there is any problem, or if you have any ideas to make it better ! It is experimental work.

