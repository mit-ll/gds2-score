# GDS2-Score

**Author:**			Timothy Trippel <br>
**Email:**			timothy.trippel@ll.mit.edu <br>
**Last Updated:**	02/12/2019 <br>

## About

GDS2-Score is a framework that enables IC designers to quantify the resiliency of their physical layouts to fabrication-time attacks. GDS2-Score analyzes physical IC layouts, encoded in the GDS2 file format. The tool is designed to be extensible. Namely, GDS2-Score simply provides an environment that enables the programatic analysis (through the computation of *metrics*) of various circuit structures encoded in a GDS2 file. Three example metrics are included in this release (v1.2) of GDS2-Score. These metrics include: 1) Net Blockage, 2) Trigger Space, and 3) Route Distance. Detailed information on each metric is provided below. Additionally the custom metrics can be developed, as additional Python modules, and executed by the GDS2-Score framework. Details on developing and executing custom GDS2-Scores metrics are listed below

GDS2-Score takes as input the following:

|    | Input                             | Command Line Flag             | Type/Description                                                                                                                     | Required? | Default |
|----|-----------------------------------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|-----------|---------|
| 1  | Analysis Type                     | `(-a\|-b\|-t\|-e)`            | -a = compute all metrics<br> -b = compute net blockage only<br> -t = compute trigger space only<br> -r = compute route distance only | yes       | none    |
| 2  | Top Module Name                   | `-m <top module name>`        | string                                                                                                                               | yes       | none    |
| 3  | GDS2 File                         | `--gds=<filename>`            | filename                                                                                                                             | yes       | none    |
| 4  | Metal Stack<br> (BEOL) LEF File   | `--ms_lef=<filename>`         | filename                                                                                                                             | yes       | none    |
| 5  | Standard Cell<br> (FEOL) LEF File | `--sc_lef=<filename>`         | filename                                                                                                                             | yes       | none    |
| 6  | Cadence Layer Map File            | `--layer_map=<filename>`      | filename                                                                                                                             | yes       | none    |
| 7  | DEF File                          | `--def=<filename>`            | filename                                                                                                                             | yes       | none    |
| 8  | Nemo Dot File                     | `--nemo_dot=<filename>`       | filename                                                                                                                             | yes       | none    |
| 9  | Cadence Wire Report               | `--wire_rpt=<filename>`       | filename                                                                                                                             | yes       | none    |
| 10 | Verbose Printing                  | `-v`                          | n/a                                                                                                                                  | no        | False   |
| 11 | Net Blockage<br> Algorithm Type   | `--nb_type=<0 or 1>`          | 0 = Fast Coarse Analysis<br> 1 = Slow Detailed Analysis                                                                              | no        | 1       |
| 12 | Net Blockage<br> Step Size        | `--nb_step=<number>`          | unsigned int;<br> Net Blockage resolution<br> in GDS2 database units                                                                 | no        | 1       |
| 13 | Number of Processes               | `--num_processes=<number>`    | unsigned int > 0;<br> Number of parallel<br>  proccesses to spawn                                                                    | no        | 1       |
| 14 | Placement Grid Output File        | `--place_grid=<filename>.npy` | filename (numpy bitmap)                                                                                                              | no        | NULL    |
| 15 | Custom Module                     | `--mod=<module>`              | Python module name<br> (without .py extension)                                                                                       | no        | NULL    |
| 16 | Print Help/Usage Info             | `-h`                          | n/a                                                                                                                                  | no        | n/a     |

\**Graphviz .dot file describing specific nets to be analyzed (this file can be generated by the Nemo tool: https://llcad-github.llan.ll.mit.edu/HSS/nemo)*

The output of the GDS2-Score framework is an ASCII report detailing results of each of the three metrics (net blockage, trigger space, and route distance).

## Compatability
Currently, GDS2-Score (v1.2) only supports physical design files generated by Cadence VLSI layout CAD tools, specifically Cadence Innovus and Virtuoso software suites.  

## Metrics

### 1. Net Blockage

The net blockage metric quantifies the percentage of surface area of security-critical nets (defined in the input Nemo .dot file) that are blocked by surrouding circuit components. Thus, the net blockage metric quantifies how *accessible* a given net is within an IC layout. Nets that are more accessible, i.e. less blocked, are easy targets for fabrication-time attacks. There are three types of net blockage that are calculated for each security-critical net: *same-layer*, *adjacent-layer*, and *overall*. Same-layer net blockage only analyzes the north, south, east, and west faces of a net. Adjacent-layer net blockage only analyzes the top and bottom sides of a net. Lastly, the overall net blockage is a weighted average of the same-layer (\~66%, for 4/6 sides) and adjacent-layer (\~33%, for 2/6 sides) net blockages.

### 2. Trigger Space

The trigger space metric computes a histogram of open 4-connected regions of all sizes on an IC's placement grid (trigger space histogram). The more large 4-connected open placement regions available, the easier it is for an attacker to locate a space to insert hardware Trojan circuit components at fabrication time. A placement site is considered to be *open* if the site is empty, or if it is occupied by a filler cell. Filler cells, or capacitor cells, are inserted into empty spaces during the last phase of layout by VLSI CAD tools. They can be removed by an attacker without altering the functionality or timing characteristics of the victim IC. Hence, these components are ignored by the trigger space metric.

### 3. Route Distance

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
