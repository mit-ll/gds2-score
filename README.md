# GDS2-Score

**Author:**			Timothy Trippel <br>
**Email:**			timothy.trippel@ll.mit.edu <br>
**Last Updated:**	02/12/2019 <br>

## About

GDS2-Score is a framework that enables integrated circuit (IC) designers to quantify the resiliency of their physical layouts to fabrication-time attacks, and thus, optimize the overall security of their designs. GDS2-Score analyzes physical IC layouts, encoded in the GDS2 file format. The tool is designed to be extensible. Namely, GDS2-Score simply provides an interface that enables the programatic analysis (through the computation of *metrics*) of various circuit structures encoded in a GDS2 file. Three example metrics are included in this release (v1.2) of GDS2-Score. These metrics include: 1) Net Blockage, 2) Trigger Space, and 3) Route Distance. Detailed information on each metric is provided below. Additionally the custom metrics can be developed, as additional Python modules, and executed by the GDS2-Score framework. Details on developing and executing custom GDS2-Scores metrics are listed below

GDS2-Score takes as input the following:

|    | Input                             | Command Line Flag             | Type/Description                                                                                                                     | Required? | Default |
|----|-----------------------------------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|-----------|---------|
| 1  | Analysis Type                     | `(-a\|-b\|-t\|-e)`            | -a = all metrics<br> -b = net blockage only<br> -t = trigger space only<br> -r = route distance only | yes       | none    |
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

\**Graphviz .dot file describing specific nets to be analyzed (this file can be generated by the Nemo [tool](https://llcad-github.llan.ll.mit.edu/HSS/nemo)*

The output of the GDS2-Score framework is an ASCII report detailing results of each of the three metrics (net blockage, trigger space, and route distance).

## Compatability

### Python

GDS2-Score is compatible with Python 2.7.

### PyPy

GDS2-Score can be significantly accelerated using [PyPy](https://pypy.org/), a JIT compiled version of RPython (an alterternative to CPython). GDS2-Score is compatable with PyPy 4.0.1. Newer versions of PyPy, may work, but have not been tested this time.

### VLSI CAD Tools

Currently, GDS2-Score (v1.2) only supports physical design files generated by Cadence VLSI layout CAD tools, specifically Cadence Innovus and Virtuoso software suites.  

## Metrics

### 1. Net Blockage

The net blockage metric quantifies the percentage of surface area of security-critical nets (defined in the input Nemo .dot file) that are blocked by surrouding circuit components. Thus, the net blockage metric quantifies how *accessible* a given net is within an IC layout. Nets that are more accessible, i.e. less blocked, are easy targets for fabrication-time attacks. There are three types of net blockage that are calculated for each security-critical net: *same-layer*, *adjacent-layer*, and *overall*. Same-layer net blockage only analyzes the north, south, east, and west faces of a net. Adjacent-layer net blockage only analyzes the top and bottom sides of a net. Lastly, the overall net blockage is a weighted average of the same-layer (\~66%, for 4/6 sides) and adjacent-layer (\~33%, for 2/6 sides) net blockages.

### 2. Trigger Space

The trigger space metric computes a histogram of open 4-connected regions of all sizes on an IC's placement grid (trigger space histogram). The more large 4-connected open placement regions available, the easier it is for an attacker to locate a space to insert hardware Trojan circuit components at fabrication time. A placement site is considered to be *open* if the site is empty, or if it is occupied by a filler cell. Filler cells, or capacitor cells, are inserted into empty spaces during the last phase of layout by VLSI CAD tools. They can be removed by an attacker without altering the functionality or timing characteristics of the victim IC. Hence, these components are ignored by the trigger space metric.

### 3. Route Distance

The routing distance metric combines the net blockage and trigger space metrics to comprehensively quantify the fabrication-time attack surface an IC layout. It computes a conservative estimate, i.e., Manhattan distance, for the minimal routing distance between open trigger spaces and all unblocked security critical nets (defined as a overall net blockage < 100%). It cross-references each Manhattan distance with the distribution of net lengths within the entire IC layout. Net length can impact whether or not the Trojan circuit will meet timing constraints and function properly. Understanding where in the distribution of net lengths the Trojan routing falls provides insights into the ability of the Trojan circuit(s) to meet any timing requirements and is an opportunity for outlier-based defenses.


# Installation

## 1. Cloning the Git Repository

`git clone git@llcad-github.llan.ll.mit.edu:HSS/gds2-score.git`

## 2. Dependencies

GDS2-Score has only two non-standard Python package dependencies, 1) [python-gdsii](https://pythonhosted.org/python-gdsii/), and 2) [NumPy](http://www.numpy.org/).

1. The first dependency, [python-gdsii](https://pythonhosted.org/python-gdsii/), can be installed in your Python or PyPy enviroment using pip:

```
pip install python-gdsii
```

2. The second dependency, [NumPy](http://www.numpy.org), has different installation instructions depending on if you're using Python or PyPy (v4.0.1):

	A. If you are using a standard distribution of Python, you can install NumPy with pip:

	```
	pip install numpy
	```

	B. If you are using PyPy, the above *may* work (i.e. `pip install numpy`) if you are using new version of PyPy (i.e. > 4.0.1), but if not you can install NumPyPy instead (PyPy's version of NumPy), as detailed [here](https://bitbucket.org/pypy/numpy):

	```
	git clone https://bitbucket.org/pypy/numpy.git
	cd numpy
	git checkout pypy-4.0.1
	pypy setup.py install
	```

## 3. Patch `python-gdsii` Package

Unfortunately, the `python-gdsii` package is somewhat outdated and has a bug that requires a simple fix for GDS2-Score to work:

# User Guide

## Run from Command Line

```
python score.py (-b|-t|-r|-a) [-v] [-h]
	-m    <top module>
	--gds=<gds2 file>
	--ms_lef=<metal stack LEF file>
	--sc_lef=<std cell LEF file>
	--layer_map=<layer map file>
	--def=<DEF file>
	--nemo_dot=<Nemo .dot file>
	--wire_rpt=<wire report file>
	[--nb_type=<0 or 1>]
	[--nb_step=<nb step size>]
	[--num_processes=<number of processes>]
	[--place_grid=<filename.npy>]
	[--mod=<custom module name>]
```

## Developing a Custom (Metric) Module

Custom modules (metrics) can be developed and executed by GDS2-Score. A single module, `layout.py`, contains a reference to all data structures contained within the GDS2-Score framework. A custom module can query and of the data structures present, or imported, in the `layout.py` module. See `net_blockage.py`, `trigger_space.py`, or `route_distance.py` for examples on how to develop a custom GDS2-Score module.

## Executing a Custom (Metric) Module

To execute a custom module, simply include the `--mod=<custom module name>` flag when invoking GDS2-Score. Note that GDS2-Score must invoke any single, or all three, base metrics (net blockage, trigger space, and/or route distance) prior to invoking any custom modules so be sure to include the `(-b|-t|-r|-a)` flag when executing the GDS2-Score framework.

# Development History

## Update 1.1 - 12/7/17

GDS2-Score has been updated to include two additional example metrics: "trigger space" and "routing_distance". Additionally bugs in the Weiler-Atherton polygon clipping algorithm (implemented in the polygon.py module) were fixed.

## Update 1.2 - 2/13/19

The net blockage metric has been updated to utilize a sliding window approach to computing the net blockage on all six sides. There was evidence that the Weiler-Atherton polygon clipping algorithm contained small implementation errors resulting in computational errors. Thus, the use of the Weiler-Atherton polygon clipping algorithm in computing the adjacent-layer net blockage has temporarily been depricated. 

The trigger space metric has been updated to fix histogram printing errors.

The route distance metric has been updated to compute a more accurate Manhattan distance. The Manhattan distance computed is now the minimal distance between the closest unblocked empty placement site within a trigger space and an unblocked location on a security critical net.

The LEF file parser has been updated to automatically identify fill cell names.

# License
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
