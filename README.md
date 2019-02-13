# GDS2-Score

**Author:**			Timothy Trippel <br>
**Email:**			timothy.trippel@ll.mit.edu <br>
**Last Updated:**	02/12/2019 <br>

## About

GDS2-Score is an extensible framework that enables IC designers to quantify the resiliency of their physical layouts to fabrication-time attacks. GDS2-Score analyzes physical IC layouts, encoded in the GDS2 file format. Currently, GDS2-Score only supports physical design files generated by Cadence VLSI layout CAD tools, specifically Cadence Innovus and Virtuoso software suites. Three example metrics are included in this release of GDS2-Score. These metrics include: 1) Net Blockage, 2) Trigger Space, and 3) Route Distance. Detailed information on each metric is provided below.

GDS2-Score takes as input the following:

|    | Input                         | Command Line Flag             | Type/Description                                                                                                                     | Required? | Default |
|----|-------------------------------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|-----------|---------|
| 1  | Analysis Type                 | `(-a\|-b\|-t\|-e)`               | -a = all metrics<br> -b = net blockage only<br> -t = trigger space only<br> -r = route distance only | yes       | none    |
| 2  | Top Module Name               | `-m <top module name>`        | string                                                                                                                               | yes       | none    |
| 3  | GDS2 File                     | `--gds=<filename>`            | filename                                                                                                                             | yes       | none    |
| 4  | Metal Stack (BEOL) LEF File   | `--ms_lef=<filename>`         | filename                                                                                                                             | yes       | none    |
| 5  | Standard Cell (FEOL) LEF File | `--sc_lef=<filename>`         | filename                                                                                                                             | yes       | none    |
| 6  | Cadence Layer Map File        | `--layer_map=<filename>`      | filename                                                                                                                             | yes       | none    |
| 7  | DEF File                      | `--def=<filename>`            | filename                                                                                                                             | yes       | none    |
| 8  | Nemo Dot File                 | `--nemo_dot=<filename>`       | filename                                                                                                                             | yes       | none    |
| 9  | Cadence Wire Report           | `--wire_rpt=<filename>`       | filename                                                                                                                             | yes       | none    |
| 10 | Net Blockage Algorithm Type   | `--nb_type=<0 or 1>`          | 0 = Fast Coarse Analysis<br> 1 = Slow Detailed Analysis                                                                              | no        | 1       |
| 11 | Net Blockage Step Size        | `--nb_step=<number>`          | unsigned int;<br> Net Blockage resolution<br> in GDS2 database units                                                                 | no        | 1       |
| 12 | Number of Processes           | `--num_processes=<number>`    | unsigned int > 0;<br> Number of parallel<br>  proccesses to spawn                                                                    | no        | 1       |
| 13 | Placement Grid<br>(.npy) Output File    | `--place_grid=<filename>` | filename (numpy bitmap)                                                                                                              | no        | NULL    |
| 14 | Custom Module                 | `--mod=<module>`  | Python module name<br> (without .py extension)                                                                                       | no        | NULL    |

\**Graphviz .dot file describing specific nets to be analyzed (this file can be generated by the Nemo tool: https://github.com/mit-ll/nemo)*

The GDS2-Score tool is designed to be extensible. This means that GDS2-Score simply provides an environment that allows one to analyze specific nets in a GDS2 file and calculate various metrics. Three example metrics are provided in this release (v1.1). These example metrics include "net blockage", "trigger space" and "routing distance". The "net blockage" metric is computed by invoking the "blockage_metric" function in the "main" function of the Python module "score.py". This metric calculates the percentage of the total surface area of the critical nets (in the .dot file input) that is blocked by other nets or components described in the IC layout. The "trigger space" metric is computed by invoking the "trigger_space_metric" function in the "main" function of the Python module "score.py". This metric calculates a histogram detailing the size and frequencies of open contiguous (4-connected) regions on the device layer placement grid of an IC layout. The "routing distance" metric is computed by invoking the "routing_distance_metric" function in the "main" function of the Python module "score.py". This metric computes Manhattan distance estimates between open spaces on the device layer placement grid and critical nets (in the .dot file input) and compares these estimates to the overall mean net length of the entire IC design.

## Metrics

### Net Blockage
### Trigger Space
### Route Distance

# Development History

## Update 1.1 - 12/7/17
GDS2-Score has been updated to include two additional example metrics: "trigger space" and "routing_distance". Additionally bugs in the Weiler-Atherton polygon clipping algorithm (implemented in the polygon.py module) were fixed.

## Update 1.2 - 2/13/19
Updated all metrics.

## Cloning the Git Repository
git clone <GDS2-Score Repository URL>

## Running GDS2-Score

1. Edit the input file paths located in the "main" function of the "score.py" script
2. To compute all metrics: python score.py -av 

**Note**: to learn how to pass input files via the command line run "python score.py -h".

## License
Copyright (c) 2017, Massachusetts Institute of Technology.

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

DISTRIBUTION STATEMENT A. Approved for public release: distribution unlimited.

This material is based upon work supported by the Assistant Secretary of Defense
for Research and Engineering under Air Force Contract No. FA8721-05-C-0002
and/or FA8702-15-D-0001. Any opinions, findings, conclusions or recommendations
expressed in this material are those of the author(s) and do not necessarily
reflect the views of the Assistant Secretary of Defense for Research and
Engineering.

© 2017 Massachusetts Institute of Technology.

The software/firmware is provided to you on an As-Is basis

Delivered to the U.S. Government with Unlimited Rights, as defined in DFARS Part
252.227-7013 or 7014 (Feb 2014). Notwithstanding any copyright notice, U.S.
Government rights in this work are defined by DFARS 252.227-7013 or DFARS
252.227-7014 as detailed above. Use of this work other than as specifically
authorized by the U.S. Government may violate any copyrights that exist in this
work.
